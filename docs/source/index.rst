aiida-dlpoly documentation
==========================

``aiida-dlpoly`` is an `AiiDA <https://www.aiida.net>`_ plugin for the
`DL_POLY <https://ccp5.gitlab.io/dl-poly/>`_ molecular/particle dynamics
software package.

It exposes DL_POLY as an AiiDA :class:`~aiida.engine.CalcJob`, letting you run,
parse and store molecular dynamics simulations with full data provenance. Inputs
can be provided either as pre-formatted DL_POLY files or as native AiiDA data
nodes (a :class:`~aiida.orm.Dict` for the ``CONTROL`` parameters and a
:class:`~aiida.orm.StructureData` for the configuration), with the plugin
handling the DL_POLY file formatting for you.

Getting started
---------------

* :doc:`installation` — install the plugin and configure a DL_POLY code.
* :doc:`usage` — run simulations and work with the results.
* :doc:`api` — the auto-generated API reference.

.. toctree::
   :maxdepth: 2
   :hidden:

   installation
   usage
   api
