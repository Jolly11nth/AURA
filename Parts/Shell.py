"""Parametric AURA outer shell."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class ShellPart:
    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def outer_dimensions(self) -> tuple[float, float, float]:
        e = self.parameters.envelope
        return e.length_mm, e.width_mm, e.height_mm - e.ground_clearance_mm

    @property
    def inner_dimensions(self) -> tuple[float, float, float]:
        e = self.parameters.envelope
        t = self.parameters.shell.wall_thickness_mm
        return e.length_mm - 2 * t, e.width_mm - 2 * t, e.height_mm - e.ground_clearance_mm - t

    def build_shape(self) -> Any:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        e = self.parameters.envelope
        t = self.parameters.shell.wall_thickness_mm
        body_h = e.height_mm - e.ground_clearance_mm
        origin = Part.Vector(0, 0, e.ground_clearance_mm)
        outer = Part.makeBox(e.length_mm, e.width_mm, body_h, origin)
        inner = Part.makeBox(e.length_mm - 2 * t, e.width_mm - 2 * t, body_h - t, Part.Vector(t, t, e.ground_clearance_mm + t))
        return outer.cut(inner)
