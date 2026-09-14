"""Parametric electronics and battery bay placeholders."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class ElectronicsPart:
    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def controller_dimensions(self) -> tuple[float, float, float]:
        e = self.parameters.electronics
        return e.controller_bay_length_mm, e.controller_bay_width_mm, self.parameters.tray.depth_mm

    @property
    def battery_dimensions(self) -> tuple[float, float, float]:
        e = self.parameters.electronics
        return e.battery_bay_length_mm, e.battery_bay_width_mm, self.parameters.tray.depth_mm

    def build_shapes(self) -> tuple[Any, Any]:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc
        e = self.parameters.electronics
        t = self.parameters.tray
        body = self.parameters.envelope
        z = body.ground_clearance_mm + self.parameters.base.floor_thickness_mm + e.service_clearance_mm
        cx = (body.length_mm - e.controller_bay_length_mm - e.battery_bay_length_mm) / 3
        controller = Part.makeBox(e.controller_bay_length_mm, e.controller_bay_width_mm, t.depth_mm, Part.Vector(cx, (body.width_mm - e.controller_bay_width_mm) / 2, z))
        battery_x = cx + e.controller_bay_length_mm + cx
        battery = Part.makeBox(e.battery_bay_length_mm, e.battery_bay_width_mm, t.depth_mm, Part.Vector(battery_x, (body.width_mm - e.battery_bay_width_mm) / 2, z))
        return controller, battery
