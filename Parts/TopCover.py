"""Parametric AURA removable top cover."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Geometry import GeometryEngine, Point3D
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class TopCoverPart:
    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def dimensions(self) -> tuple[float, float, float]:
        e = self.parameters.envelope
        return e.length_mm, e.width_mm, self.parameters.base.floor_thickness_mm

    @property
    def origin(self) -> Point3D:
        envelope = GeometryEngine.robot_envelope(self.parameters).outer_bounding_box
        return Point3D(
            envelope.origin.x_mm,
            envelope.origin.y_mm,
            self.parameters.envelope.height_mm - self.parameters.base.floor_thickness_mm,
        )

    def build_shape(self) -> Any:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        origin = self.origin
        length_mm, width_mm, height_mm = self.dimensions
        return Part.makeBox(
            length_mm,
            width_mm,
            height_mm,
            Part.Vector(origin.x_mm, origin.y_mm, origin.z_mm),
        )
