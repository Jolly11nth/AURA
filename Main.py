"""AURA application entry point."""

from __future__ import annotations

from Assembly.Assembly import AURAAssembly
from Core.Parameters import DEFAULT_PARAMETERS


def build_default_assembly() -> AURAAssembly:
    """Build the default immutable AURA assembly descriptor."""
    return AURAAssembly(DEFAULT_PARAMETERS)


if __name__ == "__main__":
    build_default_assembly()
