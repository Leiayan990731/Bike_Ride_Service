import datetime as dt
import math


UNLOCK_FEE = 5
FREE_SECONDS = 15 * 60
PER_BLOCK_SECONDS = 5 * 60
PER_BLOCK_PRICE = 1
DAILY_CAP = 25


def calculate_ride_cost(started_at: dt.datetime, ended_at: dt.datetime) -> float:
    """
    Pricing rules:
    - Unlock fee: HKD 5
    - First 15 minutes: free
    - After 15 minutes: HKD 1 per 5 minutes (ceil to next 5-min block)
    - Daily cap: HKD 25
    """
    if ended_at < started_at:
        raise ValueError("ended_at must be >= started_at")

    total_seconds = int((ended_at - started_at).total_seconds())
    billable_seconds = max(0, total_seconds - FREE_SECONDS)

    if billable_seconds <= 0:
        usage_cost = 0
    else:
        blocks = int(math.ceil(billable_seconds / float(PER_BLOCK_SECONDS)))
        usage_cost = blocks * PER_BLOCK_PRICE

    raw_cost = UNLOCK_FEE + usage_cost
    return round(float(min(DAILY_CAP, raw_cost)), 2)


def calculate_duration_seconds(started_at: dt.datetime, ended_at: dt.datetime) -> int:
    if ended_at < started_at:
        raise ValueError("ended_at must be >= started_at")
    return int((ended_at - started_at).total_seconds())

