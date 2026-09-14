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
        return GeometryEngine.dimensions(self.parameters.envelope.length_mm, self.parameters.envelope.width_mm, self.parameters.base.floor_thickness_mm)

    @property
    def envelope(self) -> BoxEnvelope:
        return self.dimensions

    @property
    def bounding_box(self) -> BoundingBox:
        box = GeometryEngine.bounding_box_from_origin(self.dimensions)
        return BoundingBox(Point3D(0.0, 0.0, self.parameters.envelope.ground_clearance_mm), box.dimensions)

    def build_shape(self) -> Any:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        e = self.parameters.envelope
        return Part.makeBox(e.length_mm, e.width_mm, self.parameters.base.floor_thickness_mm, Part.Vector(0, 0, e.ground_clearance_mm))
