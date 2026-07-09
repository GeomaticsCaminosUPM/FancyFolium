"""
map_core.py - FancyFolium internal helpers

Private (leading-underscore) utilities shared by every layer builder in
``layers/``: per-map state storage, the custom control-panel/legend HTML+JS
injection, and legend-spec construction. Not part of the public API.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import folium
import numpy as np
import pandas as pd

from .utils.color import CmapArg, resolve_cmap
from .utils.tiles import MAX_ZOOM, DEFAULT_ZOOM

_HERE      = Path(__file__).parent
_CSS_FILE  = _HERE / "assets" / "map_controls.css"
_JS_FILE   = _HERE / "assets" / "map_controls.js"
_STATE_KEY = "maplib"


def _state(m: folium.Map) -> dict:
    """Get (creating if needed) the per-map FancyFolium state dict.

    The state is stashed as a plain attribute on the ``folium.Map``
    instance so it survives across multiple layer-builder calls that share
    the same map object.

    Args:
        m: The map to fetch/attach state to.

    Returns:
        The map's mutable state dict (layers lists, legends, etc.).
    """
    if not hasattr(m, _STATE_KEY):
        object.__setattr__(m, _STATE_KEY, {
            "background_layers": [],
            "raster_layers":     [],
            "vector_layers":     [],
            "bg_raster_layers":  [],
            "bg_vector_layers":  [],
            "legends":           {},
            "map_id":            m.get_name(),
            "_assets_injected":  False,
        })
    return getattr(m, _STATE_KEY)


def _unique_id() -> str:
    """Generate a short, unique layer id.

    Returns:
        An id of the form ``"L" + 8 hex characters``.
    """
    return "L" + uuid.uuid4().hex[:8]


def _reset_view(m: folium.Map, bounds_4326: Sequence[float]) -> None:
    """Recentre the map's initial view on a bounding box.

    Args:
        m: The map to update (mutates ``m.location``/``m.zoom_start``).
        bounds_4326: ``(minx, miny, maxx, maxy)`` in EPSG:4326.
    """
    lat = (bounds_4326[1] + bounds_4326[3]) / 2
    lon = (bounds_4326[0] + bounds_4326[2]) / 2
    m.location   = [lat, lon]
    m.zoom_start = DEFAULT_ZOOM


def _accumulate_bounds(m: folium.Map, bounds_4326: Sequence[float]) -> None:
    """Grow the map's view to cover every layer added so far.

    Unlike :func:`_reset_view`, this unions the new bounds with whatever
    was accumulated from previous layer calls, so the view isn't re-centred
    on only the most recently added layer's extent.

    Args:
        m: The map to update.
        bounds_4326: The new layer's ``(minx, miny, maxx, maxy)`` in
            EPSG:4326, to be unioned with the map's existing bounds.
    """
    st = _state(m)
    prev = st.get("_bounds")
    if prev is None:
        merged = tuple(bounds_4326)
    else:
        merged = (
            min(prev[0], bounds_4326[0]),
            min(prev[1], bounds_4326[1]),
            max(prev[2], bounds_4326[2]),
            max(prev[3], bounds_4326[3]),
        )
    st["_bounds"] = merged
    _reset_view(m, merged)


def _css() -> str:
    """Read the bundled control-panel stylesheet.

    Returns:
        The contents of ``assets/map_controls.css``.
    """
    return _CSS_FILE.read_text(encoding="utf-8")


def _js() -> str:
    """Read the bundled control-panel script.

    Returns:
        The contents of ``assets/map_controls.js``.
    """
    return _JS_FILE.read_text(encoding="utf-8")


def _inject_assets(m: folium.Map) -> None:
    """Inject the control-panel CSS into the map's HTML head, once.

    Args:
        m: The map to inject assets into.
    """
    st = _state(m)
    if st["_assets_injected"]:
        return
    m.get_root().header.add_child(folium.Element(f"<style>\n{_css()}\n</style>"))
    st["_assets_injected"] = True


def _rebuild_control_panel(m: folium.Map) -> None:
    """Re-render the layer-control panel, legends, and stats-panel script.

    Called by every layer builder after registering its layer, so the
    panel/legend HTML embedded in the map always reflects the current set
    of layers. Safe to call repeatedly - each call replaces the previous
    panel/script elements.

    Args:
        m: The map to (re)build the control panel for.
    """
    _inject_assets(m)
    st  = _state(m)
    mid = m.get_name()

    bg_layers  = st["background_layers"] + st["bg_raster_layers"] + st["bg_vector_layers"]
    rst_layers = st["raster_layers"]
    vec_layers = st["vector_layers"]

    def _layer_info(layers: List[dict]) -> List[dict]:
        """Project internal layer-entry dicts to the subset sent to the JS side.

        Args:
            layers: Internal layer-entry dicts (one of ``st["background_layers"]``,
                ``st["raster_layers"]``, ``st["vector_layers"]``, etc.).

        Returns:
            A list of plain dicts holding only the fields the control-panel
            JS needs (``name``, ``overlay``, ``id``, ``active``, ``js_var``,
            plus the stats-panel metadata fields).
        """
        return [
            {
                "name":    l["name"],
                "overlay": l["overlay"],
                "id":      l["id"],
                "active":  l.get("active", True),
                "js_var":  l.get("js_var", ""),
                # extra metadata for stats panel
                "column":        l.get("column", None),
                "is_num":        l.get("is_num", None),
                "marker_column": l.get("marker_column", None),
                "rows":          l.get("rows", None),
            }
            for l in layers
        ]

    init_data = {
        "mapId":     mid,
        "bgLayers":  _layer_info(bg_layers),
        "rstLayers": _layer_info(rst_layers),
        "vecLayers": _layer_info(vec_layers),
    }

    legends_js = json.dumps(st["legends"])

    has_bg  = bool(bg_layers)
    has_rst = bool(rst_layers)
    has_vec = bool(vec_layers)
    if not (has_bg or has_rst or has_vec):
        has_bg = True

    first_active = "vector" if has_vec else ("bg" if has_bg else "raster")

    def _tab(key: str, label: str, has: bool) -> str:
        """Render one control-panel tab button, or "" if its section is empty.

        Args:
            key: Section key (``"bg"``, ``"raster"``, or ``"vector"``).
            label: Display label shown on the tab button.
            has: Whether the section has any layers; if ``False`` the tab
                is omitted entirely.

        Returns:
            The tab button's HTML, or ``""`` if ``has`` is ``False``.
        """
        if not has: return ""
        cls = " active" if key == first_active else ""
        return (f'<button class="maplib-tab{cls}" onclick="maplibTab(this,\'{key}\')">{label}</button>\n')

    def _panel(key: str, has: bool) -> str:
        """Render one control-panel body section, or "" if it's empty.

        Args:
            key: Section key (``"bg"``, ``"raster"``, or ``"vector"``).
            has: Whether the section has any layers; if ``False`` the panel
                body is omitted entirely.

        Returns:
            The panel body's HTML, or ``""`` if ``has`` is ``False``.
        """
        if not has: return ""
        cls = " active" if key == first_active else ""
        return f"""
  <div id="maplib-panel-{key}" class="maplib-panel-body{cls}">
    <div id="maplib-{key}-dropdown-wrap" class="maplib-dropdown-wrap"></div>
    <hr class="maplib-sep" id="maplib-{key}-sep">
    <div id="maplib-{key}-checks" class="maplib-checks"></div>
  </div>"""

    tabs_html = (
        _tab("bg", "Background", has_bg)
        + _tab("raster", "Raster", has_rst)
        + _tab("vector", "Vector", has_vec)
    )
    panels_html = (
        _panel("bg", has_bg)
        + _panel("raster", has_rst)
        + _panel("vector", has_vec)
    )

    panel_html = f"""
<!-- FancyFolium control panel -->
<div id="maplib-panel" class="maplib-panel">
  <div class="maplib-tabs">
{tabs_html}  </div>
{panels_html}
</div>
<div id="maplib-legend-@@MID@@" class="maplib-legend-container"></div>
<script>
(function(){{
  var _MAPLIB = @@INIT_DATA@@;
  window._MAPLIB_DATA    = window._MAPLIB_DATA    || {{}};
  window._MAPLIB_LEGENDS = window._MAPLIB_LEGENDS || {{}};
  window._MAPLIB_DATA["@@MID@@"]    = _MAPLIB;
  window._MAPLIB_LEGENDS["@@MID@@"] = @@LEGENDS@@;
  function waitAndInit() {{
    if (typeof maplibInit === "function" &&
        window["@@MID@@"] && window["@@MID@@"].getPane) {{
      maplibInit("@@MID@@", _MAPLIB);
    }} else {{
      setTimeout(waitAndInit, 100);
    }}
  }}
  waitAndInit();
}})();
</script>
"""
    panel_html = (
        panel_html
        .replace("@@MID@@",       mid)
        .replace("@@INIT_DATA@@", json.dumps(init_data))
        .replace("@@LEGENDS@@",   legends_js)
    )

    m.get_root().html.add_child(folium.Element(panel_html), name="maplib_panel")
    m.get_root().html.add_child(
        folium.Element(f"<script>\n{_js()}\n</script>"),
        name="maplib_js",
    )


def _build_legend_spec(
    *,
    layer_name: str,
    column: Optional[str],
    series: Optional[pd.Series],
    cmap: CmapArg,
    vmin: Optional[float],
    vmax: Optional[float],
    categorical: bool,
    count: bool = False,
    unit: Optional[str] = None,
    legend_override: Optional[dict] = None,
) -> Optional[dict]:
    """Build a numeric or categorical legend spec for a colormap column.

    Args:
        layer_name: Display name of the layer, used in the legend title.
        column: Name of the column driving the colormap, or ``None`` if the
            layer uses a uniform colour (in which case no legend is built).
        series: The column's values, or ``None``.
        cmap: Colour map argument (see
            :func:`FancyFolium.utils.color.resolve_cmap`).
        vmin: Lower scale bound for numeric columns.
        vmax: Upper scale bound for numeric columns.
        categorical: Force categorical treatment even for numeric columns.
        count: Treat as a "counts" column - changes the numeric ``vmin``/
            ``vmax`` defaults to ``0``/``series.max()``.
        unit: Optional unit string appended to numeric legend labels.
        legend_override: A caller-supplied legend spec (e.g. from
            :func:`FancyFolium.raster_layer`'s ``legend=`` dict) to
            normalise and return as-is instead of building one from
            ``column``/``series``.

    Returns:
        A legend spec dict (``{"type": "numeric" | "categorical", ...}``),
        or ``None`` if there's nothing to show a legend for.
    """
    if legend_override is not None:
        spec = dict(legend_override)
        spec.setdefault("name", layer_name)
        if "type" not in spec:
            spec["type"] = "categorical" if "entries" in spec else "numeric"
        return spec

    if column is None or series is None:
        return None

    is_num = pd.api.types.is_numeric_dtype(series) and not categorical

    if is_num and not isinstance(cmap, (dict, list)):
        fn = resolve_cmap(cmap, is_categorical=False)
        v0 = vmin if vmin is not None else (0.0 if count else float(np.nanpercentile(series.dropna(), 10)))
        v1 = vmax if vmax is not None else (float(series.dropna().max()) if count else float(np.nanpercentile(series.dropna(), 90)))
        stops = [[i / 20, fn(i / 20)] for i in range(21)]
        return {"type": "numeric", "name": f"{layer_name} – {column}",
                "vmin": v0, "vmax": v1, "unit": unit, "colors": stops}
    else:
        unique_vals = series.dropna().unique().tolist()
        resolved = resolve_cmap(cmap, is_categorical=True, unique_vals=unique_vals)
        color_map = resolved if isinstance(resolved, dict) else resolved(unique_vals)
        return {"type": "categorical", "name": f"{layer_name} – {column}",
                "entries": [{"label": str(v), "color": color_map.get(v, "#ccc")} for v in unique_vals]}


def _build_marker_legend_spec(
    *,
    layer_name: str,
    categories: List[str],
    marker_map: Dict[str, str],
) -> Optional[dict]:
    """Build a legend spec mapping each ``marker_column`` category to its icon.

    Independent of (and shown alongside, when applicable) any colour legend
    for a separate ``column`` - see :func:`FancyFolium.marker_layer`.

    Args:
        layer_name: Display name of the layer, used in the legend title.
        categories: The ``marker_column``'s unique category values.
        marker_map: Mapping of each category to its resolved symbol/emoji.

    Returns:
        A ``{"type": "markers", ...}`` legend spec dict, or ``None`` if
        ``categories`` is empty.
    """
    if not categories:
        return None
    return {
        "type": "markers",
        "name": f"{layer_name} – markers",
        "entries": [{"label": c, "icon": marker_map.get(c, c)} for c in categories],
    }


def _default_map() -> folium.Map:
    """Create a blank, state-initialised map with a default Google Hybrid background.

    Used by every layer builder as the fallback when no ``m=`` is passed in.

    Returns:
        A new ``folium.Map`` with FancyFolium state attached and a Google
        Hybrid background layer already registered.
    """
    from .utils.tiles import TILE_PROVIDERS
    m = folium.Map(location=[0, 0], zoom_start=DEFAULT_ZOOM, tiles=None,
                   max_zoom=MAX_ZOOM, control_scale=True)
    _state(m)
    tl = folium.TileLayer(
        tiles=TILE_PROVIDERS["google hybrid"][0], name="Google Hybrid", attr="Google",
        overlay=False, control=False, max_zoom=MAX_ZOOM,
        max_native_zoom=TILE_PROVIDERS["google hybrid"][2], opacity=0.6, show=True,
    )
    tl.add_to(m)
    _state(m)["background_layers"].append({
        "name": "Google Hybrid", "overlay": False, "id": _unique_id(),
        "active": True, "js_var": tl.get_name(),
    })
    return m
