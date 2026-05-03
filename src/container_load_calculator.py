"""Container load calculation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Box:
    """A box specification.

    Dimensions are expressed in meters and weight in kilograms. Quantity must be
    a positive whole number.
    """

    length: float
    width: float
    height: float
    weight: float
    quantity: int

    def __post_init__(self) -> None:
        numeric_fields = {
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "weight": self.weight,
        }
        for field_name, value in numeric_fields.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"{field_name} must be a positive number")
            if value <= 0:
                raise ValueError(f"{field_name} must be greater than zero")

        if not isinstance(self.quantity, int) or isinstance(self.quantity, bool):
            raise ValueError("quantity must be a positive integer")
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")

    @property
    def total_volume(self) -> float:
        """Return total volume for this box line in cubic meters."""
        return self.length * self.width * self.height * self.quantity

    @property
    def total_weight(self) -> float:
        """Return total weight for this box line in kilograms."""
        return self.weight * self.quantity


@dataclass(frozen=True)
class ContainerType:
    """Container capacity definition."""

    name: str
    volume_capacity: float
    weight_capacity: float


@dataclass(frozen=True)
class ContainerResult:
    """Calculated load result for a single container type."""

    container_name: str
    volume_capacity: float
    weight_capacity: float
    total_volume: float
    total_weight: float
    volume_utilization_percent: float
    weight_utilization_percent: float
    leftover_volume: float
    leftover_weight: float
    volume_exceeded: bool
    weight_exceeded: bool
    warnings: tuple[str, ...]


CONTAINER_TYPES: tuple[ContainerType, ...] = (
    ContainerType("20ft", 33.2, 28_200.0),
    ContainerType("40ft", 67.7, 28_800.0),
    ContainerType("40HQ", 76.3, 28_600.0),
)


def coerce_positive_float(value: Any, field_name: str) -> float:
    """Convert a value to a positive float or raise a helpful ValueError."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive number")
    try:
        converted = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive number") from exc
    if converted <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return converted


def coerce_positive_int(value: Any, field_name: str) -> int:
    """Convert a value to a positive integer or raise a helpful ValueError."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer")
    try:
        if isinstance(value, str) and not value.strip():
            raise ValueError
        converted_float = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer") from exc
    if not converted_float.is_integer():
        raise ValueError(f"{field_name} must be a whole number")
    converted = int(converted_float)
    if converted <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return converted


def box_from_mapping(data: dict[str, Any], index: int | None = None) -> Box:
    """Create a Box from a mapping, adding index context to validation errors."""
    required_fields = ("length", "width", "height", "weight", "quantity")
    prefix = f"Box {index}: " if index is not None else ""
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise ValueError(f"{prefix}missing required field(s): {', '.join(missing)}")

    try:
        return Box(
            length=coerce_positive_float(data["length"], "length"),
            width=coerce_positive_float(data["width"], "width"),
            height=coerce_positive_float(data["height"], "height"),
            weight=coerce_positive_float(data["weight"], "weight"),
            quantity=coerce_positive_int(data["quantity"], "quantity"),
        )
    except ValueError as exc:
        raise ValueError(f"{prefix}{exc}") from exc


def parse_box_spec(spec: str, index: int | None = None) -> Box:
    """Parse a CLI box spec in the form length,width,height,weight,quantity."""
    prefix = f"Box {index}: " if index is not None else ""
    parts = [part.strip() for part in spec.split(",")]
    if len(parts) != 5:
        raise ValueError(
            f"{prefix}box must be formatted as length,width,height,weight,quantity"
        )
    keys = ("length", "width", "height", "weight", "quantity")
    return box_from_mapping(dict(zip(keys, parts)), index=index)


def calculate_totals(boxes: Iterable[Box]) -> tuple[float, float]:
    """Calculate total volume and weight for all boxes."""
    total_volume = 0.0
    total_weight = 0.0
    for box in boxes:
        total_volume += box.total_volume
        total_weight += box.total_weight
    return total_volume, total_weight


def calculate_container_results(
    boxes: Iterable[Box],
    container_types: Iterable[ContainerType] = CONTAINER_TYPES,
) -> list[ContainerResult]:
    """Calculate utilization, leftover capacity, and warnings per container type."""
    total_volume, total_weight = calculate_totals(boxes)
    results: list[ContainerResult] = []

    for container in container_types:
        volume_utilization = (total_volume / container.volume_capacity) * 100
        weight_utilization = (total_weight / container.weight_capacity) * 100
        leftover_volume = max(container.volume_capacity - total_volume, 0.0)
        leftover_weight = max(container.weight_capacity - total_weight, 0.0)
        volume_exceeded = total_volume > container.volume_capacity
        weight_exceeded = total_weight > container.weight_capacity
        warnings: list[str] = []
        if volume_exceeded:
            warnings.append(
                f"Volume capacity exceeded for {container.name} "
                f"by {total_volume - container.volume_capacity:.2f} m³"
            )
        if weight_exceeded:
            warnings.append(
                f"Weight limit exceeded for {container.name} "
                f"by {total_weight - container.weight_capacity:.2f} kg"
            )

        results.append(
            ContainerResult(
                container_name=container.name,
                volume_capacity=container.volume_capacity,
                weight_capacity=container.weight_capacity,
                total_volume=total_volume,
                total_weight=total_weight,
                volume_utilization_percent=volume_utilization,
                weight_utilization_percent=weight_utilization,
                leftover_volume=leftover_volume,
                leftover_weight=leftover_weight,
                volume_exceeded=volume_exceeded,
                weight_exceeded=weight_exceeded,
                warnings=tuple(warnings),
            )
        )

    return results


def format_results(results: Iterable[ContainerResult]) -> str:
    """Format calculation results as human-readable CLI output."""
    lines = ["Container Load Calculator Results", "=" * 33]
    for result in results:
        lines.extend(
            [
                f"Container: {result.container_name}",
                f"  Total volume: {result.total_volume:.2f} m³",
                f"  Volume utilization: "
                f"{result.volume_utilization_percent:.2f}%",
                f"  Leftover volume: {result.leftover_volume:.2f} m³",
                f"  Total weight: {result.total_weight:.2f} kg",
                f"  Weight utilization: "
                f"{result.weight_utilization_percent:.2f}%",
                f"  Leftover weight: {result.leftover_weight:.2f} kg",
            ]
        )
        if result.warnings:
            for warning in result.warnings:
                lines.append(f"  WARNING: {warning}")
        else:
            lines.append("  Warnings: none")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
