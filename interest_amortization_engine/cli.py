"""Command Line Interface for Interest Amortization Engine (amortize)."""

import argparse
import csv
import sys
from decimal import Decimal
from typing import List, Optional
from .models import AmortizationMethod, DayCountConvention
from .amortization import generate_schedule, calculate_apr, calculate_apy
from .daycount import year_fraction, parse_date


def handle_schedule(args: argparse.Namespace) -> int:
    principal = Decimal(str(args.principal))
    rate = Decimal(str(args.rate))
    balloon = Decimal(str(args.balloon))
    fees = Decimal(str(args.fees))
    method = AmortizationMethod(args.method)

    schedule = generate_schedule(
        principal=principal,
        annual_rate=rate,
        term_months=args.months,
        method=method,
        balloon=balloon,
        finance_charges=fees,
    )

    print("================================================================================")
    print("                      ACTUARIAL AMORTIZATION SCHEDULE                           ")
    print("================================================================================")
    print(schedule.summary())
    print("================================================================================\n")

    if args.export_csv:
        with open(args.export_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Period",
                "Date",
                "Beginning_Balance",
                "Payment",
                "Principal",
                "Interest",
                "Ending_Balance",
                "Cumulative_Interest",
                "Cumulative_Principal",
            ])
            for r in schedule.rows:
                writer.writerow([
                    r.period,
                    r.payment_date,
                    f"{r.beginning_balance:.2f}",
                    f"{r.payment:.2f}",
                    f"{r.principal_portion:.2f}",
                    f"{r.interest_portion:.2f}",
                    f"{r.ending_balance:.2f}",
                    f"{r.cumulative_interest:.2f}",
                    f"{r.cumulative_principal:.2f}",
                ])
        print(f"Exported complete {len(schedule.rows)}-row amortization schedule to {args.export_csv}\n")

    return 0


def handle_apr(args: argparse.Namespace) -> int:
    amount = Decimal(str(args.amount))
    nominal_rate = Decimal(str(args.nominal_rate))
    points = Decimal(str(args.points))
    fees = Decimal(str(args.fees))
    months = args.months
    balloon = Decimal(str(args.balloon))

    finance_charges = points + fees
    amount_financed = amount - finance_charges

    schedule = generate_schedule(
        principal=amount,
        annual_rate=nominal_rate,
        term_months=months,
        balloon=balloon,
    )

    apr = calculate_apr(
        loan_amount=amount,
        finance_charges=finance_charges,
        monthly_payment=schedule.regular_payment,
        term_months=months,
        balloon=balloon,
    )

    print("================================================================================")
    print("            TRUTH IN LENDING ACT (REGULATION Z) APR DISCLOSURE                  ")
    print("================================================================================")
    print(f"Gross Note Principal:     ${amount:,.2f}")
    print(f"Prepaid Finance Charges:  ${finance_charges:,.2f} (Points: ${points:,.2f}, Fees: ${fees:,.2f})")
    print(f"Amount Financed:          ${amount_financed:,.2f}")
    print(f"Contract Nominal Rate:    {nominal_rate * Decimal('100'):.4f}%")
    print(f"Monthly Payment (P&I):    ${schedule.regular_payment:,.2f} for {months} months")
    print(f"Total Finance Charges:    ${(schedule.total_interest + finance_charges):,.2f}")
    print(f"Total of Payments:        ${(schedule.total_payments + finance_charges):,.2f}")
    print("--------------------------------------------------------------------------------")
    print(f"ANNUAL PERCENTAGE RATE:   {apr * Decimal('100'):.4f}% APR")
    print("================================================================================\n")
    return 0


def handle_daycount(args: argparse.Namespace) -> int:
    convention = DayCountConvention(args.convention)
    d1 = parse_date(args.start)
    d2 = parse_date(args.end)
    frac = year_fraction(d1, d2, convention=convention)
    elapsed_days = (d2 - d1).days

    print("================================================================================")
    print("                       INTEREST DAY-COUNT CALCULATION                           ")
    print("================================================================================")
    print(f"Start Date:         {d1.isoformat()}")
    print(f"End Date:           {d2.isoformat()}")
    print(f"Calendar Days:      {elapsed_days} days")
    print(f"Convention:         {convention.value}")
    print(f"Actuarial Fraction: {frac:.8f} years")
    print("================================================================================\n")
    return 0


def handle_apy(args: argparse.Namespace) -> int:
    rate = Decimal(str(args.rate))
    compounding = args.compounding
    apy = calculate_apy(rate, compounding_frequency=compounding)

    print("================================================================================")
    print("             TRUTH IN SAVINGS (REGULATION DD) APY DISCLOSURE                   ")
    print("================================================================================")
    print(f"Nominal Annual Rate:     {rate * Decimal('100'):.4f}%")
    print(f"Compounding Frequency:   {compounding} times per year")
    print(f"Annual Percentage Yield: {apy * Decimal('100'):.4f}% APY")
    print("================================================================================\n")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="amortize",
        description="Actuarial Loan Amortization, Day-Count Conventions, and APR/APY Engine",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: schedule
    p_sched = subparsers.add_parser("schedule", help="Generate loan amortization schedule")
    p_sched.add_argument("--principal", type=float, required=True, help="Loan principal amount")
    p_sched.add_argument("--rate", type=float, required=True, help="Annual interest rate (e.g. 0.065 for 6.5%%)")
    p_sched.add_argument("--months", type=int, default=360, help="Loan term in months (default: 360)")
    p_sched.add_argument(
        "--method",
        choices=["FIXED_PAYMENT", "FIXED_PRINCIPAL", "INTEREST_ONLY", "BALLOON"],
        default="FIXED_PAYMENT",
        help="Amortization method",
    )
    p_sched.add_argument("--balloon", type=float, default=0.0, help="Balloon balance at maturity")
    p_sched.add_argument("--fees", type=float, default=0.0, help="Prepaid finance charges / points")
    p_sched.add_argument("--export-csv", help="Optional CSV file path to export full schedule")

    # Subcommand: apr
    p_apr = subparsers.add_parser("apr", help="Calculate Regulation Z Actuarial APR")
    p_apr.add_argument("--amount", type=float, required=True, help="Loan amount")
    p_apr.add_argument("--nominal-rate", type=float, required=True, help="Contract interest rate (e.g. 0.065)")
    p_apr.add_argument("--months", type=int, default=360, help="Loan term in months")
    p_apr.add_argument("--points", type=float, default=0.0, help="Origination points")
    p_apr.add_argument("--fees", type=float, default=0.0, help="Other prepaid finance fees")
    p_apr.add_argument("--balloon", type=float, default=0.0, help="Balloon balance at maturity")

    # Subcommand: daycount
    p_day = subparsers.add_parser("daycount", help="Calculate actuarial day count and year fraction")
    p_day.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    p_day.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    p_day.add_argument(
        "--convention",
        choices=["30_360_US", "30E_360", "ACTUAL_360", "ACTUAL_365", "ACTUAL_ACTUAL"],
        default="30_360_US",
        help="Market day count convention",
    )

    # Subcommand: apy
    p_apy = subparsers.add_parser("apy", help="Calculate Regulation DD APY")
    p_apy.add_argument("--rate", type=float, required=True, help="Nominal interest rate (e.g. 0.05)")
    p_apy.add_argument("--compounding", type=int, default=12, help="Compounding periods per year (default: 12)")

    args = parser.parse_args(argv)

    if args.command == "schedule":
        return handle_schedule(args)
    elif args.command == "apr":
        return handle_apr(args)
    elif args.command == "daycount":
        return handle_daycount(args)
    elif args.command == "apy":
        return handle_apy(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
