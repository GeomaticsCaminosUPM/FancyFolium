"""Sphinx configuration for FancyFolium's documentation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the package importable without installing it, and expose its version.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import FancyFolium  # noqa: E402

project = "FancyFolium"
copyright = "2026, Miguel Ureña Pliego"
author = "Miguel Ureña Pliego"
release = FancyFolium.__version__
version = release

extensions = [
    "sphinx.ext.autodoc",       # pull docstrings from the source
    "sphinx.ext.napoleon",      # parse Google-style docstrings
    "sphinx.ext.viewcode",      # add "view source" links
    "sphinx.ext.intersphinx",   # link out to numpy/pandas/geopandas/folium docs
    "sphinx_autodoc_typehints", # render type hints in the signature, not inline
    "myst_parser",              # allow Markdown pages (this file's siblings)
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Napoleon (Google-style docstrings) --------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_use_rtype = False

# -- Autodoc ------------------------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}
# Third-party imports not needed just to build the docs; mock them out so
# `import FancyFolium` succeeds even without a full geo-stack installed.
autodoc_mock_imports = ["rasterio"]

# -- Intersphinx ----------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "geopandas": ("https://geopandas.org/en/stable/", None),
}

# -- MyST (Markdown) -----------------------------------------------------
myst_enable_extensions = ["colon_fence"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- HTML output ------------------------------------------------------------
html_theme = "furo"
html_title = f"FancyFolium {release}"
html_static_path = []
