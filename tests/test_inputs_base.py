"""Tests for DL_POLY base CalcJob creation and input validation."""

from aiida_dlpoly.calculations.base import DLPOLYCalculation


def test_base_defaults(generate_calcjob):
    """Make a default test input with 3 SginlefileData nodes."""
    tmp_path, calc_info = generate_calcjob(DLPOLYCalculation)

    assert calc_info.retrieve_temporary_list == [
        "OUTPUT",
        "STATIS",
        "REVCON",
        "RDFDAT",
        "HISTORY",
    ]
    assert calc_info.codes_info[0].cmdline_params == ["-c", "Ar.control"]

    return
