"""Defines the base calculation parser for the DL_POLY AiiDA plugin."""

import os

from aiida.engine import ExitCode
from aiida.orm import ArrayData, SinglefileData
from aiida.parsers.parser import Parser

from aiida_dlpoly.utils import DLPStatis


class DLPOLYParser(Parser):
    """Main DL_POLY CalcJob parser."""

    def parse(self, **kwargs) -> ExitCode:
        """Parse the results of a DL_POLY base CalcJob."""
        retrieved_tmp_path = kwargs.get("retrieved_temporary_folder", None)
        if not retrieved_tmp_path:
            return self.exit_codes.ERROR_OUTPUT_NOT_FOUND

        if "OUTPUT" not in self.retrieved.list_object_names():
            return self.exit_codes.ERROR_OUTPUT_NOT_FOUND

        with self.retrieved.open("OUTPUT", "rb") as f:
            self.out(
                "output",
                SinglefileData(
                    file=f,
                    filename="OUTPUT",
                    label="DL_POLY OUTPUT File",
                    description=f"DL_POLY output from process: {self.node.pk}",
                ),
            )

        revcon_path = os.path.join(retrieved_tmp_path, "REVCON")
        if os.path.exists(revcon_path):
            with open(revcon_path, "rb") as f:
                self.out(
                    "revive_configuration",
                    SinglefileData(
                        file=f, filename="REVCON", label="DL_POLY REVCON file."
                    ),
                )
        else:
            return self.exit_codes.ERROR_STATIS_NOT_FOUND

        statis_path = os.path.join(retrieved_tmp_path, "STATIS")
        if os.path.exists(statis_path):
            self.parse_statis(statis_path)
        else:
            return self.exit_codes.ERROR_STATIS_NOT_FOUND

        rdf_path = os.path.join(retrieved_tmp_path, "RDFDAT")
        if os.path.exists(rdf_path):
            with open(rdf_path, "rb") as f:
                self.out(
                    "rdf",
                    SinglefileData(
                        file=f, filename="RDFDAT", label="DL_POLY RDF data file."
                    ),
                )
        msd_path = os.path.join(retrieved_tmp_path, "MSDDAT")
        if os.path.exists(msd_path):
            with open(msd_path, "rb") as f:
                self.out(
                    "msd",
                    SinglefileData(
                        file=f, filename="MSDDAT", label="DL_POLY MSD data file."
                    ),
                )

        return ExitCode(0)

    def parse_statis(self, path: str) -> None:
        """Parse the STATIS file into an ArrayData node."""
        statis = DLPStatis(path)

        array = ArrayData(label="DLPOLY Statistics Output")
        for i, label in enumerate(statis.labels):
            if "Enthalpy" in label:
                label = label = "Enthalpy"
            elif "Α" in label:
                label = label.replace("Α", "alpha")
            elif "Β" in label:
                label = label.replace("Β", "beta")
            elif "Γ" in label:
                label = label.replace("Γ", "gamma")
            array.set_array(
                label.replace(" ", "_").replace("-", "_"), statis.data[:, i]
            )
        self.out("statistics", array)
        return
