"""Contains tests for solrfixtures.emitters.fixed."""
import itertools
import pytest

from solrfixtures.emitters import fixed


@pytest.mark.parametrize('value', [
    None,
    10,
    'my value',
    True,
    ['one', 'two'],
])
def test_static_emit(value):
    em = fixed.Static(value)
    assert em() == value
    assert em(5) == [value] * 5


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
def test_iterative_emit(iterator_factory, expected):
    em = fixed.Iterative(iterator_factory)
    number = len(expected)
    assert em(number) == expected
    em.reset()
    assert [em() for _ in range(number)] == expected


@pytest.mark.parametrize('sequence, expected', [
    ([], [None, None, None, None]),
    (range(1, 2), [1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (range(1, 101), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    (range(1, 3), [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1]),
    (['red', 'cat', 'sun'], ['red', 'cat', 'sun', 'red', 'cat']),
])
def test_sequential_emit(sequence, expected):
    em = fixed.Sequential(sequence)
    number = len(expected)
    assert em(number) == expected
    em.reset()
    assert [em() for _ in range(number)] == expected


def test_sequential_reset_after_changing_items():
    """If you modify the `items` on an existing Sequential instance,
    the instance should continue to emit the previous items until a
    `reset` is issued.
    """
    em = fixed.Sequential(range(5))
    assert em(2) == [0, 1]
    em.items = range(5, 10)
    assert em() == 2
    em.reset()
    assert em(2) == [5, 6]
