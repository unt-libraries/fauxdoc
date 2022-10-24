"""Contains tests for the fauxdoc.emitters.text module."""
import pytest

from fauxdoc.emitters.choice import Choice
from fauxdoc.emitters.fixed import Static
from fauxdoc.emitters.text import make_alphabet, Text, Word


# Module-specific fixtures

@pytest.fixture
def auto_word_emitter():
    """Fixture to use as the `word_emitter` arg for TextEmitter tests."""
    return Word(Choice(range(2, 9)), Choice('abcde'))


@pytest.fixture
def make_wordlist_emitter():
    words = ('red', 'cat', 'sappy', 'blooming', 'flower', 'isolated', 'runway',
             'refrigerator', 'truck', 'of', 'the', 'a', 'baseless', 'bird',
             'on', 'clapping')
    weights = (5, 5, 5, 5, 5, 5, 5, 5, 5, 10, 10, 10, 5, 5, 10, 5)

    def _make_wordlist_emitter(replace_only_after_call=False):
        return Choice(words, weights,
                      replace_only_after_call=replace_only_after_call)
    return _make_wordlist_emitter


# Tests

@pytest.mark.parametrize('ranges, expected', [
    ([(0x0041, 0x0045), (0x0047, 0x0047)], list('ABCDEG')),
    ([(ord('a'), ord('g')), (ord('A'), ord('C'))],
     list('abcdefgABC'))
])
def test_makealphabet(ranges, expected):
    assert make_alphabet(ranges) == expected


@pytest.mark.parametrize(
    'seed, mn, mx, lweights, alpha, aweights, num, repeat, expected', [
        (999, 0, 0, None, 'abcde', None, 10, 0,
         ['', '', '', '', '', '', '', '', '', '']),
        (999, 1, 1, None, 'abcde', None, 10, 0,
         ['d', 'a', 'e', 'c', 'c', 'a', 'd', 'b', 'd', 'e']),
        (999, 5, 5, None, 'abcde', None, 10, 0,
         ['daecc', 'adbde', 'aeabc', 'dbeeb', 'daabe', 'cadae', 'cecdd',
          'adcdb', 'aebdb', 'cadca']),
        (999, 5, 5, None, 'abcde', None, None, 10,
         ['daecc', 'adbde', 'aeabc', 'dbeeb', 'daabe', 'cadae', 'cecdd',
          'adcdb', 'aebdb', 'cadca']),
        (999, 5, 5, None, 'a', None, 10, 0,
         ['aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa',
          'aaaaa', 'aaaaa', 'aaaaa']),
        (999, 1, 5, None, 'abcde', None, 10, 0,
         ['daec', 'c', 'adbde', 'aea', 'bcd', 'b', 'eebd', 'aa', 'beca',
          'daece']),
        (999, 1, 5, [15, 70, 5, 5, 5], 'abcde', None, 10, 0,
         ['da', 'e', 'cca', 'db', 'de', 'a', 'ea', 'bc', 'db', 'ee']),
        (999, 1, 5, [15, 70, 5, 5, 5], 'abcde', None, None, 10,
         ['da', 'e', 'cca', 'db', 'de', 'a', 'de', 'ae', 'ad', 'bd']),
        (999, 1, 5, [15, 70, 5, 5, 5], 'abcde', [20, 5, 15, 40, 20], 10, 0,
         ['da', 'e', 'dda', 'dc', 'de', 'a', 'ea', 'cd', 'dc', 'ee']),
        (999, 1, 5, None, 'abcde', [20, 5, 15, 40, 20], 10, 0,
         ['daed', 'd', 'adcde', 'aea', 'cdd', 'c', 'eebd', 'aa', 'beda',
          'daede']),
    ]
)
def test_word_emit(seed, mn, mx, lweights, alpha, aweights, num, repeat,
                   expected):
    length_emitter = Choice(range(mn, mx + 1), lweights)
    alphabet_emitter = Choice(alpha, aweights)
    we = Word(length_emitter, alphabet_emitter, rng_seed=seed)
    result = [we(num) for _ in range(repeat)] if repeat else we(num)
    assert result == expected


@pytest.mark.parametrize('len_choices, alphabet, exp_num_unique', [
    ([1], 'abcde', 5),
    ([2], 'abcde', 25),
    ([3], 'abcde', 125),
    ([4], 'abcde', 625),
    ([1, 2, 3, 4], 'abcde', 5 + 25 + 125 + 625),
    ([3, 1], 'abcde', 125 + 5),
])
def test_word_unique_properties(len_choices, alphabet, exp_num_unique):
    length_emitter = Choice(len_choices)
    alphabet_emitter = Choice(alphabet)
    we = Word(length_emitter, alphabet_emitter)
    assert we.num_unique_values == exp_num_unique
    assert not we.emits_unique_values


@pytest.mark.parametrize(
    'seed, word_mn, word_mx, word_weights, sep_chars, sep_weights, num, '
    'repeat, expected', [
        (999, 1, 3, None, None, None, 6, 0,
         ['daeccad bd eaeabcdb', 'eebdaa', 'becad ae cecddad', 'cdba ebdbcad',
          'caecabd bc', 'bbceeeac']),
        (999, 1, 3, None, None, None, None, 6,
         ['daeccad bd eaeabcdb', 'eebdaa', 'becad aecec ddadcdba',
          'ebdbca dcaeca bdbcbb', 'ceeeacd ceeabb dadeacd', 'edb aeacaecc']),
        (999, 3, 6, None, None, None, 6, 0,
         ['daeccad bd eaeabcdb eebdaa becad ae', 'cecddad cdba ebdbcad',
          'caecabd bc bbceeeac dce eab bdade',
          'acdedb aea caeccaed abceeced bac', 'ebcbdb dc ba ded',
          'cdbbdbab bdbed dad']),
        (999, 3, 6, None, [' ', '-', ', ', '; '], [40, 30, 20, 10], 6, 0,
         ['daeccad, bd eaeabcdb, eebdaa-becad-ae', 'cecddad cdba, ebdbcad',
          'caecabd bc, bbceeeac, dce eab; bdade',
          'acdedb aea caeccaed-abceeced, bac', 'ebcbdb dc, ba; ded',
          'cdbbdbab bdbed-dad']),
        (999, 3, 6, None, [' ', '-', ', ', '; '], [40, 30, 20, 10], None, 6,
         ['daeccad, bd eaeabcdb', 'eebdaa, becad-ae-cecddad cdba, ebdbcad',
          'caecabd bc, bbceeeac, dce eab; bdade',
          'acdedb aea caeccaed-abceeced', 'bac, ebcbdb dc, ba; ded',
          'cdbbdbab bdbed-dad']),
        (999, 1, 3, [60, 25, 15], None, None, 6, 0,
         ['daeccad bd', 'eaeabcdb', 'eebdaa becad ae', 'cecddad', 'cdba',
          'ebdbcad']),
    ]
)
def test_text_emit_generated_words(seed, word_mn, word_mx, word_weights,
                                   sep_chars, sep_weights, num, repeat,
                                   expected, auto_word_emitter):
    sep_emitter = None
    if sep_chars is not None:
        sep_emitter = Choice(sep_chars, sep_weights)
    te = Text(
        Choice(range(word_mn, word_mx + 1), word_weights),
        auto_word_emitter,
        sep_emitter,
        rng_seed=seed
    )
    result = [te(num) for _ in range(repeat)] if repeat else te(num)
    assert result == expected


@pytest.mark.parametrize(
    'seed, word_mn, word_mx, unique, num, repeat, expected', [
        (999, 1, 3, False, 10, 0,
         ['baseless cat on', 'the', 'of, sappy baseless', 'runway baseless',
          'bird cat', 'clapping', 'blooming isolated the', 'a',
          'isolated on-clapping', 'flower the: cat']),
        (999, 1, 3, False, None, 10,
         ['baseless cat on', 'the', 'of, sappy baseless',
          'runway baseless bird', 'cat clapping blooming', 'isolated the',
          'a-isolated', 'on', 'clapping flower: the', 'cat red']),
        (999, 3, 6, False, 10, 0,
         ['baseless cat on, the of sappy', 'baseless runway baseless',
          'bird cat clapping-blooming isolated: the',
          'a isolated on clapping flower', 'the cat, red: flower',
          'clapping of blooming', 'a blooming on the; on of', 'a a sappy a',
          'of, a flower, sappy bird flower',
          'baseless isolated of red baseless of']),
        (999, 3, 10, True, 10, 0,
         ['a of sappy, runway truck red on clapping blooming',
          'flower refrigerator-the',
          'bird baseless: isolated cat a of sappy runway, truck',
          'red: on clapping blooming flower refrigerator the',
          'bird; baseless isolated cat a of', 'sappy, runway truck, red',
          'on clapping blooming flower refrigerator the bird baseless '
          'isolated',
          'cat a-of sappy runway',
          'truck red on clapping blooming flower refrigerator, the bird',
          'baseless isolated cat baseless cat on the of sappy']),
    ]
)
def test_text_emit_words_list(seed, word_mn, word_mx, unique, num, repeat,
                              expected, make_wordlist_emitter):
    sep_emitter = Choice((' ', '-', ', ', '; ', ': '), [80, 5, 10, 3, 2])
    te = Text(
        Choice(range(word_mn, word_mx + 1)),
        make_wordlist_emitter(unique),
        sep_emitter,
        rng_seed=seed
    )
    result = [te(num) for _ in range(repeat)] if repeat else te(num)
    print(result)
    assert result == expected


@pytest.mark.parametrize(
    'word_emitter, sep_choices, numwords_choices, exp_unique_vals', [
        (Word(Static(1), Choice('abcde')), None, [1], 5),
        (Word(Static(1), Choice('abcde')), [' '], [1], 5),
        (Word(Static(2), Choice('abcde')), None, [1], 25),
        (Word(Static(2), Choice('abcde')), [' '], [1], 25),
        (Word(Choice([1, 2, 3]), Choice('abcde')), [' '], [1], 5 + 25 + 125),
        (Word(Choice([1, 3]), Choice('abcde')), [' '], [1], 5 + 125),
        (Word(Static(2), Choice('abcde')), [' ', '-', '; '], [1], 25),
        (Word(Static(1), Choice('abcde')), [' ', '-'], [2], 25 * 2),
        (Word(Static(1), Choice('abcde')), [' ', '-', '; '], [2], 25 * 3),
        (Word(Static(1), Choice('abcde')), [' ', '-', '; '], [3], 125 * 9),
        (Word(Static(1), Choice('abcde')), [' ', '-', '; '], [2, 3],
         (25 * 3) + (125 * 9)),
        (Word(Static(1), Choice('abcde')), [' ', '-', '; '], [1, 2, 3],
         5 + (25 * 3) + (125 * 9)),
        (Word(Choice([1, 2]), Choice('abcde')), [' ', '-', '; '], [1, 2, 3],
         (5 + 25) + (((5 + 25) ** 2) * 3) + (((5 + 25) ** 3) * (3 ** 2))),
        (Choice([str(n) for n in range(100)]), [' '], [1], 100),
        (Choice([str(n) for n in range(100)]), [' '], [2], 100 ** 2),
        (Choice([str(n) for n in range(100)]), [' '], [3], 100 ** 3),
        (Choice([str(n) for n in range(100)]), [' ', '-', '; '], [3],
         (100 ** 3) * (3 ** 2)),
        (Choice([str(n) for n in range(100)]), [' ', '-', '; '], [1, 2, 3],
         100 + ((100 ** 2) * 3) + (100 ** 3) * 3 ** 2),
    ]
)
def test_text_unique_properties(word_emitter, sep_choices, numwords_choices,
                                exp_unique_vals):
    te = Text(
        Choice(numwords_choices),
        word_emitter,
        Choice(sep_choices) if sep_choices else None
    )
    assert te.num_unique_values == exp_unique_vals
    assert not te.emits_unique_values
