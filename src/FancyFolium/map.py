"""
map.py  (FancyFolium)
=====================
Top-level public API shims.  Provides:
  - create_map()
  - merge_maps()
  - export()

Layer functions live in layers/ and are re-exported from __init__.py.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

import folium

from .map_core import (
    _state, _inject_assets, _rebuild_control_panel,
)
from .utils.tiles import MAX_ZOOM, DEFAULT_ZOOM


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC: create_map
# ═══════════════════════════════════════════════════════════════════════════

def create_map(
    location: Optional[List[float]] = None,
    zoom: int = DEFAULT_ZOOM,
) -> folium.Map:
    """Create a blank Folium map with the FancyFolium control panel attached.

    No background tile is added - use :func:`background_layer` for that.

    Args:
        location: Initial ``[lat, lon]`` center. Defaults to ``[0, 0]``.
        zoom: Initial zoom level.

    Returns:
        A new, empty ``folium.Map`` with FancyFolium state and control
        panel already attached.
    """
    if location is None:
        location = [0, 0]
    m = folium.Map(
        location=location,
        zoom_start=zoom,
        tiles=None,
        max_zoom=MAX_ZOOM,
        control_scale=True,
    )
    _state(m)
    _rebuild_control_panel(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC: merge_maps
# ═══════════════════════════════════════════════════════════════════════════

def merge_maps(
    maps: List[folium.Map],
    names: List[str],
) -> folium.Map:
    """Combine multiple independent maps into one with a top-centre dropdown.

    Every layer from every map is reparented onto the first map (``maps[0]``,
    the "base"); the dropdown switcher then toggles their visibility, so
    switching never needs to load or render a different Leaflet map
    instance. Layers with the same name across maps are treated as
    corresponding to each other when preserving active state on switch.

    Args:
        maps: Maps to combine - at least two are required.
        names: Display name for each map's dropdown entry, in the same
            order as ``maps``.

    Returns:
        The first map in ``maps``, now containing every layer from all
        maps plus the dropdown switcher UI.

    Raises:
        ValueError: If ``maps`` and ``names`` differ in length, or fewer
            than two maps are given.
    """
    if len(maps) != len(names):
        raise ValueError(
            f"merge_maps: maps and names must have the same length "
            f"({len(maps)} maps, {len(names)} names)."
        )
    if len(maps) < 2:
        raise ValueError("merge_maps: at least two maps are required.")

    base = maps[0]

    map_data = []
    for mi, name in zip(maps, names):
        st = _state(mi)
        map_data.append({
            "name":      name,
            "mapId":     mi.get_name(),
            "center":    mi.location or [0, 0],
            "zoom":      mi.zoom_start or DEFAULT_ZOOM,
            "bgLayers":  (
                st.get("background_layers", [])
                + st.get("bg_raster_layers", [])
                + st.get("bg_vector_layers", [])
            ),
            "rstLayers": st.get("raster_layers", []),
            "vecLayers": st.get("vector_layers", []),
        })

    for mi in maps[1:]:
        for child in mi._children.values():
            child.add_to(base)

    # Only base's own control-panel script (added by create_map/_rebuild_control_panel)
    # ends up in the saved HTML - every other map's `get_root().html` children (its
    # legend div + the script populating window._MAPLIB_LEGENDS[its mapId]) are
    # discarded since only `base` is rendered. Re-inject those legends here so the
    # switcher has something to look up when it points at a non-base city.
    legends_by_map = {
        mi.get_name(): _state(mi).get("legends", {})
        for mi in maps[1:]
    }
    legends_script = f"""
<script>
window._MAPLIB_LEGENDS = window._MAPLIB_LEGENDS || {{}};
Object.assign(window._MAPLIB_LEGENDS, {json.dumps(legends_by_map)});
</script>
"""
    base.get_root().html.add_child(
        folium.Element(legends_script), name="maplib_merged_legends"
    )

    opts_html = "\n".join(
        f'<option value="{d["mapId"]}">{d["name"]}</option>'
        for d in map_data
    )
    switcher_html = f"""
<div id="maplib-switcher" class="maplib-switcher">
  <label style="font-weight:600;font-size:12px;display:block;margin-bottom:4px;">Map</label>
  <select id="maplib-switcher-select" onchange="maplibSwitchMap(this.value)"
          style="width:100%;font-size:13px;padding:3px 6px;border-radius:4px;border:1px solid #bbb;">
    {opts_html}
  </select>
</div>
<script>
(function(){{
  window._MAPLIB_MAPS = {json.dumps(map_data)};
  function waitSwitcher() {{
    if (typeof maplibInitSwitcher === "function") {{
      maplibInitSwitcher(window._MAPLIB_MAPS);
    }} else {{
      setTimeout(waitSwitcher, 200);
    }}
  }}
  waitSwitcher();
}})();
</script>
"""
    base.get_root().html.add_child(
        folium.Element(switcher_html), name="maplib_switcher"
    )
    _inject_assets(base)

    from .map_core import _js
    base.get_root().html.add_child(
        folium.Element(f"<script>\n{_js()}\n</script>"),
        name="maplib_js",
    )
    return base


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC: export
# ═══════════════════════════════════════════════════════════════════════════

def export(
    m: folium.Map,
    path: str,
    raster_path: str = "rasters",
) -> None:
    """Export a map as an HTML file with raster overlays as sibling files.

    Base64-embedded raster images are always extracted to
    ``{html_dir}/{raster_path}/`` as individual JPEG/PNG files, and the HTML
    is rewritten to reference them via relative paths instead of embedding
    them inline - this keeps the HTML file itself small even when a map has
    many or large raster overlays.

    Args:
        m: The map to export.
        path: Destination HTML file path. Parent directories are created
            if needed.
        raster_path: Subdirectory (relative to ``path``'s parent) that
            extracted raster images are written to.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out_path))

    raster_dir = out_path.parent / raster_path
    raster_dir.mkdir(parents=True, exist_ok=True)

    html_text = out_path.read_text(encoding="utf-8")
    # folium embeds ImageOverlay images as a raw JS string literal
    # (`L.imageOverlay("data:image/png;base64,...", ...)`), not as an HTML
    # `src="..."` attribute, so the match must not require a `src=` prefix - # only the quoted data-URI itself.
    pattern = re.compile(r'"(data:image/(png|jpeg);base64,([^"]+))"')
    idx     = 0

    def _replacer(match: "re.Match") -> str:
        """Write one embedded base64 image to disk and return its relative path, quoted.

        Args:
            match: A regex match of a quoted ``data:image/(png|jpeg);base64,...``
                data-URI, as produced by :attr:`pattern`.

        Returns:
            The quoted, forward-slash relative path (e.g. ``"rasters/raster_0000.jpg"``)
            to substitute in place of the matched data-URI.
        """
        nonlocal idx
        import base64 as _b64
        ext   = "jpg" if match.group(2) == "jpeg" else "png"
        fname = f"raster_{idx:04d}.{ext}"
        (raster_dir / fname).write_bytes(_b64.b64decode(match.group(3)))
        idx += 1
        # Always forward slashes: this path is embedded in HTML/JS as a URL,
        # not a filesystem path, so Windows' backslash separator would break it.
        return f'"{(Path(raster_path) / fname).as_posix()}"'

    out_path.write_text(pattern.sub(_replacer, html_text), encoding="utf-8")
    if idx:
        print(f"  Extracted {idx} raster(s) → '{raster_dir}'")

    print(f"✓ Map saved → {out_path}")
