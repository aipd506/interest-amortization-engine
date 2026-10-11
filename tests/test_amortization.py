"""Unit tests for loan amortization calculations and APR/APY solvers."""

from decimal import Decimal
import pytest
from interest_amortization_engine.models import AmortizationMethod
from interest_amortization_engine.amortization import (
    calculate_payment,
    calculate_apr,
    calculate_apy,
    generate_schedule,
)


def test_standard_30yr_payment():
    # $300,000 at 6.0% for 360 months
    # Standard formula yields: 1,798.6515...
    pmt = calculate_payment(
        principal=Decimal("300000"),
        annual_rate=Decimal("0.06"),
        term_months=360,
    )
    assert abs(pmt - Decimal("1798.65")) < Decimal("0.01")


def test_generate_schedule_balance_zero():
    schedule = generate_schedule(
        principal=Decimal("100000"),
        annual_rate=Decimal("0.05"),
        term_months=120,
        method=AmortizationMethod.FIXED_PAYMENT,
    )
    assert len(schedule.rows) == 120
    # Ending balance must be exactly zero at maturity
    assert schedule.rows[-1].ending_balance == Decimal("0.00")
    assert schedule.total_payments > schedule.principal
    assert schedule.total_interest == schedule.total_payments - schedule.principal


def test_fixed_principal_amortization():
    schedule = generate_schedule(
        principal=Decimal("120000"),
        annual_rate=Decimal("0.06"),
        term_months=12,
        method=AmortizationMethod.FIXED_PRINCIPAL,
    )
    assert len(schedule.rows) == 12
    # Each month principal should be 120,000 / 12 = 10,000
    for r in schedule.rows:
        assert r.principal_portion == Decimal("10000.00")
    assert schedule.rows[-1].ending_balance == Decimal("0.00")


def test_interest_only_amortization():
    schedule = generate_schedule(
        principal=Decimal("100000"),
        annual_rate=Decimal("0.06"),
        term_months=12,
        method=AmortizationMethod.INTEREST_ONLY,
    )
    # Monthly interest = 100,000 * (0.06 / 12) = 500
    for r in schedule.rows[:-1]:
        assert r.principal_portion == Decimal("0.00")
        assert r.payment == Decimal("500.00")
    # Final month repays principal
    assert schedule.rows[-1].principal_portion == Decimal("100000.00")
    assert schedule.rows[-1].ending_balance == Decimal("0.00")


def test_balloon_amortization():
    schedule = generate_schedule(
        principal=Decimal("100000"),
        annual_rate=Decimal("0.06"),
        term_months=60,
        method=AmortizationMethod.BALLOON,
        balloon=Decimal("40000"),
    )
    assert schedule.rows[-1].ending_balance == Decimal("40000.00")


def test_regulation_z_apr():
    # Zero finance fees -> APR equals nominal rate
    apr_zero = calculate_apr(
        loan_amount=Decimal("200000"),
        finance_charges=Decimal("0"),
        monthly_payment=Decimal("1199.10"),
        term_months=360,
    )
    assert abs(apr_zero - Decimal("0.06")) < Decimal("0.0005")

    # With prepaid points ($5,000) -> APR must exceed nominal
    apr_points = calculate_apr(
        loan_amount=Decimal("200000"),
        finance_charges=Decimal("5000"),
        monthly_payment=Decimal("1199.10"),
        term_months=360,
    )
    assert apr_points > apr_zero
    assert apr_points > Decimal("0.0620")


def test_apy_compounding():
    # 5.0% compounded monthly
    # APY = (1 + 0.05/12)^12 - 1 = 0.0511618...
    apy = calculate_apy(Decimal("0.05"), compounding_frequency=12)
    assert abs(apy - Decimal("0.05116")) < Decimal("0.0001")
