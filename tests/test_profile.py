"""Contains tests for the profile module."""
import datetime

import pytest

from fauxdoc.dtrange import dtrange
from fauxdoc.emitters import choice, text
from fauxdoc.emitters.fixed import Sequential, Static
from fauxdoc.group import ObjectMap
from fauxdoc.profile import Field, Schema


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
        return choice.Choice(WORDS, replace=False)
    return _emitter_unique


@pytest.fixture
def emitter_each_unique():
    def _emitter_each_unique():
        return choice.Choice(WORDS, replace_only_after_call=True)
    return _emitter_each_unique


@pytest.fixture
def name_emitter():
    def _name_emitter():
        return text.Text(
            choice.Choice(range(2, 4)),
            choice.Choice(NAMES, replace_only_after_call=True),
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
    # don't" makes it a bit easier to assign weighting/chances.
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
    (999, None, choice.chance(0.1),
     [None, 'crazy', None, None, None, None, None, None, None, None]),
    (999, None, choice.chance(0.5),
     [None, 'crazy', None, None, 'warm', 'eat', None, 'eat', None, None]),
    (999, None, choice.chance(0.85),
     ['crazy', 'warm', None, 'eat', 'eat', 'sluggish', 'happy', 'happy',
      'snowstorm', 'crazy']),
    (999, None, choice.chance(1.0),
     ['crazy', 'warm', 'eat', 'eat', 'sluggish', 'happy', 'happy', 'snowstorm',
      'crazy', 'flautist']),

    # Multi-valued fields + chance to emit (repeat, gate)
    (999, choice.poisson_choice(range(1, 6), mu=2), choice.chance(0),
     [None, None, None, None, None, None, None, None, None, None]),
    (999, choice.Choice((0, 1), weights=[25, 75]), choice.chance(0.5),
     [None, ['crazy'], None, None, [], ['warm'], None, ['eat'], None, None]),
    (999, choice.poisson_choice(range(1, 4), mu=1), choice.chance(0.75),
     [None, ['eat', 'bicycle'], None, ['eat'], ['yellow', 'flautist'],
      ['snowstorm'], None, ['crazy'], None, None]),
])
def test_field_output_repeat_and_gate(seed, repeat, gate, expected, emitter):
    field = Field('subjects', emitter(), repeat=repeat, gate=gate,
                  rng_seed=seed)
    assert [field() for _ in range(len(expected))] == expected


def test_field_change_emitter():
    field = Field('test', Static('initialized'))
    field.emitter = Static('changed')
    assert field() == 'changed'


def test_field_change_repeat_emitter():
    field = Field('test', Static('test'), repeat=Static(1))
    field.repeat_emitter = Static(2)
    assert field() == ['test', 'test']


def test_field_change_gate_emitter():
    field = Field('test', Static('test'), gate=Static(False))
    field.gate_emitter = Static(True)
    assert field() == 'test'


def test_field_change_name():
    field = Field('test', Static('test'))
    assert field.name == 'test'
    field.name = 'new'
    assert field.name == 'new'


def test_field_change_hide():
    field = Field('test', Static('test'), hide=True)
    assert field.hide
    field.hide = False
    assert not field.hide


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
    (Field('test', Static(['test'])), False),
    (Field('test', Static(['test1', 'test2'])), False),
    (Field('test', Static('test'), repeat=None), False),
    (Field('test', Static('test'), repeat=Static(None)), False),
    (Field('test', Static('test'), repeat=Static(1)), True),
    (Field('test', Static('test'), repeat=choice.Choice(range(1))), True),
    (Field('test', Static('test'), repeat=choice.Choice(range(1, 5))), True),
])
def test_field_multivalued_attribute(field, expected):
    assert field.multi_valued == expected


def test_field_multivalued_attribute_is_readonly():
    field = Field('test', Static('test'))
    with pytest.raises(AttributeError):
        field.multi_valued = False


def test_field_reset_resets_and_reseeds_all_emitters(emitter_unique):
    field = Field('test', emitter_unique(),
                  repeat=choice.Choice([1] * 12, replace=False),
                  gate=choice.chance(1.0), rng_seed=999)
    field.emitter.seed(101010)
    field.repeat_emitter.seed(12345)
    field.gate_emitter.seed(54321)
    [field() for _ in range(12)]
    assert field.emitter.num_unique_values == 0
    assert field.repeat_emitter.num_unique_values == 0
    field.reset()
    assert field.emitter.num_unique_values == 12
    assert field.emitter.rng_seed == 999
    assert field.repeat_emitter.num_unique_values == 1
    assert field.repeat_emitter.rng_seed == 999
    assert field.gate_emitter.rng_seed == 999


def test_field_reset_resets_and_reseeds_changed_emitters(emitter_unique):
    # If we originally initialize a field using one set of emitters
    # and then change those emitters by changing the applicable
    # attributes, calling `field.reset()` should reset all of the new
    # emitters.
    field = Field('test', Static('invalid'), rng_seed=999)
    field.emitter = emitter_unique()
    field.repeat_emitter = choice.Choice([1] * 12, replace=False)
    field.gate_emitter = choice.chance(1.0)
    field.emitter.seed(101010)
    field.repeat_emitter.seed(12345)
    field.gate_emitter.seed(54321)
    [field() for _ in range(12)]
    assert field.emitter.num_unique_values == 0
    assert field.repeat_emitter.num_unique_values == 0
    field.reset()
    assert field.emitter.num_unique_values == 12
    assert field.emitter.rng_seed == 999
    assert field.repeat_emitter.num_unique_values == 1
    assert field.repeat_emitter.rng_seed == 999
    assert field.gate_emitter.rng_seed == 999


def test_field_seed_reseeds_all_emitters(emitter):
    field = Field('test', emitter(), repeat=choice.Choice(range(1, 13)),
                  gate=choice.chance(0.75))
    field.emitter.seed(101010)
    field.repeat_emitter.seed(12345)
    field.gate_emitter.seed(54321)
    field.seed(999)
    assert field.emitter.rng_seed == 999
    assert field.repeat_emitter.rng_seed == 999
    assert field.gate_emitter.rng_seed == 999


def test_field_seed_reseeds_changed_emitters(emitter):
    # If we originally initialize a field using one set of emitters
    # and then change those emitters by changing the applicable
    # attributes, calling `field.seed()` should seed all of the new
    # emitters.
    field = Field('test', Static('invalid'))
    field.emitter = emitter()
    field.repeat_emitter = choice.Choice(range(1, 13))
    field.gate_emitter = choice.chance(0.75)
    field.emitter.seed(101010)
    field.repeat_emitter.seed(12345)
    field.gate_emitter.seed(54321)
    field.seed(999)
    assert field.emitter.rng_seed == 999
    assert field.repeat_emitter.rng_seed == 999
    assert field.gate_emitter.rng_seed == 999


@pytest.mark.parametrize('seed, repeat, gate, hide, expected', [
    (999, None, None, False,
     ['crazy', 'warm', 'eat', 'eat', 'sluggish', 'happy', 'happy', 'snowstorm',
      'crazy', 'flautist']),
    (999, None, None, True,
     ['crazy', 'warm', 'eat', 'eat', 'sluggish', 'happy', 'happy', 'snowstorm',
      'crazy', 'flautist']),
    (999, choice.poisson_choice(range(1, 6), mu=2), None, False,
     [['eat', 'bicycle', 'crazy'], ['eat'],
      ['yellow', 'flautist', 'crazy', 'happy'], ['happy', 'happy'],
      ['eat', 'happy'], ['zebra'], ['warm', 'chairs', 'bicycle'], ['sympathy'],
      ['sympathy', 'eat', 'chairs'], ['crazy', 'sympathy', 'zebra']]),
    (999, choice.poisson_choice(range(1, 6), mu=2), None, True,
     [['eat', 'bicycle', 'crazy'], ['eat'],
      ['yellow', 'flautist', 'crazy', 'happy'], ['happy', 'happy'],
      ['eat', 'happy'], ['zebra'], ['warm', 'chairs', 'bicycle'], ['sympathy'],
      ['sympathy', 'eat', 'chairs'], ['crazy', 'sympathy', 'zebra']]),
    (999, None, choice.chance(0.5), False,
     [None, 'crazy', None, None, 'warm', 'eat', None, 'eat', None, None]),
    (999, None, choice.chance(0.5), True,
     [None, 'crazy', None, None, 'warm', 'eat', None, 'eat', None, None]),
    (999, choice.poisson_choice(range(1, 4), mu=1), choice.chance(0.75), False,
     [None, ['eat', 'bicycle'], None, ['eat'], ['yellow', 'flautist'],
      ['snowstorm'], None, ['crazy'], None, None]),
    (999, choice.poisson_choice(range(1, 4), mu=1), choice.chance(0.75), True,
     [None, ['eat', 'bicycle'], None, ['eat'], ['yellow', 'flautist'],
      ['snowstorm'], None, ['crazy'], None, None]),
])
def test_field_caches_previous_value(seed, repeat, gate, hide, expected,
                                     emitter):
    field = Field('test', emitter(), repeat=repeat, gate=gate, hide=hide,
                  rng_seed=seed)
    prev_expected = [None] + expected[:-1]
    for exp_val, exp_prev_val in zip(expected, prev_expected):
        assert exp_prev_val == field.previous
        field()
        assert exp_val == field.previous


def test_field_previous_is_readonly():
    field = Field('test', Static('test'))
    field()
    with pytest.raises(AttributeError):
        field.previous = 'test'


def test_schema_generates_record_dict(name_emitter, date_emitter,
                                      phrase_emitter):
    test_schema = Schema(
        Field('id', choice.Choice(range(1, 10000), replace=False)),
        Field('hidden1', Static('TEST'), hide=True),
        Field('title', phrase_emitter()),
        Field('author', name_emitter()),
        Field('contributors', name_emitter(),
              repeat=choice.poisson_choice(range(1, 6), mu=2),
              gate=choice.chance(0.66)),
        Field('subjects', phrase_emitter(),
              repeat=choice.poisson_choice(range(1, 6), mu=1),
              gate=choice.chance(0.9)),
        Field('hidden2', Static('TEST'), hide=True),
        Field('creation_date', date_emitter()),
        Field('hidden3', Static('TEST'), hide=True),
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


def test_schema_hidden_and_public_fields(name_emitter, date_emitter,
                                         phrase_emitter):
    test_schema = Schema(
        Field('id', choice.Choice(range(1, 10000), replace=False)),
        Field('hidden1', Static('TEST'), hide=True),
        Field('title', phrase_emitter()),
        Field('author', name_emitter()),
    )
    assert test_schema.public_fields == {
        'id': test_schema.fields['id'],
        'title': test_schema.fields['title'],
        'author': test_schema.fields['author'],
    }
    assert test_schema.hidden_fields == {
        'hidden1': test_schema.fields['hidden1']
    }

    test_schema.add_fields(
        Field('contributors', name_emitter(),
              repeat=choice.poisson_choice(range(1, 6), mu=2),
              gate=choice.chance(0.66)),
        Field('subjects', phrase_emitter(),
              repeat=choice.poisson_choice(range(1, 6), mu=1),
              gate=choice.chance(0.9)),
        Field('hidden2', Static('TEST'), hide=True),
        Field('creation_date', date_emitter()),
        Field('hidden3', Static('TEST'), hide=True),
    )
    assert test_schema.public_fields == {
        'id': test_schema.fields['id'],
        'title': test_schema.fields['title'],
        'author': test_schema.fields['author'],
        'contributors': test_schema.fields['contributors'],
        'subjects': test_schema.fields['subjects'],
        'creation_date': test_schema.fields['creation_date']
    }
    assert test_schema.hidden_fields == {
        'hidden1': test_schema.fields['hidden1'],
        'hidden2': test_schema.fields['hidden2'],
        'hidden3': test_schema.fields['hidden3']
    }


def test_schema_hiddenfields_is_readonly():
    test_schema = Schema(
        Field('test1', Static('test')),
        Field('test2', Static('test')),
        Field('test3', Static('test'), hide=True)
    )
    with pytest.raises(AttributeError):
        test_schema.hidden_fields = {}


def test_schema_hiddenfields_cannot_be_changed():
    test_schema = Schema(
        Field('test1', Static('test')),
        Field('test2', Static('test')),
        Field('test3', Static('test'), hide=True)
    )

    # The `hidden_fields` attribute is not meant to be changed; it is
    # not technically immutable, and so this does not raise an error...
    test_schema.hidden_fields['test4'] = Field('test4', Static('test'),
                                               hide=True)

    # ...BUT it does not actually change the value of the attribute.
    # This is a read-only, calculated attribute based on `fields`. If
    # you want to add a hidden field, just add it to `fields`.
    assert test_schema.hidden_fields == {
        'test3': test_schema.fields['test3']
    }
    assert test_schema.fields == {
        'test1': test_schema.fields['test1'],
        'test2': test_schema.fields['test2'],
        'test3': test_schema.fields['test3']
    }


def test_schema_publicfields_is_readonly():
    test_schema = Schema(
        Field('test1', Static('test')),
        Field('test2', Static('test')),
        Field('test3', Static('test'), hide=True)
    )
    with pytest.raises(AttributeError):
        test_schema.public_fields = {}


def test_schema_publicfields_cannot_be_changed():
    test_schema = Schema(
        Field('test1', Static('test')),
        Field('test2', Static('test')),
        Field('test3', Static('test'), hide=True)
    )
    # The `public_fields` attribute is not meant to be changed; it is
    # not technically immutable, and so this does not raise an error...
    test_schema.public_fields['test4'] = Field('test4', Static('test'))

    # ...BUT it does not actually change the value of the attribute.
    # This is a read-only, calculated attribute based on `fields`. If
    # you want to add a public field, just add it to `fields`.
    assert test_schema.public_fields == {
        'test1': test_schema.fields['test1'],
        'test2': test_schema.fields['test2']
    }
    assert test_schema.fields == {
        'test1': test_schema.fields['test1'],
        'test2': test_schema.fields['test2'],
        'test3': test_schema.fields['test3']
    }


def test_schema_can_set_fields_directly():
    # Schema.fields can be set directly -- but, we have to provide an
    # ObjectMap.
    test_schema = Schema()
    test_schema.fields = ObjectMap({
        'id': Field('id', Sequential(range(1, 10000))),
        'title': Field('title', Static('A Title')),
        'hidden1': Field('hidden1', Static('TEST'), hide=True),
        'author': Field('author', Static('An Author')),
        'hidden2': Field('hidden2', Static('TEST'), hide=True)
    })
    assert test_schema.public_fields == {
        'id': test_schema.fields['id'],
        'title': test_schema.fields['title'],
        'author': test_schema.fields['author']
    }
    assert test_schema.hidden_fields == {
        'hidden1': test_schema.fields['hidden1'],
        'hidden2': test_schema.fields['hidden2']
    }
    assert test_schema() == {
        'id': 1,
        'title': 'A Title',
        'author': 'An Author'
    }


def test_schema_setfields():
    test_schema = Schema(
        Field('one', Static(1)),
        Field('two', Static(2)),
        Field('three', Static(3), hide=True)
    )
    test_schema.set_fields(
        Field('a', Static('a')),
        Field('b', Static('b'), hide=True),
        Field('c', Static('c'))
    )
    assert test_schema.public_fields == {
        'a': test_schema.fields['a'],
        'c': test_schema.fields['c']
    }
    assert test_schema.hidden_fields == {
        'b': test_schema.fields['b']
    }
    assert test_schema() == {
        'a': 'a',
        'c': 'c'
    }


def test_schema_can_modify_fields_directly():
    test_schema = Schema(
        Field('id', Sequential(range(1, 10000)))
    )
    test_schema.fields['title'] = Field('title', Static('A Title'))
    test_schema.fields['hidden1'] = Field('hidden1', Static('TEST'), hide=True)
    test_schema.fields['author'] = Field('author', Static('An Author'))
    test_schema.fields['hidden2'] = Field('hidden2', Static('TEST'), hide=True)
    assert test_schema.public_fields == {
        'id': test_schema.fields['id'],
        'title': test_schema.fields['title'],
        'author': test_schema.fields['author']
    }
    assert test_schema.hidden_fields == {
        'hidden1': test_schema.fields['hidden1'],
        'hidden2': test_schema.fields['hidden2']
    }
    assert test_schema() == {
        'id': 1,
        'title': 'A Title',
        'author': 'An Author'
    }


def test_schema_fields_key_name_mismatch_is_fine():
    # Generally the `fields` mapping should have dict keys that match
    # each `field.name`. If they don't match it doesn't directly cause
    # any problems; the key value will be used in all Schema methods.
    test_schema = Schema()
    test_schema.fields = ObjectMap({
        'id': Field('the', Sequential(range(1, 10000))),
        'title': Field('field', Static('A Title')),
        'hidden1': Field('name', Static('TEST'), hide=True),
        'author': Field('does not', Static('An Author')),
        'hidden2': Field('matter', Static('TEST'), hide=True)
    })
    assert isinstance(test_schema.fields, ObjectMap)
    assert test_schema.public_fields == {
        'id': test_schema.fields['id'],
        'title': test_schema.fields['title'],
        'author': test_schema.fields['author']
    }
    assert test_schema.hidden_fields == {
        'hidden1': test_schema.fields['hidden1'],
        'hidden2': test_schema.fields['hidden2']
    }
    assert test_schema() == {
        'id': 1,
        'title': 'A Title',
        'author': 'An Author'
    }


def test_schema_can_hide_or_unhide_fields_dynamically():
    test_schema = Schema(
        Field('id', Sequential(range(1, 10000))),
        Field('one', Static('field one')),
        Field('two', Static('field two')),
        Field('three', Static('field three'), hide=True),
        Field('four', Static('field four'))
    )
    assert test_schema() == {
        'id': 1,
        'one': 'field one',
        'two': 'field two',
        'four': 'field four'
    }
    test_schema.fields['one'].hide = True
    test_schema.fields['two'].hide = True
    test_schema.fields['three'].hide = False
    assert test_schema.hidden_fields == {
        'one': test_schema.fields['one'],
        'two': test_schema.fields['two']
    }
    assert test_schema.public_fields == {
        'id': test_schema.fields['id'],
        'three': test_schema.fields['three'],
        'four': test_schema.fields['four']
    }
    assert test_schema() == {
        'id': 2,
        'three': 'field three',
        'four': 'field four'
    }


def test_schema_hidden_fields_are_still_evaluated():
    test_schema = Schema(
        Field('id', Sequential(range(1, 10000))),
        Field('one', Static('field one'), hide=True),
        Field('two', Static('field two')),
        Field('three', Static('field three'), hide=True),
        Field('four', Static('field four'))
    )
    for field in test_schema.fields.values():
        assert field.previous is None
    test_schema()
    prev = {key: field.previous for key, field in test_schema.fields.items()}
    assert prev == {
        'id': 1,
        'one': 'field one',
        'two': 'field two',
        'three': 'field three',
        'four': 'field four'
    }


def test_schema_resetfields_resets_all_fields(emitter_unique):
    schema = Schema()
    schema.fields = ObjectMap({
        'test': Field(
            'test',
            emitter_unique(),
            repeat=choice.Choice([1] * 12, replace=False),
            gate=choice.chance(1.0)
        )
    })
    schema.add_fields(
        Field(
            'test2',
            emitter_unique(),
            repeat=choice.Choice([1] * 12, replace=False),
            gate=choice.chance(1.0)
        )
    )
    schema.fields['test3'] = Field(
        'test3',
        emitter_unique(),
        repeat=choice.Choice([1] * 12, replace=False),
        gate=choice.chance(1.0),
        hide=True
    )
    [schema() for _ in range(12)]
    for field in schema.fields.values():
        assert field.emitter.num_unique_values == 0
        assert field.repeat_emitter.num_unique_values == 0

    schema.reset_fields()
    for field in schema.fields.values():
        assert field.emitter.num_unique_values == 12
        assert field.repeat_emitter.num_unique_values == 1


def test_schema_seedfields_reseeds_all_fields(emitter):
    schema = Schema()
    schema.fields = ObjectMap({
        'test': Field(
            'test',
            emitter(),
            repeat=choice.Choice(range(1, 13)),
            gate=choice.chance(0.75), rng_seed=12345
        )
    })
    schema.add_fields(
        Field(
            'test2',
            emitter(),
            repeat=choice.Choice(range(1, 13)),
            gate=choice.chance(0.75),
            rng_seed=54321
        )
    )
    schema.fields['test4'] = Field(
        'test4',
        emitter(),
        repeat=choice.Choice(range(1, 13)),
        gate=choice.chance(0.75),
        hide=True,
        rng_seed=212121
    )
    schema.seed_fields(999)
    for field in schema.fields.values():
        assert field.rng_seed == 999
        assert all([em.rng_seed == 999 for em in field._emitters.values()])
