"""Contains limited tests for the solrfixtures.emitter module."""
import pytest

from solrfixtures.emitter import StaticEmitter


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
