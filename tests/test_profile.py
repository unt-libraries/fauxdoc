"""Contains tests for the profile module."""
import datetime

import pytest

from solrfixtures.dtrange import dtrange
from solrfixtures.emitters import choice, text
from solrfixtures.emitters.fixed import Static
from solrfixtures.profile import Field, Schema


# Fixtures / test data

WORDS = ('bicycle', 'warm', 'snowstorm', 'zebra', 'sympathy', 'flautist',
         'yellow', 'happy', 'sluggish', 'eat', 'crazy', 'chairs')

NAMES = ('Susan', 'Leslie', 'Boyle', 'Johnny', 'Anne', 'Krane', 'Rebecca',
         'Ashley', 'William', 'Henry', 'Chuck', 'Betty')


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


@pytest.fixture
def name_emitter():
    def _name_emitter():
        return text.Text(
            choice.Choice(range(2, 4)),
            choice.Choice(NAMES, each_unique=True),
            choice.Choice((' ', '-'), weights=[90, 10])
        )
    return _name_emitter


@pytest.fixture
def date_emitter():
    def _date_emitter():
        return choice.Choice(dtrange('2016-01-01', '2021-12-31'))
    return _date_emitter


@pytest.fixture
def phrase_emitter():
    def _phrase_emitter():
        return text.Text(
            choice.Choice(range(2, 8)),
            choice.Choice(WORDS),
            choice.Choice((' ', '-', ', ', '; ', ': '), [80, 5, 10, 3, 2])
        )
    return _phrase_emitter


# Tests

@pytest.mark.parametrize('seed, repeat, gate, expected', [
    # Single-valued fields + always emit (no repeat, no gate)
    (999, None, None, 
     ['crazy', 'warm', 'eat', 'eat', 'sluggish', 'happy', 'happy', 'snowstorm',
      'crazy', 'flautist']),

    # Multi-valued fields + always emit (repeat, no gate)
    (999, Static(0), None, [[], [], [], [], [], [], [], [], [], []]),
    (999, Static(1), None,
     [['crazy'], ['warm'], ['eat'], ['eat'], ['sluggish'], ['happy'],
      ['happy'], ['snowstorm'], ['crazy'], ['flautist']]),
    (999, Static(2), None,
     [['eat', 'bicycle'], ['crazy', 'yellow'], ['flautist', 'warm'],
      ['eat', 'zebra'], ['eat', 'crazy'], ['warm', 'chairs'],
      ['snowstorm', 'zebra'], ['yellow', 'sluggish'], ['zebra', 'crazy'],
      ['chairs', 'snowstorm']]),
    (999, choice.poisson_choice(range(1, 6), mu=2), None,
     [['eat', 'bicycle', 'crazy'], ['eat'],
      ['yellow', 'flautist', 'crazy', 'happy'], ['happy', 'happy'],
      ['eat', 'happy'], ['zebra'], ['warm', 'chairs', 'bicycle'], ['sympathy'],
      ['sympathy', 'eat', 'chairs'], ['crazy', 'sympathy', 'zebra']]),
    # Note that you CAN include a chance of repeating 0 times to gate
    # the output (which gives an empty list instead of None), but
    # generally keeping "how many to output" separate from "output or
    # or don't" makes it a bit easier to assign weighting/chances.
    (999, choice.poisson_choice(range(0, 10), mu=1), None,
     [['crazy'], [], ['warm'], [], [], [], ['eat'], [], ['eat'],
      ['sluggish']]),
    (999, choice.poisson_choice(range(1, 6), mu=1), None,
     [['eat', 'bicycle'], ['eat'], ['yellow', 'flautist'], ['snowstorm'],
      ['crazy'], ['flautist'], ['happy', 'happy'], ['warm'],
      ['happy', 'crazy'], ['warm', 'chairs']]),

    # Single-valued fields + chance to emit (no repeat, gate)
    (999, None, choice.chance(0),
     [None, None, None, None, None, None, None, None, None, None]),
    (999, None, choice.chance(10),
     [None, 'crazy', None, None, None, None, None, None, None, None]),
    (999, None, choice.chance(50),
     [None, 'crazy', None, None, 'warm', 'eat', None, 'eat', None, None]),
    (999, None, choice.chance(85),
     ['crazy', 'warm', None, 'eat', 'eat', 'sluggish', 'happy', 'happy',
      'snowstorm', 'crazy']),
    (999, None, choice.chance(100),
     ['crazy', 'warm', 'eat', 'eat', 'sluggish', 'happy', 'happy', 'snowstorm',
      'crazy', 'flautist']),

    # Multi-valued fields + chance to emit (repeat, gate)
    (999, choice.poisson_choice(range(1, 6), mu=2), choice.chance(0),
     [None, None, None, None, None, None, None, None, None, None]),
    (999, choice.Choice((0, 1), weights=[25, 75]), choice.chance(50),
      [None, ['crazy'], None, None, [], ['warm'], None, ['eat'], None, None]),
    (999, choice.poisson_choice(range(1, 4), mu=1), choice.chance(75),
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
    field = Field('unique_subjects', emitter_unique(), repeat=Static(5),
                  rng_seed=999)
    assert [field() for _ in range(2)] == [
        ['chairs', 'snowstorm', 'eat', 'yellow', 'sluggish'],
        ['bicycle', 'zebra', 'sympathy', 'happy', 'flautist']
    ]
    with pytest.raises(ValueError):
        field()


def test_field_multi_value_each_unique_violation(emitter_each_unique):
    field1 = Field('unique_subjects_12', emitter_each_unique(),
                   repeat=Static(12), rng_seed=999)
    field2 = Field('unique_subjects_13', emitter_each_unique(),
                   repeat=Static(13), rng_seed=999)
    assert [field1() for _ in range(2)] == [
        ['crazy', 'warm', 'eat', 'sluggish', 'happy', 'zebra', 'chairs',
         'snowstorm', 'bicycle', 'sympathy', 'yellow', 'flautist'],
        ['sympathy', 'eat', 'bicycle', 'chairs', 'yellow', 'happy', 'warm',
         'zebra', 'crazy', 'flautist', 'sluggish', 'snowstorm']
    ]
    with pytest.raises(ValueError):
        field2()


@pytest.mark.parametrize('field, expected', [
    (Field('test', Static('test')), False),
    (Field('test', Static('test'), repeat=None), False),
    (Field('test', Static('test'), repeat=Static(None)), False),
    (Field('test', Static('test'), repeat=Static(1)), True),
    (Field('test', Static('test'), repeat=choice.Choice(range(1))), True),
    (Field('test', Static('test'), repeat=choice.Choice(range(1, 5))), True),
])
def test_field_multivalued_attribute(field, expected):
    assert field.multi_valued == expected


def test_field_reset_resets_and_reseeds_all_emitters(emitter_unique):
    field = Field('test', emitter_unique(),
                  repeat=choice.Choice([1] * 12, unique=True),
                  gate=choice.chance(100), rng_seed=999)
    output = [field() for _ in range(12)]
    assert field.emitter.num_unique_values == 0
    assert field.repeat_emitter.num_unique_values == 0

    field.emitter.seed(101010)
    field.repeat_emitter.seed(12345)
    field.gate_emitter.seed(54321)
    field.reset()
    assert field.emitter.num_unique_values == 12
    assert field.repeat_emitter.num_unique_values == 12
    assert all([em.rng_seed == 999 for em in field._emitters.values()])


def test_field_seed_reseeds_all_emitters(emitter):
    field = Field('test', emitter(), repeat=choice.Choice(range(1, 13)),
                  gate=choice.chance(75))
    field.emitter.seed(101010)
    field.repeat_emitter.seed(12345)
    field.gate_emitter.seed(54321)
    field.seed(999)
    assert all([em.rng_seed == 999 for em in field._emitters.values()])


@pytest.mark.parametrize('seed, repeat, gate, expected', [
    (999, None, None, 
     ['crazy', 'warm', 'eat', 'eat', 'sluggish', 'happy', 'happy', 'snowstorm',
      'crazy', 'flautist']),
    (999, choice.poisson_choice(range(1, 6), mu=2), None,
     [['eat', 'bicycle', 'crazy'], ['eat'],
      ['yellow', 'flautist', 'crazy', 'happy'], ['happy', 'happy'],
      ['eat', 'happy'], ['zebra'], ['warm', 'chairs', 'bicycle'], ['sympathy'],
      ['sympathy', 'eat', 'chairs'], ['crazy', 'sympathy', 'zebra']]),
    (999, None, choice.chance(50),
     [None, 'crazy', None, None, 'warm', 'eat', None, 'eat', None, None]),
    (999, choice.poisson_choice(range(1, 4), mu=1), choice.chance(75),
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


def test_schema_generates_record_dict(emitter, name_emitter, date_emitter,
                                      phrase_emitter):
    test_schema = Schema(
        Field('id', choice.Choice(range(1, 10000), unique=True)),
        Field('title', phrase_emitter()),
        Field('author', name_emitter()),
        Field('contributors', name_emitter(),
              repeat=choice.poisson_choice(range(1, 6), mu=2),
              gate=choice.chance(66)),
        Field('subjects', phrase_emitter(),
              repeat=choice.poisson_choice(range(1, 6), mu=1),
              gate=choice.chance(90)),
        Field('creation_date', date_emitter())
    )
    test_schema.seed_fields(999)
    assert [test_schema() for _ in range(10)] == [
        {'id': 7503, 'title': 'eat bicycle crazy, yellow flautist warm eat',
         'author': 'Chuck Leslie', 'contributors': None,
         'subjects': ['eat bicycle crazy, yellow flautist warm', 'eat zebra'],
         'creation_date': datetime.date(2016, 11, 23)},
        {'id': 4311, 'title': 'zebra eat', 'author': 'Henry Betty William',
         'contributors': ['Chuck Leslie Henry', 'William Ashley',
                          'Johnny Betty Boyle'],
         'subjects': ['eat crazy warm chairs-snowstorm zebra'],
         'creation_date': datetime.date(2021, 12, 26)},
        {'id': 5710, 'title': 'crazy warm chairs-snowstorm zebra: yellow',
         'author': 'Ashley Betty Boyle', 'contributors': None,
         'subjects': ['yellow: sluggish zebra crazy chairs',
                      'snowstorm happy bicycle, bicycle'],
         'creation_date': datetime.date(2021, 7, 2)},
        {'id': 7389, 'title': 'sluggish zebra crazy chairs snowstorm happy',
         'author': 'Chuck Krane', 'contributors': ['Chuck Betty Leslie'],
         'subjects': ['snowstorm: chairs yellow'],
         'creation_date': datetime.date(2021, 6, 2)},
        {'id': 3097,
         'title': 'bicycle, bicycle: snowstorm chairs yellow snowstorm',
         'author': 'Chuck Betty Leslie',
         'contributors': ['Chuck Johnny', 'Boyle Anne Susan',
                          'Krane Henry-Betty', 'Leslie Rebecca William'],
         'subjects': ['snowstorm sluggish warm crazy yellow; chairs flautist'],
         'creation_date': datetime.date(2017, 6, 24)},
        {'id': 7587, 'title': 'sluggish warm crazy; yellow chairs',
         'author': 'Chuck Johnny',
         'contributors': ['Leslie Anne Susan', 'Johnny William Betty'],
         'subjects': ['sluggish sluggish warm happy'],
         'creation_date': datetime.date(2019, 7, 27)},
        {'id': 6452, 'title': 'flautist sluggish sluggish warm, happy',
         'author': 'Boyle Anne', 'contributors': None,
         'subjects': ['flautist, sluggish snowstorm, warm crazy',
                      'snowstorm eat zebra yellow bicycle'],
         'creation_date': datetime.date(2017, 2, 3)},
        {'id': 8746, 'title': 'flautist sluggish, snowstorm',
         'author': 'Henry Susan',
         'contributors': ['Chuck-Krane Boyle', 'Leslie Ashley Betty'],
         'subjects': ['eat flautist'],
         'creation_date': datetime.date(2018, 2, 9)},
        {'id': 5375, 'title': 'warm crazy snowstorm eat zebra yellow bicycle',
         'author': 'Betty-Anne Rebecca', 'contributors': None,
         'subjects': ['warm crazy yellow snowstorm-snowstorm',
                      'eat snowstorm yellow zebra snowstorm happy crazy'],
         'creation_date': datetime.date(2017, 9, 2)},
        {'id': 6176, 'title': 'eat flautist warm crazy',
         'author': 'Johnny Chuck', 'contributors': None,
         'subjects': ['crazy chairs',
                      'bicycle yellow, eat yellow crazy chairs bicycle'],
         'creation_date': datetime.date(2018, 12, 19)}]


def test_schema_resetfields_resets_all_fields(emitter_unique):
    schema = Schema(
        Field('test', emitter_unique(),
              repeat=choice.Choice([1] * 12, unique=True),
              gate=choice.chance(100)),
        Field('test2', emitter_unique(),
              repeat=choice.Choice([1] * 12, unique=True),
              gate=choice.chance(100))
    )
    output = [schema() for _ in range(12)]
    for field in schema.fields.values():
        assert field.emitter.num_unique_values == 0
        assert field.repeat_emitter.num_unique_values == 0

    schema.reset_fields()
    for field in schema.fields.values():
        assert field.emitter.num_unique_values == 12
        assert field.repeat_emitter.num_unique_values == 12


def test_field_seedfields_reseeds_all_fields(emitter):
    schema = Schema(
        Field('test', emitter(), repeat=choice.Choice(range(1, 13)),
              gate=choice.chance(75), rng_seed=12345),
        Field('test2', emitter(), repeat=choice.Choice(range(1, 13)),
              gate=choice.chance(75), rng_seed=54321),
    )
    schema.seed_fields(999)
    for field in schema.fields.values():
        assert field.rng_seed == 999
        assert all([em.rng_seed == 999 for em in field._emitters.values()])
