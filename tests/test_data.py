"""
Contains tests for solrfixtures.data module.
"""
import datetime

import pytest
import pytz


@pytest.mark.parametrize('emtype, defaults, overrides, vcheck', [
    ('int', {'mx': 5}, None, lambda v: v <= 5),
    ('int', None, {'mx': 5}, lambda v: v <= 5),
    ('int', {'mx': 5}, {'mn': 3}, lambda v: 3 <= v <= 5),
    ('int', {'mx': 10}, {'mn': 3, 'mx': 5}, lambda v: 3 <= v <= 5),
    ('int', {'mn': 5, 'mx': 10}, None, lambda v: 5 <= v <= 10),
    ('string', {'mn': 5}, None, lambda v: len(v) >= 5),
    ('string', {'alphabet': 'abcd'}, None,
     lambda v: all(char in 'abcd' for char in v)),
    ('string', {'alphabet': 'abcd'}, {'alphabet': 'ab'},
     lambda v: all(char in 'ab' for char in v))
])
def test_dataemitter_parameters(emtype, defaults, overrides, vcheck,
                                data_emitter):
    """
    When instantiating a `DataEmitter` object, setting emitter defaults
    individually via the `emitter_defaults` param should override
    those particular defaults. Then, emitting values via the `emit`
    method should utilize those defaults, UNLESS they are overridden in
    the method call.
    """
    em_defaults = defaults if defaults is None else {emtype: defaults}
    em = data_emitter(emitter_defaults=em_defaults)
    params = overrides or {}
    values = (em.emit(emtype, **params) for _ in range(0, 100))
    assert all(vcheck(v) for v in values)


@pytest.mark.parametrize('choices, repeatable, try_num, exp_num', [
    (list(range(0, 10)), True, 1000, 1000),
    (list(range(0, 10)), False, 1000, 10),
    (list(range(0, 10000)), True, 1000, 1000),
    (list(range(0, 10000)), False, 1000, 1000),
    (list(range(0, 1000)), True, 1000, 1000),
    (list(range(0, 1000)), False, 1000, 1000),
])
def test_solrdatagenfactory_choice(choices, repeatable, try_num, exp_num,
                                   gen_factory):
    """
    The `SolrDataGenFactory` `choice` method should return a gen
    function that chooses from the given choices list. If `repeatable`
    is True, then choices can be repeated.
    """
    gen = gen_factory().choice(choices, repeatable)
    values = [v for v in (gen({}) for _ in range(0, try_num)) if v is not None]
    assert len(values) == exp_num
    assert all(v in choices for v in values)
    if not repeatable:
        assert len(set(values)) == exp_num


@pytest.mark.parametrize('choices, multi_num, repeatable, try_num, exp_num, '
                         'exp_last_num', [
                             (list(range(0, 10)), 5, True, 1000, 1000, 5),
                             (list(range(0, 10)), 5, False, 1000, 2, 5),
                             (list(range(0, 10)), 6, False, 1000, 2, 4),
                             (list(range(0, 10000)), 5, True, 1000, 1000, 5),
                             (list(range(0, 10000)), 5, False, 1000, 1000, 5),
                             (list(range(0, 1000)), 5, True, 1000, 1000, 5),
                             (list(range(0, 1000)), 5, False, 1000, 200, 5),
                         ])
def test_solrdatagenfactory_multichoice(choices, multi_num, repeatable,
                                        try_num, exp_num, exp_last_num,
                                        gen_factory):
    """
    The `SolrDataGenFactory` `multi_choice` method should return a gen
    function that picks lists of choices, where each choice comes from
    the given choices list, and the number of items in each list is
    determined by a provided counter function. If `repeatable` is True,
    then choices can be repeated; if False, they cannot be repeated. If
    `repeatable` is False and the available choices run out, it should
    return an empty list each time it is called.
    """
    gen = gen_factory().multi_choice(choices, lambda: multi_num, repeatable)
    value_lists = [vl for vl in (gen({}) for _ in range(0, try_num)) if vl]
    values = [v for vlist in value_lists for v in vlist]
    last = value_lists.pop()
    assert len(value_lists) == exp_num - 1
    assert all(len(vl) == multi_num for vl in value_lists)
    assert len(last) == exp_last_num
    assert all(v in choices for v in values)
    if not repeatable:
        assert len(set(values)) == ((exp_num - 1) * multi_num) + exp_last_num


def test_solrdatagenfactory_type_string(gen_factory):
    """
    The `SolrDataGenFactory` `type` method with an `emtype` 'string'
    should return a gen function that returns an appropriate string
    value based on the mn/mx params.
    """
    alph = list('abcdefghijklmnopqrstuvwxyz')
    gen = gen_factory().type('string', mn=0, mx=10, alphabet=alph)
    values = (gen({}) for _ in range(0, 1000))
    chars = (char for string in values for char in string)
    assert all(0 <= len(v) <= 10 for v in values)
    assert all(char in alph for char in chars)


def test_solrdatagenfactory_type_text(gen_factory):
    """
    The `SolrDataGenFactory` `type` method with an `emtype` 'text'
    should return a gen function that returns an appropriate string
    value based on the given params.
    """
    gen = gen_factory().type('text', mn_words=1, mx_words=2, mn_word_len=3,
                             mx_word_len=5)
    values = (gen({}) for _ in range(0, 1000))
    words_lists = (v.split(' ') for v in values)
    words = (w for words_list in words_lists for w in words_list)
    assert all(1 <= len(w) <= 2 for w in words_lists)
    assert all(3 <= len(w) <= 5 for w in words)


def test_solrdatagenfactory_type_int(gen_factory):
    """
    The `SolrDataGenFactory` `type` method with an `emtype` 'int'
    should return a gen function that returns an appropriate integer
    value based on the mn/mx params.
    """
    gen = gen_factory().type('int', mn=0, mx=10)
    values = (gen({}) for _ in range(0, 1000))
    assert all(0 <= v <= 10 for v in values)


def test_solrdatagenfactory_type_boolean(gen_factory):
    """
    The `SolrDataGenFactory` `type` method with an `emtype` 'boolean'
    should return a gen function that returns an appropriate bool
    value.
    """
    gen = gen_factory().type('boolean')
    values = (gen({}) for _ in range(0, 10))
    assert all(v in (True, False) for v in values)


def test_solrdatagenfactory_type_date(gen_factory):
    """
    The `SolrDataGenFactory` `type` method with an `emtype` 'date'
    should return a gen function that returns an appropriate datetime
    value based on the mn/mx params.
    """
    min_tuple = (2018, 10, 29, 00, 00)
    max_tuple = (2018, 10, 31, 00, 00)
    min_date = datetime.datetime(*min_tuple, tzinfo=pytz.utc)
    max_date = datetime.datetime(*max_tuple, tzinfo=pytz.utc)
    gen = gen_factory().type('date', mn=min_tuple, mx=max_tuple)
    values = (gen({}) for _ in range(0, 1000))
    assert all(min_date <= v <= max_date for v in values)


def test_solrdatagenfactory_multitype(gen_factory):
    """
    The `SolrDataGenFactory` `multi_type` method should return a gen
    function that returns a list with the correct number of generated
    values, suitable for passing to a multi-valued Solr field.
    """
    num = 3
    gen = gen_factory().multi_type('int', lambda: num, mn=0, mx=10)
    value_lists = (gen({}) for _ in range(0, 10))
    values = (v for value_list in value_lists for v in value_list)
    assert all(len(vlist) == num for vlist in value_lists)
    assert all(0 <= v <= 10 for v in values)


def test_solrdatagenfactory_static(gen_factory):
    """
    The `SolrDataGenFactory` `static` method should return a gen
    function that returns the correct static value when called.
    """
    gen = gen_factory().static('Hello world.')
    values = (gen({}) for _ in range(0, 10))
    assert all(v == 'Hello world.' for v in values)


def test_solrdatagenfactory_staticcounter(gen_factory):
    """
    The `SolrDataGenFactory` `static_counter` method should create a
    counter function that always returns the provided number.
    """
    counter = gen_factory().static_counter(5)
    assert all(counter() == 5 for _ in range(0, 100))


def test_solrdatagenfactory_randomcounter(gen_factory):
    """
    The `SolrDataGenFactory` `random_counter` method should create a
    counter function that returns a random number between the min and
    max values provided.
    """
    counter = gen_factory().random_counter(0, 10)
    assert all(0 <= counter() <= 10 for _ in range(0, 100))


@pytest.mark.parametrize('num_cycles, max_total, mn, mx', [
    (5, 26, 1, 10),
    (5, 5, 1, 10),
    (5, 6, 1, 10),
    (100, 200, 1, 3),
])
def test_solrdatagenfactory_precisedistributioncounter(num_cycles, max_total,
                                                       mn, mx, gen_factory):
    """
    The `SolrDataGenFactory` `precise_distribution_counter` method
    should create a counter function that returns a more-or-less even
    (but not uniform) distribution of values, which should always sum
    to exactly the given `max_total` when run `num_cycles` times.
    Each count that's generated should fall within the given `mn` and
    `mx` values.
    """
    counter = gen_factory().precise_distribution_counter(num_cycles, max_total,
                                                         mn, mx)
    nonzero_count = [counter() for _ in range(0, num_cycles)]
    print(nonzero_count)
    assert sum(nonzero_count) == max_total
    assert all(counter() == 0 for _ in range(0, 100))
    assert all(mn <= num <= mx for num in nonzero_count)
