"""Single source of truth for AURA engineering parameters.

This module is intentionally independent of FreeCAD and other CAD runtimes so
it can be imported by tests, simulation code, manufacturing exporters, and CAD
adapters without side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Mapping


class UnitSystem(StrEnum):
    """Supported engineering unit systems."""

    METRIC_MM = "metric_mm"


class DriveLayout(StrEnum):
    """Supported mobile-base drive layouts."""

    DIFFERENTIAL = "differential"


@dataclass(frozen=True, slots=True)
class EnvelopeParameters:
    """Overall robot packaging dimensions in millimetres."""

    length_mm: float = 420.0
    width_mm: float = 320.0
    height_mm: float = 260.0
    ground_clearance_mm: float = 35.0

    def __post_init__(self) -> None:
        _require_positive("length_mm", self.length_mm)
        _require_positive("width_mm", self.width_mm)
        _require_positive("height_mm", self.height_mm)
        _require_non_negative("ground_clearance_mm", self.ground_clearance_mm)
        if self.ground_clearance_mm >= self.height_mm:
            raise ValueError("ground_clearance_mm must be less than height_mm")


@dataclass(frozen=True, slots=True)
class BaseParameters:
    """Structural base parameters in millimetres."""

    wall_thickness_mm: float = 3.0
    floor_thickness_mm: float = 4.0
    corner_radius_mm: float = 18.0
    fastener_clearance_mm: float = 0.3

    def __post_init__(self) -> None:
        _require_positive("wall_thickness_mm", self.wall_thickness_mm)
        _require_positive("floor_thickness_mm", self.floor_thickness_mm)
        _require_positive("corner_radius_mm", self.corner_radius_mm)
        _require_non_negative("fastener_clearance_mm", self.fastener_clearance_mm)


@dataclass(frozen=True, slots=True)
class WheelParameters:
    """Differential-drive wheel and axle parameters in millimetres."""

    layout: DriveLayout = DriveLayout.DIFFERENTIAL
    diameter_mm: float = 96.0
    width_mm: float = 28.0
    track_width_mm: float = 278.0
    axle_offset_from_rear_mm: float = 135.0

    def __post_init__(self) -> None:
        _require_positive("diameter_mm", self.diameter_mm)
        _require_positive("width_mm", self.width_mm)
        _require_positive("track_width_mm", self.track_width_mm)
        _require_non_negative("axle_offset_from_rear_mm", self.axle_offset_from_rear_mm)


@dataclass(frozen=True, slots=True)
class ElectronicsParameters:
    """Reserved electronics bay and service-clearance dimensions."""

    controller_bay_length_mm: float = 160.0
    controller_bay_width_mm: float = 110.0
    battery_bay_length_mm: float = 150.0
    battery_bay_width_mm: float = 95.0
    service_clearance_mm: float = 8.0

    def __post_init__(self) -> None:
        _require_positive("controller_bay_length_mm", self.controller_bay_length_mm)
        _require_positive("controller_bay_width_mm", self.controller_bay_width_mm)
        _require_positive("battery_bay_length_mm", self.battery_bay_length_mm)
        _require_positive("battery_bay_width_mm", self.battery_bay_width_mm)
        _require_non_negative("service_clearance_mm", self.service_clearance_mm)


@dataclass(frozen=True, slots=True)
class ManufacturingParameters:
    """Manufacturing tolerances and process assumptions."""

    default_tolerance_mm: float = 0.2
    minimum_printable_wall_mm: float = 1.6
    draft_angle_deg: float = 1.5

    def __post_init__(self) -> None:
        _require_positive("default_tolerance_mm", self.default_tolerance_mm)
        _require_positive("minimum_printable_wall_mm", self.minimum_printable_wall_mm)
        _require_non_negative("draft_angle_deg", self.draft_angle_deg)


@dataclass(frozen=True, slots=True)
class AURAParameters:
    """Top-level immutable configuration for the AURA robot platform."""

    unit_system: UnitSystem = UnitSystem.METRIC_MM
    envelope: EnvelopeParameters = field(default_factory=EnvelopeParameters)
    base: BaseParameters = field(default_factory=BaseParameters)
    wheels: WheelParameters = field(default_factory=WheelParameters)
    electronics: ElectronicsParameters = field(default_factory=ElectronicsParameters)
    manufacturing: ManufacturingParameters = field(default_factory=ManufacturingParameters)
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        _validate_packaging(self)



def _validate_packaging(parameters: AURAParameters) -> None:
    if parameters.wheels.track_width_mm >= parameters.envelope.width_mm:
        raise ValueError("wheels.track_width_mm must fit within envelope.width_mm")
    usable_length = parameters.envelope.length_mm - (2.0 * parameters.base.wall_thickness_mm)
    if parameters.electronics.controller_bay_length_mm > usable_length:
        raise ValueError("controller bay length must fit inside the base envelope")
    if parameters.electronics.battery_bay_length_mm > usable_length:
        raise ValueError("battery bay length must fit inside the base envelope")


def _require_positive(name: str, value: float) -> None:
    if value <= 0.0:
        raise ValueError(f"{name} must be positive")


def _require_non_negative(name: str, value: float) -> None:
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")

DEFAULT_PARAMETERS: Final[AURAParameters] = AURAParameters(
    metadata={"platform": "AURA", "release_milestone": "v0.2.0"}
)

