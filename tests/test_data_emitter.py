"""Contains tests for the solrfixtures.data.emitter module."""
import pytest

from solrfixtures.data import emitter as em
from solrfixtures.data import exceptions as ex


# Module-specific fixtures

@pytest.fixture
def word_emitter():
    """Fixture to use as the `word_emitter` arg for TextEmitter tests."""
    return em.StringEmitter(2, 8, 'abcde')


# Tests

@pytest.mark.parametrize('ranges, expected', [
    ([(0x0041, 0x0045), (0x0047, 0x0047)], list('ABCDEG')),
    ([(ord('a'), ord('g')), (ord('A'), ord('C'))],
     list('abcdefgABC'))
])
def test_makealphabet(ranges, expected):
    assert em.make_alphabet(ranges) == expected


@pytest.mark.parametrize('seed, mn, mx, weights, expected', [
    (999, 1, 10, None, [2, 10, 10, 9, 8, 8, 3, 6, 2, 4]),
    (999, 1, 10, [50, 70, 80, 85, 90, 91, 92, 93, 95, 100],
     [3, 1, 5, 2, 1, 1, 3, 1, 3, 4]),
])
def test_intemitter(seed, mn, mx, weights, expected):
    ie = em.IntEmitter(mn, mx, weights=weights)
    ie.rng.seed(seed)
    assert [ie() for _ in expected] == expected


@pytest.mark.parametrize('mn, mx, weights', [
    (1, 10, [50, 100]),
    (1, 2, [50, 75, 100])
])
def test_intemitter_incorrect_weights(mn, mx, weights):
    with pytest.raises(ex.ChoicesWeightsLengthMismatch) as excinfo:
        em.IntEmitter(mn, mx, weights=weights)
    assert excinfo.value.noun == 'integer'
    assert excinfo.value.num_choices == mx - mn + 1
    assert excinfo.value.num_weights == len(weights)


@pytest.mark.parametrize('seed, mn, mx, lweights, alpha, aweights, expected', [
    (999, 1, 5, None, 'abcde', None,
     ['d', 'aecca', 'dbdea', 'eabcd', 'beeb', 'daab', 'ec', 'ada', 'e', 'ce']),
    (999, 1, 5, [15, 85, 90, 95, 100], 'abcde', None,
     ['da', 'e', 'cca', 'db', 'de', 'a', 'ea', 'bc', 'db', 'ee']),
    (999, 1, 5, [15, 85, 90, 95, 100], 'abcde', [20, 25, 40, 80, 100],
     ['da', 'e', 'dda', 'dc', 'de', 'a', 'ea', 'cd', 'dc', 'ee']),
    (999, 1, 5, None, 'abcde', [20, 25, 40, 80, 100],
     ['d', 'aedda', 'dcdea', 'eacdd', 'ceeb', 'daab', 'ed', 'ada', 'e', 'de']),
])
def test_stringemitter(seed, mn, mx, lweights, alpha, aweights, expected):
    se = em.StringEmitter(mn, mx, alpha, len_weights=lweights,
                          alphabet_weights=aweights)
    se.rng.seed(seed)
    se.len_emitter.rng.seed(seed)
    assert [se() for _ in expected] == expected


@pytest.mark.parametrize('alpha, aweights', [
    ('abcde', [50, 100]),
    ('abc', [50, 60, 70, 80, 100]),
])
def test_stringemitter_incorrect_alpha_weights(alpha, aweights):
    with pytest.raises(ex.ChoicesWeightsLengthMismatch) as excinfo:
        em.StringEmitter(1, 5, alpha, alphabet_weights=aweights)
    assert excinfo.value.noun == 'alphabet character'
    assert excinfo.value.num_choices == len(alpha)
    assert excinfo.value.num_weights == len(aweights)


@pytest.mark.parametrize('mn, mx, lweights', [
    (1, 10, [50, 100]),
    (1, 2, [50, 75, 100]),
])
def test_stringemitter_incorrect_string_length_weights(mn, mx, lweights):
    with pytest.raises(ex.ChoicesWeightsLengthMismatch) as excinfo:
        em.StringEmitter(mn, mx, 'abcde', len_weights=lweights)
    assert excinfo.value.noun == 'string length'
    assert excinfo.value.num_choices == mx - mn + 1
    assert excinfo.value.num_weights == len(lweights)


@pytest.mark.parametrize(
    'seed, word_mn, word_mx, word_weights, sep_chars, sep_weights, expected',
    [
        (999, 1, 3, None, None, None,
         ['daeccadb deaeabc db', 'eebdaabe', 'cadaec ecddad cdbaeb',
          'dbcad caeca bdb', 'cbbceeea cdceeab bdad', 'eacdedb aeacaecc']),
        (999, 3, 6, None, None, None,
         ['daeccadb deaeabc db', 'eebdaabe cadaec ecddad cdbaeb dbcad caeca',
          'bdb cbbceeea cdceeab bdad eacdedb aeacaecc',
          'aedabce ecedbace bcbdbdcb ad', 'edcdbbd babbdbed dad ddc bced',
          'adeeda bb bdeaecd']),
        (999, 3, 6, None, [' ', '-', ', ', '; '], [40, 70, 90, 100],
         ['daeccadb, deaeabc db',
          'eebdaabe, cadaec-ecddad-cdbaeb dbcad, caeca',
          'bdb cbbceeea, cdceeab, bdad eacdedb; aeacaecc',
          'aedabce ecedbace bcbdbdcb-ad', 'edcdbbd, babbdbed dad, ddc; bced',
          'adeeda bb-bdeaecd']),
        (999, 1, 3, [60, 85, 100], None, None,
         ['daeccadb deaeabc', 'db', 'eebdaabe cadaec ecddad', 'cdbaeb',
          'dbcad', 'caeca']),
    ]
)
def test_textemitter(seed, word_mn, word_mx, word_weights, sep_chars,
                     sep_weights, expected, word_emitter):
    wse = None
    if sep_chars is not None:
        wse = em.StringEmitter(1, 1, sep_chars, alphabet_weights=sep_weights)
        wse.rng.seed(seed)
    te = em.TextEmitter(word_emitter, word_mn, word_mx,
                        numwords_weights=word_weights, word_sep_emitter=wse)
    te.word_emitter.rng.seed(seed)
    te.word_emitter.len_emitter.rng.seed(seed)
    te.numwords_emitter.rng.seed(seed)
    assert [te() for _ in expected] == expected


@pytest.mark.parametrize('word_mn, word_mx, word_weights', [
    (1, 10, [50, 100]),
    (1, 2, [50, 75, 100]),
])
def test_textemitter_incorrect_word_weights(word_mn, word_mx, word_weights,
                                            word_emitter):
    with pytest.raises(ex.ChoicesWeightsLengthMismatch) as excinfo:
        em.TextEmitter(word_emitter, word_mn, word_mx,
                       numwords_weights=word_weights)
    assert excinfo.value.noun == 'text length'
    assert excinfo.value.num_choices == word_mx - word_mn + 1
    assert excinfo.value.num_weights == len(word_weights)
