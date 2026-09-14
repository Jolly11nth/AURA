"""Parametric removable service tray."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class TrayPart:
    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def dimensions(self) -> tuple[float, float, float]:
        t = self.parameters.tray
        return t.length_mm, t.width_mm, t.depth_mm

    def build_shape(self) -> Any:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        t = self.parameters.tray
        e = self.parameters.envelope
        x = (e.length_mm - t.length_mm) / 2
        y = (e.width_mm - t.width_mm) / 2
        z = e.ground_clearance_mm + self.parameters.base.floor_thickness_mm
        return Part.makeBox(t.length_mm, t.width_mm, t.depth_mm, Part.Vector(x, y, z))
