"""TechDraw export request descriptors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TechDrawExportRequest:
    """Output path for a TechDraw export operation."""

    output_path: Path
