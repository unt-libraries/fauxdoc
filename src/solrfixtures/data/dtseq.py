"""Contains custom date and time sequence types."""

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from typing import Any, Optional, TypeVar, Union

from .math import time_to_seconds, seconds_to_time
from solrfixtures.typing import DateLike, DateTimeLike, TimeLike


class DateOrTimeRange(Sequence):
    """Class for creating range-like objs for dates and times."""

    DT = TypeVar('DT', DateLike, DateTimeLike, TimeLike)

    def __init__(self, start: DT, stop: DT, step: timedelta) -> None:
        self._start = start
        self._stop = stop
        self._step = step

        stop_offset, rem = self._value_to_offset(stop)
        # If the stop value is not a multiple of step, we stop the
        # offset range on the NEXT value to ensure our range includes
        # the last multiple of step.
        if rem:
            stop_offset += 1
        self._offset_range = range(0, stop_offset)
        self._length = len(self._offset_range)
        desc = f'"{start}", "{stop}", step="{step}"'
        self._str_repr = f"{type(self).__name__}({desc})"

    def _offset_to_value(self, offset: int) -> date:
        return self.start + (self.step * offset)

    def _value_to_offset(self, value: date) :
        return divmod(value - self.start, self.step)

    @property
    def start(self) -> DT:
        return self._start

    @property
    def stop(self) -> DT:
        return self._stop

    @property
    def step(self) -> int:
        return self._step

    def __getitem__(self, index: int) -> DT:
        if isinstance(index, slice):
            slc = self._offset_range[index]
            start = self._offset_to_value(slc.start)
            stop = self._offset_to_value(slc.stop)
            return type(self)(start, stop, self.step * slc.step)
        try:
            return self._offset_to_value(self._offset_range[index])
        except IndexError:
            pass
        raise IndexError(f'{type(self).__name__} object index out of range')

    def __len__(self) -> int:
        return self._length

    def __repr__(self) -> str:
        return self._str_repr

    def __eq__(self, other: 'OffsetRange') -> bool:
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
        offset, rem = self._value_to_offset(value)
        if not rem and offset in self._offset_range[start:stop]:
            return offset
        raise ValueError(f'{value} is not in range')

    def __contains__(self, value: DT) -> bool:
        try:
            self.index(value)
        except ValueError:
            return False
        return True

    def count(self, value: DT) -> int:
        return 1 if value in self else 0


def parse_user_value(value: Any) -> date:
    try:
        return date(value.year, value.month, value.day)
    except AttributeError:
        try:
            return date.fromisoformat(value)
        except ValueError:
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                pass
            else:
                return date(value.year, value.month, value.day)
    raise ValueError(
        '`parse_user_value` value must be a datetime.date-like object or '
        'string that datetime.date.fromisoformat or datetime.datetime.'
        'fromisoformat can interpret (e.g. YYYY-MM-DD format).'
    )
