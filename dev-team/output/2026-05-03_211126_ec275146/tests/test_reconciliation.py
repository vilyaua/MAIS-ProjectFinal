from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook
from reconciliation import (
    Item,
    OriginalOrder,
    ParsingError,
    UnsupportedFileTypeError,
    compare_documents,
    compare_items,
    parse_document,
)
from reconciliation.numeric import parse_decimal
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def _create_excel(path: Path, rows: list[list[object]]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    workbook.save(path)


def _create_pdf(path: Path, lines: list[str]) -> None:
    pdf = canvas.Canvas(str(path), pagesize=letter)
    y = 750
    for line in lines:
        pdf.drawString(40, y, line)
        y -= 18
    pdf.save()


def test_excel_invoice_comparison_returns_discrepancies(tmp_path: Path) -> None:
    invoice = tmp_path / "invoice.xlsx"
    _create_excel(
        invoice,
        [
            ["Commercial Invoice"],
            ["Item Code", "Description", "Quantity", "Unit Price"],
            ["SKU-1", "Widget", "10", "2.50"],
            ["SKU-2", "Gadget", "8", "4.00"],
            ["SKU-3", "Extra", "1", "9.00"],
        ],
    )
    order = OriginalOrder.from_data(
        [
            {"code": "SKU-1", "quantity": 10, "price": "2.50"},
            {"code": "SKU-2", "quantity": 5, "price": "4.50"},
            {"code": "SKU-4", "quantity": 1, "price": "1.00"},
        ]
    )

    discrepancies = compare_documents(invoice, order)

    assert {item.type for item in discrepancies} == {
        "QUANTITY_MISMATCH",
        "PRICE_MISMATCH",
        "MISSING_ITEM",
        "EXTRA_ITEM",
    }
    assert any(item.item_code == "SKU-2" for item in discrepancies)
    assert any(item.item_code == "SKU-3" and item.type == "EXTRA_ITEM" for item in discrepancies)
    assert any(item.item_code == "SKU-4" and item.type == "MISSING_ITEM" for item in discrepancies)


def test_pdf_packing_list_matching_order_has_no_discrepancies(tmp_path: Path) -> None:
    packing_list = tmp_path / "packing.pdf"
    _create_pdf(
        packing_list,
        [
            "Item Code Quantity Unit Price",
            "ABC-01 12 3.75",
            "ABC-02 5 10.00",
        ],
    )
    order = [
        {"code": "ABC-01", "quantity": "12", "price": "3.75"},
        {"code": "ABC-02", "quantity": "5", "price": "10.00"},
    ]

    assert compare_documents(packing_list, order) == []


def test_unsupported_file_format_raises_clear_error(tmp_path: Path) -> None:
    unsupported = tmp_path / "invoice.txt"
    unsupported.write_text("Item Code Quantity Price\nA 1 2", encoding="utf-8")

    with pytest.raises(UnsupportedFileTypeError, match="Unsupported file type"):
        parse_document(unsupported)


def test_extra_document_item_is_flagged() -> None:
    actual_items = [
        Item(code="A", quantity=Decimal("1"), price=Decimal("2")),
        Item(code="B", quantity=Decimal("1"), price=Decimal("2")),
    ]
    order = [{"code": "A", "quantity": 1, "price": 2}]

    discrepancies = compare_items(actual_items, order)

    assert len(discrepancies) == 1
    assert discrepancies[0].type == "EXTRA_ITEM"
    assert discrepancies[0].item_code == "B"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,234.56", Decimal("1234.56")),
        ("1.234,56", Decimal("1234.56")),
        ("1234,56", Decimal("1234.56")),
        ("1 234,56", Decimal("1234.56")),
        ("￥1，234．56", Decimal("1234.56")),
    ],
)
def test_numeric_fields_with_different_formatting(raw: str, expected: Decimal) -> None:
    assert parse_decimal(raw) == expected


def test_excel_with_comma_decimal_separator_parses_correctly(tmp_path: Path) -> None:
    invoice = tmp_path / "invoice.xlsx"
    _create_excel(
        invoice,
        [
            ["货号", "数量", "单价"],
            ["CN-1", "1 234,50", "2,75"],
        ],
    )

    items = parse_document(invoice)

    assert items == [Item(code="CN-1", quantity=Decimal("1234.50"), price=Decimal("2.75"))]


def test_corrupted_excel_returns_meaningful_error(tmp_path: Path) -> None:
    corrupted = tmp_path / "bad.xlsx"
    corrupted.write_bytes(b"not a valid workbook")

    with pytest.raises(ParsingError, match="Failed to read Excel file"):
        parse_document(corrupted)


def test_corrupted_pdf_returns_meaningful_error(tmp_path: Path) -> None:
    corrupted = tmp_path / "bad.pdf"
    corrupted.write_bytes(b"not a valid pdf")

    with pytest.raises(ParsingError, match="Failed to read PDF file"):
        parse_document(corrupted)
