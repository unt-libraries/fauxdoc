"""Contains an implementation of a custom date/time range type."""
from datetime import date, datetime, time, timedelta
from typing import Optional, overload, Sequence, Tuple, TypeVar, Union


DT = TypeVar('DT', date, datetime, time)
DTS = TypeVar('DTS', date, datetime, time, str)


def _index_to_value(index: int, start: DT, step: timedelta) -> DT:
    """Converts a 0-based index number to a date/time value."""
    delta = step * index
    if isinstance(start, time):
        # We can't do timedelta operations on time objects, so we have
        # to fake it by combining the time with a reference date, doing
        # the math, and returning the time.
        ref_date = date(99, 1, 1)
        ref_dt = datetime.combine(ref_date, start)
        return (ref_dt + delta).time()
    return start + delta


def _value_to_index(value: DT, start: DT,
                    step: timedelta) -> Tuple[int, timedelta]:
    """Converts a date/time value to a 0-based index number.

    `value` is the date, time, or datetime value to convert; `start` is
    the 0-index value; and `step` is the timedelta interval between
    values.
    """
    if isinstance(start, time):
        # We can't do timedelta operations on `time` objects, so we
        # have to fake it by combining the time with a reference date,
        # doing the math, and getting the time. We also want to wrap at
        # midnight; a range like 11:00 PM to 4:00 AM with step +1 sec
        # is valid, as is 4:00 AM to 11:00 PM with step -1 sec. We have
        # to add a day on either side to make this work.
        step_secs = step.total_seconds()
        startdate = date(99, 1, 2)
        if value < start and step_secs > 0:
            valdate = date(99, 1, 3)
        elif value > start and step_secs < 0:
            valdate = date(99, 1, 1)
        else:
            valdate = startdate
        valdt = datetime.combine(valdate, value)
        startdt = datetime.combine(startdate, start)
    else:
        valdt = value
        startdt = start
    return divmod(valdt - startdt, step)


class DateOrTimeRange(Sequence[DT]):
    """Class for representing ranges of dates and/or times.

    This is meant to be like the `range` type, for dates, times, and
    datetimes. The __init__ signature is slightly different (it takes
    a length instead of a stop value); this is to improve performance
    of operations like slicing where we otherwise have to do repeated
    conversions to date/time values unnecessarily.

    Under most circumstances you'll want to use the `dtrange`
    factory function to instantiate instances. That has a more range-
    like interface and a few convenience features that I left out of
    the class to keep it more focused.

    Attributes:
        length: A read-only attribute set on initialization. This is an
            int for the number of elements in the range.
        start: A read-only attribute set on initialization. This is a
            date, time, or datetime object, from the datetime module;
            the value that starts your range. All values in your range
            will have the same type.
        step: A read-only attribute set on initialization. This is a
            datetime.timedelta object representing the space between
            units in your range. We constrain this based on the
            date/time type your range stores. `date` ranges cannot
            represent time units smaller than a day, and `time` ranges
            cannot represent time units larger than a day.
        stop: A read-only attribute that is set lazily. It is the date,
            time, or datetime object that ends your range (not
            inclusive), set based on the 'start' and 'length' values.
    """

    def __init__(self, start: DT, length: int, step: timedelta) -> None:
        """Inits DateorTimeRange with start, length, and step.

        Arguments:
            start: See `start` attribute.
            length: See `length` attribute.
            step: See `step` attribute.
        """
        self.length = length
        self.start = start
        self.step = step
        self._index_range = range(0, length)

    @property
    def start(self) -> DT:
        """Read-only property. Returns the 'start' attribute."""
        return self._start

    @start.setter
    def start(self, start_val: DT) -> None:
        """Setter for the 'start' attribute. Can only be set once."""
        if hasattr(self, '_start'):
            raise AttributeError("Can't set attribute 'start'")
        if not isinstance(start_val, (date, datetime, time)):
            raise ValueError(
                "Attribute 'start' must be an instance of date, datetime, or "
                "time, from the datetime module."
            )
        self._start: DT = start_val

    @property
    def stop(self) -> DT:
        """Read-only property. Returns the 'stop' attribute."""
        if not hasattr(self, '_stop'):
            self._stop: DT = _index_to_value(len(self), self.start, self.step)
        return self._stop

    @property
    def step(self) -> timedelta:
        """Read-only property. Returns the 'step' attribute."""
        return self._step

    @step.setter
    def step(self, step_val: timedelta) -> None:
        """Setter for the 'step' attribute. Can only be set once."""
        if hasattr(self, '_step'):
            raise AttributeError("Can't set attribute 'step'")
        if not isinstance(step_val, timedelta):
            raise ValueError(
                "Attribute 'step' must be an instance of datetime.timedelta."
            )
        start_is_date_only = not hasattr(self.start, 'second')
        start_is_time_only = not hasattr(self.start, 'day')
        if start_is_date_only and step_val.total_seconds() % 86400:
            raise ValueError(
                "The 'step' amount is invalid for a date range lacking a time "
                "component. It must be some number of whole days, e.g. "
                "timedelta(days=5)."
            )
        elif start_is_time_only and abs(step_val.total_seconds()) >= 86400:
            raise ValueError(
                "The 'step' amount is invalid for a time range lacking a date "
                "component. It must be less than one day, e.g.: "
                "timedelta(days=-1) < step < timedelta(days=1)."
            )
        self._step = step_val

    @property
    def length(self) -> int:
        """Read-only property. Returns the 'length' attribute."""
        return self._length

    @length.setter
    def length(self, length_val: int) -> None:
        """Setter for the 'length' attribute. Can only be set once."""
        if hasattr(self, '_length'):
            raise AttributeError("Can't set attribute 'length'")
        try:
            self._length = int(length_val)
        except ValueError as e:
            raise type(e)(
                "Attribute 'length' must be (or be castable to) an int."
            )

    @overload
    def __getitem__(self, index: int) -> DT:
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[DT]:
        ...

    def __getitem__(self, index: Union[int, slice]) -> Union[Sequence[DT], DT]:
        """Returns the requested value or values from the range."""
        if isinstance(index, slice):
            slc = self._index_range[index]
            start = _index_to_value(slc.start, self.start, self.step)
            return type(self)(start, len(slc), self.step * slc.step)
        try:
            index_num = self._index_range[index]
        except IndexError:
            raise IndexError(f'{type(self).__name__} object index out of '
                             f'range')
        return _index_to_value(index_num, self._start, self._step)

    def __len__(self) -> int:
        """Returns the length of the range."""
        return self._length

    def __repr__(self) -> str:
        """Returns the string representation of the range."""
        if not hasattr(self, '_str_repr'):
            stop = str(self.stop)
            if isinstance(self.start, time):
                days = (self.step * len(self)).days
                if days > 0:
                    plural = '' if days == 1 else 's'
                    stop = f"{days} day{plural} + {self.stop}"
            desc = f'"{self.start}", "{stop}", step="{self.step}"'
            self._str_repr = f"{type(self).__name__}({desc})"
        return self._str_repr

    def __eq__(self, other: object) -> bool:
        """Returns True if this range is equal to a comparison range."""
        if not isinstance(other, type(self)):
            return NotImplemented
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
        """Returns a hash number for an instance of this type."""
        my_len = len(self)
        start = self.start if my_len > 0 else None
        step = self.step if my_len > 1 else None
        return hash((type(self), my_len, start, step))

    def index(self,
              value: DT,
              start: Optional[int] = None,
              stop: Optional[int] = None) -> int:
        """Returns the 0-based index for a given in-range value.

        Args:
            value: A date, time, or datetime that may be in this range.
            start: (Optional.) Limit your search based on this starting
                index.
            stop: (Optional.) Limit your search based on this stop
                index value.
        """
        if isinstance(value, type(self.start)):
            index, rem = _value_to_index(value, self._start, self._step)
            if not rem and index in self._index_range[start:stop]:
                return index
        raise ValueError(f'{value} is not in range')

    def __contains__(self, value: object) -> bool:
        """Returns True if a value is in this range."""
        if isinstance(value, type(self.start)):
            try:
                self.index(value)
            except ValueError:
                pass
            else:
                return True
        return False

    def count(self, value: DT) -> int:
        """Returns the number of times a value occurs in this range.

        Args:
            value: A date, time, or datetime that may be in this range.
        """
        return 1 if value in self else 0


def _parse_user_date(val: Union[DT, str], label: str) -> DT:
    """Converts a user date value to the appropriate date/time type."""
    dtypes = (date, time, datetime)
    if isinstance(val, dtypes):
        return val
    if isinstance(val, str):
        for dtype in dtypes:
            fromisoformat = getattr(dtype, 'fromisoformat')
            try:
                # Note: mypy throws a no-any-return error on this, I'm
                # assuming because it can't tell what the return value
                # of `fromisoformat` is supposed to be.
                return fromisoformat(val)  # type: ignore[no-any-return]
            except ValueError:
                pass
    raise ValueError(
        f"Cannot decipher '{label}' argument date type (`{val}`). It must "
        f"either be an instance of date, datetime, or time (from the datetime "
        f"module), or a string that the `fromisoformat` method of one of "
        f"these types can interpret."
    )


def dtrange(start: Union[DT, str], stop: Union[DT, str], step: float = 1,
            step_unit: Optional[str] = None) -> DateOrTimeRange[DT]:
    """Constructs and returns a DateOrTimeRange object.

    This is the intended public factory method that makes it easy to
    create DateOrTimeRange objects.

    Important note: `dtrange` is meant to function like `range`, where
    'stop' is excluded. For `time` objects, this presents a problem
    with the common edge case where you want a full 24-hour range: if
    you want 00:00:00 to 23:59:59 (inclusive), you can't provide a
    stop value of time(24, 0) because this is not a valid time. So, for
    `time` ranges only, we'll assume if 'start' == 'stop' you want a
    24-hour range rather than an empty range. For `date` and `datetime`
    ranges, you get an empty range.

    Args:
        start: A date, time, datetime, or string object representing
            the start of your range. If you provide a string, then it
            must be interpretable by the `fromisoformat` method of one
            these types. (Note this is just for convenience and is not
            meant to exhaustively parse an ISO formatted date string.)
        stop: A date, time, datetime, or string object representing the
            end of your range, not inclusive. Like 'start', if you
            provide a string it must be interpretable by the
            `fromisoformat` method of date, time, or datetime. 'stop'
            and 'start must ultimately resolve to the same type.
        step: (Optional.) An integer representing the number of units
            in your range. Default is 1.
        step_unit: (Optional.) A string defining what 'step'
            represents: weeks, days, hours, minutes, seconds, or
            microseconds. If your range contains `date` objects, then
            this defaults to "days" -- otherwise "seconds".
    """
    start_obj = _parse_user_date(start, 'start')
    stop_obj = _parse_user_date(stop, 'stop')

    if type(start_obj) != type(stop_obj):
        raise ValueError(
            f"The 'start' and 'stop' arguments must be interpretable as the "
            f"same datetime type. The provided arguments appear to be "
            f"different types: `{type(start_obj)}` and `{type(stop_obj)}`."
        )

    if step_unit is None:
        step_unit = 'seconds' if hasattr(start_obj, 'second') else 'days'

    try:
        step_td = timedelta(**{step_unit: step})
    except TypeError:
        raise ValueError(
            "Invalid 'step_unit' argument. It must be a valid kwarg for "
            "timedelta: weeks, days, hours, minutes, seconds, or microseconds."
        )

    if isinstance(start_obj, time) and start_obj == stop_obj:
        # This is kind of hacky but the simplest way I could think of
        # to accommodate the (common) edge case where you want the full
        # 24-hour clock as a time range. E.g., midnight to midnight is
        # a 24-hour range instead of an empty range.
        start_refdate = datetime.combine(date(99, 1, 1), start_obj)
        stop_refdate = start_refdate + timedelta(days=1)
        length, rem = _value_to_index(stop_refdate, start_refdate, step_td)
    else:
        length, rem = _value_to_index(stop_obj, start_obj, step_td)
    length += 1 if rem else 0
    return DateOrTimeRange(start_obj, length, step_td)
