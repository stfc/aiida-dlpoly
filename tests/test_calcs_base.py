"""Test running the base DL_POLY CalcJob."""

from aiida.engine import run
from aiida.orm import StructureData

from aiida_dlpoly.calculations.base import DLPOLYCalculation
from aiida_dlpoly.utils import (
    config_to_structuredata,
    singlefiledata_config_to_structuredata,
)


def test_argon_simulation(generate_inputs):
    """Based Argon MD simulation."""
    inputs = generate_inputs()
    results, node = run.get_node(DLPOLYCalculation, **inputs)
    assert node.is_finished_ok, "CalcJob failed."

    statis = results.get("statistics")

    assert len(statis.get_arraynames()) == 40, (
        "Incorrect number of entries in statis labels."
    )
    assert len(statis.get_array("step")) == 201, "Incorrect length of statis arrays."
    assert statis.get_array("step")[-1] == 2000

    assert abs(statis.get_array("System_Temperature")[-1] - 82.474323) < 1e-3

    assert abs(statis.get_array("Total_Extended_System_Energy")[-1] - -421.63999) < 1e-3

    revcon = singlefiledata_config_to_structuredata(results["revive_configuration"])
    assert len(revcon.sites) == 100
    assert len(revcon.kinds) == 1

    assert results.get("rdf", None)
    # assert results.get("msd", None)

    return


def test_control_dict_input(generate_inputs):
    """Test the ability to provide control parameters as a dictionary."""
    inputs = generate_inputs()
    inputs["control"] = {
        "title": "Argon System",
        "io_statis_yaml": "OFF",
        "temperature": (85.0, "K"),
        "initial_minimum_separation": (0.0, "ang"),
        "coul_method": "OFF",
        "print_frequency": (100, "steps"),
        "stats_frequency": (10, "steps"),
        "padding": (0.2, "ang"),
        "cutoff": (7.5, "ang"),
        "ensemble": "nve",
        "time_run": (2000, "steps"),
        "time_equilibration": (1000, "steps"),
        "time_job": (3000.0, "s"),
        "time_close": (100.0, "s"),
        "timestep": (0.001, "ps"),
        "rescale_frequency": (5, "steps"),
        "random_seed": (2011, 2021, 2022),
    }

    results, node = run.get_node(DLPOLYCalculation, **inputs)

    assert node.is_finished_ok, "CalcJob failed."

    assert "OUTPUT" in results["retrieved"].list_object_names()

    statis = results.get("statistics")
    assert len(statis.get_array("step")) == 201, "Incorrect length of statis arrays."
    assert len(statis.get_array("System_Temperature")) == 201, (
        "Incorrect length of statis arrays."
    )
    assert len(statis.get_array("step")) == 201, "Incorrect length of statis arrays."

    assert len(statis.get_array("Configurational_Energy")) == 201, (
        "Incorrect length of statis arrays."
    )
    assert statis.get_array("step")[-1] == 2000

    assert abs(statis.get_array("System_Temperature")[-1] - 82.474323) < 1e-3

    assert abs(statis.get_array("Total_Extended_System_Energy")[-1] - -421.63999) < 1e-3

    assert len(statis.get_arraynames()) == 40, (
        "Incorrect number of entries in statis labels."
    )

    return


def test_config_as_structuredata(generate_inputs, get_data_filepath):
    """Test the ability to use AiiDA StructureData as CONFIG inputs."""
    inputs = generate_inputs()
    inputs["configuration"] = config_to_structuredata(get_data_filepath / "CONFIG")
    assert isinstance(inputs["configuration"], StructureData)

    results, node = run.get_node(DLPOLYCalculation, **inputs)

    assert node.is_finished_ok, "CalcJob failed."

    assert "OUTPUT" in results["retrieved"].list_object_names()

    statis = results.get("statistics")
    assert len(statis.get_array("step")) == 201, "Incorrect length of statis arrays."

    assert len(statis.get_arraynames()) == 40, (
        "Incorrect number of entries in statis labels."
    )

    assert statis.get_array("step")[-1] == 2000

    assert abs(statis.get_array("System_Temperature")[-1] - 82.474323) < 1e-3

    assert abs(statis.get_array("Total_Extended_System_Energy")[-1] - -421.63999) < 1e-3
    return
