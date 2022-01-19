"""
Contains tests for solrfixtures.profile module.
"""
import datetime

import pytest


@pytest.mark.parametrize('fname, val, expected', [
    ('code', None, None),
    ('code', 'abc', u'abc'),
    ('code', 123, u'123'),
    ('id', None, None),
    ('id', '123', 123),
    ('id', 123, 123),
    ('notes', None, None),
    ('notes', [None], None),
    ('notes', [None, None], None),
    ('notes', 'one', [u'one']),
    ('notes', ['one', 123], [u'one', u'123']),
    ('creation_date', datetime.datetime(2015, 1, 1, 0, 0),
     datetime.datetime(2015, 1, 1, 0, 0))
])
def test_solrprofile_field_topython(fname, val, expected, profile):
    """
    The `SolrProfile.Field` `to_python` method should return a value
    of the appropriate type based on the parameters passed to it.
    """
    assert profile().fields[fname].to_python(val) == expected


def test_solrprofile_init_fields_structure(profile):
    """
    Initializing a `SolrProfile` object should interpret values
    correctly from the provided schema fields and return the correct
    structure.
    """
    prof = profile('test', None, None)
    assert prof.fields['haystack_id']['name'] == 'haystack_id'
    assert prof.fields['haystack_id']['is_key'] == True
    assert prof.fields['haystack_id']['type'] == 'string'
    assert prof.fields['haystack_id']['pytype'] == str
    assert prof.fields['haystack_id']['emtype'] == 'string'
    assert prof.fields['haystack_id']['multi'] == False
    assert prof.fields['haystack_id']['unique'] == True
    assert prof.fields['id']['is_key'] == False
    assert prof.fields['notes']['type'] == 'text_en'
    assert prof.fields['notes']['multi'] == True


def test_solrprofile_init_fields_include_all(schema, profile):
    """
    Initializing a `SolrProfile` object should result in a field
    structure that includes all static schema fields when the
    `user_fields` parameter is None.
    """
    assert len(profile().fields) == len(schema['fields'])


def test_solrprofile_init_fields_include_selective(profile):
    """
    Initializing a `SolrProfile` object should result in a field
    structure that includes only the provided list of user fields.
    """
    user_fields = ['haystack_id', 'creation_date', 'code', 'label']
    prof = profile('test', user_fields, None)
    assert len(prof.fields) == len(user_fields)
    assert all([fname in prof.fields for fname in user_fields])


def test_solrprofile_init_fields_include_dynamic(profile):
    """
    Initializing a `SolrProfile` object should result in a field
    structure that includes fields matching defined dynamic fields.
    """
    user_fields = ['haystack_id', 'code', 'test_facet', 'test_display']
    prof = profile('test', user_fields, None)
    assert len(prof.fields) == len(user_fields)
    assert all([fname in prof.fields for fname in user_fields])


def test_solrprofile_init_fields_unique(profile):
    """
    Initializing a `SolrProfile` object should result in a field
    structure where the `unique` key is set to True for all fields
    in the provided `unique_fields` parameter.
    """
    unique_fields = ['haystack_id', 'code']
    prof = profile('test', None, unique_fields)
    assert all([prof.fields[fn]['unique'] == True for fn in unique_fields])
    assert all([prof.fields[fn]['unique'] == False for fn in prof.fields
                if fn not in unique_fields])


def test_solrprofile_init_fields_multi_unique_error(profile):
    """
    Attempting to instantiate a `SolrProfile` object and defining a
    field that is both `multi` and `unique` should result in an error.
    """
    with pytest.raises(NotImplementedError):
        prof = profile('test', ['notes'], ['notes'])


def test_solrprofile_init_fields_invalid_types_error(schema, profile,
                                                     solr_types,
                                                     schema_types_error):
    """
    Attempting to instantiate a `SolrProfile` object using a schema
    with field types not included in the provided (or default) Solr
    type mapping should raise an error if any of those fields are used
    in the profile.
    """
    invalid_name, invalid_type = 'invalid', 'invalid'
    schema['fields'].append({'name': invalid_name, 'type': invalid_type,
                             'multiValued': False})
    assert invalid_type not in solr_types
    with pytest.raises(schema_types_error):
        prof = profile(my_schema=schema)


def test_solrprofile_init_unused_fields_invalid_types_okay(schema, profile,
                                                           solr_types):
    """
    Instantiating a `SolrProfile` object using a schema with field
    types not included in the provided (or default) Solr type mapping
    should NOT raise an error if none of the offending fields are
    included as part of the profile.
    """
    invalid_name, invalid_type = 'invalid', 'invalid'
    fnames = [f['name'] for f in schema['fields']]
    schema['fields'].append({'name': invalid_name, 'type': invalid_type,
                             'multiValued': False})
    prof = profile(user_fields=fnames, my_schema=schema)
    assert invalid_type not in solr_types
    assert invalid_name not in prof.fields


def test_solrprofile_init_fields_with_custom_type(schema, profile, solr_types):
    """
    Instantiating a `SolrProfile` object using a schema with field
    types included in the provided (but non-default) Solr type mapping
    should NOT raise an error.
    """
    custom_name, custom_type = 'custom', 'custom'
    schema['fields'].append({'name': custom_name, 'type': custom_type,
                             'multiValued': False})
    assert custom_type not in solr_types
    solr_types[custom_type] = {'pytype': str, 'emtype': 'string'}
    prof = profile(my_schema=schema, solr_types=solr_types)
    assert custom_name in prof.fields
    assert prof.fields[custom_name]['pytype'] == str
    assert prof.fields[custom_name]['emtype'] == 'string'

