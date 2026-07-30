# AURA

Autonomous Universal Robotic Assistant (AURA) is a modular robotics software framework scaffold for parametric CAD, simulation, manufacturing, export, and future Digital Twin integration.

## Architecture

```text
AURA/
├── Core/
│   ├── Parameters.py
│   ├── Geometry.py
│   ├── Materials.py
│   └── Utilities.py
├── Parts/
│   ├── Base.py
│   ├── Shell.py
│   ├── TopCover.py
│   ├── Tray.py
│   ├── Wheels.py
│   └── Electronics.py
├── Assembly/
│   └── Assembly.py
├── Manufacturing/
│   ├── BOM.py
│   └── Drawings.py
├── Simulation/
│   └── Simulation.py
├── Export/
│   ├── STEP.py
│   ├── STL.py
│   └── TechDraw.py
└── Main.py
```

## Engineering Principles

- Python 3.12+
- Strong typing and immutable dataclass configuration
- Single source of truth for engineering parameters in `Core/Parameters.py`
- FreeCAD-independent core modules
- Modular architecture with no circular dependencies
- Unit-testable public API

## Milestones

- `v0.1.0` Project scaffold
- `v0.2.0` Parameters frozen
- `v0.3.0` Geometry complete
- `v0.4.0` Parts complete
- `v0.5.0` Assembly complete
- `v0.6.0` Simulation complete
- `v0.7.0` Manufacturing complete
- `v0.8.0` Export complete
- `v0.9.0` Integration testing
- `v1.0.0` First production release

## Sprint 1 Parameter Foundation

`Core/Parameters.py` defines schema version `2.1` and keeps the parameter model independent of FreeCAD. Every public parameter dataclass inherits from `ParameterGroup`, which provides `to_dict()` and `to_json()` serialization for CAD metadata, simulations, manufacturing exports, cloud synchronization, AI optimization, and future Digital Twin integrations.

Each `AURAParameters` instance contains engineering metadata so generated artifacts can identify the robot name, version, manufacturer, author, CAD system, and units. Named configurations are exposed through `PARAMETER_REGISTRY` with `STANDARD`, `MINI`, `INDUSTRIAL`, and `DEVELOPER` profiles. `DEFAULT_PARAMETERS` remains available as a backward-compatible alias for the standard profile.

Sprint 1 intentionally does not introduce FreeCAD, geometry generation, simulation behavior, manufacturing logic, AI logic, Digital Twin synchronization, or motion planning. Those layers should consume this stable, versioned parameter API in later milestones.

## Geometry Sprint 2

`Core/Geometry.py` is the permanent geometric source of truth for AURA. It defines the coordinate-frame vocabulary, derives robot envelopes from `Core/Parameters.py`, and provides a placement solver for canonical mounting points. Modules outside `Core/Geometry.py` must request permanent mounting coordinates from the geometry layer instead of calculating their own positions.

The robot coordinate convention uses a robot-centered ground-plane origin: `+Z` points upward, `+X` points toward the rear in the 2D planning view, `+Y` points to the robot left, and `-Y` points to the robot right. This convention is FreeCAD-independent and must be preserved by CAD, simulation, manufacturing, export, and Digital Twin integrations.

## Geometry Sprint 3

`Core/Geometry.py` now owns all coordinate transformations through immutable rotation primitives, `RigidTransform`, `Pose3D`, and a validated `FrameGraph`. Every coordinate conversion in AURA must pass through this module; downstream packages must not implement independent frame-conversion logic.

The Sprint 3 frame graph starts with `world -> robot` and branches to base, shell, left wheel, right wheel, tray, battery, camera, and sensor frames. The public `GeometryEngine` API supports frame lookup, camera pose construction, transform retrieval, point conversion, and vector conversion without introducing CAD, physics, SLAM, motion-planning, or FreeCAD dependencies.

## Geometry Sprint 4

`Core/Geometry.py` now includes the `ClearanceSolver`, AURA's first geometric design-rule-checking subsystem. It models component occupied, clearance, service, and movement volumes; provides collision and minimum-clearance APIs; represents wheel motion, tray opening paths, camera visibility, ultrasonic sensor regions, and service zones; and returns structured `ClearanceReport` results.

Every permanent clearance, collision, motion-envelope, and serviceability calculation must originate from `Core/Geometry.py`. Sprint 4 remains limited to geometric checks and intentionally excludes physics simulation, structural analysis, dynamics, path planning, finite element analysis, CAD generation, and FreeCAD placement objects.
