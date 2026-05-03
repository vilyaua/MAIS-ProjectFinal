"""Comparison logic for parsed documents and original orders."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .models import Discrepancy, Item, OriginalOrder
from .parser import parse_document

_PRICE_TOLERANCE = Decimal("0.0001")
_QUANTITY_TOLERANCE = Decimal("0.0001")


def compare_documents(
    file_path: str | Path,
    original_order: OriginalOrder | Iterable[Item | Mapping[str, object]],
) -> list[Discrepancy]:
    """Parse a document and compare it against an original order."""
    actual_items = parse_document(file_path)
    return compare_items(actual_items, original_order)


def compare_items(
    actual_items: Sequence[Item],
    original_order: OriginalOrder | Iterable[Item | Mapping[str, object]],
) -> list[Discrepancy]:
    """Compare parsed items with expected order items.

    Duplicate item codes are aggregated by summing quantities. Prices must be
    consistent across duplicates; inconsistent duplicate prices are reported.
    """
    expected_order = (
        original_order
        if isinstance(original_order, OriginalOrder)
        else OriginalOrder.from_data(original_order)
    )
    expected_map, expected_price_conflicts = _aggregate_items(expected_order.items)
    actual_map, actual_price_conflicts = _aggregate_items(actual_items)

    discrepancies: list[Discrepancy] = []
    discrepancies.extend(expected_price_conflicts)
    discrepancies.extend(actual_price_conflicts)

    for code in sorted(expected_map.keys() - actual_map.keys()):
        expected = expected_map[code]
        discrepancies.append(
            Discrepancy(
                type="MISSING_ITEM",
                item_code=code,
                expected=expected,
                actual=None,
                message=f"Expected item {code!r} is missing from the document.",
            )
        )

    for code in sorted(actual_map.keys() - expected_map.keys()):
        actual = actual_map[code]
        discrepancies.append(
            Discrepancy(
                type="EXTRA_ITEM",
                item_code=code,
                expected=None,
                actual=actual,
                message=(
                    f"Document item {code!r} is not present in the original order."
                ),
            )
        )

    for code in sorted(expected_map.keys() & actual_map.keys()):
        expected = expected_map[code]
        actual = actual_map[code]
        if abs(expected.quantity - actual.quantity) > _QUANTITY_TOLERANCE:
            discrepancies.append(
                Discrepancy(
                    type="QUANTITY_MISMATCH",
                    item_code=code,
                    expected=expected,
                    actual=actual,
                    message=(
                        f"Quantity mismatch for {code!r}: expected "
                        f"{expected.quantity}, got {actual.quantity}."
                    ),
                )
            )
        if abs(expected.price - actual.price) > _PRICE_TOLERANCE:
            discrepancies.append(
                Discrepancy(
                    type="PRICE_MISMATCH",
                    item_code=code,
                    expected=expected,
                    actual=actual,
                    message=(
                        f"Price mismatch for {code!r}: expected "
                        f"{expected.price}, got {actual.price}."
                    ),
                )
            )

    return discrepancies


def _aggregate_items(items: Iterable[Item]) -> tuple[dict[str, Item], list[Discrepancy]]:
    grouped: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        grouped[item.code.strip()].append(item)

    aggregated: dict[str, Item] = {}
    discrepancies: list[Discrepancy] = []
    for code, group in grouped.items():
        quantity = sum((item.quantity for item in group), Decimal("0"))
        price = group[0].price
        distinct_prices = {item.price for item in group}
        if len(distinct_prices) > 1:
            discrepancies.append(
                Discrepancy(
                    type="DUPLICATE_PRICE_CONFLICT",
                    item_code=code,
                    expected=None,
                    actual=None,
                    message=(
                        f"Duplicate item {code!r} has inconsistent prices: "
                        f"{sorted(str(value) for value in distinct_prices)}."
                    ),
                )
            )
        aggregated[code] = Item(code=code, quantity=quantity, price=price)
    return aggregated, discrepancies
