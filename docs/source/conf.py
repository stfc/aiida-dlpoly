# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os, sys
import tomllib

sys.path.insert(0, os.path.abspath("../../src/"))

# Read the project version from pyproject.toml so the docs stay in sync with the
# packaged version without needing to be updated manually.
_pyproject_path = os.path.join(os.path.dirname(__file__), "..", "..", "pyproject.toml")
with open(_pyproject_path, "rb") as _f:
    _pyproject = tomllib.load(_f)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'aiida_dlpoly'
copyright = '2026, Dr. Benjamin T. Speake'
author = 'Dr. Benjamin T. Speake'

# The full version, e.g. "0.1.0", and the short X.Y version.
release = _pyproject["project"]["version"]
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
]

templates_path = ['_templates']
exclude_patterns = []

source_suffix = ".rst"
master_doc = 'index'
html_logo = ""

# -- Autodoc / autosummary ---------------------------------------------------
# Regenerate the API stub pages under ``generated/`` on every build so the API
# reference always matches the current source docstrings.
autosummary_generate = True

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# -- Napoleon (numpy-style docstrings) ---------------------------------------
napoleon_numpy_docstring = True
napoleon_google_docstring = False

# -- Intersphinx -------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiida": (
        "https://aiida.readthedocs.io/projects/aiida-core/en/latest/",
        None,
    ),
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'piccolo_theme'
html_static_path = ['_static']
