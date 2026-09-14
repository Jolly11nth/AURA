"""STL export adapter for FreeCAD-backed AURA assemblies."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class STLExportRequest:
    """Backward-compatible STL export request descriptor."""
    output_path: Path


def export_stl(shape: Any, output_path: str | Path, *, linear_deflection: float = 0.1, angular_deflection: float = 0.2) -> Path:
    """Export a FreeCAD shape to STL using explicit mesh tolerances."""
    try:
        import Mesh  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("FreeCAD Mesh is required for STL export") from exc
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    Mesh.export([shape], str(target), linearDeflection=linear_deflection, angularDeflection=angular_deflection)
    return target
