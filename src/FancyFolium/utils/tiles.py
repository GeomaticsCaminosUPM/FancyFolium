"""
utils/tiles.py
==============
Tile provider registry for FancyFolium.

Each entry maps a lowercase key → (tile_url_template, attribution_string).
The URL templates use {x}, {y}, {z} (and optionally {s}, {r}) placeholders
as expected by Leaflet TileLayer.

Max zoom notes
--------------
Most tile providers top out at native zoom 19–20.  Leaflet can still render
beyond that by up-scaling the last available tile — this is controlled by
``max_native_zoom`` (last available tile) vs ``max_zoom`` (Leaflet UI limit).
We set max_zoom=26 globally so users can always zoom in; Leaflet will
gracefully up-scale beyond max_native_zoom.
"""

from __future__ import annotations

from typing import Dict, Tuple

# (tile_url, attribution, max_native_zoom, default_opacity)
TileEntry = Tuple[str, str, int, float]

TILE_PROVIDERS: Dict[str, TileEntry] = {
    # Google Hybrid overlays labels/roads on satellite imagery; a lower
    # default opacity keeps the underlying imagery legible through the labels.
    "google hybrid": (
        "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        "Google",
        20,
        0.6,
    ),
    "google satellite": (
        "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "Google",
        20,
        1.0,
    ),
    "google roads": (
        "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        "Google",
        20,
        1.0,
    ),
    "osm": (
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "© OpenStreetMap contributors",
        19,
        1.0,
    ),
    "openstreetmap": (
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "© OpenStreetMap contributors",
        19,
        1.0,
    ),
    "cartodb light": (
        "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "© CartoDB",
        19,
        1.0,
    ),
    "cartodb dark": (
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        "© CartoDB",
        19,
        1.0,
    ),
    "esri satellite": (
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "Esri",
        19,
        1.0,
    ),
    "stamen toner": (
        "https://stamen-tiles-{s}.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
        "Map tiles by Stamen Design",
        18,
        1.0,
    ),
    "stamen terrain": (
        "https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
        "Map tiles by Stamen Design",
        18,
        1.0,
    ),
}

# Leaflet UI zoom cap applied to every map and layer.
# Tiles beyond max_native_zoom are up-scaled automatically.
MAX_ZOOM = 26
DEFAULT_ZOOM = 16
