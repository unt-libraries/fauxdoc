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
from solrfixtures.typing import Number, IntEmitterLike, StrEmitterLike,\
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
    """Abstract base class for defining emitter objects.

    Subclass this to implement an emitter object. At this level all you
    are required to override is the `emit` method, but you should also
    look at `reset`, `emits_unique_values`, and `num_unique_values`.
    Use `__init__` to configure whatever options your emitter may need.

    The `__call__` method wraps `emit` so you can emit data values
    simply by calling the object.
    """

    T = TypeVar('T')

    def reset(self) -> None:
        """Resets state on this object.

        Override this in your subclass if your emitter stores state
        changes that may need to be reset to their initial values. (The
        subclass is responsible for tracking state, of course.) This is
        a no-op by default.
        """

    @property
    def emits_unique_values(self) -> bool:
        """Returns a bool; True if an instance emits unique values.

        We mean "unique" in terms of the lifetime of the instance, not
        a given call to `emit_multiple`. This should return True if the
        instance is guaranteed never to return a duplicate until it is
        reset.
        """
        return False

    @property
    def num_unique_values(self) -> Union[None, int]:
        """Returns an int, the number of unique values emittable.

        This number should be relative to the next `emit` call. If your
        instance is one where `emits_unique_values` is True, then this
        should return the number of unique values that remain at any
        given time. Otherwise, this should give the total number of
        unique values that can be emitted. Return None if the number is
        so high as to be effectively infinite (such as with a random
        text emitter).
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
            f"{self.num_unique_values} possible selection"
            f"{'' if self.num_unique_values == 1 else 's'}."
        )

    def __call__(self, number: Optional[int] = None) -> Union[T, List[T]]:
        """Wraps the `emit` method so that this obj is callable.

        You can control whether you get a single value or a list of
        values via the `number` arg. E.g.:
            >>> some_emitter()
            'a val'
            >>> some_emitter(1)
            ['a val']
            >>> some_emitter(2)
            ['a val', 'another val']

        Args:
            number: (Optional.) How many data values to emit. Default
                is None, which causes us to return a single value
                instead of a list.

        Returns:
            One emitted value if `number` is None, or a list of
            emitted values if `number` is an int.
        """
        if number is None:
            return self.emit(1)[0]
        return self.emit(number)

    @abstractmethod
    def emit(self, number: int) -> List[T]:
        """Returns a list of data values.

        You must override this in your subclass. It should return a
        list of generated data values.

        Args:
            number: An int; how many values to return.
        """


class BaseRandomEmitter(BaseEmitter):
    """Abstract base class for defining emitters that need RNG.

    Subclass this to implement an emitter object that uses randomized
    values. In your subclass, instead of calling the `random` module
    directly, use the `rng` attribute. Override the `seed` method if
    you have an emitter composed of multiple BaseRandomEmitters and
    need to seed multiple RNGs at once.

    Attributes:
        rng: A random.Random object. Use this for generating random
            values in subclasses.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. This value is used to reset the RNG when
            `reset` is called; it can be set to something else either
            directly or by calling `seed` and providing a new value.
            Default is None.
    """

    def __init__(self, rng_seed: Any = None) -> None:
        """Inits a BaseRandomEmitter.

        Args:
            rng_seed: See `rng_seed` attribute.
        """
        self.rng_seed = rng_seed
        self.reset()

    def reset(self) -> None:
        """Reset the emitter's RNG instance."""
        self.rng = random.Random(self.rng_seed)

    def seed(self, rng_seed: Any) -> None:
        """Seeds all RNGs on this object with the given seed value.

        Args:
            seed: Any valid seed value you'd provide to random.seed.
        """
        self.rng_seed = rng_seed
        self.rng.seed(rng_seed)


class ChoicesEmitter(BaseRandomEmitter):
    """Class for making random selections, optionally with weighting.

    This covers any kind of random choice and implements the most
    efficient algorithm available: choices with or without weights and
    choices with or without replacement (i.e. "unique" or not). You
    should use this to implement random selection within any kind of
    range; e.g. the random selection here is more efficient than
    random.randint.

    Note that "uniqueness" is NOT based on value. Your sequence of
    items may contain duplicate values; uniqueness just means that each
    item is only selected once. E.g., with the sequence ['H', 'H', 'T']
    -- in a "unique" selection, the value 'H' may appear twice.

    Attributes:
        rng: Random Number Generator, inherited from superclass.
        items: A sequence of values you wish to choose from.
        weights: (Optional.) A sequence of weights, one per item, for
            controlling the probability of selections. This *must* be
            the same length as `items`. Weights should *not* be
            cumulative. Default is None.
        cum_weights: (Optional.) Cumulative weights are calculated from
            `weights`, if provided.
        unique: (Optional.) A bool value, True if selections must be
            unique until all items are exhausted or the emitter is
            reset. Default is False.
        each_unique: (Optional.) A bool value; True if each selection
            requesting multiple items at once must have unique values
            but values may be reused for each such selection. Default
            is False. If `unique` is True, each multiple-item selection
            is already guaranteed to be unique.
        noun: (Optional.) A string representing a singular noun or
            noun-phrase that describes what each item is. Used in
            raising a more informative error if weights and items don't
            match. Default is an empty string.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. Default is None.
    """

    T = TypeVar('T')

    def __init__(self,
                 items: Sequence[T],
                 weights: Optional[Sequence[Number]] = None,
                 unique: bool = False,
                 each_unique: bool = False,
                 noun: str = '',
                 rng_seed: Any = None) -> None:
        """Inits a ChoicesEmitter with items, weights, and settings.

        Args:
            items: See `items` attribute.
            weights: (Optional.) See `weights` attribute.
            unique: (Optional.) See `unique` attribute.
            each_unique: (Optional.) See `each_unique` attribute.
            noun: (Optional.) See `noun` attribute.
            rng_seed: (Optional.) See `rng_seed` attribute.
        """
        self.items = items
        self.weights = weights
        self.cum_weights = None
        self.unique = unique
        self.each_unique = each_unique
        self.noun = noun
        self.rng_seed = rng_seed
        self._shuffled = None
        self._shuffled_index = None
        self.reset()

    def reset(self) -> None:
        """Reset state and calculated attributes.

        If `unique` is True, this resets the emitter so that it loses
        track of what has already been emitted.

        It also resets `cum_weights`.
        """
        super().reset()
        if self.weights is not None:
            nitems = len(self.items)
            nweights = len(self.weights)
            if nitems != nweights:
                raise ChoicesWeightsLengthMismatch(nitems, nweights, self.noun)
            if not (self.unique or self.each_unique):
                self.cum_weights = list(itertools.accumulate(self.weights))

        if self.unique:
            # For globally unique emitters (with replacement), it's
            # most efficient to pre-shuffle the items ONCE. Then you
            # just return the values in shuffled order as they're
            # requested. Resetting regenerates this shuffle.
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
        """Returns True if this emitter only emits unique values."""
        return self.unique

    @property
    def num_unique_values(self) -> int:
        """Returns the remaining number of unique values to be emitted.

        Use this to sanity-check an `emit` call, if any uniqueness is
        required. If `self.unique` is True, then this gives you how
        many items remain to be selected. Otherwise, it gives you the
        total number of unique items to be selected.
        """
        try:
            return len(self._shuffled) - self._shuffled_index
        except TypeError:
            return len(self.items)

    def emit(self, number: int) -> List[T]:
        """Returns a list of randomly chosen items.

        This uses the most efficient selection method possible given
        the emitter configuration and checks to ensure there are enough
        unique values available if `self.unique` or `self.each_unique`
        is True.

        Args:
            number: An int; how many items you want to choose.
        """
        if self.unique or self.each_unique:
            if number > self.num_unique_values:
                self.raise_uniqueness_violation(number)
            if self.unique:
                # Global no replacement, with/without weights.
                return self._get_next_shuffled(number)
            if self.weights is None:
                # Local no replacement, without weights.
                return self.rng.sample(self.items, k=number)
            # Local no replacement, with weights.
            return weighted_shuffle(self.items, self.weights, self.rng, number)
        # With replacement, with/without weights.
        if len(self.items) == 1:
            # No choice here.
            return list(self.items) * number
        if self.weights is None and number == 1:
            # `choice` is faster if we just need 1.
            return [self.rng.choice(self.items)]
        return self.rng.choices(self.items, cum_weights=self.cum_weights,
                                k=number)


class WordEmitter(BaseRandomEmitter):
    """Class for generating and emitting randomized words.

    Words that are emitted have a random variable length and characters
    randomly selected from an alphabet. Each of these dimensions is
    implemented via emitters that you pass to __init__.

    Attributes:
        rng: Random Number Generator, inherited from superclass.
        length_emitter: A `BaseEmitter`-like instance that emits
            integers, used to generate a randomized length for each
            emitted string.
        alphabet_emitter: A `BaseEmitter`-like instance that emits
            characters (strings), used to generate each character for
            each emitted string.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. Default is None.
    """

    def __init__(self,
                 length_emitter: IntEmitterLike,
                 alphabet_emitter: StrEmitterLike,
                 rng_seed: Any = None) -> None:
        """Inits WordEmitter with a length and alphabet emitter.

        Args:
            length_emitter: See `length_emitter` attribute.
            alphabet_emitter: See `alphabet_emitter` attribute.
            rng_seed (Optional.) See `rng_seed` attribute.
        """
        self.length_emitter = length_emitter
        self.alphabet_emitter = alphabet_emitter
        self.rng_seed = rng_seed
        self.reset()

    def reset(self) -> None:
        """See superclass."""
        super().reset()
        for attr in ('length_emitter', 'alphabet_emitter'):
            emitter = getattr(self, attr)
            try:
                emitter.rng_seed = self.rng_seed
            except AttributeError:
                pass
            emitter.reset()

    def seed(self, rng_seed: Any) -> None:
        """See superclass."""
        super().seed(rng_seed)
        for attr in ('length_emitter', 'alphabet_emitter'):
            emitter = getattr(self, attr)
            try:
                emitter.seed(rng_seed)
            except AttributeError:
                pass

    @property
    def num_unique_values(self) -> int:
        """Returns the max number of unique strs this emitter produces."""
        nlengths = self.length_emitter.num_unique_values
        nchars = self.alphabet_emitter.num_unique_values
        return sum([nchars ** i for i in range(1, nlengths + 1)])

    def emit(self, number: int) -> List[str]:
        """Returns multiple strs with random chars and length.

        Args:
            number: An int; how many strings to return.
        """
        if number == 1:
            # This is faster if we just need 1.
            return [''.join(self.alphabet_emitter(self.length_emitter()))]

        # Generating all the characters at once and then partitioning
        # them into words is faster than generating each separate word.
        lengths = self.length_emitter(number)
        chars = self.alphabet_emitter(sum(lengths))
        words = []
        char_index = 0
        for length in lengths:
            words.append(''.join(chars[char_index:char_index+length]))
            char_index += length
        return words 


class TextEmitter(BaseRandomEmitter):
    """Class for emitting random text.

    "Text" in this case is defined very basically as a string of words,
    each of which is separated by a separator character or string. Text
    that this emitter produces is not formed into sentences, but you
    can use `sep_emitter` to produce internal punctuation.

    Attributes:
        rng: Random Number Generator, inherited from superclass.
        numwords_emitter: A `BaseRandomEmitter`-like instance that
            emits integers. Used to generate the number of words for
            each emitted text value.
        word_emitter: A `BaseRandomEmitter`-like instance that emits
            words (strings.) Used to generate the list of words for
            each emitted text value.
        sep_emitter: (Optional.) A `BaseRandomEmitter`-like instance
            that emits word separator character strings, used to
            generate the characters between words. If not provided,
            words are separated by a space (' ') value.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. Default is None.
    """

    def __init__(self,
                 numwords_emitter: IntEmitterLike,
                 word_emitter: StrEmitterLike,
                 sep_emitter: Optional[StrEmitterLike] = None,
                 rng_seed: Any = None) -> None:
        """Inits TextEmitter with word, separator, and text settings.

        Args:
            numword_emitter: See `numword_emitter` attribute.
            word_emitter: See `word_emitter` attribute.
            sep_emitter: (Optional.) See `sep_emitter` attribute.
            rng_seed: (Optional.) See `rng_seed` attribute.
        """
        self.numwords_emitter = numwords_emitter
        self.word_emitter = word_emitter
        self.sep_emitter = sep_emitter
        self.rng_seed = rng_seed
        self.reset()

    def reset(self) -> None:
        """See superclass."""
        super().reset()
        for attr in ('numwords_emitter', 'word_emitter', 'sep_emitter'):
            emitter = getattr(self, attr)
            try:
                emitter.rng_seed = self.rng_seed
            except AttributeError:
                pass
            if emitter is not None:
                emitter.reset()

    def seed(self, rng_seed: Any) -> None:
        """See superclass."""
        super().seed(rng_seed)
        for attr in ('numwords_emitter', 'word_emitter', 'sep_emitter'):
            try:
                getattr(self, attr).seed(rng_seed)
            except AttributeError:
                pass

    def emit(self, number: int) -> List[str]:
        """Returns a text string with a random number of words.

        Args:
            number: An int; how many text strings to return.
        """
        texts = []
        lengths = self.numwords_emitter(number)
        total_words = sum(lengths)
        words = (word for word in self.word_emitter(total_words))
        try:
            seps = (sep for sep in self.sep_emitter(total_words - number))
        except TypeError:
            seps = (sep for sep in [])
        for length in lengths:
            if length:
                render = [next(words)]
                for _ in range(1, length):
                    render.extend([next(seps, ' '), next(words)])
                texts.append(''.join(render))
        return texts


class DateEmitter(BaseRandomEmitter):
    """Class for emitting random datetime.date values.

    Attributes:
        rng: Random Number Generator, inherited from superclass.
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
