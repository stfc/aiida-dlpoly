Usage
=====

This page shows how to run DL_POLY simulations through the plugin and how to work
with the results. All examples assume the plugin is installed and a code with the
label ``dlpoly`` has been configured (see :doc:`installation`).

Running with existing input files
---------------------------------

The simplest way to run a simulation is to provide existing DL_POLY ``CONTROL``,
``FIELD`` and ``CONFIG`` input files as
:class:`~aiida.orm.nodes.data.singlefile.SinglefileData` nodes:

.. code-block:: python

   from aiida.engine import run
   from aiida.orm import SinglefileData, load_code
   from aiida import load_profile

   load_profile("username")  # Replace with your own AiiDA profile

   builder = load_code("dlpoly").get_builder()
   # Change these to the absolute paths to your input files
   builder.control = SinglefileData(file="/absolute/path/to/CONTROL")
   builder.field = SinglefileData(file="/absolute/path/to/FIELD")
   builder.configuration = SinglefileData(file="/absolute/path/to/CONFIG")

   results, node = run.get_node(builder)

Inputs
------

.. list-table::
   :header-rows: 1
   :widths: 20 30 15 35

   * - Input
     - Accepted types
     - Required
     - Description
   * - ``configuration``
     - ``SinglefileData`` or ``StructureData``
     - Yes
     - The ``CONFIG`` file, or an AiiDA :class:`~aiida.orm.StructureData` node
       describing the molecular/particle system.
   * - ``field``
     - ``SinglefileData``
     - Yes
     - The force field definition file in DL_POLY format.
   * - ``control``
     - ``SinglefileData`` or ``Dict``
     - Yes
     - The simulation control parameters, either as a pre-formatted DL_POLY
       ``CONTROL`` file or as a dictionary of inputs.

Outputs
-------

By default the calculation produces three output nodes:

.. list-table::
   :header-rows: 1
   :widths: 25 25 15 35

   * - Output
     - Type
     - Always produced
     - Description
   * - ``output``
     - ``SinglefileData``
     - Yes
     - The main DL_POLY ``OUTPUT`` file.
   * - ``statistics``
     - ``ArrayData``
     - Yes
     - Statistics collected throughout the simulation (parsed from ``STATIS``).
   * - ``revive_configuration``
     - ``SinglefileData``
     - Yes
     - The final configuration (``REVCON``) that enables simulation restart.
   * - ``rdf``
     - ``SinglefileData``
     - No
     - Radial distribution function data (``RDFDAT``).
   * - ``history``
     - ``TrajectoryData``
     - No
     - The simulation trajectory (``HISTORY``).

The optional ``rdf`` and ``history`` nodes are only produced when the relevant
keys are present in the DL_POLY ``CONTROL`` file (``rdf_calculate`` and
``traj_calculate`` respectively). Further information on AiiDA data types and how
to interact with them can be found in the
`AiiDA data types documentation
<https://aiida.readthedocs.io/projects/aiida-core/en/stable/topics/data_types.html>`_.

Using native AiiDA inputs
-------------------------

The plugin additionally allows the ``control`` and ``configuration`` inputs to
be supplied as native AiiDA nodes — a :class:`~aiida.orm.Dict` and a
:class:`~aiida.orm.StructureData` respectively. The plugin then handles the
relevant file formatting to be compatible with DL_POLY. The example below assumes
a :class:`~aiida.orm.StructureData` node already exists in the database.

.. code-block:: python

   from aiida.engine import run
   from aiida.orm import Dict, load_node, SinglefileData, load_code
   from aiida import load_profile

   load_profile("username")  # Replace with your own AiiDA profile

   builder = load_code("dlpoly").get_builder()
   # Change this to the absolute path to your FIELD file
   builder.field = SinglefileData(file="/absolute/path/to/FIELD")
   # Replace with the pk of an existing StructureData node
   builder.configuration = load_node(pk=10)
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

.. _control-dict-formatting:

Control dictionary formatting
-----------------------------

When the ``control`` input is provided as a :class:`~aiida.orm.Dict`, each
key/value pair is converted into a line of the DL_POLY ``CONTROL`` file. The
value type determines the formatting:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Value type
     - Example
     - Rendered as
   * - String / Path
     - ``"ensemble": "nve"``
     - ``ensemble  nve``
   * - Boolean
     - ``"coul_method": False``
     - ``coul_method  OFF`` (``True`` → ``ON``)
   * - Value with unit (tuple)
     - ``"temperature": (295.0, "K")``
     - ``temperature  295.0 K``
   * - Vector with unit (tuple)
     - ``"padding": (0.2, "ang")``
     - ``padding  0.2 ang``

.. note::

   All numeric inputs to DL_POLY require a unit, so they must be supplied as a
   tuple in the form ``(value, unit)``. Multi-element vectors are rendered inside
   square brackets, e.g. ``(1, 2, 3, "ang")`` becomes ``[1 2 3] ang``. Values
   carrying the ``"steps"`` unit are coerced to integers.

The ``title`` key is treated specially and written as the first line of the
``CONTROL`` file. If no ``title`` is provided, a default title is used.

Converting between files and nodes
----------------------------------

The :mod:`aiida_dlpoly.utils` module also provides helpers for converting
between DL_POLY files and AiiDA nodes outside of a calculation, for example
:func:`~aiida_dlpoly.utils.config_to_structuredata` to build a
:class:`~aiida.orm.StructureData` from a ``CONFIG`` file. See the :doc:`api` for
the full list.
