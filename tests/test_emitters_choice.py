"""Contains tests for the fauxdoc.emitters.choice module."""
import datetime
import random

import pytest

from fauxdoc.dtrange import dtrange
from fauxdoc.emitters.choice import chance, Choice, gaussian_choice,\
                                    poisson_choice


@pytest.mark.parametrize('seed, items, weights, cw, repl, num, repeat, exp', [
    (999, range(2), None, None, True, 10, 0, [1, 0, 1, 1, 0, 0, 1, 0, 1, 1]),
    (999, range(2), None, None, True, None, 10,
     [0, 1, 1, 0, 1, 0, 0, 0, 1, 0]),
    (999, range(1, 2), None, None, True, 10, 0,
     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (999, range(1, 2), None, None, True, None, 10,
     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    (999, range(5, 6), None, None, True, 10, 0,
     [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]),
    (999, range(1, 11), None, None, True, 10, 0,
     [8, 1, 9, 6, 5, 2, 8, 4, 8, 9]),
    (999, 'abcde', None, None, True, 10, 0,
     ['d', 'a', 'e', 'c', 'c', 'a', 'd', 'b', 'd', 'e']),
    (999, ['H', 'T'], [80, 20], None, True, 10, 0,
     ['H', 'H', 'T', 'H', 'H', 'H', 'H', 'H', 'H', 'T']),
    (999, ['H', 'T'], None, [80, 100], True, 10, 0,
     ['H', 'H', 'T', 'H', 'H', 'H', 'H', 'H', 'H', 'T']),
    (999, ['H', 'T'], [80, 20], None, True, None, 10,
     ['H', 'H', 'T', 'H', 'H', 'H', 'H', 'H', 'H', 'T']),
    (999, ['H', 'T'], [20, 80], None, True, 10, 0,
     ['T', 'H', 'T', 'T', 'T', 'H', 'T', 'T', 'T', 'T']),
    (999, ['H', 'T'], None, [20, 100], True, 10, 0,
     ['T', 'H', 'T', 'T', 'T', 'H', 'T', 'T', 'T', 'T']),
    (999, 'TTHHHHHHHH', None, None, 'after_call', 10, 0,
     ['T', 'H', 'H', 'H', 'H', 'H', 'T', 'H', 'H', 'H']),
    (999, 'HHHHT', None, None, 'after_call', None, 10,
     ['H', 'T', 'T', 'T', 'H', 'H', 'H', 'H', 'H', 'H']),
    (999, 'HT', [80, 20], None, 'after_call', None, 10,
     ['H', 'H', 'T', 'H', 'H', 'H', 'H', 'H', 'H', 'T']),
    (999, 'HT', [20, 80], None, 'after_call', None, 10,
     ['T', 'H', 'T', 'T', 'T', 'H', 'T', 'T', 'T', 'T']),
    (999, range(5), [70, 20, 7, 2, 1], None, 'after_call', 3, 10,
     [[0, 2, 1], [1, 0, 3], [1, 0, 2], [0, 3, 2], [0, 4, 1], [0, 2, 1],
      [1, 0, 2], [1, 0, 2], [1, 0, 3], [0, 2, 1]]),
    (999, range(5), [70, 20, 7, 2, 1], None, True, 3, 10,
     [[1, 0, 1], [0, 0, 0], [1, 0, 1], [1, 0, 4], [0, 0, 0], [1, 0, 1],
      [3, 0, 0], [0, 0, 0], [2, 0, 0], [0, 0, 1]]),
    (999, range(25), None, None, False, 5, 5,
     [[11, 18, 24, 17, 2], [9, 6, 8, 0, 15], [20, 3, 14, 4, 7],
      [13, 16, 19, 23, 12], [5, 10, 1, 21, 22]]),
    (999, range(25), None, None, False, None, 25,
     [11, 18, 24, 17, 2, 9, 6, 8, 0, 15, 20, 3, 14, 4, 7, 13, 16, 19, 23, 12,
      5, 10, 1, 21, 22]),
    (9999, range(25), [50] * 5 + [10] * 5 + [1] * 15, None, False, 5, 5,
     [[0, 3, 7, 12, 4], [6, 1, 2, 9, 8], [22, 14, 5, 18, 11],
      [20, 24, 13, 23, 16], [21, 17, 19, 15, 10]]),
    (9999, range(25), [50] * 5 + [10] * 5 + [1] * 15, None, False, None, 25,
     [0, 3, 7, 12, 4, 6, 1, 2, 9, 8, 22, 14, 5, 18, 11, 20, 24, 13, 23, 16, 21,
      17, 19, 15, 10]),
])
def test_choice(seed, items, weights, cw, repl, num, repeat, exp):
    after_call = repl == 'after_call'
    replace = repl or after_call
    ce = Choice(items, weights=weights, cum_weights=cw, replace=replace,
                replace_only_after_call=after_call, rng_seed=seed)
    result = [ce(num) for _ in range(repeat)] if repeat else ce(num)
    assert result == exp


@pytest.mark.parametrize(
    'emitter, exp_unique_vals, exp_unique_items, exp_emits_unique,'
    'num_to_emit, post_emit_exp_unique_vals, post_emit_exp_unique_items,'
    'post_emit_exp_emits_unique', [
        (Choice(range(5), replace=True), 5, 5, False, 10, 5, 5, False),
        (Choice(range(5), replace_only_after_call=True),
         5, 5, False, 5, 5, 5, False),
        (Choice(range(5), replace=False), 5, 5, True, 3, 2, 2, True),
        (Choice(range(5), replace=False), 5, 5, True, 5, 0, 0, True),
        (Choice([0, 1, 0, 2, 2], replace=False, rng_seed=999),
         3, 5, False, 3, 2, 2, True),
        (Choice([0, 1, 0, 2, 2], replace=True, rng_seed=999),
         3, 5, False, 10, 3, 5, False),
    ]
)
def test_choice_uniqueness_properties(emitter, exp_unique_vals,
                                      exp_unique_items, exp_emits_unique,
                                      num_to_emit, post_emit_exp_unique_vals,
                                      post_emit_exp_unique_items,
                                      post_emit_exp_emits_unique):
    assert emitter.num_unique_values == exp_unique_vals
    assert emitter.num_unique_items == exp_unique_items
    assert emitter.emits_unique_values == exp_emits_unique
    emitter(num_to_emit)
    assert emitter.num_unique_values == post_emit_exp_unique_vals
    assert emitter.num_unique_items == post_emit_exp_unique_items
    assert emitter.emits_unique_values == post_emit_exp_emits_unique
    emitter.reset()
    assert emitter.num_unique_values == exp_unique_vals
    assert emitter.num_unique_items == exp_unique_items
    assert emitter.emits_unique_values == exp_emits_unique


@pytest.mark.parametrize('items, repl, num, repeat, exp_error', [
    (range(9), 'after_call', 10, 0,
     '10 new unique values were requested, out of 9 possible selections.'),
    (range(9), False, 10, 0,
     '10 new unique values were requested, out of 9 possible selections.'),
    (range(9), False, None, 10,
     '1 new unique value was requested, out of 0 possible selections.'),
    (range(9), False, 3, 4,
     '3 new unique values were requested, out of 0 possible selections.'),
    (range(10), False, 3, 4,
     '3 new unique values were requested, out of 1 possible selection.'),
])
def test_choice_not_enough_unique_values(items, repl, num, repeat, exp_error):
    after_call = repl == 'after_call'
    replace = repl or after_call
    ce = Choice(items, replace=replace, replace_only_after_call=after_call)
    with pytest.raises(ValueError) as excinfo:
        [ce(num) for _ in range(repeat)] if repeat else ce(num)
    assert exp_error in str(excinfo.value)


def test_choice_reset_reshuffles_when_no_replacement():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=False, rng_seed=999)
    assert ce(4) == [0, 2, 3, 1]
    ce.reset()
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert ce(4) == [0, 2, 3, 1]


def test_choice_seed_reseeds_and_reshuffles_when_no_replacement():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=False, rng_seed=999)
    assert ce.rng_seed == 999
    assert ce(4) == [0, 2, 3, 1]
    ce.seed(9999)
    assert ce.rng_seed == 9999
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert ce(4) == [0, 3, 1, 2]


def test_choice_setting_rngseed_does_not_reshuffle_when_no_replacement():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=False, rng_seed=999)
    assert ce(2) == [0, 2]
    ce.rng_seed = 9999
    assert ce.num_unique_values == 2
    assert ce.num_unique_items == 2
    assert ce(2) == [3, 1]


def test_choice_setting_rng_does_not_reshuffle_when_no_replacement():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=False, rng_seed=999)
    assert ce(2) == [0, 2]
    ce.rng = random.Random(9999)
    assert ce.num_unique_values == 2
    assert ce.num_unique_items == 2
    assert ce(2) == [3, 1]


def test_choice_setting_rngseed_does_not_change_output_until_reset():
    ce = Choice(range(4), replace=True, rng_seed=999)
    assert ce(10) == [3, 0, 3, 2, 1, 0, 3, 1, 3, 3]
    ce.reset()
    ce.rng_seed = 9999
    assert ce(10) == [3, 0, 3, 2, 1, 0, 3, 1, 3, 3]
    ce.reset()
    assert ce(10) == [3, 0, 0, 3, 1, 0, 3, 3, 1, 2]


def test_choice_setting_rng_immediately_changes_output():
    ce = Choice(range(4), replace=True, rng_seed=999)
    assert ce(10) == [3, 0, 3, 2, 1, 0, 3, 1, 3, 3]
    ce.reset()
    ce.rng = random.Random(9999)
    assert ce(10) == [3, 0, 0, 3, 1, 0, 3, 3, 1, 2]


def test_choice_items_is_readonly():
    ce = Choice(range(4))
    assert ce.items == range(4)
    with pytest.raises(AttributeError):
        ce.items = range(4)


def test_choice_emitsuniquevalues_is_readonly():
    ce = Choice(range(4))
    assert not ce.emits_unique_values
    with pytest.raises(AttributeError):
        ce.emits_unique_values = False


def test_choice_numuniquevalues_is_readonly():
    ce = Choice(range(4))
    assert ce.num_unique_values == 4
    with pytest.raises(AttributeError):
        ce.num_unique_values = 4


def test_choice_numuniqueitems_is_readonly():
    ce = Choice(range(4))
    assert ce.num_unique_items == 4
    with pytest.raises(AttributeError):
        ce.num_unique_items = 4


def test_choice_weights_is_immutable():
    ce = Choice(range(4), weights=[97, 1, 1, 1])
    assert ce.weights == (97, 1, 1, 1)
    with pytest.raises(TypeError):
        ce.weights[0] = 1


def test_choice_cumweights_is_immutable():
    ce = Choice(range(4), cum_weights=[97, 98, 99, 100])
    assert ce.cum_weights == (97, 98, 99, 100)
    with pytest.raises(TypeError):
        ce.cum_weights[0] = 1


def test_choice_setting_weights_sets_cumweights():
    ce = Choice(range(4))
    ce.weights = [97, 1, 1, 1]
    assert ce.cum_weights == (97, 98, 99, 100)


def test_choice_setting_cumweights_sets_weights():
    ce = Choice(range(4))
    ce.cum_weights = [97, 98, 99, 100]
    assert ce.weights == (97, 1, 1, 1)


def test_choice_removing_weights_removes_cumweights():
    ce = Choice(range(4), weights=[97, 1, 1, 1])
    ce.weights = None
    assert ce.cum_weights is None


def test_choice_removing_cumweights_removes_weights():
    ce = Choice(range(4), weights=[97, 1, 1, 1])
    ce.cum_weights = None
    assert ce.weights is None


def test_choice_remove_weights_with_replacement():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=True, rng_seed=999)
    ce(2)
    ce.weights = None
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(10) == [3, 2, 1, 0, 3, 1, 3, 3, 0, 3]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4


def test_choice_remove_weights_no_replacement():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=False, rng_seed=999)
    ce(2)
    ce.weights = None
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert ce.emits_unique_values
    assert ce(4) == [2, 0, 3, 1]
    assert ce.num_unique_values == 0
    assert ce.num_unique_items == 0


def test_choice_remove_weights_only_replace_after_call():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace_only_after_call=True,
                rng_seed=999)
    ce(2)
    ce.weights = None
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(4) == [3, 1, 0, 2]
    assert ce(4) == [0, 2, 3, 1]
    assert ce(4) == [2, 3, 0, 1]
    assert ce(4) == [3, 0, 1, 2]
    assert ce(4) == [2, 0, 3, 1]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4


def test_choice_add_weights_with_replacement():
    ce = Choice(range(4), replace=True, rng_seed=999)
    ce(2)
    ce.weights = [97, 1, 1, 1]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(10) == [0, 0, 0, 0, 0, 0, 0, 0, 0, 3]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4


def test_choice_add_weights_no_replacement():
    ce = Choice(range(4), replace=False, rng_seed=999)
    ce(2)
    ce.weights = [97, 1, 1, 1]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert ce.emits_unique_values
    assert ce(4) == [0, 2, 3, 1]
    assert ce.num_unique_values == 0
    assert ce.num_unique_items == 0


def test_choice_add_weights_only_replace_after_call():
    ce = Choice(range(4), replace_only_after_call=True, rng_seed=999)
    ce(2)
    ce.weights = [97, 1, 1, 1]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(4) == [0, 3, 1, 2]
    assert ce(4) == [0, 2, 1, 3]
    assert ce(4) == [0, 3, 2, 1]
    assert ce(4) == [0, 3, 2, 1]
    assert ce(4) == [0, 1, 2, 3]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4


def test_choice_change_weights_with_replacement():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=True, rng_seed=999)
    ce(2)
    ce.weights = [1, 1, 1, 97]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(10) == [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4


def test_choice_change_weights_no_replacement():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=False, rng_seed=999)
    ce(2)
    ce.weights = [1, 1, 1, 97]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert ce.emits_unique_values
    assert ce(4) == [3, 2, 0, 1]
    assert ce.num_unique_values == 0
    assert ce.num_unique_items == 0


def test_choice_change_weights_only_replace_after_call():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace_only_after_call=True,
                rng_seed=999)
    ce(2)
    ce.weights = [1, 1, 1, 97]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(4) == [3, 2, 0, 1]
    assert ce(4) == [3, 1, 0, 2]
    assert ce(4) == [3, 2, 1, 0]
    assert ce(4) == [2, 3, 1, 0]
    assert ce(4) == [3, 0, 1, 2]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4


def test_choice_change_replacement__replace_to_replace_only_after_call():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=True, rng_seed=999)
    ce(10)
    ce.replace_only_after_call = True
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(4) == [1, 0, 3, 2]
    assert ce(4) == [0, 3, 1, 2]
    assert ce(4) == [0, 2, 1, 3]
    assert ce(4) == [2, 0, 3, 1]
    assert ce(4) == [0, 3, 1, 2]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    with pytest.raises(ValueError):
        ce(5)


def test_choice_change_replacement__replace_to_none():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=True, rng_seed=999)
    ce(10)
    ce.replace = False
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert ce.emits_unique_values
    assert ce(4) == [1, 0, 3, 2]
    assert ce.num_unique_values == 0
    assert ce.num_unique_items == 0
    with pytest.raises(ValueError):
        ce()


def test_choice_change_replacement__replace_only_after_call_to_replace():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace_only_after_call=True,
                rng_seed=999)
    ce(4)
    ce.replace_only_after_call = False
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(10) == [0, 0, 0, 0, 0, 0, 0, 3, 0, 0]


def test_choice_change_replacement__replace_only_after_call_to_none():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace_only_after_call=True,
                rng_seed=999)
    ce(4)
    ce.replace = False
    assert not ce.replace_only_after_call
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert ce.emits_unique_values
    assert ce(4) == [0, 2, 3, 1]
    assert ce.num_unique_values == 0
    assert ce.num_unique_items == 0
    with pytest.raises(ValueError):
        ce()


def test_choice_change_replacement__none_to_replace():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=False, rng_seed=999)
    ce(2)
    ce.replace = True
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(10) == [0, 0, 0, 0, 0, 0, 0, 3, 0, 0]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4


def test_choice_change_replacement__none_to_replace_only_after_call():
    ce = Choice(range(4), weights=[97, 1, 1, 1], replace=False,
                replace_only_after_call=False, rng_seed=999)
    ce(2)
    ce.replace_only_after_call = True
    assert ce.replace
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    assert not ce.emits_unique_values
    assert ce(4) == [0, 2, 3, 1]
    assert ce(4) == [0, 3, 1, 2]
    assert ce(4) == [0, 3, 2, 1]
    assert ce(4) == [0, 2, 1, 3]
    assert ce(4) == [0, 3, 1, 2]
    assert ce.num_unique_values == 4
    assert ce.num_unique_items == 4
    with pytest.raises(ValueError):
        ce(5)


def test_choice_cannot_init_empty_items():
    with pytest.raises(ValueError):
        Choice(range(0))


def test_choice_cannot_init_weights_and_cumweights():
    with pytest.raises(TypeError) as excinfo:
        Choice(['abc'], weights=[10, 50, 40], cum_weights=[10, 60, 100])
    assert "Only one of 'weights' or 'cum_weights'" in str(excinfo.value)


@pytest.mark.parametrize('items, bad_weights, are_cumulative, noun', [
    ([0, 1, 2, 3], [40, 50], False, 'item'),
    ([0, 1, 2, 3], [40, 50], True, 'item'),
    ([0, 1], [50, 10, 2], False, None),
    ([0, 1], [50, 10, 2], True, None)
])
def test_choice_incorrect_weights(items, bad_weights, are_cumulative, noun):
    kwargs = {
        'cum_weights' if are_cumulative else 'weights': bad_weights,
        'noun': noun
    }
    with pytest.raises(ValueError) as excinfo:
        Choice(items, **kwargs)
    error_msg = str(excinfo.value)
    assert f"({len(items)}" in error_msg
    assert f"({len(bad_weights)}" in error_msg
    if noun:
        assert f"{noun} choices" in error_msg
    if are_cumulative:
        assert "choice cum_weights" in error_msg
    else:
        assert "choice weights" in error_msg


@pytest.mark.parametrize('items, bad_weights, are_cumulative', [
    ([0, 1, 2, 3], [40, 50], False),
    ([0, 1, 2, 3], [40, 50], True),
    ([0, 1], [50, 10, 2], False),
    ([0, 1], [50, 10, 2], True),
])
def test_choice_change_weights_to_incorrect_weights(items, bad_weights,
                                                    are_cumulative):
    attr = 'cum_weights' if are_cumulative else 'weights'
    ce = Choice(items, **{attr: [10] * len(items)})
    with pytest.raises(ValueError) as excinfo:
        setattr(ce, attr, bad_weights)
    error_msg = str(excinfo.value)
    assert f"({len(items)}" in error_msg
    assert f"({len(bad_weights)}" in error_msg


def test_choice_change_noun():
    ce = Choice(range(4), noun='name')
    with pytest.raises(ValueError) as excinfo1:
        ce.weights = [1]
    error_msg1 = str(excinfo1.value)
    assert 'name choices' in error_msg1
    ce.noun = 'title'
    with pytest.raises(ValueError) as excinfo2:
        ce.weights = [1]
    error_msg2 = str(excinfo2.value)
    assert 'title choices' in error_msg2


@pytest.mark.parametrize('seed, mn, mx, weights, expected', [
    (999, (2015, 1, 1), (2015, 1, 2), None,
     [(2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1),
      (2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1), (2015, 1, 1)]),
    (999, (2015, 1, 1), (2015, 1, 6), None,
     [(2015, 1, 4), (2015, 1, 1), (2015, 1, 5), (2015, 1, 3), (2015, 1, 3),
      (2015, 1, 1), (2015, 1, 4), (2015, 1, 2), (2015, 1, 4), (2015, 1, 5)]),
    (999, (2015, 1, 1), (2015, 1, 6), [60, 20, 10, 5, 5],
     [(2015, 1, 2), (2015, 1, 1), (2015, 1, 3), (2015, 1, 1), (2015, 1, 1),
      (2015, 1, 1), (2015, 1, 2), (2015, 1, 1), (2015, 1, 2), (2015, 1, 3)]),
])
def test_choice_dates(seed, mn, mx, weights, expected):
    dates = dtrange(datetime.date(*mn), datetime.date(*mx))
    de = Choice(dates, weights=weights, rng_seed=seed)
    assert de(len(expected)) == [datetime.date(*i) for i in expected]


@pytest.mark.parametrize('seed, mn, mx, step, step_unit, weights, expected', [
    (999, (0, 0, 0), (0, 0, 0), 1, 'seconds', None,
     [(18, 45, 8), (1, 55, 17), (20, 56, 23), (13, 46, 12), (11, 46, 24),
      (3, 10, 10), (19, 10, 4), (7, 38, 5), (19, 4, 5), (20, 17, 0)]),
    (999, (0, 0), (0, 0), 60, 'seconds', None,
     [(18, 45), (1, 55), (20, 56), (13, 46), (11, 46), (3, 10), (19, 10),
      (7, 38), (19, 4), (20, 17)]),
    (999, (5, 0, 0), (5, 30, 0), 1, 'seconds', None,
     [(5, 23, 26), (5, 2, 24), (5, 26, 10), (5, 17, 12), (5, 14, 43),
      (5, 3, 57), (5, 23, 57), (5, 9, 32), (5, 23, 50), (5, 25, 21)]),
    # The next examples show weighting a time range by sub-ranges -- in
    # these cases by hour. E.g., [1] * 60 gives each minute from 5:00
    # to 5:59 a weight of 1, etc.
    (999, (5, 0, 0), (12, 0, 0), 1, 'minutes',
     [1] * 60 + [1] * 60 + [5] * 60 + [10] * 60 + [5] * 60 + [3] * 60 +
     [2] * 60,
     [(9, 49), (7, 1), (10, 31), (8, 50), (8, 37), (7, 18), (9, 54), (8, 9),
      (9, 53), (10, 16)]),
    (999, (6, 0, 0), (9, 0, 0), 10, 'minutes', [10] * 6 + [5] * 6 + [2] * 6,
     [(7, 30), (6, 0), (7, 50), (6, 50), (6, 50), (6, 10), (7, 40), (6, 30),
      (7, 40), (7, 50)]),
    (999, (20, 0, 1), (20, 1, 0), 20, 'seconds', [50, 30, 20],
     [(20, 0, 21), (20, 0, 1), (20, 0, 41), (20, 0, 21), (20, 0, 1),
      (20, 0, 1), (20, 0, 21), (20, 0, 1), (20, 0, 21), (20, 0, 41)]),
])
def test_choice_times(seed, mn, mx, step, step_unit, weights, expected):
    times = dtrange(datetime.time(*mn), datetime.time(*mx), step, step_unit)
    te = Choice(times, weights=weights, rng_seed=seed)
    assert te(len(expected)) == [datetime.time(*i) for i in expected]


@pytest.mark.parametrize('seed, mn, mx, step, step_unit, weights, expected', [
    (999, (2016, 1, 1, 20, 0), (2016, 1, 2, 7, 0), 1, 'minutes', None,
     [(2016, 1, 2, 4, 35, 0), (2016, 1, 1, 20, 52, 0), (2016, 1, 2, 5, 35, 0),
      (2016, 1, 2, 2, 18, 0), (2016, 1, 2, 1, 23, 0), (2016, 1, 1, 21, 27, 0),
      (2016, 1, 2, 4, 47, 0), (2016, 1, 1, 23, 29, 0), (2016, 1, 2, 4, 44, 0),
      (2016, 1, 2, 5, 17, 0)]),
    (999, (2016, 1, 1, 0, 0), (2017, 1, 1, 0, 0), 12, 'hours', None,
     [(2016, 10, 12, 12, 0, 0), (2016, 1, 30, 0, 0, 0),
      (2016, 11, 15, 0, 0, 0), (2016, 7, 28, 12, 0, 0),
      (2016, 6, 28, 12, 0, 0), (2016, 2, 18, 0, 0, 0), (2016, 10, 19, 0, 0, 0),
      (2016, 4, 26, 0, 0, 0), (2016, 10, 17, 12, 0, 0),
      (2016, 11, 5, 0, 0, 0)]),
    # This shows weighting a full year by sub-ranges of months.
    (999, (2016, 1, 1, 0, 0), (2017, 1, 1, 0, 0), 1, 'hours',
     [5] * (31 * 24) + [10] * (29 * 24) + [15] * (31 * 24) + [15] * (30 * 24) +
     [5] * (31 * 24) + [2] * (30 * 24) + [2] * (31 * 24) + [5] * (31 * 24) +
     [10] * (30 * 24) + [15] * (31 * 24) + [15] * (30 * 24) + [5] * (31 * 24),
     [(2016, 10, 26, 5, 0, 0), (2016, 2, 10, 19, 0, 0),
      (2016, 11, 14, 10, 0, 0), (2016, 9, 3, 5, 0, 0), (2016, 6, 19, 1, 0, 0),
      (2016, 2, 27, 6, 0, 0), (2016, 10, 29, 21, 0, 0), (2016, 4, 7, 9, 0, 0),
      (2016, 10, 29, 0, 0, 0), (2016, 11, 8, 16, 0, 0)]),
])
def test_choice_datetimes(seed, mn, mx, step, step_unit, weights, expected):
    datetimes = dtrange(datetime.datetime(*mn), datetime.datetime(*mx), step,
                        step_unit)
    dte = Choice(datetimes, weights=weights, rng_seed=seed)
    assert dte(len(expected)) == [datetime.datetime(*i) for i in expected]


@pytest.mark.parametrize('seed, items, mu, weight_floor, expected', [
    (999, range(1, 10), 1, 0,
     [2, 1, 2, 1, 1, 1, 2, 1, 2, 2, 1, 5, 1, 1, 1, 2, 1, 3, 4, 1]),
    (999, range(1, 10), 1.5, 0,
     [3, 1, 3, 2, 2, 1, 3, 1, 3, 3, 1, 6, 1, 1, 2, 2, 1, 3, 5, 1]),
    (999, range(1, 10), 0.1, 0,
     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1]),
    (999, range(1, 10), 2, 0,
     [3, 1, 4, 2, 2, 1, 3, 2, 3, 4, 1, 6, 1, 1, 2, 3, 1, 4, 6, 1]),
    (999, range(1, 10), 3, 0,
     [4, 1, 5, 3, 3, 1, 4, 2, 4, 5, 1, 8, 2, 2, 3, 4, 2, 5, 7, 2]),
    (999, range(1, 10), 10, 0,
     [9, 5, 9, 8, 8, 5, 9, 7, 9, 9, 5, 9, 6, 6, 8, 8, 6, 9, 9, 6]),
    (999, range(1, 10), 20, 0,
     [9, 7, 9, 9, 9, 7, 9, 8, 9, 9, 7, 9, 8, 8, 9, 9, 8, 9, 9, 8]),
    (999, range(1, 10), 1, 0.05,
     [6, 1, 7, 2, 2, 1, 6, 1, 6, 7, 1, 9, 1, 1, 2, 4, 1, 7, 9, 1]),
    (999, range(1, 10), 1, 0.5,
     [8, 1, 8, 6, 5, 2, 8, 3, 8, 8, 1, 9, 2, 3, 6, 7, 3, 8, 9, 3]),
])
def test_poisson_choice(seed, items, mu, weight_floor, expected):
    em = poisson_choice(items, mu=mu, weight_floor=weight_floor, rng_seed=seed)
    assert em(len(expected)) == expected


@pytest.mark.parametrize('seed, items, mu, sigma, weight_floor, expected', [
    (999, range(1, 10), 0, 1, 0,
     [1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 3, 1, 1, 1, 1, 1, 2, 3, 1]),
    (999, range(1, 10), 1, 1, 0,
     [2, 1, 2, 2, 1, 1, 2, 1, 2, 2, 1, 4, 1, 1, 2, 2, 1, 2, 3, 1]),
    (999, range(1, 10), 2, 1, 0,
     [3, 1, 3, 2, 2, 1, 3, 2, 3, 3, 1, 4, 1, 2, 2, 3, 1, 3, 4, 1]),
    (999, range(1, 10), 3, 1, 0,
     [4, 2, 4, 3, 3, 2, 4, 3, 4, 4, 2, 5, 2, 2, 3, 4, 2, 4, 5, 2]),
    (999, range(1, 10), 10, 1, 0,
     [9, 8, 9, 9, 9, 8, 9, 9, 9, 9, 8, 9, 8, 9, 9, 9, 9, 9, 9, 9]),
    (999, range(1, 10), 20, 1, 0,
     [9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9]),
    (999, range(1, 10), 1, 0.5, 0,
     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1]),
    (999, range(1, 10), 1, 1.5, 0,
     [3, 1, 3, 2, 2, 1, 3, 1, 3, 3, 1, 5, 1, 1, 2, 2, 1, 3, 4, 1]),
    (999, range(1, 10), 1, 2, 0,
     [3, 1, 4, 2, 2, 1, 3, 1, 3, 4, 1, 6, 1, 1, 2, 3, 1, 4, 6, 1]),
    (999, range(1, 10), 10, 5, 0,
     [8, 2, 9, 7, 6, 3, 8, 5, 8, 9, 3, 9, 4, 5, 7, 8, 5, 9, 9, 4]),
    (999, range(1, 10), 0, 1, 0.01,
     [2, 1, 5, 1, 1, 1, 2, 1, 2, 4, 1, 9, 1, 1, 1, 2, 1, 5, 9, 1]),
    (999, range(1, 10), 0, 1, 0.1,
     [7, 1, 8, 5, 4, 1, 7, 2, 7, 8, 1, 9, 1, 2, 5, 6, 2, 8, 9, 1]),
])
def test_gaussian_choice(seed, items, mu, sigma, weight_floor, expected):
    gce = gaussian_choice(items, mu=mu, sigma=sigma, weight_floor=weight_floor,
                          rng_seed=seed)
    assert gce(len(expected)) == expected


@pytest.mark.parametrize('seed, percent_chance, expected', [
    (999, -10,
     [False, False, False, False, False, False, False, False, False, False]),
    (999, 0,
     [False, False, False, False, False, False, False, False, False, False]),
    (999, 0.25,
     [False, True, False, False, False, True, False, False, False, False]),
    (999, 0.455,
     [False, True, False, False, False, True, False, True, False, False]),
    (999, 0.8,
     [True, True, False, True, True, True, True, True, True, False]),
    (999, 1.0,
     [True, True, True, True, True, True, True, True, True, True]),
    (999, 10000,
     [True, True, True, True, True, True, True, True, True, True]),
])
def test_chance(seed, percent_chance, expected):
    chance_em = chance(percent_chance, rng_seed=seed)
    assert chance_em(len(expected)) == expected
