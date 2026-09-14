"""Parametric differential-drive wheels."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Geometry import Point3D
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class WheelPart:
    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def left_center(self) -> Point3D:
        e = self.parameters.envelope
        w = self.parameters.wheels
        return Point3D(e.length_mm - w.axle_offset_from_rear_mm, (e.width_mm + w.track_width_mm) / 2, e.ground_clearance_mm + w.diameter_mm / 2)

    @property
    def right_center(self) -> Point3D:
        e = self.parameters.envelope
        w = self.parameters.wheels
        return Point3D(e.length_mm - w.axle_offset_from_rear_mm, (e.width_mm - w.track_width_mm) / 2, e.ground_clearance_mm + w.diameter_mm / 2)

    def build_shapes(self) -> tuple[Any, Any]:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        w = self.parameters.wheels
        r = w.diameter_mm / 2
        shapes = []
        for center in (self.left_center, self.right_center):
            shape = Part.makeCylinder(r, w.width_mm, Part.Vector(center.x_mm, center.y_mm - w.width_mm / 2, center.z_mm), Part.Vector(0, 1, 0))
            shapes.append(shape)
        return shapes[0], shapes[1]
