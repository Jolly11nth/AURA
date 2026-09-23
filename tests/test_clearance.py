"""Engineering clearance and serviceability invariants for AURA."""

from Core.Geometry import (
    ClearanceStatus,
    GeometryEngine,
    MountingPointName,
    Point3D,
    Vector3D,
)
from Main import build_default_assembly


def test_default_robot_envelope_contains_canonical_internal_components() -> None:
    assembly = build_default_assembly()
    solver = GeometryEngine.clearance_solver(assembly.parameters)
    envelope = GeometryEngine.robot_envelope(assembly.parameters).outer_bounding_box

    for name in ("battery", "motherboard", "tray", "left_wheel", "right_wheel"):
        component = solver.component(name)
        assert envelope.contains_box(component.volumes.occupied)


def test_battery_and_controller_have_defined_service_clearance() -> None:
    assembly = build_default_assembly()
    solver = GeometryEngine.clearance_solver(assembly.parameters)

    battery = solver.component("battery")
    controller = solver.component("motherboard")

    assert solver.minimum_clearance(battery, controller) == (
        assembly.parameters.electronics.service_clearance_mm
    )
    assert not solver.has_collision(battery, controller)


def test_can_place_detects_an_intentional_component_collision() -> None:
    assembly = build_default_assembly()
    solver = GeometryEngine.clearance_solver(assembly.parameters)
    battery = solver.component("battery")
    overlapping_pose = battery.pose.__class__(
        position=battery.pose.position.translate(Vector3D(1.0, 0.0, 0.0)),
        orientation=battery.pose.orientation,
        frame=battery.pose.frame,
    )

    report = solver.can_place(
        battery,
        overlapping_pose,
        existing_components=(battery,),
    )

    assert report.status is ClearanceStatus.FAIL
    assert any("collides with battery" in item.message for item in report.violations)


def test_wheel_motion_envelopes_are_symmetric() -> None:
    assembly = build_default_assembly()
    solver = GeometryEngine.clearance_solver(assembly.parameters)

    left = solver.wheel_motion_envelope("left")
    right = solver.wheel_motion_envelope("right")

    assert left.rotation_envelope.dimensions == right.rotation_envelope.dimensions
    assert left.rotation_envelope.center.x_mm == right.rotation_envelope.center.x_mm
    assert left.rotation_envelope.center.y_mm == -right.rotation_envelope.center.y_mm
    assert left.rotation_envelope.center.z_mm == right.rotation_envelope.center.z_mm


def test_wheel_motion_allowance_is_not_required_body_clearance() -> None:
    assembly = build_default_assembly()
    solver = GeometryEngine.clearance_solver(assembly.parameters)

    for side in ("left", "right"):
        wheel = solver.component(f"{side}_wheel")
        assert wheel.volumes.required_clearance == wheel.volumes.occupied
        assert wheel.volumes.movement != wheel.volumes.required_clearance


def test_tray_motion_envelope_has_explicit_opening_travel() -> None:
    assembly = build_default_assembly()
    solver = GeometryEngine.clearance_solver(assembly.parameters)
    motion = solver.tray_motion_envelope()

    assert motion.closed == solver.component("tray").volumes.occupied
    assert motion.opening_path.dimensions.length_mm == (
        motion.closed.dimensions.length_mm + solver.TRAY_OPEN_DISTANCE_MM
    )
    assert motion.fully_open.origin == Point3D(
        x_mm=motion.closed.origin.x_mm + solver.TRAY_OPEN_DISTANCE_MM,
        y_mm=motion.closed.origin.y_mm,
        z_mm=motion.closed.origin.z_mm,
    )


def test_camera_and_sensor_geometry_use_canonical_mounts() -> None:
    assembly = build_default_assembly()
    engine = GeometryEngine(assembly.parameters)
    placements = engine.placement_solver()

    camera = engine.clearance_solver().component("camera")
    assert camera.pose.position == placements.camera_mount()

    for sensor_name in (
        MountingPointName.FRONT_LEFT_ULTRASONIC.value,
        MountingPointName.FRONT_RIGHT_ULTRASONIC.value,
    ):
        cone = engine.clearance_solver().ultrasonic_detection_cone(sensor_name)
        assert cone.sensor_name == sensor_name
        assert not cone.region.contains_point(placements.sensor_mount(sensor_name))
        assert cone.region.max_point.x_mm == placements.sensor_mount(sensor_name).x_mm - cone.blind_zone_mm


def test_assembly_exposes_one_geometry_validation_report() -> None:
    assembly = build_default_assembly()

    report = assembly.validate_geometry()

    assert report.status in tuple(ClearanceStatus)
    assert report.minimum_distance_mm >= 0.0
    assert report.violations or report.warnings or report.status is ClearanceStatus.PASS
