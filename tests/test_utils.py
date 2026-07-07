"""Tests for the utility functions provided with aiida-dlpoly."""

from aiida_dlpoly.utils import config_to_structuredata, control_to_dict


def test_config_to_structuredata(get_data_filepath):
    """Test converting a CONFIG file to a structuredata node."""
    structure = config_to_structuredata(get_data_filepath / "Ar.config")

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


def test_control_to_dict(get_data_filepath):
    """Test extracting the control inputs from a file into a dictionary."""
    control = control_to_dict(get_data_filepath / "Ar.control")
    assert len(list(control.keys())) == 23
    assert control["title"] == "Argon System, stress autocorrelation"
    assert control["io_file_field"] == "Ar.field"
    assert control["temperature"] == ["85.0", "K"]
    assert control["random_seed"] == ["2011", "2021", "2022"]
    return
