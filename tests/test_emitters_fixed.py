"""Contains tests for fauxdoc.emitters.fixed."""
import itertools
import pytest
import warnings

from fauxdoc.emitters import fixed


@pytest.mark.parametrize('value', [
    None,
    10,
    'my value',
    True,
    ['one', 'two'],
])
def test_static_emit(value):
    em = fixed.Static(value)
    assert em.value == value
    assert em() == value
    assert em(5) == [value] * 5


def test_static_set_value():
    em = fixed.Static('three')
    em.value = 1
    assert em() == 1
    assert em.items == [1]


def test_static_items_is_readonly():
    em = fixed.Static('three')
    with pytest.raises(AttributeError):
        em.items = [1]


def test_static_uniqueness_properties():
    em = fixed.Static(1)
    assert em.num_unique_values == 1
    assert not em.emits_unique_values


def test_static_emituniquevalues_is_readonly():
    em = fixed.Static(1)
    with pytest.raises(AttributeError):
        em.emits_unique_values = True


def test_static_numuniquevalues_is_readonly():
    em = fixed.Static(1)
    with pytest.raises(AttributeError):
        em.num_unique_values = 5


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


def test_iterative_set_iterator_factory():
    em = fixed.Iterative(lambda: iter([1, 2, 3]))
    _ = em()    # 1
    _ = em(3)   # 2, 3, 1
    em.iterator_factory = lambda: iter([4, 5, 6])
    assert em() == 4
    assert em(5) == [5, 6, 4, 5, 6]


def test_iterative_empty_iterator_factory_raises_error_on_init():
    with pytest.raises(ValueError) as excinfo:
        _ = fixed.Iterative(lambda: iter([]))
    assert 'empty iterator' in str(excinfo.value)


def test_iterative_empty_iterator_factory_raises_error_when_set():
    em = fixed.Iterative(lambda: iter([1]))
    with pytest.raises(ValueError) as excinfo:
        em.iterator_factory = lambda: iter([])
    assert 'empty iterator' in str(excinfo.value)


def test_iterative_resetaftercall_isfalse_doesnot_reset_after_call():
    em = fixed.Iterative(lambda: iter([1, 2, 3]), reset_after_call=False)
    assert not em.reset_after_call
    assert em(7) == [1, 2, 3, 1, 2, 3, 1]
    assert em(7) == [2, 3, 1, 2, 3, 1, 2]
    assert em() == 3
    assert em() == 1
    assert em() == 2


def test_iterative_resetaftercall_istrue_resets_after_call():
    em = fixed.Iterative(lambda: iter([1, 2, 3]), reset_after_call=True)
    assert em.reset_after_call
    assert em(7) == [1, 2, 3, 1, 2, 3, 1]
    assert em(7) == [1, 2, 3, 1, 2, 3, 1]
    assert em() == 1
    assert em() == 1
    assert em() == 1


def test_iterative_change_resetaftercall():
    em = fixed.Iterative(lambda: iter([1, 2, 3]), reset_after_call=False)
    em.reset_after_call = True
    assert em(4) == [1, 2, 3, 1]
    assert em(2) == [1, 2]
    assert em() == 1
    em.reset_after_call = False
    assert em(4) == [1, 2, 3, 1]
    assert em(3) == [2, 3, 1]
    assert em() == 2


def test_iterative_iterator_is_readonly():
    em = fixed.Iterative(lambda: iter([1]))
    assert next(em.iterator) == 1
    with pytest.raises(AttributeError):
        em.iterator = iter([1])


def test_iterative_reset():
    em = fixed.Iterative(lambda: iter([1, 2, 3]), reset_after_call=False)
    assert em() == 1
    assert em() == 2
    em.reset()
    assert em() == 1


def test_iterative_uniqueness_properties():
    em = fixed.Iterative(lambda: iter([1, 2, 3]))
    assert em.num_unique_values is None
    assert not em.emits_unique_values


def test_iterative_emituniquevalues_is_readonly():
    em = fixed.Iterative(lambda: iter([1, 2, 3]))
    with pytest.raises(AttributeError):
        em.emits_unique_values = True


def test_iterative_numuniquevalues_is_readonly():
    em = fixed.Iterative(lambda: iter([1, 2, 3]))
    with pytest.raises(AttributeError):
        em.num_unique_values = 5


@pytest.mark.parametrize('sequence, expected', [
    (range(1, 2), [1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (range(1, 101), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    (range(1, 3), [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1]),
    (['red', 'cat', 'sun'], ['red', 'cat', 'sun', 'red', 'cat']),
])
def test_sequential_emit(sequence, expected):
    em = fixed.Sequential(sequence)
    number = len(expected)
    assert em.items == sequence
    assert em(number) == expected
    em.reset()
    assert [em() for _ in range(number)] == expected


def test_sequential_set_iterator_factory():
    em = fixed.Sequential([1, 2])
    _ = em()    # 1
    _ = em(2)   # 2, 1
    # This will throw a deprecation warning, which we ignore here:
    with warnings.catch_warnings(record=True):
        em.iterator_factory = lambda: iter([4, 5, 6])
    assert em.items == (4, 5, 6)
    assert em.num_unique_values == 3
    assert em() == 4
    assert em(5) == [5, 6, 4, 5, 6]


def test_sequential_set_nonseq_iterator_factory_raises_error():
    em = fixed.Sequential([1, 2, 3])
    _ = em()
    with pytest.raises(ValueError) as excinfo:
        # This also throws a deprecation warning, which we ignore here:
        with warnings.catch_warnings(record=True):
            em.iterator_factory = lambda: itertools.count()
    assert 'sequence iterator' in str(excinfo.value)


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
    assert 'cannot be empty' in str(excinfo.value)


def test_sequential_resetaftercall_isfalse_doesnot_reset_after_call():
    em = fixed.Sequential([1, 2, 3], reset_after_call=False)
    assert em(7) == [1, 2, 3, 1, 2, 3, 1]
    assert em(7) == [2, 3, 1, 2, 3, 1, 2]
    assert em() == 3
    assert em() == 1
    assert em() == 2


def test_sequential_resetaftercall_istrue_resets_after_call():
    em = fixed.Sequential([1, 2, 3], reset_after_call=True)
    assert em(7) == [1, 2, 3, 1, 2, 3, 1]
    assert em(7) == [1, 2, 3, 1, 2, 3, 1]
    assert em() == 1
    assert em() == 1
    assert em() == 1
