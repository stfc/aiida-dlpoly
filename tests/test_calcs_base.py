"""Test running the base DL_POLY CalcJob."""

from aiida.engine import run

from aiida_dlpoly.calculations.base import DLPOLYCalculation


def test_argon_simulation(generate_inputs):
    """Based Argon MD simulation."""
    inputs = generate_inputs()
    results, node = run.get_node(DLPOLYCalculation, **inputs)
    assert node.is_finished_ok, "CalcJob failed."

    with open("tmp.out", "w") as f:
        f.write(results["retrieved"].get_object_content("OUTPUT"))
