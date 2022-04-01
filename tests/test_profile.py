"""Contains tests for the profile module."""
import pytest

from solrfixtures.emitter import StaticEmitter
from solrfixtures.emitters import choice
from solrfixtures.profile import Field


# Fixtures / test data

WORDS = ('bicycle', 'warm', 'snowstorm', 'zebra', 'sympathy', 'flautist',
         'yellow', 'happy', 'sluggish', 'eat', 'crazy', 'chairs')


@pytest.fixture
def emitter():
    def _emitter():
        return choice.Choice(WORDS)
    return _emitter


@pytest.fixture
def emitter_unique():
    def _emitter_unique():
        return choice.Choice(WORDS, unique=True)
    return _emitter_unique


@pytest.fixture
def emitter_each_unique():
    def _emitter_each_unique():
        return choice.Choice(WORDS, each_unique=True)
    return _emitter_each_unique


# Tests

@pytest.mark.parametrize('seed, repeat, gate, expected', [
    # Single-valued fields + always emit (no repeat, no gate)
    (999, None, None, 
     ['crazy', 'warm', 'eat', 'eat', 'sluggish', 'happy', 'happy', 'snowstorm',
      'crazy', 'flautist']),

    # Multi-valued fields + always emit (repeat, no gate)
    (999, StaticEmitter(0), None,
     [[], [], [], [], [], [], [], [], [], []]),
    (999, StaticEmitter(1), None,
     [['crazy'], ['warm'], ['eat'], ['eat'], ['sluggish'], ['happy'],
      ['happy'], ['snowstorm'], ['crazy'], ['flautist']]),
    (999, StaticEmitter(2), None,
     [['eat', 'bicycle'], ['crazy', 'yellow'], ['flautist', 'warm'],
      ['eat', 'zebra'], ['eat', 'crazy'], ['warm', 'chairs'],
      ['snowstorm', 'zebra'], ['yellow', 'sluggish'], ['zebra', 'crazy'],
      ['chairs', 'snowstorm']]),
    (999, choice.PoissonChoice(range(1, 6), mu=2), None,
     [['eat', 'bicycle', 'crazy'], ['eat'],
      ['yellow', 'flautist', 'crazy', 'happy'], ['happy', 'happy'],
      ['eat', 'happy'], ['zebra'], ['warm', 'chairs', 'bicycle'], ['sympathy'],
      ['sympathy', 'eat', 'chairs'], ['crazy', 'sympathy', 'zebra']]),
    # Note that you CAN include a chance of repeating 0 times to gate
    # the output (which gives an empty list instead of None), but
    # generally keeping "how many to output" separate from "output or
    # or don't" makes it a bit easier to assign weighting/chances.
    (999, choice.PoissonChoice(range(0, 10), mu=1), None,
     [['crazy'], [], ['warm'], [], [], [], ['eat'], [], ['eat'],
      ['sluggish']]),
    (999, choice.PoissonChoice(range(1, 6), mu=1), None,
     [['eat', 'bicycle'], ['eat'], ['yellow', 'flautist'], ['snowstorm'],
      ['crazy'], ['flautist'], ['happy', 'happy'], ['warm'],
      ['happy', 'crazy'], ['warm', 'chairs']]),

    # Single-valued fields + chance to emit (no repeat, gate)
    (999, None, choice.Chance(0),
     [None, None, None, None, None, None, None, None, None, None]),
    (999, None, choice.Chance(10),
     [None, 'crazy', None, None, None, None, None, None, None, None]),
    (999, None, choice.Chance(50),
     [None, 'crazy', None, None, 'warm', 'eat', None, 'eat', None, None]),
    (999, None, choice.Chance(85),
     ['crazy', 'warm', None, 'eat', 'eat', 'sluggish', 'happy', 'happy',
      'snowstorm', 'crazy']),
    (999, None, choice.Chance(100),
     ['crazy', 'warm', 'eat', 'eat', 'sluggish', 'happy', 'happy', 'snowstorm',
      'crazy', 'flautist']),

    # Multi-valued fields + chance to emit (repeat, gate)
    (999, choice.PoissonChoice(range(1, 6), mu=2), choice.Chance(0),
     [None, None, None, None, None, None, None, None, None, None]),
    (999, choice.Choice((0, 1), weights=[25, 75]), choice.Chance(50),
      [None, ['crazy'], None, None, [], ['warm'], None, ['eat'], None, None]),
    (999, choice.PoissonChoice(range(1, 4), mu=1), choice.Chance(75),
     [None, ['eat', 'bicycle'], None, ['eat'], ['yellow', 'flautist'],
      ['snowstorm'], None, ['crazy'], None, None]),
])
def test_field_output_repeat_and_gate(seed, repeat, gate, expected, emitter):
    field = Field('subjects', emitter(), repeat=repeat, gate=gate,
                  rng_seed=seed)
    assert [field() for _ in range(len(expected))] == expected


def test_field_single_value_global_unique_violation(emitter_unique):
    field = Field('subject', emitter_unique(), rng_seed=999)
    assert [field() for _ in range(12)] == [
        'chairs', 'snowstorm', 'eat', 'yellow', 'sluggish', 'bicycle', 'zebra',
        'sympathy', 'happy', 'flautist', 'crazy', 'warm'
    ]
    with pytest.raises(ValueError):
        field()


def test_field_multi_value_global_unique_violation(emitter_unique):
    field = Field('unique_subjects', emitter_unique(), repeat=StaticEmitter(5),
                  rng_seed=999)
    assert [field() for _ in range(2)] == [
        ['chairs', 'snowstorm', 'eat', 'yellow', 'sluggish'],
        ['bicycle', 'zebra', 'sympathy', 'happy', 'flautist']
    ]
    with pytest.raises(ValueError):
        field()


def test_field_multi_value_each_unique_violation(emitter_each_unique):
    field1 = Field('unique_subjects_12', emitter_each_unique(),
                   repeat=StaticEmitter(12), rng_seed=999)
    field2 = Field('unique_subjects_13', emitter_each_unique(),
                   repeat=StaticEmitter(13), rng_seed=999)
    assert [field1() for _ in range(2)] == [
        ['crazy', 'warm', 'eat', 'sluggish', 'happy', 'zebra', 'chairs',
         'snowstorm', 'bicycle', 'sympathy', 'yellow', 'flautist'],
        ['sympathy', 'eat', 'bicycle', 'chairs', 'yellow', 'happy', 'warm',
         'zebra', 'crazy', 'flautist', 'sluggish', 'snowstorm']
    ]
    with pytest.raises(ValueError):
        field2()


def test_field_reset_resets_and_reseeds_all_emitters(emitter_unique):
    field = Field('test', emitter_unique(),
                  repeat=choice.Choice([1] * 12, unique=True),
                  gate=choice.Chance(100), rng_seed=999)
    output = [field() for _ in range(12)]
    assert field.emitter.num_unique_values == 0
    assert field.repeat_emitter.num_unique_values == 0

    field.emitter.seed(101010)
    field.repeat_emitter.seed(12345)
    field.gate_emitter.seed(54321)
    field.reset()
    assert field.emitter.num_unique_values == 12
    assert field.repeat_emitter.num_unique_values == 12
    assert all([em.rng_seed == 999 for em in field.emitter_group.emitters])


def test_field_seed_reseeds_all_emitters(emitter):
    field = Field('test', emitter(), repeat=choice.Choice(range(1, 13)),
                  gate=choice.Chance(75))
    field.emitter.seed(101010)
    field.repeat_emitter.seed(12345)
    field.gate_emitter.seed(54321)
    field.seed(999)
    assert all([em.rng_seed == 999 for em in field.emitter_group.emitters])


@pytest.mark.parametrize('seed, repeat, gate, expected', [
    (999, None, None, 
     ['crazy', 'warm', 'eat', 'eat', 'sluggish', 'happy', 'happy', 'snowstorm',
      'crazy', 'flautist']),
    (999, choice.PoissonChoice(range(1, 6), mu=2), None,
     [['eat', 'bicycle', 'crazy'], ['eat'],
      ['yellow', 'flautist', 'crazy', 'happy'], ['happy', 'happy'],
      ['eat', 'happy'], ['zebra'], ['warm', 'chairs', 'bicycle'], ['sympathy'],
      ['sympathy', 'eat', 'chairs'], ['crazy', 'sympathy', 'zebra']]),
    (999, None, choice.Chance(50),
     [None, 'crazy', None, None, 'warm', 'eat', None, 'eat', None, None]),
    (999, choice.PoissonChoice(range(1, 4), mu=1), choice.Chance(75),
     [None, ['eat', 'bicycle'], None, ['eat'], ['yellow', 'flautist'],
      ['snowstorm'], None, ['crazy'], None, None]),
])
def test_field_caches_previous_value(seed, repeat, gate, expected, emitter):
    field = Field('test', emitter(), repeat=repeat, gate=gate, rng_seed=seed)
    prev_expected = [None] + expected[:-1]
    for exp_val, exp_prev_val in zip(expected, prev_expected):
        assert exp_prev_val == field.previous
        field()
        assert exp_val == field.previous
