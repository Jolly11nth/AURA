"""Technical drawing export adapter for FreeCAD."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TechDrawExportRequest:
    """Backward-compatible TechDraw export request descriptor."""
    output_path: Path


def export_techdraw(document: Any, page_name: str, output_path: str | Path) -> Path:
    """Export an existing FreeCAD TechDraw page to PDF."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    page = document.getObject(page_name)
    if page is None:
        raise ValueError(f"TechDraw page {page_name!r} does not exist")
    page.ViewObject.show()
    page.ViewObject.saveAs(str(target))
    return target
