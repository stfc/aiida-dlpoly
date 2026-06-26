"""PyTest Configurations."""

import os
import pathlib

import pytest
from aiida.common.folders import Folder
from aiida.engine import CalcJob
from aiida.engine.utils import instantiate_process
from aiida.manage.manager import get_manager
from aiida.orm import InstalledCode, SinglefileData

pytest_plugins = "aiida.tools.pytest_fixtures"


@pytest.fixture
def get_data_filepath() -> pathlib.Path:
    """Return the path to the tests data folder."""
    return pathlib.Path(__file__).resolve().parent / "data"


@pytest.fixture
def get_test_data_file(get_data_filepath):
    """Return a SinglefileData object containing the an input chemical structure."""

    def factory(fname: str = "CONFIG") -> SinglefileData:
        return SinglefileData(file=str(get_data_filepath / fname))

    return factory


@pytest.fixture
def dlpoly_code(aiida_code_installed):
    """Return a ChemShell AiiDA code instance."""

    def factory(plugin: str = "dlpoly") -> InstalledCode:
        return aiida_code_installed(
            filepath_executable=os.environ.get("DLPOLY_BIN", "DLPOLY.Z"),
            default_calc_job_plugin=plugin,
            prepend_text=os.environ.get("DLPOLY_PREPEND_TEXT", ""),
            append_text=os.environ.get("DLPOLY_APPEND_TEXT", ""),
        )

    return factory


@pytest.fixture
def generate_inputs(dlpoly_code, get_test_data_file):
    """Return a dictionary of inputs for the ChemShellCalculation."""

    def factory() -> dict:
        return {
            "configuration": get_test_data_file("CONFIG"),
            "control": get_test_data_file("CONTROL"),
            "field": get_test_data_file("FIELD"),
            "code": dlpoly_code(),
        }

    return factory


@pytest.fixture
def generate_calcjob(tmp_path, generate_inputs):
    """Return an initialised aiida-chemshell CalcJob instance."""

    def factory(process_class: CalcJob, inputs=generate_inputs(), return_process=False):
        manager = get_manager()
        runner = manager.get_runner()
        process = instantiate_process(runner, process_class, **inputs)

        if return_process:
            return process

        calc_info = process.prepare_for_submission(Folder(tmp_path))
        return tmp_path, calc_info

    return factory
