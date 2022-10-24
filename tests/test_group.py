"""Contains tests for the fauxdoc.group module."""
import pytest

from fauxdoc.group import ObjectGroup, ObjectMap
from fauxdoc.emitter import Emitter
from fauxdoc.emitters.fixed import Static


# Fixtures and test data

class MockEmitter(Static):
    def __init__(self, value):
        super().__init__(value)
        self.mock_val = value
        self.mock_method_call = None

    def mock_method(self, arg, kwarg=None):
        self.mock_method_call = {'arg': arg, 'kwarg': kwarg}


# Tests

@pytest.mark.parametrize('emitters', [
    (None,),
    (MockEmitter('foo'),),
    (Static('foo'),),
    (MockEmitter('foo'), None),
    (MockEmitter('foo'), Static('foo'), MockEmitter('foo')),
    (MockEmitter('foo'), Static('foo'), None, MockEmitter('foo')),
])
def test_objectgroup_setattr(emitters):
    group = ObjectGroup(*emitters)
    group.setattr('mock_val', 'bar')
    for obj in group:
        if isinstance(obj, MockEmitter):
            assert obj.mock_val == 'bar' and obj.value == 'foo'
        elif isinstance(obj, Emitter):
            assert not hasattr(obj, 'mock_val') and obj.value == 'foo'
        else:
            assert obj is None


@pytest.mark.parametrize('emitters', [
    (None,),
    (MockEmitter('foo'),),
    (Static('foo'),),
    (MockEmitter('foo'), None),
    (MockEmitter('foo'), Static('foo'), MockEmitter('foo')),
    (MockEmitter('foo'), Static('foo'), None, MockEmitter('foo')),
])
def test_objectgroup_domethod(emitters):
    group = ObjectGroup(*emitters)
    group.do_method('mock_method', 'test_arg', kwarg='test_kwarg')
    for obj in group:
        if isinstance(obj, MockEmitter):
            assert obj.mock_method_call['arg'] == 'test_arg'
            assert obj.mock_method_call['kwarg'] == 'test_kwarg'
        elif isinstance(obj, Emitter):
            assert not hasattr(obj, 'mock_method')
        else:
            assert obj is None


@pytest.mark.parametrize('emitters', [
    {'first': None},
    {'first': MockEmitter('foo')},
    {'first': Static('foo')},
    {'first': MockEmitter('foo'), 'second': None},
    {'first': MockEmitter('foo'), 'second': Static('foo'),
     'third': MockEmitter('foo')},
    {'first': MockEmitter('foo'), 'second': Static('foo'),
     'third': None, 'fourth': MockEmitter('foo')},
])
def test_objectmap_setattr(emitters):
    group = ObjectMap(emitters)
    group.setattr('mock_val', 'bar')
    for obj in group.values():
        if isinstance(obj, MockEmitter):
            assert obj.mock_val == 'bar' and obj.value == 'foo'
        elif isinstance(obj, Emitter):
            assert not hasattr(obj, 'mock_val') and obj.value == 'foo'
        else:
            assert obj is None


@pytest.mark.parametrize('emitters', [
    {'first': None},
    {'first': MockEmitter('foo')},
    {'first': Static('foo')},
    {'first': MockEmitter('foo'), 'second': None},
    {'first': MockEmitter('foo'), 'second': Static('foo'),
     'third': MockEmitter('foo')},
    {'first': MockEmitter('foo'), 'second': Static('foo'),
     'third': None, 'fourth': MockEmitter('foo')},
])
def test_objectmap_domethod(emitters):
    group = ObjectMap(emitters)
    group.do_method('mock_method', 'test_arg', kwarg='test_kwarg')
    for obj in group.values():
        if isinstance(obj, MockEmitter):
            assert obj.mock_method_call['arg'] == 'test_arg'
            assert obj.mock_method_call['kwarg'] == 'test_kwarg'
        elif isinstance(obj, Emitter):
            assert not hasattr(obj, 'mock_method')
        else:
            assert obj is None
