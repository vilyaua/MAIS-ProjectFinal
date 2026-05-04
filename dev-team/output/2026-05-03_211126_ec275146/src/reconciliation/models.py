"""Data models used by the reconciliation library."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class Item:
    """A normalized line item from an order, invoice, or packing list."""

    code: str
    quantity: Decimal
    price: Decimal
    description: str | None = None


@dataclass(frozen=True)
class OriginalOrder:
    """Container for expected order line items."""

    items: list[Item]

    @classmethod
    def from_data(cls, data: Iterable[Item | Mapping[str, Any]]) -> "OriginalOrder":
        """Build an order from Item instances or dictionaries.

        Dictionary keys may use common names such as ``code``, ``item_code``,
        ``sku``, ``quantity``, ``qty``, ``price`` or ``unit_price``.
        """
        from .numeric import parse_decimal

        normalized: list[Item] = []
        for index, raw_item in enumerate(data, start=1):
            if isinstance(raw_item, Item):
                normalized.append(raw_item)
                continue
            if not isinstance(raw_item, Mapping):
                raise TypeError(
                    f"Order item #{index} must be an Item or mapping, "
                    f"got {type(raw_item).__name__}."
                )

            code = raw_item.get("code") or raw_item.get("item_code") or raw_item.get("sku")
            quantity = raw_item.get("quantity", raw_item.get("qty"))
            price = raw_item.get("price", raw_item.get("unit_price"))
            if code is None or quantity is None or price is None:
                raise ValueError(f"Order item #{index} must contain code, quantity, and price.")

            normalized.append(
                Item(
                    code=str(code).strip(),
                    quantity=parse_decimal(quantity, field_name=f"order quantity #{index}"),
                    price=parse_decimal(price, field_name=f"order price #{index}"),
                    description=(
                        str(raw_item["description"]).strip()
                        if raw_item.get("description") is not None
                        else None
                    ),
                )
            )
        return cls(normalized)


@dataclass(frozen=True)
class Discrepancy:
    """A structured difference between expected and parsed document data."""

    type: str
    item_code: str
    message: str
    expected: Item | None = None
    actual: Item | None = None
