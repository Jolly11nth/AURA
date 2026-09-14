"""Parametric AURA chassis base."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Geometry import BoundingBox, BoxEnvelope, GeometryEngine, Point3D
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class BasePart:
    """Parametric chassis floor descriptor and optional FreeCAD builder."""

    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def dimensions(self) -> BoxEnvelope:
        return GeometryEngine.dimensions(
            self.parameters.envelope.length_mm,
            self.parameters.envelope.width_mm,
            self.parameters.base.floor_thickness_mm,
        )

    @property
    def envelope(self) -> BoxEnvelope:
        return self.dimensions

    @property
    def bounding_box(self) -> BoundingBox:
        robot_envelope = GeometryEngine.robot_envelope(self.parameters)
        return BoundingBox(
            origin=Point3D(
                x_mm=robot_envelope.outer_bounding_box.origin.x_mm,
                y_mm=robot_envelope.outer_bounding_box.origin.y_mm,
                z_mm=self.parameters.envelope.ground_clearance_mm,
            ),
            dimensions=self.dimensions,
        )

    def build_shape(self) -> Any:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        box = self.bounding_box
        return Part.makeBox(
            box.dimensions.length_mm,
            box.dimensions.width_mm,
            box.dimensions.height_mm,
            Part.Vector(box.origin.x_mm, box.origin.y_mm, box.origin.z_mm),
        )
