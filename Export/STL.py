"""STL export request descriptors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class STLExportRequest:
    """Output path for a STL export operation."""

    output_path: Path
