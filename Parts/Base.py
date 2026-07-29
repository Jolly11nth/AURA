"""Base part specification."""

from __future__ import annotations

from dataclasses import dataclass

from Core.Geometry import BoxEnvelope
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class BasePart:
    """Parametric base part descriptor."""

    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def envelope(self) -> BoxEnvelope:
        """Return the base bounding envelope."""
        return BoxEnvelope(
            self.parameters.envelope.length_mm,
            self.parameters.envelope.width_mm,
            self.parameters.base.floor_thickness_mm,
        )
