"""Contains tests for solrfixtures.emitters.counters."""
import itertools
import pytest

from solrfixtures.emitters import counters


@pytest.mark.parametrize('iterator_factory, expected', [
    (lambda: iter([]), [None, None, None, None]),
    (lambda: iter([1]), [1, 1, 1, 1, 1, 1]),
    (lambda: itertools.count(), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    (lambda: itertools.count(1001), [1001, 1002, 1003, 1004, 1005, 1006]),
    (lambda: iter(range(100)), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    (lambda: iter(range(5)), [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0]),
    (lambda: (f"b{n}" for n in itertools.count(1)), ['b1', 'b2', 'b3', 'b4']),
    (lambda: (str(n) for n in range(3)), ['0', '1', '2', '0', '1', '2', '0']),
    (lambda: iter(['red', 'cat', 'sun']), ['red', 'cat', 'sun', 'red', 'cat']),
])
def test_sequential_emit(iterator_factory, expected):
    em = counters.Sequential(iterator_factory)
    number = len(expected)
    assert em(number) == expected
    em.reset()
    assert [em() for _ in range(number)] == expected


@pytest.mark.parametrize('iterable, expected', [
    ([], [None, None, None, None]),
    (range(1, 2), [1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (range(1, 101), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    (range(1, 3), [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1]),
    (['red', 'cat', 'sun'], ['red', 'cat', 'sun', 'red', 'cat']),
])
def test_sequentialfromiterable_emit(iterable, expected):
    em = counters.sequential_from_iterable(iterable)
    number = len(expected)
    assert em(number) == expected
    em.reset()
    assert [em() for _ in range(number)] == expected
