"""Contains math utility functions used in the data module."""
import datetime
import math
import random
from typing import List, Optional, Sequence

from .exceptions import ChoicesWeightsLengthMismatch
from solrfixtures.typing import Number, T


def poisson(x: int, mu: Optional[Number] = 1) -> float:
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


def gaussian(x: Number,
             mu: Optional[Number] = 0,
             sigma: Optional[Number] = 1) -> float:
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


def clamp(number: Number,
          mn: Optional[Number] = None,
          mx: Optional[Number] = None) -> Number:
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


def time_to_seconds(time: datetime.time) -> float:
    """Determines the # of seconds since midnight for a datetime.time.

    E.g.: 12:00:59 AM is 59 seconds since midnight, so
    time_to_seconds(datetime.time(0, 0, 59)) returns 59.

    Args:
        time: The input datetime.time object. It may or may not be
            timezone aware.

    Returns:
        A float representing the # of seconds since midnight.
    """
    second = time.second + (time.microsecond / (10 ** 6))
    return (time.hour * 3600) + (time.minute * 60) + second


def seconds_to_time(seconds: Number) -> datetime.time:
    """Converts a # of seconds since midnight to a datetime.time.

    E.g.: 43200 seconds after midnight is noon, so
    seconds_to_time(43200) returns datetime.time(12, 0, 0).

    Args:
        seconds: The input float representing seconds since midnight.
            If a value > 86399 is provided, then the clock effectively
            rolls over. 86400 and 0 both return midnight.

    Returns:
        A datetime.time value corresponding to the # of seconds since
        midnight.
    """
    seconds %= 86400
    hour = int(seconds / 3600)
    minute_seconds = seconds % 3600
    minute = int(minute_seconds / 60)
    seconds_float = minute_seconds % 60
    second = int(seconds_float)
    microsecond = round((seconds_float - second) * (10 ** 6))
    return datetime.time(hour, minute, second, microsecond)


def weighted_shuffle(items: Sequence[T],
                     weights: Sequence[Number],
                     rng: Optional[random.Random] = random.Random(),
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
    def _faster_for_low_k(items, weights, rng, k):
        # I adapted this from https://stackoverflow.com/a/43649323.
        # We iterate using random.choices to build our sample, removing
        # duplicate selections as we go. This brute force approach is
        # surprisingly fast for lower values of k.
        weights = list(weights)
        positions = range(len(items))
        sample = []
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

    def _faster_for_high_k(items, weights, rng, k):
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
        raise ChoicesWeightsLengthMismatch(nitems, nweights)

    # The k threshold where the `high_k` method becomes faster than the
    # `low_k` is k =~ 42% of the total number of items.
    if number <= nitems * 0.42:
        return _faster_for_low_k(items, weights, rng, number)
    return _faster_for_high_k(items, weights, rng, number)
