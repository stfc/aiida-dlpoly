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

```
pip install aiida-dlpoly
```

At present due to a outdated dependency this package requires the distutils module which will cause issues
with certain environments running python >= 3.12. This is being addressed and should be resolved in a future
release.

## Requirements 

To use this plugin a configured AiiDA profile and computer configuration are required, see the
[AiiDa documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/get_started.html)
for instructions on how to install and configure AiiDA.


## Setup 

To configure the DL_POLY plugin an AiiDA code instance needs to be configured for the DL_POLY executable.
The following is an example of a basic YAML configuration file:

```yaml
label: dlpoly
description: DL_POLY 
computer: localhost 
filepath_executable: /absolute/path/to/DLPOLY.Z
default_calc_job_plugin: dlpoly.md
use_double_quotes: false 
with_mpi: true 
prepend_text: '' 
append_text: '' 
```

Write this to a file named `dlpoly_config.yml` ensuring the value for `computer` matches the label of your computer configured in the previous 
step. The code can then be configured by running:

```bash
verdi code create core.code.installed --config dlpoly_config.yml -n 
```

If successful this will have created a code with the label `dlpoly` which can then be used to run ChemShell jobs within the AiiDA workflow. 

## Examples 

