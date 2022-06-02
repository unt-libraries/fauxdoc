"""Contains tests for solrfixtures.emitters.fromfields emitters."""
import pytest

from solrfixtures.emitters.fixed import Static
from solrfixtures.emitters.choice import chance, Choice
from solrfixtures.emitters.fromfields import CopyFields, BasedOnFields
from solrfixtures.profile import Field


# Fixtures / test data

def single_field_multi(values):
    if values is not None:
        return [str(v) for v in values]


def single_field_multi_collapse(values):
    if values is not None:
        return ' '.join([str(v) for v in values])


def single_field_random(value, rng):
    em = chance(0.5)
    em.rng = rng
    return str(value) if em() else value


def multi_field_each_single(data):
    return [str(v) for v in data.values() if v is not None] or None


def multi_field_each_multi(data):
    return [str(x) for v in data.values() if v is not None for x in v] or None


def multi_field_each_single_collapse(data):
    return ' '.join([str(v) for v in data.values() if v is not None]) or None


def multi_field_each_multi_collapse(data):
    return ' '.join([
        str(x) for v in data.values() if v is not None for x in v
    ]) or None


def multi_field_random(data, rng):
    em = chance(0.5)
    em.rng = rng
    render_stack = []
    for vals in data.values():
        for val in vals:
            if em():
                render_stack.append(f'{val}!')
            else:
                render_stack.append(str(val))
    return ' '.join(render_stack)


# Tests

@pytest.mark.parametrize('source, separator, expected', [
    # Single-field tests
    (Field('test', Static('Test Val')), None, 'Test Val'),
    (Field('test', Static('Test Val')), ' ', 'Test Val'),
    (Field('test', Static('one'), repeat=Static(3)), None,
     ['one', 'one', 'one']),
    (Field('test', Static('one'), repeat=Static(3)), '; ',
     'one; one; one'),
    (Field('test', Static('one'), repeat=Static(3),
           gate=chance(0)), None, None),
    (Field('test', Static('one'), repeat=Static(0)), None, None),

    # Multi-field tests
    ([Field('test1', Static('one')),
      Field('test2', Static('two')),
      Field('test3', Static('three'))], None, ['one', 'two', 'three']),
    ([Field('test1', Static('one')),
      Field('test2', Static('two')),
      Field('test3', Static('three'))], ' ', 'one two three'),
    ([Field('test1', Static('one'), repeat=Static(3)),
      Field('test2', Static('two')),
      Field('test3', Static('three'), repeat=Static(1))], None,
     ['one', 'one', 'one', 'two', 'three']),
    ([Field('test1', Static('one'), repeat=Static(3)),
      Field('test2', Static('two')),
      Field('test3', Static('three'), repeat=Static(1))], '-',
     'one-one-one-two-three'),
    ([Field('test1', Static('one'), repeat=Static(3)),
      Field('test2', Static('two'), gate=chance(0)),
      Field('test3', Static('three'))], None,
     ['one', 'one', 'one', 'three']),
    ([Field('test1', Static('one'), repeat=Static(3),
            gate=chance(0)),
      Field('test2', Static('two'), gate=chance(0)),
      Field('test3', Static('three'))], None, ['three']),
    ([Field('test1', Static('one'), repeat=Static(3),
            gate=chance(0)),
      Field('test2', Static('two'), gate=chance(0)),
      Field('test3', Static('three'), repeat=Static(2))], None,
     ['three', 'three']),
    ([Field('test1', Static('one'), repeat=Static(3),
            gate=chance(0)),
      Field('test2', Static('two'), gate=chance(0)),
      Field('test3', Static('three'), repeat=Static(2),
            gate=chance(0))], None, None),
    ([Field('test1', Static('one'), repeat=Static(0)),
      Field('test2', Static('two'), gate=chance(0)),
      Field('test3', Static('three'), repeat=Static(2),
            gate=chance(0))], None, None),
])
def test_copyfields_emit(source, separator, expected):
    em = CopyFields(source, separator)

    # load initial field data
    _ = [field() for field in em.source]
    assert em() == expected
    assert em(2) == [expected, expected]


@pytest.mark.parametrize('source, action, needs_rng, seed, expected', [
    # Single-field tests
    (Field('test1', Static(0)), str, False, None, '0'),
    (Field('test1', Static(0), repeat=Static(1)), single_field_multi,
     False, None, ['0']),
    (Field('test1', Static(0), repeat=Static(1)), single_field_multi_collapse,
     False, None, '0'),
    (Field('test1', Static(0), repeat=Static(3)), single_field_multi,
     False, None, ['0', '0', '0']),
    (Field('test1', Static(0), repeat=Static(3)), single_field_multi_collapse,
     False, None, '0 0 0'),
    (Field('test1', Static(0), repeat=Static(3), gate=chance(0)),
     single_field_multi_collapse, False, None, None),
    (Field('test1', Choice(range(1, 6))), single_field_random, True, 999,
     1),

    # Multi-field tests
    ([Field('test1', Static(1)),
      Field('test2', Static(2)),
      Field('test3', Static(3))], multi_field_each_single, False, None,
     ['1', '2', '3']),
    ([Field('test1', Static(1)),
      Field('test2', Static(2)),
      Field('test3', Static(3))], multi_field_each_single_collapse, False,
     None, '1 2 3'),
    ([Field('test1', Static(1), repeat=Static(1)),
      Field('test2', Static(2), repeat=Static(2)),
      Field('test3', Static(3), repeat=Static(2))], multi_field_each_multi,
     False, None, ['1', '2', '2', '3', '3']),
    ([Field('test1', Static(1), repeat=Static(1)),
      Field('test2', Static(2), repeat=Static(2)),
      Field('test3', Static(3), repeat=Static(2))],
     multi_field_each_multi_collapse, False, None, '1 2 2 3 3'),
    ([Field('test1', Static(1), repeat=Static(1), gate=chance(0)),
      Field('test2', Static(2), repeat=Static(2), gate=chance(0)),
      Field('test3', Static(3), repeat=Static(2))], multi_field_each_multi,
     False, None, ['3', '3']),
    ([Field('test1', Static(1), repeat=Static(1), gate=chance(0)),
      Field('test2', Static(2), repeat=Static(2), gate=chance(0)),
      Field('test3', Static(3), repeat=Static(2), gate=chance(0))],
     multi_field_each_multi, False, None, None),
    ([Field('test1', Choice(range(1, 6)), repeat=Choice(range(1, 4))),
      Field('test2', Static('-'), repeat=Choice(range(1, 4))),
      Field('test3', Choice('ABCDEFG'), repeat=Static(2))], multi_field_random,
     True, 999, '4 1! 5 - -! -! F A!'),
    ([Field('test1', Static('1'), repeat=Static(2)),
      Field('test2', Static('2')),
      Field('test3', Static('3'))],
     lambda v: ':'.join([' '.join(v['test1']), v['test2'], v['test3']]), False,
     None, '1 1:2:3'),
])
def test_basedonfields_emit(source, action, needs_rng, seed, expected):
    em = BasedOnFields(source, action, needs_rng, seed)

    # Note: Normally the owning schema instance will handle seeding and
    # loading the source fields. Because we are testing outside the
    # context of a schema instance, we have to do this manually.
    em.seed_source(seed)
    _ = [field() for field in em.source]
    assert em() == expected

    em.reset_source()
    em.reset()
    _ = [field() for field in em.source]
    assert em(2) == [expected, expected]
