"""Utility functions for the AiiDA DL_POLY plugin."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy
from aiida.orm import SinglefileData, StructureData
from ruamel.yaml import YAML


class DLPStatis:
    """
    A utility class for parsing a DL_POLY STATIS file.

    Aspects of this class have been derived from the dlpoly-py python package, see
    https://gitlab.com/ccp5/dlpoly-py.
    """

    def __init__(self, file: str | None, control: dict | None = None):
        """
        DLPStatis constructor.

        Parameters
        ----------
        file: str | None
            An optional path to a STATIS file to parse on initialisation.
        """
        self.labels = []
        self.data = numpy.array([])
        if file is not None:
            self.parse(file, control)

    def parse(self, file: str, control: dict | None = None) -> None:
        """Parse the statistics dictionary from a STATIS file."""
        with open(file) as f:
            yaml_key = f.readline().split()[0]

        if yaml_key == "%YAML":
            yml = YAML()
            with open(file, "rb") as f:
                data = yml.load(f)
                self.labels = data["labels"][0]
                self.data = numpy.array(data["timesteps"])
        else:
            with open(file) as f:
                _, _, data = f.read().split("\n", 2)
                data = numpy.array(data.split(), dtype=float)
                columns = int(data[2]) + 3
                rows = data.size // columns
                self.data = data[: rows * columns]
                self.data = self.data.reshape((rows, columns), copy=False)
                self.data = numpy.delete(self.data, 2, axis=1)
            self.labels = self.generate_labels()
            if control is not None:
                self.add_additional_labels(control)

    @staticmethod
    def generate_labels() -> list[str]:
        """Generate the default labels when reading a text formatted STATIS file."""
        return [
            "step",
            "Elapsed Simulation Time",
            "Total Extended System Energy",
            "System Temperature",
            "Configurational Energy",
            "Short Range Potential Energy",
            "Electrostatic Energy",
            "Chemical Bond Energy",
            "Valence Angle And 3-Body Potential Energy",
            "Dihedral Inversion And 4-Body Potential Energy",
            "Tethering Energy",
            "Enthalpy (Total Energy + Pv)",
            "Rotational Temperature",
            "Total Virial",
            "Short-Range Virial",
            "Electrostatic Virial",
            "Bond Virial",
            "Valence Angle And 3-Body Virial",
            "Constraint Bond Virial",
            "Tethering Virial",
            "Volume",
            "Core-Shell Temperature",
            "Core-Shell Potential Energy",
            "Core-Shell Virial",
            "Md Cell Angle Α",
            "Md Cell Angle Β",
            "Md Cell Angle Γ",
            "Pmf Constraint Virial",
            "Pressure",
            "External Degree Of Freedom",
            "stress xx",
            "stress xy",
            "stress xz",
            "stress yx",
            "stress yy",
            "stress yz",
            "stress zx",
            "stress zy",
            "stress zz",
        ]

    def add_additional_labels(self, control: dict) -> None:
        """Add additional optional entries to the statistics based on control inputs."""
        if control.get("ensemble_method", "").lower() == "dpd":
            components = ["xx", "xy", "xz", "yx", "yy", "yz", "zx", "zy", "zz"]
            for component in components:
                self.labels.append(f"conservative stress {component}")
            for component in components:
                self.labels.append(f"dissipative stress {component}")
            for component in components:
                self.labels.append(f"random stress {component}")
            for component in components:
                self.labels.append(f"kinetic stress {component}")
        if control.get("ensemble", "").lower() in ("nst", "npt"):
            num_atom_types = self.data.shape[1] - len(self.labels) - 10
            for i in range(num_atom_types):
                self.labels.append(f"amsd atom {i}")
            for component in ("x", "y", "z"):
                self.labels.append(f"cell a_{component}")
            for component in ("x", "y", "z"):
                self.labels.append(f"cell b_{component}")
            for component in ("x", "y", "z"):
                self.labels.append(f"cell c_{component}")
            self.labels.append("PV")
        else:
            num_atom_types = self.data.shape[1] - len(self.labels)
            for i in range(num_atom_types):
                self.labels.append(f"amsd atom {i}")
        return


def config_to_structuredata(config_file: str) -> StructureData:
    """Convert a CONFIG file into an AiiDA StructureData node."""
    structure = StructureData()

    with open(config_file) as f:
        lines = f.readlines()

    structure.label = lines[0].strip()
    info_line = lines[1].split()
    levcfg = int(info_line[0])
    imgcon = int(info_line[1])
    natoms = int(info_line[2])

    structure.pbc = [
        True if imgcon in [1, 2, 3, 6] else False,
        True if imgcon in [1, 2, 3, 6] else False,
        True if imgcon in [1, 2, 3] else False,
    ]

    cell = numpy.zeros((3, 3), dtype=float)
    for i, line in enumerate(lines[2:5]):
        cell[i, :] = numpy.array(line.split(), dtype=float)
    structure.cell = cell

    li = 5
    for _ in range(natoms):
        symbol = lines[li].split()[0]
        position = numpy.array(lines[li + 1].split(), dtype=float)
        structure.append_atom(position=position, symbols=symbol)
        li += levcfg + 2

    return structure


def singlefiledata_config_to_structuredata(
    config_file: SinglefileData,
) -> StructureData:
    """Convert a SinglefileData config node to a StructureData node."""
    with NamedTemporaryFile(mode="w+", delete=True, suffix="") as tmp:
        tmp.write(config_file.get_content(mode="r"))
        return config_to_structuredata(tmp.name)


def structuredata_to_config(structure: StructureData) -> str:
    """Write a CONFIG file based on an AiiDA StructureData node."""
    config_str = f"{structure.label}\n"
    config_str += f"        0        3 {len(structure.sites):8d}\n"
    config_str += (
        f"    {structure.cell[0][0]:12.6f} {structure.cell[0][1]:12.6f} "
        f"{structure.cell[0][2]:12.6f}\n"
    )
    config_str += (
        f"    {structure.cell[1][0]:12.6f} {structure.cell[1][1]:12.6f} "
        f"{structure.cell[1][2]:12.6f}\n"
    )
    config_str += (
        f"    {structure.cell[2][0]:12.6f} {structure.cell[2][1]:12.6f} "
        f"{structure.cell[2][2]:12.6f}"
    )
    for i, site in enumerate(structure.sites):
        config_str += f"\n{site.kind_name:8s}{i:8d}"
        config_str += (
            f"\n    {site.position[0]:12.6f} {site.position[1]:12.6f} "
            f"{site.position[2]:12.6f}"
        )
    return config_str


def control_to_dict(control: str | Path | SinglefileData) -> dict:
    """Extract all parameters in a CONTROL file into a dictionary."""
    control_dict = {}
    if isinstance(control, SinglefileData):
        lines = control.get_content("r").split("\n")
    else:
        with open(control) as f:
            lines = f.readlines()

    for line in lines:
        line = line.split("#")[0]
        line = line.split("!")[0]
        line = line.strip()
        if not line:
            continue
        key, *args = line.split()
        if key == "title":
            control_dict[key] = " ".join(args)
        elif len(args) > 1:
            control_dict[key] = [
                stripped_arg for arg in args if (stripped_arg := arg.strip("[]"))
            ]
        else:
            control_dict[key] = args[0]
    return control_dict
