[![Release](https://img.shields.io/github/v/release/stfc/aiida-dlpoly)](https://github.com/stfc/aiida-dlpoly/releases)
[![PyPI](https://img.shields.io/pypi/v/aiida-dlpoly)](https://pypi.org/project/aiida-dlpoly/)

[![Docs status](https://github.com/stfc/aiida-dlpoly/actions/workflows/ci-docs.yml/badge.svg?branch=main)](https://stfc.github.io/aiida-dlpoly/)
[![Pipeline Status](https://github.com/stfc/aiida-dlpoly/actions/workflows/ci-testing.yml/badge.svg?branch=main)](https://github.com/stfc/aiida-dlpoly/actions)
[![Coverage Status]( https://coveralls.io/repos/github/stfc/aiida-dlpoly/badge.svg?branch=main)](https://coveralls.io/github/stfc/aiida-dlpoly?branch=main)

[![DOI]()]()

# aiida-dlpoly

An [AiiDA](https://www.aiida.net) plugin for the [DL_POLY](https://ccp5.gitlab.io/dl-poly/) molecular/particle
dynamics software.

## Installation

This plugin is available through PyPI and should be installed using [`pip`](https://pip.pypa.io/en/stable/) python package manager.

```bash
pip install aiida-dlpoly
```

At present due to a outdated dependency this package requires the distutils module which will cause issues
with certain environments running python >= 3.12. This is being addressed and should be resolved in a future
release.

## Requirements

To use this plugin a configured AiiDA profile and computer instance are required, see the
[AiiDA documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/get_started.html)
for instructions on how to install and configure AiiDA and 
[AiiDA code setup](https://aiida.readthedocs.io/projects/aiida-core/en/stable/howto/run_codes.html)
for how to configure AiiDA to link to external software.

## Setup

To configure the DL_POLY plugin, an AiiDA code instance needs to be configured for the DL_POLY executable.
The following is an example of a basic YAML configuration file:

```yaml
label: dlpoly
description: DL_POLY 
computer: localhost 
filepath_executable: /absolute/path/to/DLPOLY.Z
default_calc_job_plugin: dlpoly
use_double_quotes: false 
with_mpi: true 
prepend_text: '' 
append_text: '' 
```

Write this to a file named `dlpoly_config.yml` ensuring the value for `computer` matches the label of your 
configured computer instance and the `filepath_executable` entry is the absolute path to a compiled DL_POLY executable.
The code can then be configured by running:

```bash
verdi code create core.code.installed --config dlpoly_config.yml -n 
```

If successful this will have created a code with the label `dlpoly` which can then be used to run DL_POLY jobs 
within the AiiDA workflow.

## Examples

An example script for running an simple molecular dynamics simulation with existing `CONTROL`, `FIELD` and `CONFIG` input
files is given below.

```python
from aiida.engine import run
from aiida.orm import SinglefileData
from aiida import load_profile

load_profile("username") # Replace with your own AiiDA username

build.load_code("dlpoly").get_builder()
builder.control = SinglefileData(file="/absolute/path/to/CONTROL") # Change these to the absolute paths to input files
builder.field = SinglefileData(file="/absolute/path/to/FIELD")
builder.configuration = SinglefileData(file="/absolute/path/to/CONFIG")

results, node = run.get_node(builder)
```

By default the calculation will produce three output nodes, a *SinglefileData* node containing the generated `OUTPUT` file
from DL_POLY, an *ArrayData* node containing the calculated statistics from the simulation and another *SinglefileData*
node containing the
[DL_POLY formatted `REVCON` file](https://ccp5.gitlab.io/dl-poly/UserManual/data_files/output_files.html#the-revcon-file).
Additionally the following optional output nodes are supported by the aiida-dlpoly plugin:

- Trajectory history (*TrajectoryData*)
- Radial distribution function (*SinglefileData*)

These will be generated if the relevant input keys are present in the DL_POLY `CONTROL` file. Further information on
AiiDA data types and how to interact with them can be found in the
[AiiDA documentation](https://aiida.readthedocs.io/projects/aiida-core/en/stable/topics/data_types.html).

The aiida-dlpoly plugin additionally allows alternative input methods for the `CONTROL` and `CONFIG` inputs,
which can both be optionally specified as a *Dict* or *StructureData* node respectively. The plugin itself will
then handle the relevant file formatting for to be compatible with DL_POLY. An example showing these alternative
inputs methods is shown below, it assumes an AiiDA *StructureData* node already exists in the user's database.

```python
from aiida.engine import run
from aiida.orm import Dict, load_node, SinglefileData
from aiida import load_profile

load_profile("username") # Replace with your own AiiDA username

build.load_code("dlpoly").get_builder()
builder.field = SinglefileData(file="/absolute/path/to/FIELD") # Change these to the absolute paths to input file
builder.configuration = load_node(pk=10) # Replace with the pk of the StructureData node or create a new StructureData node
builder.control = Dict({
    "title": "DL_POLY example MD simulation",
    "temperature": (295.0, "K"),
    "coul_method": "OFF",
    "print_frequency": (100, "steps"),
    "stats_frequency": (10, "steps"),
    "padding": (0.2, "ang"),
    "cutoff": (7.5, "ang"),
    "ensemble": "nve",
    "time_run": (2000, "steps"),
    "time_equilibration": (1000, "steps"),
    "time_job": (3000.0, "s"),
    "time_close": (100.0, "s"),
    "timestep": (0.001, "ps"),
    "rescale_frequency": (5, "steps"),
})

results, node = run.get_node(builder)
```
