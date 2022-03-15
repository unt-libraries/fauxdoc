"""Contains custom date and time sequence types."""

from collections.abc import Sequence
from datetime import date, time, timedelta
import math
from typing import Optional

from .math import clamp


class DateRange(Sequence):
    """Class for creating range-like sequences of datetime.dates."""

    def __init__(self, start: date, stop: date, step: int = 1) -> None:
        self._start = start
        self._stop = stop
        self._step = step
        self._offset_range = range(0, self.value_to_offset(stop), step)
        self._length = len(self._offset_range)

    def offset_to_value(self, offset: int) -> date:
        return self.start + timedelta(days=offset)

    def value_to_offset(self, value: date) -> int:
        return (value - self.start).days

    @property
    def start(self) -> date:
        return self._start

    @property
    def stop(self) -> date:
        return self._stop

    @property
    def step(self) -> int:
        return self._step

    def __getitem__(self, index: int) -> date:
        if isinstance(index, slice):
            slc = self._offset_range[index]
            start = self.offset_to_value(slc.start)
            stop = self.offset_to_value(slc.stop)
            return type(self)(start, stop, slc.step)
        try:
            return self.offset_to_value(self._offset_range[index])
        except IndexError:
            raise IndexError(f'{type(self).__name__} object index out of '
                             f'range')

    def __len__(self) -> int:
        return self._length

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.start}, {self.stop}, {self.step})'

    def __eq__(self, other: 'DateRange') -> bool:
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
              value: date,
              start: Optional[int] = None,
              stop: Optional[int] = None) -> int:
        offset = self.value_to_offset(value)
        if offset in self._offset_range[start:stop]:
            return offset
        raise ValueError(f'{value} is not in range')

    def __contains__(self, value: date) -> bool:
        try:
            self.index(value)
        except ValueError:
            return False
        return True

    def count(self, value: date) -> int:
        return 1 if value in self else 0
