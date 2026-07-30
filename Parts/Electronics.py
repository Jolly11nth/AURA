"""Electronics part placeholder for the AURA parametric architecture."""

from __future__ import annotations

from dataclasses import dataclass

from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class ElectronicsPart:
    """Parametric Electronics part descriptor."""

    parameters: AURAParameters = DEFAULT_PARAMETERS
