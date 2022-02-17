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
    ie = em.IntEmitter(mn, mx, weights=weights)
    ie.rng.seed(seed)
    assert [ie() for _ in expected] == expected


@pytest.mark.parametrize('mn, mx, weights, exp_num_weights', [
    (1, 10, [50, 100], 10),
    (1, 2, [50, 75, 100], 2)
])
def test_intemitter_incorrect_weights(mn, mx, weights, exp_num_weights):
    with pytest.raises(ValueError) as excinfo:
        em.IntEmitter(mn, mx, weights=weights)
    err_msg = str(excinfo.value)
    assert f'There are {exp_num_weights} integers' in err_msg
    assert f'{len(weights)} weights were provided' in err_msg


@pytest.mark.parametrize('seed, mn, mx, lweights, alpha, aweights, expected', [
    (999, 1, 5, None, 'abcde', None,
     ['d', 'aecca', 'dbdea', 'eabcd', 'beeb', 'daab', 'ec', 'ada', 'e', 'ce']),
    (999, 1, 5, [15, 85, 90, 95, 100], 'abcde', None,
     ['da', 'e', 'cca', 'db', 'de', 'a', 'ea', 'bc', 'db', 'ee']),
    (999, 1, 5, [15, 85, 90, 95, 100], 'abcde', [20, 25, 40, 80, 100],
     ['da', 'e', 'dda', 'dc', 'de', 'a', 'ea', 'cd', 'dc', 'ee']),
    (999, 1, 5, None, 'abcde', [20, 25, 40, 80, 100],
     ['d', 'aedda', 'dcdea', 'eacdd', 'ceeb', 'daab', 'ed', 'ada', 'e', 'de']),
])
def test_stringemitter(seed, mn, mx, lweights, alpha, aweights, expected):
    se = em.StringEmitter(mn, mx, alpha, len_weights=lweights,
                          alphabet_weights=aweights)
    se.rng.seed(seed)
    se.len_emitter.rng.seed(seed)
    assert [se() for _ in expected] == expected


@pytest.mark.parametrize('mn, mx, lweights, alpha, aweights, exp_lw, exp_aw', [
    (1, 5, [50, 100], 'abcde', None, 5, None),
    (1, 2, [50, 75, 100], 'abcde', None, 2, None),
    (1, 5, None, 'abcde', [50, 100], None, 5),
    (1, 5, None, 'abc', [50, 60, 70, 80, 100], None, 3),
    (1, 2, [50, 75, 100], 'abcde', [50, 100], 2, None),
])
def test_stringemitter_incorrect_weights(mn, mx, lweights, alpha, aweights,
                                         exp_lw, exp_aw):
    with pytest.raises(ValueError) as excinfo:
        em.StringEmitter(mn, mx, alphabet=alpha, len_weights=lweights,
                         alphabet_weights=aweights)
    err_msg = str(excinfo.value)
    if exp_lw is not None:
        assert f'There are {exp_lw} total possible string lengths' in err_msg
        assert f'{len(lweights)} weights were provided' in err_msg
    else:
        assert f'For a {exp_aw}-character alphabet' in err_msg
