---
name: aiida-dlpoly
description: >-
  Set up, submit, and troubleshoot DL_POLY molecular dynamics calculations through AiiDA
  using the aiida-dlpoly plugin. Use when the user wants to run a DL_POLY simulation from
  AiiDA, build a DL_POLY CONTROL/FIELD/CONFIG input, interpret aiida-dlpoly's calcjob
  outputs or exit codes, or asks about the aiida_dlpoly.mcp tools
  (describe_dlpoly_calcjob, submit_dlpoly_job).
---

# aiida-dlpoly

`aiida-dlpoly` wraps the [DL_POLY](https://ccp5.gitlab.io/dl-poly/) molecular/particle
dynamics code as an AiiDA `CalcJob` (entry point `dlpoly`), so DL_POLY runs get full AiiDA
data provenance.

## Prerequisites

An AiiDA profile, a configured `Computer`, and a `Code` with
`default_calc_job_plugin: dlpoly` are required before anything can be submitted. If none
exists yet, configure one with a YAML file and `verdi code create core.code.installed`:

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

```bash
verdi code create core.code.installed --config dlpoly_config.yml -n
```

## Two ways to submit a job

**Prefer the MCP tools if connected to an `aiida-mcp` server** (check for
`describe_dlpoly_calcjob` / `submit_dlpoly_job` among available tools): call
`describe_dlpoly_calcjob` first to confirm current inputs/outputs/exit codes, then
`submit_dlpoly_job` with the arguments below, then follow up with aiida-mcp's own
`get_process` / `get_process_report` to poll status and see output. Each of
`configuration`, `field`, `control` takes exactly one of `path` (file on the server's
machine), `text` (raw file contents), or `pk` (existing node); `control` also accepts
`parameters` (a dict, see below).

**Otherwise, write an AiiDA script** using the builder API:

```python
from aiida import load_profile
from aiida.engine import run
from aiida.orm import SinglefileData, load_code

load_profile("username")

builder = load_code("dlpoly").get_builder()
builder.control = SinglefileData(file="/absolute/path/to/CONTROL")
builder.field = SinglefileData(file="/absolute/path/to/FIELD")
builder.configuration = SinglefileData(file="/absolute/path/to/CONFIG")

results, node = run.get_node(builder)
```

`control` and `configuration` also accept native AiiDA data nodes instead of pre-formatted
files — `control` as a `Dict`, `configuration` as a `StructureData` (loaded from an
existing node, e.g. `load_node(pk=...)`) — letting the plugin generate the DL_POLY file
text itself:

```python
from aiida.orm import Dict, load_node, SinglefileData, load_code

builder = load_code("dlpoly").get_builder()
builder.field = SinglefileData(file="/absolute/path/to/FIELD")
builder.configuration = load_node(pk=10)  # a StructureData node
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
```

## Building a CONTROL dict

When the `control` input is a `Dict` (or the MCP `control.parameters` argument), each key
is a DL_POLY CONTROL directive and the plugin formats the value for you:

- A `(value, unit)` tuple (e.g. `(295.0, "K")`, `(100, "steps")`) renders as `value unit`.
  Most DL_POLY numeric parameters require an explicit unit, so prefer this form over a bare
  number.
- A longer tuple/sequence renders as a bracketed vector, e.g. `(1.0, 2.0, 3.0, "ang")` ->
  `[1.0 2.0 3.0] ang`.
- A `bool` renders as `ON`/`OFF` (e.g. `"rdf_calculate": True` -> `rdf_calculate  ON`).
- A plain `str` is written through unchanged (e.g. `"ensemble": "nve"`).
- `title` is special-cased as the first line of the file, not a directive.
- `io_file_field` / `io_file_config` override the staged file names DL_POLY expects
  (default `FIELD` / `CONFIG`).

## Outputs

Always produced: `output` (`SinglefileData`, the DL_POLY `OUTPUT` file), `statistics`
(`ArrayData`, parsed from `STATIS`), `revive_configuration` (`SinglefileData`, the
`REVCON` restart file).

Conditionally produced, controlled by CONTROL keys:

- `rdf` (`SinglefileData`, from `RDFDAT`) — only if `rdf_calculate` is truthy/`"ON"` in
  CONTROL.
- `history` (`TrajectoryData`, parsed from `HISTORY`) — only if `traj_calculate` is
  truthy/`"ON"` in CONTROL.

If one of these keys is set but the corresponding file isn't found among the retrieved
outputs, the calcjob exits with an error (see below) rather than silently omitting it.

## Exit codes

| Code | Name | Meaning |
|---|---|---|
| 300 | `ERROR_OUTPUT_NOT_FOUND` | The `OUTPUT` file wasn't retrieved — check the job actually ran. |
| 301 | `ERROR_DL_POLY_DRIVER_FAILED` | DL_POLY itself raised an error; read the retrieved `OUTPUT` file for the reason. |
| 302 | `ERROR_STATIS_NOT_FOUND` | The `STATIS` file wasn't retrieved. |
| 303 | `ERROR_REVCON_NOT_FOUND` | The `REVCON` file wasn't retrieved. |
| 304 | `ERROR_RDFDAT_NOT_FOUND` | `rdf_calculate` was set but no `RDFDAT` file was retrieved. |
| 305 | `ERROR_HISTORY_NOT_FOUND` | `traj_calculate` was set but no `HISTORY` file was retrieved. |

When a job fails, load the `output` node (if present) and read it before guessing further.
