from dataclasses import FrozenInstanceError
import json

import pytest

from Core.Parameters import (
    AURAParameters,
    DEFAULT_PARAMETERS,
    EngineeringMetadata,
    EnvelopeParameters,
    PARAMETER_REGISTRY,
    PayloadParameters,
    SCHEMA_VERSION,
    TrayParameters,
    VersionMismatchError,
    WheelParameters,
)


def test_default_parameters_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        DEFAULT_PARAMETERS.envelope = EnvelopeParameters()  # type: ignore[misc]


def test_labels_are_immutable() -> None:
    with pytest.raises(TypeError):
        DEFAULT_PARAMETERS.labels["platform"] = "changed"  # type: ignore[index]


def test_metadata_is_available_and_versioned() -> None:
    assert DEFAULT_PARAMETERS.schema_version == SCHEMA_VERSION
    assert DEFAULT_PARAMETERS.metadata.robot_name == "AURA"
    assert DEFAULT_PARAMETERS.metadata.manufacturer == "Cee Jay Solutions Ltd"
    assert DEFAULT_PARAMETERS.metadata.cad_system == "FreeCAD"
    assert DEFAULT_PARAMETERS.metadata.units == "millimeters"


def test_rejects_mismatched_schema_version() -> None:
    with pytest.raises(VersionMismatchError):
        EngineeringMetadata(schema_version="1.0")


def test_rejects_negative_dimensions() -> None:
    with pytest.raises(ValueError, match="length_mm must be positive"):
        EnvelopeParameters(length_mm=-1.0)


def test_rejects_wheel_track_outside_envelope() -> None:
    with pytest.raises(ValueError, match="track_width"):
        AURAParameters(wheels=WheelParameters(track_width_mm=999.0))


def test_rejects_tray_outside_shell_width() -> None:
    with pytest.raises(ValueError, match="tray.width_mm"):
        AURAParameters(tray=TrayParameters(width_mm=999.0))


def test_rejects_payload_above_structural_limit() -> None:
    with pytest.raises(ValueError, match="payload.maximum_payload_kg"):
        AURAParameters(payload=PayloadParameters(maximum_payload_kg=999.0))


def test_parameter_groups_serialize_to_dict_and_json() -> None:
    data = DEFAULT_PARAMETERS.to_dict()
    assert data["metadata"]["schema_version"] == SCHEMA_VERSION
    assert data["unit_system"] == "millimeters"
    assert data["wheels"]["layout"] == "differential"

    encoded = DEFAULT_PARAMETERS.to_json(indent=None)
    decoded = json.loads(encoded)
    assert decoded == data


def test_registry_exposes_named_configurations() -> None:
    assert set(PARAMETER_REGISTRY) == {"STANDARD", "MINI", "INDUSTRIAL", "DEVELOPER"}
    assert AURAParameters.from_registry("standard") is DEFAULT_PARAMETERS
    assert PARAMETER_REGISTRY["MINI"].labels["profile"] == "MINI"
