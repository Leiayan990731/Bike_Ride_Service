import datetime as dt

import pytest

from app.services.pricing import calculate_ride_cost


def test_unlock_fee_only_under_15_min():
    start = dt.datetime(2026, 1, 1, 0, 0, 0)
    end = start + dt.timedelta(minutes=10)
    assert calculate_ride_cost(start, end) == 5.00


def test_exactly_15_min_still_free_usage():
    start = dt.datetime(2026, 1, 1, 0, 0, 0)
    end = start + dt.timedelta(minutes=15)
    assert calculate_ride_cost(start, end) == 5.00


def test_15_min_plus_1_second_bills_one_block():
    start = dt.datetime(2026, 1, 1, 0, 0, 0)
    end = start + dt.timedelta(minutes=15, seconds=1)
    assert calculate_ride_cost(start, end) == 6.00


def test_15_min_plus_5_min_bills_one_block():
    start = dt.datetime(2026, 1, 1, 0, 0, 0)
    end = start + dt.timedelta(minutes=20)
    assert calculate_ride_cost(start, end) == 6.00


def test_ceil_to_next_5_min_block():
    start = dt.datetime(2026, 1, 1, 0, 0, 0)
    end = start + dt.timedelta(minutes=21)
    # 6 minutes billable -> 2 blocks -> HKD 2 + unlock HKD 5
    assert calculate_ride_cost(start, end) == 7.00


def test_daily_cap():
    start = dt.datetime(2026, 1, 1, 0, 0, 0)
    end = start + dt.timedelta(hours=24)
    assert calculate_ride_cost(start, end) == 25.00


def test_invalid_time_raises():
    start = dt.datetime(2026, 1, 1, 0, 0, 0)
    end = start - dt.timedelta(seconds=1)
    with pytest.raises(ValueError):
        calculate_ride_cost(start, end)

