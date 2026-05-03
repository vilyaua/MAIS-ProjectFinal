"""Command-line interface for the payment reconciliation tool."""

from __future__ import annotations

import argparse
from pathlib import Path

from payment_reconciliation.errors import ReconciliationError
from payment_reconciliation.reconciler import reconcile_excel
from payment_reconciliation.report import format_report


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="payment-reconciliation",
        description=(
            "Reconcile supplier payments in an Excel workbook against a "
            "30% initial / 70% final payment scheme."
        ),
    )
    parser.add_argument(
        "excel_file",
        type=Path,
        help="Path to the Excel .xlsx file containing payment data.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional path to write the text report. Defaults to stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the payment reconciliation CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = reconcile_excel(args.excel_file)
        report = format_report(result)
        if args.output:
            args.output.write_text(report + "\n", encoding="utf-8")
            print(f"Report written to {args.output}")
        else:
            print(report)
        return 1 if result.has_discrepancies else 0
    except ReconciliationError as exc:
        parser.exit(status=2, message=f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
