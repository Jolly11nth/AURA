"""Simulation configuration primitives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationScenario:
    """Named simulation scenario descriptor."""

    name: str
    duration_s: float
