from dataclasses import FrozenInstanceError

import pytest

from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS, EnvelopeParameters, WheelParameters


def test_default_parameters_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        DEFAULT_PARAMETERS.envelope = EnvelopeParameters()  # type: ignore[misc]


def test_metadata_is_immutable() -> None:
    with pytest.raises(TypeError):
        DEFAULT_PARAMETERS.metadata["platform"] = "changed"  # type: ignore[index]


def test_rejects_negative_dimensions() -> None:
    with pytest.raises(ValueError, match="length_mm must be positive"):
        EnvelopeParameters(length_mm=-1.0)


def test_rejects_wheel_track_outside_envelope() -> None:
    with pytest.raises(ValueError, match="track_width"):
        AURAParameters(wheels=WheelParameters(track_width_mm=999.0))
