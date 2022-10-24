"""Contains tests for fauxdoc.emitters.wrappers."""
from datetime import date, datetime
from unittest.mock import call, Mock

import pytest
from fauxdoc.emitter import Emitter
from fauxdoc.emitters.choice import Choice
from fauxdoc.emitters.fixed import Static
from fauxdoc.emitters.wrappers import WrapOne, WrapMany


# Fixtures and test data

class NumberEmitter(Emitter):
    def __init__(self):
        self.reset()

    def reset(self):
        self.counter = iter(range(9999))

    def emit(self):
        return next(self.counter)

    def emit_many(self, number):
        return [next(self.counter) for _ in range(number)]


# Tests

@pytest.mark.parametrize('source, wrapper, expected', [
    (Static(1000), str, ['1000']),
    (NumberEmitter(), str, ['0', '1', '2', '3', '4', '5', '6', '7']),
    (Static('1000'), int, [1000]),
    (Static(date(2016, 1, 1)), str, ['2016-01-01']),
    (Static(datetime(2016, 1, 1, 23, 30, 5)),
     lambda dt: (f'{dt:%A}, {dt:%B} {dt.day}, {dt.year} @ {dt.hour % 12}:'
                 f'{dt:%M:%S %p}'),
     ['Friday, January 1, 2016 @ 11:30:05 PM']),
    (Static('Susan'), lambda n: f'{n} says, "Hello!"',
     ['Susan says, "Hello!"']),
    (lambda number=None: (['Susan'] * number) if number else 'Susan',
     lambda n: f'{n} says, "Hello!"', ['Susan says, "Hello!"']),
])
def test_wrapone_emit_no_rng(source, wrapper, expected):
    em = WrapOne(source, wrapper)
    assert [em() for _ in range(len(expected))] == expected
    em.reset()
    assert em(len(expected)) == expected


@pytest.mark.parametrize('seed, source, wrapper, exp_single, exp_many', [
    (999, Choice('abcdefg'),
     lambda v, rng: v.upper() if rng.choice([True, False]) else v,
     ['G', 'f', 'a', 'G', 'e'], ['F', 'a', 'g', 'E', 'd']),
    (999, Static('a'),
     lambda v, rng: v.upper() if rng.choice([True, False]) else v,
     ['A', 'a', 'a', 'A', 'a'], ['A', 'a', 'a', 'A', 'a']),
])
def test_wrapone_emit_w_rng(seed, source, wrapper, exp_single, exp_many):
    em = WrapOne(source, wrapper, seed)
    # Note: exp_single and exp_many are separate because, the way
    # Choice emitters are implemented, `emit` and `emit_many` methods
    # result in different output for the same seed.
    assert [em() for _ in range(len(exp_single))] == exp_single
    em.reset()
    assert em(len(exp_many)) == exp_many


@pytest.mark.parametrize('wrapper, has_rng, problem', [
    (lambda: None, False, 'takes 0 positional arguments but 1 was given'),
    (lambda rng: rng, True, "multiple values for argument 'rng'"),
    (lambda rng, val: val, True, "multiple values for argument 'rng'"),
    (lambda val1, val2: val1, False,
     "missing 1 required positional argument: 'val2'"),
    (lambda val1, val2, rng: val1, True,
     "missing 1 required positional argument: 'val2'"),
    (lambda val1, rng, val2: val1, True,
     "missing 1 required positional argument: 'val2'"),
])
def test_wrapone_emit_bad_wrapper_raises_error(wrapper, has_rng, problem):
    args = "'test'"
    kwargs = "rng=" if has_rng else ''
    em = WrapOne(Static('test'), wrapper)
    with pytest.raises(TypeError) as excinfo_one:
        _ = em()
    with pytest.raises(TypeError) as excinfo_two:
        _ = em(10)
    for excinfo in (excinfo_one, excinfo_two):
        err_msg = str(excinfo.value)
        for blurb in (args, kwargs, problem):
            assert blurb in err_msg


def test_wrapone_init_and_reset_do_reset_source_emitter():
    mock_em = Mock()
    wrapped_em = WrapOne(mock_em, lambda n: None)
    mock_em.reset.assert_called_once()
    wrapped_em.reset()
    mock_em.reset.assert_has_calls([call(), call()])


def test_wrapone_seed_does_seed_source_emitter():
    mock_em = Mock()
    wrapped_em = WrapOne(mock_em, lambda n: None)
    mock_em.seed.assert_not_called()
    wrapped_em.seed(999)
    mock_em.seed.assert_called_once_with(999)


@pytest.mark.parametrize('sources, wrapper, expected', [
    ({'a': Static(1000)}, lambda a: str(a), ['1000', '1000']),
    ({'a': Static('A'), 'b': NumberEmitter()}, lambda a, b: f"{a} -- {b}",
     ['A -- 0', 'A -- 1', 'A -- 2', 'A -- 3', 'A -- 4', 'A -- 5']),
    ({'subj': Static('Susan'), 'verb': Static('says'), 'obj': Static('Hello')},
     lambda subj, verb, obj: f'{subj} {verb}, "{obj}!"',
     ['Susan says, "Hello!"', 'Susan says, "Hello!"']),
])
def test_wrapmany_emit(sources, wrapper, expected):
    em = WrapMany(sources, wrapper)
    assert [em() for _ in range(len(expected))] == expected
    em.reset()
    assert em(len(expected)) == expected


@pytest.mark.parametrize('seed, sources, wrapper, exp_single, exp_many', [
    (999, {'a': Choice('abcdefg'), 'b': Choice([1, 2, 3, 4, 5])},
     lambda a, b, rng: a if rng.choice([True, False]) else str(b),
     ['g', '5', '5', 'g', '4'], ['f', '1', '5', 'e', '3']),
    (999, {'a': Static('a'), 'b': Static('b')},
     lambda rng, a, b: a.upper() if rng.choice([True, False]) else b,
     ['A', 'b', 'b', 'A', 'b'], ['A', 'b', 'b', 'A', 'b']),
])
def test_wrapmany_emit_w_rng(seed, sources, wrapper, exp_single, exp_many):
    em = WrapMany(sources, wrapper, seed)
    # Note: exp_single and exp_many are separate because, the way
    # Choice emitters are implemented, `emit` and `emit_many` methods
    # result in different output for the same seed.
    assert [em() for _ in range(len(exp_single))] == exp_single
    em.reset()
    assert em(len(exp_many)) == exp_many


@pytest.mark.parametrize('wrapper, has_rng, problem', [
    (lambda: None, False, "got an unexpected keyword argument 'a'"),
    (lambda rng: rng, True, "got an unexpected keyword argument 'a'"),
    (lambda val1, val2: val1, False, "got an unexpected keyword argument 'a'"),
    (lambda val1, val2, rng: val1, True,
     "got an unexpected keyword argument 'a'"),
    (lambda a: a, False, "got an unexpected keyword argument 'b'"),
    (lambda a, c: a, False, "got an unexpected keyword argument 'b'"),
    (lambda a, rng: a, True, "got an unexpected keyword argument 'b'"),
    (lambda a, b, c: a, False,
     "missing 1 required positional argument: 'c'"),
    (lambda a, b, c, rng: a, True,
     "missing 1 required positional argument: 'c'"),
    (lambda a, c, b, rng: a, True,
     "missing 1 required positional argument: 'c'"),
])
def test_wrapmany_emit_bad_wrapper_raises_error(wrapper, has_rng, problem):
    kwargs_em = "a='test_a', b='test_b'"
    kwargs_rng = 'rng=' if has_rng else ''
    em = WrapMany({'a': Static('test_a'), 'b': Static('test_b')}, wrapper)
    with pytest.raises(TypeError) as excinfo_one:
        _ = em()
    with pytest.raises(TypeError) as excinfo_two:
        _ = em(10)
    for excinfo in (excinfo_one, excinfo_two):
        err_msg = str(excinfo.value)
        for blurb in (kwargs_em, kwargs_rng, problem):
            assert blurb in err_msg


def test_wrapmany_init_and_reset_do_reset_all_source_emitters():
    mock_ems = {'one': Mock(), 'two': Mock()}
    wrapped_em = WrapMany(mock_ems, lambda n: None)
    for m in mock_ems.values():
        m.reset.assert_called_once()
    wrapped_em.reset()
    for m in mock_ems.values():
        m.reset.assert_has_calls([call(), call()])


def test_wrapmany_seed_seeds_all_source_emitters():
    mock_ems = {'one': Mock(), 'two': Mock()}
    wrapped_em = WrapMany(mock_ems, lambda n: None)
    for m in mock_ems.values():
        m.seed.assert_not_called()
    wrapped_em.seed(999)
    for m in mock_ems.values():
        m.seed.assert_called_once_with(999)
