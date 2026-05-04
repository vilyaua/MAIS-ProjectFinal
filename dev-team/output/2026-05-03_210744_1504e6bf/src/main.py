"""Command-line interface for the container load calculator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from container_load_calculator import (
    Box,
    box_from_mapping,
    calculate_container_results,
    format_results,
    parse_box_spec,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Calculate volume and weight utilization for 20ft, 40ft, and "
            "40HQ containers. Dimensions are meters and weight is kilograms."
        )
    )
    parser.add_argument(
        "--box",
        action="append",
        default=[],
        metavar="L,W,H,WEIGHT,QTY",
        help=("Box specification. Can be repeated. Example: --box 1.2,0.8,0.5,25,10"),
    )
    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "Path to a JSON file containing a list of boxes. Each box must "
            "have length, width, height, weight, and quantity fields."
        ),
    )
    return parser


def load_boxes_from_json(path: Path) -> list[Box]:
    """Load and validate boxes from a JSON file."""
    try:
        raw_content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"unable to read input file '{path}': {exc}") from exc

    try:
        data: Any = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in input file '{path}': {exc.msg}") from exc

    if not isinstance(data, list):
        raise ValueError("input JSON must be a list of box objects")

    boxes: list[Box] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Box {index}: must be a JSON object")
        boxes.append(box_from_mapping(item, index=index))
    return boxes


def parse_boxes(args: argparse.Namespace) -> list[Box]:
    """Parse all box inputs from CLI arguments."""
    boxes: list[Box] = []

    if args.input is not None:
        boxes.extend(load_boxes_from_json(args.input))

    for index, spec in enumerate(args.box, start=len(boxes) + 1):
        boxes.append(parse_box_spec(spec, index=index))

    return boxes


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return an exit status code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        boxes = parse_boxes(args)
        results = calculate_container_results(boxes)
    except ValueError as exc:
        parser.exit(status=2, message=f"Error: {exc}\n")

    print(format_results(results), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
