"""Contains tests for fauxdoc.emitters.fromfields emitters."""
import pytest

from fauxdoc.emitters.choice import chance, Choice
from fauxdoc.emitters.fixed import Static
from fauxdoc.emitters.fromfields import (
    SourceFieldGroup, CopyFields, BasedOnFields
)
from fauxdoc.emitters.wrappers import BoundWrapper
from fauxdoc.profile import Field


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

@pytest.mark.parametrize('source, expected', [
    # A SourceFieldGroup is only single-valued if the originally-
    # provided Field is singular and not multi-valued.
    (Field('test', Static('Test Val')), True),
    (Field('test', Static('Test Val'), repeat=Static(0)), False),
    (Field('test', Static('Test Val'), repeat=Static(1)), False),
    (Field('test', Static('Test Val'), repeat=Static(2)), False),
    ([Field('test', Static('Test Val'))], False),
    ([Field('test', Static('Test Val'), repeat=Static(0))], False),
    ([Field('test', Static('Test Val'), repeat=Static(1))], False),
    ([Field('test', Static('Test Val'), repeat=Static(2))], False),
    ([Field('test1', Static('one')),
      Field('test2', Static('two'))], False),
    ([Field('test1', Static('one'), repeat=Static(0)),
      Field('test2', Static('two'), repeat=Static(0))], False),
    ([Field('test1', Static('one'), repeat=Static(1)),
      Field('test2', Static('two'), repeat=Static(1))], False),
    ([Field('test1', Static('one'), repeat=Static(2)),
      Field('test2', Static('two'), repeat=Static(2))], False),
])
def test_sourcefieldgroup_singlevalued(source, expected):
    sfgroup = SourceFieldGroup(source)
    assert sfgroup.single_valued == expected


def test_sourcefieldgroup_singlevalued_changes_start_singular():
    # Edge Case. Normally modifying fields on a SourceFieldGroup isn't
    # necessary, but, if you do, I've attempted to make the
    # `single_valued` property behave logically. This tests behavior if
    # your group starts out as single-valued.
    sfgroup = SourceFieldGroup(Field('test1', Static('one')))
    assert sfgroup.single_valued

    # Appending a field makes it NOT single-valued.
    sfgroup.append(Field('test2', Static('two')))
    assert not sfgroup.single_valued

    # Returning to a single, single-valued field makes it single-valued
    # again.
    sfgroup.pop()
    assert sfgroup.single_valued

    # Deleting all values and returning to a single, single-valued
    # field makes it single-valued again.
    sfgroup.pop()
    sfgroup.append(Field('test1', Static('one')))
    assert sfgroup.single_valued

    # Deleting all values but adding a single multi-valued field makes
    # it NOT single-valued.
    sfgroup.pop()
    sfgroup.append(Field('test1', Static('one'), repeat=Static(2)))
    assert not sfgroup.single_valued


def test_sourcefieldgroup_singlevalued_changes_start_singular_multi():
    # Edge Case. Normally modifying fields on a SourceFieldGroup isn't
    # necessary, but, if you do, I've attempted to make the
    # `single_valued` property behave logically. This tests behavior if
    # your group starts out as single multi-valued field.
    sfgroup = SourceFieldGroup(Field('test1', Static('one'), repeat=Static(2)))
    assert not sfgroup.single_valued

    # Appending a field, still not single-valued.
    sfgroup.append(Field('test2', Static('two')))
    assert not sfgroup.single_valued

    # Returning to the original field, still not single-valued.
    sfgroup.pop()
    assert not sfgroup.single_valued

    # Removing the original field and adding a single single-valued
    # field does make it single-valued.
    sfgroup.pop()
    sfgroup.append(Field('test1', Static('one')))
    assert sfgroup.single_valued

    # Deleting all values but adding a single multi-valued field makes
    # it NOT single-valued.
    sfgroup.pop()
    sfgroup.append(Field('test1', Static('one'), repeat=Static(2)))
    assert not sfgroup.single_valued


def test_sourcefieldgroup_singlevalued_changes_start_multi():
    # Edge Case. Normally modifying fields on a SourceFieldGroup isn't
    # necessary, but, if you do, I've attempted to make the
    # `single_valued` property behave logically. If your group starts
    # out as a list, then it's never considered single-valued.
    # Returning to one field assumes it's a list with one value,
    # e.g. [field].
    sfgroup = SourceFieldGroup([Field('test1', Static('one'))])
    assert not sfgroup.single_valued
    sfgroup.append(Field('test2', Static('two')))
    assert not sfgroup.single_valued
    sfgroup.pop()
    assert not sfgroup.single_valued
    sfgroup.pop()
    sfgroup.append(Field('test1', Static('one')))
    assert not sfgroup.single_valued
    sfgroup.pop()
    sfgroup.append(Field('test1', Static('one'), repeat=Static(2)))
    assert not sfgroup.single_valued


@pytest.mark.parametrize('source, expected', [
    # A CopyField is only single-valued if it is not based on a list of
    # Fields and its source Field is not multi-valued.
    (Field('test', Static('Test Val')), True),
    (Field('test', Static('Test Val'), repeat=Static(0)), False),
    (Field('test', Static('Test Val'), repeat=Static(1)), False),
    (Field('test', Static('Test Val'), repeat=Static(2)), False),
    ([Field('test', Static('Test Val'))], False),
    ([Field('test', Static('Test Val'), repeat=Static(0))], False),
    ([Field('test', Static('Test Val'), repeat=Static(1))], False),
    ([Field('test', Static('Test Val'), repeat=Static(2))], False),
    ([Field('test1', Static('one')),
      Field('test2', Static('two'))], False),
    ([Field('test1', Static('one'), repeat=Static(0)),
      Field('test2', Static('two'), repeat=Static(0))], False),
    ([Field('test1', Static('one'), repeat=Static(1)),
      Field('test2', Static('two'), repeat=Static(1))], False),
    ([Field('test1', Static('one'), repeat=Static(2)),
      Field('test2', Static('two'), repeat=Static(2))], False),
])
def test_copyfields_singlevalued(source, expected):
    em = CopyFields(source)
    assert em.single_valued == expected


def test_copyfields_multi_with_separator_not_singlevalued():
    # Edge Case. The CopyFields `single_valued` attribute is based on
    # the source data, not the output. A CopyFields emitter that is set
    # to concatenate multiple values is not `single_valued`, even
    # though it emits one string value.
    em = CopyFields([
        Field('test1', Static('one')),
        Field('test2', Static('two')),
    ], separator=' | ')
    assert not em.single_valued


def test_copyfields_source_is_settable():
    # If setting `source` directly, you must use an
    # `emitters.fromfields.SourceFieldGroup` instance.
    em = CopyFields(Field('test', Static('one')))
    em.source = SourceFieldGroup([
        Field('test1', Static('one')),
        Field('test2', Static('two')),
    ])
    em.source[0]()
    em.source[1]()
    assert em() == ['one', 'two']
    assert not em.single_valued


@pytest.mark.parametrize('fields', [
    Field('new_test', Static('foo')),
    [Field('test1', Static('one')), Field('test2', Static('two'))]
])
def test_copyfields_setsourcefields(fields):
    # The `set_source_fields` method is a more convenient way to set
    # `source` -- it takes one or a list of fields.
    em = CopyFields(Field('test', Static('one')))
    em.set_source_fields(fields)
    exp = fields if isinstance(fields, list) else [fields]
    assert isinstance(em.source, SourceFieldGroup)
    assert list(em.source) == exp


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
    ([Field('test', Static('Test Val'))], None, ['Test Val']),
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
     lambda: None, False, 'too many positional arguments'),
    ([Field('test1', Static('test'))],
     lambda rng: None, False, "multiple values for argument 'rng'"),
    ([Field('test1', Static('test'))],
     lambda rng, test1: None, False, "multiple values for argument 'rng'"),
    ([Field('test1', Static('test'))],
     lambda v1, v2: None, False, "missing a required argument: 'v2'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda: None, False, "got an unexpected keyword argument 'test1'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda rng: None, False, "got an unexpected keyword argument 'test1'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda v1, v2: None, False, "missing a required argument: 'v1'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda test1, rng: None, False,
     "got an unexpected keyword argument 'test2'"),
    ([Field('test1', Static('test')),
      Field('test2', Static('test'))],
     lambda test1, test2, test3: None, False,
     "missing a required argument: 'test3'"),
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
    with pytest.raises(TypeError) as excinfo:
        BasedOnFields(source, action)
    err_msg = str(excinfo.value)
    for blurb in (args, kwargs_sources, kwargs_rng, problem):
        assert blurb in err_msg


def test_basedonfields_source_is_settable():
    em = BasedOnFields(Field('test', Static('one')), lambda val: val)
    em.source = SourceFieldGroup([
        Field('test1', Static('one')),
        Field('test2', Static('two')),
    ])
    em.source[0]()
    em.source[1]()

    # NOTE: When we set the source to use a different number of fields,
    # it invalidates the given action (which still expects one field),
    # but it DOES NOT raise an error unless you try to call the
    # emitter.
    with pytest.raises(TypeError):
        em()

    # If we set `action` now, then it validates against the new source
    # fields and works as expected.
    em.action = BoundWrapper(lambda test1, test2: f'{test1} {test2}', em)
    assert em() == 'one two'
    assert not em.source.single_valued


@pytest.mark.parametrize('fields', [
    Field('new_test', Static('foo')),
    [Field('test1', Static('one')), Field('test2', Static('two'))]
])
def test_basedonfields_setsourcefields(fields):
    # The `set_source_fields` method is a more convenient way to set
    # `source` -- it takes one or a list of fields.
    em = BasedOnFields(Field('test', Static('one')), lambda val: None)
    em.set_source_fields(fields)
    exp = fields if isinstance(fields, list) else [fields]
    assert isinstance(em.source, SourceFieldGroup)
    assert list(em.source) == exp


def test_basedonfields_action_is_settable():
    # The `action` attribute can be set directly but requires an
    # `emitters.wrappers.BoundWrapper` instance.
    field = Field('test', Static(1))
    em = BasedOnFields(field, lambda val: None)
    field()
    em.action = BoundWrapper(lambda val: f'{val}', em)
    assert em() == '1'
    assert em.action.bound_to == em


def test_basedonfields_setting_action_w_invalid_callable_raises_error():
    field = Field('test', Static(1))
    em = BasedOnFields(field, lambda val: None)
    with pytest.raises(TypeError):
        em.action = BoundWrapper(lambda val1, val2: f'{val1} {val2}', em)


def test_basedonfields_setactionfunction():
    # The `set_action_function` method is a more convenient way to set
    # `action` -- it just takes your function and wraps it in
    # BoundWrapper for you.
    field = Field('test', Static(1))
    em = BasedOnFields(field, lambda val: None)
    em.set_action_function(lambda val: 'new action')
    assert isinstance(em.action, BoundWrapper)
    assert em.action(None) == 'new action'
