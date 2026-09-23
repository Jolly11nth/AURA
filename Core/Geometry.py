"""FreeCAD-independent geometric source of truth for AURA.

Every spatial calculation in AURA must originate here. Part, assembly,
simulation, manufacturing, export, and future Digital Twin modules should use
these primitives instead of calculating positions, dimensions, offsets, or
clearances independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import cos, sin, sqrt
from typing import Final, Mapping, Sequence

from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class Point3D:
    """A Cartesian point in AURA model space.

    Units:
        Millimetres along the X, Y, and Z axes.
    Purpose:
        Represent an absolute location. Use ``translate`` to derive new points
        rather than performing ad hoc coordinate arithmetic in downstream
        modules.
    """

    x_mm: float
    y_mm: float
    z_mm: float

    def translate(self, vector: Vector3D) -> "Point3D":
        """Return a point moved by ``vector``."""
        return Point3D(
            x_mm=self.x_mm + vector.x_mm,
            y_mm=self.y_mm + vector.y_mm,
            z_mm=self.z_mm + vector.z_mm,
        )

    def vector_to(self, other: "Point3D") -> Vector3D:
        """Return the vector from this point to ``other``."""
        return Vector3D(
            x_mm=other.x_mm - self.x_mm,
            y_mm=other.y_mm - self.y_mm,
            z_mm=other.z_mm - self.z_mm,
        )


@dataclass(frozen=True, slots=True)
class Vector3D:
    """A displacement vector in AURA model space.

    Units:
        Millimetres along the X, Y, and Z axes.
    Purpose:
        Represent offsets, translations, and direction-independent clearances
        without implying an absolute location.
    """

    x_mm: float
    y_mm: float
    z_mm: float

    @property
    def magnitude_mm(self) -> float:
        """Return the Euclidean length of the vector in millimetres."""
        return sqrt((self.x_mm**2) + (self.y_mm**2) + (self.z_mm**2))

    def scaled(self, factor: float) -> "Vector3D":
        """Return a vector multiplied by ``factor``."""
        return Vector3D(
            x_mm=self.x_mm * factor,
            y_mm=self.y_mm * factor,
            z_mm=self.z_mm * factor,
        )


class CoordinateFrame(StrEnum):
    """Canonical AURA coordinate frames.

    Convention:
        The robot frame is centered on the ground-plane midpoint of the robot
        footprint. +Z points upward, +X points toward the rear of the robot in
        the 2D planning view, +Y points to the robot left, and -Y points to the
        robot right. Other frames are named anchors for future transforms while
        Sprint 2 keeps all coordinates expressed in robot-frame millimetres.
    """

    WORLD = "world"
    ROBOT = "robot"
    SHELL = "shell"
    BASE = "base"
    WHEEL = "wheel"
    TRAY = "tray"
    ELECTRONICS = "electronics"
    SENSOR = "sensor"
    CAMERA = "camera"


class MountingPointName(StrEnum):
    """Canonical permanent mounting coordinate names owned by geometry."""

    LEFT_WHEEL = "left_wheel"
    RIGHT_WHEEL = "right_wheel"
    BATTERY = "battery"
    MOTHERBOARD = "motherboard"
    LEFT_SPEAKER = "left_speaker"
    RIGHT_SPEAKER = "right_speaker"
    DISPLAY = "display"
    USB_PORT = "usb_port"
    FRONT_LEFT_LED = "front_left_led"
    FRONT_RIGHT_LED = "front_right_led"
    FRONT_LEFT_ULTRASONIC = "front_left_ultrasonic"
    FRONT_RIGHT_ULTRASONIC = "front_right_ultrasonic"
    CAMERA = "camera"
    LEFT_DOCKING_CONTACT = "left_docking_contact"
    RIGHT_DOCKING_CONTACT = "right_docking_contact"


@dataclass(frozen=True, slots=True)
class CoordinateFrameDefinition:
    """Named reference frame with an origin expressed in robot coordinates.

    Units:
        Millimetres.
    Purpose:
        Make reference frames explicit before Sprint 3 introduces transforms.
        Downstream modules should carry the frame with coordinates instead of
        assuming a global coordinate system.
    """

    frame: CoordinateFrame
    origin: Point3D


@dataclass(frozen=True, slots=True)
class Dimensions3D:
    """Positive length, width, and height dimensions.

    Units:
        Millimetres.
    Purpose:
        Represent derived or configured spatial extents. All dimensional volume
        and fit calculations should use this class.
    Constraints:
        Length, width, and height must be positive.
    """

    length_mm: float
    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        _require_positive("length_mm", self.length_mm)
        _require_positive("width_mm", self.width_mm)
        _require_positive("height_mm", self.height_mm)

    @property
    def volume_mm3(self) -> float:
        """Return the enclosed rectangular volume in cubic millimetres."""
        return self.length_mm * self.width_mm * self.height_mm

    def fits_within(self, other: "Dimensions3D") -> bool:
        """Return whether this dimension set fits inside ``other``."""
        return (
            self.length_mm <= other.length_mm
            and self.width_mm <= other.width_mm
            and self.height_mm <= other.height_mm
        )


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Axis-aligned bounding box in AURA model space.

    Units:
        Millimetres.
    Purpose:
        Centralize spatial extents and containment checks for later robot
        envelope, placement, clearance, and collision engines.
    Constraints:
        ``dimensions`` must be positive; ``origin`` is the minimum X/Y/Z corner.
    """

    origin: Point3D
    dimensions: Dimensions3D

    @property
    def min_point(self) -> Point3D:
        """Return the minimum X/Y/Z corner."""
        return self.origin

    @property
    def max_point(self) -> Point3D:
        """Return the maximum X/Y/Z corner."""
        return Point3D(
            x_mm=self.origin.x_mm + self.dimensions.length_mm,
            y_mm=self.origin.y_mm + self.dimensions.width_mm,
            z_mm=self.origin.z_mm + self.dimensions.height_mm,
        )

    @property
    def center(self) -> Point3D:
        """Return the geometric center of this bounding box."""
        return Point3D(
            x_mm=self.origin.x_mm + (self.dimensions.length_mm / 2.0),
            y_mm=self.origin.y_mm + (self.dimensions.width_mm / 2.0),
            z_mm=self.origin.z_mm + (self.dimensions.height_mm / 2.0),
        )

    @property
    def volume_mm3(self) -> float:
        """Return the enclosed rectangular volume in cubic millimetres."""
        return self.dimensions.volume_mm3

    def translated(self, vector: Vector3D) -> "BoundingBox":
        """Return this bounding box moved by ``vector``."""
        return BoundingBox(origin=self.origin.translate(vector), dimensions=self.dimensions)

    def contains_point(self, point: Point3D) -> bool:
        """Return whether ``point`` lies inside or on this bounding box."""
        maximum = self.max_point
        return (
            self.origin.x_mm <= point.x_mm <= maximum.x_mm
            and self.origin.y_mm <= point.y_mm <= maximum.y_mm
            and self.origin.z_mm <= point.z_mm <= maximum.z_mm
        )

    def contains_box(self, other: "BoundingBox") -> bool:
        """Return whether ``other`` is fully contained by this bounding box."""
        return self.contains_point(other.min_point) and self.contains_point(other.max_point)

    def intersects(self, other: "BoundingBox") -> bool:
        """Return whether this bounding box intersects ``other``."""
        self_max = self.max_point
        other_max = other.max_point
        return not (
            self_max.x_mm < other.origin.x_mm
            or other_max.x_mm < self.origin.x_mm
            or self_max.y_mm < other.origin.y_mm
            or other_max.y_mm < self.origin.y_mm
            or self_max.z_mm < other.origin.z_mm
            or other_max.z_mm < self.origin.z_mm
        )


@dataclass(frozen=True, slots=True)
class EulerAngles:
    """Roll, pitch, and yaw orientation angles.

    Units:
        Radians.
    Purpose:
        Provide a human-readable rotation input format while allowing the public
        API to evolve toward quaternions without changing transform consumers.
    """

    roll_rad: float = 0.0
    pitch_rad: float = 0.0
    yaw_rad: float = 0.0


@dataclass(frozen=True, slots=True)
class Quaternion:
    """Quaternion rotation representation foundation.

    Purpose:
        Reserve a robotics-standard orientation representation for future
        interpolation and sensor-fusion work. Sprint 3 validates and stores the
        value; conversion-heavy quaternion workflows can be added later without
        changing the public transform API.
    """

    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __post_init__(self) -> None:
        if self.norm == 0.0:
            raise ValueError("quaternion norm must be positive")

    @property
    def norm(self) -> float:
        """Return the quaternion norm."""
        return sqrt((self.w**2) + (self.x**2) + (self.y**2) + (self.z**2))


@dataclass(frozen=True, slots=True)
class RotationMatrix3x3:
    """Immutable 3x3 rotation matrix.

    Purpose:
        Store the canonical computation form used by ``Rotation3D`` and
        ``RigidTransform``. Rows are stored in row-major order.
    """

    rows: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]

    def apply(self, vector: Vector3D) -> Vector3D:
        """Rotate ``vector`` by this matrix."""
        return Vector3D(
            x_mm=(self.rows[0][0] * vector.x_mm)
            + (self.rows[0][1] * vector.y_mm)
            + (self.rows[0][2] * vector.z_mm),
            y_mm=(self.rows[1][0] * vector.x_mm)
            + (self.rows[1][1] * vector.y_mm)
            + (self.rows[1][2] * vector.z_mm),
            z_mm=(self.rows[2][0] * vector.x_mm)
            + (self.rows[2][1] * vector.y_mm)
            + (self.rows[2][2] * vector.z_mm),
        )

    def compose(self, other: "RotationMatrix3x3") -> "RotationMatrix3x3":
        """Return matrix multiplication ``self * other``."""
        rows = tuple(
            tuple(sum(self.rows[row][idx] * other.rows[idx][col] for idx in range(3)) for col in range(3))
            for row in range(3)
        )
        return RotationMatrix3x3(rows=rows)  # type: ignore[arg-type]

    def transpose(self) -> "RotationMatrix3x3":
        """Return the inverse of an orthonormal rotation matrix."""
        return RotationMatrix3x3(
            rows=tuple(tuple(self.rows[row][col] for row in range(3)) for col in range(3))  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class Rotation3D:
    """Immutable orientation abstraction used by all transforms.

    Purpose:
        Hide the internal rotation representation from consumers so Euler angles,
        quaternions, and matrices can coexist behind one API.
    """

    matrix: RotationMatrix3x3

    @classmethod
    def identity(cls) -> "Rotation3D":
        """Return the identity rotation."""
        return cls(
            RotationMatrix3x3(
                rows=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
            )
        )

    @classmethod
    def from_euler(cls, angles: EulerAngles) -> "Rotation3D":
        """Create a rotation from roll, pitch, and yaw radians.

        The matrix follows the standard intrinsic XYZ convention equivalent to
        yaw around Z, pitch around Y, and roll around X applied as ``Rz * Ry * Rx``.
        """
        cr = cos(angles.roll_rad)
        sr = sin(angles.roll_rad)
        cp = cos(angles.pitch_rad)
        sp = sin(angles.pitch_rad)
        cy = cos(angles.yaw_rad)
        sy = sin(angles.yaw_rad)
        return cls(
            RotationMatrix3x3(
                rows=(
                    (cy * cp, (cy * sp * sr) - (sy * cr), (cy * sp * cr) + (sy * sr)),
                    (sy * cp, (sy * sp * sr) + (cy * cr), (sy * sp * cr) - (cy * sr)),
                    (-sp, cp * sr, cp * cr),
                )
            )
        )

    def apply(self, vector: Vector3D) -> Vector3D:
        """Rotate ``vector``."""
        return self.matrix.apply(vector)

    def inverse(self) -> "Rotation3D":
        """Return the inverse rotation."""
        return Rotation3D(self.matrix.transpose())

    def compose(self, other: "Rotation3D") -> "Rotation3D":
        """Return ``self`` followed by ``other`` in matrix-composition form."""
        return Rotation3D(self.matrix.compose(other.matrix))


@dataclass(frozen=True, slots=True)
class Pose3D:
    """Position and orientation in an explicit coordinate frame."""

    position: Point3D
    orientation: Rotation3D
    frame: str


@dataclass(frozen=True, slots=True)
class RigidTransform:
    """Rigid transform relating a child frame to a parent frame.

    Semantics:
        ``apply_point`` maps a point expressed in ``child_frame`` into
        ``parent_frame``. The translation is the child-frame origin expressed in
        parent-frame coordinates.
    """

    translation: Vector3D
    rotation: Rotation3D
    parent_frame: str
    child_frame: str

    def apply_point(self, point: Point3D) -> Point3D:
        """Transform ``point`` from ``child_frame`` into ``parent_frame``."""
        rotated = self.rotation.apply(Vector3D(point.x_mm, point.y_mm, point.z_mm))
        return Point3D(
            x_mm=rotated.x_mm + self.translation.x_mm,
            y_mm=rotated.y_mm + self.translation.y_mm,
            z_mm=rotated.z_mm + self.translation.z_mm,
        )

    def apply_vector(self, vector: Vector3D) -> Vector3D:
        """Rotate ``vector`` from ``child_frame`` into ``parent_frame``."""
        return self.rotation.apply(vector)

    def inverse(self) -> "RigidTransform":
        """Return the inverse transform from parent to child."""
        inverse_rotation = self.rotation.inverse()
        inverse_translation = inverse_rotation.apply(self.translation.scaled(-1.0))
        return RigidTransform(
            translation=inverse_translation,
            rotation=inverse_rotation,
            parent_frame=self.child_frame,
            child_frame=self.parent_frame,
        )

    def compose(self, other: "RigidTransform") -> "RigidTransform":
        """Compose this transform with ``other``.

        ``self`` must map ``child -> parent`` and ``other`` must map
        ``grandchild -> child``. The result maps ``grandchild -> parent``.
        """
        if self.child_frame != other.parent_frame:
            raise ValueError(
                "transform composition requires self.child_frame to match other.parent_frame"
            )
        rotated_translation = self.rotation.apply(other.translation)
        return RigidTransform(
            translation=Vector3D(
                x_mm=rotated_translation.x_mm + self.translation.x_mm,
                y_mm=rotated_translation.y_mm + self.translation.y_mm,
                z_mm=rotated_translation.z_mm + self.translation.z_mm,
            ),
            rotation=self.rotation.compose(other.rotation),
            parent_frame=self.parent_frame,
            child_frame=other.child_frame,
        )


@dataclass(frozen=True, slots=True)
class FrameNode:
    """A coordinate-frame node and its transform to its parent frame."""

    name: str
    parent: str | None
    transform_to_parent: RigidTransform | None

    def __post_init__(self) -> None:
        if self.parent is None and self.transform_to_parent is not None:
            raise ValueError("root frame cannot define transform_to_parent")
        if self.parent is not None and self.transform_to_parent is None:
            raise ValueError("non-root frame must define transform_to_parent")
        if self.transform_to_parent is not None:
            if self.transform_to_parent.parent_frame != self.parent:
                raise ValueError("transform parent_frame must match node parent")
            if self.transform_to_parent.child_frame != self.name:
                raise ValueError("transform child_frame must match node name")


@dataclass(frozen=True, slots=True)
class FrameGraph:
    """Validated tree of coordinate frames with conversion helpers."""

    nodes: Mapping[str, FrameNode]

    def __post_init__(self) -> None:
        _validate_frame_graph(self.nodes)

    def frame(self, name: str) -> FrameNode:
        """Return a frame node by name."""
        try:
            return self.nodes[name]
        except KeyError as exc:
            raise KeyError(f"Unknown coordinate frame {name!r}") from exc

    def transform(self, from_frame: str, to_frame: str) -> RigidTransform:
        """Return a transform that maps points from ``from_frame`` to ``to_frame``."""
        if from_frame == to_frame:
            return RigidTransform(
                translation=Vector3D(0.0, 0.0, 0.0),
                rotation=Rotation3D.identity(),
                parent_frame=to_frame,
                child_frame=from_frame,
            )
        root_from = self._transform_to_root(from_frame)
        root_to = self._transform_to_root(to_frame)
        return root_to.inverse().compose(root_from)

    def transform_point(self, point: Point3D, *, from_frame: str, to_frame: str) -> Point3D:
        """Transform ``point`` between named frames."""
        return self.transform(from_frame, to_frame).apply_point(point)

    def transform_vector(self, vector: Vector3D, *, from_frame: str, to_frame: str) -> Vector3D:
        """Transform ``vector`` between named frames."""
        return self.transform(from_frame, to_frame).apply_vector(vector)

    def _transform_to_root(self, frame_name: str) -> RigidTransform:
        node = self.frame(frame_name)
        if node.parent is None:
            return RigidTransform(
                translation=Vector3D(0.0, 0.0, 0.0),
                rotation=Rotation3D.identity(),
                parent_frame=frame_name,
                child_frame=frame_name,
            )
        if node.transform_to_parent is None:
            raise ValueError(f"Frame {frame_name!r} is missing transform_to_parent")
        parent_transform = self._transform_to_root(node.parent)
        if parent_transform.parent_frame == parent_transform.child_frame:
            return node.transform_to_parent
        return parent_transform.compose(node.transform_to_parent)


@dataclass(frozen=True, slots=True)
class RobotEnvelope:
    """Authoritative robot envelope derived from ``Core.Parameters``.

    Units:
        Millimetres for dimensions and cubic millimetres for volumes.
    Purpose:
        Centralize derived envelope properties so CAD, simulation, manufacturing,
        and Digital Twin layers do not recompute body geometry independently.
    Assumptions:
        The outer footprint is represented by the configured rectangular body;
        ``outer_diameter_mm`` is the maximum footprint span and
        ``outer_radius_mm`` is half that span for radial clearance checks.
    """

    outer_dimensions: Dimensions3D
    shell_thickness_mm: float
    ground_clearance_mm: float

    @property
    def outer_diameter_mm(self) -> float:
        """Return the maximum plan-view span of the robot envelope."""
        return max(self.outer_dimensions.length_mm, self.outer_dimensions.width_mm)

    @property
    def outer_radius_mm(self) -> float:
        """Return half of ``outer_diameter_mm`` for radial clearance checks."""
        return self.outer_diameter_mm / 2.0

    @property
    def inner_dimensions(self) -> Dimensions3D:
        """Return shell interior dimensions after shell thickness is removed."""
        shell_allowance_mm = self.shell_thickness_mm * 2.0
        return Dimensions3D(
            length_mm=self.outer_dimensions.length_mm - shell_allowance_mm,
            width_mm=self.outer_dimensions.width_mm - shell_allowance_mm,
            height_mm=self.outer_dimensions.height_mm - self.ground_clearance_mm,
        )

    @property
    def inner_diameter_mm(self) -> float:
        """Return the maximum plan-view span of the usable shell interior."""
        return max(self.inner_dimensions.length_mm, self.inner_dimensions.width_mm)

    @property
    def inner_radius_mm(self) -> float:
        """Return half of ``inner_diameter_mm``."""
        return self.inner_diameter_mm / 2.0

    @property
    def internal_volume_mm3(self) -> float:
        """Return the rectangular interior volume available inside the shell."""
        return self.inner_dimensions.volume_mm3

    @property
    def usable_envelope(self) -> BoundingBox:
        """Return the usable internal bounding box in robot coordinates."""
        dimensions = self.inner_dimensions
        return BoundingBox(
            origin=Point3D(
                x_mm=-(dimensions.length_mm / 2.0),
                y_mm=-(dimensions.width_mm / 2.0),
                z_mm=self.ground_clearance_mm,
            ),
            dimensions=dimensions,
        )

    @property
    def outer_bounding_box(self) -> BoundingBox:
        """Return the full robot bounding box in robot coordinates."""
        return BoundingBox(
            origin=Point3D(
                x_mm=-(self.outer_dimensions.length_mm / 2.0),
                y_mm=-(self.outer_dimensions.width_mm / 2.0),
                z_mm=0.0,
            ),
            dimensions=self.outer_dimensions,
        )


@dataclass(frozen=True, slots=True)
class MountingPoint:
    """Permanent mounting coordinate owned by the geometry layer.

    Units:
        Millimetres in the declared coordinate frame.
    Purpose:
        Provide one canonical source for part placement and future CAD features.
    """

    name: MountingPointName
    frame: CoordinateFrame
    point: Point3D


@dataclass(frozen=True, slots=True)
class PlacementSolver:
    """Canonical placement service for AURA permanent mounting points.

    Parts and assemblies should request coordinates here instead of deriving
    their own offsets. Sprint 2 exposes deterministic anchor points; later
    sprints can replace formulas with transform-aware placement while preserving
    the public API.
    """

    parameters: AURAParameters = DEFAULT_PARAMETERS

    @property
    def robot_envelope(self) -> RobotEnvelope:
        """Return the derived robot envelope for these parameters."""
        return GeometryEngine.robot_envelope(self.parameters)

    def coordinate_frames(self) -> Mapping[CoordinateFrame, CoordinateFrameDefinition]:
        """Return canonical frame origins expressed in robot coordinates."""
        tray_origin = self.tray_origin()
        return {
            CoordinateFrame.WORLD: CoordinateFrameDefinition(CoordinateFrame.WORLD, ORIGIN),
            CoordinateFrame.ROBOT: CoordinateFrameDefinition(CoordinateFrame.ROBOT, ORIGIN),
            CoordinateFrame.SHELL: CoordinateFrameDefinition(
                CoordinateFrame.SHELL, self.robot_envelope.outer_bounding_box.origin
            ),
            CoordinateFrame.BASE: CoordinateFrameDefinition(
                CoordinateFrame.BASE,
                Point3D(
                    x_mm=-(self.parameters.envelope.length_mm / 2.0),
                    y_mm=-(self.parameters.envelope.width_mm / 2.0),
                    z_mm=0.0,
                ),
            ),
            CoordinateFrame.WHEEL: CoordinateFrameDefinition(CoordinateFrame.WHEEL, ORIGIN),
            CoordinateFrame.TRAY: CoordinateFrameDefinition(CoordinateFrame.TRAY, tray_origin),
            CoordinateFrame.ELECTRONICS: CoordinateFrameDefinition(
                CoordinateFrame.ELECTRONICS, self.battery_center()
            ),
            CoordinateFrame.SENSOR: CoordinateFrameDefinition(CoordinateFrame.SENSOR, ORIGIN),
            CoordinateFrame.CAMERA: CoordinateFrameDefinition(CoordinateFrame.CAMERA, self.camera_mount()),
        }

    def wheel_center(self, side: str) -> Point3D:
        """Return the left or right wheel center in robot coordinates."""
        normalized = side.lower()
        if normalized not in {"left", "right"}:
            raise ValueError("side must be 'left' or 'right'")
        y_sign = 1.0 if normalized == "left" else -1.0
        return Point3D(
            x_mm=self.parameters.wheels.axle_offset_from_rear_mm
            - (self.parameters.envelope.length_mm / 2.0),
            y_mm=y_sign * (self.parameters.wheels.track_width_mm / 2.0),
            z_mm=self.parameters.wheels.diameter_mm / 2.0,
        )

    def tray_origin(self) -> Point3D:
        """Return the tray minimum-corner origin in robot coordinates."""
        return Point3D(
            x_mm=-(self.parameters.tray.length_mm / 2.0),
            y_mm=-(self.parameters.tray.width_mm / 2.0),
            z_mm=self.parameters.base.floor_thickness_mm + self.parameters.electronics.service_clearance_mm,
        )

    def battery_center(self) -> Point3D:
        """Return the battery bay center in robot coordinates."""
        tray_origin = self.tray_origin()
        return Point3D(
            x_mm=tray_origin.x_mm + (self.parameters.electronics.battery_bay_length_mm / 2.0),
            y_mm=0.0,
            z_mm=tray_origin.z_mm + (self.parameters.tray.depth_mm / 2.0),
        )

    def motherboard_center(self) -> Point3D:
        """Return the controller or motherboard bay center in robot coordinates."""
        tray_origin = self.tray_origin()
        return Point3D(
            x_mm=tray_origin.x_mm
            + self.parameters.electronics.battery_bay_length_mm
            + self.parameters.electronics.service_clearance_mm
            + (self.parameters.electronics.controller_bay_length_mm / 2.0),
            y_mm=0.0,
            z_mm=tray_origin.z_mm + (self.parameters.tray.depth_mm / 2.0),
        )

    def sensor_mount(self, name: str) -> Point3D:
        """Return a named ultrasonic sensor or LED mounting point."""
        try:
            mounting_name = MountingPointName(name)
        except ValueError as exc:
            raise KeyError(f"Unknown sensor mounting point {name!r}") from exc
        points = self.mounting_points()
        if mounting_name not in points:
            raise KeyError(f"Unknown sensor mounting point {name!r}")
        return points[mounting_name].point

    def camera_mount(self) -> Point3D:
        """Return the canonical front camera mounting point."""
        return Point3D(
            x_mm=-(self.parameters.envelope.length_mm / 2.0),
            y_mm=0.0,
            z_mm=self.parameters.envelope.height_mm - self.parameters.shell.lid_clearance_mm,
        )

    def mounting_points(self) -> Mapping[MountingPointName, MountingPoint]:
        """Return all canonical permanent mounting points."""
        front_x = -(self.parameters.envelope.length_mm / 2.0)
        rear_x = self.parameters.envelope.length_mm / 2.0
        half_inner_width = self.robot_envelope.inner_dimensions.width_mm / 2.0
        upper_z = self.parameters.envelope.height_mm - self.parameters.shell.lid_clearance_mm
        tray_z = self.tray_origin().z_mm + (self.parameters.tray.depth_mm / 2.0)
        side_y = half_inner_width - self.parameters.electronics.service_clearance_mm
        return {
            MountingPointName.LEFT_WHEEL: MountingPoint(
                MountingPointName.LEFT_WHEEL, CoordinateFrame.ROBOT, self.wheel_center("left")
            ),
            MountingPointName.RIGHT_WHEEL: MountingPoint(
                MountingPointName.RIGHT_WHEEL, CoordinateFrame.ROBOT, self.wheel_center("right")
            ),
            MountingPointName.BATTERY: MountingPoint(
                MountingPointName.BATTERY, CoordinateFrame.ROBOT, self.battery_center()
            ),
            MountingPointName.MOTHERBOARD: MountingPoint(
                MountingPointName.MOTHERBOARD, CoordinateFrame.ROBOT, self.motherboard_center()
            ),
            MountingPointName.LEFT_SPEAKER: MountingPoint(
                MountingPointName.LEFT_SPEAKER,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=0.0, y_mm=side_y, z_mm=tray_z),
            ),
            MountingPointName.RIGHT_SPEAKER: MountingPoint(
                MountingPointName.RIGHT_SPEAKER,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=0.0, y_mm=-side_y, z_mm=tray_z),
            ),
            MountingPointName.DISPLAY: MountingPoint(
                MountingPointName.DISPLAY,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=front_x, y_mm=0.0, z_mm=upper_z),
            ),
            MountingPointName.USB_PORT: MountingPoint(
                MountingPointName.USB_PORT,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=rear_x, y_mm=0.0, z_mm=tray_z),
            ),
            MountingPointName.FRONT_LEFT_LED: MountingPoint(
                MountingPointName.FRONT_LEFT_LED,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=front_x, y_mm=side_y, z_mm=upper_z),
            ),
            MountingPointName.FRONT_RIGHT_LED: MountingPoint(
                MountingPointName.FRONT_RIGHT_LED,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=front_x, y_mm=-side_y, z_mm=upper_z),
            ),
            MountingPointName.FRONT_LEFT_ULTRASONIC: MountingPoint(
                MountingPointName.FRONT_LEFT_ULTRASONIC,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=front_x, y_mm=side_y / 2.0, z_mm=upper_z),
            ),
            MountingPointName.FRONT_RIGHT_ULTRASONIC: MountingPoint(
                MountingPointName.FRONT_RIGHT_ULTRASONIC,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=front_x, y_mm=-(side_y / 2.0), z_mm=upper_z),
            ),
            MountingPointName.CAMERA: MountingPoint(
                MountingPointName.CAMERA, CoordinateFrame.ROBOT, self.camera_mount()
            ),
            MountingPointName.LEFT_DOCKING_CONTACT: MountingPoint(
                MountingPointName.LEFT_DOCKING_CONTACT,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=rear_x, y_mm=side_y / 2.0, z_mm=self.parameters.base.floor_thickness_mm),
            ),
            MountingPointName.RIGHT_DOCKING_CONTACT: MountingPoint(
                MountingPointName.RIGHT_DOCKING_CONTACT,
                CoordinateFrame.ROBOT,
                Point3D(x_mm=rear_x, y_mm=-(side_y / 2.0), z_mm=self.parameters.base.floor_thickness_mm),
            ),
        }


class ClearanceStatus(StrEnum):
    """Structured result status for geometric clearance checks."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class ClearanceVolumeKind(StrEnum):
    """Required geometric volume categories for mounted components."""

    OCCUPIED = "occupied"
    REQUIRED_CLEARANCE = "required_clearance"
    SERVICE = "service"
    MOVEMENT = "movement"


@dataclass(frozen=True, slots=True)
class ClearanceVolume:
    """Occupied, clearance, service, and movement volumes for one component.

    Units:
        Bounding boxes are expressed in millimetres in robot coordinates unless a
        ``Pose3D`` explicitly requests conversion through the transform engine.
    Purpose:
        Ensure AURA validates the component body plus the additional space needed
        for removal, wiring, movement, and assembly rather than checking only the
        physical body volume.
    """

    occupied: BoundingBox
    required_clearance: BoundingBox
    service: BoundingBox
    movement: BoundingBox

    def by_kind(self, kind: ClearanceVolumeKind) -> BoundingBox:
        """Return a volume by semantic kind."""
        if kind is ClearanceVolumeKind.OCCUPIED:
            return self.occupied
        if kind is ClearanceVolumeKind.REQUIRED_CLEARANCE:
            return self.required_clearance
        if kind is ClearanceVolumeKind.SERVICE:
            return self.service
        return self.movement


@dataclass(frozen=True, slots=True)
class ComponentGeometry:
    """Geometric description used by the clearance solver."""

    name: str
    pose: Pose3D
    volumes: ClearanceVolume


@dataclass(frozen=True, slots=True)
class ViewCone:
    """Axis-aligned first-pass camera visibility region.

    Sprint 4 stores a bounding region for a future true frustum. This remains
    geometric and FreeCAD-independent while exposing near/far plane metadata.
    """

    frame: str
    near_plane_mm: float
    far_plane_mm: float
    horizontal_fov_deg: float
    vertical_fov_deg: float
    region: BoundingBox


@dataclass(frozen=True, slots=True)
class SensorDetectionCone:
    """Axis-aligned ultrasonic sensing volume with blind-zone metadata."""

    sensor_name: str
    frame: str
    blind_zone_mm: float
    maximum_range_mm: float
    housing_clearance_mm: float
    region: BoundingBox


@dataclass(frozen=True, slots=True)
class WheelMotionEnvelope:
    """Wheel occupied and movement envelopes for rotation and future suspension."""

    wheel_name: str
    rotation_envelope: BoundingBox
    suspension_allowance_mm: float
    turning_clearance_mm: float
    chassis_interference: bool


@dataclass(frozen=True, slots=True)
class TrayMotionEnvelope:
    """Tray closed, opening-path, and fully-open envelopes."""

    closed: BoundingBox
    opening_path: BoundingBox
    fully_open: BoundingBox


@dataclass(frozen=True, slots=True)
class ClearanceFinding:
    """One structured clearance validation finding."""

    severity: ClearanceStatus
    message: str
    component: str | None = None
    recommendation: str | None = None


@dataclass(frozen=True, slots=True)
class ClearanceReport:
    """Structured result for clearance, motion, and serviceability validation."""

    status: ClearanceStatus
    minimum_distance_mm: float
    violations: tuple[ClearanceFinding, ...] = ()
    warnings: tuple[ClearanceFinding, ...] = ()
    recommendations: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        """Return whether the report has no blocking violations."""
        return self.status is not ClearanceStatus.FAIL


class ClearanceSolver:
    """Geometric DRC subsystem for AURA clearance and serviceability checks.

    Scope:
        Axis-aligned collision, minimum-clearance, motion-envelope, visibility,
        sensor, assembly, and service-zone validation. This does not perform
        physics, structural analysis, dynamics, path planning, FEA, or CAD work.
    """

    CAMERA_NEAR_PLANE_MM: Final[float] = 30.0
    CAMERA_FAR_PLANE_MM: Final[float] = 1500.0
    CAMERA_HORIZONTAL_FOV_DEG: Final[float] = 70.0
    CAMERA_VERTICAL_FOV_DEG: Final[float] = 45.0
    ULTRASONIC_BLIND_ZONE_MM: Final[float] = 25.0
    ULTRASONIC_MAX_RANGE_MM: Final[float] = 2000.0
    SENSOR_HOUSING_CLEARANCE_MM: Final[float] = 8.0
    WHEEL_SUSPENSION_ALLOWANCE_MM: Final[float] = 8.0
    WHEEL_TURNING_CLEARANCE_MM: Final[float] = 6.0
    TRAY_OPEN_DISTANCE_MM: Final[float] = 160.0
    EXTERNAL_SERVICE_ZONES: Final[frozenset[str]] = frozenset(
        {"usb_access", "power_switch", "speaker_vent"}
    )
    EXTERNAL_COMPONENTS: Final[frozenset[str]] = frozenset({"camera"})
    INTENTIONAL_CONTAINMENT_PAIRS: Final[frozenset[frozenset[str]]] = frozenset(
        {
            frozenset({"tray", "battery"}),
            frozenset({"tray", "motherboard"}),
        }
    )

    def __init__(self, parameters: AURAParameters = DEFAULT_PARAMETERS) -> None:
        self.parameters = parameters
        self._placement_solver = PlacementSolver(parameters=parameters)
        self._robot_envelope = GeometryEngine.robot_envelope(parameters)

    def component(self, name: str) -> ComponentGeometry:
        """Return canonical component geometry by name."""
        normalized = name.lower()
        if normalized == "battery":
            return self._battery_component()
        if normalized in {"motherboard", "controller"}:
            return self._motherboard_component()
        if normalized == "tray":
            return self._tray_component()
        if normalized == "left_wheel":
            return self._wheel_component("left")
        if normalized == "right_wheel":
            return self._wheel_component("right")
        if normalized == "camera":
            return self._camera_component()
        raise KeyError(f"Unknown component geometry {name!r}")

    def can_place(
        self,
        component: ComponentGeometry,
        pose: Pose3D,
        existing_components: Sequence[ComponentGeometry] = (),
    ) -> ClearanceReport:
        """Return whether ``component`` can be placed at ``pose`` without collisions."""
        placed = self._component_at_pose(component, pose)
        findings: list[ClearanceFinding] = []
        minimum = self._minimum_distance_to_envelope(placed.volumes.required_clearance)
        outer_envelope = self._robot_envelope.outer_bounding_box
        if placed.name in self.EXTERNAL_COMPONENTS:
            if not outer_envelope.intersects(placed.volumes.occupied):
                findings.append(
                    ClearanceFinding(
                        ClearanceStatus.FAIL,
                        "external component is detached from robot envelope",
                        placed.name,
                        "Keep the external component physically mounted to the robot envelope.",
                    )
                )
        elif not outer_envelope.contains_box(placed.volumes.required_clearance):
            findings.append(
                ClearanceFinding(
                    ClearanceStatus.FAIL,
                    "component clearance volume exceeds robot envelope",
                    placed.name,
                    "Move the component inward or reduce its required clearance volume.",
                )
            )
        for other in existing_components:
            if self.has_collision(placed, other):
                findings.append(
                    ClearanceFinding(
                        ClearanceStatus.FAIL,
                        f"component collides with {other.name}",
                        placed.name,
                        "Adjust placement through Core.Geometry placement rules.",
                    )
                )
            minimum = min(minimum, self.minimum_clearance(placed, other))
        return self._report_from_findings(findings, minimum)

    def has_collision(self, component_a: ComponentGeometry, component_b: ComponentGeometry) -> bool:
        """Return whether occupied volumes intersect."""
        return component_a.volumes.occupied.intersects(component_b.volumes.occupied)

    def minimum_clearance(self, component_a: ComponentGeometry, component_b: ComponentGeometry) -> float:
        """Return the minimum distance between occupied component volumes."""
        return _minimum_box_distance(component_a.volumes.occupied, component_b.volumes.occupied)

    def wheel_motion_envelope(self, side: str) -> WheelMotionEnvelope:
        """Return the wheel rotation and clearance envelope for ``side``."""
        component = self._wheel_component(side)
        rotation = component.volumes.movement
        # The wheel may use the space immediately outside the body envelope while turning.
        # Chassis interference therefore checks the physical wheel envelope, not its
        # external motion allowance.
        chassis_interference = not self._robot_envelope.outer_bounding_box.contains_box(
            component.volumes.occupied
        )
        return WheelMotionEnvelope(
            wheel_name=f"{side.lower()}_wheel",
            rotation_envelope=rotation,
            suspension_allowance_mm=self.WHEEL_SUSPENSION_ALLOWANCE_MM,
            turning_clearance_mm=self.WHEEL_TURNING_CLEARANCE_MM,
            chassis_interference=chassis_interference,
        )

    def tray_motion_envelope(self) -> TrayMotionEnvelope:
        """Return the tray closed, opening path, and fully open volumes."""
        tray = self._tray_component().volumes.occupied
        opening = BoundingBox(
            origin=tray.origin,
            dimensions=Dimensions3D(
                length_mm=tray.dimensions.length_mm + self.TRAY_OPEN_DISTANCE_MM,
                width_mm=tray.dimensions.width_mm,
                height_mm=tray.dimensions.height_mm,
            ),
        )
        fully_open = tray.translated(Vector3D(self.TRAY_OPEN_DISTANCE_MM, 0.0, 0.0))
        return TrayMotionEnvelope(closed=tray, opening_path=opening, fully_open=fully_open)

    def camera_visibility_cone(self) -> ViewCone:
        """Return the initial geometric camera visibility region."""
        mount = self._placement_solver.camera_mount()
        region = BoundingBox(
            origin=Point3D(
                x_mm=mount.x_mm - self.CAMERA_FAR_PLANE_MM,
                y_mm=-(self._robot_envelope.outer_dimensions.width_mm / 2.0),
                z_mm=self.parameters.envelope.ground_clearance_mm,
            ),
            dimensions=Dimensions3D(
                length_mm=self.CAMERA_FAR_PLANE_MM - self.CAMERA_NEAR_PLANE_MM,
                width_mm=self._robot_envelope.outer_dimensions.width_mm,
                height_mm=self.parameters.envelope.height_mm - self.parameters.envelope.ground_clearance_mm,
            ),
        )
        return ViewCone(
            frame=CoordinateFrame.ROBOT.value,
            near_plane_mm=self.CAMERA_NEAR_PLANE_MM,
            far_plane_mm=self.CAMERA_FAR_PLANE_MM,
            horizontal_fov_deg=self.CAMERA_HORIZONTAL_FOV_DEG,
            vertical_fov_deg=self.CAMERA_VERTICAL_FOV_DEG,
            region=region,
        )

    def ultrasonic_detection_cone(self, sensor_name: str) -> SensorDetectionCone:
        """Return the geometric detection region for an ultrasonic sensor."""
        mount = self._placement_solver.sensor_mount(sensor_name)
        region = BoundingBox(
            origin=Point3D(
                x_mm=mount.x_mm - self.ULTRASONIC_MAX_RANGE_MM,
                y_mm=mount.y_mm - self.SENSOR_HOUSING_CLEARANCE_MM,
                z_mm=mount.z_mm - self.SENSOR_HOUSING_CLEARANCE_MM,
            ),
            dimensions=Dimensions3D(
                length_mm=self.ULTRASONIC_MAX_RANGE_MM - self.ULTRASONIC_BLIND_ZONE_MM,
                width_mm=self.SENSOR_HOUSING_CLEARANCE_MM * 2.0,
                height_mm=self.SENSOR_HOUSING_CLEARANCE_MM * 2.0,
            ),
        )
        return SensorDetectionCone(
            sensor_name=sensor_name,
            frame=CoordinateFrame.ROBOT.value,
            blind_zone_mm=self.ULTRASONIC_BLIND_ZONE_MM,
            maximum_range_mm=self.ULTRASONIC_MAX_RANGE_MM,
            housing_clearance_mm=self.SENSOR_HOUSING_CLEARANCE_MM,
            region=region,
        )

    def service_zones(self) -> Mapping[str, BoundingBox]:
        """Return canonical service zones for maintenance and assembly checks."""
        battery = self._battery_component().volumes.service
        tray_motion = self.tray_motion_envelope()
        usb = self._service_box_around_point(
            self._placement_solver.mounting_points()[MountingPointName.USB_PORT].point,
            Dimensions3D(50.0, 40.0, 30.0),
        )
        power_switch = self._service_box_around_point(
            self._placement_solver.mounting_points()[MountingPointName.DISPLAY].point,
            Dimensions3D(60.0, 30.0, 30.0),
        )
        speaker_vent = self._service_box_around_point(
            self._placement_solver.mounting_points()[MountingPointName.LEFT_SPEAKER].point,
            Dimensions3D(40.0, 40.0, 30.0),
        )
        cooling_air = self._robot_envelope.usable_envelope
        return {
            "battery_removal": battery,
            "tray_slide_out": tray_motion.opening_path,
            "usb_access": usb,
            "power_switch": power_switch,
            "speaker_vent": speaker_vent,
            "cooling_air": cooling_air,
        }

    def validate_robot(self) -> ClearanceReport:
        """Validate default component clearances, motion envelopes, and service zones."""
        components = [
            self._battery_component(),
            self._motherboard_component(),
            self._tray_component(),
            self._wheel_component("left"),
            self._wheel_component("right"),
            self._camera_component(),
        ]
        findings: list[ClearanceFinding] = []
        minimum = self._minimum_distance_to_envelope(self._robot_envelope.usable_envelope)
        for index, component in enumerate(components):
            placement_report = self.can_place(component, component.pose)
            findings.extend(placement_report.violations)
            minimum = min(minimum, placement_report.minimum_distance_mm)
            for other in components[index + 1 :]:
                distance = self.minimum_clearance(component, other)
                minimum = min(minimum, distance)
                pair = frozenset({component.name, other.name})
                if self.has_collision(component, other) and pair not in self.INTENTIONAL_CONTAINMENT_PAIRS:
                    findings.append(
                        ClearanceFinding(
                            ClearanceStatus.FAIL,
                            f"{component.name} collides with {other.name}",
                            component.name,
                            "Resolve placement through Core.Geometry placement rules.",
                        )
                    )
        findings.extend(self.validate_motion().violations)
        service_report = self.validate_serviceability()
        return self._report_from_findings(
            [*findings, *service_report.violations], minimum, warnings=list(service_report.warnings)
        )

    def validate_component(self, component: ComponentGeometry) -> ClearanceReport:
        """Validate a single component against the robot envelope."""
        return self.can_place(component, component.pose)

    def validate_serviceability(self) -> ClearanceReport:
        """Validate that service zones remain represented and envelope-aware."""
        findings: list[ClearanceFinding] = []
        warnings: list[ClearanceFinding] = []
        minimum = self._minimum_distance_to_envelope(self._robot_envelope.usable_envelope)
        for name, zone in self.service_zones().items():
            intersects_envelope = self._robot_envelope.outer_bounding_box.intersects(zone)
            if not intersects_envelope and name not in self.EXTERNAL_SERVICE_ZONES:
                findings.append(
                    ClearanceFinding(
                        ClearanceStatus.FAIL,
                        f"service zone {name} is unreachable from robot envelope",
                        name,
                        "Re-anchor the service zone through Core.Geometry.",
                    )
                )
            if not self._robot_envelope.outer_bounding_box.contains_box(zone):
                warnings.append(
                    ClearanceFinding(
                        ClearanceStatus.WARNING,
                        f"service zone {name} extends outside robot envelope",
                        name,
                        "Confirm this is intentional for external service access.",
                    )
                )
            minimum = min(minimum, self._minimum_distance_to_envelope(zone))
        return self._report_from_findings(findings, minimum, warnings=warnings)

    def validate_motion(self) -> ClearanceReport:
        """Validate wheel rotation and tray opening motion envelopes."""
        findings: list[ClearanceFinding] = []
        for side in ("left", "right"):
            wheel = self.wheel_motion_envelope(side)
            if wheel.chassis_interference:
                findings.append(
                    ClearanceFinding(
                        ClearanceStatus.FAIL,
                        f"{wheel.wheel_name} motion envelope exceeds chassis",
                        wheel.wheel_name,
                        "Increase chassis width/height or reduce wheel envelope.",
                    )
                )
        tray_motion = self.tray_motion_envelope()
        if not self._robot_envelope.outer_bounding_box.intersects(tray_motion.opening_path):
            findings.append(
                ClearanceFinding(
                    ClearanceStatus.FAIL,
                    "tray opening path is disconnected from robot envelope",
                    "tray",
                    "Recompute tray origin and opening path through Core.Geometry.",
                )
            )
        return self._report_from_findings(findings, 0.0)

    def _battery_component(self) -> ComponentGeometry:
        center = self._placement_solver.battery_center()
        dimensions = Dimensions3D(
            self.parameters.electronics.battery_bay_length_mm,
            self.parameters.electronics.battery_bay_width_mm,
            self.parameters.tray.depth_mm,
        )
        occupied = _box_centered_on(center, dimensions)
        clearance = _expanded_box(occupied, self.parameters.electronics.service_clearance_mm)
        service = _expanded_box(occupied, self.parameters.electronics.service_clearance_mm * 2.0)
        return ComponentGeometry(
            name="battery",
            pose=Pose3D(center, Rotation3D.identity(), CoordinateFrame.ROBOT.value),
            volumes=ClearanceVolume(occupied, clearance, service, service),
        )

    def _motherboard_component(self) -> ComponentGeometry:
        center = self._placement_solver.motherboard_center()
        dimensions = Dimensions3D(
            self.parameters.electronics.controller_bay_length_mm,
            self.parameters.electronics.controller_bay_width_mm,
            self.parameters.tray.depth_mm,
        )
        occupied = _box_centered_on(center, dimensions)
        clearance = _expanded_box(occupied, self.parameters.electronics.service_clearance_mm)
        service = _expanded_box(occupied, self.parameters.electronics.service_clearance_mm * 1.5)
        return ComponentGeometry(
            name="motherboard",
            pose=Pose3D(center, Rotation3D.identity(), CoordinateFrame.ROBOT.value),
            volumes=ClearanceVolume(occupied, clearance, service, service),
        )

    def _tray_component(self) -> ComponentGeometry:
        occupied = BoundingBox(
            origin=self._placement_solver.tray_origin(),
            dimensions=Dimensions3D(
                self.parameters.tray.length_mm,
                self.parameters.tray.width_mm,
                self.parameters.tray.depth_mm,
            ),
        )
        return ComponentGeometry(
            name="tray",
            pose=Pose3D(occupied.origin, Rotation3D.identity(), CoordinateFrame.ROBOT.value),
            volumes=ClearanceVolume(occupied, occupied, occupied, occupied),
        )

    def _wheel_component(self, side: str) -> ComponentGeometry:
        center = self._placement_solver.wheel_center(side)
        dimensions = Dimensions3D(
            length_mm=self.parameters.wheels.diameter_mm,
            width_mm=self.parameters.wheels.width_mm,
            height_mm=self.parameters.wheels.diameter_mm,
        )
        occupied = _box_centered_on(center, dimensions)
        movement = _expanded_box(
            occupied, self.WHEEL_SUSPENSION_ALLOWANCE_MM + self.WHEEL_TURNING_CLEARANCE_MM
        )
        return ComponentGeometry(
            name=f"{side.lower()}_wheel",
            pose=Pose3D(center, Rotation3D.identity(), CoordinateFrame.ROBOT.value),
            volumes=ClearanceVolume(occupied, movement, movement, movement),
        )

    def _camera_component(self) -> ComponentGeometry:
        mount = self._placement_solver.camera_mount()
        occupied = _box_centered_on(mount, Dimensions3D(30.0, 30.0, 20.0))
        clearance = _expanded_box(occupied, self.SENSOR_HOUSING_CLEARANCE_MM)
        service = _expanded_box(occupied, self.SENSOR_HOUSING_CLEARANCE_MM * 2.0)
        return ComponentGeometry(
            name="camera",
            pose=Pose3D(mount, Rotation3D.identity(), CoordinateFrame.ROBOT.value),
            volumes=ClearanceVolume(occupied, clearance, service, self.camera_visibility_cone().region),
        )

    def _component_at_pose(self, component: ComponentGeometry, pose: Pose3D) -> ComponentGeometry:
        offset = component.pose.position.vector_to(pose.position)
        return ComponentGeometry(
            name=component.name,
            pose=pose,
            volumes=ClearanceVolume(
                occupied=component.volumes.occupied.translated(offset),
                required_clearance=component.volumes.required_clearance.translated(offset),
                service=component.volumes.service.translated(offset),
                movement=component.volumes.movement.translated(offset),
            ),
        )

    def _service_box_around_point(self, point: Point3D, dimensions: Dimensions3D) -> BoundingBox:
        return _box_centered_on(point, dimensions)

    def _minimum_distance_to_envelope(self, box: BoundingBox) -> float:
        if self._robot_envelope.outer_bounding_box.contains_box(box):
            return min(
                box.origin.x_mm - self._robot_envelope.outer_bounding_box.origin.x_mm,
                box.origin.y_mm - self._robot_envelope.outer_bounding_box.origin.y_mm,
                box.origin.z_mm - self._robot_envelope.outer_bounding_box.origin.z_mm,
                self._robot_envelope.outer_bounding_box.max_point.x_mm - box.max_point.x_mm,
                self._robot_envelope.outer_bounding_box.max_point.y_mm - box.max_point.y_mm,
                self._robot_envelope.outer_bounding_box.max_point.z_mm - box.max_point.z_mm,
            )
        return _minimum_box_distance(self._robot_envelope.outer_bounding_box, box)

    def _report_from_findings(
        self,
        violations: Sequence[ClearanceFinding],
        minimum_distance_mm: float,
        *,
        warnings: Sequence[ClearanceFinding] = (),
    ) -> ClearanceReport:
        status = ClearanceStatus.FAIL if violations else ClearanceStatus.PASS
        if status is ClearanceStatus.PASS and warnings:
            status = ClearanceStatus.WARNING
        recommendations = tuple(
            finding.recommendation
            for finding in (*violations, *warnings)
            if finding.recommendation is not None
        )
        return ClearanceReport(
            status=status,
            minimum_distance_mm=minimum_distance_mm,
            violations=tuple(violations),
            warnings=tuple(warnings),
            recommendations=recommendations,
        )


class GeometryEngine:
    """Central entry point for current and future AURA spatial calculations.

    Sprint 1 scope:
        Construct and validate core math primitives.
    Sprint 2 scope:
        Derive robot envelopes, coordinate frames, and canonical mounting
        placements from ``Core.Parameters``.
    Sprint 3 scope:
        Provide rotation abstractions, rigid transforms, frame graph validation,
        pose construction, and frame conversion APIs.
    Future sprints:
        Transform-aware clearance, collision helpers, optimization, and freeze
        validation.
    FreeCAD independence:
        The engine uses only standard Python types and the primitives in this
        module, so CAD adapters can consume results without creating a dependency
        from Core to FreeCAD.
    """

    def __init__(self, parameters: AURAParameters = DEFAULT_PARAMETERS) -> None:
        self.parameters = parameters
        self._placement_solver = PlacementSolver(parameters=parameters)
        self._frame_graph = self._build_frame_graph()

    @staticmethod
    def point(x_mm: float, y_mm: float, z_mm: float) -> Point3D:
        """Create an absolute point in millimetres."""
        return Point3D(x_mm=x_mm, y_mm=y_mm, z_mm=z_mm)

    @staticmethod
    def vector(x_mm: float, y_mm: float, z_mm: float) -> Vector3D:
        """Create a displacement vector in millimetres."""
        return Vector3D(x_mm=x_mm, y_mm=y_mm, z_mm=z_mm)

    @staticmethod
    def dimensions(length_mm: float, width_mm: float, height_mm: float) -> Dimensions3D:
        """Create positive three-dimensional extents in millimetres."""
        return Dimensions3D(length_mm=length_mm, width_mm=width_mm, height_mm=height_mm)

    @staticmethod
    def bounding_box(origin: Point3D, dimensions: Dimensions3D) -> BoundingBox:
        """Create an axis-aligned bounding box from an origin and dimensions."""
        return BoundingBox(origin=origin, dimensions=dimensions)

    @classmethod
    def bounding_box_from_origin(cls, dimensions: Dimensions3D) -> BoundingBox:
        """Create a bounding box anchored at the model origin."""
        return cls.bounding_box(origin=ORIGIN, dimensions=dimensions)

    @staticmethod
    def robot_envelope(parameters: AURAParameters = DEFAULT_PARAMETERS) -> RobotEnvelope:
        """Derive the authoritative robot envelope from parameters."""
        return RobotEnvelope(
            outer_dimensions=Dimensions3D(
                length_mm=parameters.envelope.length_mm,
                width_mm=parameters.envelope.width_mm,
                height_mm=parameters.envelope.height_mm,
            ),
            shell_thickness_mm=parameters.shell.wall_thickness_mm,
            ground_clearance_mm=parameters.envelope.ground_clearance_mm,
        )

    @staticmethod
    def placement_solver(parameters: AURAParameters = DEFAULT_PARAMETERS) -> PlacementSolver:
        """Create a placement solver for a parameter set."""
        return PlacementSolver(parameters=parameters)


    @staticmethod
    def clearance_solver(parameters: AURAParameters = DEFAULT_PARAMETERS) -> ClearanceSolver:
        """Create a clearance solver for a parameter set."""
        return ClearanceSolver(parameters=parameters)

    def validate_robot(self) -> ClearanceReport:
        """Validate robot-level clearance, motion, and serviceability."""
        return self.clearance_solver(self.parameters).validate_robot()

    def validate_component(self, component: ComponentGeometry) -> ClearanceReport:
        """Validate one component against the robot envelope."""
        return self.clearance_solver(self.parameters).validate_component(component)

    def validate_serviceability(self) -> ClearanceReport:
        """Validate service-zone accessibility."""
        return self.clearance_solver(self.parameters).validate_serviceability()

    def validate_motion(self) -> ClearanceReport:
        """Validate geometric motion envelopes."""
        return self.clearance_solver(self.parameters).validate_motion()

    @staticmethod
    def rotation_from_euler(angles: EulerAngles) -> Rotation3D:
        """Create a rotation from Euler angles."""
        return Rotation3D.from_euler(angles)

    @staticmethod
    def identity_rotation() -> Rotation3D:
        """Return the identity rotation."""
        return Rotation3D.identity()

    @staticmethod
    def rigid_transform(
        parent_frame: str,
        child_frame: str,
        translation: Vector3D | None = None,
        rotation: Rotation3D | None = None,
    ) -> RigidTransform:
        """Create a rigid transform from a child frame into a parent frame."""
        return RigidTransform(
            translation=translation or Vector3D(0.0, 0.0, 0.0),
            rotation=rotation or Rotation3D.identity(),
            parent_frame=parent_frame,
            child_frame=child_frame,
        )

    def robot_frame(self) -> FrameNode:
        """Return the robot frame node."""
        return self._frame_graph.frame(CoordinateFrame.ROBOT.value)

    def camera_frame(self) -> FrameNode:
        """Return the camera frame node."""
        return self._frame_graph.frame(CoordinateFrame.CAMERA.value)

    def camera_pose(self) -> Pose3D:
        """Return the camera pose expressed in the robot frame."""
        return Pose3D(
            position=self._placement_solver.camera_mount(),
            orientation=Rotation3D.identity(),
            frame=CoordinateFrame.ROBOT.value,
        )

    def transform(self, from_frame: str, to_frame: str) -> RigidTransform:
        """Return a transform that maps coordinates from one frame to another."""
        return self._frame_graph.transform(from_frame=from_frame, to_frame=to_frame)

    def transform_point(self, point: Point3D, *, from_frame: str, to_frame: str) -> Point3D:
        """Transform ``point`` from ``from_frame`` into ``to_frame``."""
        return self._frame_graph.transform_point(point, from_frame=from_frame, to_frame=to_frame)

    def transform_vector(self, vector: Vector3D, *, from_frame: str, to_frame: str) -> Vector3D:
        """Transform ``vector`` from ``from_frame`` into ``to_frame``."""
        return self._frame_graph.transform_vector(vector, from_frame=from_frame, to_frame=to_frame)

    @property
    def frame_graph(self) -> FrameGraph:
        """Return the validated frame graph."""
        return self._frame_graph

    def _build_frame_graph(self) -> FrameGraph:
        placements = self._placement_solver
        robot_to_world = self.rigid_transform(
            CoordinateFrame.WORLD.value, CoordinateFrame.ROBOT.value
        )
        shell_origin = placements.robot_envelope.outer_bounding_box.origin
        tray_origin = placements.tray_origin()
        nodes = {
            CoordinateFrame.WORLD.value: FrameNode(
                name=CoordinateFrame.WORLD.value,
                parent=None,
                transform_to_parent=None,
            ),
            CoordinateFrame.ROBOT.value: FrameNode(
                name=CoordinateFrame.ROBOT.value,
                parent=CoordinateFrame.WORLD.value,
                transform_to_parent=robot_to_world,
            ),
            CoordinateFrame.BASE.value: FrameNode(
                name=CoordinateFrame.BASE.value,
                parent=CoordinateFrame.ROBOT.value,
                transform_to_parent=self.rigid_transform(
                    CoordinateFrame.ROBOT.value,
                    CoordinateFrame.BASE.value,
                    Vector3D(
                        x_mm=-(self.parameters.envelope.length_mm / 2.0),
                        y_mm=-(self.parameters.envelope.width_mm / 2.0),
                        z_mm=0.0,
                    ),
                ),
            ),
            CoordinateFrame.SHELL.value: FrameNode(
                name=CoordinateFrame.SHELL.value,
                parent=CoordinateFrame.ROBOT.value,
                transform_to_parent=self.rigid_transform(
                    CoordinateFrame.ROBOT.value,
                    CoordinateFrame.SHELL.value,
                    Vector3D(shell_origin.x_mm, shell_origin.y_mm, shell_origin.z_mm),
                ),
            ),
            "left_wheel": FrameNode(
                name="left_wheel",
                parent=CoordinateFrame.ROBOT.value,
                transform_to_parent=self.rigid_transform(
                    CoordinateFrame.ROBOT.value,
                    "left_wheel",
                    _point_as_vector(placements.wheel_center("left")),
                ),
            ),
            "right_wheel": FrameNode(
                name="right_wheel",
                parent=CoordinateFrame.ROBOT.value,
                transform_to_parent=self.rigid_transform(
                    CoordinateFrame.ROBOT.value,
                    "right_wheel",
                    _point_as_vector(placements.wheel_center("right")),
                ),
            ),
            CoordinateFrame.TRAY.value: FrameNode(
                name=CoordinateFrame.TRAY.value,
                parent=CoordinateFrame.ROBOT.value,
                transform_to_parent=self.rigid_transform(
                    CoordinateFrame.ROBOT.value,
                    CoordinateFrame.TRAY.value,
                    Vector3D(tray_origin.x_mm, tray_origin.y_mm, tray_origin.z_mm),
                ),
            ),
            "battery": FrameNode(
                name="battery",
                parent=CoordinateFrame.TRAY.value,
                transform_to_parent=self.rigid_transform(
                    CoordinateFrame.TRAY.value,
                    "battery",
                    placements.tray_origin().vector_to(placements.battery_center()),
                ),
            ),
            CoordinateFrame.CAMERA.value: FrameNode(
                name=CoordinateFrame.CAMERA.value,
                parent=CoordinateFrame.ROBOT.value,
                transform_to_parent=self.rigid_transform(
                    CoordinateFrame.ROBOT.value,
                    CoordinateFrame.CAMERA.value,
                    _point_as_vector(placements.camera_mount()),
                ),
            ),
            CoordinateFrame.SENSOR.value: FrameNode(
                name=CoordinateFrame.SENSOR.value,
                parent=CoordinateFrame.ROBOT.value,
                transform_to_parent=self.rigid_transform(
                    CoordinateFrame.ROBOT.value,
                    CoordinateFrame.SENSOR.value,
                ),
            ),
        }
        return FrameGraph(nodes=nodes)


# Backward-compatible alias from the initial scaffold.
BoxEnvelope = Dimensions3D
ORIGIN: Final[Point3D] = Point3D(x_mm=0.0, y_mm=0.0, z_mm=0.0)




def _box_centered_on(center: Point3D, dimensions: Dimensions3D) -> BoundingBox:
    return BoundingBox(
        origin=Point3D(
            x_mm=center.x_mm - (dimensions.length_mm / 2.0),
            y_mm=center.y_mm - (dimensions.width_mm / 2.0),
            z_mm=center.z_mm - (dimensions.height_mm / 2.0),
        ),
        dimensions=dimensions,
    )


def _expanded_box(box: BoundingBox, allowance_mm: float) -> BoundingBox:
    _require_non_negative("allowance_mm", allowance_mm)
    growth = allowance_mm * 2.0
    return BoundingBox(
        origin=Point3D(
            x_mm=box.origin.x_mm - allowance_mm,
            y_mm=box.origin.y_mm - allowance_mm,
            z_mm=box.origin.z_mm - allowance_mm,
        ),
        dimensions=Dimensions3D(
            length_mm=box.dimensions.length_mm + growth,
            width_mm=box.dimensions.width_mm + growth,
            height_mm=box.dimensions.height_mm + growth,
        ),
    )


def _minimum_box_distance(box_a: BoundingBox, box_b: BoundingBox) -> float:
    if box_a.intersects(box_b):
        return 0.0
    a_max = box_a.max_point
    b_max = box_b.max_point
    dx = max(box_a.origin.x_mm - b_max.x_mm, box_b.origin.x_mm - a_max.x_mm, 0.0)
    dy = max(box_a.origin.y_mm - b_max.y_mm, box_b.origin.y_mm - a_max.y_mm, 0.0)
    dz = max(box_a.origin.z_mm - b_max.z_mm, box_b.origin.z_mm - a_max.z_mm, 0.0)
    return sqrt((dx**2) + (dy**2) + (dz**2))


def _point_as_vector(point: Point3D) -> Vector3D:
    return Vector3D(point.x_mm, point.y_mm, point.z_mm)


def _validate_frame_graph(nodes: Mapping[str, FrameNode]) -> None:
    if not nodes:
        raise ValueError("frame graph must contain at least one frame")
    for name, node in nodes.items():
        if name != node.name:
            raise ValueError("frame graph keys must match node names")
        if node.parent is not None and node.parent not in nodes:
            raise ValueError(f"Frame {node.name!r} references unknown parent {node.parent!r}")
        _detect_frame_cycle(node.name, nodes, path=())
    roots = [node.name for node in nodes.values() if node.parent is None]
    if len(roots) != 1:
        raise ValueError("frame graph must contain exactly one root frame")


def _detect_frame_cycle(name: str, nodes: Mapping[str, FrameNode], *, path: Sequence[str]) -> None:
    if name in path:
        cycle = " -> ".join((*path, name))
        raise ValueError(f"Circular frame dependency detected: {cycle}")
    node = nodes[name]
    if node.parent is not None:
        _detect_frame_cycle(node.parent, nodes, path=(*path, name))


def _require_positive(name: str, value: float) -> None:
    if value <= 0.0:
        raise ValueError(f"{name} must be positive")


def _require_non_negative(name: str, value: float) -> None:
    if value < 0.0:
        raise ValueError(f"{name} must be non-negative")