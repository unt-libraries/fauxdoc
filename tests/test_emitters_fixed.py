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


def test_iterative_empty_iterator_factory_raises_error():
    with pytest.raises(ValueError) as excinfo:
        _ = fixed.Iterative(lambda: iter([]))
    assert 'empty iterator' in str(excinfo.value)


@pytest.mark.parametrize('sequence, expected', [
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


@pytest.mark.parametrize('sequence, expected', [
    ('abcde', 5),
    ([1, 2, 1, 2, 1, 2], 2),
    ('aaaaaa', 1)
])
def test_sequential_uniqueness_properties(sequence, expected):
    em = fixed.Sequential(sequence)
    assert em.num_unique_values == expected
    assert not em.emits_unique_values


def test_sequential_empty_iterator_factory_raises_error():
    with pytest.raises(ValueError) as excinfo:
        _ = fixed.Sequential([])
    assert 'empty iterator' in str(excinfo.value)
