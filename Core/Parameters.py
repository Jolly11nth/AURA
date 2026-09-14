"""Versioned engineering parameter model for AURA.

Sprint 1 keeps this module as the single source of truth for robot parameters
while making every configuration self-describing, serializable, and validated
without importing FreeCAD or any CAD runtime. All dimensions are millimetres
unless a field name explicitly states another unit.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass, dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Final, Mapping


SCHEMA_VERSION: Final[str] = "2.1"
REQUIRED_SCHEMA_VERSION: Final[str] = SCHEMA_VERSION


class VersionMismatchError(ValueError):
    """Raised when a parameter set uses an unsupported schema version."""


class UnitSystem(StrEnum):
    """Supported engineering unit systems for serialized parameters."""

    METRIC_MM = "millimeters"


class DriveLayout(StrEnum):
    """Supported mobile-base drive layouts."""

    DIFFERENTIAL = "differential"


class ParameterGroup:
    """Shared behavior for immutable AURA parameter dataclasses.

    Purpose:
        Provide common inspection and serialization for every engineering
        parameter group without coupling the core model to CAD, simulation, or
        manufacturing runtimes.
    Assumptions:
        Subclasses are frozen dataclasses using explicit engineering units in
        their field names. Subclasses should perform local validation in
        ``__post_init__`` and top-level relationship checks belong in
        ``AURAParameters``.
    """

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary representation of this group."""
        if not is_dataclass(self):
            raise TypeError("ParameterGroup subclasses must be dataclasses")
        return {item.name: _serialize_value(getattr(self, item.name)) for item in fields(self)}

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return a deterministic JSON representation of this group."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def verify_schema_version(cls, schema_version: str) -> None:
        """Ensure a serialized parameter payload matches this module's schema."""
        if schema_version != REQUIRED_SCHEMA_VERSION:
            raise VersionMismatchError(
                f"Unsupported parameter schema {schema_version!r}; expected {REQUIRED_SCHEMA_VERSION!r}"
            )


@dataclass(frozen=True, slots=True)
class EngineeringMetadata(ParameterGroup):
    """Self-description carried by every AURA build artifact.

    Purpose:
        Identify the robot build across CAD files, simulation models, exports,
        manufacturing packages, and future Digital Twin records.
    Units:
        ``units`` stores the canonical human-readable unit label for dimensional
        values in this parameter file.
    Constraints:
        All fields must be non-empty and ``schema_version`` must match the
        module-level ``SCHEMA_VERSION``.
    Relationships:
        ``AURAParameters`` mirrors ``schema_version`` for convenient compatibility
        checks by downstream modules.
    """

    schema_version: str = SCHEMA_VERSION
    robot_name: str = "AURA"
    robot_version: str = "Prototype 1"
    manufacturer: str = "Cee Jay Solutions Ltd"
    author: str = "Jolly Christopher"
    cad_system: str = "FreeCAD"
    units: str = UnitSystem.METRIC_MM.value

    def __post_init__(self) -> None:
        self.verify_schema_version(self.schema_version)
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"metadata.{item.name} must be non-empty")


@dataclass(frozen=True, slots=True)
class EnvelopeParameters(ParameterGroup):
    """Overall robot packaging dimensions.

    Purpose:
        Define the maximum physical body envelope available to all other
        parameter groups.
    Units:
        Millimetres.
    Constraints:
        Length, width, and height must be positive. Ground clearance must be
        non-negative and lower than the total height.
    Relationships:
        Wheel, electronics, shell, tray, and payload checks are validated against
        this envelope by ``AURAParameters``.
    """

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
class BaseParameters(ParameterGroup):
    """Structural base dimensions and limits.

    Purpose:
        Define chassis floor and wall assumptions shared by body, tray,
        electronics, and wheel packaging checks.
    Units:
        Millimetres for dimensions; kilograms for payload capacity.
    Constraints:
        Structural dimensions and capacity must be positive; clearances may be
        zero but not negative.
    Relationships:
        ``AURAParameters`` verifies that the base walls leave enough usable
        interior room for batteries, controllers, and tray payloads.
    """

    wall_thickness_mm: float = 3.0
    floor_thickness_mm: float = 4.0
    corner_radius_mm: float = 18.0
    fastener_clearance_mm: float = 0.3
    structural_payload_limit_kg: float = 12.0

    def __post_init__(self) -> None:
        _require_positive("wall_thickness_mm", self.wall_thickness_mm)
        _require_positive("floor_thickness_mm", self.floor_thickness_mm)
        _require_positive("corner_radius_mm", self.corner_radius_mm)
        _require_non_negative("fastener_clearance_mm", self.fastener_clearance_mm)
        _require_positive("structural_payload_limit_kg", self.structural_payload_limit_kg)


@dataclass(frozen=True, slots=True)
class ShellParameters(ParameterGroup):
    """Outer shell packaging constraints.

    Purpose:
        Reserve shell wall and lid clearances before CAD geometry is generated in
        later sprints.
    Units:
        Millimetres.
    Constraints:
        Wall and lid clearances must be positive.
    Relationships:
        Tray and electronics bay dimensions must fit inside the shell interior.
    """

    wall_thickness_mm: float = 2.5
    lid_clearance_mm: float = 1.2

    def __post_init__(self) -> None:
        _require_positive("shell.wall_thickness_mm", self.wall_thickness_mm)
        _require_positive("shell.lid_clearance_mm", self.lid_clearance_mm)


@dataclass(frozen=True, slots=True)
class TrayParameters(ParameterGroup):
    """Internal service tray dimensions.

    Purpose:
        Define the removable tray area reserved for electronics and payload
        fixtures.
    Units:
        Millimetres.
    Constraints:
        Dimensions must be positive.
    Relationships:
        ``AURAParameters`` ensures the tray fits within the shell and body.
    """

    length_mm: float = 250.0
    width_mm: float = 210.0
    depth_mm: float = 24.0

    def __post_init__(self) -> None:
        _require_positive("tray.length_mm", self.length_mm)
        _require_positive("tray.width_mm", self.width_mm)
        _require_positive("tray.depth_mm", self.depth_mm)


@dataclass(frozen=True, slots=True)
class WheelParameters(ParameterGroup):
    """Differential-drive wheel and axle parameters.

    Purpose:
        Capture wheel packaging before CAD and motion simulation are introduced.
    Units:
        Millimetres.
    Constraints:
        Wheel dimensions and track width must be positive. Axle offset may be
        zero but not negative.
    Relationships:
        ``AURAParameters`` ensures wheels fit within the chassis width and height.
    """

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
class ElectronicsParameters(ParameterGroup):
    """Electronics and battery bay dimensions.

    Purpose:
        Reserve body volume for controller and battery hardware while keeping
        later CAD/export modules self-describing.
    Units:
        Millimetres.
    Constraints:
        Bay dimensions must be positive and service clearance cannot be negative.
    Relationships:
        ``AURAParameters`` verifies that both bays fit within the usable body and
        tray footprint.
    """

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
class PayloadParameters(ParameterGroup):
    """Payload assumptions for structural validation.

    Purpose:
        Prevent parameter sets from exceeding the structural chassis limit before
        detailed finite-element or manufacturing analysis exists.
    Units:
        Kilograms.
    Constraints:
        Payload mass cannot be negative.
    Relationships:
        ``AURAParameters`` ensures requested payload is no greater than the base
        structural payload limit.
    """

    maximum_payload_kg: float = 5.0

    def __post_init__(self) -> None:
        _require_non_negative("payload.maximum_payload_kg", self.maximum_payload_kg)


@dataclass(frozen=True, slots=True)
class ManufacturingParameters(ParameterGroup):
    """Manufacturing tolerances and process assumptions.

    Purpose:
        Provide tolerance and draft assumptions consumed by later drawing and
        export modules.
    Units:
        Millimetres for tolerances; degrees for draft angle.
    Constraints:
        Tolerances and printable wall values must be positive; draft angle may be
        zero but not negative.
    Relationships:
        Base and shell wall dimensions must be at least the minimum printable
        wall thickness.
    """

    default_tolerance_mm: float = 0.2
    minimum_printable_wall_mm: float = 1.6
    draft_angle_deg: float = 1.5

    def __post_init__(self) -> None:
        _require_positive("default_tolerance_mm", self.default_tolerance_mm)
        _require_positive("minimum_printable_wall_mm", self.minimum_printable_wall_mm)
        _require_non_negative("draft_angle_deg", self.draft_angle_deg)


@dataclass(frozen=True, slots=True)
class AURAParameters(ParameterGroup):
    """Top-level immutable configuration for one AURA robot build.

    Purpose:
        Aggregate all engineering parameter groups into a versioned,
        serializable, CAD-independent configuration object.
    Units:
        Uses the units declared in ``metadata.units``; Sprint 1 supports
        millimetres for dimensions and kilograms for payload fields.
    Constraints:
        The schema version must match ``SCHEMA_VERSION`` and all relationship
        checks in ``_validate_engineering_relationships`` must pass.
    Assumptions:
        The object is immutable after construction and safe to share across CAD,
        simulation, manufacturing, and Digital Twin layers.
    Relationships:
        This class is the compatibility boundary for downstream modules. Existing
        fields such as ``envelope``, ``base``, ``wheels``, ``electronics``,
        ``manufacturing``, and ``metadata`` remain available.
    """

    metadata: EngineeringMetadata = field(default_factory=EngineeringMetadata)
    unit_system: UnitSystem = UnitSystem.METRIC_MM
    envelope: EnvelopeParameters = field(default_factory=EnvelopeParameters)
    base: BaseParameters = field(default_factory=BaseParameters)
    shell: ShellParameters = field(default_factory=ShellParameters)
    tray: TrayParameters = field(default_factory=TrayParameters)
    wheels: WheelParameters = field(default_factory=WheelParameters)
    electronics: ElectronicsParameters = field(default_factory=ElectronicsParameters)
    payload: PayloadParameters = field(default_factory=PayloadParameters)
    manufacturing: ManufacturingParameters = field(default_factory=ManufacturingParameters)
    labels: Mapping[str, str] = field(default_factory=dict)

    @property
    def schema_version(self) -> str:
        """Return the schema version declared by this parameter set."""
        return self.metadata.schema_version

    def __post_init__(self) -> None:
        self.verify_schema_version(self.metadata.schema_version)
        if self.metadata.units != self.unit_system.value:
            raise ValueError("metadata.units must match unit_system")
        object.__setattr__(self, "labels", MappingProxyType(dict(self.labels)))
        _validate_engineering_relationships(self)

    @classmethod
    def from_registry(cls, name: str) -> "AURAParameters":
        """Return a named configuration from ``PARAMETER_REGISTRY``."""
        try:
            return PARAMETER_REGISTRY[name.upper()]
        except KeyError as exc:
            available = ", ".join(sorted(PARAMETER_REGISTRY))
            raise KeyError(f"Unknown AURA parameter configuration {name!r}; available: {available}") from exc


def _validate_engineering_relationships(parameters: AURAParameters) -> None:
    usable_length = parameters.envelope.length_mm - (2.0 * parameters.base.wall_thickness_mm)
    usable_width = parameters.envelope.width_mm - (2.0 * parameters.base.wall_thickness_mm)
    shell_interior_width = parameters.envelope.width_mm - (2.0 * parameters.shell.wall_thickness_mm)
    shell_interior_height = parameters.envelope.height_mm - parameters.envelope.ground_clearance_mm

    if parameters.wheels.track_width_mm >= parameters.envelope.width_mm:
        raise ValueError("wheels.track_width_mm must fit within envelope.width_mm")
    if parameters.wheels.diameter_mm > shell_interior_height:
        raise ValueError("wheels.diameter_mm must fit inside chassis height")
    if parameters.wheels.axle_offset_from_rear_mm >= parameters.envelope.length_mm:
        raise ValueError("wheels.axle_offset_from_rear_mm must fit within envelope.length_mm")
    if parameters.tray.length_mm > usable_length:
        raise ValueError("tray.length_mm must fit inside the usable base length")
    if parameters.tray.width_mm > shell_interior_width:
        raise ValueError("tray.width_mm must fit inside the shell width")
    if parameters.tray.depth_mm >= shell_interior_height:
        raise ValueError("tray.depth_mm must fit inside the chassis height")
    if parameters.electronics.controller_bay_length_mm > usable_length:
        raise ValueError("controller bay length must fit inside the base envelope")
    if parameters.electronics.battery_bay_length_mm > usable_length:
        raise ValueError("battery bay length must fit inside the base envelope")
    if parameters.electronics.controller_bay_width_mm > parameters.tray.width_mm:
        raise ValueError("controller bay width must fit on the tray")
    if parameters.electronics.battery_bay_width_mm > parameters.tray.width_mm:
        raise ValueError("battery bay width must fit on the tray")
    if parameters.payload.maximum_payload_kg > parameters.base.structural_payload_limit_kg:
        raise ValueError("payload.maximum_payload_kg must not exceed base structural limit")
    if parameters.base.wall_thickness_mm < parameters.manufacturing.minimum_printable_wall_mm:
        raise ValueError("base.wall_thickness_mm must meet minimum printable wall thickness")
    if parameters.shell.wall_thickness_mm < parameters.manufacturing.minimum_printable_wall_mm:
        raise ValueError("shell.wall_thickness_mm must meet minimum printable wall thickness")
    if usable_width <= 0.0 or usable_length <= 0.0:
        raise ValueError("base wall thickness leaves no usable internal envelope")


def _serialize_value(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, ParameterGroup):
        return value.to_dict()
    if is_dataclass(value):
        return {item.name: _serialize_value(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, tuple | list):
        return [_serialize_value(item) for item in value]
    return value


def _require_positive(name: str, value: float) -> None:
    if value <= 0.0:
        raise ValueError(f"{name} must be positive")


def _require_non_negative(name: str, value: float) -> None:
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")


STANDARD_PARAMETERS: Final[AURAParameters] = AURAParameters(labels={"profile": "STANDARD"})
MINI_PARAMETERS: Final[AURAParameters] = AURAParameters(
    metadata=EngineeringMetadata(robot_version="Mini Prototype"),
    envelope=EnvelopeParameters(length_mm=320.0, width_mm=240.0, height_mm=210.0),
    wheels=WheelParameters(diameter_mm=72.0, width_mm=22.0, track_width_mm=206.0),
    tray=TrayParameters(length_mm=190.0, width_mm=150.0, depth_mm=20.0),
    electronics=ElectronicsParameters(
        controller_bay_length_mm=120.0,
        controller_bay_width_mm=90.0,
        battery_bay_length_mm=110.0,
        battery_bay_width_mm=80.0,
        service_clearance_mm=6.0,
    ),
    payload=PayloadParameters(maximum_payload_kg=2.0),
    labels={"profile": "MINI"},
)
INDUSTRIAL_PARAMETERS: Final[AURAParameters] = AURAParameters(
    metadata=EngineeringMetadata(robot_version="Industrial Prototype"),
    envelope=EnvelopeParameters(length_mm=620.0, width_mm=460.0, height_mm=360.0),
    base=BaseParameters(wall_thickness_mm=5.0, floor_thickness_mm=6.0, structural_payload_limit_kg=30.0),
    wheels=WheelParameters(diameter_mm=140.0, width_mm=45.0, track_width_mm=390.0),
    tray=TrayParameters(length_mm=390.0, width_mm=310.0, depth_mm=36.0),
    electronics=ElectronicsParameters(
        controller_bay_length_mm=220.0,
        controller_bay_width_mm=150.0,
        battery_bay_length_mm=240.0,
        battery_bay_width_mm=140.0,
        service_clearance_mm=12.0,
    ),
    payload=PayloadParameters(maximum_payload_kg=18.0),
    labels={"profile": "INDUSTRIAL"},
)
DEVELOPER_PARAMETERS: Final[AURAParameters] = AURAParameters(
    metadata=EngineeringMetadata(robot_version="Developer Kit"),
    electronics=ElectronicsParameters(service_clearance_mm=15.0),
    payload=PayloadParameters(maximum_payload_kg=3.0),
    labels={"profile": "DEVELOPER"},
)

PARAMETER_REGISTRY: Final[Mapping[str, AURAParameters]] = MappingProxyType(
    {
        "STANDARD": STANDARD_PARAMETERS,
        "MINI": MINI_PARAMETERS,
        "INDUSTRIAL": INDUSTRIAL_PARAMETERS,
        "DEVELOPER": DEVELOPER_PARAMETERS,
    }
)

# Backward-compatible alias used by the original scaffold.
DEFAULT_PARAMETERS: Final[AURAParameters] = STANDARD_PARAMETERS
