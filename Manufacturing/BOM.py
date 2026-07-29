"""Bill-of-materials generation primitives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BOMLine:
    """A single bill-of-materials line item."""

    part_number: str
    description: str
    quantity: int
