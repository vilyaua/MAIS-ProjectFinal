"""Tests for the container load calculator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from container_load_calculator import (  # noqa: E402
    Box,
    calculate_container_results,
    parse_box_spec,
)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI for integration-style assertions."""
    return subprocess.run(
        [sys.executable, str(SRC / "main.py"), *args],
        check=False,
        text=True,
        capture_output=True,
    )


def test_valid_boxes_calculate_utilization_percentages() -> None:
    boxes = [Box(1.0, 1.0, 1.0, 100.0, 10), Box(2.0, 1.0, 1.0, 200.0, 5)]

    results = calculate_container_results(boxes)

    assert len(results) == 3
    assert results[0].container_name == "20ft"
    assert results[0].total_volume == pytest.approx(20.0)
    assert results[0].volume_utilization_percent == pytest.approx(60.2409638)
    assert results[1].container_name == "40ft"
    assert results[2].container_name == "40HQ"


def test_weight_limit_exceeded_warning_is_reported() -> None:
    boxes = [Box(1.0, 1.0, 1.0, 30_000.0, 1)]

    results = calculate_container_results(boxes)

    assert all(result.weight_exceeded for result in results)
    assert all(
        any("Weight limit exceeded" in warning for warning in result.warnings) for result in results
    )
    assert all(result.leftover_weight == 0 for result in results)


@pytest.mark.parametrize(
    "spec, expected",
    [
        ("0,1,1,1,1", "length must be greater than zero"),
        ("1,-1,1,1,1", "width must be greater than zero"),
        ("1,1,nope,1,1", "height must be a positive number"),
        ("1,1,1,1,1.5", "quantity must be a whole number"),
        ("1,1,1", "box must be formatted"),
    ],
)
def test_invalid_box_specs_raise_helpful_errors(spec: str, expected: str) -> None:
    with pytest.raises(ValueError, match=expected):
        parse_box_spec(spec, index=1)


def test_empty_list_outputs_zero_utilization() -> None:
    results = calculate_container_results([])

    assert len(results) == 3
    for result in results:
        assert result.total_volume == 0
        assert result.total_weight == 0
        assert result.volume_utilization_percent == 0
        assert result.weight_utilization_percent == 0
        assert result.leftover_volume == result.volume_capacity
        assert result.leftover_weight == result.weight_capacity
        assert result.warnings == ()


def test_large_quantity_exceeds_volume_and_leftover_is_zero() -> None:
    boxes = [Box(2.0, 2.0, 2.0, 1.0, 100)]

    results = calculate_container_results(boxes)

    assert all(result.volume_exceeded for result in results)
    assert all(result.leftover_volume == 0 for result in results)
    assert all(
        any("Volume capacity exceeded" in warning for warning in result.warnings)
        for result in results
    )


def test_cli_accepts_repeated_box_arguments() -> None:
    completed = run_cli("--box", "1,1,1,100,2", "--box", "2,1,1,50,1")

    assert completed.returncode == 0
    assert "Container: 20ft" in completed.stdout
    assert "Volume utilization:" in completed.stdout
    assert "Total volume: 4.00 m³" in completed.stdout


def test_cli_invalid_input_returns_error_without_traceback() -> None:
    completed = run_cli("--box", "1,0,1,100,2")

    assert completed.returncode == 2
    assert "Error: Box 1: width must be greater than zero" in completed.stderr
    assert "Traceback" not in completed.stderr


def test_cli_accepts_empty_json_list(tmp_path: Path) -> None:
    input_file = tmp_path / "boxes.json"
    input_file.write_text(json.dumps([]), encoding="utf-8")

    completed = run_cli("--input", str(input_file))

    assert completed.returncode == 0
    assert "Total volume: 0.00 m³" in completed.stdout
    assert "Warnings: none" in completed.stdout
