"""Daily Expense Tracker CLI Tool.

Provides expense persistence, validation, monthly reporting, and CSV export.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Sequence
from uuid import uuid4

DEFAULT_CATEGORIES: tuple[str, ...] = (
    "food",
    "transport",
    "housing",
    "utilities",
    "healthcare",
    "entertainment",
    "education",
    "shopping",
    "travel",
    "other",
)

DATE_FORMAT = "%Y-%m-%d"


class ExpenseError(ValueError):
    """Raised for user-correctable expense tracker errors."""


@dataclass(frozen=True)
class Expense:
    """Expense record stored by the tracker."""

    id: str
    amount: str
    category: str
    expense_date: str
    note: str = ""

    @property
    def decimal_amount(self) -> Decimal:
        """Return the amount as a Decimal."""
        return Decimal(self.amount)


class ExpenseStore:
    """JSON-backed persistent storage for expenses."""

    def __init__(self, storage_path: str | Path) -> None:
        self.storage_path = Path(storage_path).expanduser()

    def load(self) -> list[Expense]:
        """Load all stored expenses.

        Returns an empty list if the storage file does not exist. Raises
        ExpenseError for malformed JSON or invalid records.
        """
        if not self.storage_path.exists():
            return []

        try:
            raw_data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ExpenseError(
                f"Storage file is not valid JSON: {self.storage_path}"
            ) from exc

        if not isinstance(raw_data, list):
            raise ExpenseError("Storage file must contain a JSON list of expenses.")

        expenses: list[Expense] = []
        for index, item in enumerate(raw_data, start=1):
            if not isinstance(item, dict):
                raise ExpenseError(f"Expense record #{index} is not an object.")
            try:
                expenses.append(
                    Expense(
                        id=str(item["id"]),
                        amount=str(item["amount"]),
                        category=str(item["category"]),
                        expense_date=str(item["expense_date"]),
                        note=str(item.get("note", "")),
                    )
                )
            except KeyError as exc:
                raise ExpenseError(
                    f"Expense record #{index} is missing field: {exc.args[0]}"
                ) from exc

        return expenses

    def save(self, expenses: Iterable[Expense]) -> None:
        """Persist expenses to disk as pretty-printed JSON."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(expense) for expense in expenses]
        self.storage_path.write_text(
            json.dumps(data, indent=2, sort_keys=True), encoding="utf-8"
        )

    def append(self, expense: Expense) -> None:
        """Append a single expense and persist the updated collection."""
        expenses = self.load()
        expenses.append(expense)
        self.save(expenses)


class ExpenseTracker:
    """Core expense operations independent of the command-line interface."""

    def __init__(
        self,
        storage_path: str | Path,
        categories: Sequence[str] = DEFAULT_CATEGORIES,
    ) -> None:
        normalized_categories = tuple(category.lower() for category in categories)
        if not normalized_categories:
            raise ValueError("At least one category is required.")
        self.categories = normalized_categories
        self.store = ExpenseStore(storage_path)

    def add_expense(
        self,
        amount: str | float | Decimal,
        category: str,
        expense_date: str | None = None,
        note: str = "",
    ) -> Expense:
        """Validate, create, and persist an expense."""
        normalized_amount = parse_amount(amount)
        normalized_category = self.validate_category(category)
        normalized_date = parse_date(expense_date) if expense_date else date.today()

        expense = Expense(
            id=str(uuid4()),
            amount=format_decimal(normalized_amount),
            category=normalized_category,
            expense_date=normalized_date.isoformat(),
            note=note.strip(),
        )
        self.store.append(expense)
        return expense

    def monthly_report(self, year: int, month: int) -> dict[str, Any]:
        """Generate a monthly report with total and per-category expenses."""
        validate_year_month(year, month)
        expenses = [
            expense
            for expense in self.store.load()
            if is_expense_in_month(expense, year, month)
        ]
        categorized: dict[str, Decimal] = {category: Decimal("0.00") for category in self.categories}
        total = Decimal("0.00")
        for expense in expenses:
            amount = expense.decimal_amount
            total += amount
            categorized[expense.category] = categorized.get(expense.category, Decimal("0.00")) + amount

        non_zero_categories = {
            category: format_decimal(amount)
            for category, amount in categorized.items()
            if amount != Decimal("0.00")
        }
        return {
            "year": year,
            "month": month,
            "total": format_decimal(total),
            "categories": non_zero_categories,
            "count": len(expenses),
        }

    def export_csv(
        self,
        start_date: str,
        end_date: str,
        output_path: str | Path,
    ) -> int:
        """Export expenses in the inclusive date range to a CSV file.

        Returns the number of exported expenses.
        """
        start = parse_date(start_date)
        end = parse_date(end_date)
        if start > end:
            raise ExpenseError("Start date must be on or before end date.")

        matching_expenses = [
            expense
            for expense in self.store.load()
            if start <= parse_date(expense.expense_date) <= end
        ]
        output = Path(output_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["id", "date", "category", "amount", "note"],
            )
            writer.writeheader()
            for expense in matching_expenses:
                writer.writerow(
                    {
                        "id": expense.id,
                        "date": expense.expense_date,
                        "category": expense.category,
                        "amount": expense.amount,
                        "note": expense.note,
                    }
                )
        return len(matching_expenses)

    def validate_category(self, category: str) -> str:
        """Return normalized category or raise ExpenseError."""
        normalized = category.strip().lower()
        if normalized not in self.categories:
            supported = ", ".join(self.categories)
            raise ExpenseError(
                f"Unsupported category '{category}'. Supported categories: {supported}."
            )
        return normalized


def default_storage_path() -> Path:
    """Return the default storage path for persisted expenses."""
    return Path.home() / ".expense_tracker" / "expenses.json"


def parse_amount(amount: str | float | Decimal) -> Decimal:
    """Parse and validate a positive expense amount."""
    try:
        decimal_amount = Decimal(str(amount)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError) as exc:
        raise ExpenseError("Amount must be a valid number.") from exc

    if decimal_amount <= Decimal("0.00"):
        raise ExpenseError("Amount must be greater than zero.")
    return decimal_amount


def parse_date(value: str) -> date:
    """Parse a YYYY-MM-DD date string."""
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except ValueError as exc:
        raise ExpenseError(f"Date must be in {DATE_FORMAT.replace('%', '').lower()} format.") from exc


def validate_year_month(year: int, month: int) -> None:
    """Validate report year and month."""
    if year < 1:
        raise ExpenseError("Year must be a positive integer.")
    if month < 1 or month > 12:
        raise ExpenseError("Month must be between 1 and 12.")


def is_expense_in_month(expense: Expense, year: int, month: int) -> bool:
    """Return True if an expense date falls in a month."""
    expense_date = parse_date(expense.expense_date)
    return expense_date.year == year and expense_date.month == month


def format_decimal(amount: Decimal) -> str:
    """Format a Decimal as a fixed two-decimal string."""
    return str(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Track daily expenses, generate reports, and export CSV data.",
    )
    parser.add_argument(
        "--storage",
        default=str(default_storage_path()),
        help="Path to JSON storage file (default: ~/.expense_tracker/expenses.json).",
    )
    parser.add_argument(
        "--categories",
        default=",".join(DEFAULT_CATEGORIES),
        help="Comma-separated supported categories.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a daily expense.")
    add_parser.add_argument("amount", help="Positive amount, for example 12.50.")
    add_parser.add_argument("category", help="Expense category.")
    add_parser.add_argument(
        "--date",
        dest="expense_date",
        help="Expense date in YYYY-MM-DD format (default: today).",
    )
    add_parser.add_argument("--note", default="", help="Optional note.")

    report_parser = subparsers.add_parser(
        "report", help="Generate a monthly expense report."
    )
    report_parser.add_argument("year", type=int, help="Report year, for example 2025.")
    report_parser.add_argument("month", type=int, help="Report month, 1-12.")

    export_parser = subparsers.add_parser(
        "export", help="Export expenses for a date range to CSV."
    )
    export_parser.add_argument("start_date", help="Inclusive start date in YYYY-MM-DD format.")
    export_parser.add_argument("end_date", help="Inclusive end date in YYYY-MM-DD format.")
    export_parser.add_argument("output", help="Output CSV file path.")

    categories_parser = subparsers.add_parser(
        "categories", help="List supported expense categories."
    )
    categories_parser.set_defaults(command="categories")

    return parser


def parse_categories(value: str) -> tuple[str, ...]:
    """Parse comma-separated categories from CLI option."""
    categories = tuple(
        category.strip().lower() for category in value.split(",") if category.strip()
    )
    if not categories:
        raise ExpenseError("At least one category must be configured.")
    return categories


def format_report(report: dict[str, Any]) -> str:
    """Format a monthly report for terminal output."""
    lines = [
        f"Monthly Expense Report: {report['year']:04d}-{report['month']:02d}",
        f"Expenses recorded: {report['count']}",
        f"Total: {report['total']}",
        "By category:",
    ]
    categories: dict[str, str] = report["categories"]
    if categories:
        for category in sorted(categories):
            lines.append(f"  {category}: {categories[category]}")
    else:
        lines.append("  No expenses recorded.")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the expense tracker CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        categories = parse_categories(args.categories)
        tracker = ExpenseTracker(args.storage, categories)

        if args.command == "add":
            expense = tracker.add_expense(
                amount=args.amount,
                category=args.category,
                expense_date=args.expense_date,
                note=args.note,
            )
            print(
                "Expense added: "
                f"{expense.expense_date} {expense.category} {expense.amount}"
            )
            return 0

        if args.command == "report":
            report = tracker.monthly_report(args.year, args.month)
            print(format_report(report))
            return 0

        if args.command == "export":
            count = tracker.export_csv(args.start_date, args.end_date, args.output)
            print(f"Exported {count} expense(s) to {args.output}")
            return 0

        if args.command == "categories":
            print("Supported categories: " + ", ".join(categories))
            return 0

        parser.error("Unknown command.")
        return 2
    except ExpenseError as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
