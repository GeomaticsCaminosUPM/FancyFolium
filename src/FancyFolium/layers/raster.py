"""
layers/raster.py
================
``raster_layer()`` - add a georeferenced (or plain) raster image overlay.
"""

from __future__ import annotations
import warnings
from pathlib import Path
from typing import List, Optional
import folium
from ..map_core import _state, _unique_id, _rebuild_control_panel, _accumulate_bounds, _default_map
from ..utils.raster import raster_to_png_base64, image_to_png_base64
from ..utils.color import resolve_cmap
from ..utils.tiles import MAX_ZOOM


def raster_layer(
    raster: str,
    layer_name: Optional[str] = None,
    opacity: float = 1.0,
    bounds: Optional[List[List[float]]] = None,
    *,
    m: Optional[folium.Map] = None,
    overlay: bool = False,
    background: bool = False,
    active: bool = True,
    legend: Optional[dict] = None,
) -> folium.Map:
    """Add a raster image (georeferenced or plain) as a map overlay.

    Args:
        raster: Path to a raster file. If it carries an embedded CRS
            (read via rasterio), its bounds are used automatically;
            otherwise pass ``bounds=`` explicitly.
        layer_name: Display name shown in the control panel. Defaults to
            the file's stem.
        opacity: Overlay opacity in ``[0, 1]``.
        bounds: Explicit ``[[south, west], [north, east]]`` bounds in
            EPSG:4326. Required for images with no embedded CRS; if given
            for a geo-referenced raster, only the overlapping window is
            read.
        m: Map to add the layer to. A new map is created if omitted.
        overlay: If ``True``, shown as an independently toggleable
            checkbox; otherwise a radio-style choice within its category
            (raster, or background if ``background=True``).
        background: If ``True``, registers this as a background layer
            (grouped with tile backgrounds in the control panel) rather
            than a foreground raster layer.
        active: Whether the layer starts visible.
        legend: A pre-built legend spec dict to show for this layer (e.g.
            ``{"entries": [{"label": ..., "color": ...}, ...]}`` for a
            categorical legend, or a numeric spec with ``vmin``/``vmax``/
            ``cmap``). Passed through mostly as-is; ``"colors"`` stops are
            filled in automatically for a numeric spec that omits them.

    Returns:
        The map, for chaining.

    Raises:
        FileNotFoundError: If ``raster`` does not exist.
        ValueError: If the raster has no embedded CRS and no ``bounds``
            were supplied.
    """
    raster_p = Path(raster)
    if not raster_p.exists():
        raise FileNotFoundError(f"Raster file not found: '{raster}'")
    display_name = layer_name or raster_p.stem

    try:
        img_url, img_bounds = raster_to_png_base64(str(raster_p), bounds=bounds)
    except ValueError:
        if bounds is None:
            raise ValueError(f"Raster '{raster}' has no embedded CRS. Supply bounds=.")
        img_url    = image_to_png_base64(str(raster_p))
        img_bounds = bounds
    except Exception as exc:
        if bounds is not None:
            warnings.warn(str(exc), UserWarning, stacklevel=2)
            img_url    = image_to_png_base64(str(raster_p))
            img_bounds = bounds
        else:
            raise

    if m is None:
        m = _default_map()

    st  = _state(m)
    category_key = "bg_raster_layers" if background else "raster_layers"
    if not overlay and active:
        for entry in st[category_key]:
            if not entry["overlay"]:
                entry["active"] = False

    ov = folium.raster_layers.ImageOverlay(
        image=img_url, bounds=img_bounds, opacity=opacity,
        name=display_name, cross_origin=False, zindex=10,
        show=True,   # always render; JS init hides inactive ones
    )
    ov.add_to(m)

    st[category_key] = [l for l in st[category_key] if l["name"] != display_name]
    st[category_key].append({
        "name":    display_name,
        "overlay": overlay,
        "id":      _unique_id(),
        "bounds":  img_bounds,
        "active":  active,
        "js_var":  ov.get_name(),
    })

    if legend is not None:
        spec = dict(legend)
        spec.setdefault("name", display_name)
        if "type" not in spec:
            spec["type"] = "categorical" if "entries" in spec else "numeric"
        if spec["type"] == "numeric" and "colors" not in spec:
            fn = resolve_cmap(spec.get("cmap"), is_categorical=False)
            spec["colors"] = [[i / 20, fn(i / 20)] for i in range(21)]
        st["legends"][display_name] = [spec]

    s_, w_ = img_bounds[0]
    n_, e_ = img_bounds[1]
    _accumulate_bounds(m, (w_, s_, e_, n_))
    _rebuild_control_panel(m)
    return m