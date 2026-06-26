"""Tests for the utility functions provided with aiida-dlpoly."""

from aiida_dlpoly.utils import config_to_structuredata


def test_config_to_structuredata(get_data_filepath):
    """Test converting a CONFIG file to a structuredata node."""
    structure = config_to_structuredata(get_data_filepath / "CONFIG")

    assert structure.pbc1
    assert structure.pbc2
    assert structure.pbc3

    cell_vec = 17.395296948
    assert abs(structure.cell[0][0] - cell_vec) < 1e-8
    assert abs(structure.cell[1][1] - cell_vec) < 1e-8
    assert abs(structure.cell[2][2] - cell_vec) < 1e-8
    assert abs(structure.cell[0][1]) < 1e-10

    assert "Ar" in structure.get_kind_names()
    assert len(structure.get_kind_names()) == 1
    assert len(structure.kinds) == 1
    assert len(structure.sites) == 100

    return
