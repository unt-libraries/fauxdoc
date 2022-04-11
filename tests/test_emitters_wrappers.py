"""Contains tests for solrfixtures.emitters.wrappers."""
from datetime import date, time, datetime
import pytest

from solrfixtures.emitter import Emitter, StaticEmitter
from solrfixtures.emitters.wrappers import Wrap, WrapMany


# Fixtures and test data

class MockEmitter(Emitter):
    def __init__(self):
        self.reset_called = False
        self.seed_called = False
        self.seed_called_with = None

    def reset(self):
        self.reset_called = True
        super().reset()

    def seed(self, rng_seed):
        self.seed_called = True
        self.seed_called_with = rng_seed

    def emit(self):
        pass

    def emit_many(self, number):
        pass


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
    (StaticEmitter(1000), str, ['1000']),
    (NumberEmitter(), str, ['0', '1', '2', '3', '4', '5', '6', '7']),
    (StaticEmitter('1000'), int, [1000]),
    (StaticEmitter(date(2016, 1, 1)), str, ['2016-01-01']),
    (StaticEmitter(datetime(2016, 1, 1, 23, 30, 5)),
     lambda dt: (f'{dt:%A}, {dt:%B} {dt.day}, {dt.year} @ {dt.hour % 12}:'
                 f'{dt:%M:%S %p}'),
     ['Friday, January 1, 2016 @ 11:30:05 PM']),
    (StaticEmitter('Susan'), lambda n: f'{n} says, "Hello!"',
     ['Susan says, "Hello!"']),
    (lambda number=None: (['Susan'] * number) if number else 'Susan',
     lambda n: f'{n} says, "Hello!"', ['Susan says, "Hello!"']),
])
def test_wrap_emit(source, wrapper, expected):
    em = Wrap(source, wrapper)
    assert [em() for _ in range(len(expected))] == expected
    em.reset()
    assert em(len(expected)) == expected


def test_wrap_reset_resets_source_emitter():
    mock_em = MockEmitter()
    wrapped_em = Wrap(mock_em, lambda n: None)
    assert not mock_em.reset_called
    wrapped_em.reset()
    assert mock_em.reset_called


def test_wrap_seed_seeds_source_emitter():
    mock_em = MockEmitter()
    wrapped_em = Wrap(mock_em, lambda n: None)
    assert not mock_em.seed_called
    assert mock_em.seed_called_with is None
    wrapped_em.seed(999)
    assert mock_em.seed_called
    assert mock_em.seed_called_with == 999


@pytest.mark.parametrize('sources, wrapper, expected', [
    ([StaticEmitter(1000)], str, ['1000', '1000']),
    ([StaticEmitter('A'), NumberEmitter()], lambda a, b: f"{a} -- {b}",
     ['A -- 0', 'A -- 1', 'A -- 2', 'A -- 3', 'A -- 4', 'A -- 5']),
    ([StaticEmitter('Susan'), StaticEmitter('says'), StaticEmitter('Hello')],
     lambda a, b, c: f'{a} {b}, "{c}!"',
     ['Susan says, "Hello!"', 'Susan says, "Hello!"']),
])
def test_wrapmany_emit(sources, wrapper, expected):
    em = WrapMany(sources, wrapper)
    assert [em() for _ in range(len(expected))] == expected
    em.reset()
    assert em(len(expected)) == expected


def test_wrapmany_reset_resets_all_source_emitters():
    mock_ems = [MockEmitter(), MockEmitter()]
    wrapped_em = WrapMany(mock_ems, lambda n: None)
    assert all([not m.reset_called for m in mock_ems])
    wrapped_em.reset()
    assert all([m.reset_called for m in mock_ems])


def test_wrapmany_seed_seeds_all_source_emitters():
    mock_ems = [MockEmitter(), MockEmitter()]
    wrapped_em = WrapMany(mock_ems, lambda n: None)
    assert all([not m.seed_called for m in mock_ems])
    assert all([m.seed_called_with is None for m in mock_ems]) 
    wrapped_em.seed(999)
    assert all([m.seed_called for m in mock_ems])
    assert all([m.seed_called_with == 999 for m in mock_ems])
