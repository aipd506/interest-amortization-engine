"""Unit tests for actuarial day count conventions."""

from datetime import date
from decimal import Decimal
import pytest
from interest_amortization_engine.daycount import (
    day_count_30_360_us,
    day_count_30e_360,
    year_fraction,
    DayCountConvention,
)


def test_30_360_us_standard():
    d1 = date(2026, 1, 1)
    d2 = date(2026, 7, 1)
    # Exactly 6 months = 180 days = 0.5 year
    days = day_count_30_360_us(d1, d2)
    assert days == 180
    frac = year_fraction(d1, d2, DayCountConvention.THIRTY_360_US)
    assert frac == Decimal("0.5")


def test_30_360_us_end_of_month_31():
    d1 = date(2026, 1, 31)
    d2 = date(2026, 3, 31)
    # Under US 30/360: D1=31 -> 30, D2=31 & D1>=30 -> 30.
    # Days = 360*0 + 30*2 + (30 - 30) = 60 days
    days = day_count_30_360_us(d1, d2)
    assert days == 60


def test_30e_360_eurobond():
    d1 = date(2026, 1, 31)
    d2 = date(2026, 2, 28)
    days = day_count_30e_360(d1, d2)
    assert days == 360 * 0 + 30 * 1 + (28 - 30)  # 28 days


def test_actual_360_and_actual_365():
    d1 = date(2026, 1, 1)
    d2 = date(2026, 4, 1)
    # Jan(31) + Feb(28) + Mar(31) = 90 days
    frac_360 = year_fraction(d1, d2, DayCountConvention.ACTUAL_360)
    assert frac_360 == Decimal("90") / Decimal("360")

    frac_365 = year_fraction(d1, d2, DayCountConvention.ACTUAL_365_FIXED)
    assert frac_365 == Decimal("90") / Decimal("365")


def test_actual_actual_isda():
    # Leap year 2024: 366 days
    d1 = date(2024, 1, 1)
    d2 = date(2024, 12, 31)
    frac = year_fraction(d1, d2, DayCountConvention.ACTUAL_ACTUAL)
    assert frac == Decimal("365") / Decimal("366")


def test_invalid_dates():
    with pytest.raises(ValueError, match="cannot be after"):
        year_fraction("2026-12-01", "2026-01-01")
