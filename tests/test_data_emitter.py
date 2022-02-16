"""Contains tests for the solrfixtures.data.emitter module."""
import pytest

from solrfixtures.data import emitter as em


@pytest.mark.parametrize('ranges, expected', [
    ([(0x0041, 0x0045), (0x0047, 0x0047)], list('ABCDEG')),
    ([(ord('a'), ord('g')), (ord('A'), ord('C'))],
     list('abcdefgABC'))
])
def test_makealphabet(ranges, expected):
    assert em.make_alphabet(ranges) == expected


@pytest.mark.parametrize('seed, mn, mx, weights, expected', [
    (999, 1, 10, None, [2, 10, 10, 9, 8, 8, 3, 6, 2, 4]),
    (999, 1, 10, [50, 70, 80, 85, 90, 91, 92, 93, 95, 100],
     [3, 1, 5, 2, 1, 1, 3, 1, 3, 4]),
])
def test_intemitter(seed, mn, mx, weights, expected):
    ie = em.IntEmitter(mn, mx, weights)
    ie.rng.seed(seed)
    for num in expected:
        assert ie() == num
