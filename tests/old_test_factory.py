"""
Contains tests for solrfixtures.factory module.
"""
import datetime
import itertools

import pytest
import pytz


def test_solrfixturefactory_make_basic_fields(data_emitter, gen_factory,
                                              profile, fixture_factory):
    """
    The `SolrFixtureFactory` `make` function should make and return a
    set of docs with fields corresponding to a particular SolrProfile
    object. For this test we have no unique or multi-valued fields.
    """
    user_fields = ['id', 'code', 'title', 'creation_date', 'suppressed']
    alphabet = list('abcdefghijklmnopqrstuvwxyz')
    defaults = {
        'string': {'mn': 1, 'mx': 8},
        'int': {'mn': 1, 'mx': 999999},
        'date': {'mn': (2018, 10, 29, 0, 0), 'mx': (2018, 10, 31, 0, 0)},
        'text': {'mn_words': 1, 'mx_words': 5, 'mn_word_len': 2,
                 'mx_word_len': 6}
    }

    gens = gen_factory(data_emitter(alphabet, defaults))
    prof = profile('test', user_fields, None, gens)
    factory = fixture_factory(prof)
    docs = factory.make(1000)

    values = {fname: [d[fname] for d in docs] for fname in user_fields}
    title_words_lists = [v.split(' ') for v in values['title']]
    title_words = [w for words_list in title_words_lists for w in words_list]
    min_date = datetime.datetime(*defaults['date']['mn'], tzinfo=pytz.utc)
    max_date = datetime.datetime(*defaults['date']['mx'], tzinfo=pytz.utc)

    assert len(docs) == 1000
    assert all(1 <= v <= 999999 for v in values['id'])
    assert all(ch in alphabet for val in values['code'] for ch in val)
    assert all(1 <= len(v) <= 8 for v in values['code'])
    assert all(1 <= len(wl) <= 5 for wl in title_words_lists)
    assert all(2 <= len(w) <= 6 for w in title_words)
    assert all(min_date <= v <= max_date for v in values['creation_date'])
    assert all(v in (True, False) for v in values['suppressed'])


def test_solrfixturefactory_make_multi_fields(profile, fixture_factory):
    """
    The `SolrFixtureFactory` `make` function should make and return a
    set of docs with fields corresponding to a particular
    SolrProfile object. For this test we use multi-valued fields.
    """
    user_fields = ('notes', 'children_ids')
    prof = profile('test', user_fields)
    factory = fixture_factory(prof)
    docs = factory.make(1000)

    values = {fname: [d[fname] for d in docs] for fname in user_fields}
    ftypes = {fname: f['pytype'] for fname, f in prof.fields.items()}

    assert len(docs) == 1000
    assert all(isinstance(v, ftypes['notes'])
               for vlist in values['notes']
               for v in vlist)
    assert all(isinstance(v, ftypes['children_ids'])
               for vlist in values['children_ids']
               for v in vlist)
    assert all(1 <= len(vlist) <= 10 for vlist in values['notes'])
    assert all(1 <= len(vlist) <= 10 for vlist in values['children_ids'])


@pytest.mark.parametrize('fields, defaults, attempted, expected', [
    (['id'], {'int': {'mn': 1, 'mx': 2000}}, 1000, 1000),
    (['code'], {'string': {'mn': 1, 'mx': 5}}, 1000, 1000),
    (['code'], {'string': {'mn': 1, 'mx': 1}}, 1000, 26),
    (['suppressed'], None, 1000, 2),
    (['creation_date'], None, 1000, 1000),
    (['title'], None, 1000, 1000),
])
def test_solrfixturefactory_make_unique_fields(fields, defaults, attempted,
                                               expected, data_emitter,
                                               gen_factory, profile,
                                               fixture_factory):
    """
    The `SolrFixtureFactory` `make` method should make and return a set
    of docs with fields corresponding to a particular SolrProfile
    object. This tests unique fields.
    """
    default_alphabet = list('abcdefghijklmnopqrstuvwxyz')
    gens = gen_factory(data_emitter(default_alphabet, defaults))
    prof = profile('test', fields, fields, gens)
    factory = fixture_factory(prof)
    docs = factory.make(attempted)

    values = {fname: [d[fname] for d in docs] for fname in prof.fields}

    assert len(docs) == expected
    # converting the generated values list to a set tests uniqueness
    assert all(len(set(values[fname])) == expected for fname in values)


@pytest.mark.parametrize('fields, unique, defaults, attempted, expected', [
    (['id', 'title'], ['id'], {'int': {'mn': 1, 'mx': 2000}}, 1000, 1000),
    (['id', 'title'], ['title'], None, 1000, 1000),
    (['code', 'title'], ['code'], {'string': {'mn': 1, 'mx': 1}}, 1000, 26),
    (['code', 'title'], ['code', 'title'], {'string': {'mn': 1, 'mx': 1}},
     1000, 26),
])
def test_solrfixturefactory_makemore(fields, unique, defaults, attempted,
                                     expected, data_emitter, gen_factory,
                                     profile, fixture_factory):
    """
    The `SolrFixtureFactory` `make_more` method should behave like the
    `make` method, except it takes a list of existing docs, makes
    the requested number of additional docs using a combination of
    the two lists for determining uniqueness, and then it returns the
    list of new docs without modifying the original.
    """
    default_alphabet = list('abcdefghijklmnopqrstuvwxyz')
    gens = gen_factory(data_emitter(default_alphabet, defaults))
    prof = profile('test', fields, unique, gens)
    factory = fixture_factory(prof)

    attempted_first = int(expected / 2)
    attempted_second = attempted - attempted_first
    first_docset = factory.make(attempted_first)
    first_docset_copy = list(first_docset)
    second_docset = factory.make_more(first_docset, attempted_second)
    docs = first_docset + second_docset

    values = {fname: [d[fname] for d in docs] for fname in prof.fields}

    assert len(first_docset) == attempted_first
    assert first_docset == first_docset_copy
    assert len(docs) == expected
    assert all(len(values[fname]) == expected for fname in values)
    assert all(len(set(values[fname])) == expected for fname in unique)


def test_solrfixturefactory_custom_gens(gen_factory, profile, fixture_factory):
    """
    Test a realistic use case for making Solr fixtures.

    This is adapted from a Django Haystack-based profile we use for one
    of our Django projects.
    """
    gens = gen_factory()

    def haystack_id(doc):
        return f"{doc['django_ct']}.{doc['django_id']}"

    def id_(doc):
        return doc['django_id']

    fields = ('haystack_id', 'django_ct', 'django_id', 'id', 'type', 'code',
              'creation_date', 'suppressed')
    unique = ('haystack_id', 'django_id', 'id', 'code')
    prof = profile('test', fields, unique)
    prof.set_field_gens(
        ('django_ct', gens.static('base.location')),
        ('django_id', gens.type('int', mn=1, mx=999999)),
        ('haystack_id', gens(haystack_id)),
        ('id', gens(id_)),
        ('code', gens.type('string', mn=3, mx=5)),
        ('type', gens.static('Location'))
    )
    factory = fixture_factory(prof)
    docs = factory.make(1000)

    values = {fname: [d[fname] for d in docs] for fname in fields}
    ftypes = {fname: f['pytype'] for fname, f in prof.fields.items()}

    assert len(docs) == 1000
    assert all(len(values[fname]) == 1000 for fname in values)
    assert all(len(set(values[fname])) == 1000 for fname in unique)
    assert all(isinstance(v, ftypes[fname])
               for fname in values
               for v in values[fname])
    assert all(v == 'base.location' for v in values['django_ct'])
    assert all(1 <= int(v) <= 999999 for v in values['django_id'])
    assert all(d['haystack_id'] == f"{d['django_ct']}.{d['django_id']}"
               for d in docs)
    assert all(d['id'] == int(d['django_id']) for d in docs)
    assert all(3 <= len(v) <= 5 for v in values['code'])
    assert all(v == 'Location' for v in values['type'])


@pytest.mark.parametrize('profgen_fields, callgen_fields', [
    (None, None),
    (('django_ct', 'django_id'), None),
    (None, ('django_ct', 'django_id')),
    (('django_ct', 'django_id'), ('id', 'type')),
    (('django_ct', 'django_id'), ('django_ct', 'type')),
    (('django_ct', 'django_id'), ('django_ct', 'type', 'code', 'label')),
], ids=[
    'no field gen overrides',
    'profile gens only',
    'call gens only',
    'profile gens and call gens, no overlap',
    'profile gens and call gens, with overlap',
    'all field gens overridden'
])
def test_solrfixturefactory_fieldgen_precedence(profgen_fields, callgen_fields,
                                                data_emitter, gen_factory,
                                                profile, fixture_factory):
    """
    This tests to make sure gens and gen overrides fire using the
    correct precedence. Setting field gens on the `SolrProfile` object
    overrides the fixture factory's default auto generators. Then,
    passing field gens to the fixture

    Overrides
    for those can then be passed when calling the fixture factory's
    `make` methods.
    """
    fields = ('django_ct', 'django_id', 'id', 'type', 'code', 'label')
    profgen_fields = profgen_fields or tuple()
    callgen_fields = callgen_fields or tuple()

    expected_use_callgen = callgen_fields
    expected_use_profgen = tuple(set(profgen_fields) - set(callgen_fields))
    expected_use_basegen = tuple(set(fields) - set(profgen_fields)
                                 - set(callgen_fields))

    # Test logic: a profile-level gen returns 1; a call-level gen
    # returns 2. (These numbers will automatically be converted to the
    # correct type based on the field). We set up the default emitter
    # so that `int` fields generate a minimum of 3 and `string` fields
    # use a simple a-z alphabet to avoid possible conflicts. Then we
    # can check these values in the final doc set to confirm which
    # level of gen was used.
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    emitter = data_emitter(alphabet, {'int': {'mn': 3}})
    gens = gen_factory(emitter)

    profgen = gens.static(1)
    callgen = gens.static(2)
    profgens = [(fname, profgen) for fname in profgen_fields]
    callgens = {fname: callgen for fname in callgen_fields}
    prof = profile('test', fields, None, gens, profgens)
    factory = fixture_factory(prof)
    docs = factory.make(10, **callgens)

    values = {fname: [d[fname] for d in docs] for fname in prof.fields}

    assert len(docs) == 10
    assert all(int(v) == 1
               for fname in expected_use_profgen
               for v in values[fname])
    assert all(int(v) == 2
               for fname in expected_use_callgen
               for v in values[fname])
    assert all(v not in (1, 2)
               for fname in expected_use_basegen
               for v in values[fname])


@pytest.mark.parametrize('profgen_fields, auto_fields, callgen_fields', [
    (('type', 'id', 'label'), None, None),
    (('type', 'id', 'label'), None, ('code', 'django_id')),
    (('type', 'id', 'label'), None, ('id', 'code')),
    (('code', 'type', 'label'), None, ('id', 'code')),
    (('type', 'id', 'label'), None, ('id', 'type')),
    (('code', 'type', 'label', 'id'), ('code', 'id'), ('id', 'code')),
], ids=[
    'profile gens only',
    'profile gens and call gens, no overlap',
    'profile gens and call gens, some overlap',
    'profile gens and call gens, different overlap',
    'profile gens and call gens, full overlap',
    'profile gens with auto and call gens',
])
def test_solrfixturefactory_fieldgen_order(profgen_fields, auto_fields,
                                           callgen_fields, data_emitter,
                                           gen_factory, profile,
                                           fixture_factory):
    """
    This tests to make sure field gen overrides fire in the correct
    order. Setting field gens on the `SolrProfile` object sets what
    order those field gens get called in when the fixture factory makes
    fixtures. Call-level overrides then fire in the order set via the
    profile. For fields that need to be generated in a particular order
    where it doesn't make sense to specify a custom gen at the profile
    level, you can include the field in the profile definition but use
    the keyword 'auto' in place of an actual gen.
    """
    fields = ('django_ct', 'django_id', 'id', 'type', 'code', 'label')
    profgen_fields = profgen_fields or tuple()
    callgen_fields = callgen_fields or tuple()
    auto_fields = auto_fields or tuple()

    # Test logic: A custom gen uses a global iterator to increase and
    # return a count number each time a field using that gen is called.
    # We set up the default emitter so that `int` fields generate a min
    # of 10000 and `string` fields use a simple a-z alphabet to avoid
    # possible conflicts. We use the custom counter gen for certain
    # fields at the profile level and at the call level, and then we
    # compare the numerical order of output values to the expected
    # field sort order for each doc.
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    emitter = data_emitter(alphabet, {'int': {'mn': 10000}})
    gens = gen_factory(emitter)

    count = itertools.count()
    countgen = gens(lambda r: next(count))
    profgens = [(fname, 'auto' if fname in auto_fields else countgen)
                for fname in profgen_fields]
    callgens = {fname: countgen for fname in callgen_fields}
    prof = profile('test', fields, None, gens, profgens)
    factory = fixture_factory(prof)
    docs = factory.make(100, **callgens)

    assert len(docs) == 100
    for doc in docs:
        generated_values = [int(doc[fn]) for fn in profgen_fields]
        assert generated_values == sorted(generated_values)
