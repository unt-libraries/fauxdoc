"""
Create Solr profiles to use for generating document sets.
"""
import datetime
import fnmatch
from collections import OrderedDict

import ujson

from . import data


class SolrProfile(object):
    """
    Class used for creating objects that represent a Solr profile, i.e.
    a subset of fields from a particular schema.
    """
    class SchemaTypesError(Exception):
        """
        Exception raised when you try using a field in your profile
        that has a Solr type not included in the `solr_types` data
        structure used during initialization.
        """
        pass

    DEFAULT_SOLR_FIELD_TYPE_MAPPING = {
        'string': {'pytype': str, 'emtype': 'string'},
        'text_en': {'pytype': str, 'emtype': 'text'},
        'long': {'pytype': int, 'emtype': 'int'},
        'int': {'pytype': int, 'emtype': 'int'},
        'date': {'pytype': datetime.datetime, 'emtype': 'date'},
        'boolean': {'pytype': bool, 'emtype': 'boolean'}
    }

    def __init__(self, name, conn=None, schema=None, user_fields=None,
                 unique_fields=None, solr_types=None, gen_factory=None,
                 default_field_gens=None):
        """
        Initialize a `SolrProfile` object. Lots of options.

        `conn`, `schema`: The first is the pysolr connection object for
        the Solr index your profile covers; the second is a schema
        dataset you want to force. Provide one or the other; you don't
        need both. Normally you'll provide the `conn` and the schema
        will be grabbed automatically; `schema` overrides `conn` if
        both are provided.

        `user_fields`: A list of field names (each of which should
        match a field name (whether static or dynamic) in the schema).
        Using the default of None assumes you want ALL the
        [non-dynamic] fields in the schema.

        `unique_fields`: A list or tuple of field names (each of which
        should match with a field name in the schema) where values
        should be unique in a given record set. Whatever field is the
        uniqueKey in your schema is already unique; you can include it
        or not.

        `solr_types`: A dict structure that tells the profile object
        how Solr schema types work, mapping each Solr type to a Python
        type and a data.DataEmitter type. See the
        DEFAULT_SOLR_FIELD_TYPE_MAPPING class attribute for an example.
        This is used as the default mapping if you don't provide one.

        `gen_factory`: The SolrDataGenFactory object you want to use
        for auto gen fields. Defaults to a plain object that uses a
        plain data.DataEmitter object.

        `default_field_gens`: A list (or tuple) of specific, non-auto
        gens that you want to use for specific fields in this profile.
        Each tuple item should be a (field_name, gen) tuple. This gets
        passed to the `set_field_gens` method, so see that for more
        info. You can also set (reset) the default field gens by
        calling that method directly after the profile object is
        initialized.
        """
        unique_fields = unique_fields or []
        solr_types = solr_types or type(self).DEFAULT_SOLR_FIELD_TYPE_MAPPING
        self.gen_factory = gen_factory or data.SolrDataGenFactory()
        self.conn = conn
        schema = schema or self.fetch_schema(conn)
        self.key_name = schema['uniqueKey']
        filtered_fields = self._filter_schema_fields(schema, user_fields)
        self._check_schema_types(filtered_fields, solr_types)
        self.fields = {}
        for sf in filtered_fields:
            field = type(self).Field({
                'name': sf['name'],
                'is_key': sf['name'] == self.key_name,
                'type': sf['type'],
                'emtype': solr_types[sf['type']]['emtype'],
                'pytype': solr_types[sf['type']]['pytype'],
                'multi': sf.get('multiValued', False),
                'unique': sf['name'] in list(unique_fields) + [self.key_name]
            }, gen_factory)
            self.fields[field['name']] = field
        self.name = name
        self.set_field_gens(*(default_field_gens or tuple()))

    @staticmethod
    def fetch_schema(conn):
        """
        Fetch the Solr schema in JSON format via the provided pysolr
        connection object (`conn`).
        """
        jsn = conn._send_request('get', 'schema?wt=json')
        return ujson.loads(jsn)['schema']

    def _get_schema_field(self, schema_fields, name):
        """
        Return a dict from the Solr schema for a field matching `name`.
        Returns the first match found, or None.
        """
        for field in schema_fields:
            if fnmatch.fnmatch(name, field['name']):
                field = field.copy()
                field['name'] = name
                return field
        return None

    def _filter_schema_fields(self, schema, user_fields):
        if not user_fields:
            return [f for f in schema['fields'] if f['name'] != '_version_']

        schema_fields = schema['fields'] + schema.get('dynamicFields', [])
        return_fields = []
        for ufname in user_fields:
            field = self._get_schema_field(schema_fields, ufname)
            if field is not None:
                return_fields.append(field)
        return return_fields

    def _check_schema_types(self, schema_fields, solr_types):
        schema_types = set([field['type'] for field in schema_fields])
        unknown_types = schema_types - set(solr_types.keys())
        if len(unknown_types) > 0:
            msg = ('Found field types in Solr schema that do not have '
                   'matching entries in the defined Solr field type mapping '
                   '(`solr_types` arg). {}').format(', '.join(unknown_types))
            raise type(self).SchemaTypesError(msg)

    def set_field_gens(self, *field_gens):
        """
        Set the default list of field_gen tuples to use for generating
        data via the fixture factory. Each field_gen is a (field_name,
        gen) tuple.

        Note that field gens will get called in the order specified,
        so make sure any gens that rely on existing field data are
        listed after the fields they depend on. You can set the `gen`
        portion of the tuple to the string 'auto' if you want to use
        the default generator, or None if you just want a placeholder.
        """
        field_gens = OrderedDict(field_gens)
        for fname, field in self.fields.items():
            if field_gens.get(fname, 'auto') == 'auto':
                field_gens[fname] = field.auto_gen
        self.field_gens = field_gens

    def reset_fields(self):
        """
        Reset any state stored on fields, like lists of unique values.

        Use this any time you need to reset to generate a new batch of
        records from scratch.
        """
        for field in self.fields.values():
            field.reset()

    class Field(dict):
        """
        Internal class used for individual fields in the `fields`
        attribute of a `SolrProfile` object. Subclass of `dict`. The
        field attributes (like `multi` and `unique`) are key/value
        pairs. Also provides methods for generating and converting data
        values.
        """
        class ViolatesUniqueness(Exception):
            """
            Exception raised when it's impossible to generate a unique
            value for a given record set (e.g. if all unique values are
            used up).
            """
            pass

        def __init__(self, params, gen_factory):
            super(SolrProfile.Field, self).__init__(params)
            self.reset()
            if self['multi']:
                if self['unique']:
                    msg = ('Uniqueness for multivalued fields is not '
                           'implemented.')
                    raise NotImplementedError(msg)
                counter = gen_factory.random_counter(1, 10)
                self.auto_gen = gen_factory.multi_type(self['emtype'], counter)
            else:
                self.auto_gen = gen_factory.type(self['emtype'])

        def reset(self):
            self.unique_vals = set()

        def to_python(self, val):
            """
            Force the given value to the right Python type.
            """
            def dtype(val):
                _type = self['pytype']
                return val if isinstance(val, _type) else _type(val)

            if isinstance(val, (list, tuple, set)):
                vals = [dtype(v) for v in val if v is not None]
                if vals:
                    return vals if self['multi'] else vals[0]
            else:
                val = dtype(val) if val is not None else None
                return [val] if (self['multi'] and val is not None) else val

        def _do_gen(self, gen, record):
            return self.to_python(gen(record))

        def _do_unique_gen(self, gen, record, records):
            val = self._do_gen(gen, record)

            if gen.max_unique is not None:
                if val in self.unique_vals and len(records) >= gen.max_unique:
                    raise type(self).ViolatesUniqueness

            while val in self.unique_vals:
                val = self._do_gen(gen, record)
            self.unique_vals.add(val)
            return val

        def gen_value(self, gen=None, record=None, records=None):
            """
            Generate a value for this field type, optionally using the
            provided `gen`. A default auto gen is used, otherwise.
            `record` and `records` are optional, strictly speaking, but
            needed when generating values for a set of records.
            """
            record = record or {}
            records = records or []
            gen = gen or self.auto_gen
            if self['unique']:
                return self._do_unique_gen(gen, record, records)
            return self._do_gen(gen, record)
