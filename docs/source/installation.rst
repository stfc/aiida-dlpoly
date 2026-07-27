Installation
============

Installing the plugin
---------------------

``aiida-dlpoly`` is available on `PyPI <https://pypi.org/project/aiida-dlpoly/>`_
and should be installed using `pip <https://pip.pypa.io/en/stable/>`_ or an
equivalent Python package manager:

.. code-block:: bash

   pip install aiida-dlpoly

Requirements
------------

To use this plugin a configured AiiDA profile and computer instance are
required. See the
`AiiDA getting started guide
<https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/get_started.html>`_
for instructions on how to install and configure AiiDA, and
`running external codes
<https://aiida.readthedocs.io/projects/aiida-core/en/stable/howto/run_codes.html>`_
for how to configure AiiDA to link to external software.

A working DL_POLY executable (``DLPOLY.Z``) is also required. See the
`DL_POLY documentation <https://ccp5.gitlab.io/dl-poly/>`_ for build and
installation instructions.

Configuring a DL_POLY code
--------------------------

Once the prerequisites above are in place, an AiiDA code instance needs to be
configured for the DL_POLY executable.

The following is an example of a basic YAML configuration file for a DL_POLY
code running with MPI on the local machine:

.. code-block:: yaml

   label: dlpoly
   description: DL_POLY
   computer: localhost
   filepath_executable: /absolute/path/to/DLPOLY.Z
   default_calc_job_plugin: dlpoly
   use_double_quotes: false
   with_mpi: true
   prepend_text: ''
   append_text: ''

The configuration options are:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Option
     - Description
   * - ``label``
     - The label used to refer to the code (e.g. ``verdi code show dlpoly``).
   * - ``description``
     - A free-text description of the code.
   * - ``computer``
     - The label of a configured AiiDA computer instance the code runs on.
   * - ``filepath_executable``
     - The absolute path to the compiled DL_POLY executable.
   * - ``default_calc_job_plugin``
     - The AiiDA calculation plugin to associate with the code; use ``dlpoly``.
   * - ``use_double_quotes``
     - Whether command-line arguments are wrapped in double quotes.
   * - ``with_mpi``
     - Whether the executable is launched with the computer's MPI runner.
   * - ``prepend_text``
     - Shell commands run before the executable (e.g. ``module load`` lines).
   * - ``append_text``
     - Shell commands run after the executable.

Creating the code
-----------------

Write the configuration to a file named ``dlpoly_config.yml``, ensuring that the
value for ``computer`` matches the label of your configured computer instance and
the ``filepath_executable`` entry is the absolute path to a compiled DL_POLY
executable.

The code can then be configured by running:

.. code-block:: bash

   verdi code create core.code.installed --config dlpoly_config.yml -n

If successful, this will have created a code with the label ``dlpoly`` which can
then be used to run DL_POLY jobs within the AiiDA workflow. See :doc:`usage` for
examples.
