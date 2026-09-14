"""Parametric AURA removable top cover."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class TopCoverPart:
    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def dimensions(self) -> tuple[float, float, float]:
        e = self.parameters.envelope
        return e.length_mm, e.width_mm, self.parameters.base.floor_thickness_mm

    def build_shape(self) -> Any:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        e = self.parameters.envelope
        t = self.parameters.base.floor_thickness_mm
        return Part.makeBox(e.length_mm, e.width_mm, t, Part.Vector(0, 0, e.height_mm - t))
