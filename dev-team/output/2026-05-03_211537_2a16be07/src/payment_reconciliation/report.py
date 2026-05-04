"""Text report generation for reconciliation results."""

from __future__ import annotations

from decimal import Decimal

from payment_reconciliation.reconciler import Discrepancy, ReconciliationResult


def format_report(result: ReconciliationResult) -> str:
    """Return a human-readable text report for a reconciliation result."""

    lines = [
        "Payment Reconciliation Report",
        "=============================",
        f"Suppliers processed: {result.supplier_count}",
        f"Payment entries processed: {result.payment_count}",
        f"Discrepancies found: {len(result.discrepancies)}",
        "",
    ]

    if not result.discrepancies:
        lines.append("No discrepancies found. All payments match the 30%/70% scheme.")
        return "\n".join(lines)

    grouped = _group_by_supplier(result.discrepancies)
    for supplier in sorted(grouped):
        lines.append(f"Supplier: {supplier}")
        lines.append("-" * (len(supplier) + 10))
        for discrepancy in grouped[supplier]:
            lines.extend(_format_discrepancy(discrepancy))
        lines.append("")

    return "\n".join(lines).rstrip()


def _group_by_supplier(
    discrepancies: list[Discrepancy],
) -> dict[str, list[Discrepancy]]:
    grouped: dict[str, list[Discrepancy]] = {}
    for discrepancy in discrepancies:
        grouped.setdefault(discrepancy.supplier, []).append(discrepancy)
    return grouped


def _format_discrepancy(discrepancy: Discrepancy) -> list[str]:
    row = "supplier total" if discrepancy.row_number is None else f"row {discrepancy.row_number}"
    lines = [
        f"  * {discrepancy.category} ({row})",
        f"    Currency: {discrepancy.currency}",
        f"    Details: {discrepancy.message}",
    ]
    if discrepancy.expected_amount is not None:
        lines.append(
            f"    Expected: {_format_money(discrepancy.expected_amount, discrepancy.currency)}"
        )
    if discrepancy.actual_amount is not None:
        lines.append(
            f"    Actual:   {_format_money(discrepancy.actual_amount, discrepancy.currency)}"
        )
    if discrepancy.difference is not None:
        lines.append(
            f"    Difference: {_format_money(discrepancy.difference, discrepancy.currency)}"
        )
    return lines


def _format_money(amount: Decimal, currency: str) -> str:
    return f"{amount:,.2f} {currency}"
