"""AURA application entry point."""
from __future__ import annotations

import argparse
from pathlib import Path

from Assembly.Assembly import AURAAssembly
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


def build_assembly(parameters: AURAParameters = DEFAULT_PARAMETERS) -> AURAAssembly:
    """Create the complete parametric AURA assembly descriptor."""
    return AURAAssembly(parameters)


def build_default_assembly() -> AURAAssembly:
    """Backward-compatible factory for the standard AURA configuration."""
    return build_assembly(DEFAULT_PARAMETERS)


def main() -> int:
    parser = argparse.ArgumentParser(description="AURA robotics CAD framework")
    parser.add_argument("--profile", default="STANDARD", help="Named parameter profile")
    parser.add_argument("--save", type=Path, help="Optional FreeCAD document output path")
    args = parser.parse_args()

    parameters = AURAParameters.from_registry(args.profile)
    assembly = build_assembly(parameters)
    if args.save is not None:
        document = assembly.build_document()
        document.saveAs(str(args.save))
        print(f"Saved AURA document to {args.save}")
    else:
        print(f"AURA {parameters.schema_version}: {len(assembly.parts)} parametric part groups ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
