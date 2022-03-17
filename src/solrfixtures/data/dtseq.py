"""Contains custom date and time sequence types."""

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from typing import Any, Optional, Tuple, TypeVar, Union

from .math import time_to_seconds, seconds_to_time
from solrfixtures.typing import DateLike, DateTimeLike, Number, TimeLike


DT = TypeVar('DT', DateLike, DateTimeLike, TimeLike)
DTS = TypeVar('DTS', DateLike, DateTimeLike, TimeLike, str)


def _index_to_value(index: int, start: DT, step: timedelta) -> DT:
    try:
        return start + (step * index)
    except TypeError:
        # We can't do timedelta operations on `time` objects, so we
        # have to fake it.
        seconds = time_to_seconds(start) + (step.total_seconds() * index)
        return seconds_to_time(seconds)


def _value_to_index(value: DT, start: DT,
                    step: timedelta) -> Tuple[int, timedelta]:
    try:
        return divmod(value - start, step)
    except TypeError:
        # We can't do timedelta operations on `time` objects, so we
        # have to fake it.
        val_secs = time_to_seconds(value)
        start_secs = time_to_seconds(start)
        step_secs = step.total_seconds()

        # We want to wrap at midnight; a range like 11:00 PM to 4:00 AM
        # with step +1 second is valid, as is 4:00 AM to 11:00 PM with
        # step -1 second. We have to add a day on either side to make
        # this work.
        if val_secs < start_secs and step_secs > 0:
            val_secs += 86400
        elif val_secs > start_secs and step_secs < 0:
            start_secs += 86400
        index, rem = divmod(val_secs - start_secs, step_secs)
        return int(index), timedelta(seconds=rem)


class DateOrTimeRange(Sequence):
    """Class for representing ranges of dates and/or times."""

    def __init__(self, start: DT, length: int, step: timedelta) -> None:
        self._index_range = range(0, length)
        self._length = length
        self._start = start
        self._step = step
        self._stop = None
        self._str_repr = None

    @property
    def start(self) -> DT:
        return self._start

    @property
    def stop(self) -> DT:
        if self._stop is None:
            self._stop = _index_to_value(len(self), self._start, self._step)
        return self._stop

    @property
    def step(self) -> int:
        return self._step

    def __getitem__(self, index: int) -> DT:
        if isinstance(index, slice):
            slc = self._index_range[index]
            start = _index_to_value(slc.start, self._start, self._step)
            return type(self)(start, len(slc), self._step * slc.step)
        try:
            index_num = self._index_range[index]
        except IndexError:
            raise IndexError(f'{type(self).__name__} object index out of '
                             f'range')
        return _index_to_value(index_num, self._start, self._step)

    def __len__(self) -> int:
        return self._length

    def __repr__(self) -> str:
        if self._str_repr is None:
            desc = f'"{self.start}", "{self.stop}", step="{self.step}"'
            self._str_repr = f"{type(self).__name__}({desc})"
        return self._str_repr

    def __eq__(self, other: 'DateOrTimeRange') -> bool:
        my_len = len(self)
        other_len = len(other)
        if my_len != other_len:
            return False
        if my_len == 0:
            return True
        if my_len == 1:
            return self.start == other.start
        return (self.start, self.step) == (other.start, other.step)

    def __hash__(self) -> int:
        my_len = len(self)
        start = self.start if my_len > 0 else None
        step = self.step if my_len > 1 else None
        return hash((type(self), my_len, start, step))

    def index(self,
              value: DT,
              start: Optional[int] = None,
              stop: Optional[int] = None) -> int:
        index, rem = _value_to_index(value, self._start, self._step)
        if not rem and index in self._index_range[start:stop]:
            return index
        raise ValueError(f'{value} is not in range')

    def __contains__(self, value: DT) -> bool:
        try:
            self.index(value)
        except ValueError:
            return False
        return True

    def count(self, value: DT) -> int:
        return 1 if value in self else 0


def _parse_user_value(value: DTS) -> Union[date, datetime, time]:
    if isinstance(value, (date, time, datetime)):
        return value
    if isinstance(value, str):
        for dtype in (date, datetime, time):
            try:
                return getattr(dtype, 'fromisoformat')(value)
            except ValueError:
                pass
        raise ValueError

    type_attributes = (
        (datetime, ('year', 'month', 'day', 'hour', 'second', 'minute',
                      'microsecond')),
        (date, ('year', 'month', 'day')),
        (time, ('hour', 'minute', 'second', 'microsecond'))
    )
    for dtype, attrs in type_attributes:
        try:
            return dtype(*(getattr(value, attr) for attr in attrs))
        except AttributeError:
            pass
    raise ValueError


def dt_range(start: DTS, stop: DTS, step: Number = 1,
             step_unit: Optional[str] = None) -> DateOrTimeRange:
    stop_start_err_message = (
        'Unknown argument type. It must be one of the following:\n'
        '    - datetime.date, datetime.datetime, or datetime.time;\n'
        '    - a string that the `fromisoformat` method of datetime.date, '
        'datetime.datetime, or datetime.time can interpret; or,\n'
        '    - a type like datetime.date, datetime.datetime, or datetime.time '
        'that has the appropriate year, month, day, hour, minute, second, and '
        'microsecond atteributes.'
    )

    try:
        start = _parse_user_value(start)
    except ValueError:
        raise ValueError(f'For `start` argument: {stop_start_err_message}')
    try:
        stop = _parse_user_value(stop)
    except ValueError:
        raise ValueError(f'For `stop` argument: {stop_start_err_message}')

    if type(start) != type(stop):
        raise ValueError(
            f'The `start` and `stop` arguments must be interpretable as the '
            f'same datetime type. The provided arguments appear to be types '
            f'`{type(start)}` and `{type(stop)}`.'
        )

    is_date_only = not hasattr(start, 'second')
    is_time_only = not hasattr(start, 'day')

    if step_unit is None:
        if is_date_only:
            step_unit = 'days'
        else:
            step_unit = 'seconds'

    try:
        step = timedelta(**{step_unit: step})
    except TypeError:
        raise ValueError(
            'Invalid `step_unit` argument. It must be a valid kwarg for '
            'timedelta: weeks, days, hours, minutes, seconds, or microseconds.'
        )
    if is_date_only and step_unit not in {'weeks', 'days'}:
        raise ValueError(
            f'Invalid `step_unit` argument for a range of date objects. It '
            f'must not be a unit smaller than days. (Provided: "{step_unit}")'
        )
    if is_time_only and step_unit in {'weeks', 'days'}:
        raise ValueError(
            f'Invalid `step_unit` argument for a range of time objects. It '
            f'must be a unit smaller than days. (Provided: "{step_unit}")'
        )

    length, rem = _value_to_index(stop, start, step)
    length += 1 if rem else 0
    drange = DateOrTimeRange(start, length, step)
    return drange
