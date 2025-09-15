# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2023 Benjamin Thomas Schwertfeger
# All rights reserved.
# https://github.com/btschwertfeger
#
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# pylint: disable=invalid-name

"""
This module is the configuration for the Sphinx documentation building process.
"""

import sys
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "infinity-grid"
copyright = "2025, Benjamin Thomas Schwertfeger"  # noqa: A001 # pylint: disable=redefined-builtin
author = "Benjamin Thomas Schwertfeger"

# Import the local package
sys.path.insert(0, str(Path("..").resolve() / "src"))

rst_epilog = ""
# Read link all targets from file
with Path("links.rst").open(encoding="utf-8") as f:
    rst_epilog += f.read()


# def setup(app: Any) -> None:
#     """Setup function to modify doc building"""
#     copyfile(
#         Path("..") / "tools" / "backtesting" / "Backtesting.ipynb",
#         Path("Backtesting.ipynb"),
#     )


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


extensions = [
    "IPython.sphinxext.ipython_console_highlighting",
    "nbsphinx",
    "sphinx_click",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "links.rst",
    "**.ipynb_checkpoints",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"  # "sphinx_book_theme"  # "sphinx_rtd_theme"
# html_logo = "images/logo.svg" # FIXME
html_static_path = ["_static"]
html_context = {
    "display_github": True,
    "github_user": "btschwertfeger",
    "github_repo": "infinity-grid",
    "github_version": "master/doc/",
}
html_theme_options = {
    # "sidebar_hide_name": True,
    "light_css_variables": {
        "color-brand-primary": "#336790",  # "blue"
        "color-brand-content": "#336790",
    },
    "dark_css_variables": {
        "color-brand-primary": "#E5B62F",  # "yellow"
        "color-brand-content": "#E5B62F",
    },
    "source_repository": "https://github.com/btschwertfeger/infinity-grid",
    "source_branch": "master",
    "source_directory": "doc/",
}
