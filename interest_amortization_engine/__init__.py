"""Actuarial Loan Amortization, Day-Count Conventions, and APR/APY Engine."""

from .models import (
    DayCountConvention,
    AmortizationMethod,
    AmortizationRow,
    AmortizationSchedule,
)
from .daycount import year_fraction, parse_date
from .amortization import (
    calculate_payment,
    calculate_apr,
    calculate_apy,
    generate_schedule,
)

__version__ = "0.1.0"
__all__ = [
    "DayCountConvention",
    "AmortizationMethod",
    "AmortizationRow",
    "AmortizationSchedule",
    "year_fraction",
    "parse_date",
    "calculate_payment",
    "calculate_apr",
    "calculate_apy",
    "generate_schedule",
]
