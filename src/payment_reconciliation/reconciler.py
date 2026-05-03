"""Core reconciliation logic for supplier payment Excel files."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import pandas as pd

from payment_reconciliation.errors import InputFileError, ValidationError

SUPPORTED_CURRENCIES = {"USD", "CNY", "EUR"}
REQUIRED_COLUMNS = {
    "supplier",
    "contract_amount",
    "currency",
    "payment_stage",
    "payment_amount",
    "balance",
    "initial_percent",
    "final_percent",
}
STAGE_PERCENT_COLUMN = {"initial": "initial_percent", "final": "final_percent"}
EXPECTED_SCHEME = {"initial": Decimal("30.00"), "final": Decimal("70.00")}
MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")


@dataclass(frozen=True)
class PaymentEntry:
    """Validated payment row from the input file."""

    row_number: int
    supplier: str
    contract_amount: Decimal
    currency: str
    payment_stage: str
    payment_amount: Decimal
    balance: Decimal
    initial_percent: Decimal
    final_percent: Decimal


@dataclass(frozen=True)
class Discrepancy:
    """A user-facing reconciliation discrepancy."""

    supplier: str
    currency: str
    row_number: int | None
    category: str
    message: str
    expected_amount: Decimal | None = None
    actual_amount: Decimal | None = None
    difference: Decimal | None = None


@dataclass(frozen=True)
class ReconciliationResult:
    """Complete reconciliation result for a workbook."""

    discrepancies: list[Discrepancy]
    payment_count: int
    supplier_count: int

    @property
    def has_discrepancies(self) -> bool:
        """Return True when at least one discrepancy was found."""

        return bool(self.discrepancies)


def reconcile_excel(file_path: str | Path) -> ReconciliationResult:
    """Parse, validate, and reconcile a payment Excel workbook.

    Args:
        file_path: Path to an .xlsx/.xls file. The first sheet must contain the
            required columns listed in REQUIRED_COLUMNS.

    Raises:
        InputFileError: If the file is missing or cannot be parsed as Excel.
        ValidationError: If required columns/data are missing or invalid.
    """

    frame = _read_excel(file_path)
    normalized_frame = _normalize_columns(frame)
    _validate_required_columns(normalized_frame)
    entries = _validate_rows(normalized_frame)
    discrepancies = _find_discrepancies(entries)
    suppliers = {entry.supplier for entry in entries}
    return ReconciliationResult(
        discrepancies=discrepancies,
        payment_count=len(entries),
        supplier_count=len(suppliers),
    )


def _read_excel(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise InputFileError(f"Input file not found: {path}")
    if not path.is_file():
        raise InputFileError(f"Input path is not a file: {path}")

    try:
        return pd.read_excel(path, sheet_name=0, engine="openpyxl")
    except ValueError as exc:
        raise InputFileError(
            f"Malformed Excel file or unsupported workbook format: {path}. "
            "Please provide a readable .xlsx file."
        ) from exc
    except OSError as exc:
        raise InputFileError(f"Could not read input file {path}: {exc}") from exc
    except Exception as exc:  # pandas/openpyxl use several exception classes
        raise InputFileError(
            f"Could not parse Excel file {path}. Please check that the file is "
            f"a valid, uncorrupted Excel workbook. Details: {exc}"
        ) from exc


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [
        str(column).strip().lower().replace(" ", "_") for column in frame.columns
    ]
    return normalized


def _validate_required_columns(frame: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValidationError(
            "Missing required column(s): "
            f"{', '.join(missing)}. Required columns are: "
            f"{', '.join(sorted(REQUIRED_COLUMNS))}."
        )
    if frame.empty:
        raise ValidationError("The Excel file contains no payment rows to process.")


def _validate_rows(frame: pd.DataFrame) -> list[PaymentEntry]:
    entries: list[PaymentEntry] = []
    errors: list[str] = []

    for index, row in frame.iterrows():
        excel_row = int(index) + 2  # header is row 1
        try:
            entries.append(_validate_row(row, excel_row))
        except ValidationError as exc:
            errors.append(str(exc))

    if errors:
        raise ValidationError("Input validation failed:\n- " + "\n- ".join(errors))

    return entries


def _validate_row(row: pd.Series, excel_row: int) -> PaymentEntry:
    supplier = _required_text(row, "supplier", excel_row)
    currency = _required_text(row, "currency", excel_row).upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise ValidationError(
            f"Row {excel_row}: unsupported currency '{currency}'. Supported "
            f"currencies are: {', '.join(sorted(SUPPORTED_CURRENCIES))}."
        )

    payment_stage = _required_text(row, "payment_stage", excel_row).lower()
    if payment_stage not in STAGE_PERCENT_COLUMN:
        raise ValidationError(
            f"Row {excel_row}: payment_stage must be 'initial' or 'final', "
            f"got '{payment_stage}'."
        )

    contract_amount = _required_decimal(row, "contract_amount", excel_row)
    payment_amount = _required_decimal(row, "payment_amount", excel_row)
    balance = _required_decimal(row, "balance", excel_row)
    initial_percent = _required_decimal(row, "initial_percent", excel_row)
    final_percent = _required_decimal(row, "final_percent", excel_row)

    if contract_amount <= 0:
        raise ValidationError(f"Row {excel_row}: contract_amount must be greater than 0.")
    if payment_amount < 0:
        raise ValidationError(f"Row {excel_row}: payment_amount cannot be negative.")
    if initial_percent < 0 or final_percent < 0:
        raise ValidationError(
            f"Row {excel_row}: payment percentages cannot be negative."
        )

    return PaymentEntry(
        row_number=excel_row,
        supplier=supplier,
        contract_amount=_money(contract_amount),
        currency=currency,
        payment_stage=payment_stage,
        payment_amount=_money(payment_amount),
        balance=_money(balance),
        initial_percent=_percent(initial_percent),
        final_percent=_percent(final_percent),
    )


def _required_text(row: pd.Series, column: str, excel_row: int) -> str:
    value = row[column]
    if _is_missing(value):
        raise ValidationError(f"Row {excel_row}: missing required value for {column}.")
    text = str(value).strip()
    if not text:
        raise ValidationError(f"Row {excel_row}: missing required value for {column}.")
    return text


def _required_decimal(row: pd.Series, column: str, excel_row: int) -> Decimal:
    value = row[column]
    if _is_missing(value):
        raise ValidationError(f"Row {excel_row}: missing required value for {column}.")
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValidationError(
            f"Row {excel_row}: {column} must be a valid number, got {value!r}."
        ) from exc


def _is_missing(value: Any) -> bool:
    return bool(pd.isna(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _percent(value: Decimal) -> Decimal:
    return value.quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP)


def _expected_amount(contract_amount: Decimal, percent: Decimal) -> Decimal:
    return _money(contract_amount * percent / Decimal("100"))


def _find_discrepancies(entries: list[PaymentEntry]) -> list[Discrepancy]:
    discrepancies: list[Discrepancy] = []
    discrepancies.extend(_scheme_discrepancies(entries))
    discrepancies.extend(_payment_entry_discrepancies(entries))
    discrepancies.extend(_supplier_level_discrepancies(entries))
    return discrepancies


def _scheme_discrepancies(entries: list[PaymentEntry]) -> list[Discrepancy]:
    discrepancies: list[Discrepancy] = []
    for entry in entries:
        if entry.initial_percent != EXPECTED_SCHEME["initial"]:
            discrepancies.append(
                Discrepancy(
                    supplier=entry.supplier,
                    currency=entry.currency,
                    row_number=entry.row_number,
                    category="Incorrect prepayment percentage",
                    message=(
                        "Initial/prepayment percentage must be 30.00%, "
                        f"got {entry.initial_percent}%."
                    ),
                )
            )
        if entry.final_percent != EXPECTED_SCHEME["final"]:
            discrepancies.append(
                Discrepancy(
                    supplier=entry.supplier,
                    currency=entry.currency,
                    row_number=entry.row_number,
                    category="Incorrect final percentage",
                    message=(
                        "Final payment percentage must be 70.00%, "
                        f"got {entry.final_percent}%."
                    ),
                )
            )
        if entry.initial_percent + entry.final_percent != Decimal("100.00"):
            discrepancies.append(
                Discrepancy(
                    supplier=entry.supplier,
                    currency=entry.currency,
                    row_number=entry.row_number,
                    category="Invalid payment scheme",
                    message=(
                        "Initial and final percentages must total 100.00%, "
                        f"got {entry.initial_percent + entry.final_percent}%."
                    ),
                )
            )
    return discrepancies


def _payment_entry_discrepancies(entries: list[PaymentEntry]) -> list[Discrepancy]:
    discrepancies: list[Discrepancy] = []
    for entry in entries:
        percent = EXPECTED_SCHEME[entry.payment_stage]
        expected = _expected_amount(entry.contract_amount, percent)
        actual = entry.payment_amount
        difference = _money(actual - expected)

        if difference < 0:
            discrepancies.append(
                Discrepancy(
                    supplier=entry.supplier,
                    currency=entry.currency,
                    row_number=entry.row_number,
                    category="Underpayment",
                    message=(
                        f"{entry.payment_stage.title()} payment is below the "
                        "expected 30%/70% milestone amount."
                    ),
                    expected_amount=expected,
                    actual_amount=actual,
                    difference=difference,
                )
            )
        elif difference > 0:
            category = (
                "Incorrect prepayment"
                if entry.payment_stage == "initial"
                else "Overpayment"
            )
            discrepancies.append(
                Discrepancy(
                    supplier=entry.supplier,
                    currency=entry.currency,
                    row_number=entry.row_number,
                    category=category,
                    message=(
                        f"{entry.payment_stage.title()} payment exceeds the "
                        "expected 30%/70% milestone amount."
                    ),
                    expected_amount=expected,
                    actual_amount=actual,
                    difference=difference,
                )
            )
    return discrepancies


def _supplier_level_discrepancies(entries: list[PaymentEntry]) -> list[Discrepancy]:
    discrepancies: list[Discrepancy] = []
    for supplier_entries in _group_by_supplier(entries).values():
        first = supplier_entries[0]
        _validate_supplier_consistency(first, supplier_entries, discrepancies)

        total_paid = _money(sum((entry.payment_amount for entry in supplier_entries), Decimal("0")))
        outstanding = _money(first.contract_amount - total_paid)
        reported_zero_balance = any(entry.balance == Decimal("0.00") for entry in supplier_entries)

        if reported_zero_balance and outstanding > 0:
            discrepancies.append(
                Discrepancy(
                    supplier=first.supplier,
                    currency=first.currency,
                    row_number=None,
                    category="Zero balance with outstanding debt",
                    message=(
                        "At least one row reports a zero balance, but total "
                        "payments are less than the contract amount."
                    ),
                    expected_amount=first.contract_amount,
                    actual_amount=total_paid,
                    difference=_money(total_paid - first.contract_amount),
                )
            )
    return discrepancies


def _validate_supplier_consistency(
    first: PaymentEntry,
    supplier_entries: list[PaymentEntry],
    discrepancies: list[Discrepancy],
) -> None:
    for entry in supplier_entries[1:]:
        if entry.currency != first.currency:
            discrepancies.append(
                Discrepancy(
                    supplier=entry.supplier,
                    currency=entry.currency,
                    row_number=entry.row_number,
                    category="Inconsistent supplier currency",
                    message=(
                        f"Supplier has mixed currencies: {first.currency} and "
                        f"{entry.currency}. Currency values are not converted."
                    ),
                )
            )
        if entry.contract_amount != first.contract_amount:
            discrepancies.append(
                Discrepancy(
                    supplier=entry.supplier,
                    currency=entry.currency,
                    row_number=entry.row_number,
                    category="Inconsistent contract amount",
                    message=(
                        "Supplier rows must use the same contract_amount; got "
                        f"{first.contract_amount} and {entry.contract_amount}."
                    ),
                )
            )


def _group_by_supplier(entries: list[PaymentEntry]) -> dict[str, list[PaymentEntry]]:
    grouped: dict[str, list[PaymentEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.supplier, []).append(entry)
    return grouped
