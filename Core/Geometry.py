"""Framework-neutral geometric primitives for AURA modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point3D:
    """A three-dimensional point in millimetres."""

    x_mm: float
    y_mm: float
    z_mm: float


@dataclass(frozen=True, slots=True)
class BoxEnvelope:
    """Axis-aligned rectangular envelope in millimetres."""

    length_mm: float
    width_mm: float
    height_mm: float

    @property
    def volume_mm3(self) -> float:
        """Return the enclosed volume in cubic millimetres."""
        return self.length_mm * self.width_mm * self.height_mm
