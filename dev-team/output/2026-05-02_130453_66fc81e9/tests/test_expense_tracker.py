from __future__ import annotations

import csv
import json

import pytest
from src.expense_tracker import ExpenseError, ExpenseTracker, main


def test_add_expense_records_and_persists(tmp_path):
    storage = tmp_path / "expenses.json"
    tracker = ExpenseTracker(storage)

    expense = tracker.add_expense("12.5", "Food", "2025-01-15", "lunch")

    assert expense.amount == "12.50"
    assert expense.category == "food"
    stored = json.loads(storage.read_text(encoding="utf-8"))
    assert len(stored) == 1
    assert stored[0]["amount"] == "12.50"
    assert stored[0]["category"] == "food"
    assert stored[0]["expense_date"] == "2025-01-15"
    assert stored[0]["note"] == "lunch"


def test_monthly_report_summarizes_total_and_categories(tmp_path):
    storage = tmp_path / "expenses.json"
    tracker = ExpenseTracker(storage)
    tracker.add_expense("10", "food", "2025-02-01")
    tracker.add_expense("15.25", "transport", "2025-02-10")
    tracker.add_expense("2.75", "food", "2025-02-20")
    tracker.add_expense("100", "food", "2025-03-01")

    report = tracker.monthly_report(2025, 2)

    assert report == {
        "year": 2025,
        "month": 2,
        "total": "28.00",
        "categories": {"food": "12.75", "transport": "15.25"},
        "count": 3,
    }


def test_export_csv_for_specified_period(tmp_path):
    storage = tmp_path / "expenses.json"
    output = tmp_path / "exports" / "jan.csv"
    tracker = ExpenseTracker(storage)
    tracker.add_expense("5", "food", "2025-01-02", "coffee")
    tracker.add_expense("9", "travel", "2025-01-31")
    tracker.add_expense("20", "shopping", "2025-02-01")

    count = tracker.export_csv("2025-01-01", "2025-01-31", output)

    assert count == 2
    with output.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert [row["date"] for row in rows] == ["2025-01-02", "2025-01-31"]
    assert rows[0]["category"] == "food"
    assert rows[0]["amount"] == "5.00"
    assert rows[0]["note"] == "coffee"


@pytest.mark.parametrize(
    ("amount", "category", "message"),
    [
        ("-1", "food", "Amount must be greater than zero"),
        ("0", "food", "Amount must be greater than zero"),
        ("abc", "food", "Amount must be a valid number"),
        ("10", "invalid", "Unsupported category"),
    ],
)
def test_invalid_add_inputs_do_not_record(tmp_path, amount, category, message):
    storage = tmp_path / "expenses.json"
    tracker = ExpenseTracker(storage)

    with pytest.raises(ExpenseError, match=message):
        tracker.add_expense(amount, category, "2025-01-01")

    assert not storage.exists()


def test_export_rejects_start_after_end(tmp_path):
    tracker = ExpenseTracker(tmp_path / "expenses.json")

    with pytest.raises(ExpenseError, match="Start date must be on or before end date"):
        tracker.export_csv("2025-02-01", "2025-01-01", tmp_path / "out.csv")


def test_cli_help_displays_usage(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.out
    assert "add" in captured.out
    assert "report" in captured.out
    assert "export" in captured.out


def test_cli_add_invalid_input_outputs_error(tmp_path, capsys):
    storage = tmp_path / "expenses.json"

    with pytest.raises(SystemExit) as exc_info:
        main(["--storage", str(storage), "add", "-3", "food"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Amount must be greater than zero" in captured.err
    assert not storage.exists()


def test_cli_report_output(tmp_path, capsys):
    storage = tmp_path / "expenses.json"
    tracker = ExpenseTracker(storage)
    tracker.add_expense("3.5", "food", "2025-04-02")

    exit_code = main(["--storage", str(storage), "report", "2025", "4"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Monthly Expense Report: 2025-04" in captured.out
    assert "Total: 3.50" in captured.out
    assert "food: 3.50" in captured.out
