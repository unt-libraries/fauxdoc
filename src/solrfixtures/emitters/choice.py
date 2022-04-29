"""Contains emitters for choosing random data values."""
import itertools
from typing import Any, Optional, List, Sequence

from solrfixtures.emitter import Emitter
from solrfixtures.mathtools import clamp, gaussian, poisson, weighted_shuffle
from solrfixtures.mixins import RandomMixin, ItemsMixin
from solrfixtures.typing import Number, T


class Choice(RandomMixin, ItemsMixin, Emitter):
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
        rng: Random Number Generator, inherited from superclass.
        items: A sequence of values you wish to choose from.
        weights: (Optional.) A sequence of weights, one per item, for
            controlling the probability of selections. This *must* be
            the same length as `items`. Weights should *not* be
            cumulative. Default is None.
        cum_weights: (Optional.) Cumulative weights are calculated from
            `weights`, if provided.
        replace: (Optional.) A bool value; False if selecting an
            item should prevent it from being selected again. Default
            is True.
        replace_only_after_call: (Optional.) A bool value; True if you
            only want items replaced after each call. I.e., with a
            call that requests multiple items, items will be unique,
            but items are reused for each such call. Default is False.
            If this is True, `replace` is set to True.
        noun: (Optional.) A string representing a singular noun or
            noun-phrase that describes what each item is. Used in
            raising a more informative error if weights and items don't
            match. Default is an empty string.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. Default is None.
    """

    def __init__(self,
                 items: Sequence[T],
                 weights: Optional[Sequence[Number]] = None,
                 replace: bool = True,
                 replace_only_after_call: bool = False,
                 noun: str = '',
                 rng_seed: Any = None) -> None:
        """Inits a Choice emitter with items, weights, and settings.

        Args:
            items: See `items` attribute.
            weights: (Optional.) See `weights` attribute.
            replace: (Optional.) See `replace` attribute.
            replace_only_after_call: (Optional.) See
                `replace_only_after_call` attribute.
            noun: (Optional.) See `noun` attribute.
            rng_seed: (Optional.) See `rng_seed` attribute.
        """
        self.weights = weights
        self.cum_weights = None
        self.replace = replace or replace_only_after_call
        self.replace_only_after_call = replace_only_after_call
        self.noun = noun
        self._shuffled = None
        super().__init__(items=items, rng_seed=rng_seed)

    def reset(self) -> None:
        """Reset state and calculated attributes.

        If `replace` is False, this resets the emitter so that it loses
        track of what has already been emitted.

        It also resets `cum_weights`.
        """
        super().reset()
        if not self._items:
            raise ValueError(
                f"The 'items' attribute must be a non-empty sequence. "
                f"(Provided: {self._items})"
            )
        self._num_unique_items = len(self._items)
        if self.weights is not None:
            nitems = len(self._items)
            nweights = len(self.weights)
            if nitems != nweights:
                noun_phr = f"{self.noun} choices" if self.noun else "choices"
                raise ValueError(
                    f"Mismatched number of {noun_phr} ({nitems}) to choice "
                    f"weights ({nweights}). These amounts must match."
                )
            self.cum_weights = list(itertools.accumulate(self.weights))

        if not self.replace:
            # For emitters without replacement, it's most efficient to
            # pre-shuffle items ONCE. Then you just return items in
            # shuffled order as they're requested. Resetting and
            # reseeding both regenerate this shuffle.
            self._global_shuffle()

    def seed(self, rng_seed: Any) -> None:
        """See superclass.

        WARNING: Reseeding an emitter where `replace` is False resets
        the random shuffle, losing track of what has already been
        emitted, if anything. I think this is what would be expected.
        """
        super().seed(rng_seed)
        if not self.replace:
            # For emitters without replacement: the new seed isn't
            # applied to what we emit until we regenerate the shuffle,
            # losing track of what has already been emitted.
            self._global_shuffle()

    def _global_shuffle(self):
        weights = self.weights or [1] * len(self._items)
        self._shuffled = weighted_shuffle(self._items, weights, self.rng)
        self._shuffled_index = 0

    @property
    def emits_unique_values(self) -> bool:
        """Returns True if this emitter only emits unique values.

        If `self.replace` is False, then this is based on the items
        that are left. This may change from False to True if an emitter
        without replacement has already emitted all the duplicates.
        """
        if not self.replace:
            return self.num_unique_items == self.num_unique_values
        return False

    @property
    def num_unique_values(self) -> int:
        """Returns the number of unique values that can be emitted.

        Use this to sanity-check an `emit` call if unique values are
        required. If `self.replace` is False, then this gives you the
        number of unique values that remain to be selected. Otherwise,
        it gives you the total number of unique values that can be
        selected.
        """
        if getattr(self, '_shuffled', None):
            return len(set(self._shuffled[self._shuffled_index:]))
        return super().num_unique_values

    @property
    def num_unique_items(self) -> int:
        """Returns the number of unique items that can be emitted.

        If `self.replace` is False, then this gives you the number of
        items that remain to be selected.
        """
        return self._num_unique_items

    def _choice_without_replacement(self, number: int):
        """Makes choices without replacing items."""
        if number > self._num_unique_items:
            self.raise_uniqueness_violation(number)
        if not self.replace:
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
        if self.weights is None:
            # One call without replacement, without weights.
            return self.rng.sample(self._items, k=number)
        # One call without replacement, with weights.
        return weighted_shuffle(self._items, self.weights, self.rng, number)

    def _choice_with_replacement(self, number: int):
        """Makes non-unique choices (with replacement)."""
        if len(self._items) == 1:
            # No choice here.
            return list(self._items) * number
        if self.weights is None and number == 1:
            # `choice` is fastest if there are no weights and we just
            # need 1.
            return [self.rng.choice(self._items)]
        return self.rng.choices(self._items, cum_weights=self.cum_weights,
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
        if not self.replace or (self.replace_only_after_call and number > 1):
            return self._choice_without_replacement(number)
        return self._choice_with_replacement(number)


def poisson_choice(items: Sequence[T],
                   mu: int = 1,
                   weight_floor: Number = 0,
                   replace: bool = True,
                   replace_only_after_call: bool = False,
                   noun: str = '',
                   rng_seed: Any = None) -> Choice:
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
                    mu: Number = 0,
                    sigma: Number = 1,
                    weight_floor: Number = 0,
                    replace: bool = True,
                    replace_only_after_call: bool = False,
                    noun: str = '',
                    rng_seed: Any = None) -> None:
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


def chance(percent_chance: Number, rng_seed: Any = None) -> None:
    """Returns a Choice emitter with a percent_chance of emitting True.

    Args:
        percent_chance: A number representing the percent chance this
            emits True. Always emits False if chance <= 0; always emits
            True if chance >= 100.
        rng_seed: (Optional.) 'rng_seed' kwarg to pass to Choice.
    """
    return Choice([True, False], [percent_chance, 100 - percent_chance],
                  rng_seed=rng_seed)
