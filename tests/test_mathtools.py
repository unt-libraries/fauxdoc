"""Contains tests for the fauxdoc data.math module."""
import random

import pytest

from fauxdoc import mathtools as m


@pytest.mark.parametrize('x, mu, expected', [
    (0, 1, 0.3679),
    (1, 1, 0.3679),
    (2, 1, 0.1839),
    (6, 1, 0.0005),
    (10, 1, 0.0),
    (1, 1.5, 0.3347),
    (2, 2, 0.2707)
])
def test_poisson(x, mu, expected):
    assert round(m.poisson(x, mu), 4) == expected


@pytest.mark.parametrize('x, mu, sigma, expected', [
    (0, 1, 1, 0.242),
    (1, 1, 1, 0.3989),
    (2, 1, 1, 0.242),
    (6, 1, 1, 0.0),
    (10, 1, 1, 0.0),
    (1, 1.5, 1, 0.3521),
    (1.5, 1, 1, 0.3521),
    (2, 2, 1, 0.3989),
    (2, 1, 5, 0.0782),
    (2, 1, 10, 0.0397),
])
def test_gaussian(x, mu, sigma, expected):
    assert round(m.gaussian(x, mu, sigma), 4) == expected


@pytest.mark.parametrize('start, end, function, kwargs, expected', [
    (0, 4, m.poisson, {}, [0.3679, 0.3679, 0.1839, 0.0613]),
    (1, 4, m.poisson, {}, [0.3679, 0.1839, 0.0613]),
    (0, 4, m.gaussian, {'sigma': 2}, [0.1995, 0.176, 0.121, 0.0648]),
])
def test_distribution(start, end, function, kwargs, expected):
    """Demonstrates creating a distribution from a dist function.

    At one point I had a `distribute` function that basically just did
    the first line in this test, below. But it's simple enough to do
    that without the complexity of an additional function. Still, since
    this is the intended primary use for the various distribution
    functions (poisson, gaussian, etc.), I wanted to leave this test
    for illustration.
    """
    dist = (function(i, **kwargs) for i in range(start, end))
    assert [round(val, 4) for val in dist] == expected


@pytest.mark.parametrize('number, mn, mx, expected', [
    (35, 50, 100, 50),
    (35, 1, 100, 35),
    (35, 1, 20, 20),
    (35, None, 20, 20),
    (35, 20, None, 35),
    (35, 50, None, 50),
    (35, None, None, 35)
])
def test_clamp(number, mn, mx, expected):
    assert m.clamp(number, mn, mx) == expected


@pytest.mark.parametrize('seed, items, weights, k, expected', [
    (999, range(6), [10, 5, 5, 5, 5, 1], None,
     [[0, 2, 3, 4, 1, 5], [5, 0, 3, 2, 1, 4], [3, 2, 5, 0, 1, 4],
      [0, 2, 1, 3, 4, 5], [0, 3, 5, 1, 2, 4], [1, 4, 0, 3, 2, 5],
      [0, 2, 1, 5, 3, 4], [1, 3, 0, 5, 2, 4], [2, 0, 3, 4, 1, 5],
      [0, 2, 3, 4, 1, 5]]),
    (999, range(100), [20]*25 + [10]*25 + [5]*25 + [1]*25, 6,
     [[45, 3, 57, 26, 22, 5], [46, 14, 52, 4, 94, 8], [11, 26, 38, 58, 86, 9],
      [31, 3, 1, 9, 74, 22], [8, 35, 7, 59, 24, 66], [20, 37, 42, 5, 33, 44],
      [10, 5, 51, 46, 12, 23], [1, 44, 20, 4, 64, 24], [7, 10, 46, 9, 23, 12],
      [11, 28, 54, 60, 95, 1]]),
    (999, range(2), [75, 25], 1,
     [[0], [0], [0], [0], [0], [1], [0], [0], [1], [0], [0], [0], [0], [1],
      [1], [1], [0], [0], [0], [0], [1], [1], [0], [1], [0], [0], [0], [0],
      [0], [0], [0], [0], [0], [1], [0], [0], [0], [1], [1], [0], [0], [1],
      [1], [1], [0], [1], [0], [0], [0], [1]]),
    (999, range(10), [71, 21] + [1] * 8, 2,
     [[1, 0], [1, 0], [0, 4], [0, 1], [1, 0], [9, 0], [0, 1], [0, 1], [8, 0],
      [0, 1], [0, 6], [0, 1], [0, 1], [0, 2], [0, 2], [0, 1], [1, 0], [0, 1],
      [0, 1], [0, 1], [1, 0], [0, 1], [0, 1], [1, 0], [0, 1], [0, 1], [1, 9],
      [0, 3], [0, 1], [8, 0], [0, 3], [0, 7], [0, 3], [2, 0], [0, 4], [0, 1],
      [1, 0], [0, 9], [0, 1], [0, 9], [1, 0], [6, 0], [0, 1], [1, 0], [0, 1],
      [0, 1], [0, 1], [1, 2], [1, 0], [1, 0]]),
    (999, ['heads', 'tails'], [25, 75], 1,
     [['heads'], ['heads'], ['tails'], ['heads'], ['tails'], ['tails'],
      ['tails'], ['tails'], ['tails'], ['heads']])
])
def test_weighted_shuffle(seed, items, weights, k, expected):
    rng = random.Random(seed)
    result = [m.weighted_shuffle(items, weights, rng, k) for _ in expected]
    assert result == expected


@pytest.mark.parametrize('items, weights', [
    (range(3), []),
    (range(3), [10, 5]),
    (range(3), [10, 5, 5, 5])
])
def test_weighted_shuffle_raises_error_mismatched_weights(items, weights):
    with pytest.raises(ValueError) as excinfo:
        m.weighted_shuffle(items, weights)
    error_msg = str(excinfo.value)
    assert f"({len(items)})" in error_msg
    assert f"({len(weights)})" in error_msg
