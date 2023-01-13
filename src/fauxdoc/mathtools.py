"""Contains math utility functions used in the data module."""
import math
import random
from typing import List, Optional, Sequence

from fauxdoc.typing import F, T


def poisson(x: int, mu: float = 1) -> float:
    """Applies a poisson probability distribution function.

    Args:
        x: The x-axis value for which you want to return a probability
            value. It must be an integer.
        mu: (Optional.) The average x value for the distribution, i.e.,
            the peak of the distribution curve. Defaults to 1.

    Returns:
        A float value representing a probability that the given x value
        might occur.
    """
    return (mu ** x) * (math.exp(-1 * mu)) / math.factorial(x)


def gaussian(x: float, mu: float = 0, sigma: float = 1) -> float:
    """Applies a gaussian probability density function.

    Args:
        x: The x-axis value for which you want to return a probability
            value.
        mu: (Optional.) The average x value for the distribution, i.e.,
            the peak of the distribution curve. Defaults to 0.
        sigma: (Optional.) The standard deviation, which controls the
            width of the distribution curve. Defaults to 1.

    Returns:
        A float value representing the relative probability that a
        random variable would be approximately x.
    """
    term1 = math.exp(-1 * (((x - mu) / sigma) ** 2) / 2)
    term2 = 1 / (math.sqrt(2 * math.pi) * sigma)
    return term1 * term2


def clamp(number: F, mn: Optional[F] = None, mx: Optional[F] = None) -> F:
    """Limits a given number to a minimum and/or maximum value.

    Examples:
        >>> clamp(35, mn=50, mx=100)
        50
        >>> clamp(35, mn=20)
        35
        >>> clamp(35, mx=20)
        20

    Args:
        number: The number to clamp.
        mn: (Optional.) The lower limit. None means you want no lower
        limit. Default is None.
        mx: (Optional.) The upper limit. None means you want no upper
        limit. Default is None.

    Returns:
        The adjusted value based on mn and mx parameters.
    """
    if mn is not None and number < mn:
        return mn
    if mx is not None and number > mx:
        return mx
    return number


def weighted_shuffle(items: Sequence[T],
                     weights: Sequence[float],
                     rng: random.Random = random.Random(),
                     number: Optional[int] = None) -> List[T]:
    """Returns a list of items randomly shuffled based on weights.

    Use this if you need a unique random sample (i.e., select
    without replacement) using weights. The built-in `random` module
    lacks this as of Python 3.10. This is the fastest pure Python
    implementation I could manage and is about comparable to the other
    `random` methods. It's faster than numpy when `number` is ~ 0 to
    10 percent of the total number of items, and it remains below ~2x
    the speed of numpy for higher values.

    Args:
        items: Any sequence of items you wish to randomize.
        weights: A sequence of weights, one per item. Note these should
            NOT be cumulative weights.
        rng: (Optional.) A `random.Random` instance to use as the RNG.
            Defaults to a new instance.
        number: (Optional.) The number of items you need. Defaults to
            the full length of `items`.
    """
    def _faster_for_low_k(items: Sequence[T],
                          weights: Sequence[float],
                          rng: random.Random,
                          k: int) -> List[T]:
        # I adapted this from https://stackoverflow.com/a/43649323.
        # We iterate using random.choices to build our sample, removing
        # duplicate selections as we go. This brute force approach is
        # surprisingly fast for lower values of k.
        weights = list(weights)
        positions = range(len(items))
        sample: List[T] = []
        while True:
            needed = k - len(sample)
            if not needed:
                break
            for i in rng.choices(positions, weights, k=needed):
                # Duplicates: a weight of 0 indicates something has
                # been selected already, letting us skip duplicates.
                # Zeroing out weights of selected items also ensures
                # they are not reselected on the next `choices` call.
                if weights[i]:
                    weights[i] = 0.0
                    sample.append(items[i])
        return sample

    def _faster_for_high_k(items: Sequence[T],
                           weights: Sequence[float],
                           rng: random.Random,
                           k: int) -> List[T]:
        # I adapted this from https://stackoverflow.com/a/20548895.
        # This is more of an actual shuffle: we create a randomized
        # score for each item based on weight, and then reverse sort
        # by score. Having to operate on the full list makes this
        # slower for lower values of k, but the lack of iteration makes
        # it scale very well for higher values of k. Zipping the scores
        # and items is faster than tracking positions.
        scores = zip((math.log(rng.random()) / w for w in weights), items)

        # Note: to pick the highest scoring k items, reverse sorting
        # the whole list is faster than using the `heapq.nlargest`
        # method shown in the referenced StackOverflow post. The latter
        # is only faster for very small k values, where the brute force
        # low_k approach is much faster anyway.
        top_n = sorted(scores, reverse=True, key=lambda x: x[0])[:k]
        return [item for _, item in top_n]

    nitems = len(items)
    nweights = len(weights)
    number = nitems if number is None else number
    if nitems != nweights:
        raise ValueError(
            f"Mismatched number of choices ({nitems}) to choice weights "
            f"({nweights}). These amounts must match."
        )

    # The k threshold where the `high_k` method becomes faster than the
    # `low_k` is k =~ 42% of the total number of items.
    if number <= nitems * 0.42:
        return _faster_for_low_k(items, weights, rng, number)
    return _faster_for_high_k(items, weights, rng, number)
