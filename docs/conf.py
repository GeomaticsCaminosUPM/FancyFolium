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
# _static/example/ holds a pre-built copy of examples/example.ipynb's output
# map (index.html + rasters/), embedded as a live iframe on the Examples
# page - see docs/examples.md. Regenerate it by re-running the notebook and
# copying examples/output/{example_map.html -> _static/example/index.html,
# rasters/ -> _static/example/rasters/}.
html_static_path = ["_static"]

# Author/repo links shown in the footer of every page (not just index.rst).
html_theme_options = {
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/GeomaticsCaminosUPM/FancyFolium",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 '
                '8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>'
            ),
            "class": "",
        },
        {
            "name": "ORCID",
            "url": "https://orcid.org/0000-0001-6594-2566",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 256 256"><path d="M128 24a104 104 0 1 0 104 104A104.11 104.11 0 0 0 128 24ZM99 82a11 11 0 1 1-11 11 11 11 0 0 1 11-11Zm12 92H88V112h12Zm45 0h-12v-40c0-13.23-9.85-16-16-16a15.68 15.68 0 0 0-13 6.94V174H103V112h12v8.35c2.94-4.14 8.86-9.35 20-9.35 15.8 0 21 11.6 21 25Z"/></svg>'
            ),
            "class": "",
        },
        {
            "name": "LinkedIn",
            "url": "https://www.linkedin.com/in/miguel-urena-pliego",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 16 16"><path d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 '
                '0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 '
                '15.487 0 14.854V1.146zm4.943 12.248V6.169H2.542v7.225h2.401zm-1.2-8.212c.837 '
                '0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248-.822 0-1.359.54-1.359 '
                '1.248 0 .694.521 1.248 1.327 1.248h.016zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 '
                '1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 '
                '0-1.845.7-2.165 1.193v.025h-.016a5.54 5.54 0 0 1 .016-.025V6.169h-2.4c.03.678 0 7.225 0 '
                '7.225h2.4z"/></svg>'
            ),
            "class": "",
        },
    ],
}
