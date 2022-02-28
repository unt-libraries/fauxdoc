"""Contains math utility functions used in the data module."""
import datetime
import heapq
import math
import random
from typing import Optional, Sequence

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
