from Manufacturing.BOM import generate_bom
from Manufacturing.Drawings import generate_drawing_specs


def test_bom_is_deterministic() -> None:
    bom = generate_bom()
    assert len(bom) == 7
    assert bom[0].part_number == "AURA-BASE-001"
    assert bom[4].quantity == 2


def test_drawing_specs_follow_parameters() -> None:
    specs = generate_drawing_specs()
    assert specs[0].width_mm > 0
    assert specs[2].title == "Service tray"
