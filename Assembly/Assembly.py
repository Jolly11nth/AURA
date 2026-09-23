"""Top-level AURA assembly composition and optional FreeCAD document builder."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from Core.Geometry import ClearanceReport, GeometryEngine
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS
from Parts.Base import BasePart
from Parts.Electronics import ElectronicsPart
from Parts.Shell import ShellPart
from Parts.TopCover import TopCoverPart
from Parts.Tray import TrayPart
from Parts.Wheels import WheelPart


@dataclass(frozen=True, slots=True)
class AURAAssembly:
    """Complete parametric assembly descriptor."""

    parameters: AURAParameters = DEFAULT_PARAMETERS
    base: BasePart = field(init=False)
    shell: ShellPart = field(init=False)
    top_cover: TopCoverPart = field(init=False)
    tray: TrayPart = field(init=False)
    wheels: WheelPart = field(init=False)
    electronics: ElectronicsPart = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "base", BasePart(self.parameters))
        object.__setattr__(self, "shell", ShellPart(self.parameters))
        object.__setattr__(self, "top_cover", TopCoverPart(self.parameters))
        object.__setattr__(self, "tray", TrayPart(self.parameters))
        object.__setattr__(self, "wheels", WheelPart(self.parameters))
        object.__setattr__(self, "electronics", ElectronicsPart(self.parameters))

    def validate_geometry(self) -> ClearanceReport:
        """Return the canonical Geometry validation report for this assembly."""
        return GeometryEngine(self.parameters).validate_robot()

    @property
    def parts(self) -> tuple[Any, ...]:
        return (self.base, self.shell, self.top_cover, self.tray, self.wheels, self.electronics)

    def build_document(self, name: str = "AURA") -> Any:
        """Build a named FreeCAD document containing every AURA part."""
        try:
            import FreeCAD  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("FreeCAD is required to build the AURA document") from exc

        doc = FreeCAD.newDocument(name)
        shapes = {
            "Base": self.base.build_shape(),
            "Shell": self.shell.build_shape(),
            "TopCover": self.top_cover.build_shape(),
            "Tray": self.tray.build_shape(),
        }
        left_wheel, right_wheel = self.wheels.build_shapes()
        controller, battery = self.electronics.build_shapes()
        shapes.update({"LeftWheel": left_wheel, "RightWheel": right_wheel, "ControllerBay": controller, "BatteryBay": battery})
        for object_name, shape in shapes.items():
            feature = doc.addObject("PartDesign::Feature", object_name)
            feature.Label = f"AURA {object_name}"
            feature.Shape = shape
        doc.recompute()
        return doc
