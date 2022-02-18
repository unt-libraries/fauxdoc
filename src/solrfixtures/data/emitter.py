"""Contains functions and classes for emitting randomized data values."""
from abc import ABC, abstractmethod
import datetime
import random
from typing import Any, Optional, List, Sequence, Union

import pytz

from .exceptions import ChoicesWeightsLengthMismatch


Number = Union[int, float]


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

    def __call__(self) -> Any:
        """Wraps the `self.emit` method so that this obj is callable."""
        return self.emit()

    @abstractmethod
    def emit(self) -> Any:
        """Returns an atomic data value of a certain type.

        Override this in your base class. It should return whatever
        value is appropriate given your emitter class.
        """


class BaseRandomEmitter(BaseEmitter):
    """Abstract base class for defining emitters that need RNG.

    Subclass this to implement an emitter object that uses randomized
    values. In your subclass, instead of calling the `random` module
    directly, use the `rng` attribute.

    This also adds a private utility method for validating args when
    you need to use random.choices, which is common.

    Attributes:
        rng: A random.Random object. Use this for generating random
            values in subclasses.
    """
    
    def __init__(self) -> None:
        """Inits the emitter with a new RNG instance."""
        self.rng = random.Random()

    @staticmethod
    def _check_choices_against_weights(num_choices: int,
                                       num_weights: int,
                                       noun: str = '') -> None:
        """Validates a number of choices against a number of weights.

        When calling self.rng.choices with optional weights args, it
        will raise an error if the number of choices and number of
        weights don't match. Use this to validate those args ahead of
        time, such as during __init__.

        Raises:
            solrfixtures.data.exceptions.ChoicesWeightsLengthMismatch:
                If the number of choices and weights don't match.
        """
        if num_choices != num_weights:
            raise ChoicesWeightsLengthMismatch(num_choices, num_weights, noun)


class IntEmitter(BaseRandomEmitter):
    """Class for picking and emitting random integer values.

    Attributes:
        rng: Inherited from superclass. This is the random number
            generator, a random.Random instance, for this emitter.
        mn: The minimum possible random integer to pick.
        mx: The maximum possible random integer to pick.
        weights: (Optional.) A sequence of cumulative weights to use
            when making the selection, to make certain integers
            relatively more or less likely to be picked. If provided,
            the number of weights must be equal to the total number of
            integers that may be selected. If not provided, then no
            weighting is applied, and all integers are equally likely.
    """

    def __init__(self,
                 mn: int,
                 mx: int,
                 weights: Optional[Sequence[Number]] = None) -> None:
        """Inits IntEmitter with mn, mx, and weights.

        Note that `weights` should be the *cumulative* weights, e.g.
        [70, 80, 100] instead of [70, 10, 20]. An easy way to convert
        weights to cumulative weights is with itertools.accumulate:
            >>> import itertools
            >>> weights = [70, 10, 20]
            >>> list(itertools.accumulate(weights))
            [70, 80, 100]
        """
        super().__init__()
        if weights is not None:
            self._check_choices_against_weights(mx - mn + 1, len(weights),
                                                'integer')
        self.mn = mn
        self.mx = mx
        self.weights = weights

    def emit(self) -> int:
        """Returns a random integer.

        Object attributes control the min/max range and weighting for
        generated values.
        """
        if self.weights is None:
            return self.rng.randint(self.mn, self.mx)
        return self.rng.choices(range(self.mn, self.mx + 1),
                                cum_weights=self.weights)[0]


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
        alphabet: A sequence of characters to use when generating
            strings.
        alphabet_weights: (Optional.) A sequence of cumulative weights
            controlling the chances that each alphabet character will
            selected during string generation. The number of weights
            must match the number of characters in `alphabet`. If not
            provided, weighting is not used, and each character is
            equally likely to be selected.
        len_emitter: An `IntEmitter` object used internally to generate
            a randomized string length for each call to `emit`. The
            `len_mn`, `len_mx`, and `len_weights` values supplied to
            `__init__` are used to initialize it.
    """

    def __init__(self,
                 len_mn: int,
                 len_mx: int,
                 alphabet: Sequence[str],
                 len_weights: Optional[Sequence[Number]] = None,
                 alphabet_weights: Optional[Sequence[Number]] = None) -> None:
        """Inits StringEmitter with an alphabet and len_emitter.

        The `len_mn`, `len_mx`, and `len_weights` args provided to
        __init__ are used to instantiate an `IntEmitter` that generates
        randomized string lengths. They are stored as attributes on
        that object.

        Note that all weights should be the *cumulative* weights, e.g.
        [70, 80, 100] instead of [70, 10, 20]. An easy way to convert
        weights to cumulative weights is with itertools.accumulate:
            >>> import itertools
            >>> weights = [70, 10, 20]
            >>> list(itertools.accumulate(weights))
            [70, 80, 100]

        Args:
            len_mn: The minimum length for generated strings.
            len_mx: The maximum length for generated strings.
            alphabet: See attributes for this class.
            len_weights: (Optional.) A sequence of cumulative weights
                controlling the chances a string will be a certain
                length. The number of weights provided here should
                match the total number of string length possibilities.
                If not provided, weighting is not used, and each string
                length has an equal chance of being selected.
            alphabet_weights: (Optional.) See attributes for this
                class.
        """
        super().__init__()
        try:
            self.len_emitter = IntEmitter(len_mn, len_mx, weights=len_weights)
        except ChoicesWeightsLengthMismatch as err:
            noun = 'string length'
            raise ChoicesWeightsLengthMismatch(err.args[0], err.args[1], noun)
        if alphabet_weights is not None:
            self._check_choices_against_weights(len(alphabet),
                                                len(alphabet_weights),
                                                'alphabet character')
        self.alphabet = alphabet
        self.alphabet_weights = alphabet_weights

    def emit(self) -> str:
        """Returns a str with random characters and a random length.

        Object attributes control the min/max number of characters, the
        alphabet used to generate the string, and the weighting for
        the distribution of string lengths and characters.
        """
        chosen = self.rng.choices(self.alphabet,
                                  cum_weights=self.alphabet_weights,
                                  k=self.len_emitter())
        return ''.join(chosen)


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
