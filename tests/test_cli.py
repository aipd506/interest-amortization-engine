"""Unit tests for amortize CLI commands."""

import tempfile
import os
from interest_amortization_engine.cli import main


def test_cli_schedule(capsys):
    ret = main(["schedule", "--principal", "250000", "--rate", "0.065", "--months", "180"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "ACTUARIAL AMORTIZATION SCHEDULE" in captured.out
    assert "Regular Payment:" in captured.out


def test_cli_schedule_export_csv(capsys):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as tmp:
        csv_path = tmp.name

    try:
        ret = main(["schedule", "--principal", "100000", "--rate", "0.05", "--months", "24", "--export-csv", csv_path])
        assert ret == 0
        captured = capsys.readouterr()
        assert "Exported complete 24-row" in captured.out
        with open(csv_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 25  # header + 24 rows
    finally:
        os.remove(csv_path)


def test_cli_apr(capsys):
    ret = main(["apr", "--amount", "300000", "--nominal-rate", "0.065", "--months", "360", "--points", "3000", "--fees", "1500"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "REGULATION Z" in captured.out
    assert "ANNUAL PERCENTAGE RATE:" in captured.out


def test_cli_daycount(capsys):
    ret = main(["daycount", "--start", "2026-01-01", "--end", "2026-07-01", "--convention", "30_360_US"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "INTEREST DAY-COUNT CALCULATION" in captured.out
    assert "0.50000000 years" in captured.out


def test_cli_apy(capsys):
    ret = main(["apy", "--rate", "0.05", "--compounding", "12"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "REGULATION DD" in captured.out
    assert "5.1162% APY" in captured.out or "5.116" in captured.out
