"""Contains functions and emitters for emitting text data."""
from typing import Any, Generator, Iterator, List, Optional, Sequence, Tuple

from fauxdoc.emitter import Emitter
from fauxdoc.emitters import Static
from fauxdoc.mathtools import clamp
from fauxdoc.mixins import RandomWithChildrenMixin
from fauxdoc.typing import EmitterLike


def make_alphabet(uchar_ranges: Optional[Sequence[Tuple[int, int]]] = None
                  ) -> List[str]:
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


class Word(RandomWithChildrenMixin, Emitter[str]):
    """Class for generating and emitting randomized words.

    Words that are emitted have a random variable length and characters
    randomly selected from an alphabet. Each of these dimensions is
    implemented via emitters that you pass to __init__.

    Note about uniqueness: I have not implemented a way to ensure
    uniqueness for this emitter, mainly because the best implementation
    for this depends on the number of possible combinations your
    alphabet and range of lengths would produce. If you need unique
    words, I'd recommend one of these options:

        1) Emit values into a set and stop once you have enough unique
        values. This works well for high cardinality emitters that are
        less likely to emit duplicate values. Be aware -- even modest-
        seeming Word emitters can be very high cardinality. One that
        can emit between 2 and 10 letter words using a 26-character
        alphabet gives you 146,813,779,479,484 possible combinations.
        (Though, heavily weighting fewer lengths or characters
        increases the chance for duplication, so you may have to
        experiment.)

        2) If you have a smaller set of possible unique values, I'd
        suggest using a choices.Choice emitter without replacement,
        where you explicitly initialize the emitter with your desired
        vocabulary words.

    Attributes:
        rng: Random Number Generator, inherited from superclass.
        length_emitter: An `Emitter`-like instance that emits integers,
            used to generate a random length for each emitted string.
            It should emit infinite values.
        alphabet_emitter: A `Emitter`-like instance that emits
            characters (strings), used to generate each character for
            each emitted string. It should emit infinite values.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. Default is None.
    """

    def __init__(self,
                 length_emitter: EmitterLike[int],
                 alphabet_emitter: EmitterLike[str],
                 rng_seed: Any = None) -> None:
        """Inits Word emitter with a length and alphabet emitter.

        Args:
            length_emitter: See `length_emitter` attribute.
            alphabet_emitter: See `alphabet_emitter` attribute.
            rng_seed (Optional.) See `rng_seed` attribute.
        """
        super().__init__(children={
            'length': length_emitter,
            'alphabet': alphabet_emitter
        }, rng_seed=rng_seed)
        self._update_num_unique_vals()

    @property
    def length_emitter(self) -> EmitterLike[int]:
        """Returns the 'length_emitter' attribute."""
        return self._emitters['length']

    @property
    def alphabet_emitter(self) -> EmitterLike[str]:
        """Returns the 'alphabet_emitter' attribute."""
        return self._emitters['alphabet']

    def _update_num_unique_vals(self) -> None:
        """Updates the cached number of unique values this can emit."""
        self._num_unique_values: Optional[int] = None
        nchars = self._emitters['alphabet'].num_unique_values
        if nchars is not None and hasattr(self._emitters['length'], 'items'):
            poss_items = self._emitters['length'].items
            self._num_unique_values = sum([nchars ** i for i in poss_items])

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
    def num_unique_values(self) -> Optional[int]:
        """Returns the max number of unique values this can emit."""
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


class Text(RandomWithChildrenMixin, Emitter[str]):
    """Class for emitting random text.

    "Text" in this case is defined very basically as a string of words,
    each of which is separated by a separator character or string. Text
    that this emitter produces is not formed into sentences, but you
    can use `sep_emitter` to produce internal punctuation.

    Attributes:
        rng: Random Number Generator, inherited from superclass.
        numwords_emitter: An `Emitter`-like instance that emits
            integers. Used to generate the number of words for each
            emitted text value. This should emit infinite values.
        word_emitter: An `Emitter`-like instance that emits words
            (strings.) Used to generate the list of words for each
            emitted text value. This should emit infinite values.
        sep_emitter: An `Emitter`-like instance that emits word
            separator character strings, used to generate characters
            between words.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. Default is None.
    """

    def __init__(self,
                 numwords_emitter: EmitterLike[int],
                 word_emitter: EmitterLike[str],
                 sep_emitter: Optional[EmitterLike[str]] = None,
                 rng_seed: Any = None) -> None:
        """Inits TextEmitter with word, separator, and text settings.

        Args:
            numwords_emitter: See `numwords_emitter` attribute.
            word_emitter: See `word_emitter` attribute.
            sep_emitter: (Optional.) See `sep_emitter` attribute.
                Defaults to a Static emitter that emits a space (' ').
            rng_seed: (Optional.) See `rng_seed` attribute.
        """
        super().__init__(children={
            'numwords': numwords_emitter,
            'word': word_emitter,
            'sep': sep_emitter or Static(' ')
        }, rng_seed=rng_seed)
        self._update_num_unique_vals()

    @property
    def numwords_emitter(self) -> EmitterLike[int]:
        """Returns the 'numwords_emitter' attribute."""
        return self._emitters['numwords']

    @property
    def word_emitter(self) -> EmitterLike[str]:
        """Returns the 'word_emitter' attribute."""
        return self._emitters['word']

    @property
    def sep_emitter(self) -> EmitterLike[str]:
        """Returns the 'sep_emitter' attribute."""
        return self._emitters['sep']

    def _update_num_unique_vals(self) -> None:
        """Updates the cached number of unique values this can emit."""
        self._num_unique_values: Optional[int] = None
        numwords = self._emitters['numwords']
        word_em_has_uv = self._emitters['word'].num_unique_values is not None
        sep_em_has_uv = self._emitters['sep'].num_unique_values is not None
        if word_em_has_uv and sep_em_has_uv and hasattr(numwords, 'items'):
            nums: List[int] = []
            for length in numwords.items:
                n_uw = self._emitters['word'].num_unique_values ** length
                n_us = self._emitters['sep'].num_unique_values ** (length - 1)
                nums.append(n_uw * n_us)
            self._num_unique_values = sum(nums)

    @property
    def num_unique_values(self) -> Optional[int]:
        """Returns the max number of unique values this can produce."""
        return self._num_unique_values

    def reset(self) -> None:
        """See superclass."""
        super().reset()
        self._emitters.setattr('rng_seed', self.rng_seed)
        self._emitters.do_method('reset')

    def seed(self, rng_seed: Any) -> None:
        """See superclass."""
        super().seed(rng_seed)
        self._emitters.do_method('seed', self.rng_seed)

    def _get_words_iterator(self, total: int) -> Iterator[str]:
        """Creates an iterator/generator for generating words."""

        # This addresses the edge case where the word_emitter for this
        # is a list of words (e.g. implemented via a Choice object),
        # where `replace_only_after_call` is True -- the expectation is
        # that each set of words emitted will contain unique words, but
        # each word can appear in multiple sets, where each text value
        # is a set of words. If we generated text values one at a time,
        # this would be trivial. But, instead, we generate all words at
        # once and then divide them out into text values they belong
        # to, because this is way more performant. In order to address
        # this edge case, we create a generator that resets the
        # word_emitter each time it runs out of words; thus, words are
        # reused, but each word appears only after all words have been
        # emitted. Text values generated that way don't guarantee
        # totally unique sets of words, since words might repeat if a
        # `reset` call happens in the middle of a set of words, but
        # this is about the best we can do I think.

        if getattr(self._emitters['word'], 'replace_only_after_call', False):
            num_unique = self._emitters['word'].num_unique_values or 0
            if num_unique and total > num_unique:
                def generator() -> Generator[str, None, None]:
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
        seps = iter(self._emitters['sep'](total_words - number))
        for length in lengths:
            if length:
                render = [next(words)]
                for _ in range(1, length):
                    render.extend([next(seps, ' '), next(words)])
                texts.append(''.join(render))
        return texts
