Agent Skill
===========

`aiida-dlpoly` ships an `Agent Skill <https://www.anthropic.com/news/skills>`_ — a
``SKILL.md`` file describing how to set up, submit and troubleshoot DL_POLY calculations
with this plugin, for AI assistants (such as Claude Code) that support the format. It
covers configuring a DL_POLY code, the two submission paths (a plain AiiDA script, or the
:doc:`mcp` tools), building a ``CONTROL`` ``Dict``, the calcjob's outputs, and its exit
codes.

It is installed alongside the package at ``aiida_dlpoly/skills/aiida-dlpoly/SKILL.md``. The
``aiida-dlpoly`` command installs it into your assistant's skills directory:

.. code-block:: bash

   aiida-dlpoly skills install

This copies the skill into ``~/.claude/skills/`` by default. Pass a directory to install
somewhere else, e.g. a project-local ``.claude/skills/``:

.. code-block:: bash

   aiida-dlpoly skills install .claude/skills
