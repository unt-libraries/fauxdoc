"""Contains tests for the solrfixtures.data.emitter module."""
import datetime
import itertools

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
    (999, 0, 1, None, [0, 1, 1, 0, 1, 0, 0, 0, 1, 0]),
    (999, 1, 1, None, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (999, 5, 5, None, [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]),
    (999, 1, 10, None, [2, 10, 10, 9, 8, 8, 3, 6, 2, 4]),
    (999, 1, 10, [50, 70, 80, 85, 90, 91, 92, 93, 95, 100],
     [3, 1, 5, 2, 1, 1, 3, 1, 3, 4]),
])
def test_intemitter(seed, mn, mx, weights, expected):
    ie = em.IntEmitter(mn, mx, weights=weights)
    ie.seed_rngs(seed)
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
    se.seed_rngs(seed)
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
    te = em.TextEmitter(word_emitter, word_mn, word_mx,
                        numwords_weights=word_weights, word_sep_emitter=wse)
    te.seed_rngs(seed)
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


@pytest.mark.parametrize('seed, mn, mx, weights, expected', [
    (999, (2015, 1, 1), (2015, 1, 1), None,
     [(2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1),
      (2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1)]),
    (999, (2015, 1, 1), (2015, 1, 5), None,
     [(2015, 1, 1), (2015, 1, 5), (2015, 1, 5), (2015, 1, 5), (2015, 1, 4),
      (2015, 1, 4), (2015, 1, 2), (2015, 1, 3), (2015, 1, 1), (2015, 1, 2)]),
    (999, (2015, 1, 1), (2015, 1, 5), [60, 80, 90, 95, 100],
     [(2015, 1, 2), (2015, 1, 1), (2015, 1, 3), (2015, 1, 1), (2015, 1, 1),
      (2015, 1, 1), (2015, 1, 2), (2015, 1, 1), (2015, 1, 2), (2015, 1, 3)]),
])
def test_dateemitter(seed, mn, mx, weights, expected):
    mn = datetime.date(*mn)
    mx = datetime.date(*mx)
    de = em.DateEmitter(mn, mx, weights=weights)
    de.seed_rngs(seed)
    assert [de() for _ in expected] == [datetime.date(*i) for i in expected]


@pytest.mark.parametrize('mn, mx, weights', [
    ((2015, 1, 1), (2015, 1, 2), [60, 80, 100]),
    ((2015, 1, 1), (2015, 12, 31), [60, 80, 100]),
])
def test_dateemitter_incorrect_daydelta_weights(mn, mx, weights):
    mn = datetime.date(*mn)
    mx = datetime.date(*mx)
    with pytest.raises(ex.ChoicesWeightsLengthMismatch) as excinfo:
        em.DateEmitter(mn, mx, weights)
    assert excinfo.value.noun == 'day delta'
    assert excinfo.value.num_choices == (mx - mn).days + 1
    assert excinfo.value.num_weights == len(weights)


@pytest.mark.parametrize('seed, mn, mx, resolution, weights, expected', [
    (999, None, None, 1, None,
     [(2, 54, 54), (20, 40, 20), (20, 53, 23), (19, 25, 53), (17, 51, 38),
      (17, 35, 58), (4, 48, 30), (23, 34, 15), (11, 34, 56), (23, 26, 12)]),
    (999, None, None, 60, None,
     [(23, 10), (2, 43), (19, 22), (19, 35), (18, 13), (16, 44), (16, 29),
      (4, 30), (22, 5), (10, 51)]),
    (999, (5, 0, 0), (5, 30, 0), 1, None,
     [(5, 26, 40), (5, 23, 10), (5, 2, 43), (5, 29, 46), (5, 19, 22),
      (5, 19, 35), (5, 18, 13), (5, 16, 44), (5, 16, 29), (5, 4, 30)]),
    (999, (5, 0, 0), (11, 59, 59), 60,
     list(itertools.accumulate([1] * 60 + [1] * 60 + [5] * 60 + [10] * 60 +
                               [5] * 60 + [3] * 60 + [2] * 60)),
     [(9, 49), (7, 1), (10, 31), (8, 50), (8, 37), (7, 18), (9, 54), (8, 9),
      (9, 53), (10, 16)]),
    (999, (6, 0, 0), (8, 59, 59), 600,
     list(itertools.accumulate([10] * 6 + [5] * 6 + [2] * 6)),
     [(7, 30), (6, 0), (7, 50), (6, 50), (6, 50), (6, 10), (7, 40), (6, 30),
      (7, 40), (7, 50)]),
    (999, (20, 0, 1), (20, 0, 59), 20, [50, 80, 100],
     [(20, 0, 21), (20, 0, 1), (20, 0, 41), (20, 0, 21), (20, 0, 1),
      (20, 0, 1), (20, 0, 21), (20, 0, 1), (20, 0, 21), (20, 0, 41)]),
])
def test_timeemitter(seed, mn, mx, resolution, weights, expected):
    mn = mn if mn is None else datetime.time(*mn)
    mx = mx if mx is None else datetime.time(*mx)
    te = em.TimeEmitter(mn, mx, resolution=resolution, weights=weights)
    te.seed_rngs(seed)
    assert [te() for _ in expected] == [datetime.time(*i) for i in expected]


@pytest.mark.parametrize('mn, mx, resolution, weights, exp_num_choices', [
    ((6, 0, 0), (8, 0, 0), 60,
     list(itertools.accumulate([5] * 60 + [10] * 60)), 121),
    ((6, 0, 0), (6, 0, 5), 1, [10, 50, 60, 65, 76], 6),
    ((20, 0, 1), (20, 0, 59), 10, [10, 30, 35, 40, 45, 70, 100], 6),
])
def test_timeemitter_incorrect_intervaldelta_weights(mn, mx, resolution,
                                                     weights, exp_num_choices):
    mn = datetime.time(*mn)
    mx = datetime.time(*mx)
    with pytest.raises(ex.ChoicesWeightsLengthMismatch) as excinfo:
        em.TimeEmitter(mn, mx, resolution=resolution, weights=weights)
    assert excinfo.value.noun == 'time interval delta'
    assert excinfo.value.num_choices == exp_num_choices
    assert excinfo.value.num_weights == len(weights)
