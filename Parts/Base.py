"""Base part specification."""

from __future__ import annotations

from dataclasses import dataclass

from Core.Geometry import BoundingBox, BoxEnvelope, GeometryEngine
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class BasePart:
    """Parametric base part descriptor."""

    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def dimensions(self) -> BoxEnvelope:
        """Return base extents from the centralized geometry engine."""
        return GeometryEngine.dimensions(
            self.parameters.envelope.length_mm,
            self.parameters.envelope.width_mm,
            self.parameters.base.floor_thickness_mm,
        )

    @property
    def envelope(self) -> BoxEnvelope:
        """Return the base bounding dimensions.

        This property preserves the original scaffold API while delegating all
        derived dimensions to ``Core.Geometry``.
        """
        return self.dimensions

    @property
    def bounding_box(self) -> BoundingBox:
        """Return the base bounding box anchored at the model origin."""
        return GeometryEngine.bounding_box_from_origin(self.dimensions)
