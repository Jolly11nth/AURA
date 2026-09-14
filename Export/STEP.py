"""STEP export adapter for FreeCAD-backed AURA assemblies."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class STEPExportRequest:
    """Backward-compatible STEP export request descriptor."""
    output_path: Path


def export_step(shapes: Iterable[Any], output_path: str | Path) -> Path:
    """Export one or more FreeCAD Part shapes to STEP."""
    try:
        import Part  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("FreeCAD Part is required for STEP export") from exc
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    Part.export(list(shapes), str(target))
    return target
