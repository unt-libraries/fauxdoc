"""Contains limited tests for the solrfixtures.emitter module."""
import pytest

from solrfixtures.emitter import Emitter, EmitterGroup, StaticEmitter


# Fixtures and test data

class MockEmitter(StaticEmitter):
    def __init__(self, value):
        self.value = value
        self.mock_val = value
        self.mock_method_call = None

    def mock_method(self, arg, kwarg=None):
        self.mock_method_call = {'arg': arg, 'kwarg': kwarg}


# Tests

@pytest.mark.parametrize('value', [
    None,
    10,
    'my value',
    True,
    ['one', 'two'],
])
def test_staticemitter(value):
    em = StaticEmitter(value)
    assert em() == value
    assert em(5) == [value] * 5


@pytest.mark.parametrize('emitters', [
    (None,),
    (MockEmitter('foo'),),
    (StaticEmitter('foo'),),
    (MockEmitter('foo'), None),
    (MockEmitter('foo'), StaticEmitter('foo'), MockEmitter('foo')),
    (MockEmitter('foo'), StaticEmitter('foo'), None, MockEmitter('foo')),
])
def test_emittergroup_setattr(emitters):
    group = EmitterGroup(*emitters)
    group.setattr('mock_val', 'bar')
    for obj in group.emitters:
        if isinstance(obj, MockEmitter):
            assert obj.mock_val == 'bar' and obj.value == 'foo'
        elif isinstance(obj, Emitter):
            assert not hasattr(obj, 'mock_val') and obj.value == 'foo'
        else:
            assert obj is None


@pytest.mark.parametrize('emitters', [
    (None,),
    (MockEmitter('foo'),),
    (StaticEmitter('foo'),),
    (MockEmitter('foo'), None),
    (MockEmitter('foo'), StaticEmitter('foo'), MockEmitter('foo')),
    (MockEmitter('foo'), StaticEmitter('foo'), None, MockEmitter('foo')),
])
def test_emittergroup_domethod(emitters):
    group = EmitterGroup(*emitters)
    group.do_method('mock_method', 'test_arg', kwarg='test_kwarg')
    for obj in group.emitters:
        if isinstance(obj, MockEmitter):
            assert obj.mock_method_call['arg'] == 'test_arg'
            assert obj.mock_method_call['kwarg'] == 'test_kwarg'
        elif isinstance(obj, Emitter):
            assert not hasattr(obj, 'mock_method')
        else:
            assert obj is None
