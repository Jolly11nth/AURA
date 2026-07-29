"""Material definitions shared by design and manufacturing modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Material:
    """Engineering material metadata."""

    name: str
    density_g_cm3: float
    process: str


PETG = Material(name="PETG", density_g_cm3=1.27, process="FDM")
ALUMINUM_6061 = Material(name="Aluminum 6061", density_g_cm3=2.70, process="CNC")
