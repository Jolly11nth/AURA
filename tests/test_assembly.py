from Main import build_default_assembly


def test_build_default_assembly_has_base_envelope() -> None:
    assembly = build_default_assembly()

    assert assembly.base.envelope.length_mm == assembly.parameters.envelope.length_mm
