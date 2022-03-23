"""Contains tests for the solrfixtures.emitters.text module."""
import pytest

from solrfixtures.emitters.choice import ChoicesEmitter
from solrfixtures.emitters.text import make_alphabet, TextEmitter, WordEmitter


# Module-specific fixtures

@pytest.fixture
def word_emitter():
    """Fixture to use as the `word_emitter` arg for TextEmitter tests."""
    return WordEmitter(
        ChoicesEmitter(range(2, 9)),
        ChoicesEmitter('abcde'),
    )


# Tests

@pytest.mark.parametrize('ranges, expected', [
    ([(0x0041, 0x0045), (0x0047, 0x0047)], list('ABCDEG')),
    ([(ord('a'), ord('g')), (ord('A'), ord('C'))],
     list('abcdefgABC'))
])
def test_makealphabet(ranges, expected):
    assert make_alphabet(ranges) == expected


@pytest.mark.parametrize('seed, mn, mx, lweights, alpha, aweights, expected', [
    (999, 0, 0, None, 'abcde', None, ['', '', '', '', '', '', '', '', '', '']),
    (999, 1, 1, None, 'abcde', None,
     ['d', 'a', 'e', 'c', 'c', 'a', 'd', 'b', 'd', 'e']),
    (999, 5, 5, None, 'abcde', None,
     ['daecc', 'adbde', 'aeabc', 'dbeeb', 'daabe', 'cadae', 'cecdd', 'adcdb',
      'aebdb', 'cadca']),
    (999, 5, 5, None, 'a', None,
     ['aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa',
      'aaaaa', 'aaaaa']),
    (999, 1, 5, None, 'abcde', None,
     ['daec', 'c', 'adbde', 'aea', 'bcd', 'b', 'eebd', 'aa', 'beca', 'daece']),
    (999, 1, 5, [15, 70, 5, 5, 5], 'abcde', None,
     ['da', 'e', 'cca', 'db', 'de', 'a', 'ea', 'bc', 'db', 'ee']),
    (999, 1, 5, [15, 70, 5, 5, 5], 'abcde', [20, 5, 15, 40, 20],
     ['da', 'e', 'dda', 'dc', 'de', 'a', 'ea', 'cd', 'dc', 'ee']),
    (999, 1, 5, None, 'abcde', [20, 5, 15, 40, 20],
     ['daed', 'd', 'adcde', 'aea', 'cdd', 'c', 'eebd', 'aa', 'beda', 'daede']),
])
def test_wordemitter(seed, mn, mx, lweights, alpha, aweights, expected):
    length_emitter = ChoicesEmitter(range(mn, mx + 1), lweights)
    alphabet_emitter = ChoicesEmitter(alpha, aweights)
    se = WordEmitter(length_emitter, alphabet_emitter, rng_seed=seed)
    assert se(len(expected)) == expected


@pytest.mark.parametrize(
    'seed, word_mn, word_mx, word_weights, sep_chars, sep_weights, expected',
    [
        (999, 1, 3, None, None, None,
         ['daeccad bd eaeabcdb', 'eebdaa', 'becad ae cecddad', 'cdba ebdbcad',
          'caecabd bc', 'bbceeeac']),
        (999, 3, 6, None, None, None,
         ['daeccad bd eaeabcdb eebdaa becad ae', 'cecddad cdba ebdbcad',
          'caecabd bc bbceeeac dce eab bdade',
          'acdedb aea caeccaed abceeced bac', 'ebcbdb dc ba ded',
          'cdbbdbab bdbed dad']),
        (999, 3, 6, None, [' ', '-', ', ', '; '], [40, 30, 20, 10],
         ['daeccad, bd eaeabcdb, eebdaa-becad-ae', 'cecddad cdba, ebdbcad',
          'caecabd bc, bbceeeac, dce eab; bdade',
          'acdedb aea caeccaed-abceeced, bac', 'ebcbdb dc, ba; ded',
          'cdbbdbab bdbed-dad']),
        (999, 1, 3, [60, 25, 15], None, None,
         ['daeccad bd', 'eaeabcdb', 'eebdaa becad ae', 'cecddad', 'cdba',
          'ebdbcad']),
    ]
)
def test_textemitter(seed, word_mn, word_mx, word_weights, sep_chars,
                     sep_weights, expected, word_emitter):
    sep_emitter = None
    if sep_chars is not None:
        sep_emitter = WordEmitter(
            ChoicesEmitter(range(1, 2)),
            ChoicesEmitter(sep_chars, sep_weights)
        )
    te = TextEmitter(
        ChoicesEmitter(range(word_mn, word_mx + 1), word_weights),
        word_emitter,
        sep_emitter,
        rng_seed=seed
    )
    assert te(len(expected)) == expected
