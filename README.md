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
