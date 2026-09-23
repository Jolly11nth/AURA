"""Focused engineering DRC invariants for AURA."""

from Core.Geometry import ClearanceStatus, GeometryEngine
from Main import build_default_assembly


def test_default_geometry_report_has_no_blocking_findings() -> None:
    report = build_default_assembly().validate_geometry()

    assert report.status is not ClearanceStatus.FAIL
    assert not report.violations


def test_default_motion_validation_has_no_blocking_findings() -> None:
    report = GeometryEngine().validate_motion()

    assert report.status is not ClearanceStatus.FAIL
    assert not report.violations


def test_default_serviceability_has_no_blocking_findings() -> None:
    report = GeometryEngine().validate_serviceability()

    assert report.status is not ClearanceStatus.FAIL
    assert not report.violations


def test_critical_component_clearances_are_non_negative() -> None:
    solver = GeometryEngine.clearance_solver()
    names = ("battery", "motherboard", "tray", "left_wheel", "right_wheel", "camera")

    for index, first_name in enumerate(names):
        first = solver.component(first_name)
        for second_name in names[index + 1 :]:
            second = solver.component(second_name)
            assert solver.minimum_clearance(first, second) >= 0.0
