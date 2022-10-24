"""Contains tests for the fauxdoc data.dtrange module."""
from datetime import date, datetime, time, timedelta

import pytest

from fauxdoc import dtrange


def test_dateortimerange_attributes_are_readonly():
    """Public attrs start, stop, step, and length should be read only."""
    dtr = dtrange.DateOrTimeRange(date(2016, 1, 1), 7, timedelta(days=1))
    for attr in ('start', 'stop', 'step', 'length'):
        with pytest.raises(AttributeError):
            setattr(dtr, attr, 1)


@pytest.mark.parametrize('start, length, step, exp_err_str', [
    # 'start' attribute validation
    ('2016-01-01', 7, timedelta(days=1),
     "'start' must be an instance of date, datetime, or time"),
    ((2016, 1, 1), 7, timedelta(days=1),
     "'start' must be an instance of date, datetime, or time"),
    (date(2016, 1, 1), 7, timedelta(days=1), None),
    (datetime(2016, 1, 1, 10, 0, 0), 7, timedelta(days=1), None),
    (time(10, 0, 0), 10, timedelta(seconds=1), None),

    # 'length' attribute validation
    (date(2016, 1, 1), 'A', timedelta(days=1),
     "'length' must be (or be castable to) an int"),

    # 'step' attribute validation
    (date(2016, 1, 1), 7, 1,
     "'step' must be an instance of datetime.timedelta"),
    (date(2016, 1, 1), 7, 1.5,
     "'step' must be an instance of datetime.timedelta"),
    (date(2016, 1, 1), 7, timedelta(hours=2),
     "'step' amount is invalid for a date range"),
    (date(2016, 1, 1), 7, timedelta(seconds=20),
     "'step' amount is invalid for a date range"),
    (date(2016, 1, 1), 7, timedelta(hours=-20),
     "'step' amount is invalid for a date range"),
    (date(2016, 1, 1), 7, timedelta(days=2.5),
     "'step' amount is invalid for a date range"),
    (date(2016, 1, 1), 7, timedelta(days=1), None),
    (date(2016, 1, 1), 7, timedelta(days=-1), None),
    (date(2016, 1, 1), 7, timedelta(seconds=86400), None),
    (date(2016, 1, 1), 7, timedelta(seconds=-86400), None),
    (time(10, 0), 12, timedelta(days=1),
     "'step' amount is invalid for a time range"),
    (time(10, 0), 12, timedelta(days=2.5),
     "'step' amount is invalid for a time range"),
    (time(10, 0), 12, timedelta(seconds=86400),
     "'step' amount is invalid for a time range"),
    (time(10, 0), 12, timedelta(seconds=86399), None),
    (time(10, 0), 12, timedelta(minutes=-5), None),
    (time(10, 0), 12, timedelta(seconds=-86399), None),
    (datetime(2016, 1, 1, 10, 0, 0), 10, timedelta(hours=12), None),
    (datetime(2016, 1, 1, 10, 0, 0), 10, timedelta(days=2), None),
    (datetime(2016, 1, 1, 10, 0, 0), 10, timedelta(days=2.5), None),
])
def test_dateortimerange_validation(start, length, step, exp_err_str):
    if exp_err_str:
        with pytest.raises(ValueError) as excinfo:
            dtr = dtrange.DateOrTimeRange(start, length, step)
        assert exp_err_str in str(excinfo.value)
    else:
        dtr = dtrange.DateOrTimeRange(start, length, step)
        assert dtr.start == start
        assert dtr.length == length == len(dtr)
        assert dtr.step == step


@pytest.mark.parametrize('start, length, step, exp_stop', [
    (date(2016, 1, 1), 5, timedelta(days=1), date(2016, 1, 6)),
    (date(2016, 1, 1), 5, timedelta(days=-1), date(2015, 12, 27)),
    (time(23, 50), 5, timedelta(minutes=10), time(0, 40)),
    (time(23, 55), 5, timedelta(minutes=1), time(0, 0)),
    (time(0, 5), 5, timedelta(minutes=-1), time(0, 0)),
    (time(0, 5), 6, timedelta(minutes=-1), time(23, 59)),
    (datetime(2016, 1, 1, 22, 0, 0), 5, timedelta(hours=1),
     datetime(2016, 1, 2, 3, 0, 0))
])
def test_dateortimerange_stop_value_is_correct(start, length, step, exp_stop):
    assert dtrange.DateOrTimeRange(start, length, step).stop == exp_stop


@pytest.mark.parametrize('start, length, step, expected', [
    (date(2016, 1, 1), 6, timedelta(days=1),
     [date(2016, 1, 1), date(2016, 1, 2), date(2016, 1, 3), date(2016, 1, 4),
      date(2016, 1, 5), date(2016, 1, 6)]),
    (date(2016, 1, 1), 3, timedelta(days=2),
     [date(2016, 1, 1), date(2016, 1, 3), date(2016, 1, 5)]),
    (date(2016, 1, 1), 3, timedelta(days=-1),
     [date(2016, 1, 1), date(2015, 12, 31), date(2015, 12, 30)]),
    (time(10, 0), 5, timedelta(seconds=1),
     [time(10, 0), time(10, 0, 1), time(10, 0, 2), time(10, 0, 3),
      time(10, 0, 4)]),
    (time(10, 0), 5, timedelta(minutes=1),
     [time(10, 0), time(10, 1), time(10, 2), time(10, 3), time(10, 4)]),
    (time(23, 40), 5, timedelta(minutes=10),
     [time(23, 40), time(23, 50), time(0, 0), time(0, 10), time(0, 20)]),
    (time(0, 15), 5, timedelta(minutes=-5),
     [time(0, 15), time(0, 10), time(0, 5), time(0, 0), time(23, 55)]),
    (datetime(2016, 1, 1, 10, 0, 0), 6, timedelta(days=1),
     [datetime(2016, 1, 1, 10, 0, 0), datetime(2016, 1, 2, 10, 0, 0),
      datetime(2016, 1, 3, 10, 0, 0), datetime(2016, 1, 4, 10, 0, 0),
      datetime(2016, 1, 5, 10, 0, 0), datetime(2016, 1, 6, 10, 0, 0)]),
    (datetime(2016, 1, 1, 0, 0, 0), 3, timedelta(hours=12),
     [datetime(2016, 1, 1, 0, 0, 0), datetime(2016, 1, 1, 12, 0, 0),
      datetime(2016, 1, 2, 0, 0, 0)]),
    (datetime(2016, 1, 1, 0, 0, 0), 4, timedelta(seconds=-5),
     [datetime(2016, 1, 1, 0, 0, 0), datetime(2015, 12, 31, 23, 59, 55),
      datetime(2015, 12, 31, 23, 59, 50), datetime(2015, 12, 31, 23, 59, 45)]),
    (datetime(2016, 1, 1, 12, 0, 0), 4, timedelta(days=1.5),
     [datetime(2016, 1, 1, 12, 0, 0), datetime(2016, 1, 3, 0, 0, 0),
      datetime(2016, 1, 4, 12, 0, 0), datetime(2016, 1, 6, 0, 0, 0)]),
])
def test_dateortimerange_items_as_list(start, length, step, expected):
    assert list(dtrange.DateOrTimeRange(start, length, step)) == expected


@pytest.mark.parametrize('start, length, step, index, expected', [
    (date(2016, 1, 1), 6, timedelta(days=1), 0, date(2016, 1, 1)),
    (date(2016, 1, 1), 6, timedelta(days=1), -1, date(2016, 1, 6)),
    (date(2016, 1, 1), 6, timedelta(days=1), 2, date(2016, 1, 3)),
    (date(2016, 1, 1), 6, timedelta(days=2), -1, date(2016, 1, 11)),
    (date(2016, 1, 1), 6, timedelta(days=-1), 0, date(2016, 1, 1)),
    (date(2016, 1, 1), 6, timedelta(days=-1), -1, date(2015, 12, 27)),
    (date(2016, 1, 1), 6, timedelta(days=-1), 5, date(2015, 12, 27)),
    (date(2016, 1, 1), 6, timedelta(days=-1), 6, None),
    (date(2016, 1, 1), 6, timedelta(days=1), slice(0, 3),
     [date(2016, 1, 1), date(2016, 1, 2), date(2016, 1, 3)]),
    (date(2016, 1, 1), 6, timedelta(days=1), slice(1, 4),
     [date(2016, 1, 2), date(2016, 1, 3), date(2016, 1, 4)]),
    (date(2016, 1, 1), 6, timedelta(days=1), slice(1, 1), []),
    (date(2016, 1, 1), 6, timedelta(days=1), slice(7, 7), []),
    (date(2016, 1, 1), 6, timedelta(days=1), slice(3, 1), []),
    (date(2016, 1, 1), 6, timedelta(days=1), slice(None, None, -1),
     [date(2016, 1, 6), date(2016, 1, 5), date(2016, 1, 4), date(2016, 1, 3),
      date(2016, 1, 2), date(2016, 1, 1)]),
    (date(2016, 1, 1), 6, timedelta(days=1), slice(3, None, -1),
     [date(2016, 1, 4), date(2016, 1, 3), date(2016, 1, 2), date(2016, 1, 1)]),
    (date(2016, 1, 1), 6, timedelta(days=1), slice(None, 2, -1),
     [date(2016, 1, 6), date(2016, 1, 5), date(2016, 1, 4)]),
    (date(2016, 1, 1), 6, timedelta(days=1), slice(None, None, -2),
     [date(2016, 1, 6), date(2016, 1, 4), date(2016, 1, 2)]),
    (date(2016, 1, 1), 6, timedelta(days=2), slice(None, None, 4),
     [date(2016, 1, 1), date(2016, 1, 9)]),
])
def test_dateortimerange_getitem_by_index(start, length, step, index,
                                          expected):
    dtr = dtrange.DateOrTimeRange(start, length, step)
    if expected is None:
        with pytest.raises(IndexError):
            dtr[index]
    elif isinstance(index, slice):
        assert list(dtr[index]) == expected
    else:
        assert dtr[index] == expected


@pytest.mark.parametrize('start, length, step, expected', [
    (date(2016, 1, 1), 6, timedelta(days=1),
     'DateOrTimeRange("2016-01-01", "2016-01-07", step="1 day, 0:00:00")'),
    (time(0, 0), 86399, timedelta(seconds=1),
     'DateOrTimeRange("00:00:00", "23:59:59", step="0:00:01")'),
    (time(0, 0), 86400, timedelta(seconds=1),
     'DateOrTimeRange("00:00:00", "1 day + 00:00:00", step="0:00:01")'),
    (time(0, 0), 86400 * 2, timedelta(seconds=1),
     'DateOrTimeRange("00:00:00", "2 days + 00:00:00", step="0:00:01")'),
    (time(0, 0), 1441, timedelta(minutes=1),
     'DateOrTimeRange("00:00:00", "1 day + 00:01:00", step="0:01:00")'),
])
def test_dateortimerange_string_representation(start, length, step, expected):
    assert str(dtrange.DateOrTimeRange(start, length, step)) == expected


@pytest.mark.parametrize('range_one, range_two, expected', [
    (dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=1)),
     dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=1)), True),
    (dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=1)),
     dtrange.DateOrTimeRange(date(2016, 1, 1), 5, timedelta(days=1)), False),
    (dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=1)),
     dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=-1)), False),
    (dtrange.DateOrTimeRange(date(2016, 1, 2), 6, timedelta(days=1)),
     dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=-1)), False),
    (dtrange.DateOrTimeRange(datetime(2016, 1, 1), 6, timedelta(days=1)),
     dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=1)), False),
    (dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=2)),
     dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=2)), True),
    (dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=2)),
     dtrange.DateOrTimeRange(time(0, 0), 6, timedelta(minutes=1)), False),
    (dtrange.DateOrTimeRange(datetime(2016, 1, 1, 8, 0), 6, timedelta(days=1)),
     dtrange.DateOrTimeRange(date(2016, 1, 1), 6, timedelta(days=1)), False),
])
def test_dateortimerange_equality_and_hash(range_one, range_two, expected):
    assert (range_one == range_two) == expected
    assert (list(range_one) == list(range_two)) == expected
    assert (hash(range_one) == hash(range_two)) == expected


@pytest.mark.parametrize('start, length, step, search_val, expected', [
    (date(2016, 1, 1), 6, timedelta(days=1), date(2016, 1, 1), 0),
    (date(2016, 1, 1), 6, timedelta(days=1), date(2016, 1, 6), 5),
    (date(2016, 1, 1), 6, timedelta(days=1), date(2016, 1, 7), None),
    (date(2016, 1, 1), 6, timedelta(days=1), date(2015, 12, 31), None),
    (date(2016, 1, 1), 6, timedelta(days=2), date(2016, 1, 3), 1),
    (date(2016, 1, 1), 6, timedelta(days=2), date(2016, 1, 2), None),
    (time(8, 0), 5, timedelta(hours=1), time(10, 0), 2),
    (time(8, 0), 5, timedelta(hours=1), time(8, 30), None),
    (datetime(2016, 1, 1, 8, 0), 5, timedelta(hours=1), time(8, 30), None),
    (datetime(2016, 1, 1, 8, 0), 5, timedelta(hours=1), date(2016, 1, 1),
     None),
    (datetime(2016, 1, 1, 8, 0), 5, timedelta(hours=1),
     datetime(2016, 1, 1, 9, 0), 1),
])
def test_dateortimerange_find_index_by_item(start, length, step, search_val,
                                            expected):
    dtr = dtrange.DateOrTimeRange(start, length, step)
    if expected is None:
        with pytest.raises(ValueError):
            dtr.index(search_val)
        assert search_val not in dtr
        assert dtr.count(search_val) == 0
    else:
        assert dtr.index(search_val) == expected
        assert search_val in dtr
        assert dtr.count(search_val) == 1


@pytest.mark.parametrize('start, stop, step, step_unit, exp_err_str', [
    ('2016/1/1', '2016/1/5', 1, 'days', "Cannot decipher 'start' argument"),
    ('2016-01-01', '2016/1/5', 1, 'days', "Cannot decipher 'stop' argument"),
    ((2016, 1, 1), '2016/1/5', 1, 'days', "Cannot decipher 'start' argument"),
    (date(2016, 1, 1), datetime(2016, 1, 3), 1, 'days',
     "arguments must be interpretable as the same datetime type"),
    ('2016-01-01', '04:00:00', 1, 'days',
     "arguments must be interpretable as the same datetime type"),
    (date(2016, 1, 1), date(2016, 1, 3), 1, 'day', "Invalid 'step_unit'"),
    (date(2016, 1, 1), date(2016, 1, 3), 1, 'month', "Invalid 'step_unit'"),
])
def test_dtrange_validation(start, stop, step, step_unit, exp_err_str):
    with pytest.raises(ValueError) as excinfo:
        dtrange.dtrange(start, stop, step, step_unit)
    assert exp_err_str in str(excinfo.value)


@pytest.mark.parametrize('start, stop, step, step_unit, expected', [
    ('2016-01-01', '2016-01-06', 1, None,
     [date(2016, 1, 1), date(2016, 1, 2), date(2016, 1, 3), date(2016, 1, 4),
      date(2016, 1, 5)]),
    ('2016-01-05', '2015-12-31', -1, None,
     [date(2016, 1, 5), date(2016, 1, 4), date(2016, 1, 3), date(2016, 1, 2),
      date(2016, 1, 1)]),
    (date(2016, 1, 1), date(2016, 1, 6), 2, 'days',
     [date(2016, 1, 1), date(2016, 1, 3), date(2016, 1, 5)]),
    (date(2016, 1, 1), date(2016, 1, 5), 2, 'days',
     [date(2016, 1, 1), date(2016, 1, 3)]),
    (time(10, 30, 0), time(10, 30, 6), 1, None,
     [time(10, 30, 0), time(10, 30, 1), time(10, 30, 2), time(10, 30, 3),
      time(10, 30, 4), time(10, 30, 5)]),
    (time(23, 0), time(3, 0), 1, 'hours',
     [time(23, 0), time(0, 0), time(1, 0), time(2, 0)]),
    ('03:00', '22:00', -1, 'hours',
     [time(3, 0), time(2, 0), time(1, 0), time(0, 0), time(23, 0)]),
    (datetime(2016, 1, 1, 0, 0, 0), datetime(2016, 1, 3, 0, 0, 0), 12, 'hours',
     [datetime(2016, 1, 1, 0, 0, 0), datetime(2016, 1, 1, 12, 0, 0),
      datetime(2016, 1, 2, 0, 0, 0), datetime(2016, 1, 2, 12, 0, 0)]),
    ('2015-12-31T23:59:58', '2016-01-01T00:00:02', 1, None,
     [datetime(2015, 12, 31, 23, 59, 58), datetime(2015, 12, 31, 23, 59, 59),
      datetime(2016, 1, 1, 0, 0, 0), datetime(2016, 1, 1, 0, 0, 1)]),
])
def test_dtrange_return_value(start, stop, step, step_unit, expected):
    dtr = dtrange.dtrange(start, stop, step, step_unit)
    assert list(dtr) == expected


@pytest.mark.parametrize('start, stop, step, step_unit, exp_length', [
    (time(0, 0), time(0, 0), 1, None, 86400),
    (time(1, 0), time(1, 0), 1, None, 86400),
    (time(0, 0), time(0, 0), 1, 'hours', 24),
    (time(0, 0), time(0, 1), 1, 'minutes', 1),
    (date(2016, 1, 1), date(2016, 1, 1), 1, None, 0),
    (datetime(2016, 1, 1, 0, 0), datetime(2016, 1, 1, 0, 0), 1, None, 0),
])
def test_dtrange_start_equals_stop(start, stop, step, step_unit, exp_length):
    """A time range where start == stop should include the full clock.

    `dtrange` generally functions like `range` as much as possible,
    such as the fact that the range 'stop' value is excluded. This
    works, except for the edge case where you need to represent a full
    24 hour range with `time` objects. To do this you would need, e.g.,
    time(0, 0) to time(24, 0) -- but the latter is invalid. As a
    workaround, this is how we interpret a range of time(0, 0) to
    time(0, 0), instead of an empty range.
    """
    dtr = dtrange.dtrange(start, stop, step, step_unit)
    assert len(dtr) == exp_length
