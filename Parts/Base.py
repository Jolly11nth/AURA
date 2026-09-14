"""Parametric AURA chassis base.

The module is CAD-runtime independent until ``build_shape`` is called.  This
keeps tests and engineering calculations usable on machines without FreeCAD.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Geometry import BoundingBox, BoxEnvelope, GeometryEngine
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
        return GeometryEngine.bounding_box_from_origin(self.dimensions)

    def build_shape(self) -> Any:
        """Build the chassis floor as a FreeCAD Part shape.

        Raises:
            RuntimeError: when FreeCAD/Part is not available.
        """
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        return Part.makeBox(
            self.parameters.envelope.length_mm,
            self.parameters.envelope.width_mm,
            self.parameters.base.floor_thickness_mm,
        )
