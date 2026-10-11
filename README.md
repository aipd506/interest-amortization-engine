# interest-amortization-engine

Actuarial Loan Amortization, Day-Count Conventions, and APR/APY Engine.

`interest-amortization-engine` provides institutional-grade loan amortization calculation, international bond/money-market day-count conventions, and consumer credit regulatory disclosures (Truth in Lending Act / Regulation Z APR, Truth in Savings / Regulation DD APY).

Built exclusively with zero external dependencies using the Python standard library.

## Key Capabilities

1. Multiple Amortization Structures: Fixed payment annuity (French amortization), fixed principal (German amortization), interest-only loans, and maturity balloon balances.
2. Market Day-Count Conventions: Comprehensive implementation of `30/360 US` (Bond Basis), `30E/360` (Eurobond), `Actual/360`, `Actual/365 Fixed`, and `Actual/Actual ISDA`.
3. Regulation Z APR Solver: Newton-Raphson internal rate of return (IRR) solver computing true actuarial Annual Percentage Rate accounting for points and prepaid finance charges.
4. Regulation DD APY Compounding: Exact effective yield determination across arbitrary compounding frequencies.
5. High Financial Precision: Implements `decimal.Decimal` with banker's rounding (`ROUND_HALF_UP`) and final-period cent reconciliation to prevent balance drift.

## Installation

```bash
pip install .
```

## CLI Usage

### 1. Generate 30-Year Mortgage Amortization Schedule

```bash
amortize schedule --principal 400000 --rate 0.0675 --months 360
```

### 2. Export Full 360-Row Amortization Table to CSV

```bash
amortize schedule --principal 500000 --rate 0.0625 --months 360 --export-csv loan_schedule.csv
```

### 3. Calculate Actuarial APR with Origination Fees (Regulation Z)

```bash
amortize apr --amount 300000 --nominal-rate 0.065 --months 360 --points 6000 --fees 2500
```

### 4. Compute Bond / Money Market Day-Count Fraction

```bash
amortize daycount --start 2026-01-15 --end 2026-07-15 --convention ACTUAL_360
```

### 5. Calculate Truth in Savings APY

```bash
amortize apy --rate 0.0525 --compounding 12
```

## Python API Usage

```python
from decimal import Decimal
from interest_amortization_engine import generate_schedule, calculate_apr, year_fraction, DayCountConvention

# 1. Generate schedule
schedule = generate_schedule(
    principal=Decimal("350000"),
    annual_rate=Decimal("0.065"),
    term_months=360,
)
print(schedule.summary())

# 2. Compute year fraction under 30/360 US
frac = year_fraction("2026-01-01", "2026-07-01", convention=DayCountConvention.THIRTY_360_US)
print(f"Year fraction: {frac}")

# 3. Solve APR
apr = calculate_apr(
    loan_amount=Decimal("350000"),
    finance_charges=Decimal("8500"),
    monthly_payment=schedule.regular_payment,
    term_months=360,
)
print(f"Reg Z APR: {apr * Decimal('100'):.4f}%")
```

## License

MIT License. Open source for core banking, retail lending, and debt capital markets infrastructure.
