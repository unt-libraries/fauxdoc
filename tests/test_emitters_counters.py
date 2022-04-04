"""Contains tests for solrfixtures.emitters.counters."""
import pytest

from solrfixtures.emitters import counters


@pytest.mark.parametrize('start, template, expected', [
    (0, None, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    (1001, None, [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009]),
    (1, 'b{}', ['b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'b10']),
    (1, '{}', ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']),
    (1, '_{0}{0}_', ['_11_', '_22_', '_33_', '_44_', '_55_', '_66_']),
])
def test_autoincrementnumber_emitted_values(start, template, expected):
    em = counters.AutoIncrementNumber(start, template)
    assert em(len(expected)) == expected
    em.reset()
    assert [em() for _ in range(len(expected))] == expected
