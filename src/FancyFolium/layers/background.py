"""
layers/background.py
=====================
``background_layer()`` — add a tile-based background layer to the map.
"""

from __future__ import annotations
from typing import Optional
import folium
from ..map_core import _state, _unique_id, _rebuild_control_panel
from ..utils.tiles import TILE_PROVIDERS, MAX_ZOOM, DEFAULT_ZOOM


def background_layer(
    name_or_url: str,
    layer_name: Optional[str] = None,
    opacity: Optional[float] = None,
    overlay: bool = False,
    active: bool = True,
    m: Optional[folium.Map] = None,
) -> folium.Map:
    """Add a background tile layer to the map.

    Background layers are radio-style (only one non-overlay layer active
    at a time) unless ``overlay=True``, in which case it can be toggled
    independently alongside others.

    Args:
        name_or_url: A key from ``FancyFolium.utils.tiles.TILE_PROVIDERS``
            (e.g. ``"google hybrid"``, ``"osm"``, ``"cartodb light"``,
            case-insensitive) or a custom Leaflet tile URL template
            containing ``{x}``/``{y}``/``{z}`` placeholders.
        layer_name: Display name shown in the control panel. Defaults to
            ``name_or_url``.
        opacity: Layer opacity in ``[0, 1]``. Defaults to the provider's
            own default (e.g. Google Hybrid defaults to ``0.6`` so the
            underlying imagery stays legible through its labels), or
            ``1.0`` for custom URLs.
        overlay: If ``True``, shown as an independently toggleable
            checkbox rather than a radio-style background choice.
        active: Whether the layer starts visible.
        m: Map to add the layer to. A new map is created if omitted.

    Returns:
        The map, for chaining.
    """
    key = name_or_url.lower().strip()
    if key in TILE_PROVIDERS:
        tile_url, attr, native_zoom, default_opacity = TILE_PROVIDERS[key]
        display_name = layer_name or name_or_url
    else:
        tile_url        = name_or_url
        attr            = layer_name or "Custom"
        display_name    = layer_name or name_or_url
        native_zoom     = 20
        default_opacity = 1.0

    if opacity is None:
        opacity = default_opacity

    if m is None:
        m = folium.Map(location=[0, 0], zoom_start=DEFAULT_ZOOM, tiles=None,
                       max_zoom=MAX_ZOOM, control_scale=True)
        _state(m)

    st = _state(m)
    if not overlay and active:
        for entry in st["background_layers"]:
            if not entry["overlay"]:
                entry["active"] = False

    tl = folium.TileLayer(
        tiles=tile_url,
        name=display_name,
        attr=attr,
        overlay=overlay,
        control=False,
        max_zoom=MAX_ZOOM,
        max_native_zoom=native_zoom,
        show=True,   # always render; JS init hides inactive ones
        opacity=opacity,
    )
    tl.add_to(m)

    st["background_layers"] = [l for l in st["background_layers"] if l["name"] != display_name]
    st["background_layers"].append({
        "name":    display_name,
        "overlay": overlay,
        "id":      _unique_id(),
        "active":  active,
        "js_var":  tl.get_name(),
    })

    _rebuild_control_panel(m)
    return m