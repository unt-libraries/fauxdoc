"""Contains tests for solrfixtures.emitters.fromfields emitters."""
import pytest

from solrfixtures.emitter import StaticEmitter
from solrfixtures.emitters.choice import Chance
from solrfixtures.emitters.fromfields import CopyFields
from solrfixtures.profile import Field


@pytest.mark.parametrize('source, separator, expected', [
    # Single-field tests
    (Field('test', StaticEmitter('Test Val')), None, 'Test Val'),
    (Field('test', StaticEmitter('Test Val')), ' ', 'Test Val'),
    (Field('test', StaticEmitter('one'), repeat=StaticEmitter(3)), None,
     ['one', 'one', 'one']),
    (Field('test', StaticEmitter('one'), repeat=StaticEmitter(3)), '; ',
     'one; one; one'),
    (Field('test', StaticEmitter('one'), repeat=StaticEmitter(3),
           gate=Chance(0)), None, None),
    (Field('test', StaticEmitter('one'), repeat=StaticEmitter(0)), None, None),

    # Multi-field tests
    ([Field('test1', StaticEmitter('one')),
      Field('test2', StaticEmitter('two')),
      Field('test3', StaticEmitter('three'))], None, ['one', 'two', 'three']),
    ([Field('test1', StaticEmitter('one')),
      Field('test2', StaticEmitter('two')),
      Field('test3', StaticEmitter('three'))], ' ', 'one two three'),
    ([Field('test1', StaticEmitter('one'), repeat=StaticEmitter(3)),
      Field('test2', StaticEmitter('two')),
      Field('test3', StaticEmitter('three'), repeat=StaticEmitter(1))], None,
     ['one', 'one', 'one', 'two', 'three']),
    ([Field('test1', StaticEmitter('one'), repeat=StaticEmitter(3)),
      Field('test2', StaticEmitter('two')),
      Field('test3', StaticEmitter('three'), repeat=StaticEmitter(1))], '-',
     'one-one-one-two-three'),
    ([Field('test1', StaticEmitter('one'), repeat=StaticEmitter(3)),
      Field('test2', StaticEmitter('two'), gate=Chance(0)),
      Field('test3', StaticEmitter('three'))], None,
     ['one', 'one', 'one', 'three']),
    ([Field('test1', StaticEmitter('one'), repeat=StaticEmitter(3),
            gate=Chance(0)),
      Field('test2', StaticEmitter('two'), gate=Chance(0)),
      Field('test3', StaticEmitter('three'))], None, ['three']),
    ([Field('test1', StaticEmitter('one'), repeat=StaticEmitter(3),
            gate=Chance(0)),
      Field('test2', StaticEmitter('two'), gate=Chance(0)),
      Field('test3', StaticEmitter('three'), repeat=StaticEmitter(2))], None,
     ['three', 'three']),
    ([Field('test1', StaticEmitter('one'), repeat=StaticEmitter(3),
            gate=Chance(0)),
      Field('test2', StaticEmitter('two'), gate=Chance(0)),
      Field('test3', StaticEmitter('three'), repeat=StaticEmitter(2),
            gate=Chance(0))], None, None),
    ([Field('test1', StaticEmitter('one'), repeat=StaticEmitter(0)),
      Field('test2', StaticEmitter('two'), gate=Chance(0)),
      Field('test3', StaticEmitter('three'), repeat=StaticEmitter(2),
            gate=Chance(0))], None, None),
])
def test_copyfields_emit(source, separator, expected):
    em = CopyFields(source, separator)
    [field() for field in em.source]
    assert em() == expected
    assert em(2) == [expected, expected]
