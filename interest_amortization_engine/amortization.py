"""Actuarial amortization engine, APR solver (Regulation Z), and APY calculator."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from .models import AmortizationMethod, AmortizationRow, AmortizationSchedule


def quantize_currency(val: Decimal) -> Decimal:
    """Quantize to 2 decimal places using standard financial round-half-up."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_payment(
    principal: Decimal,
    annual_rate: Decimal,
    term_months: int,
    balloon: Decimal = Decimal("0"),
) -> Decimal:
    """
    Calculate periodic fixed payment (PMT) for loan with optional balloon balance.
    """
    if term_months <= 0:
        raise ValueError("Term in months must be strictly positive")
    if principal <= Decimal("0"):
        raise ValueError("Principal must be strictly positive")

    r = annual_rate / Decimal("12")
    if r == Decimal("0"):
        return (principal - balloon) / Decimal(term_months)

    # PMT = r * [P * (1 + r)^n - B] / [(1 + r)^n - 1]
    compound = (Decimal("1") + r) ** term_months
    numerator = r * (principal * compound - balloon)
    denominator = compound - Decimal("1")

    return numerator / denominator


def calculate_apr(
    loan_amount: Decimal,
    finance_charges: Decimal,
    monthly_payment: Decimal,
    term_months: int,
    balloon: Decimal = Decimal("0"),
    tolerance: Decimal = Decimal("1e-9"),
    max_iterations: int = 100,
) -> Decimal:
    """
    Actuarial solver for Regulation Z Annual Percentage Rate (APR).
    Finds periodic internal rate of return (IRR) via Newton-Raphson.
    """
    net_proceeds = loan_amount - finance_charges
    if net_proceeds <= Decimal("0"):
        raise ValueError("Finance charges cannot equal or exceed loan amount")

    # Initial guess: nominal rate based on payment
    total_paid = monthly_payment * Decimal(term_months) + balloon
    rate_guess = ((total_paid / net_proceeds) - Decimal("1")) / Decimal(term_months)
    if rate_guess <= Decimal("0"):
        rate_guess = Decimal("0.005")

    i = rate_guess

    for _ in range(max_iterations):
        # f(i) = sum(PMT / (1+i)^t) + B / (1+i)^n - net_proceeds
        # f'(i) = -sum(t * PMT / (1+i)^(t+1)) - n * B / (1+i)^(n+1)
        pv = Decimal("0")
        dpv = Decimal("0")

        for t in range(1, term_months + 1):
            discount = (Decimal("1") + i) ** t
            pv += monthly_payment / discount
            dpv -= (Decimal(t) * monthly_payment) / ((Decimal("1") + i) ** (t + 1))

        if balloon > Decimal("0"):
            discount_n = (Decimal("1") + i) ** term_months
            pv += balloon / discount_n
            dpv -= (Decimal(term_months) * balloon) / ((Decimal("1") + i) ** (term_months + 1))

        f_val = pv - net_proceeds
        if abs(f_val) < tolerance or abs(dpv) < tolerance:
            break

        i_next = i - (f_val / dpv)
        if i_next <= Decimal("-0.99"):
            i = i / Decimal("2")
        else:
            if abs(i_next - i) < tolerance:
                i = i_next
                break
            i = i_next

    apr = i * Decimal("12")
    return apr


def calculate_apy(nominal_rate: Decimal, compounding_frequency: int = 12) -> Decimal:
    """Calculate Annual Percentage Yield (APY) given compounding frequency."""
    r = nominal_rate / Decimal(compounding_frequency)
    return ((Decimal("1") + r) ** compounding_frequency) - Decimal("1")


def generate_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    term_months: int,
    method: AmortizationMethod = AmortizationMethod.FIXED_PAYMENT,
    balloon: Decimal = Decimal("0"),
    start_date: Optional[date] = None,
    finance_charges: Decimal = Decimal("0"),
) -> AmortizationSchedule:
    """Generate detailed monthly amortization schedule with precise actuarial balance reconciliation."""
    if start_date is None:
        start_date = date.today()

    r = annual_rate / Decimal("12")
    p = principal
    rows: List[AmortizationRow] = []

    if method == AmortizationMethod.FIXED_PAYMENT:
        raw_pmt = calculate_payment(principal, annual_rate, term_months, balloon=balloon)
        pmt = quantize_currency(raw_pmt)
    elif method == AmortizationMethod.FIXED_PRINCIPAL:
        fixed_princ = quantize_currency((principal - balloon) / Decimal(term_months))
        pmt = fixed_princ + quantize_currency(p * r)
    elif method == AmortizationMethod.INTEREST_ONLY:
        pmt = quantize_currency(principal * r)
    elif method == AmortizationMethod.BALLOON:
        raw_pmt = calculate_payment(principal, annual_rate, term_months, balloon=balloon)
        pmt = quantize_currency(raw_pmt)
    else:
        raise ValueError(f"Unsupported method {method}")

    curr_balance = p
    cum_interest = Decimal("0")
    cum_principal = Decimal("0")

    curr_year = start_date.year
    curr_month = start_date.month

    for period in range(1, term_months + 1):
        # Advance payment date by 1 month
        curr_month += 1
        if curr_month > 12:
            curr_month = 1
            curr_year += 1
        pay_date = date(curr_year, curr_month, min(start_date.day, 28)).isoformat()

        interest_due = quantize_currency(curr_balance * r)

        if method == AmortizationMethod.INTEREST_ONLY:
            if period == term_months:
                principal_due = curr_balance
                total_due = principal_due + interest_due
            else:
                principal_due = Decimal("0")
                total_due = interest_due

        elif method == AmortizationMethod.FIXED_PRINCIPAL:
            if period == term_months:
                principal_due = curr_balance - balloon
            else:
                principal_due = fixed_princ
            total_due = principal_due + interest_due

        else:
            # Fixed payment / Balloon
            if period == term_months:
                # Adjust final payment to clear residual rounding
                principal_due = curr_balance - balloon
                total_due = principal_due + interest_due
            else:
                total_due = pmt
                principal_due = total_due - interest_due
                if principal_due > curr_balance:
                    principal_due = curr_balance
                    total_due = principal_due + interest_due

        end_balance = curr_balance - principal_due
        cum_interest += interest_due
        cum_principal += principal_due

        rows.append(
            AmortizationRow(
                period=period,
                payment_date=pay_date,
                beginning_balance=curr_balance,
                payment=total_due,
                principal_portion=principal_due,
                interest_portion=interest_due,
                ending_balance=end_balance,
                cumulative_interest=cum_interest,
                cumulative_principal=cum_principal,
            )
        )
        curr_balance = end_balance

    total_payments = sum(r.payment for r in rows)
    if balloon > Decimal("0"):
        total_payments += balloon

    # Calculate APR if finance charges are specified or equal to nominal if 0
    if finance_charges > Decimal("0"):
        apr = calculate_apr(principal, finance_charges, pmt, term_months, balloon=balloon)
    else:
        apr = annual_rate

    apy = calculate_apy(annual_rate, compounding_frequency=12)

    return AmortizationSchedule(
        principal=principal,
        annual_rate=annual_rate,
        term_months=term_months,
        method=method,
        regular_payment=pmt,
        total_payments=total_payments,
        total_interest=cum_interest,
        balloon_amount=balloon,
        apr=apr,
        apy=apy,
        rows=rows,
    )
