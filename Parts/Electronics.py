"""Parametric electronics and battery bay placeholders."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Core.Geometry import GeometryEngine, Point3D
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

    @property
    def controller_center(self) -> Point3D:
        return GeometryEngine.placement_solver(self.parameters).motherboard_center()

    @property
    def battery_center(self) -> Point3D:
        return GeometryEngine.placement_solver(self.parameters).battery_center()

    def build_shapes(self) -> tuple[Any, Any]:
        try:
            import Part  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD Part is required to build CAD geometry") from exc

        # Keep the runtime import alive for the FreeCAD-only CAD boundary.
        del Part
        controller = self._box_from_center(self.controller_center, self.controller_dimensions)
        battery = self._box_from_center(self.battery_center, self.battery_dimensions)
        return controller, battery

    @staticmethod
    def _box_from_center(center: Point3D, dimensions: tuple[float, float, float]) -> Any:
        import Part

        length_mm, width_mm, height_mm = dimensions
        return Part.makeBox(
            length_mm,
            width_mm,
            height_mm,
            Part.Vector(
                center.x_mm - (length_mm / 2.0),
                center.y_mm - (width_mm / 2.0),
                center.z_mm - (height_mm / 2.0),
            ),
        )
