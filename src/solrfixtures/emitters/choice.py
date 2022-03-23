"""Contains emitters for choosing random data values."""
import itertools
from typing import Any, Optional, List, Sequence, TypeVar

from solrfixtures.emitter import RandomEmitter
from solrfixtures.exceptions import ChoicesWeightsLengthMismatch
from solrfixtures.mathtools import weighted_shuffle
from solrfixtures.typing import Number


class ChoicesEmitter(RandomEmitter):
    """Class for making random selections, optionally with weighting.

    This covers any kind of random choice and implements the most
    efficient algorithm available: choices with or without weights and
    choices with or without replacement (i.e. "unique" or not). You
    should use this to implement random selection within any kind of
    range; e.g. the random selection here is more efficient than
    random.randint.

    Note that "uniqueness" is NOT based on value. Your sequence of
    items may contain duplicate values; uniqueness just means that each
    item is only selected once. E.g., with the sequence ['H', 'H', 'T']
    -- in a "unique" selection, the value 'H' may appear twice.

    Attributes:
        rng: Random Number Generator, inherited from superclass.
        items: A sequence of values you wish to choose from.
        weights: (Optional.) A sequence of weights, one per item, for
            controlling the probability of selections. This *must* be
            the same length as `items`. Weights should *not* be
            cumulative. Default is None.
        cum_weights: (Optional.) Cumulative weights are calculated from
            `weights`, if provided.
        unique: (Optional.) A bool value, True if selections must be
            unique until all items are exhausted or the emitter is
            reset. Default is False.
        each_unique: (Optional.) A bool value; True if each selection
            requesting multiple items at once must have unique values
            but values may be reused for each such selection. Default
            is False. If `unique` is True, each multiple-item selection
            is already guaranteed to be unique.
        noun: (Optional.) A string representing a singular noun or
            noun-phrase that describes what each item is. Used in
            raising a more informative error if weights and items don't
            match. Default is an empty string.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. Default is None.
    """

    T = TypeVar('T')

    def __init__(self,
                 items: Sequence[T],
                 weights: Optional[Sequence[Number]] = None,
                 unique: bool = False,
                 each_unique: bool = False,
                 noun: str = '',
                 rng_seed: Any = None) -> None:
        """Inits a ChoicesEmitter with items, weights, and settings.

        Args:
            items: See `items` attribute.
            weights: (Optional.) See `weights` attribute.
            unique: (Optional.) See `unique` attribute.
            each_unique: (Optional.) See `each_unique` attribute.
            noun: (Optional.) See `noun` attribute.
            rng_seed: (Optional.) See `rng_seed` attribute.
        """
        self.items = items
        self.weights = weights
        self.cum_weights = None
        self.unique = unique
        self.each_unique = each_unique
        self.noun = noun
        self.rng_seed = rng_seed
        self._shuffled = None
        self._shuffled_index = None
        self.reset()

    def reset(self) -> None:
        """Reset state and calculated attributes.

        If `unique` is True, this resets the emitter so that it loses
        track of what has already been emitted.

        It also resets `cum_weights`.
        """
        super().reset()
        if not self.items:
            raise ValueError(
                f"The 'items' attribute must be a non-empty sequence. "
                f"(Provided: {self.items})"
            )
        if self.weights is not None:
            nitems = len(self.items)
            nweights = len(self.weights)
            if nitems != nweights:
                raise ChoicesWeightsLengthMismatch(nitems, nweights, self.noun)
            if not (self.unique or self.each_unique):
                self.cum_weights = list(itertools.accumulate(self.weights))

        if self.unique:
            # For globally unique emitters (without replacement), it's
            # most efficient to pre-shuffle the items ONCE. Then you
            # just return the values in shuffled order as they're
            # requested. Resetting regenerates this shuffle.
            weights = self.weights or [1] * len(self.items)
            self._shuffled = weighted_shuffle(self.items, weights, self.rng)
            self._shuffled_index = 0

    def _get_next_shuffled(self, number: int = 1) -> List[T]:
        slc_start = self._shuffled_index
        slc = self._shuffled[slc_start:slc_start+number]
        self._shuffled_index += number
        return slc

    @property
    def emits_unique_values(self) -> bool:
        """Returns True if this emitter only emits unique values."""
        return self.unique

    @property
    def num_unique_values(self) -> int:
        """Returns the remaining number of unique values to be emitted.

        Use this to sanity-check an `emit` call, if any uniqueness is
        required. If `self.unique` is True, then this gives you how
        many items remain to be selected. Otherwise, it gives you the
        total number of unique items to be selected.
        """
        try:
            return len(self._shuffled) - self._shuffled_index
        except TypeError:
            return len(self.items)

    def emit(self, number: int) -> List[T]:
        """Returns a list of randomly chosen items.

        This uses the most efficient selection method possible given
        the emitter configuration and checks to ensure there are enough
        unique values available if `self.unique` or `self.each_unique`
        is True.

        Args:
            number: An int; how many items you want to choose.
        """
        if self.unique or self.each_unique:
            if number > self.num_unique_values:
                self.raise_uniqueness_violation(number)
            if self.unique:
                # Global no replacement, with/without weights.
                return self._get_next_shuffled(number)
            if self.weights is None:
                # Local no replacement, without weights.
                return self.rng.sample(self.items, k=number)
            # Local no replacement, with weights.
            return weighted_shuffle(self.items, self.weights, self.rng, number)
        # With replacement, with/without weights.
        if len(self.items) == 1:
            # No choice here.
            return list(self.items) * number
        if self.weights is None and number == 1:
            # `choice` is faster if we just need 1.
            return [self.rng.choice(self.items)]
        return self.rng.choices(self.items, cum_weights=self.cum_weights,
                                k=number)


