"""Defines the base calculation parser for the DL_POLY AiiDA plugin."""

from aiida.engine import ExitCode
from aiida.orm import SinglefileData
from aiida.parsers.parser import Parser


class DLPOLYParser(Parser):
    """Main DL_POLY CalcJob parser."""

    def parse(self, **kwargs) -> ExitCode:
        """Parse the results of a DL_POLY base CalcJob."""
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

        return ExitCode(0)
