"""Utility functions for the AiiDA DL_POLY plugin."""

from aiida.orm import StructureData
from dlpoly.config import Config


def config_to_structuredata(config_file: str) -> StructureData:
    """Convert a CONFIG file into an AiiDA StructureData node."""
    config = Config(config_file)
    structure = StructureData()
    structure.label = config.title
    structure.pbc = [
        True if config.pbc in [1, 2, 3, 6] else False,
        True if config.pbc in [1, 2, 3, 6] else False,
        True if config.pbc in [1, 2, 3] else False,
    ]
    structure.cell = config.cell

    for atom in config.atoms:
        structure.append_atom(position=atom.pos, symbols=atom.element)

    return structure


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
