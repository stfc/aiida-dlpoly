"""Defines the base calculation parser for the DL_POLY AiiDA plugin."""

import os

import numpy
from aiida.engine import ExitCode
from aiida.orm import ArrayData, SinglefileData, TrajectoryData
from aiida.parsers.parser import Parser

from aiida_dlpoly.utils import DLPStatis, control_to_dict


class DLPOLYParser(Parser):
    """Main DL_POLY CalcJob parser."""

    def parse(self, **kwargs) -> ExitCode:
        """Parse the results of a DL_POLY base CalcJob."""
        retrieved_tmp_path = kwargs.get("retrieved_temporary_folder", None)
        if not retrieved_tmp_path:
            return self.exit_codes.ERROR_OUTPUT_NOT_FOUND

        if isinstance(self.node.inputs.control, SinglefileData):
            control = control_to_dict(self.node.inputs.control)
        else:
            control = self.node.inputs.control.get_dict()

        output_path = os.path.join(retrieved_tmp_path, "OUTPUT")
        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                self.out(
                    "output",
                    SinglefileData(
                        file=f,
                        filename="OUTPUT",
                        label="DL_POLY OUTPUT File",
                        description=f"DL_POLY output from process: {self.node.pk}",
                    ),
                )
        else:
            return self.exit_codes.ERROR_OUTPUT_NOT_FOUND

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

        if control.get("rdf_calculate", "off").lower() == "on":
            rdf_path = os.path.join(retrieved_tmp_path, "RDFDAT")
            if os.path.exists(rdf_path):
                with open(rdf_path, "rb") as f:
                    self.out(
                        "rdf",
                        SinglefileData(
                            file=f, filename="RDFDAT", label="DL_POLY RDF data file."
                        ),
                    )
            else:
                return self.exit_codes.ERROR_RDFDAT_NOT_FOUND

        if control.get("traj_calculate", "off").lower() == "on":
            history_path = os.path.join(retrieved_tmp_path, "HISTORY")
            if os.path.exists(history_path):
                self._parse_history(history_path)
            else:
                return self.exit_codes.ERROR_HISTORY_NOT_FOUND

        return ExitCode(0)

    def parse_statis(self, path: str) -> None:
        """Parse the STATIS file into an ArrayData node."""
        if isinstance(self.node.inputs.control, SinglefileData):
            control = control_to_dict(self.node.inputs.control)
        else:
            control = self.node.inputs.control.get_dict()
        statis = DLPStatis(path, control)

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

    def _parse_history(self, path: str) -> None:
        """Parse the HISTORY file into a TrajecotoryData node."""
        stepids = []
        positions = []
        velocities = []
        times = []
        symbols = []
        cells = []

        with open(path) as f:
            label = f.readline()
            info_line = f.readline().split()
            keytrj = int(info_line[0])
            imcon = int(info_line[1])
            natoms = int(info_line[2])
            nsteps = int(info_line[3])

            for step in range(nsteps):
                step_info_line = f.readline().split()
                stepids.append(int(step_info_line[1]))
                times.append(float(step_info_line[6]))

                step_positions = []
                step_velocities = []

                step_cell = numpy.zeros((3, 3), dtype=float)
                for i in range(3):
                    step_cell[i, :] = numpy.array(f.readline().split(), dtype=float)

                for _ in range(natoms):
                    atom_line = f.readline()
                    if step == 0:
                        symbols.append(atom_line.split()[0])
                    position_line = f.readline()
                    step_positions.append([float(val) for val in position_line.split()])
                    if keytrj >= 1:
                        vel_line = f.readline()
                        step_velocities.append([float(val) for val in vel_line.split()])
                    if keytrj >= 2:
                        f.readline()

                cells.append(step_cell)
                positions.append(step_positions)
                velocities.append(step_velocities)

        trajectory = TrajectoryData(label=label)
        trajectory.set_trajectory(
            symbols=symbols,
            positions=numpy.array(positions, dtype=float),
            stepids=numpy.array(stepids, dtype=int),
            cells=numpy.array(cells, dtype=float),
            times=numpy.array(times, dtype=float),
            velocities=numpy.array(velocities, dtype=float) if keytrj >= 1 else None,
            pbc=[
                True if imcon in [1, 2, 3, 6] else False,
                True if imcon in [1, 2, 3, 6] else False,
                True if imcon in [1, 2, 3] else False,
            ],
        )

        self.out("history", trajectory)

        return
