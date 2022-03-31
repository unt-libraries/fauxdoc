"""Contains functions and emitters for emitting text data."""
from typing import Any, List, Optional, Sequence

from solrfixtures.emitter import EmitterGroup, RandomEmitter
from solrfixtures.typing import IntEmitterLike, StrEmitterLike


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


class Word(RandomEmitter):
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
        """Inits Word emitter with a length and alphabet emitter.

        Args:
            length_emitter: See `length_emitter` attribute.
            alphabet_emitter: See `alphabet_emitter` attribute.
            rng_seed (Optional.) See `rng_seed` attribute.
        """
        self.length_emitter = length_emitter
        self.alphabet_emitter = alphabet_emitter
        self.emitter_group = EmitterGroup(length_emitter, alphabet_emitter)
        self.rng_seed = rng_seed
        self.reset()

    def reset(self) -> None:
        """See superclass."""
        super().reset()
        self.emitter_group.setattr('rng_seed', self.rng_seed)
        self.emitter_group.do_method('reset')

    def seed(self, rng_seed: Any) -> None:
        """See superclass."""
        super().seed(rng_seed)
        self.emitter_group.do_method('seed', self.rng_seed)

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


class Text(RandomEmitter):
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
        self.emitter_group = EmitterGroup(numwords_emitter, word_emitter,
                                          sep_emitter)
        self.rng_seed = rng_seed
        self.reset()

    def reset(self) -> None:
        """See superclass."""
        super().reset()
        self.emitter_group.setattr('rng_seed', self.rng_seed)
        self.emitter_group.do_method('reset')

    def seed(self, rng_seed: Any) -> None:
        """See superclass."""
        super().seed(rng_seed)
        self.emitter_group.do_method('seed', self.rng_seed)

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
