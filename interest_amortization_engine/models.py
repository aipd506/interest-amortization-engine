"""Data models for loan contracts, amortization schedules, and regulatory disclosures."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class DayCountConvention(str, Enum):
    THIRTY_360_US = "30_360_US"
    THIRTY_E_360 = "30E_360"
    ACTUAL_360 = "ACTUAL_360"
    ACTUAL_365_FIXED = "ACTUAL_365"
    ACTUAL_ACTUAL = "ACTUAL_ACTUAL"


class AmortizationMethod(str, Enum):
    FIXED_PAYMENT = "FIXED_PAYMENT"        # Standard annuity / French amortization
    FIXED_PRINCIPAL = "FIXED_PRINCIPAL"    # Constant principal / German amortization
    INTEREST_ONLY = "INTEREST_ONLY"        # Interest only with bullet principal at end
    BALLOON = "BALLOON"                    # Partial amortization with lump sum at end


@dataclass
class AmortizationRow:
    """Individual installment row within an amortization schedule."""
    period: int
    payment_date: str
    beginning_balance: Decimal
    payment: Decimal
    principal_portion: Decimal
    interest_portion: Decimal
    ending_balance: Decimal
    cumulative_interest: Decimal
    cumulative_principal: Decimal


@dataclass
class AmortizationSchedule:
    """Complete amortization schedule with actuarial metrics and regulatory disclosures."""
    principal: Decimal
    annual_rate: Decimal
    term_months: int
    method: AmortizationMethod
    regular_payment: Decimal
    total_payments: Decimal
    total_interest: Decimal
    balloon_amount: Decimal = Decimal("0")
    apr: Optional[Decimal] = None
    apy: Optional[Decimal] = None
    rows: List[AmortizationRow] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Loan Principal:     ${self.principal:,.2f}",
            f"Nominal Rate:       {self.annual_rate * Decimal('100'):.4f}% per annum",
            f"Loan Term:          {self.term_months} months ({self.term_months / 12:.1f} years)",
            f"Amortization Type:  {self.method.value}",
            f"Regular Payment:    ${self.regular_payment:,.2f} / month",
            f"Total Interest:     ${self.total_interest:,.2f}",
            f"Total Payments:     ${self.total_payments:,.2f}",
        ]
        if self.balloon_amount > Decimal("0"):
            lines.append(f"Balloon Balance:    ${self.balloon_amount:,.2f}")
        if self.apr is not None:
            lines.append(f"Actuarial APR:      {self.apr * Decimal('100'):.4f}% (Reg Z)")
        if self.apy is not None:
            lines.append(f"Effective APY:      {self.apy * Decimal('100'):.4f}% (Compounded)")

        lines.append("First 3 Installments:")
        for r in self.rows[:3]:
            lines.append(
                f"  Period {r.period:2d}: Pymt=${r.payment:,.2f} (Princ=${r.principal_portion:,.2f}, Int=${r.interest_portion:,.2f}) EndBal=${r.ending_balance:,.2f}"
            )
        if len(self.rows) > 3:
            lines.append(f"  ... [{len(self.rows) - 4} intermediate payments omitted] ...")
            last = self.rows[-1]
            lines.append(
                f"  Period {last.period:2d}: Pymt=${last.payment:,.2f} (Princ=${last.principal_portion:,.2f}, Int=${last.interest_portion:,.2f}) EndBal=${last.ending_balance:,.2f}"
            )
        return "\n".join(lines)
