"""Parametric differential-drive wheels."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Geometry import GeometryEngine, Point3D
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class WheelPart:
    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def left_center(self) -> Point3D:
        return GeometryEngine.placement_solver(self.parameters).wheel_center("left")

    @property
    def right_center(self) -> Point3D:
        return GeometryEngine.placement_solver(self.parameters).wheel_center("right")

    def build_shapes(self) -> tuple[Any, Any]:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        w = self.parameters.wheels
        r = w.diameter_mm / 2.0
        return tuple(
            Part.makeCylinder(
                r,
                w.width_mm,
                Part.Vector(c.x_mm, c.y_mm - w.width_mm / 2.0, c.z_mm),
                Part.Vector(0, 1, 0),
            )
            for c in (self.left_center, self.right_center)
        )  # type: ignore[return-value]


# Original scaffold name retained for compatibility.
WheelsPart = WheelPart
