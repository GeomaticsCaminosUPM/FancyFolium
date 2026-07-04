"""
FancyFolium
===========
Composable Folium mapping library with a custom three-panel layer control,
automatic legends, named colourmaps, per-layer custom popup/style, and
vector-to-raster conversion.

Quick start
-----------
    from FancyFolium import create_map, vector_layer, export

    m = create_map()
    m = vector_layer(gdf, column="height", cmap="Reds", overlay=True, m=m)
    export(m, "output/map.html")

File layout
-----------
    FancyFolium/
    ├── __init__.py          Public re-exports (this file)
    ├── map.py               create_map / merge_maps / export
    ├── map_core.py          Internal helpers (state, panel builder, …)
    ├── assets/
    │   ├── map_controls.css
    │   └── map_controls.js
    ├── layers/
    │   ├── background.py    background_layer()
    │   ├── raster.py        raster_layer()
    │   ├── vector.py        vector_layer()
    │   └── marker.py        marker_layer()
    └── utils/
        ├── color.py         Colour scales, cmap resolver
        ├── geo.py           Bounds helpers, CRS conversion
        ├── raster.py        Raster I/O, PNG encoding, vector_to_raster
        └── tiles.py         Tile provider registry
"""

# ── Core API ──────────────────────────────────────────────────────────────
from .map import (
    create_map,
    merge_maps,
    export,
)

# ── Layer functions (import directly, not modules) ────────────────────────
from .layers.background import background_layer
from .layers.raster import raster_layer
from .layers.vector import vector_layer
from .layers.marker import marker_layer

# ── Colour helpers ────────────────────────────────────────────────────────
from .utils.color import (
    hsl_to_hex,
    viridis,
    plasma,
    rdylgn,
    rdylgn_r,
    categorical_colors,
    stable_color,
    percentile_range,
    normalise,
    resolve_cmap,
    compute_feature_colors,
    validate_count_column,
    emoji_for_categories,
    EMOJI_PALETTE,
)

# ── Geometry helpers ──────────────────────────────────────────────────────
from .utils.geo import (
    bounds_center,
    gdf_bounds_wgs84,
    bounds_to_folium,
    raster_bounds_wgs84,
    clip_raster_to_bounds,
)

# ── Raster helpers ────────────────────────────────────────────────────────
from .utils.raster import (
    raster_to_png_base64,
    image_to_png_base64,
    vector_to_raster,
)

__all__ = [
    # core
    "create_map",
    "background_layer",
    "raster_layer",
    "vector_layer",
    "marker_layer",
    "merge_maps",
    "export",
    # colour
    "hsl_to_hex",
    "viridis",
    "plasma",
    "rdylgn",
    "rdylgn_r",
    "categorical_colors",
    "stable_color",
    "percentile_range",
    "normalise",
    "resolve_cmap",
    "compute_feature_colors",
    "validate_count_column",
    "emoji_for_categories",
    "EMOJI_PALETTE",
    # geometry
    "bounds_center",
    "gdf_bounds_wgs84",
    "bounds_to_folium",
    "raster_bounds_wgs84",
    "clip_raster_to_bounds",
    # raster
    "raster_to_png_base64",
    "image_to_png_base64",
    "vector_to_raster",
]

__version__ = "0.1.0"
__author__  = "Miguel Ureña Pliego"