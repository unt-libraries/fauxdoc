"""Contains tests for solrfixtures.emitters.fromfields emitters."""
import pytest

from solrfixtures.emitters.fixed import Static
from solrfixtures.emitters.choice import chance
from solrfixtures.emitters.fromfields import CopyFields
from solrfixtures.profile import Field


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
    [field() for field in em.source]
    assert em() == expected
    assert em(2) == [expected, expected]
