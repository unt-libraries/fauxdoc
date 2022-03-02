"""Contains functions and classes for emitting randomized data values."""
from abc import ABC, abstractmethod
import collections.abc
import datetime
import itertools
import random
from typing import Any, Callable, Optional, List, Sequence, Tuple, Union,\
                   TypeVar

import pytz

from .exceptions import ChoicesWeightsLengthMismatch
from .math import time_to_seconds, seconds_to_time, weighted_shuffle
from solrfixtures.typing import Number, RandomStrEmitterLike,\
                                RandomDateEmitterLike, RandomTimeEmitterLike,\
                                TzInfoLike


def make_alphabet(uchar_ranges: Optional[Sequence[tuple]] = None) -> List[str]:
    """Generates an alphabet from provided unicode character ranges.

    This creates a list of characters to use as an alphabet for string
    and text-type emitter objects. Tip: providing a range like
    (ord('A'), ord('Z')) gives you letters from A to Z.

    Args:
        uchar_ranges: (Optional.) A sequence of tuples, where each
        tuple represents a range of Unicode code points to include in
        your alphabet. RANGES ARE INCLUSIVE, unlike Python range
        objects. If not provided, defaults to: [
            (0x0021, 0x0021), (0x0023, 0x0026), (0x0028, 0x007E),
            (0x00A1, 0x00AC), (0x00AE, 0x00FF)
        ]

    Returns:
        A list of characters that fall within the provided ranges.
    """
    uchar_ranges = uchar_ranges or [
        (0x0021, 0x0021), (0x0023, 0x0026), (0x0028, 0x007E), (0x00A1, 0x00AC),
        (0x00AE, 0x00FF)
    ]
    return [
        chr(code) for (start, end) in uchar_ranges
        for code in range(start, end + 1)
    ]


class BaseEmitter(ABC):
    """Simple abstract base class for defining emitter objects.

    Subclass this to implement an emitter object. At this level all we
    require is an `emit` method. Use `__init__` to configure whatever
    options your emitter may need.

    The `__call__` method wraps `emit` so you can emit data values
    simply by calling the object.
    """

    T = TypeVar('T')

    def __init__(self) -> None:
        """Inits the BaseEmitter instance."""
        self.reset()

    def reset(self) -> None:
        """Resets state on this object.

        Override this in your subclass if your emitter stores state
        changes that may need to be reset to their initial values. (The
        subclass is responsible for tracking the initial values.) By
        default this is a no-op.
        """

    @property
    def emits_unique_values(self) -> bool:
        """Returns a bool; True if an instance emits unique values.

        We mean "unique" in terms of the lifetime of the instance, not
        a given call to `emit_multiple`. This should return True if the
        instance is guaranteed never to return a duplicate.
        """
        return False

    @property
    def num_unique_values(self) -> Union[None, int]:
        """Returns an int, the number of unique values emittable.

        This number should be relative to the next `emit` or
        `emit_multiple` call. If your instance is one where
        `emits_unique_values` is True, then this should return the
        number of unique values that remain at any given time.
        Otherwise, this should give the total number of unique values
        that can be emitted. Return None if the number is effectively
        infinite (such as with a random text emitter).
        """
        return None

    def raise_uniqueness_violation(self, number: int) -> None:
        """Raises a ValueError indicating not enough unique values.

        Args:
            number: An integer indicating how many new unique values
                were requested.
        """
        raise ValueError(
            f"Could not emit: {number} new unique value"
            f"{' was' if number == 1 else 's were'} requested, out of "
            f"{self.num_unique_values} possible selections."
        )

    def __call__(self, number: int = 1) -> Union[T, List[T]]:
        """Wraps the `self.emit` method so that this obj is callable.

        Args:
            number: (Optional.) How many data values to emit. Default
                is 1.

        Returns:
            If `number` is 1, then it returns one data value by calling
            `emit`. If `number` > 1, then it returns a list of data
            values by calling `emit_multiple`.
        """
        return self.emit() if number == 1 else self.emit_multiple(number)

    @abstractmethod
    def emit(self) -> T:
        """Returns one data value.

        Override this in your subclass. It should return whatever value
        is appropriate given your emitter class.
        """

    def emit_multiple(self, number: int = 1) -> List[T]:
        """Returns a list of data values.

        Override this in your base class, if necessary. By default this
        just calls `emit` `number` times, but sometimes there are more
        performant ways of repeating your `emit` method. (E.g.: If you
        use `random.choices`, passing a `k` value to choose multiple
        items is much faster than repeating the call.)

        Args:
            number: (Optional.) An int for how many data values to
                return. The default is 1.
        """
        return [self.emit() for _ in range(0, number)]


class BaseRandomEmitter(BaseEmitter):
    """Abstract base class for defining emitters that need RNG.

    Subclass this to implement an emitter object that uses randomized
    values. In your subclass, instead of calling the `random` module
    directly, use the `rng` attribute.

    Attributes:
        rng: A random.Random object. Use this for generating random
            values in subclasses.
    """

    def reset(self) -> None:
        """Reset the emitter's RNG instance."""
        self.rng = random.Random()

    def seed_rngs(self, seed: Any) -> None:
        """Seeds all RNGs on this object with the given seed value.

        Args:
            seed: Any valid seed value you'd provide to random.seed;
                usually this is an integer.
        """
        self.rng.seed(seed)


class ChoicesEmitter(BaseRandomEmitter):

    T = TypeVar('T')

    def __init__(self,
                 items: Sequence[T],
                 weights: Optional[Sequence[Number]] = None,
                 unique: bool = False,
                 each_unique: bool = False,
                 noun: str = '') -> None:
        """Pass"""
        self.noun = noun
        self.items = items
        self.weights = weights
        self.cum_weights = None
        self.unique = unique
        self.each_unique = each_unique
        self._shuffled = None
        self._shuffled_index = None
        self.reset()

    def reset(self) -> None:
        super().reset()
        if self.weights is not None:
            nitems = len(self.items)
            nweights = len(self.weights)
            if nitems != nweights:
                raise ChoicesWeightsLengthMismatch(nitems, nweights, self.noun)
            if not (self.unique or self.each_unique):
                self.cum_weights = list(itertools.accumulate(self.weights))

        if self.unique:
            weights = self.weights or [1] * len(self.items)
            self._shuffled = weighted_shuffle(self.items, weights, self.rng)
            self._shuffled_index = 0

    def _get_next_shuffled(self, number: int = 1) -> List[T]:
        slc_start = self._shuffled_index
        slc = self._shuffled[slc_start:slc_start+number]
        self._shuffled_index += number
        return slc

    @property
    def emits_unique_values(self) -> bool:
        return self.unique

    @property
    def num_unique_values(self) -> int:
        try:
            return len(self._shuffled) - self._shuffled_index
        except TypeError:
            return len(self.items)

    def emit(self) -> T:
        if self.unique:
            if not self.num_unique_values:
                self.raise_uniqueness_violation(1)
            return self._get_next_shuffled()[0]
        if len(self.items) == 1:
            return self.items[0]
        if self.weights is None:
            return self.rng.choice(self.items)
        return self.rng.choices(self.items, cum_weights=self.cum_weights,
                                k=1)[0]

    def emit_multiple(self, number: int = 1) -> List[T]:
        if self.unique or self.each_unique:
            if number > self.num_unique_values:
                self.raise_uniqueness_violation(number)
            if self.unique:
                return self._get_next_shuffled(number)
            if self.weights is None:
                return self.rng.sample(self.items, k=number)
            return weighted_shuffle(self.items, self.weights, self.rng, number)
        if len(self.items) == 1:
            return self.items * number
        return self.rng.choices(self.items, cum_weights=self.cum_weights,
                                k=number)


class StringEmitter(BaseRandomEmitter):
    """Class for emitting random string values.

    Strings that are emitted have a random length between a
    configurable minimum and maximum number of characters, with
    optional weighting for choosing a string length. Characters are
    randomly selected from a provided alphabet, with optional weighting
    for selecting characters.

    Attributes:
        rng: Inherited from superclass. This is the random number
            generator, a random.Random instance, for this emitter.
        length_emitter: A `ChoicesEmitter` instance used to generate
            a randomized string length for each value emitted.
        alphabet_emitter: A `ChoicesEmitter` instance used to generate
            random alphabet characters.
    """

    def __init__(self,
                 length_emitter: ChoicesEmitter,
                 alphabet_emitter: ChoicesEmitter) -> None:
        """Inits StringEmitter with a length and alphabet emitter."""
        super().__init__()
        self.length_emitter = length_emitter
        self.alphabet_emitter = alphabet_emitter

    def reset(self) -> None:
        """See base class."""
        super().reset()
        self.length_emitter.reset()
        self.alphabet_emitter.reset()

    def seed_rngs(self, seed: Any) -> None:
        """See base class."""
        super().seed_rngs(seed)
        self.alphabet_emitter.seed_rngs(seed)
        self.length_emitter.seed_rngs(seed)

    def emit(self) -> str:
        """Returns a str with random characters and a random length."""
        return ''.join(self.alphabet_emitter(self.length_emitter()))

    @property
    def num_unique_values(self) -> int:
        num_unique_lengths = self.length_emitter.num_unique_values
        return self.alphabet_emitter.num_unique_values ** num_unique_lengths

    def emit_multiple(self, number: int = 1):
        """Returns multiple strs with random chars and length."""
        lengths = self.length_emitter(number)
        return [''.join(self.alphabet_emitter(length)) for length in lengths]


class TextEmitter(BaseRandomEmitter):
    """Class for emitting random text.

    "Text" in this case is defined very basically as a string of words,
    each of which is separated by a separator character or string. Text
    that this emitter produces is not formed into sentences, but you
    can use `word_sep_emitter` to produce internal punctuation.

    Attributes:
        numwords_emitter: An `IntEmitter` object used internally to
            generate a randomized number of words for each call to
            `emit`. The `numwords_mn`, `numwords_mx`, and
            `numwords_weights` values supplied to `__init__` are used
            to initialize it.
        word_emitter: A callable that takes no args and generates a
            word (str value) when called. E.g., each call to
            `word_emitter` generates a new word to use in the
            `TextEmitter.emit` return value. *If your callable
            generates words randomly, then it should be
            RandomEmitter-like, in that any RNGs should be localized
            (such as local random.Random instances), and it should have
            a `seed_rngs` method that takes a seed value and seeds all
            local RNGs.*
        word_sep_emitter: (Optional.) A callable that takes no args and
            generates a word separator (str value) when called. E.g.,
            each call to `word_sep_emitter` generates the next word
            separator to use in the `TextEmitter.emit` return value. If
            not provided, we default to using a static space (' ')
            separator value. *As with `word_emitter`, if your callable
            generates values randomly, it should be RandomEmitter-like,
            as described.*
    """

    TextPartType = Union[RandomStrEmitterLike, Callable[[], str]]

    def __init__(self,
                 word_emitter: TextPartType,
                 numwords_mn: int,
                 numwords_mx: int,
                 numwords_weights: Optional[Sequence[Number]] = None,
                 word_sep_emitter: Optional[TextPartType] = None) -> None:
        """Inits TextEmitter with word, separator, and text settings.

        The `numwords_mn`, `numwords_mx`, and `numwords_weights` args
        provided to __init__ are used to instantiate an `IntEmitter`
        that generates randomized text lengths, in numbers of words.
        If you need to access these values later, they are stored as
        attributes on that object (self.numwords_emitter).

        Note that all weights should be *cumulative* weights, e.g.
        [70, 80, 100] instead of [70, 10, 20]. An easy way to convert
        weights to cumulative weights is with itertools.accumulate:
            >>> import itertools
            >>> weights = [70, 10, 20]
            >>> list(itertools.accumulate(weights))
            [70, 80, 100]

        Args:
            word_emitter: See object attributes for details.
            numwords_mn: The minimum number of words in the generated
                text.
            numwords_mx: The maximum number of words in the generated
                text.
            numwords_weights: (Optional.) A sequence of cumulative
                weights controlling the chances a text value will be a
                certain number of words. The number of weights provided
                here should match the total number of text length
                possibilities. If not provided, weighting is not used,
                and each length has an equal chance of being selected.
            word_sep_emitter: (Optional.) See object attributes for
                details.
        """
        super().__init__()
        try:
            self.numwords_emitter = IntEmitter(numwords_mn, numwords_mx,
                                               weights=numwords_weights)
        except ChoicesWeightsLengthMismatch as err:
            noun = 'text length'
            raise ChoicesWeightsLengthMismatch(err.args[0], err.args[1], noun)
        self.word_emitter = word_emitter
        self.word_sep_emitter = word_sep_emitter

    def seed_rngs(self, seed: Any) -> None:
        """See base class."""
        self.numwords_emitter.seed_rngs(seed)
        try:
            self.word_emitter.seed_rngs(seed)
        except AttributeError:
            pass
        try:
            self.word_sep_emitter.seed_rngs(seed)
        except AttributeError:
            pass

    def emit(self) -> str:
        """Returns a text string with a random number of words.

        Object attributes control word selection, the min/max number of
        words, and what word separators are used.
        """
        numwords = self.numwords_emitter()
        words = (self.word_emitter() for _ in range(0, numwords))

        if self.word_sep_emitter is None:
            return ' '.join(words)

        separators = (self.word_sep_emitter() for _ in range(0, numwords - 1))
        text_iterable = itertools.zip_longest(words, separators, fillvalue='')
        return ''.join(itertools.chain.from_iterable(text_iterable))


class DateEmitter(BaseRandomEmitter):
    """Class for emitting random datetime.date values.

    Attributes:
        rng: Inherited from superclass. This is the random number
            generator, a random.Random instance, for this emitter.
        mn: The minimum possible datetime.date value.
        mx: (Optional.) The maximum possible datetime.date value.
            Default is today.
        weights: (Optional.) A sequence of cumulative weights to use
            when making the selection, to make certain dates relatively
            more or less likely to be picked. If provided, the number
            of weights must be equal to the total number of dates that
            may be selected. If not provided, then no weighting is
            applied, and all dates are equally likely.
        daydelta_emitter: An `IntEmitter` used internally to generate
            a random differential for date selection.
    """

    def __init__(self,
                 mn: datetime.date,
                 mx: Optional[datetime.date] = None,
                 weights: Optional[Sequence[Number]] = None) -> None:
        """Inits DateEmitter with mn, mx, and weights.

        Note that `weights` should be *cumulative* weights, e.g.
        [70, 80, 100] instead of [70, 10, 20]. An easy way to convert
        weights to cumulative weights is with itertools.accumulate:
            >>> import itertools
            >>> weights = [70, 10, 20]
            >>> list(itertools.accumulate(weights))
            [70, 80, 100]
        """
        super().__init__()
        mx = datetime.date.today() if mx is None else mx
        mx_daydelta = (mx - mn).days
        try:
            self.daydelta_emitter = IntEmitter(0, mx_daydelta, weights=weights)
        except ChoicesWeightsLengthMismatch as err:
            noun = 'day delta'
            raise ChoicesWeightsLengthMismatch(err.args[0], err.args[1], noun)
        self.mn = mn
        self.mx = mx

    def seed_rngs(self, seed: Any) -> None:
        """See base class."""
        self.daydelta_emitter.seed_rngs(seed)

    def emit(self) -> datetime.date:
        """Returns a random datetime.date value.

        Object attributes control the min/max values and weights for
        random selection.
        """
        return self.mn + datetime.timedelta(days=self.daydelta_emitter())


class TimeEmitter(BaseRandomEmitter):
    """Class for emitting random datetime.time values.

    Attributes:
        rng: Inherited from superclass. This is the random number
            generator, a random.Random instance, for this emitter.
        mn: (Optional.) The minimum possible datetime.time value.
            Default is time(0, 0, 0), or midnight.
        mx: (Optional.) The maximum possible datetime.time value.
            Default is time(23, 59, 59), or 11:59:59 PM.
        resolution: (Optional.) The "step" value (in seconds) between
            adjacent selections within your time range. E.g., a value
            of 60 would select minutes. Note that this is relative to
            your `mn` value; if you provide mn=time(0, 0, 5) and a
            resolution of 60, viable selections would be 1 minute + 5
            seconds, e.g. time(0, 1, 5), time(0, 2, 5), etc. Default
            resolution is 1, which means every second can be selected.
        weights: (Optional.) A sequence of cumulative weights to use
            when making the selection, to make certain dates relatively
            more or less likely to be picked. If provided, the number
            of weights must be equal to the total number of dates that
            may be selected. If not provided, then no weighting is
            applied, and all dates are equally likely.
        tzinfo: (Optional.) A tzinfo-compatible object to use to apply
            a timezone to the generated time. Defaults to UTC
            (datetime.timezone.utc).
        intervaldelta_emitter: An `IntEmitter` used internally to
            generate a time differential for random selection.
    """

    def __init__(self,
                 mn: Optional[datetime.time] = None,
                 mx: Optional[datetime.time] = None,
                 resolution: int = 1,
                 weights: Optional[Sequence[Number]] = None,
                 tzinfo: TzInfoLike = datetime.timezone.utc) -> None:
        """Inits TimeEmitter with mn, mx, weights, tz, and resolution.

        Note that `weights` should be *cumulative* weights, e.g.
        [70, 80, 100] instead of [70, 10, 20]. An easy way to convert
        weights to cumulative weights is with itertools.accumulate:
            >>> import itertools
            >>> weights = [70, 10, 20]
            >>> list(itertools.accumulate(weights))
            [70, 80, 100]

        When dealing with times, if you want specific time ranges to be
        weighted, you can use notation such as
        `[weight1] * interval1 + [weight2] * interval2`. E.g.:
            >>> import itertools
            >>> from datetime import time
            >>> mn = time(6, 0, 0)
            >>> mx = time(8, 59, 59)
            >>> weights = [1] * 3600 + [5] * 3600 + [20] * 3600
            >>> cum_weights = list(itertools.accumulate(weights))
            ...etc.

        In the above, our time range is a period of 3 hours (6 AM to
        9 AM). We've given all seconds from 6:00:00 to 6:59:59 a weight
        of 1; all seconds from 7:00:00 to 7:59:59 a weight of 5, and
        all seconds from 8:00:00 to 8:59:59 a weight of 20. (Adjust the
        multiplier based on your resolution -- if your resolution is
        60, you'd use a multiplier of 60 for each hour instead of
        3600.)
        """
        super().__init__()
        mn = mn or datetime.time(0, 0, 0)
        mx = mx or datetime.time(23, 59, 59)
        mn_secs = time_to_seconds(mn)
        mx_secs = time_to_seconds(mx)
        mx_intervaldelta = int((mx_secs - mn_secs) / resolution)
        try:
            self.intervaldelta_emitter = IntEmitter(0, mx_intervaldelta,
                                                    weights=weights)
        except ChoicesWeightsLengthMismatch as err:
            noun = 'time interval delta'
            raise ChoicesWeightsLengthMismatch(err.args[0], err.args[1], noun)
        self.mn = mn
        self.mx = mx
        self.resolution = resolution
        self.tzinfo = tzinfo
        self._mn_secs = mn_secs

    def seed_rngs(self, seed: Any) -> None:
        """See base class."""
        self.intervaldelta_emitter.seed_rngs(seed)

    def emit(self) -> datetime.time:
        """Returns a random, timezone aware datetime.time value.

        Object attributes control the min/max, weights, and resolution
        values for random selection, as well as the timezone of the
        returned time.
        """
        secsdelta = self.intervaldelta_emitter() * self.resolution
        secs_since_midnight = self._mn_secs + secsdelta
        return seconds_to_time(secs_since_midnight).replace(tzinfo=self.tzinfo)


# OLD CODE IS BELOW -- We want to refactor this out -------------------

class DataEmitter:
    """
    Class containing emitter methods for generating randomized data.
    """
    default_emitter_defaults = {
        'string': {'mn': 10, 'mx': 20, 'alphabet': None, 'len_weights': None},
        'text': {'mn_words': 2, 'mx_words': 10, 'mn_word_len': 1,
                 'mx_word_len': 20, 'alphabet': None, 'word_len_weights': None,
                 'phrase_len_weights': None},
        'int': {'mn': 0, 'mx': 9999999999},
        'date': {'mn': (2015, 1, 1, 0, 0), 'mx': None}
    }

    def __init__(self, alphabet=None, emitter_defaults=None):
        """
        On initialization, you can set up defaults via the two kwargs.
        If a default is NOT set here, the value(s) in the class
        attribute `default_emitter_defaults` will be used. All defaults
        can be overridden via the `emit` method.

        `alphabet` should be a list of characters that string/text
        emitter types will use by default. (This can be set separately
        for different types via `emitter_defaults`, but it's included
        as a single argument for convenience.)

        `emitter_defaults` is a nested dict that should be structured
        like the `default_emitter_defaults` class attribute. But, the
        class attribute is copied and then updated with user-provided
        overrides, so you don't have to provide the entire dictionary
        if you only want to override a few values.
        """
        user_defaults = emitter_defaults or {}
        both_defaults = {}
        for key, val in type(self).default_emitter_defaults.items():
            both_defaults[key] = val.copy()
            both_defaults[key].update(user_defaults.get(key, {}))
            if 'alphabet' in val and both_defaults[key]['alphabet'] is None:
                alphabet = alphabet or self.make_unicode_alphabet()
                both_defaults[key]['alphabet'] = alphabet
        self.emitter_defaults = both_defaults

    @staticmethod
    def make_unicode_alphabet(uchar_ranges=None):
        """
        Generate a list of characters to use for initializing a new
        DataEmitters object. Pass a nested list of tuples representing
        the character ranges to include via `char_ranges`.
        """
        if uchar_ranges is None:
            uchar_ranges = [
                (0x0021, 0x0021), (0x0023, 0x0026), (0x0028, 0x007E),
                (0x00A1, 0x00AC), (0x00AE, 0x00FF)
            ]
        return [
            chr(code) for this_range in uchar_ranges
            for code in range(this_range[0], this_range[1] + 1)
        ]

    @staticmethod
    def _choose_token_length(mn, mx, len_weights):
        len_choices = range(mn, mx + 1)
        if len_weights is None:
            return random.choice(len_choices)
        return random.choices(len_choices, cum_weights=len_weights)[0]

    def _emit_string(self, mn=0, mx=0, alphabet=None, len_weights=None):
        """
        Generate a random unicode string with length between `mn` and
        `mx`.
        """
        length = self._choose_token_length(mn, mx, len_weights)
        return ''.join(random.choice(alphabet) for _ in range(length))

    def _emit_text(self, mn_words=0, mx_words=0, mn_word_len=0,
                   mx_word_len=0, alphabet=None, word_len_weights=None,
                   phrase_len_weights=None):
        """
        Generate random unicode multi-word text.

        The number of words is between `mn_words` and `mx_words` (where
        words are separated by spaces). Each word has a length between
        `mn_word_len` and `mx_word_len`.
        """
        text_length = self._choose_token_length(mn_words, mx_words,
                                                phrase_len_weights)
        args = (mn_word_len, mx_word_len, alphabet, word_len_weights)
        words = [self._emit_string(*args) for _ in range(text_length)]
        return ' '.join(words)

    @staticmethod
    def _emit_int(mn=0, mx=0):
        """
        Generate a random int between `mn` and `mx`.
        """
        return random.randint(mn, mx)

    @staticmethod
    def _emit_date(mn=(2000, 1, 1, 0, 0), mx=None):
        """
        Generate a random UTC date between `mn` and `mx`. If `mx` is
        None, the default is now. Returns a timezone-aware
        datetime.datetime obj.
        """
        min_date = datetime.datetime(*mn, tzinfo=pytz.utc)
        if mx is None:
            max_date = datetime.datetime.now(pytz.utc)
        else:
            max_date = datetime.datetime(*mx, tzinfo=pytz.utc)
        min_td = (min_date - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc))
        max_td = (max_date - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc))
        min_ts, max_ts = min_td.total_seconds(), max_td.total_seconds()
        new_ts = min_ts + (random.random() * (max_ts - min_ts))
        new_date = datetime.datetime.utcfromtimestamp(new_ts)
        return new_date.replace(tzinfo=pytz.utc)

    @staticmethod
    def _emit_boolean():
        """
        Generate a random boolean value.
        """
        return bool(random.randint(0, 1))

    def _calculate_emitter_params(self, emtype, **user_params):
        """
        Return complete parameters for the given emitter type; default
        parameters with user_param overrides are returned.
        """
        params = self.emitter_defaults.get(emtype, {}).copy()
        params.update(user_params)
        return params

    def determine_max_unique_values(self, emtype, **user_params):
        """
        Return the maximum number of unique values possible for a given
        emitter type with the given user_params. This is mainly just so
        we can prevent infinite loops when generating unique values.
        E.g., the maximum number of unique values you can generate for
        an int range of 1 to 100 is 100, so it would be impossible to
        use those parameters for that emitter for a unique field. This
        really only applies to integers and strings. Dates and text
        values are either unlikely to repeat or unlikely ever to need
        to be unique.
        """
        params = self._calculate_emitter_params(emtype, **user_params)
        if emtype == 'int':
            return params['mx'] - params['mn'] + 1
        if emtype == 'string':
            mn, mx, alphabet = params['mn'], params['mx'], params['alphabet']
            return sum((len(alphabet) ** n for n in range(mn, mx + 1)))
        if emtype == 'boolean':
            return 2
        return None

    def emit(self, emtype, **user_params):
        """
        Generate and emit a value using the given `emtype` and
        `user_params`.
        """
        params = self._calculate_emitter_params(emtype, **user_params)
        emitter = getattr(self, f'_emit_{emtype}')
        return emitter(**params)
