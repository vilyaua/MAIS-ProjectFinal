"""Landed cost calculator core logic and CLI helpers."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO


class LandedCostError(ValueError):
    """Raised when input data cannot be parsed or validated."""


REQUIRED_FIELDS: tuple[str, ...] = (
    "product_id",
    "fob_price",
    "sea_freight",
    "customs_duty",
    "vat",
    "quantity",
)

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "product_id": ("product_id", "product_identifier", "identifier", "sku", "product", "id"),
    "fob_price": ("fob_price", "fob", "fob price", "fob_price_per_unit"),
    "sea_freight": (
        "sea_freight",
        "freight",
        "sea freight",
        "allocated_sea_freight",
        "allocated_sea_freight_per_unit",
    ),
    "customs_duty": ("customs_duty", "duty", "customs duty"),
    "vat": ("vat", "tax"),
    "quantity": ("quantity", "qty", "units"),
}

MONEY_FIELDS: tuple[str, ...] = ("fob_price", "sea_freight", "customs_duty", "vat")


@dataclass(frozen=True)
class ProductPosition:
    """Validated product position input."""

    product_id: str
    fob_price: Decimal
    sea_freight: Decimal
    customs_duty: Decimal
    vat: Decimal
    quantity: Decimal


@dataclass(frozen=True)
class LandedCostResult:
    """Computed landed cost values for a product position."""

    product_id: str
    landed_cost_per_unit: Decimal
    total_landed_cost: Decimal


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _build_normalized_mapping(row: Mapping[str, Any]) -> dict[str, Any]:
    return {_normalize_key(str(key)): value for key, value in row.items()}


def _get_field(row: Mapping[str, Any], canonical_name: str, row_number: int) -> Any:
    normalized = _build_normalized_mapping(row)
    for alias in FIELD_ALIASES[canonical_name]:
        normalized_alias = _normalize_key(alias)
        if normalized_alias in normalized:
            value = normalized[normalized_alias]
            if value is None or (isinstance(value, str) and value.strip() == ""):
                raise LandedCostError(
                    f"Missing data in row {row_number}: field '{canonical_name}' is empty."
                )
            return value
    raise LandedCostError(
        f"Missing data in row {row_number}: required field '{canonical_name}' is absent."
    )


def _parse_decimal(value: Any, field_name: str, row_number: int) -> Decimal:
    if isinstance(value, bool):
        raise LandedCostError(
            f"Invalid input in row {row_number}: field '{field_name}' must be a number."
        )
    try:
        decimal_value = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        raise LandedCostError(
            f"Invalid input in row {row_number}: field '{field_name}' must be a number."
        ) from None
    if not decimal_value.is_finite():
        raise LandedCostError(
            f"Invalid input in row {row_number}: field '{field_name}' must be finite."
        )
    if decimal_value < 0:
        raise LandedCostError(
            f"Invalid input in row {row_number}: field '{field_name}' must be non-negative."
        )
    return decimal_value


def validate_position(row: Mapping[str, Any], row_number: int) -> ProductPosition:
    """Validate one product row and return a ProductPosition."""
    product_id = str(_get_field(row, "product_id", row_number)).strip()
    if not product_id:
        raise LandedCostError(f"Missing data in row {row_number}: field 'product_id' is empty.")

    parsed_values = {
        field: _parse_decimal(_get_field(row, field, row_number), field, row_number)
        for field in (*MONEY_FIELDS, "quantity")
    }

    return ProductPosition(
        product_id=product_id,
        fob_price=parsed_values["fob_price"],
        sea_freight=parsed_values["sea_freight"],
        customs_duty=parsed_values["customs_duty"],
        vat=parsed_values["vat"],
        quantity=parsed_values["quantity"],
    )


def calculate_landed_cost(position: ProductPosition) -> LandedCostResult:
    """Calculate landed cost per unit and total batch landed cost."""
    per_unit = position.fob_price + position.sea_freight + position.customs_duty + position.vat
    total = per_unit * position.quantity
    return LandedCostResult(
        product_id=position.product_id,
        landed_cost_per_unit=per_unit,
        total_landed_cost=total,
    )


def calculate_landed_costs(rows: Iterable[Mapping[str, Any]]) -> list[LandedCostResult]:
    """Validate and calculate landed costs for all input rows."""
    results: list[LandedCostResult] = []
    for row_number, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise LandedCostError(
                f"Invalid input in row {row_number}: each product position must be an object/record."
            )
        results.append(calculate_landed_cost(validate_position(row, row_number)))
    return results


def parse_json(content: str) -> list[Mapping[str, Any]]:
    """Parse JSON content into product position mappings."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LandedCostError(
            f"Invalid JSON format: {exc.msg} at line {exc.lineno}, column {exc.colno}."
        ) from None

    if isinstance(data, Mapping):
        if "products" in data:
            data = data["products"]
        elif "positions" in data:
            data = data["positions"]
        else:
            data = [data]

    if not isinstance(data, list):
        raise LandedCostError("Invalid JSON format: expected an array of product positions.")
    return data


def parse_csv(content: str) -> list[Mapping[str, Any]]:
    """Parse CSV content into product position mappings."""
    try:
        reader = csv.DictReader(StringIO(content))
        if reader.fieldnames is None:
            raise LandedCostError("Invalid CSV format: missing header row.")
        if any(field is None or field.strip() == "" for field in reader.fieldnames):
            raise LandedCostError("Invalid CSV format: header contains an empty column name.")
        rows = list(reader)
    except csv.Error as exc:
        raise LandedCostError(f"Invalid CSV format: {exc}.") from None

    if not rows and not content.strip():
        raise LandedCostError("Invalid CSV format: input is empty.")
    return rows


def parse_input(content: str, input_format: str) -> list[Mapping[str, Any]]:
    """Parse content according to the requested input format."""
    if not content.strip():
        raise LandedCostError("Invalid input: no data provided.")

    normalized_format = input_format.lower()
    if normalized_format == "json":
        return parse_json(content)
    if normalized_format == "csv":
        return parse_csv(content)
    if normalized_format == "auto":
        stripped = content.lstrip()
        if stripped.startswith("{") or stripped.startswith("["):
            return parse_json(content)
        return parse_csv(content)
    raise LandedCostError("Invalid format option: choose 'json', 'csv', or 'auto'.")


def _format_decimal(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{quantized:.2f}"


def format_results_table(results: Sequence[LandedCostResult]) -> str:
    """Format results as a plain-text table."""
    headers = ("Product Identifier", "Landed Cost per Unit", "Total Landed Cost")
    rows = [
        (
            result.product_id,
            _format_decimal(result.landed_cost_per_unit),
            _format_decimal(result.total_landed_cost),
        )
        for result in results
    ]
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def render_row(values: Sequence[str]) -> str:
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(values))

    separator = "-+-".join("-" * width for width in widths)
    lines = [render_row(headers), separator]
    lines.extend(render_row(row) for row in rows)
    return "\n".join(lines)


def read_text(path: str | None) -> str:
    """Read text from a file path or standard input when path is None/'-'."""
    if path is None or path == "-":
        return sys.stdin.read()
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise LandedCostError(f"Unable to read input file '{path}': {exc.strerror}.") from None


def write_text(path: str | None, content: str, stdout: TextIO | None = None) -> None:
    """Write text to a file path or standard output when path is None/'-'."""
    if path is None or path == "-":
        target = stdout if stdout is not None else sys.stdout
        target.write(content)
        target.write("\n")
        return
    try:
        Path(path).write_text(content + "\n", encoding="utf-8")
    except OSError as exc:
        raise LandedCostError(f"Unable to write output file '{path}': {exc.strerror}.") from None


def run(content: str, input_format: str = "auto") -> str:
    """Parse input content, calculate costs, and return a formatted table."""
    rows = parse_input(content, input_format)
    results = calculate_landed_costs(rows)
    return format_results_table(results)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Calculate landed cost per unit and total batch landed cost."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Input file path, or '-' / omitted to read from standard input.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("auto", "json", "csv"),
        default="auto",
        help="Input format. Defaults to auto-detection.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="-",
        help="Output file path, or '-' to write to standard output.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        content = read_text(args.input)
        table = run(content, args.format)
        write_text(args.output, table)
    except LandedCostError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
