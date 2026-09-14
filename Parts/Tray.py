"""Parametric removable service tray."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Geometry import GeometryEngine, Point3D
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class TrayPart:
    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def dimensions(self) -> tuple[float, float, float]:
        t = self.parameters.tray
        return t.length_mm, t.width_mm, t.depth_mm

    @property
    def origin(self) -> Point3D:
        return GeometryEngine.placement_solver(self.parameters).tray_origin()

    def build_shape(self) -> Any:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        origin = self.origin
        length_mm, width_mm, depth_mm = self.dimensions
        return Part.makeBox(
            length_mm,
            width_mm,
            depth_mm,
            Part.Vector(origin.x_mm, origin.y_mm, origin.z_mm),
        )
