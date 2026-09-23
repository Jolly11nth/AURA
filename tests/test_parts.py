from Core.Geometry import GeometryEngine
from Core.Parameters import DEFAULT_PARAMETERS
from Parts.Base import BasePart
from Parts.Electronics import ElectronicsPart
from Parts.Shell import ShellPart
from Parts.TopCover import TopCoverPart
from Parts.Tray import TrayPart
from Parts.Wheels import WheelPart


def test_all_part_descriptors_use_same_parameters() -> None:
    parts = (BasePart(), ShellPart(), TopCoverPart(), TrayPart(), WheelPart(), ElectronicsPart())
    assert all(part.parameters is DEFAULT_PARAMETERS for part in parts)


def test_wheel_centres_match_geometry_authority() -> None:
    wheels = WheelPart()
    solver = GeometryEngine.placement_solver(DEFAULT_PARAMETERS)
    assert wheels.left_center == solver.wheel_center("left")
    assert wheels.right_center == solver.wheel_center("right")
    assert wheels.left_center.x_mm == wheels.right_center.x_mm
    assert wheels.left_center.y_mm == -wheels.right_center.y_mm


def test_tray_origin_matches_geometry_authority() -> None:
    tray = TrayPart()
    solver = GeometryEngine.placement_solver(DEFAULT_PARAMETERS)
    assert tray.origin == solver.tray_origin()
    assert tray.dimensions[0] <= DEFAULT_PARAMETERS.envelope.length_mm
    assert tray.dimensions[1] <= DEFAULT_PARAMETERS.envelope.width_mm


def test_base_is_centered_on_robot_frame() -> None:
    base = BasePart()
    envelope = GeometryEngine.robot_envelope(DEFAULT_PARAMETERS).outer_bounding_box
    assert base.bounding_box.origin.x_mm == envelope.origin.x_mm
    assert base.bounding_box.origin.y_mm == envelope.origin.y_mm
    assert base.bounding_box.dimensions == base.dimensions


def test_electronics_centres_match_geometry_authority() -> None:
    electronics = ElectronicsPart()
    solver = GeometryEngine.placement_solver(DEFAULT_PARAMETERS)
    assert electronics.controller_center == solver.motherboard_center()
    assert electronics.battery_center == solver.battery_center()
