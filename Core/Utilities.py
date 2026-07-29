"""General-purpose helpers with no CAD runtime dependencies."""

from __future__ import annotations


def millimetres_to_metres(value_mm: float) -> float:
    """Convert millimetres to metres."""
    return value_mm / 1000.0
