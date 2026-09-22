from Core.Geometry import CoordinateFrame, GeometryEngine, ORIGIN, Point3D
from Main import build_default_assembly


def test_assembly_parts_share_one_parameter_set() -> None:
    assembly = build_default_assembly()

    assert all(part.parameters is assembly.parameters for part in assembly.parts)


def test_part_origins_and_centres_are_geometry_authoritative() -> None:
    assembly = build_default_assembly()
    solver = GeometryEngine.placement_solver(assembly.parameters)
    robot_envelope = GeometryEngine.robot_envelope(assembly.parameters).outer_bounding_box

    assert assembly.base.bounding_box.origin == Point3D(
        robot_envelope.origin.x_mm,
        robot_envelope.origin.y_mm,
        assembly.parameters.envelope.ground_clearance_mm,
    )
    assert assembly.shell.bounding_box.origin == Point3D(
        robot_envelope.origin.x_mm,
        robot_envelope.origin.y_mm,
        assembly.parameters.envelope.ground_clearance_mm,
    )
    assert assembly.top_cover.origin == Point3D(
        robot_envelope.origin.x_mm,
        robot_envelope.origin.y_mm,
        assembly.parameters.envelope.height_mm
        - assembly.parameters.base.floor_thickness_mm,
    )
    assert assembly.tray.origin == solver.tray_origin()
    assert assembly.wheels.left_center == solver.wheel_center("left")
    assert assembly.wheels.right_center == solver.wheel_center("right")
    assert assembly.electronics.controller_center == solver.motherboard_center()
    assert assembly.electronics.battery_center == solver.battery_center()


def test_canonical_frame_origins_transform_to_robot_placements() -> None:
    engine = GeometryEngine()
    solver = engine.placement_solver()
    graph = solver.frame_graph()

    frame_origins = (
        (CoordinateFrame.ROBOT.value, ORIGIN),
        (CoordinateFrame.TRAY.value, solver.tray_origin()),
        ("left_wheel", solver.wheel_center("left")),
        ("right_wheel", solver.wheel_center("right")),
        (CoordinateFrame.CAMERA.value, solver.camera_mount()),
        ("battery", solver.battery_center()),
    )

    for frame, expected_robot_point in frame_origins:
        transformed = graph.transform_point(
            ORIGIN,
            from_frame=frame,
            to_frame=CoordinateFrame.ROBOT.value,
        )
        assert transformed == expected_robot_point


def test_robot_envelope_contains_the_base_and_tray() -> None:
    assembly = build_default_assembly()
    envelope = GeometryEngine.robot_envelope(assembly.parameters).outer_bounding_box

    assert envelope.contains_box(assembly.base.bounding_box)
    tray_box = GeometryEngine.bounding_box_from_origin(
        GeometryEngine.dimensions(*assembly.tray.dimensions),
        assembly.tray.origin,
    )
    assert envelope.contains_box(tray_box)


def test_wheel_packaging_is_symmetric_about_robot_centerline() -> None:
    assembly = build_default_assembly()

    assert assembly.wheels.left_center.x_mm == assembly.wheels.right_center.x_mm
    assert assembly.wheels.left_center.z_mm == assembly.wheels.right_center.z_mm
    assert assembly.wheels.left_center.y_mm == -assembly.wheels.right_center.y_mm
