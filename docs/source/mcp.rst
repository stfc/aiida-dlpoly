MCP integration
================

`aiida-mcp <https://github.com/stfc/aiida-mcp>`_ is a
`Model Context Protocol <https://modelcontextprotocol.io>`_ server that lets an MCP
client, such as an AI assistant, inspect an AiiDA database and submit calculations.
``aiida-dlpoly`` ships its own integration module, ``aiida_dlpoly.mcp``, which exposes
DL_POLY as a pair of MCP tools.

Installing the optional ``mcp`` extra:

.. code-block:: bash

   pip install "aiida-dlpoly[mcp]"

pulls in aiida-mcp and registers ``aiida_dlpoly.mcp`` under its ``aiida_mcp.plugins``
entry point group. Any aiida-mcp server running in the same environment then
automatically exposes ``describe_dlpoly_calcjob`` and ``submit_dlpoly_job`` tools — no
changes needed in aiida-mcp itself. See aiida-mcp's own documentation for how to run the
server and its other tools.

``submit_dlpoly_job``
----------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Argument
     - Meaning
   * - ``code``
     - Label (e.g. ``dl_poly@localhost``) or PK of the DL_POLY code.
   * - ``configuration``
     - The ``CONFIG`` file, or a ``StructureData`` node.
   * - ``field``
     - The ``FIELD`` file.
   * - ``control``
     - The ``CONTROL`` file, or a dict of parameters.
   * - ``num_machines``
     - Machines to run on. Default 1.
   * - ``num_mpiprocs_per_machine``
     - MPI processes per machine. Default 1.
   * - ``label``
     - Optional label to set on the calcjob node.
   * - ``description``
     - Optional description to set on the calcjob node.

Each of ``configuration``, ``field`` and ``control`` takes **exactly one** of ``path`` (a
file on the machine running the server), ``text`` (the file contents as a string), or
``pk`` (an existing node in the database). ``configuration`` accepts ``SinglefileData``
or ``StructureData``, ``field`` accepts ``SinglefileData``, and ``control`` accepts
``SinglefileData`` or ``Dict``. ``control`` also accepts ``parameters``, a dictionary
stored as a ``Dict`` node.

Example arguments:

.. code-block:: json

   {
     "code": "dl_poly@localhost",
     "configuration": {"path": "/data/TEST001/CONFIG"},
     "field": {"path": "/data/TEST001/FIELD"},
     "control": {"path": "/data/TEST001/CONTROL"}
   }

The inputs are checked against the calcjob definition before anything is stored — a bad
input returns an error and creates no nodes. On success the tool returns the process PK
and the PKs of the input nodes; follow the job with aiida-mcp's ``get_process`` and
``get_process_report`` tools. If the daemon is stopped, the job is created and waits
until the daemon starts, and the result says so.

A typical session: call ``get_status``, call ``list_codes`` to find the code, call
``submit_dlpoly_job``, then poll ``get_process`` until ``state`` is ``finished`` and
check ``exit_status``. An ``exit_status`` of 0 means success; other values are listed by
``describe_dlpoly_calcjob``.
