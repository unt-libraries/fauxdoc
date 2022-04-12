"""Contains functions and emitters for emitting text data."""
from typing import Any, Iterator, List, Optional, Sequence

from solrfixtures.group import ObjectMap
from solrfixtures.emitter import RandomEmitter
from solrfixtures.mathtools import clamp
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
        self._emitters = ObjectMap({})
        self.length_emitter = length_emitter
        self.alphabet_emitter = alphabet_emitter
        self.rng_seed = rng_seed
        self.reset()

    @property
    def length_emitter(self) -> IntEmitterLike:
        """Returns the 'length_emitter' attribute."""
        return self._emitters['length']

    @length_emitter.setter
    def length_emitter(self, length_emitter: IntEmitterLike) -> None:
        """Sets the 'length_emitter' attribute."""
        self._emitters['length'] = length_emitter
        self._update_num_unique_vals()

    @property
    def alphabet_emitter(self) -> None:
        """Returns the 'alphabet_emitter' attribute."""
        return self._emitters['alphabet']

    @alphabet_emitter.setter
    def alphabet_emitter(self, alphabet_emitter: StrEmitterLike) -> None:
        """Sets the 'alphabet_emitter' attribute."""
        self._emitters['alphabet'] = alphabet_emitter
        self._update_num_unique_vals()

    def _update_num_unique_vals(self) -> None:
        """Updates """
        alpha = self._emitters.get('alphabet')
        length = self._emitters.get('length')
        if alpha and length:
            nchars = alpha.num_unique_values
            nlengths = length.num_unique_values
            number = sum([nchars ** i for i in range(1, nlengths + 1)])
            self._num_unique_values = number

    def reset(self) -> None:
        """See superclass."""
        super().reset()
        self._emitters.setattr('rng_seed', self.rng_seed)
        self._emitters.do_method('reset')

    def seed(self, rng_seed: Any) -> None:
        """See superclass."""
        super().seed(rng_seed)
        self._emitters.do_method('seed', self.rng_seed)

    @property
    def num_unique_values(self) -> int:
        """Returns the max number of unique strs this emitter produces."""
        return self._num_unique_values

    def emit(self) -> str:
        """Returns one str with random chars and length."""
        return ''.join(self._emitters['alphabet'](self._emitters['length']()))

    def emit_many(self, number: int) -> List[str]:
        """Returns a list of strs, ecah with random chars and length.
        Args:
            number: See superclass.
        """
        # Generating all the characters at once and then partitioning
        # them into words is faster than generating each separate word.
        lengths = self._emitters['length'](number)
        chars = self._emitters['alphabet'](sum(lengths))
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
        self._emitters = ObjectMap({})
        self.numwords_emitter = numwords_emitter
        self.word_emitter = word_emitter
        self.sep_emitter = sep_emitter
        self.rng_seed = rng_seed
        self.reset()

    @property
    def numwords_emitter(self) -> IntEmitterLike:
        """Returns the 'numwords_emitter' attribute."""
        return self._emitters['numwords']

    @numwords_emitter.setter
    def numwords_emitter(self, numwords_emitter: IntEmitterLike):
        """Sets the 'numwords_emitter' attribute."""
        self._emitters['numwords'] = numwords_emitter

    @property
    def word_emitter(self) -> StrEmitterLike:
        """Returns the 'word_emitter' attribute."""
        return self._emitters['word']

    @word_emitter.setter
    def word_emitter(self, word_emitter: StrEmitterLike):
        """Sets the 'word_emitter' attribute."""
        self._emitters['word'] = word_emitter

    @property
    def sep_emitter(self) -> StrEmitterLike:
        """Returns the 'sep_emitter' attribute."""
        return self._emitters['sep']

    @sep_emitter.setter
    def sep_emitter(self, sep_emitter: StrEmitterLike):
        """Sets the 'sep_emitter' attribute."""
        self._emitters['sep'] = sep_emitter

    def reset(self) -> None:
        """See superclass."""
        super().reset()
        self._emitters.setattr('rng_seed', self.rng_seed)
        self._emitters.do_method('reset')

    def seed(self, rng_seed: Any) -> None:
        """See superclass."""
        super().seed(rng_seed)
        self._emitters.do_method('seed', self.rng_seed)

    def _get_words_iterator(self, total: int) -> Iterator:
        """Creates an iterator/generator for generating words."""

        # This addresses the edge case where the word_emitter for this
        # is a list of words (e.g. implemented via a Choice object),
        # where `each_unique` is True -- the expectation is that each
        # set of words emitted will contain unique words, but each word
        # can appear in multiple sets. (Each text value is essentially
        # a set of words.) If we generated text values one at a time,
        # this would be trivial. But, instead, we generate all words at
        # once and then divide them out into text values they belong
        # to, because this is way more performant. In order to address
        # the each_unique edge case, we create a generator that resets
        # the word_emitter each time it runs out of words; thus, words
        # are reused, but each word appears only after all words have
        # been emitted. Text values generated that way don't guarantee
        # totally unique sets of words, since words might repeat if a
        # `reset` call happens in the middle of a set of words, but
        # this is about the best we can do I think.

        num_unique = self._emitters['word'].num_unique_values
        each_unique = getattr(self._emitters['word'], 'each_unique', False)
        if each_unique and total > num_unique:
            def generator():
                remainder = total
                while remainder > 0:
                    needed = clamp(num_unique, mx=remainder)
                    for word in self._emitters['word'](needed):
                        yield word
                    self._emitters['word'].reset()
                    remainder -= needed
            return generator()
        return iter(self._emitters['word'](total))

    def emit(self) -> str:
        """Returns one text str with a random # of words."""
        return self.emit_many(1)[0]

    def emit_many(self, number: int) -> List[str]:
        """Returns a list of text strs with random #s of words.

        Args:
            number: See superclass.
        """
        texts = []
        lengths = self._emitters['numwords'](number)
        total_words = sum(lengths)
        words = self._get_words_iterator(total_words)
        try:
            seps = iter(self._emitters['sep'](total_words - number))
        except TypeError:
            seps = iter([])
        for length in lengths:
            if length:
                render = [next(words)]
                for _ in range(1, length):
                    render.extend([next(seps, ' '), next(words)])
                texts.append(''.join(render))
        return texts
