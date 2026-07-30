import pytest

from Core.Geometry import BoundingBox, Dimensions3D, GeometryEngine, ORIGIN, Point3D, Vector3D


def test_point_translation_and_vector_derivation() -> None:
    start = Point3D(x_mm=1.0, y_mm=2.0, z_mm=3.0)
    vector = Vector3D(x_mm=4.0, y_mm=5.0, z_mm=6.0)

    moved = start.translate(vector)

    assert moved == Point3D(x_mm=5.0, y_mm=7.0, z_mm=9.0)
    assert start.vector_to(moved) == vector


def test_vector_magnitude_and_scaling() -> None:
    vector = Vector3D(x_mm=3.0, y_mm=4.0, z_mm=12.0)

    assert vector.magnitude_mm == 13.0
    assert vector.scaled(2.0) == Vector3D(x_mm=6.0, y_mm=8.0, z_mm=24.0)


def test_dimensions_are_positive_and_report_volume() -> None:
    dimensions = Dimensions3D(length_mm=2.0, width_mm=3.0, height_mm=4.0)

    assert dimensions.volume_mm3 == 24.0
    assert dimensions.fits_within(Dimensions3D(length_mm=3.0, width_mm=3.0, height_mm=4.0))

    with pytest.raises(ValueError, match="length_mm must be positive"):
        Dimensions3D(length_mm=0.0, width_mm=1.0, height_mm=1.0)


def test_bounding_box_spatial_queries() -> None:
    box = BoundingBox(
        origin=ORIGIN,
        dimensions=Dimensions3D(length_mm=10.0, width_mm=20.0, height_mm=30.0),
    )

    assert box.max_point == Point3D(x_mm=10.0, y_mm=20.0, z_mm=30.0)
    assert box.center == Point3D(x_mm=5.0, y_mm=10.0, z_mm=15.0)
    assert box.contains_point(Point3D(x_mm=5.0, y_mm=5.0, z_mm=5.0))
    assert box.contains_box(
        BoundingBox(
            origin=Point3D(x_mm=1.0, y_mm=1.0, z_mm=1.0),
            dimensions=Dimensions3D(length_mm=2.0, width_mm=2.0, height_mm=2.0),
        )
    )
    assert box.intersects(
        BoundingBox(
            origin=Point3D(x_mm=9.0, y_mm=19.0, z_mm=29.0),
            dimensions=Dimensions3D(length_mm=2.0, width_mm=2.0, height_mm=2.0),
        )
    )


def test_geometry_engine_creates_primitives() -> None:
    dimensions = GeometryEngine.dimensions(length_mm=1.0, width_mm=2.0, height_mm=3.0)
    box = GeometryEngine.bounding_box_from_origin(dimensions)

    assert box.origin == ORIGIN
    assert box.dimensions == dimensions


def test_robot_envelope_derives_from_parameters() -> None:
    from Core.Parameters import DEFAULT_PARAMETERS

    envelope = GeometryEngine.robot_envelope(DEFAULT_PARAMETERS)

    assert envelope.outer_dimensions.length_mm == DEFAULT_PARAMETERS.envelope.length_mm
    assert envelope.shell_thickness_mm == DEFAULT_PARAMETERS.shell.wall_thickness_mm
    assert envelope.ground_clearance_mm == DEFAULT_PARAMETERS.envelope.ground_clearance_mm
    assert envelope.outer_radius_mm == envelope.outer_diameter_mm / 2.0
    assert envelope.inner_radius_mm == envelope.inner_diameter_mm / 2.0
    assert envelope.internal_volume_mm3 == envelope.inner_dimensions.volume_mm3
    assert envelope.usable_envelope.origin.z_mm == DEFAULT_PARAMETERS.envelope.ground_clearance_mm


def test_placement_solver_exposes_coordinate_frames_and_wheel_centers() -> None:
    from Core.Geometry import CoordinateFrame
    from Core.Parameters import DEFAULT_PARAMETERS

    solver = GeometryEngine.placement_solver(DEFAULT_PARAMETERS)
    frames = solver.coordinate_frames()

    assert set(frames) == set(CoordinateFrame)
    assert frames[CoordinateFrame.ROBOT].origin == ORIGIN
    assert solver.wheel_center("left").y_mm == DEFAULT_PARAMETERS.wheels.track_width_mm / 2.0
    assert solver.wheel_center("right").y_mm == -(DEFAULT_PARAMETERS.wheels.track_width_mm / 2.0)

    with pytest.raises(ValueError, match="side"):
        solver.wheel_center("middle")


def test_placement_solver_centralizes_mounting_points() -> None:
    from Core.Geometry import CoordinateFrame, MountingPointName
    from Core.Parameters import DEFAULT_PARAMETERS

    solver = GeometryEngine.placement_solver(DEFAULT_PARAMETERS)
    mounting_points = solver.mounting_points()

    assert set(mounting_points) == set(MountingPointName)
    assert mounting_points[MountingPointName.CAMERA].point == solver.camera_mount()
    assert mounting_points[MountingPointName.BATTERY].point == solver.battery_center()
    assert mounting_points[MountingPointName.LEFT_WHEEL].frame == CoordinateFrame.ROBOT
    assert solver.sensor_mount("front_left_ultrasonic") == mounting_points[
        MountingPointName.FRONT_LEFT_ULTRASONIC
    ].point

    with pytest.raises(KeyError, match="Unknown sensor"):
        solver.sensor_mount("unknown")


def test_rotation_from_euler_rotates_about_z_axis() -> None:
    from math import pi

    from Core.Geometry import EulerAngles

    rotation = GeometryEngine.rotation_from_euler(EulerAngles(yaw_rad=pi / 2.0))
    rotated = rotation.apply(Vector3D(x_mm=1.0, y_mm=0.0, z_mm=0.0))

    assert rotated.x_mm == pytest.approx(0.0)
    assert rotated.y_mm == pytest.approx(1.0)
    assert rotated.z_mm == pytest.approx(0.0)


def test_rigid_transform_inversion_round_trips_point() -> None:
    transform = GeometryEngine.rigid_transform(
        "robot",
        "camera",
        Vector3D(x_mm=10.0, y_mm=20.0, z_mm=30.0),
    )
    camera_point = Point3D(x_mm=1.0, y_mm=2.0, z_mm=3.0)

    robot_point = transform.apply_point(camera_point)
    round_trip = transform.inverse().apply_point(robot_point)

    assert round_trip == camera_point


def test_rigid_transform_composition_validates_frame_relationships() -> None:
    robot_from_tray = GeometryEngine.rigid_transform(
        "robot", "tray", Vector3D(x_mm=1.0, y_mm=0.0, z_mm=0.0)
    )
    tray_from_battery = GeometryEngine.rigid_transform(
        "tray", "battery", Vector3D(x_mm=2.0, y_mm=0.0, z_mm=0.0)
    )

    robot_from_battery = robot_from_tray.compose(tray_from_battery)

    assert robot_from_battery.parent_frame == "robot"
    assert robot_from_battery.child_frame == "battery"
    assert robot_from_battery.apply_point(ORIGIN) == Point3D(x_mm=3.0, y_mm=0.0, z_mm=0.0)

    with pytest.raises(ValueError, match="composition"):
        tray_from_battery.compose(robot_from_tray)


def test_geometry_engine_frame_lookup_and_conversion_api() -> None:
    engine = GeometryEngine()
    camera_pose = engine.camera_pose()

    assert engine.robot_frame().name == "robot"
    assert engine.camera_frame().name == "camera"
    assert camera_pose.frame == "robot"
    assert camera_pose.position == engine.transform_point(ORIGIN, from_frame="camera", to_frame="robot")
    assert engine.transform_vector(
        Vector3D(x_mm=1.0, y_mm=2.0, z_mm=3.0), from_frame="camera", to_frame="robot"
    ) == Vector3D(x_mm=1.0, y_mm=2.0, z_mm=3.0)


def test_frame_graph_validation_rejects_missing_parent_and_cycles() -> None:
    from Core.Geometry import FrameGraph, FrameNode

    with pytest.raises(ValueError, match="unknown parent"):
        FrameGraph(
            nodes={
                "world": FrameNode("world", None, None),
                "camera": FrameNode(
                    "camera",
                    "missing",
                    GeometryEngine.rigid_transform("missing", "camera"),
                ),
            }
        )

    with pytest.raises(ValueError, match="Circular frame dependency"):
        FrameGraph(
            nodes={
                "a": FrameNode("a", "b", GeometryEngine.rigid_transform("b", "a")),
                "b": FrameNode("b", "a", GeometryEngine.rigid_transform("a", "b")),
            }
        )


def test_clearance_solver_detects_component_collisions_and_clearance() -> None:
    from Core.Geometry import ClearanceStatus

    solver = GeometryEngine.clearance_solver()
    battery = solver.component("battery")
    motherboard = solver.component("motherboard")

    assert not solver.has_collision(battery, motherboard)
    assert solver.minimum_clearance(battery, motherboard) >= 0.0

    overlapping_pose = motherboard.pose.__class__(
        position=battery.pose.position,
        orientation=motherboard.pose.orientation,
        frame=motherboard.pose.frame,
    )
    report = solver.can_place(motherboard, overlapping_pose, existing_components=(battery,))

    assert report.status is ClearanceStatus.FAIL
    assert report.minimum_distance_mm == 0.0
    assert report.violations


def test_clearance_solver_reports_wheel_and_tray_motion_envelopes() -> None:
    solver = GeometryEngine.clearance_solver()

    left_wheel = solver.wheel_motion_envelope("left")
    tray_motion = solver.tray_motion_envelope()

    assert left_wheel.rotation_envelope.dimensions.length_mm > 0.0
    assert left_wheel.suspension_allowance_mm > 0.0
    assert tray_motion.opening_path.dimensions.length_mm > tray_motion.closed.dimensions.length_mm
    assert tray_motion.fully_open.origin.x_mm > tray_motion.closed.origin.x_mm


def test_clearance_solver_represents_camera_and_sensor_clearance() -> None:
    solver = GeometryEngine.clearance_solver()

    camera = solver.camera_visibility_cone()
    ultrasonic = solver.ultrasonic_detection_cone("front_left_ultrasonic")

    assert camera.near_plane_mm < camera.far_plane_mm
    assert camera.region.dimensions.length_mm > 0.0
    assert ultrasonic.blind_zone_mm < ultrasonic.maximum_range_mm
    assert ultrasonic.region.dimensions.length_mm > 0.0


def test_clearance_solver_generates_service_and_validation_reports() -> None:
    from Core.Geometry import ClearanceStatus

    engine = GeometryEngine()
    solver = engine.clearance_solver()

    service_zones = solver.service_zones()
    service_report = engine.validate_serviceability()
    motion_report = engine.validate_motion()
    robot_report = engine.validate_robot()

    assert {"battery_removal", "tray_slide_out", "usb_access", "cooling_air"}.issubset(
        service_zones
    )
    assert service_report.status in {ClearanceStatus.PASS, ClearanceStatus.WARNING}
    assert motion_report.status in {ClearanceStatus.PASS, ClearanceStatus.WARNING, ClearanceStatus.FAIL}
    assert robot_report.recommendations == tuple(
        finding.recommendation
        for finding in (*robot_report.violations, *robot_report.warnings)
        if finding.recommendation is not None
    )
