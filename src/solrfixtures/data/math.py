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


def time_to_seconds(time: datetime.time) -> int:
    """Determines the # of seconds since midnight for a datetime.time.

    E.g.: 12:00:59 AM is 59 seconds since midnight, so
    time_to_seconds(datetime.time(0, 0, 59)) returns 59.

    Args:
        time: The input datetime.time object. It may or may not be
            timezone aware.

    Returns:
        An int representing the # of seconds since midnight.
    """
    return (time.hour * 3600) + (time.minute * 60) + time.second


def seconds_to_time(seconds: int) -> datetime.time:
    """Converts a # of seconds since midnight to a datetime.time.

    E.g.: 43200 seconds after midnight is noon, so
    seconds_to_time(43200) returns datetime.time(12, 0, 0).

    Args:
        seconds: The input integer representing seconds since midnight.
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
    second = minute_seconds % 60
    return datetime.time(hour, minute, second)


def weighted_shuffle(items: Sequence[T],
                     weights: Sequence[Number],
                     rng: Optional[random.Random] = random.Random(),
                     number: Optional[int] = None) -> List[T]:
    """Returns a list of items randomly shuffled based on weights.

    Use this if you need a unique random sample (i.e., select
    without replacement) using weights. The built-in `random` module
    lacks this as of Python 3.10, and I don't really want numpy as a
    dependency.

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
        # It is surprisingly fast for lower values of k.
        weights = list(weights)
        positions = range(len(items))
        sample = []
        while True:
            needed = k - len(sample)
            if not needed:
                break
            # Note that using random.choices *does* select duplicates.
            # Checking weights[i] for each ensures we don't add the
            # duplicates to our sample. Zeroing out the weights of
            # selected items at each iteration ensures they are not
            # reselected. 
            for i in rng.choices(positions, weights, k=needed):
                if weights[i]:
                    weights[i] = 0.0
                    sample.append(items[i])
        return sample

    def _faster_for_high_k(items, weights, rng, k):
        # I adapted this from https://stackoverflow.com/a/20548895.
        # First we create a score for each item based on weight.
        scores = zip((math.log(rng.random()) / w for w in weights), items)

        # To pick the highest scoring k items, reverse sorting is much
        # faster than using heapq.nlargest, given we're using this for
        # higher k values.
        top_n = sorted(scores, reverse=True, key=lambda x: x[0])[:k]
        return [item for _, item in top_n]

    nitems = len(items)
    nweights = len(weights)
    number = nitems if number is None else number
    if nitems != nweights:
        raise ChoicesWeightsLengthMismatch(nitems, nweights)

    # k == ~42% of the total number of items is the threshold where the
    # second method becomes faster than the first.
    if number <= nitems * 0.42:
        return _faster_for_low_k(items, weights, rng, number)
    return _faster_for_high_k(items, weights, rng, number)
