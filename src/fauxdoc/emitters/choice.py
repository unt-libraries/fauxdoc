"""Contains emitters for choosing random data values."""
import itertools
from typing import Any, Optional, List, Sequence

from fauxdoc.emitter import Emitter
from fauxdoc.mathtools import clamp, gaussian, poisson, weighted_shuffle
from fauxdoc.mixins import RandomMixin, ItemsMixin
from fauxdoc.typing import T


class Choice(RandomMixin, ItemsMixin[T], Emitter[T]):
    """Class for making random selections, optionally with weighting.

    This covers any kind of random choice and implements the most
    efficient algorithm available: choices with or without weights and
    choices with or without replacement. You should use this to
    implement random selection within any kind of range; e.g., the
    random selection here is more efficient than random.randint.

    Note about replacement vs uniqueness: A Choice emitter may be set
    up to emit items without replacement (therefore emitting unique
    items), but it still may not emit unique values. Example: items
    sequence ['H', 'H', 'H', 'T'] has four items but two unique values.
    Even without replacement, the value "H" may still appear three
    times in your output. The properties `emits_unique_values` and
    `num_unique_values` only count unique VALUES. For the former to be
    true, an emitter must not use replacement AND the list of items
    must contain unique values, such as ['A', 'B', 'C', 'D', 'E'].

    Attributes:
        rng: Random Number Generator, inherited from superclass. Should
            be a random.Random instance.
        items: (Read-only.) A sequence of values you wish to choose
            from.
        weights: (Optional, Immutable.) A tuple of weights, one per
            item, for controlling the probability of selections. This
            *must* be the same length as `items`. Weights are *not*
            cumulative -- the 'cum_weights' attribute contains
            cumulative weights. When weights are set, cum_weights are
            calculated accordingly, and vice-versa. If weights and
            cum_weights are None, then choices are made randomly
            without weights. Default is None.
        cum_weights: (Optional, Immutable.) A tuple of cumulative
            weights, one per item, for controlling the probability of
            selections. This *must* be the same length as `items`. When
            cum_weights are set, weights are calculated accordingly,
            and vice-versa. If weights and cum_weights are None, then
            choices are made randomly without weights. Default is None.
        replace: A bool value. True if items can be chosen multiple
            times; False if each item can be chosen ONCE. Default is
            True. Note the interaction with `replace_only_after_call`
            -- the latter defines WHEN replacement happens, the former
            defines IF it happens. So if `replace` is False, then
            `replace_only_after_call` is automatically switched to
            False. If `replace_only_after_call` is True, then `replace`
            is switched to True.
        replace_only_after_call: A bool value. True if items should
            only be replaced after each call; False otherwise. I.e.,
            if this is True, then each call that requests multiple
            items ensures that all items in each call are unique, but
            items are reused from call to call. Default is False.
            If this is True, then `replace` is set to True.
        noun: A string representing a singular noun or noun-phrase that
            describes what each item is. Used in raising a more
            informative error if weights and items don't match. Default
            is an empty string.
        emits_unique_values: (Read-only.) A bool value. True if this
            emitter will only emit unique values given the current
            state. (If an emitter without replacement starts out with
            duplicate items but then emits all the duplicates, this
            changes from False to True.)
        num_unique_values: (Read-only.) An int representing the number
            of unique values that this emitter can emit given the
            current state. If replace is False, and some values have
            already been emitted, this tells you how many unique values
            remain.
        num_unique_items: (Read-only.) An int representing the number
            of unique items that this emitter can emit given the
            current state. If replace is False, and some items have
            already been emitted, this tells you how many items remain.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. Default is None. Note: if you want seed the
            RNG, use the `seed` method -- setting the `rng_seed`
            attribute by itself does nothing.
    """

    def __init__(self,
                 items: Sequence[T],
                 weights: Optional[Sequence[float]] = None,
                 replace: bool = True,
                 replace_only_after_call: bool = False,
                 noun: str = '',
                 rng_seed: Any = None,
                 cum_weights: Optional[Sequence[float]] = None) -> None:
        """Inits a Choice emitter with items, weights, and settings.

        Args:
            items: See `items` attribute.
            weights: (Optional.) See `weights` attribute. Note: you may
                supply either weights or cum_weights, not both.
            replace: (Optional.) See `replace` attribute.
            replace_only_after_call: (Optional.) See
                `replace_only_after_call` attribute.
            noun: (Optional.) See `noun` attribute.
            rng_seed: (Optional.) See `rng_seed` attribute.
            cum_weights: (Optional.) See `cum_weights` attribute. Note:
                you may supply either weights or cum_weights, not both.
        """
        if not items or not isinstance(items, Sequence):
            raise ValueError(
                f"The 'items' argument must be a non-empty sequence. "
                f"(Provided: {items})"
            )
        if weights and cum_weights:
            raise TypeError(
                "Only one of 'weights' or 'cum_weights' (cumulative weights) "
                "may be supplied -- not both."
            )
        self._num_unique_items = len(items)
        self._shuffled: List[T] = []
        self._replace = replace or replace_only_after_call
        self._replace_only_after_call = replace_only_after_call
        self.noun = noun
        weights_to_set = weights or cum_weights
        weights_are_cumulative = bool(cum_weights)
        self._set_all_weights(weights_to_set, weights_are_cumulative, items)
        super().__init__(items=items, rng_seed=rng_seed)

    def _set_all_weights(self,
                         weights_to_set: Optional[Sequence[float]] = None,
                         weights_are_cumulative: bool = False,
                         items: Optional[Sequence[T]] = None) -> None:
        weights = None
        cum_weights = None
        if weights_to_set is not None:
            items = items or self._items
            nitems = len(items)
            nweights = len(weights_to_set)
            if nitems != nweights:
                noun_phr = f"{self.noun} choices" if self.noun else "choices"
                v_phr = 'cum_weights' if weights_are_cumulative else 'weights'
                raise ValueError(
                    f"Mismatched number of {noun_phr} ({nitems}) to choice "
                    f"{v_phr} ({nweights}). These amounts must match."
                )
            if weights_are_cumulative:
                cum_weights = tuple(weights_to_set)
                de_cum_weights = []
                prev: float = 0
                for weight in cum_weights:
                    de_cum_weights.append(weight - prev)
                    prev = weight
                weights = tuple(de_cum_weights)
            else:
                cum_weights = tuple(itertools.accumulate(weights_to_set))
                weights = tuple(weights_to_set)
        self._weights = weights
        self._cum_weights = cum_weights

    @property
    def weights(self) -> Optional[Sequence[float]]:
        """See the `weights` attribute."""
        return self._weights

    @weights.setter
    def weights(self, weights: Optional[Sequence[float]]) -> None:
        """Sets the `weights` attribute.

        WARNING: Changing weights on an emitter where `replace` is
        False invalidates the previous random shuffle, causing it to be
        reset, losing track of which values have already been emitted.
        """
        self._set_all_weights(weights)
        if not self._replace:
            self._global_shuffle()

    @property
    def cum_weights(self) -> Optional[Sequence[float]]:
        """See the `cum_weights` attribute."""
        return self._cum_weights

    @cum_weights.setter
    def cum_weights(self, cum_weights: Optional[Sequence[float]]) -> None:
        """Sets the `cum_weights` attribute.

        WARNING: Changing cum_weights on an emitter where `replace` is
        False invalidates the previous random shuffle, causing it to be
        reset, losing track of which values have already been emitted.
        """
        self._set_all_weights(cum_weights, weights_are_cumulative=True)
        if not self._replace:
            self._global_shuffle()

    @property
    def replace(self) -> bool:
        """See the `replace` attribute."""
        return self._replace

    @replace.setter
    def replace(self, replace: bool) -> None:
        """Sets the `replace` attribute.

        Setting this to False means you want no replacement at all, and
        so also sets `replace_only_after_call` to False.

        WARNING: Changing `replace` to False resets the previous random
        shuffle, losing track of which values have already been
        emitted.
        """
        if replace != self._replace:
            self._replace = replace
            if replace:
                self._num_unique_items = len(self._items)
            else:
                self._replace_only_after_call = False
                self._global_shuffle()

    @property
    def replace_only_after_call(self) -> bool:
        """See the `replace_only_after_call` attribute."""
        return self._replace_only_after_call

    @replace_only_after_call.setter
    def replace_only_after_call(self, replace_only_after_call: bool) -> None:
        """Sets the `replace_only_after_call` attribute.

        Setting this to True also sets `replace` to True.
        """
        self._replace_only_after_call = replace_only_after_call
        if replace_only_after_call:
            self.replace = True

    def reset(self) -> None:
        """Resets state.

        If `replace` is False, this resets the emitter so that it loses
        track of what has already been emitted.
        """
        super().reset()
        if not self._replace:
            # For emitters without replacement, it's most efficient to
            # pre-shuffle items ONCE. Then you just return items in
            # shuffled order as they're requested. This shuffle gets
            # regenerated when `reset` is called. It's also regenerated
            # any time changing object state invalidates the shuffle:
            # setting `weights`, setting `replace` to False, and
            # reseeding.
            self._global_shuffle()

    def seed(self, rng_seed: Any) -> None:
        """See superclass.

        WARNING: Reseeding an emitter where `replace` is False
        invalidates the previous random shuffle, causing it to be
        reset, losing track of which values have already been emitted.
        """
        super().seed(rng_seed)
        if not self._replace:
            self._global_shuffle()

    def _global_shuffle(self) -> None:
        num_items = len(self._items)
        weights = self.weights or [1] * num_items
        self._shuffled = weighted_shuffle(self._items, weights, self.rng)
        self._shuffled_index = 0
        self._num_unique_items = num_items

    @property
    def emits_unique_values(self) -> bool:
        """True if this emitter only emits unique values.

        If `self.replace` is False, then this is based on the items
        that are left. So -- if an emitter without replacement starts
        out with some duplicate values in `items`, this is False. Once
        all duplicate items have been emitted and only unique values
        remain, this becomes True.
        """
        if not self._replace:
            return self.num_unique_items == self.num_unique_values
        return False

    @property
    def num_unique_values(self) -> int:
        """The number of unique values that can be emitted.

        Use this to sanity-check an `emit` call if unique values are
        required. If `self.replace` is False, then this gives you the
        number of unique values that remain to be selected. Otherwise,
        it gives you the total number of unique values that can be
        selected.
        """
        if not self._replace:
            return len(set(self._shuffled[self._shuffled_index:]))
        return super().num_unique_values

    @property
    def num_unique_items(self) -> int:
        """The number of unique items that can be emitted.

        If `self.replace` is False, then this gives you the number of
        items that remain to be selected.

        Note the difference between "items" and "values." An emitter
        with items [1, 1, 1, 2, 3] has 5 unique items and 3 unique
        values.
        """
        return self._num_unique_items

    def _choice_without_replacement(self, number: int) -> List[T]:
        """Makes choices without replacing items."""
        if number > self._num_unique_items:
            self.raise_uniqueness_violation(number)
        if not self._replace:
            # No replacement, with/without weights.
            if number == 1:
                items = [self._shuffled[self._shuffled_index]]
            else:
                start = self._shuffled_index
                end = start + number
                items = list(self._shuffled[start:end])
            self._shuffled_index += number
            self._num_unique_items -= number
            return items
        if self._weights is None:
            # One call without replacement, without weights.
            return self.rng.sample(self._items, k=number)
        # One call without replacement, with weights.
        return weighted_shuffle(self._items, self._weights, self.rng, number)

    def _choice_with_replacement(self, number: int) -> List[T]:
        """Makes non-unique choices (with replacement)."""
        if len(self._items) == 1:
            # No choice here.
            return list(self._items) * number
        if self._weights is None and number == 1:
            # `choice` is fastest if there are no weights and we just
            # need 1.
            return [self.rng.choice(self._items)]
        return self.rng.choices(self._items, cum_weights=self._cum_weights,
                                k=number)

    def emit(self) -> T:
        """Returns one randomly chosen value."""
        if not self.replace:
            return self._choice_without_replacement(1)[0]
        return self._choice_with_replacement(1)[0]

    def emit_many(self, number: int) -> List[T]:
        """Returns 'number' randomly chosen values.

        Args:
            number: See superclass.
        """
        if not self._replace or (self._replace_only_after_call and number > 1):
            return self._choice_without_replacement(number)
        return self._choice_with_replacement(number)


def poisson_choice(items: Sequence[T],
                   mu: int = 1,
                   weight_floor: float = 0,
                   replace: bool = True,
                   replace_only_after_call: bool = False,
                   noun: str = '',
                   rng_seed: Any = None) -> Choice[T]:
    """Returns a Choice emitter with a Poisson weight distribution.

    Args:
        items: A list / sequence of all available choices.
        mu: (Optional.) A positive integer or float representing the
            average x value, or peak, of the distribution curve --
            i.e., which items are chosen most frequently. Default is 1.
        weight_floor: (Optional.) A positive integer or float
            representing the lowest possible individual weight for an
            item. This is most useful when you have a large number of
            'items' -- it helps ensure you'll see more of the long tail
            in choices that are made. Set to 0 (default) for no floor.
        replace: (Optional.) 'replace' kwarg to pass to Choice.
        replace_only_after_call: (Optional.) 'replace_only_after_call'
            kwarg to pass to Choice.
        noun: (Optional.) 'noun' kwarg to pass to Choice.
        rng_seed: (Optional.) 'rng_seed' kwarg to pass to Choice.
    """
    weights = [clamp(poisson(x, mu), mn=weight_floor)
               for x in range(1, len(items) + 1)]
    return Choice(items, weights, replace, replace_only_after_call, noun,
                  rng_seed)


def gaussian_choice(items: Sequence[T],
                    mu: float = 0,
                    sigma: float = 1,
                    weight_floor: float = 0,
                    replace: bool = True,
                    replace_only_after_call: bool = False,
                    noun: str = '',
                    rng_seed: Any = None) -> Choice[T]:
    """Returns a Choice emitter with a Gaussian weight distribution.

    Args:
        items: A list / sequence of all available choices.
        mu: (Optional.) An integer or float representing the average x
            value, or peak, of the distribution curve -- i.e., which
            items are chosen most frequently. Default is 0.
        sigma: (Optional.) A positive integer or float representing the
            standard deviation of the distribution curve -- i.e., the
            width of the curve. Default is 1. Note: lower values create
            a sharper peak, decreasing the number of items around it
            that are chosen frequently. Higher values dull the peak,
            increasing how frequently the items around it are chosen.
        weight_floor: (Optional.) A positive integer or float
            representing the lowest possible individual weight for an
            item. This is most useful when you have a large number of
            'items' -- it helps ensure you'll see more of the long tail
            in choices that are made. Set to 0 (default) for no floor.
        replace: (Optional.) 'replace' kwarg to pass to Choice.
        replace_only_after_call: (Optional.) 'replace_only_after_call'
            kwarg to pass to Choice.
        noun: (Optional.) 'noun' kwarg to pass to Choice.
        rng_seed: (Optional.) 'rng_seed' kwarg to pass to Choice.
    """
    weights = [clamp(gaussian(x, mu, sigma), mn=weight_floor)
               for x in range(1, len(items) + 1)]
    return Choice(items, weights, replace, replace_only_after_call, noun,
                  rng_seed)


def chance(chance: float, rng_seed: Any = None) -> Choice[bool]:
    """Returns a Choice emitter with a certain chance of emitting True.

    Args:
        chance: A number between 0.0 and 1.0 representing the chance
            this emits True. Always emits False if chance <= 0; always emits
            True if chance >= 1.0.
        rng_seed: (Optional.) 'rng_seed' kwarg to pass to Choice.
    """
    return Choice([True, False], [chance, 1.0 - chance], rng_seed=rng_seed)
