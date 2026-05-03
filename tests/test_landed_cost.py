from decimal import Decimal

import pytest

from src.landed_cost import (
    LandedCostError,
    calculate_landed_costs,
    format_results_table,
    parse_input,
    run,
)


def test_valid_json_outputs_correct_table() -> None:
    content = """
    [
      {
        "product_id": "SKU-1",
        "fob_price": 10,
        "sea_freight": 2.5,
        "customs_duty": 1,
        "vat": 2,
        "quantity": 3
      },
      {
        "product_id": "SKU-2",
        "fob_price": "5.25",
        "sea_freight": "0.75",
        "customs_duty": "0.50",
        "vat": "1.00",
        "quantity": "4"
      }
    ]
    """

    output = run(content, "json")

    assert "Product Identifier" in output
    assert "SKU-1" in output
    assert "15.50" in output
    assert "46.50" in output
    assert "SKU-2" in output
    assert "7.50" in output
    assert "30.00" in output


def test_valid_csv_outputs_correct_table() -> None:
    content = (
        "product_id,fob_price,sea_freight,customs_duty,vat,quantity\n"
        "A,100,20,5,25,2\n"
        "B,10,1,2,3,0\n"
    )

    output = run(content, "csv")

    assert "A" in output
    assert "150.00" in output
    assert "300.00" in output
    assert "B" in output
    assert "16.00" in output
    assert "0.00" in output


def test_negative_monetary_value_raises_error() -> None:
    content = (
        "product_id,fob_price,sea_freight,customs_duty,vat,quantity\n"
        "A,100,-1,5,25,2\n"
    )

    with pytest.raises(LandedCostError, match="sea_freight.*non-negative"):
        run(content, "csv")


def test_missing_required_field_raises_error() -> None:
    content = (
        "product_id,fob_price,sea_freight,vat,quantity\n"
        "A,100,20,25,2\n"
    )

    with pytest.raises(LandedCostError, match="customs_duty.*absent"):
        run(content, "csv")


def test_zero_quantity_has_zero_total_but_nonzero_unit_cost() -> None:
    rows = parse_input(
        "product_id,fob_price,sea_freight,customs_duty,vat,quantity\nA,10,2,1,3,0\n",
        "csv",
    )
    results = calculate_landed_costs(rows)

    assert results[0].landed_cost_per_unit == Decimal("16")
    assert results[0].total_landed_cost == Decimal("0")


def test_malformed_json_raises_invalid_format_error() -> None:
    with pytest.raises(LandedCostError, match="Invalid JSON format"):
        run('[{"product_id": "A",]', "json")


def test_malformed_csv_empty_header_raises_invalid_format_error() -> None:
    content = "product_id,,fob_price,sea_freight,customs_duty,vat,quantity\nA,x,1,2,3,4,5\n"

    with pytest.raises(LandedCostError, match="Invalid CSV format"):
        run(content, "csv")


def test_json_object_with_positions_key_is_supported() -> None:
    content = (
        '{"positions": [{"product_id": "A", "fob_price": 1, '
        '"sea_freight": 2, "customs_duty": 3, "vat": 4, "quantity": 5}]}'
    )

    output = run(content, "auto")

    assert "A" in output
    assert "10.00" in output
    assert "50.00" in output


def test_format_results_table_handles_empty_results() -> None:
    output = format_results_table([])

    assert "Product Identifier" in output
    assert "Landed Cost per Unit" in output
