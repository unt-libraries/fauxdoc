"""
Generate random data values to use in test profiles and test documents.
"""
import datetime
import math
import random

import pytz


class DataEmitter:
    """
    Class containing emitter methods for generating randomized data.
    """
    default_emitter_defaults = {
        'string': {'mn': 10, 'mx': 20, 'alphabet': None, 'len_weights': None},
        'text': {'mn_words': 2, 'mx_words': 10, 'mn_word_len': 1,
                 'mx_word_len': 20, 'alphabet': None, 'word_len_weights': None,
                 'phrase_len_weights': None},
        'int': {'mn': 0, 'mx': 9999999999},
        'date': {'mn': (2015, 1, 1, 0, 0), 'mx': None}
    }

    def __init__(self, alphabet=None, emitter_defaults=None):
        """
        On initialization, you can set up defaults via the two kwargs.
        If a default is NOT set here, the value(s) in the class
        attribute `default_emitter_defaults` will be used. All defaults
        can be overridden via the `emit` method.

        `alphabet` should be a list of characters that string/text
        emitter types will use by default. (This can be set separately
        for different types via `emitter_defaults`, but it's included
        as a single argument for convenience.)

        `emitter_defaults` is a nested dict that should be structured
        like the `default_emitter_defaults` class attribute. But, the
        class attribute is copied and then updated with user-provided
        overrides, so you don't have to provide the entire dictionary
        if you only want to override a few values.
        """
        user_defaults = emitter_defaults or {}
        both_defaults = {}
        for key, val in type(self).default_emitter_defaults.items():
            both_defaults[key] = val.copy()
            both_defaults[key].update(user_defaults.get(key, {}))
            if 'alphabet' in val and both_defaults[key]['alphabet'] is None:
                alphabet = alphabet or self.make_unicode_alphabet()
                both_defaults[key]['alphabet'] = alphabet
        self.emitter_defaults = both_defaults

    @staticmethod
    def make_unicode_alphabet(uchar_ranges=None):
        """
        Generate a list of characters to use for initializing a new
        DataEmitters object. Pass a nested list of tuples representing
        the character ranges to include via `char_ranges`.
        """
        if uchar_ranges is None:
            uchar_ranges = [
                (0x0021, 0x0021), (0x0023, 0x0026), (0x0028, 0x007E),
                (0x00A1, 0x00AC), (0x00AE, 0x00FF)
            ]
        return [
            chr(code) for this_range in uchar_ranges
            for code in range(this_range[0], this_range[1] + 1)
        ]

    @staticmethod
    def _choose_token_length(mn, mx, len_weights):
        len_choices = range(mn, mx + 1)
        if len_weights is None:
            return random.choice(len_choices)
        return random.choices(len_choices, cum_weights=len_weights)[0]

    def _emit_string(self, mn=0, mx=0, alphabet=None, len_weights=None):
        """
        Generate a random unicode string with length between `mn` and
        `mx`.
        """
        length = self._choose_token_length(mn, mx, len_weights)
        return ''.join(random.choice(alphabet) for _ in range(length))

    def _emit_text(self, mn_words=0, mx_words=0, mn_word_len=0,
                   mx_word_len=0, alphabet=None, word_len_weights=None,
                   phrase_len_weights=None):
        """
        Generate random unicode multi-word text.

        The number of words is between `mn_words` and `mx_words` (where
        words are separated by spaces). Each word has a length between
        `mn_word_len` and `mx_word_len`.
        """
        text_length = self._choose_token_length(mn_words, mx_words,
                                                phrase_len_weights)
        args = (mn_word_len, mx_word_len, alphabet, word_len_weights)
        words = [self._emit_string(*args) for _ in range(text_length)]
        return ' '.join(words)

    @staticmethod
    def _emit_int(mn=0, mx=0):
        """
        Generate a random int between `mn` and `mx`.
        """
        return random.randint(mn, mx)

    @staticmethod
    def _emit_date(mn=(2000, 1, 1, 0, 0), mx=None):
        """
        Generate a random UTC date between `mn` and `mx`. If `mx` is
        None, the default is now. Returns a timezone-aware
        datetime.datetime obj.
        """
        min_date = datetime.datetime(*mn, tzinfo=pytz.utc)
        if mx is None:
            max_date = datetime.datetime.now(pytz.utc)
        else:
            max_date = datetime.datetime(*mx, tzinfo=pytz.utc)
        min_td = (min_date - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc))
        max_td = (max_date - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc))
        min_ts, max_ts = min_td.total_seconds(), max_td.total_seconds()
        new_ts = min_ts + (random.random() * (max_ts - min_ts))
        new_date = datetime.datetime.utcfromtimestamp(new_ts)
        return new_date.replace(tzinfo=pytz.utc)

    @staticmethod
    def _emit_boolean():
        """
        Generate a random boolean value.
        """
        return bool(random.randint(0, 1))

    def _calculate_emitter_params(self, emtype, **user_params):
        """
        Return complete parameters for the given emitter type; default
        parameters with user_param overrides are returned.
        """
        params = self.emitter_defaults.get(emtype, {}).copy()
        params.update(user_params)
        return params

    def determine_max_unique_values(self, emtype, **user_params):
        """
        Return the maximum number of unique values possible for a given
        emitter type with the given user_params. This is mainly just so
        we can prevent infinite loops when generating unique values.
        E.g., the maximum number of unique values you can generate for
        an int range of 1 to 100 is 100, so it would be impossible to
        use those parameters for that emitter for a unique field. This
        really only applies to integers and strings. Dates and text
        values are either unlikely to repeat or unlikely ever to need
        to be unique.
        """
        params = self._calculate_emitter_params(emtype, **user_params)
        if emtype == 'int':
            return params['mx'] - params['mn'] + 1
        if emtype == 'string':
            mn, mx, alphabet = params['mn'], params['mx'], params['alphabet']
            return sum((len(alphabet) ** n for n in range(mn, mx + 1)))
        if emtype == 'boolean':
            return 2
        return None

    def emit(self, emtype, **user_params):
        """
        Generate and emit a value using the given `emtype` and
        `user_params`.
        """
        params = self._calculate_emitter_params(emtype, **user_params)
        emitter = getattr(self, f'_emit_{emtype}')
        return emitter(**params)


class SolrDataGenFactory:
    """
    Factory for creating "gen" data generation functions.
    """
    default_emitter = DataEmitter()

    def __init__(self, emitter=None):
        """
        Pass an optional `emitter` obj for custom emitter methods.
        """
        self.emitter = emitter or type(self).default_emitter

    def __call__(self, function, max_unique=None):
        """
        Convert the given function to a "gen" (data generator) function
        for use in `SolrProfile` and `SolrFixtureFactory` objects.

        A `max_unique` value is only needed if you're making a custom
        gen function to be used with unique fields that can only create
        a small number of unique values.
        """
        def gen(record):
            return function(record)
        gen.max_unique = max_unique
        return gen

    @staticmethod
    def _make_choice_function(values, repeatable):
        choices = list(values)
        random.shuffle(choices)

        def _choice_function(_record):
            if repeatable:
                return random.choice(choices)
            return choices.pop() if choices else None

        return _choice_function

    def choice(self, values, repeatable=True):
        """
        Return a gen function that chooses randomly from the choices in
        the given `values` arg. Pass `repeatable=False` if choices
        cannot be repeated.
        """
        func = self._make_choice_function(values, repeatable)
        max_unique = len(values)
        return self(func, max_unique)

    def multi_choice(self, values, counter, repeatable=True):
        """
        Return a gen function that makes multiple random choices from
        the given `values` arg and returns the list of chosen values.
        `counter` is a function whose return value determines how many
        items are chosen. Pass `repeatable=False` if choices cannot be
        repeated.
        """
        choose = self._make_choice_function(values, repeatable)
        max_unique = len(values)

        def multi_choice_gen(record):
            choices = (choose(record) for _ in range(0, counter()))
            return [val for val in choices if val is not None]

        return self(multi_choice_gen, max_unique)

    def type(self, emtype, **params):
        """
        Return an emitter gen function for the given emtype using the
        given params.
        """
        max_unique = self.emitter.determine_max_unique_values(emtype, **params)

        def type_emitter_gen(_record):
            return self.emitter.emit(emtype, **params)

        return self(type_emitter_gen, max_unique)

    def multi_type(self, emtype, counter, **params):
        """
        Return a multi-value gen function for the given emitter using
        the given params. `counter` is a function whose return value
        determines how many values are generated.
        """
        max_unique = self.emitter.determine_max_unique_values(emtype, **params)

        def multi_type_emitter_gen(_record):
            emit = self.emitter.emit
            return [emit(emtype, **params) for _ in range(0, counter())]

        return self(multi_type_emitter_gen, max_unique)

    def static(self, value):
        """
        Return a gen function that generates the given static value.
        """
        return self(lambda r: value, max_unique=1)

    # Following are `counter` methods--utility methods for generating
    # counter functions to use with `multi_choice` and `multi_type`.

    @staticmethod
    def static_counter(num):
        """
        Create a counter function that always returns the number passed
        in (`num`).
        """
        return lambda: num

    @staticmethod
    def random_counter(mn=0, mx=10):
        """
        Create a counter function that returns a random integer between
        `mn` and `mx`.
        """
        return lambda: random.randint(mn, mx)

    @staticmethod
    def precise_distribution_counter(num_groups, aggregate_num, dev=None):
        """
        Create a counter function that attempts to distribute a certain
        number (`aggregate_num`) over a certain number of groups
        (`num_groups`), with a random amount of deviation in each
        group, controlled by `dev`. (dev=0 creates groups that are the
        same size, to the greatest extent possible.)

        `dev` is capped at (aggregate_num / num_groups) to create a
        regular amount of deviation per group. E.g., if you're dividing
        100 into 5 groups, the maximum valid `dev` value is 20, meaning
        each group could be between 1 and 40. This prevents outliers
        that would disproportionately affect the other groups.

        A ValueError is raised if you provide a `dev` larger than the
        cap. If `dev` is None, then the default is (cap value / 2).

        Example: divide 100 into 5 groups.
            >>> counter = precise_distribution_counter(5, 100, dev=0)
            >>> [counter() for _ in range(0, 8)]
            [20, 20, 20, 20, 20, 0, 0, 0]
            >>> counter = precise_distribution_counter(5, 100, dev=1)
            >>> [counter() for _ in range(0, 8)]
            [19, 21, 19, 19, 22, 0, 0, 0]
            >>> counter = precise_distribution_counter(5, 100, dev=10)
            >>> [counter() for _ in range(0, 8)]
            [13, 10, 28, 21, 28, 0, 0, 0]

        Note that calling the counter after `num_groups` is exhausted
        always returns 0.

        For groups after the first, the provided `dev` value may not
        hold exactly. Since the actual variation in each group is
        random, the `dev` range is adjusted up or down to ensure
        the deviation can remain relatively even for the remaining
        groups. E.g., if higher values happen to be selected initially,
        then the upper limit may come down to prevent `aggregate_num`
        from being exhausted before `num_groups` is exhausted.
        """
        def _get_min_min(counters, mx):
            return counters['agg_rem'] - ((counters['ngroups_rem'] - 1) * mx)

        def _get_max_min(counters):
            return math.floor(counters['agg_rem'] / counters['ngroups_rem'])

        def _get_min_max(counters):
            return math.ceil(counters['agg_rem'] / counters['ngroups_rem'])

        def _get_max_max(counters, mn):
            return counters['agg_rem'] - ((counters['ngroups_rem'] - 1) * mn)

        def _get_new_dev(counters):
            new_dev = int(_get_max_min(counters) / 2)
            return new_dev if new_dev > 1 else 1

        def _get_best_min_and_max_from_dev(counters, dev):
            local_min = _get_max_min(counters) - dev
            local_min = 1 if local_min < 1 else local_min
            local_max = _get_min_max(counters) + dev
            upper_limit = _get_max_max(counters, local_min)
            if local_max > upper_limit:
                local_max = upper_limit
            else:
                lower_limit = _get_min_min(counters, local_max)
                local_min = max(local_min, lower_limit)
            return local_min, local_max

        counters = {'ngroups_rem': num_groups, 'agg_rem': aggregate_num}
        if dev is None:
            dev = _get_new_dev(counters)
        else:
            max_min = _get_max_min(counters)
            if dev > max_min:
                raise ValueError(
                    f'A deviation of {dev} is too large; the largest '
                    f'deviation for {aggregate_num} / {num_groups} is '
                    f'{max_min}.'
                )

        def _counter():
            if counters['ngroups_rem'] == 0:
                return 0
            if counters['ngroups_rem'] == 1:
                number = counters['agg_rem']
            else:
                mn, mx = _get_best_min_and_max_from_dev(counters, dev)
                number = random.randint(mn, mx)
            counters['ngroups_rem'] -= 1
            counters['agg_rem'] -= number
            return number
        return _counter
