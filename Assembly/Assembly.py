"""Top-level AURA assembly composition."""

from __future__ import annotations

from dataclasses import dataclass, field

from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS
from Parts.Base import BasePart


@dataclass(frozen=True, slots=True)
class AURAAssembly:
    """Immutable assembly descriptor for all configured robot parts."""

    parameters: AURAParameters = DEFAULT_PARAMETERS
    base: BasePart = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "base", BasePart(self.parameters))
