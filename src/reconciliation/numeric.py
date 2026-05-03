"""Numeric parsing helpers for supplier documents."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from .exceptions import ParsingError

_CURRENCY_SYMBOLS = ("¥", "￥", "$", "€", "£", "RMB", "CNY", "USD")


def parse_decimal(value: Any, field_name: str = "numeric field") -> Decimal:
    """Parse a quantity or price with common Chinese/European separators.

    Handles examples such as ``1,234.56``, ``1.234,56``, ``1234,56``,
    ``1 234,56`` and values containing currency symbols.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if value is None:
        raise ParsingError(f"Missing value for {field_name}.")

    text = str(value).strip()
    if not text:
        raise ParsingError(f"Empty value for {field_name}.")

    for symbol in _CURRENCY_SYMBOLS:
        text = text.replace(symbol, "")
    text = text.replace("\u00a0", "").replace(" ", "").strip()
    text = text.replace("，", ",").replace("．", ".")

    # Parenthesized accounting notation: (1,234.50) -> -1,234.50
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]

    # Remove leading plus signs and keep a single leading minus if present.
    text = text.lstrip("+")

    comma_pos = text.rfind(",")
    dot_pos = text.rfind(".")
    if comma_pos != -1 and dot_pos != -1:
        decimal_separator = "," if comma_pos > dot_pos else "."
        thousands_separator = "." if decimal_separator == "," else ","
        text = text.replace(thousands_separator, "")
        text = text.replace(decimal_separator, ".")
    elif comma_pos != -1:
        text = _normalize_single_separator(text, ",")
    elif dot_pos != -1:
        text = _normalize_single_separator(text, ".")

    if negative and not text.startswith("-"):
        text = f"-{text}"

    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ParsingError(f"Invalid numeric value for {field_name}: {value!r}.") from exc


def _normalize_single_separator(text: str, separator: str) -> str:
    """Normalize a number with only commas or only dots."""
    parts = text.split(separator)
    if len(parts) == 1:
        return text

    # Multiple separators usually indicate thousands grouping, except the last
    # group could be a decimal fraction in malformed supplier exports. Prefer
    # valid 3-digit groups as thousands separators.
    if len(parts) > 2:
        if all(len(part) == 3 for part in parts[1:]):
            return "".join(parts)
        return "".join(parts[:-1]) + "." + parts[-1]

    left, right = parts
    # One separator: a 3-digit right side is commonly a thousands separator;
    # otherwise treat it as a decimal separator (e.g. 12,5 or 1234,56).
    if len(right) == 3 and left not in {"", "-"}:
        return left + right
    return left + "." + right
