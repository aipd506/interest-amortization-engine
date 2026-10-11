"""Actuarial day-count conventions and year fraction calculators."""

import calendar
from datetime import date
from decimal import Decimal
from typing import Union
from .models import DayCountConvention


def parse_date(d: Union[str, date]) -> date:
    """Parse string YYYY-MM-DD or return date object."""
    if isinstance(d, date):
        return d
    return date.fromisoformat(str(d).strip())


def is_leap_year(year: int) -> bool:
    return calendar.isleap(year)


def day_count_30_360_us(d1: date, d2: date) -> int:
    """Calculate day count under 30/360 US (NASD / Bond Basis)."""
    y1, m1, day1 = d1.year, d1.month, d1.day
    y2, m2, day2 = d2.year, d2.month, d2.day

    if day1 == 31:
        day1 = 30
    if day2 == 31 and day1 >= 30:
        day2 = 30

    return 360 * (y2 - y1) + 30 * (m2 - m1) + (day2 - day1)


def day_count_30e_360(d1: date, d2: date) -> int:
    """Calculate day count under 30E/360 (Eurobond Basis / ISMA-30/360)."""
    y1, m1, day1 = d1.year, d1.month, d1.day
    y2, m2, day2 = d2.year, d2.month, d2.day

    if day1 == 31:
        day1 = 30
    if day2 == 31:
        day2 = 30

    return 360 * (y2 - y1) + 30 * (m2 - m1) + (day2 - day1)


def year_fraction(
    start_date: Union[str, date],
    end_date: Union[str, date],
    convention: DayCountConvention = DayCountConvention.THIRTY_360_US,
) -> Decimal:
    """
    Compute the actuarial year fraction between two dates according to standard market convention.
    """
    d1 = parse_date(start_date)
    d2 = parse_date(end_date)

    if d1 > d2:
        raise ValueError(f"Start date {d1} cannot be after end date {d2}")
    if d1 == d2:
        return Decimal("0")

    if convention == DayCountConvention.THIRTY_360_US:
        days = day_count_30_360_us(d1, d2)
        return Decimal(days) / Decimal("360")

    elif convention == DayCountConvention.THIRTY_E_360:
        days = day_count_30e_360(d1, d2)
        return Decimal(days) / Decimal("360")

    elif convention == DayCountConvention.ACTUAL_360:
        days = (d2 - d1).days
        return Decimal(days) / Decimal("360")

    elif convention == DayCountConvention.ACTUAL_365_FIXED:
        days = (d2 - d1).days
        return Decimal(days) / Decimal("365")

    elif convention == DayCountConvention.ACTUAL_ACTUAL:
        # ISDA Actual/Actual convention
        if d1.year == d2.year:
            days_in_year = 366 if is_leap_year(d1.year) else 365
            return Decimal((d2 - d1).days) / Decimal(days_in_year)
        else:
            # Portion in year 1
            end_of_year_1 = date(d1.year, 12, 31)
            days_year_1 = (end_of_year_1 - d1).days + 1
            basis_year_1 = 366 if is_leap_year(d1.year) else 365
            frac = Decimal(days_year_1) / Decimal(basis_year_1)

            # Intermediate full years
            for y in range(d1.year + 1, d2.year):
                frac += Decimal("1")

            # Portion in year 2
            start_of_year_2 = date(d2.year, 1, 1)
            days_year_2 = (d2 - start_of_year_2).days
            basis_year_2 = 366 if is_leap_year(d2.year) else 365
            frac += Decimal(days_year_2) / Decimal(basis_year_2)
            return frac

    raise ValueError(f"Unsupported day count convention: {convention}")
