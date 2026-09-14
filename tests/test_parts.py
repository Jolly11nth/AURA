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


def test_wheel_centres_are_symmetric() -> None:
    wheels = WheelPart()
    assert wheels.left_center.y_mm + wheels.right_center.y_mm == DEFAULT_PARAMETERS.envelope.width_mm


def test_tray_fits_configured_envelope() -> None:
    tray = TrayPart()
    assert tray.dimensions[0] <= DEFAULT_PARAMETERS.envelope.length_mm
    assert tray.dimensions[1] <= DEFAULT_PARAMETERS.envelope.width_mm
