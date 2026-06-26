"""Core DL_POLY simulation calculation module."""

from tempfile import NamedTemporaryFile

from aiida.common import CalcInfo, CodeInfo
from aiida.common.folders import Folder
from aiida.engine import CalcJob, CalcJobProcessSpec
from aiida.orm import ArrayData, Dict, SinglefileData, StructureData
from dlpoly.new_control import NewControl

from aiida_dlpoly.utils import structuredata_to_config


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
        calc_info.retrieve_temporary_list = ["STATIS", "REVCON", "RDFDAT", "MSDDAT"]
        calc_info.provenance_exclude_list = []
        calc_info.retrieve_list = ["OUTPUT"]

        calc_info.local_copy_list = [
            (
                self.inputs.field.uuid,
                self.inputs.field.filename,
                self.inputs.field.filename,
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
        else:
            control_str = self.write_control_file()
            with folder.open("CONTROL", "w") as f:
                f.write(control_str)

        if isinstance(self.inputs.configuration, SinglefileData):
            calc_info.local_copy_list.append(
                (
                    self.inputs.configuration.uuid,
                    self.inputs.configuration.filename,
                    self.inputs.configuration.filename,
                )
            )
        else:
            config_str = structuredata_to_config(self.inputs.configuration)
            with folder.open("CONFIG", "w") as f:
                f.write(config_str)

        return calc_info

    def write_control_file(self) -> str:
        """Write a formatted CONTROL file from an input dictionary."""
        control = NewControl.from_dict(self.inputs.control.get_dict())
        with NamedTemporaryFile(mode="w+", delete=True, suffix="") as tmp:
            control.write(tmp.name)
            tmp.seek(0)
            return tmp.read()
        # return control_str
