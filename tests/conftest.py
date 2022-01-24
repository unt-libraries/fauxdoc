"""
Contains pytest test fixtures for solrfixtures tests.
"""
import pytest

import solrfixtures as sf


@pytest.fixture
def schema():
    """
    Pytest fixture that returns a set of solr field definitions as
    though from the Solr schema API. Irrelevant elements `stored`,
    `indexed`, and `required` are not included.
    """
    return {
        'uniqueKey': 'haystack_id',
        'fields': [
            {'name': 'haystack_id',
             'type': 'string',
             'multiValued': False},
            {'name': 'django_id',
             'type': 'string',
             'multiValued': False},
            {'name': 'django_ct',
             'type': 'string',
             'multiValued': False},
            {'name': 'code',
             'type': 'string',
             'multiValued': False},
            {'name': 'label',
             'type': 'string',
             'multiValued': False},
            {'name': 'type',
             'type': 'string',
             'multiValued': False},
            {'name': 'id',
             'type': 'long',
             'multiValued': False},
            {'name': 'creation_date',
             'type': 'date',
             'multiValued': False},
            {'name': 'title',
             'type': 'text_en',
             'multiValued': False},
            {'name': 'notes',
             'type': 'text_en',
             'multiValued': True},
            {'name': 'status_code',
             'type': 'string',
             'multiValued': False},
            {'name': 'children_ids',
             'type': 'long',
             'multiValued': True},
            {'name': 'children_codes',
             'type': 'string',
             'multiValued': True},
            {'name': 'parent_id',
             'type': 'long',
             'multiValued': False},
            {'name': 'parent_title',
             'type': 'text_en',
             'multiValued': False},
            {'name': 'suppressed',
             'type': 'boolean',
             'multiValued': False}],
        'dynamicFields': [
            {'name': '*_unstem_search',
             'type': 'textNoStem',
             'multiValued': True},
            {'name': '*_display',
             'type': 'string',
             'multiValued': True},
            {'name': '*_search',
             'type': 'string',
             'multiValued': True},
            {'name': '*_facet',
             'type': 'string',
             'multiValued': True}
        ]}


@pytest.fixture
def data_emitter():
    """
    Pytest fixture function that generates and returns an appropriate
    DataEmitter object.
    """
    def _data_emitter(alphabet=None, emitter_defaults=None):
        return sf.DataEmitter(alphabet, emitter_defaults)
    return _data_emitter


@pytest.fixture
def gen_factory(data_emitter):
    """
    Pytest fixture function that generates and returns an appropriate
    SolrDataGenFactory object.
    """
    def _gen_factory(emitter=None):
        emitter = emitter or data_emitter()
        return sf.SolrDataGenFactory(emitter)
    return _gen_factory


@pytest.fixture
def profile(schema, gen_factory):
    """
    Pytest fixture function that generates and returns an appropriate
    `SolrProfile` object.
    """
    def _profile(name='test', user_fields=None, unique_fields=None, gens=None,
                 default_field_gens=None, my_schema=None, solr_types=None):
        gens = gens or gen_factory()
        my_schema = my_schema or schema
        return sf.SolrProfile(
            name, schema=my_schema, user_fields=user_fields,
            unique_fields=unique_fields, gen_factory=gens,
            solr_types=solr_types, default_field_gens=default_field_gens
        )
    return _profile


@pytest.fixture
def schema_types_error():
    """
    Pytest fixture that returns the SolrProfile.SchemaTypesError class.
    """
    return sf.SolrProfile.SchemaTypesError


@pytest.fixture
def solr_types():
    """
    Pytest fixture that returns the default solr field type mapping,
    used in defining SolrProfile objects.
    """
    default = sf.SolrProfile.DEFAULT_SOLR_FIELD_TYPE_MAPPING
    return {t: params.copy() for t, params in default.items()}


@pytest.fixture
def fixture_factory(profile):
    """
    Pytest fixture function that generates and returns an appropriate
    SolrFixtureFactory object.
    """
    solr_profile = profile

    def _fixture_factory(profile=None):
        profile = profile or solr_profile()
        return sf.SolrFixtureFactory(profile)
    return _fixture_factory
