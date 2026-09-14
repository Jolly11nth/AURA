"""Bill-of-materials generation from the canonical parameter model."""
from __future__ import annotations
from dataclasses import dataclass
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class BOMItem:
    part_number: str
    description: str
    quantity: int
    material: str = ""
    notes: str = ""


# Original scaffold name retained for compatibility.
BOMLine = BOMItem


def generate_bom(parameters: AURAParameters = DEFAULT_PARAMETERS) -> tuple[BOMItem, ...]:
    return (
        BOMItem("AURA-BASE-001", "Chassis base", 1, "PETG"),
        BOMItem("AURA-SHELL-001", "Outer shell", 1, "PETG"),
        BOMItem("AURA-TOP-001", "Removable top cover", 1, "PETG"),
        BOMItem("AURA-TRAY-001", "Service tray", 1, "PETG"),
        BOMItem("AURA-WHEEL-001", f"Drive wheel Ø{parameters.wheels.diameter_mm:.0f} mm", 2, "TPU"),
        BOMItem("AURA-ELEC-001", "Controller bay envelope", 1, "ALUMINUM_6061"),
        BOMItem("AURA-ELEC-002", "Battery bay envelope", 1, "ALUMINUM_6061"),
    )
