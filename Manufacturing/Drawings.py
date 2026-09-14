"""Manufacturing drawing specifications derived from AURA parameters."""
from __future__ import annotations
from dataclasses import dataclass
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class DrawingSpec:
    drawing_number: str
    title: str
    width_mm: float
    height_mm: float
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DrawingRequest:
    """Original scaffold request retained for compatibility."""
    part_number: str
    revision: str


def generate_drawing_specs(parameters: AURAParameters = DEFAULT_PARAMETERS) -> tuple[DrawingSpec, ...]:
    e = parameters.envelope
    b = parameters.base
    return (
        DrawingSpec("AURA-DWG-001", "Chassis base", e.length_mm, e.width_mm, (f"Floor thickness: {b.floor_thickness_mm:g} mm",)),
        DrawingSpec("AURA-DWG-002", "Outer shell", e.length_mm, e.width_mm, (f"Wall thickness: {parameters.shell.wall_thickness_mm:g} mm",)),
        DrawingSpec("AURA-DWG-003", "Service tray", parameters.tray.length_mm, parameters.tray.width_mm, (f"Depth: {parameters.tray.depth_mm:g} mm",)),
        DrawingSpec("AURA-DWG-004", "Drive wheel", parameters.wheels.diameter_mm, parameters.wheels.width_mm, ("Differential-drive pair",)),
    )
