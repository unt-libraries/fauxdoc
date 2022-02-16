"""Contains tools for creating data generation (gen) functions."""
import math
import random

from .emitter import DataEmitter


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
