"""Contains emitters for choosing random data values."""
import itertools
from typing import Any, Optional, List, Sequence, TypeVar

from solrfixtures.emitter import RandomEmitter
from solrfixtures.mathtools import clamp, gaussian, poisson, weighted_shuffle
from solrfixtures.typing import Number, T


class Choice(RandomEmitter):
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

    def __init__(self,
                 items: Sequence[T],
                 weights: Optional[Sequence[Number]] = None,
                 unique: bool = False,
                 each_unique: bool = False,
                 noun: str = '',
                 rng_seed: Any = None) -> None:
        """Inits a Choice emitter with items, weights, and settings.

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
                noun_phr = f"{self.noun} choices" if self.noun else "choices"
                raise ValueError(
                    f"Mismatched number of {noun_phr} ({nitems}) to choice "
                    f"weights ({nweights}). These amounts must match."
                )
            self.cum_weights = list(itertools.accumulate(self.weights))

        if self.unique:
            # For globally unique emitters (without replacement), it's
            # most efficient to pre-shuffle the items ONCE. Then you
            # just return the values in shuffled order as they're
            # requested. Resetting and reseeding both regenerate this
            # shuffle.
            self._global_shuffle()

    def seed(self, rng_seed: Any) -> None:
        """See superclass.

        WARNING: Reseeding a globally unique emitter (`unique` is True)
        resets the random shuffle, losing track of what has already
        been emitted, if anything. I think this is what would be
        expected.
        """
        super().seed(rng_seed)
        if self.unique:
            # For unique emitters: the new seed isn't applied to what
            # we emit until we regenerate the shuffle, losing track of
            # what has already been emitted. If it turns out that this
            # is confusing, it would be possible to allow for a partial
            # reshuffle -- e.g., only reshuffle
            # self._shuffled[self.shuffled_index:]. However, we would
            # have to implement a version of the `weighted_shuffle`
            # algorithm that lets us get the corresponding weights
            # along with the shuffled items whenever we do a global
            # shuffle. (Right now we lose what weights go with what
            # items when they get shuffled.) I'm leaving this as a
            # possible future TODO if turns out to be needed.
            self._global_shuffle()

    def _global_shuffle(self):
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
        if self.unique or (self.each_unique and number > 1):
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


class PoissonChoice(Choice):
    """Choice emitter that applies Poisson weighting when choosing.

    Attributes:
        See parent class.
    """

    def __init__(self,
                 items: Sequence[T],
                 mu: int = 1,
                 weight_floor: Number = 0,
                 unique: bool = False,
                 each_unique: bool = False,
                 noun: str = '',
                 rng_seed: Any = None) -> None:
        """Inits a PoissonChoice emitter.

        Args:
            items: See parent class.
            mu: (Optional.) A positive integer or float representing
                the average x value, or peak, of the distribution
                curve. This controls which items are chosen most
                frequently. Default is 1.
            weight_floor: (Optional.) A positive integer or float
                representing the lowest possible individual weight for
                an item. This is most useful when you have a large
                number of choices in 'items' -- it helps ensure you'll
                see more of the long tail in choices that are made, at
                the expense of comprimising the integrity of the
                distribution. Set to 0 if you do not want a floor.
                Default is 0.
            unique: (Optional.) See parent class.
            each_unique: (Optional.) See parent class.
            noun: (Optional.) See parent class.
            rng_seed: (Optional.) See parent class.
        """
        weights = [clamp(poisson(x, mu), mn=weight_floor)
                   for x in range(1, len(items) + 1)]
        super().__init__(items, weights, unique, each_unique, noun, rng_seed)


class GaussianChoice(Choice):
    """Choice emitter that applies Gaussian weighting when choosing.

    Attributes:
        See parent class.
    """

    def __init__(self,
                 items: Sequence[T],
                 mu: Number = 0,
                 sigma: Number = 1,
                 weight_floor: Number = 0,
                 unique: bool = False,
                 each_unique: bool = False,
                 noun: str = '',
                 rng_seed: Any = None) -> None:
        """Inits a GaussianChoice emitter.

        Args:
            items: See parent class.
            mu: (Optional.) An integer or float representing the
                average x value, or peak, of the distribution curve.
                This controls which items are chosen most frequently.
                Default is 0.
            sigma: (Optional.) A positive integer or float representing
                the standard deviation of the distribution curve, which
                controls the width of the curve. Default is 1. Lower
                values create a sharper peak, decreasing the number of
                items around the peak that are chosen frequently.
                Higher values dull the peak, increasing how frequently
                the items around the peak are chosen.
            weight_floor: (Optional.) A positive integer or float
                representing the lowest possible individual weight for
                an item. This is most useful when you have a large
                number of choices in 'items' -- it helps ensure you'll
                see more of the long tail in choices that are made, at
                the expense of comprimising the integrity of the
                distribution. Set to 0 if you do not want a floor.
                Default is 0.
            unique: (Optional.) See parent class.
            each_unique: (Optional.) See parent class.
            noun: (Optional.) See parent class.
            rng_seed: (Optional.) See parent class.
        """
        weights = [clamp(gaussian(x, mu, sigma), mn=weight_floor)
                   for x in range(1, len(items) + 1)]
        super().__init__(items, weights, unique, each_unique, noun, rng_seed)


class Chance(Choice):
    """Choice emitter that emits True/False based on chance percentage.

    Attributes:
        See superclass.
    """

    def __init__(self, percent_chance: Number, rng_seed: Any = None) -> None:
        """Inits a Chance emitter with the given percentage.

        Args:
            percent_chance: A number representing the percent chance
                this will emit True. Always emits False if chance <= 0,
                and always emits True if chance >= 100.
            rng_seed: See superclass.
        """
        super().__init__([True, False], [percent_chance, 100 - percent_chance],
                         rng_seed=rng_seed)
