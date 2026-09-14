# AURA

**Autonomous Universal Robotic Assistant** — a parametric robotics engineering framework for CAD, assembly, manufacturing definition, kinematic simulation, export, and future autonomy/digital-twin layers.

## Frozen architecture

```text
AURA/
├── Core/             # engineering parameters, geometry, materials, utilities
├── Parts/            # parametric robot components
├── Assembly/         # complete robot composition
├── Manufacturing/    # BOM and drawing specifications
├── Simulation/       # deterministic kinematic simulation
├── Export/           # STEP, STL and TechDraw adapters
├── tests/            # regression and integration tests
└── Main.py           # application entry point
```

## Engineering contract

- `Core/Parameters.py` is the single source of engineering constants.
- `Core/Geometry.py` is the single source of spatial calculations, frames, clearances, and motion envelopes.
- Core engineering modules remain FreeCAD-independent.
- CAD runtime imports occur only at build/export boundaries.
- Configuration is immutable, typed, versioned, serializable, and validated.
- No magic engineering numbers in downstream modules.
- Existing public APIs are preserved where practical for backward compatibility.

## Current implementation

### Parameters — schema 2.1

The parameter model provides metadata, envelope/base/shell/tray/wheel/electronics/payload/manufacturing groups, relationship validation, JSON serialization, named profiles (`STANDARD`, `MINI`, `INDUSTRIAL`, `DEVELOPER`), and the backward-compatible `DEFAULT_PARAMETERS` alias.

### Geometry — Sprints 1–4

Geometry owns 3D primitives, coordinate frames, rotations, rigid transforms, frame graphs, robot envelopes, placement, clearance volumes, service zones, camera/sensor regions, wheel/tray motion envelopes, collision checks, and structured clearance reports.

### Parts and assembly

Base, shell, top cover, tray, wheels, and electronics are now parametric descriptors. When FreeCAD is installed, each part can build a Part shape and `AURAAssembly.build_document()` creates a complete CAD document.

### Manufacturing

`Manufacturing/BOM.py` generates a deterministic BOM from the parameter model. `Manufacturing/Drawings.py` generates parameter-driven drawing specifications.

### Simulation

`Simulation/Simulation.py` provides a deterministic differential-drive kinematic model suitable for regression tests and early motion integration.

### Export

STEP, STL, and TechDraw adapters are isolated behind explicit FreeCAD runtime boundaries so CI does not require a CAD installation.

## Development

Python 3.12+ is required. Development dependencies are declared under `[project.optional-dependencies].dev`.

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m mypy
```

The GitHub Actions workflow runs compilation, tests, linting, and type checking on pushes and pull requests.

## Status

- `v0.1` scaffold: complete
- `v0.2` parameter foundation: complete
- `v0.3` geometry foundation: complete
- `v0.4` geometry clearance engine: complete
- `v0.5` parametric parts, assembly, manufacturing definitions, simulation, export boundaries: **in progress / integration stage**
- `v1.0` production robotics platform: not yet claimed

AURA is not considered production-ready merely because the software framework builds. Physical validation, FreeCAD model review, tolerance verification, electronics integration, motor/driver validation, safety analysis, hardware-in-the-loop testing, and field testing remain mandatory engineering gates.
