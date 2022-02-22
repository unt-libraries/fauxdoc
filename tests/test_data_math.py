"""Contains tests for the solrfixtures data.math module."""

import datetime

import pytest

from solrfixtures.data import math as m


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


@pytest.mark.parametrize('x, mu, expected', [
    (0, 1, 0.3679),
    (1, 1, 0.7358),
    (2, 1, 0.9197),
    (6, 1, 0.9999),
    (10, 1, 1.0),
    (1, 1.5, 0.5578),
    (2, 2, 0.6767)
])
def test_poisson_cdf(x, mu, expected):
    assert round(m.poisson_cdf(x, mu), 4) == expected


@pytest.mark.parametrize('x, mu, sigma, expected', [
    (0, 1, 1, 0.1587),
    (1, 1, 1, 0.5),
    (2, 1, 1, 0.8413),
    (6, 1, 1, 1.0),
    (10, 1, 1, 1.0),
    (1, 1.5, 1, 0.3085),
    (1.5, 1, 1, 0.6915),
    (2, 2, 1, 0.5),
    (2, 1, 5, 0.5793),
    (2, 1, 10, 0.5398),
])
def test_gaussian_cdf(x, mu, sigma, expected):
    assert round(m.gaussian_cdf(x, mu, sigma), 4) == expected


@pytest.mark.parametrize('start, end, function, kwargs, expected', [
    (0, 4, m.poisson, {}, [0.3679, 0.3679, 0.1839, 0.0613]),
    (1, 4, m.poisson, {}, [0.3679, 0.1839, 0.0613]),
    (0, 4, m.gaussian_cdf, {'sigma': 2}, [0.5, 0.6915, 0.8413, 0.9332]),
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


@pytest.mark.parametrize('time, expected', [
    ((0, 0, 0), 0),
    ((0, 0, 59), 59),
    ((0, 10, 30), 630),
    ((1, 10, 30), 4230),
    ((12, 0, 0), 43200),
    ((20, 8, 33), 72513),
    ((23, 59, 59), 86399),
])
def test_time_to_seconds(time, expected):
    assert m.time_to_seconds(datetime.time(*time)) == expected


@pytest.mark.parametrize('seconds, expected', [
    (0, (0, 0, 0)),
    (59, (0, 0, 59)),
    (630, (0, 10, 30)),
    (4230, (1, 10, 30)),
    (43200, (12, 0, 0)),
    (72513, (20, 8, 33)),
    (86399, (23, 59, 59)),
    (86400, (0, 0, 0)),
    (86459, (0, 0, 59)),
    (172800, (0, 0, 0)),
])
def test_seconds_to_time(seconds, expected):
    assert m.seconds_to_time(seconds) == datetime.time(*expected)
