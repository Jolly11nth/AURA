"""Parametric AURA outer shell."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Geometry import BoundingBox, Dimensions3D, GeometryEngine, Point3D
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

    @property
    def bounding_box(self) -> BoundingBox:
        envelope = GeometryEngine.robot_envelope(self.parameters)
        return BoundingBox(
            origin=Point3D(
                envelope.outer_bounding_box.origin.x_mm,
                envelope.outer_bounding_box.origin.y_mm,
                envelope.ground_clearance_mm,
            ),
            dimensions=Dimensions3D(*self.outer_dimensions),
        )

    def build_shape(self) -> Any:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        box = self.bounding_box
        t = self.parameters.shell.wall_thickness_mm
        outer = Part.makeBox(
            box.dimensions.length_mm,
            box.dimensions.width_mm,
            box.dimensions.height_mm,
            Part.Vector(box.origin.x_mm, box.origin.y_mm, box.origin.z_mm),
        )
        inner = Part.makeBox(
            box.dimensions.length_mm - 2.0 * t,
            box.dimensions.width_mm - 2.0 * t,
            box.dimensions.height_mm - t,
            Part.Vector(
                box.origin.x_mm + t,
                box.origin.y_mm + t,
                box.origin.z_mm + t,
            ),
        )
        return outer.cut(inner)
