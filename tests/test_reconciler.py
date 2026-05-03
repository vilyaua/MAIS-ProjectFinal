from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from payment_reconciliation.cli import main
from payment_reconciliation.errors import InputFileError, ValidationError
from payment_reconciliation.reconciler import reconcile_excel
from payment_reconciliation.report import format_report


BASE_COLUMNS = [
    "supplier",
    "contract_amount",
    "currency",
    "payment_stage",
    "payment_amount",
    "balance",
    "initial_percent",
    "final_percent",
]


def write_workbook(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    workbook = tmp_path / "payments.xlsx"
    pd.DataFrame(rows, columns=BASE_COLUMNS).to_excel(workbook, index=False)
    return workbook


def test_valid_excel_outputs_no_discrepancies_for_multiple_currencies(tmp_path: Path) -> None:
    workbook = write_workbook(
        tmp_path,
        [
            {
                "supplier": "Alpha",
                "contract_amount": 1000,
                "currency": "USD",
                "payment_stage": "initial",
                "payment_amount": 300,
                "balance": 700,
                "initial_percent": 30,
                "final_percent": 70,
            },
            {
                "supplier": "Alpha",
                "contract_amount": 1000,
                "currency": "USD",
                "payment_stage": "final",
                "payment_amount": 700,
                "balance": 0,
                "initial_percent": 30,
                "final_percent": 70,
            },
            {
                "supplier": "Beta",
                "contract_amount": 2000,
                "currency": "EUR",
                "payment_stage": "initial",
                "payment_amount": 600,
                "balance": 1400,
                "initial_percent": 30,
                "final_percent": 70,
            },
            {
                "supplier": "Gamma",
                "contract_amount": 3000,
                "currency": "CNY",
                "payment_stage": "initial",
                "payment_amount": 900,
                "balance": 2100,
                "initial_percent": 30,
                "final_percent": 70,
            },
            {
                "supplier": "Gamma",
                "contract_amount": 3000,
                "currency": "CNY",
                "payment_stage": "final",
                "payment_amount": 2100,
                "balance": 0,
                "initial_percent": 30,
                "final_percent": 70,
            },
        ],
    )

    result = reconcile_excel(workbook)
    report = format_report(result)

    assert not result.has_discrepancies
    assert "No discrepancies found" in report
    assert result.supplier_count == 3
    assert result.payment_count == 5


def test_discrepancies_are_identified_and_reported(tmp_path: Path) -> None:
    workbook = write_workbook(
        tmp_path,
        [
            {
                "supplier": "UnderCo",
                "contract_amount": 1000,
                "currency": "USD",
                "payment_stage": "initial",
                "payment_amount": 250,
                "balance": 750,
                "initial_percent": 30,
                "final_percent": 70,
            },
            {
                "supplier": "OverCo",
                "contract_amount": 1000,
                "currency": "EUR",
                "payment_stage": "final",
                "payment_amount": 750,
                "balance": 0,
                "initial_percent": 30,
                "final_percent": 70,
            },
            {
                "supplier": "ZeroDebt",
                "contract_amount": 1000,
                "currency": "CNY",
                "payment_stage": "initial",
                "payment_amount": 300,
                "balance": 0,
                "initial_percent": 30,
                "final_percent": 70,
            },
            {
                "supplier": "BadPrepay",
                "contract_amount": 1000,
                "currency": "USD",
                "payment_stage": "initial",
                "payment_amount": 400,
                "balance": 600,
                "initial_percent": 40,
                "final_percent": 60,
            },
        ],
    )

    result = reconcile_excel(workbook)
    report = format_report(result)
    categories = {discrepancy.category for discrepancy in result.discrepancies}

    assert "Underpayment" in categories
    assert "Overpayment" in categories
    assert "Zero balance with outstanding debt" in categories
    assert "Incorrect prepayment" in categories
    assert "Incorrect prepayment percentage" in categories
    assert "Incorrect final percentage" in categories
    assert "UnderCo" in report
    assert "OverCo" in report
    assert "CNY" in report
    assert "USD" in report
    assert "EUR" in report


def test_unsupported_currency_is_validation_error(tmp_path: Path) -> None:
    workbook = write_workbook(
        tmp_path,
        [
            {
                "supplier": "Unsupported",
                "contract_amount": 1000,
                "currency": "GBP",
                "payment_stage": "initial",
                "payment_amount": 300,
                "balance": 700,
                "initial_percent": 30,
                "final_percent": 70,
            }
        ],
    )

    with pytest.raises(ValidationError, match="unsupported currency 'GBP'"):
        reconcile_excel(workbook)


def test_malformed_excel_is_handled_gracefully(tmp_path: Path) -> None:
    bad_file = tmp_path / "broken.xlsx"
    bad_file.write_text("not an excel workbook", encoding="utf-8")

    with pytest.raises(InputFileError, match="Excel"):
        reconcile_excel(bad_file)


def test_missing_required_columns_are_reported(tmp_path: Path) -> None:
    workbook = tmp_path / "missing.xlsx"
    pd.DataFrame(
        [
            {
                "supplier": "Missing",
                "contract_amount": 1000,
                "currency": "USD",
            }
        ]
    ).to_excel(workbook, index=False)

    with pytest.raises(ValidationError) as exc_info:
        reconcile_excel(workbook)

    message = str(exc_info.value)
    assert "Missing required column" in message
    assert "payment_stage" in message
    assert "payment_amount" in message


def test_missing_required_cell_is_reported(tmp_path: Path) -> None:
    workbook = write_workbook(
        tmp_path,
        [
            {
                "supplier": "BlankPayment",
                "contract_amount": 1000,
                "currency": "USD",
                "payment_stage": "initial",
                "payment_amount": None,
                "balance": 700,
                "initial_percent": 30,
                "final_percent": 70,
            }
        ],
    )

    with pytest.raises(ValidationError, match="missing required value for payment_amount"):
        reconcile_excel(workbook)


def test_cli_prints_report_and_returns_status_code(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    workbook = write_workbook(
        tmp_path,
        [
            {
                "supplier": "CliSupplier",
                "contract_amount": 1000,
                "currency": "USD",
                "payment_stage": "initial",
                "payment_amount": 300,
                "balance": 700,
                "initial_percent": 30,
                "final_percent": 70,
            }
        ],
    )

    status = main([str(workbook)])
    captured = capsys.readouterr()

    assert status == 0
    assert "Payment Reconciliation Report" in captured.out
