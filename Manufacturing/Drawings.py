"""Manufacturing drawing request descriptors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DrawingRequest:
    """Metadata required to produce a drawing."""

    part_number: str
    revision: str
