"""Core DL_POLY simulation calculation module."""

from collections.abc import Sequence
from functools import singledispatchmethod
from pathlib import Path
from typing import Any

from aiida.common import CalcInfo, CodeInfo
from aiida.common.folders import Folder
from aiida.engine import CalcJob, CalcJobProcessSpec
from aiida.orm import ArrayData, Dict, SinglefileData, StructureData

from aiida_dlpoly.utils import control_to_dict, structuredata_to_config


class DLPOLYCalculation(CalcJob):
    """AiiDA calculation plugin for running molecular dynamics with DL_POLY."""

    @classmethod
    def define(cls, spec: CalcJobProcessSpec) -> None:
        """
         Define the inputs, outputs and metadata of the DL_POLY simulation.

        Parameters
        ----------
        spec : CalcJobProcessSpec
            The AiiDA Process specification object for the job.
        """
        super().define(spec)

        ## INPUTS
        spec.input(
            "configuration",
            valid_type=(SinglefileData, StructureData),
            required=True,
            help=(
                "The 'CONFIG' file or a AiiDA StructureData object containing the"
                "definition of the molecular/particle based system."
            ),
        )

        spec.input(
            "field",
            valid_type=SinglefileData,
            required=True,
            help="The force field definition file in DL_POLY format.",
        )

        spec.input(
            "control",
            valid_type=(SinglefileData, Dict),
            required=True,
            help=(
                "The control parameters for the simulation either in a pre-formatted "
                "DL_POLY 'CONTROL' file or as a dictionary of inputs"
            ),
        )

        ## OUTPUTS
        spec.output(
            "output",
            valid_type=SinglefileData,
            required=True,
            help="The main DL_POLY 'OUTPUT' file.",
        )
        spec.output(
            "statistics",
            valid_type=ArrayData,
            required=True,
            help="Statistics collected throughout the simulation.",
        )
        spec.output(
            "revive_configuration",
            valid_type=SinglefileData,
            required=True,
            help="The final configuration generated to enable simulation restart.",
        )
        spec.output(
            "rdf",
            valid_type=SinglefileData,
            required=False,
            help="Radial Distribution Function data file produced by DL_POLY.",
        )
        spec.output(
            "msd",
            valid_type=SinglefileData,
            required=False,
            help="Mean Squared Displacement data file produced by DL_POLY.",
        )

        ## Metadata
        spec.inputs["metadata"]["options"]["resources"].default = {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        }
        spec.inputs["metadata"]["options"]["parser_name"].default = "dlpoly"

        ## Error Codes
        spec.exit_code(
            300,
            "ERROR_OUTPUT_NOT_FOUND",
            message="Error accessing the main DL_POLY output file.",
        )
        spec.exit_code(
            301,
            "ERROR_DL_POLY_DRIVER_FAILED",
            message=(
                "DL_POLY raised an error during execution. See the 'OUTPUT' file "
                "for more information"
            ),
        )
        spec.exit_code(
            302,
            "ERROR_STATIS_NOT_FOUND",
            message="Error accessing the DL_POLY statistics file.",
        )
        spec.exit_code(
            303,
            "ERROR_REVCON_NOT_FOUND",
            message="Unable to find the expected REVCON file.",
        )
        spec.exit_code(
            304,
            "ERROR_RDFDAT_NOT_FOUND",
            message="Unable to find the expected RDF data file.",
        )
        spec.exit_code(
            305,
            "ERROR_HISTORY_NOT_FOUND",
            message="Unable to find the expected trajectory file.",
        )

    def prepare_for_submission(self, folder: Folder) -> CalcInfo:
        """
        Prepare the DL_POLY calculation for submission.

        Params
        ------
        folder : Folder
            An `aiida.common.folders.Folder` specifying the temporary working
            directory for the calculation.

        Returns
        -------
        calcInfo : CalcInfo
            An `aiida.common.CalcInfo` instance.
        """
        if isinstance(self.inputs.control, SinglefileData):
            control = control_to_dict(self.inputs.control)
        else:
            control = self.inputs.control.get_dict()

        io_file_field: str = control.get("io_file_field", "FIELD")
        io_file_config: str = control.get("io_file_config", "CONFIG")

        code_info = CodeInfo()
        code_info.code_uuid = self.inputs.code.uuid
        if isinstance(self.inputs.control, SinglefileData):
            code_info.cmdline_params = ["-c", self.inputs.control.filename]
        else:
            code_info.cmdline_params = ["-c", "CONTROL"]
            with folder.open("CONTROL", "w") as f:
                f.write(self.write_control_file())

        calc_info = CalcInfo()
        calc_info.codes_info = [
            code_info,
        ]
        calc_info.retrieve_temporary_list = [
            "OUTPUT",
            "STATIS",
            "REVCON",
            "RDFDAT",
            "HISTORY",
        ]
        calc_info.provenance_exclude_list = []
        calc_info.retrieve_list = []

        calc_info.local_copy_list = [
            (
                self.inputs.field.uuid,
                self.inputs.field.filename,
                io_file_field,
            )
        ]
        if isinstance(self.inputs.control, SinglefileData):
            calc_info.local_copy_list.append(
                (
                    self.inputs.control.uuid,
                    self.inputs.control.filename,
                    self.inputs.control.filename,
                )
            )

        if isinstance(self.inputs.configuration, SinglefileData):
            calc_info.local_copy_list.append(
                (
                    self.inputs.configuration.uuid,
                    self.inputs.configuration.filename,
                    io_file_config,
                )
            )
        else:
            config_str = structuredata_to_config(self.inputs.configuration)
            with folder.open(io_file_config, "w") as f:
                f.write(config_str)

        return calc_info

    def write_control_file(self) -> str:
        """Write a formatted CONTROL file from an input dictionary."""
        title = self.inputs.control.get("title", "AiiDA DL_POLY simulation.")
        control_str = f"title {title}\n"
        for key, item in self.inputs.control.get_dict().items():
            if key != "title":
                control_str += f"{key}  {self.format_control_input(item, key)}\n"
        return control_str

    @singledispatchmethod
    @staticmethod
    def format_control_input(value: Any, key: str) -> str:
        """
        Format a DL_POLY control file input argument.

        Some aspects of the function overloads for this method have been derived from
        the dlpoly-py python package, see https://gitlab.com/ccp5/dlpoly-py.

        Parameters
        ----------
        value : Any
            The value to be applied to the given key.
        key : str
            Key of variable.

        Returns
        -------
        str
            The value correctly formatted for DL_POLY CONTROL file.
        """
        return str(value)

    @format_control_input.register
    @staticmethod
    def _(value: Sequence, key: str) -> str:
        """
        Format tuple/vector of parameters.

        This function formats both vector style inputs and inputs which contain
        a units key i.e. an input of (10, 'steps'). All numeric inputs to DL_POLY
        require a unit so must be supplied as a tuple in the form (value, unit).

        Parameters
        ----------
        vals : Sequence
            Vector-like value.
        key : str
            Key of variable.

        Returns
        -------
        str
            Formatted `Control` variable.
        """
        lvals = None
        can_be_len_1 = key in (
            "correlation_observable",
            "correlation_blocks",
            "correlation_block_points",
            "correlation_window",
            "correlation_update_frequency",
            "momentum_density",
        )

        if not can_be_len_1 and isinstance(value[-1], str):
            lvals, unit = value[:-1], value[-1]
        else:
            lvals, unit = value, ""

        if unit == "steps":
            lvals = list(map(int, lvals))

        out = " ".join(map(str, lvals))

        if len(lvals) > 1 or can_be_len_1:
            out = f"[{out}]"

        return f"{out} {unit}"

    @format_control_input.register
    @staticmethod
    def _(value: bool, key: str) -> str:
        """
        Format boolean arguments.

        Parameters
        ----------
        vals : bool
            Boolean value.
        key : str
            Key of variable.

        Returns
        -------
        str
            Formatted `Control` variable.
        """
        return "ON" if value else "OFF"

    @format_control_input.register(str)
    @format_control_input.register(Path)
    @staticmethod
    def _(value: str | Path, key: str) -> str:
        """
        Format string/Path arguments.

        Parameters
        ----------
        vals : Union[str, Path]
            Path or string-like value.
        key : str
            Key of variable.

        Returns
        -------
        str
            Formatted `Control` variable.
        """
        return str(value)
