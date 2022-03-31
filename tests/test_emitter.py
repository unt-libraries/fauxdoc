"""Contains limited tests for the solrfixtures.emitter module."""
import pytest

from solrfixtures.emitter import Emitter, RandomEmitter, StaticEmitter


# Fixtures / test data

def make_callable_class(name, attributes):
    attributes['__call__'] = lambda self, number=1: ['test'] * number
    return type(name, (object,), attributes)


PlainCallable = make_callable_class('PlainCallable', {})
CallableResetTooManyArgs = make_callable_class(
    'CallableResetTooManyArgs', {'reset': lambda self, my_arg: None}
)
CallableReset = make_callable_class(
    'CallableReset', {'reset': lambda self: None}
)
CallableSeedTooFewArgs = make_callable_class(
    'CallableSeedTooFewArgs', {'reset': lambda self: None,
                               'seed': lambda self: None}
)
CallableSeedTooManyArgs = make_callable_class(
    'CallableSeedTooManyArgs', {'reset': lambda self: None,
                                'seed': lambda self, arg1, arg2: None}
)
CallableSeed = make_callable_class(
    'CallableSeed', {'reset': lambda self: None,
                     'seed': lambda self, rng_seed: None}
)


# Tests

@pytest.mark.parametrize('em_cls, obj, val_types, exp_error_patterns', [
    (Emitter, None, None, 
     ['is not Emitter-like', 'is not callable']),
    (StaticEmitter, None, None, 
     ['is not Emitter-like', 'is not callable']),
    (RandomEmitter, None, None, 
     ['is not RandomEmitter-like', 'is not callable']),
    (Emitter, 1, None,
     ['is not Emitter-like', 'is not callable']),
    (StaticEmitter, 1, None,
     ['is not Emitter-like', 'is not callable']),
    (RandomEmitter, 1, None,
     ['is not RandomEmitter-like', 'is not callable']),
    (Emitter, lambda: None, None,
     ['is not Emitter-like', "does not take a 'number' kwarg"]),
    (StaticEmitter, lambda: None, None,
     ['is not Emitter-like', "does not take a 'number' kwarg"]),
    (RandomEmitter, lambda: None, None,
     ['is not RandomEmitter-like', "does not take a 'number' kwarg"]),
    (Emitter, lambda number=None: None, None,
     ['is not Emitter-like', 'does not return a list or tuple']),
    (StaticEmitter, lambda number=None: None, None,
     ['is not Emitter-like', 'does not return a list or tuple']),
    (RandomEmitter, lambda number=None: None, None,
     ['is not RandomEmitter-like', 'does not return a list or tuple']),
    (Emitter, PlainCallable(), None,
     ['is not Emitter-like', 'lacks a `reset` method']),
    (Emitter, CallableResetTooManyArgs(), None,
     ['is not Emitter-like', '`reset`', 'incorrect number of arguments']),
    (Emitter, CallableReset(), None, None),
    (RandomEmitter, CallableReset(), None, 
     ['is not RandomEmitter-like', 'lacks a `seed` method']),
    (Emitter, CallableSeedTooFewArgs(), None, None),
    (RandomEmitter, CallableSeedTooFewArgs(), None,
     ['is not RandomEmitter-like', '`seed`', 'incorrect number of arguments']),
    (Emitter, CallableSeedTooManyArgs(), None, None),
    (RandomEmitter, CallableSeedTooManyArgs(), None,
     ['is not RandomEmitter-like', '`seed`', 'incorrect number of arguments']),
    (Emitter, CallableSeed(), None, None),
    (RandomEmitter, CallableSeed(), None, None),
    (Emitter, StaticEmitter('test'), None, None),
    (Emitter, StaticEmitter('1'), (int,),
     ['is Emitter-like', '`str`-type', 'not `int`-type']),
    (Emitter, StaticEmitter('1'), (int, bool),
     ['is Emitter-like', '`str`-type', 'not `int` or `bool`-type']),
    (Emitter, StaticEmitter('1'), (int, float, bool),
     ['is Emitter-like', '`str`-type', 'not `int`, `float`, or `bool`-type']),
    (Emitter, StaticEmitter(1), (int,), None),
    (Emitter, StaticEmitter(1), (int, float, bool), None),
])
def test_base_emitters_checkobject(em_cls, obj, val_types, exp_error_patterns):
    if exp_error_patterns:
        with pytest.raises(TypeError) as excinfo:
            em_cls.check_object(obj, val_types)
        msg = str(excinfo.value)
        for exp_pattern in exp_error_patterns:
            assert exp_pattern in msg
    else:
        assert Emitter.check_object(obj, val_types) is not None


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
