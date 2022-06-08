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


def multi_field_each_single(**kwargs):
    return [str(v) for v in kwargs.values() if v is not None] or None


def multi_field_each_multi(**kwargs):
    return [
        str(x) for v in kwargs.values() if v is not None for x in v
    ] or None


def multi_field_each_single_collapse(**kwargs):
    return ' '.join([str(v) for v in kwargs.values() if v is not None]) or None


def multi_field_each_multi_collapse(**kwargs):
    return ' '.join([
        str(x) for v in kwargs.values() if v is not None for x in v
    ]) or None


def multi_field_random(rng, **kwargs):
    em = chance(0.5)
    em.rng = rng
    render_stack = []
    for vals in kwargs.values():
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


@pytest.mark.parametrize('source, action, seed, expected', [
    # Single-field tests
    (Field('test1', Static(0)), str, None, '0'),
    (Field('test1', Static(0), repeat=Static(1)), single_field_multi, None,
     ['0']),
    (Field('test1', Static(0), repeat=Static(1)), single_field_multi_collapse,
     None, '0'),
    (Field('test1', Static(0), repeat=Static(3)), single_field_multi, None,
     ['0', '0', '0']),
    (Field('test1', Static(0), repeat=Static(3)), single_field_multi_collapse,
     None, '0 0 0'),
    (Field('test1', Static(0), repeat=Static(3), gate=chance(0)),
     single_field_multi_collapse, None, None),
    (Field('test1', Choice(range(1, 6))), single_field_random, 999, 1),

    # Multi-field tests
    ([Field('test1', Static(1)),
      Field('test2', Static(2)),
      Field('test3', Static(3))], multi_field_each_single, None,
     ['1', '2', '3']),
    ([Field('test1', Static(1)),
      Field('test2', Static(2)),
      Field('test3', Static(3))], multi_field_each_single_collapse, None,
     '1 2 3'),
    ([Field('test1', Static(1), repeat=Static(1)),
      Field('test2', Static(2), repeat=Static(2)),
      Field('test3', Static(3), repeat=Static(2))], multi_field_each_multi,
     None, ['1', '2', '2', '3', '3']),
    ([Field('test1', Static(1), repeat=Static(1)),
      Field('test2', Static(2), repeat=Static(2)),
      Field('test3', Static(3), repeat=Static(2))],
     multi_field_each_multi_collapse, None, '1 2 2 3 3'),
    ([Field('test1', Static(1), repeat=Static(1), gate=chance(0)),
      Field('test2', Static(2), repeat=Static(2), gate=chance(0)),
      Field('test3', Static(3), repeat=Static(2))], multi_field_each_multi,
     None, ['3', '3']),
    ([Field('test1', Static(1), repeat=Static(1), gate=chance(0)),
      Field('test2', Static(2), repeat=Static(2), gate=chance(0)),
      Field('test3', Static(3), repeat=Static(2), gate=chance(0))],
     multi_field_each_multi, None, None),
    ([Field('test1', Choice(range(1, 6)), repeat=Choice(range(1, 4))),
      Field('test2', Static('-'), repeat=Choice(range(1, 4))),
      Field('test3', Choice('ABCDEFG'), repeat=Static(2))], multi_field_random,
     999, '4 1! 5 - -! -! F A!'),
    ([Field('t1', Static('1'), repeat=Static(2)),
      Field('t2', Static('2')),
      Field('t3', Static('3'))],
     lambda t1, t2, t3: ':'.join([' '.join(t1), t2, t3]),
     None, '1 1:2:3'),
])
def test_basedonfields_emit(source, action, seed, expected):
    em = BasedOnFields(source, action, seed)

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


@pytest.mark.parametrize('source, action, has_rng, problem', [
    ([Field('test1', Static('test'))],
     lambda: None, False, 'takes 0 positional arguments but 1 was given'),
    ([Field('test1', Static('test'))],
     lambda rng: None, False, "got multiple values for argument 'rng'"),
    ([Field('test1', Static('test'))],
     lambda rng, test1: None, False, "got multiple values for argument 'rng'"),
    ([Field('test1', Static('test'))],
     lambda v1, v2: None, False,
     "missing 1 required positional argument: 'v2'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda: None, False, "got an unexpected keyword argument 'test1'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda rng: None, False, "got an unexpected keyword argument 'test1'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda v1, v2: None, False, "got an unexpected keyword argument 'test1'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda test1, rng: None, False,
     "got an unexpected keyword argument 'test2'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda test1, test2, test3: None, False,
     "missing 1 required positional argument: 'test3'"),
])
def test_basedonfields_emit_bad_action_raises_error(source, action, has_rng,
                                                    problem):
    if len(source) == 1:
        args = "'test'"
        kwargs_sources = ''
    else:
        args = ''
        kwargs_sources = ', '.join([f"{f.name}='test'" for f in source])
    kwargs_rng = "rng=" if has_rng else ''
    em = BasedOnFields(source, action)
    _ = [field() for field in em.source]
    with pytest.raises(TypeError) as excinfo_one:
        _ = em()
    with pytest.raises(TypeError) as excinfo_two:
        _ = em(10)
    for excinfo in (excinfo_one, excinfo_two):
        err_msg = str(excinfo.value)
        for blurb in (args, kwargs_sources, kwargs_rng, problem):
            assert blurb in err_msg
