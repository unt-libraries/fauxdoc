"""Contains tests for the solrfixtures.emitters.choice module."""
import datetime

import pytest

from solrfixtures.dtrange import dtrange
from solrfixtures.emitters.choice import chance, Choice, gaussian_choice,\
                                         poisson_choice


@pytest.mark.parametrize('seed, items, weights, unq, num, repeat, expected', [
    (999, range(2), None, False, 10, 0, [1, 0, 1, 1, 0, 0, 1, 0, 1, 1]),
    (999, range(2), None, False, None, 10, [0, 1, 1, 0, 1, 0, 0, 0, 1, 0]),
    (999, range(1, 2), None, False, 10, 0, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (999, range(1, 2), None, False, None, 10, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (999, range(5, 6), None, False, 10, 0, [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]),
    (999, range(1, 11), None, False, 10, 0, [8, 1, 9, 6, 5, 2, 8, 4, 8, 9]),
    (999, 'abcde', None, False, 10, 0,
     ['d', 'a', 'e', 'c', 'c', 'a', 'd', 'b', 'd', 'e']),
    (999, ['H', 'T'], [80, 20], False, 10, 0,
     ['H', 'H', 'T', 'H', 'H', 'H', 'H', 'H', 'H', 'T']),
    (999, ['H', 'T'], [80, 20], False, None, 10,
     ['H', 'H', 'T', 'H', 'H', 'H', 'H', 'H', 'H', 'T']),
    (999, ['H', 'T'], [20, 80], False, 10, 0,
     ['T', 'H', 'T', 'T', 'T', 'H', 'T', 'T', 'T', 'T']),
    (999, 'TTHHHHHHHH', None, 'each', 10, 0,
     ['T', 'H', 'H', 'H', 'H', 'H', 'T', 'H', 'H', 'H']),
    (999, 'HHHHT', None, 'each', None, 10,
     ['H', 'T', 'T', 'T', 'H', 'H', 'H', 'H', 'H', 'H']),
    (999, 'HT', [80, 20], 'each', None, 10,
     ['H', 'H', 'T', 'H', 'H', 'H', 'H', 'H', 'H', 'T']),
    (999, 'HT', [20, 80], 'each', None, 10,
     ['T', 'H', 'T', 'T', 'T', 'H', 'T', 'T', 'T', 'T']),
    (999, range(5), [70, 20, 7, 2, 1], 'each', 3, 10,
     [[0, 2, 1], [1, 0, 3], [1, 0, 2], [0, 3, 2], [0, 4, 1], [0, 2, 1],
      [1, 0, 2], [1, 0, 2], [1, 0, 3], [0, 2, 1]]),
    (999, range(5), [70, 20, 7, 2, 1], False, 3, 10,
     [[1, 0, 1], [0, 0, 0], [1, 0, 1], [1, 0, 4], [0, 0, 0], [1, 0, 1],
      [3, 0, 0], [0, 0, 0], [2, 0, 0], [0, 0, 1]]),
    (999, range(25), None, True, 5, 5,
     [[11, 18, 24, 17, 2], [9, 6, 8, 0, 15], [20, 3, 14, 4, 7],
      [13, 16, 19, 23, 12], [5, 10, 1, 21, 22]]),
    (999, range(25), None, True, None, 25,
     [11, 18, 24, 17, 2, 9, 6, 8, 0, 15, 20, 3, 14, 4, 7, 13, 16, 19, 23, 12,
      5, 10, 1, 21, 22]),
    (9999, range(25), [50] * 5 + [10] * 5 + [1] * 15, True, 5, 5,
     [[0, 3, 7, 12, 4], [6, 1, 2, 9, 8], [22, 14, 5, 18, 11],
      [20, 24, 13, 23, 16], [21, 17, 19, 15, 10]]),
    (9999, range(25), [50] * 5 + [10] * 5 + [1] * 15, True, None, 25,
     [0, 3, 7, 12, 4, 6, 1, 2, 9, 8, 22, 14, 5, 18, 11, 20, 24, 13, 23, 16, 21,
      17, 19, 15, 10]),
])
def test_choice(seed, items, weights, unq, num, repeat, expected):
    each_unique = unq == 'each'
    replace = not unq or each_unique
    ce = Choice(items, weights=weights, replace=replace,
                replace_only_after_call=each_unique, rng_seed=seed)
    result = [ce(num) for _ in range(repeat)] if repeat else ce(num)
    assert result == expected


def test_choice_empty_items():
    with pytest.raises(ValueError):
        Choice(range(0))


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
def test_choice_too_many_unique(items, unq, num, repeat, exp_error):
    each_unique = unq == 'each'
    replace = not unq or each_unique
    ce = Choice(items, replace=replace, replace_only_after_call=each_unique)
    with pytest.raises(ValueError) as excinfo:
        [ce(num) for _ in range(repeat)] if repeat else ce(num)
    assert exp_error in str(excinfo.value)


@pytest.mark.parametrize('items, weights', [
    ([0, 1, 2, 3], [40, 50]),
    ([0, 1], [50, 10, 2])
])
def test_choice_incorrect_weights(items, weights):
    with pytest.raises(ValueError) as excinfo:
        Choice(items, weights=weights)
    error_msg = str(excinfo.value)
    assert f"({len(items)}" in error_msg
    assert f"({len(weights)}" in error_msg


@pytest.mark.parametrize(
    'emitter, exp_unique_vals, exp_unique_items, exp_emits_unique,'
    'num_to_emit, post_emit_exp_unique_vals, post_emit_exp_unique_items,'
    'post_emit_exp_emits_unique', [
        (Choice(range(5), replace=True), 5, 5, False, 10, 5, 5, False),
        (Choice(range(5), replace_only_after_call=True),
         5, 5, False, 5, 5, 5, False),
        (Choice(range(5), replace=False), 5, 5, True, 3, 2, 2, True),
        (Choice(range(5), replace=False), 5, 5, True, 5, 0, 0, True),
        (Choice([0, 1, 0, 2, 2], replace=False, rng_seed=999),
         3, 5, False, 3, 2, 2, True),
        (Choice([0, 1, 0, 2, 2], replace=True, rng_seed=999),
         3, 5, False, 10, 3, 5, False),
    ]
)
def test_choice_uniqueness_properties(emitter, exp_unique_vals,
                                      exp_unique_items, exp_emits_unique,
                                      num_to_emit, post_emit_exp_unique_vals,
                                      post_emit_exp_unique_items,
                                      post_emit_exp_emits_unique):
    assert emitter.num_unique_values == exp_unique_vals
    assert emitter.num_unique_items == exp_unique_items
    assert emitter.emits_unique_values == exp_emits_unique
    emitter(num_to_emit)
    assert emitter.num_unique_values == post_emit_exp_unique_vals
    assert emitter.num_unique_items == post_emit_exp_unique_items
    assert emitter.emits_unique_values == post_emit_exp_emits_unique
    emitter.reset()
    assert emitter.num_unique_values == exp_unique_vals
    assert emitter.num_unique_items == exp_unique_items
    assert emitter.emits_unique_values == exp_emits_unique


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
def test_choice_dates(seed, mn, mx, weights, expected):
    dates = dtrange(datetime.date(*mn), datetime.date(*mx))
    de = Choice(dates, weights=weights, rng_seed=seed)
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
def test_choice_times(seed, mn, mx, step, step_unit, weights, expected):
    times = dtrange(datetime.time(*mn), datetime.time(*mx), step, step_unit)
    te = Choice(times, weights=weights, rng_seed=seed)
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
def test_choice_datetimes(seed, mn, mx, step, step_unit, weights, expected):
    datetimes = dtrange(datetime.datetime(*mn), datetime.datetime(*mx), step,
                        step_unit)
    dte = Choice(datetimes, weights=weights, rng_seed=seed)
    assert dte(len(expected)) == [datetime.datetime(*i) for i in expected]


@pytest.mark.parametrize('seed, items, mu, weight_floor, expected', [
    (999, range(1, 10), 1, 0,
     [2, 1, 2, 1, 1, 1, 2, 1, 2, 2, 1, 5, 1, 1, 1, 2, 1, 3, 4, 1]),
    (999, range(1, 10), 1.5, 0,
     [3, 1, 3, 2, 2, 1, 3, 1, 3, 3, 1, 6, 1, 1, 2, 2, 1, 3, 5, 1]),
    (999, range(1, 10), 0.1, 0,
     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1]),
    (999, range(1, 10), 2, 0,
     [3, 1, 4, 2, 2, 1, 3, 2, 3, 4, 1, 6, 1, 1, 2, 3, 1, 4, 6, 1]),
    (999, range(1, 10), 3, 0,
     [4, 1, 5, 3, 3, 1, 4, 2, 4, 5, 1, 8, 2, 2, 3, 4, 2, 5, 7, 2]),
    (999, range(1, 10), 10, 0,
     [9, 5, 9, 8, 8, 5, 9, 7, 9, 9, 5, 9, 6, 6, 8, 8, 6, 9, 9, 6]),
    (999, range(1, 10), 20, 0,
     [9, 7, 9, 9, 9, 7, 9, 8, 9, 9, 7, 9, 8, 8, 9, 9, 8, 9, 9, 8]),
    (999, range(1, 10), 1, 0.05,
     [6, 1, 7, 2, 2, 1, 6, 1, 6, 7, 1, 9, 1, 1, 2, 4, 1, 7, 9, 1]),
    (999, range(1, 10), 1, 0.5,
     [8, 1, 8, 6, 5, 2, 8, 3, 8, 8, 1, 9, 2, 3, 6, 7, 3, 8, 9, 3]),
])
def test_poisson_choice(seed, items, mu, weight_floor, expected):
    em = poisson_choice(items, mu=mu, weight_floor=weight_floor, rng_seed=seed)
    assert em(len(expected)) == expected


@pytest.mark.parametrize('seed, items, mu, sigma, weight_floor, expected', [
    (999, range(1, 10), 0, 1, 0,
     [1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 3, 1, 1, 1, 1, 1, 2, 3, 1]),
    (999, range(1, 10), 1, 1, 0,
     [2, 1, 2, 2, 1, 1, 2, 1, 2, 2, 1, 4, 1, 1, 2, 2, 1, 2, 3, 1]),
    (999, range(1, 10), 2, 1, 0,
     [3, 1, 3, 2, 2, 1, 3, 2, 3, 3, 1, 4, 1, 2, 2, 3, 1, 3, 4, 1]),
    (999, range(1, 10), 3, 1, 0,
     [4, 2, 4, 3, 3, 2, 4, 3, 4, 4, 2, 5, 2, 2, 3, 4, 2, 4, 5, 2]),
    (999, range(1, 10), 10, 1, 0,
     [9, 8, 9, 9, 9, 8, 9, 9, 9, 9, 8, 9, 8, 9, 9, 9, 9, 9, 9, 9]),
    (999, range(1, 10), 20, 1, 0,
     [9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9]),
    (999, range(1, 10), 1, 0.5, 0,
     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1]),
    (999, range(1, 10), 1, 1.5, 0,
     [3, 1, 3, 2, 2, 1, 3, 1, 3, 3, 1, 5, 1, 1, 2, 2, 1, 3, 4, 1]),
    (999, range(1, 10), 1, 2, 0,
     [3, 1, 4, 2, 2, 1, 3, 1, 3, 4, 1, 6, 1, 1, 2, 3, 1, 4, 6, 1]),
    (999, range(1, 10), 10, 5, 0,
     [8, 2, 9, 7, 6, 3, 8, 5, 8, 9, 3, 9, 4, 5, 7, 8, 5, 9, 9, 4]),
    (999, range(1, 10), 0, 1, 0.01,
     [2, 1, 5, 1, 1, 1, 2, 1, 2, 4, 1, 9, 1, 1, 1, 2, 1, 5, 9, 1]),
    (999, range(1, 10), 0, 1, 0.1,
     [7, 1, 8, 5, 4, 1, 7, 2, 7, 8, 1, 9, 1, 2, 5, 6, 2, 8, 9, 1]),
])
def test_gaussian_choice(seed, items, mu, sigma, weight_floor, expected):
    gce = gaussian_choice(items, mu=mu, sigma=sigma, weight_floor=weight_floor,
                          rng_seed=seed)
    assert gce(len(expected)) == expected


@pytest.mark.parametrize('seed, percent_chance, expected', [
    (999, -10,
     [False, False, False, False, False, False, False, False, False, False]),
    (999, 0,
     [False, False, False, False, False, False, False, False, False, False]),
    (999, 0.25,
     [False, True, False, False, False, True, False, False, False, False]),
    (999, 0.455,
     [False, True, False, False, False, True, False, True, False, False]),
    (999, 0.8,
     [True, True, False, True, True, True, True, True, True, False]),
    (999, 1.0,
     [True, True, True, True, True, True, True, True, True, True]),
    (999, 10000,
     [True, True, True, True, True, True, True, True, True, True]),
])
def test_chance(seed, percent_chance, expected):
    chance_em = chance(percent_chance, rng_seed=seed)
    assert chance_em(len(expected)) == expected
