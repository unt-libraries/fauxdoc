"""Contains tests for the solrfixtures.data.emitter module."""
import datetime

import pytest

from solrfixtures.data import dtrange
from solrfixtures.data import emitter as em
from solrfixtures.data import exceptions as ex


# Module-specific fixtures

@pytest.fixture
def word_emitter():
    """Fixture to use as the `word_emitter` arg for TextEmitter tests."""
    return em.WordEmitter(
        em.ChoicesEmitter(range(2, 9)),
        em.ChoicesEmitter('abcde'),
    )


# Tests

@pytest.mark.parametrize('ranges, expected', [
    ([(0x0041, 0x0045), (0x0047, 0x0047)], list('ABCDEG')),
    ([(ord('a'), ord('g')), (ord('A'), ord('C'))],
     list('abcdefgABC'))
])
def test_makealphabet(ranges, expected):
    assert em.make_alphabet(ranges) == expected


@pytest.mark.parametrize('seed, items, weights, unq, num, repeat, expected', [
    (999, range(2), None, False, 10, 0, [1, 0, 1, 1, 0, 0, 1, 0, 1, 1]),
    (999, range(1, 2), None, False, 10, 0, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (999, range(5, 6), None, False, 10, 0, [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]),
    (999, range(1, 11), None, False, 10, 0, [8, 1, 9, 6, 5, 2, 8, 4, 8, 9]),
    (999, 'abcde', None, False, 10, 0,
     ['d', 'a', 'e', 'c', 'c', 'a', 'd', 'b', 'd', 'e']),
    (999, ['H', 'T'], [80, 20], False, 10, 0,
     ['H', 'H', 'T', 'H', 'H', 'H', 'H', 'H', 'H', 'T']),
    (999, ['H', 'T'], [20, 80], False, 10, 0,
     ['T', 'H', 'T', 'T', 'T', 'H', 'T', 'T', 'T', 'T']),
    (999, 'TTHHHHHHHH', None, 'each', 10, 0,
     ['T', 'H', 'H', 'H', 'H', 'H', 'T', 'H', 'H', 'H']),
    (999, 'HHHHT', None, 'each', None, 10,
     ['H', 'T', 'T', 'T', 'H', 'H', 'H', 'H', 'H', 'H']),
    (999, 'HT', [80, 20], 'each', None, 10,
     ['H', 'H', 'H', 'H', 'H', 'T', 'H', 'H', 'T', 'H']),
    (999, 'HT', [20, 80], 'each', None, 10,
     ['H', 'H', 'T', 'H', 'T', 'T', 'T', 'T', 'T', 'H']),
    (999, range(5), [70, 20, 7, 2, 1], 'each', 3, 10,
     [[0, 2, 1], [1, 0, 3], [1, 0, 2], [0, 3, 2], [0, 4, 1], [0, 2, 1],
      [1, 0, 2], [1, 0, 2], [1, 0, 3], [0, 2, 1]]),
    (999, range(5), [70, 20, 7, 2, 1], None, 3, 10,
     [[1, 0, 1], [0, 0, 0], [1, 0, 1], [1, 0, 4], [0, 0, 0], [1, 0, 1],
      [3, 0, 0], [0, 0, 0], [2, 0, 0], [0, 0, 1]]),
    (999, range(25), None, True, 5, 5,
     [[11, 18, 24, 17, 2], [9, 6, 8, 0, 15], [20, 3, 14, 4, 7],
      [13, 16, 19, 23, 12], [5, 10, 1, 21, 22]]),
    (9999, range(25), [50] * 5 + [10] * 5 + [1] * 15, True, 5, 5,
     [[0, 3, 7, 12, 4], [6, 1, 2, 9, 8], [22, 14, 5, 18, 11],
      [20, 24, 13, 23, 16], [21, 17, 19, 15, 10]]),
])
def test_choicesemitter(seed, items, weights, unq, num, repeat, expected):
    each_unique = unq == 'each'
    unique = unq and not each_unique
    ce = em.ChoicesEmitter(items, weights=weights, unique=unique,
                           each_unique=each_unique, rng_seed=seed)
    result = [ce(num) for _ in range(repeat)] if repeat else ce(num)
    assert result == expected


def test_choicesemitter_empty_items():
    with pytest.raises(ValueError):
        em.ChoicesEmitter(range(0))


@pytest.mark.parametrize('items, unq, num, repeat, exp_error', [
    (range(9), 'each', 10, 0,
     '10 new unique values were requested, out of 9 possible selections.'),
    (range(9), True, 10, 0,
     '10 new unique values were requested, out of 9 possible selections.'),
    (range(9), True, None, 10,
     '1 new unique value was requested, out of 0 possible selections.'),
    (range(9), True, 3, 4,
     '3 new unique values were requested, out of 0 possible selections.'),
    (range(10), True, 3, 4,
     '3 new unique values were requested, out of 1 possible selection.'),
])
def test_choicesemitter_too_many_unique(items, unq, num, repeat, exp_error):
    each_unique = unq == 'each'
    unique = unq and not each_unique
    ce = em.ChoicesEmitter(items, unique=unique, each_unique=each_unique)
    with pytest.raises(ValueError) as excinfo:
        [ce(num) for _ in range(repeat)] if repeat else ce(num)
    assert exp_error in str(excinfo.value)


@pytest.mark.parametrize('items, weights', [
    ([0, 1, 2, 3], [40, 50]),
    ([0, 1], [50, 10, 2])
])
def test_choicesemitter_incorrect_weights(items, weights):
    with pytest.raises(ex.ChoicesWeightsLengthMismatch) as excinfo:
        em.ChoicesEmitter(items, weights=weights)
    assert excinfo.value.num_choices == len(items)
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
     ['daec', 'c', 'adbde', 'aea', 'bcd', 'b', 'eebd', 'aa', 'beca', 'daece']),
    (999, 1, 5, [15, 70, 5, 5, 5], 'abcde', None,
     ['da', 'e', 'cca', 'db', 'de', 'a', 'ea', 'bc', 'db', 'ee']),
    (999, 1, 5, [15, 70, 5, 5, 5], 'abcde', [20, 5, 15, 40, 20],
     ['da', 'e', 'dda', 'dc', 'de', 'a', 'ea', 'cd', 'dc', 'ee']),
    (999, 1, 5, None, 'abcde', [20, 5, 15, 40, 20],
     ['daed', 'd', 'adcde', 'aea', 'cdd', 'c', 'eebd', 'aa', 'beda', 'daede']),
])
def test_wordemitter(seed, mn, mx, lweights, alpha, aweights, expected):
    length_emitter = em.ChoicesEmitter(range(mn, mx + 1), lweights)
    alphabet_emitter = em.ChoicesEmitter(alpha, aweights)
    se = em.WordEmitter(length_emitter, alphabet_emitter, rng_seed=seed)
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
        sep_emitter = em.WordEmitter(
            em.ChoicesEmitter(range(1, 2)),
            em.ChoicesEmitter(sep_chars, sep_weights)
        )
    te = em.TextEmitter(
        em.ChoicesEmitter(range(word_mn, word_mx + 1), word_weights),
        word_emitter,
        sep_emitter,
        rng_seed=seed
    )
    assert te(len(expected)) == expected


# The next few tests are an illustration to show how to implement
# date, datetime, and time emitters using data.emitter.ChoicesEmitter
# and data.dtrange.

@pytest.mark.parametrize('seed, mn, mx, weights, expected', [
    (999, (2015, 1, 1), (2015, 1, 2), None,
     [(2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1),
      (2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1)]),
    (999, (2015, 1, 1), (2015, 1, 6), None,
     [(2015, 1, 4), (2015, 1, 1), (2015, 1, 5), (2015, 1, 3), (2015, 1, 3),
      (2015, 1, 1), (2015, 1, 4), (2015, 1, 2), (2015, 1, 4), (2015, 1, 5)]),
    (999, (2015, 1, 1), (2015, 1, 6), [60, 20, 10, 5, 5],
     [(2015, 1, 2), (2015, 1, 1), (2015, 1, 3), (2015, 1, 1), (2015, 1, 1),
      (2015, 1, 1), (2015, 1, 2), (2015, 1, 1), (2015, 1, 2), (2015, 1, 3)]),
])
def test_choicesemitter_dates(seed, mn, mx, weights, expected):
    dates = dtrange.dtrange(datetime.date(*mn), datetime.date(*mx))
    de = em.ChoicesEmitter(dates, weights=weights, rng_seed=seed)
    assert de(len(expected)) == [datetime.date(*i) for i in expected]


@pytest.mark.parametrize('seed, mn, mx, step, step_unit, weights, expected', [
    (999, (0, 0, 0), (0, 0, 0), 1, 'seconds', None,
     [(18, 45, 8), (1, 55, 17), (20, 56, 23), (13, 46, 12), (11, 46, 24),
      (3, 10, 10), (19, 10, 4), (7, 38, 5), (19, 4, 5), (20, 17, 0)]),
    (999, (0, 0), (0, 0), 60, 'seconds', None,
     [(18, 45), (1, 55), (20, 56), (13, 46), (11, 46), (3, 10), (19, 10),
      (7, 38), (19, 4), (20, 17)]),
    (999, (5, 0, 0), (5, 30, 0), 1, 'seconds', None,
     [(5, 23, 26), (5, 2, 24), (5, 26, 10), (5, 17, 12), (5, 14, 43),
      (5, 3, 57), (5, 23, 57), (5, 9, 32), (5, 23, 50), (5, 25, 21)]),
    # The next examples show weighting a time range by sub-ranges -- in
    # these cases by hour. E.g., [1] * 60 gives each minute from 5:00
    # to 5:59 a weight of 1, etc.
    (999, (5, 0, 0), (12, 0, 0), 1, 'minutes',
     [1] * 60 + [1] * 60 + [5] * 60 + [10] * 60 + [5] * 60 + [3] * 60 +
     [2] * 60,
     [(9, 49), (7, 1), (10, 31), (8, 50), (8, 37), (7, 18), (9, 54), (8, 9),
      (9, 53), (10, 16)]),
    (999, (6, 0, 0), (9, 0, 0), 10, 'minutes', [10] * 6 + [5] * 6 + [2] * 6,
     [(7, 30), (6, 0), (7, 50), (6, 50), (6, 50), (6, 10), (7, 40), (6, 30),
      (7, 40), (7, 50)]),
    (999, (20, 0, 1), (20, 1, 0), 20, 'seconds', [50, 30, 20],
     [(20, 0, 21), (20, 0, 1), (20, 0, 41), (20, 0, 21), (20, 0, 1),
      (20, 0, 1), (20, 0, 21), (20, 0, 1), (20, 0, 21), (20, 0, 41)]),
])
def test_timeemitter(seed, mn, mx, step, step_unit, weights, expected):
    times = dtrange.dtrange(datetime.time(*mn), datetime.time(*mx), step,
                            step_unit)
    te = em.ChoicesEmitter(times, weights=weights, rng_seed=seed)
    assert te(len(expected)) == [datetime.time(*i) for i in expected]


@pytest.mark.parametrize('seed, mn, mx, step, step_unit, weights, expected', [
    (999, (2016, 1, 1, 20, 0), (2016, 1, 2, 7, 0), 1, 'minutes', None,
     [(2016, 1, 2, 4, 35, 0), (2016, 1, 1, 20, 52, 0), (2016, 1, 2, 5, 35, 0),
      (2016, 1, 2, 2, 18, 0), (2016, 1, 2, 1, 23, 0), (2016, 1, 1, 21, 27, 0),
      (2016, 1, 2, 4, 47, 0), (2016, 1, 1, 23, 29, 0), (2016, 1, 2, 4, 44, 0),
      (2016, 1, 2, 5, 17, 0)]),
    (999, (2016, 1, 1, 0, 0), (2017, 1, 1, 0, 0), 12, 'hours', None,
     [(2016, 10, 12, 12, 0, 0), (2016, 1, 30, 0, 0, 0),
      (2016, 11, 15, 0, 0, 0), (2016, 7, 28, 12, 0, 0),
      (2016, 6, 28, 12, 0, 0), (2016, 2, 18, 0, 0, 0), (2016, 10, 19, 0, 0, 0),
      (2016, 4, 26, 0, 0, 0), (2016, 10, 17, 12, 0, 0),
      (2016, 11, 5, 0, 0, 0)]),
    # This shows weighting a full year by sub-ranges of months.
    (999, (2016, 1, 1, 0, 0), (2017, 1, 1, 0, 0), 1, 'hours',
     [5] * (31 * 24) + [10] * (29 * 24) + [15] * (31 * 24) + [15] * (30 * 24) +
     [5] * (31 * 24) + [2] * (30 * 24) + [2] * (31 * 24) + [5] * (31 * 24) +
     [10] * (30 * 24) + [15] * (31 * 24) + [15] * (30 * 24) + [5] * (31 * 24),
     [(2016, 10, 26, 5, 0, 0), (2016, 2, 10, 19, 0, 0),
      (2016, 11, 14, 10, 0, 0), (2016, 9, 3, 5, 0, 0), (2016, 6, 19, 1, 0, 0),
      (2016, 2, 27, 6, 0, 0), (2016, 10, 29, 21, 0, 0), (2016, 4, 7, 9, 0, 0),
      (2016, 10, 29, 0, 0, 0), (2016, 11, 8, 16, 0, 0)]),
])
def test_datetimeemitter(seed, mn, mx, step, step_unit, weights, expected):
    datetimes = dtrange.dtrange(datetime.datetime(*mn), datetime.datetime(*mx),
                                step, step_unit)
    dte = em.ChoicesEmitter(datetimes, weights=weights, rng_seed=seed)
    assert dte(len(expected)) == [datetime.datetime(*i) for i in expected]
