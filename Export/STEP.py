"""STEP export request descriptors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class STEPExportRequest:
    """Output path for a STEP export operation."""

    output_path: Path
