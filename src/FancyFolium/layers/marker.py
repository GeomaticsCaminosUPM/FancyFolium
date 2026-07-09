"""
layers/marker.py
================
``marker_layer()`` - add a point GeoDataFrame as colour- and/or icon-coded
markers.
"""

from __future__ import annotations
import warnings
from typing import Dict, List, Optional, Union
import folium
import geopandas as gpd
import pandas as pd
from ..map_core import (
    _state, _unique_id, _rebuild_control_panel, _accumulate_bounds, _default_map,
    _build_legend_spec, _build_marker_legend_spec,
)
from ..utils.color import CmapArg, compute_feature_colors, validate_count_column
from ..utils.geo import gdf_bounds_wgs84
from .vector import PopupArg, StyleArg

MarkerArg = Union[None, str, Dict[str, str]]


def _resolve_marker_map(marker: MarkerArg, categories: List[str]) -> Optional[Dict[str, str]]:
    """Resolve the ``marker`` argument into a ``{category: symbol}`` map.

    Args:
        marker: The ``marker_layer(marker=...)`` argument:

            - ``dict``: user-supplied category -> symbol/emoji override;
              categories not covered fall back to their own raw
              ``marker_column`` value (so a partial override dict doesn't
              blank out the rest).
            - ``str``: not resolved here - a fixed marker is applied
              uniformly by the caller instead of varying per category.
            - ``None``: each row shows its own raw ``marker_column`` value
              as-is - e.g. pre-populate ``marker_column`` with emojis (see
              :func:`FancyFolium.emoji_for_categories`) to have emojis
              shown without needing ``marker=``.
        categories: The ``marker_column``'s unique category values.

    Returns:
        A ``{category: symbol}`` map, or ``None`` if there are no
        categories or ``marker`` isn't a dict (in which case the caller
        falls back to the raw category value or the fixed ``marker`` string).
    """
    if not categories:
        return None
    if isinstance(marker, dict):
        return {c: marker.get(c, c) for c in categories}
    return None


def marker_layer(
    gdf: gpd.GeoDataFrame,
    layer_name: Optional[str] = None,
    column: Optional[str] = None,
    marker_column: Optional[str] = None,
    marker: MarkerArg = None,
    color: str = "blue",
    cmap: CmapArg = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    categorical: bool = False,
    count: bool = False,
    overlay: bool = False,
    popup: PopupArg = None,
    m: Optional[folium.Map] = None,
    style: StyleArg = None,
    legend: bool = True,
    legend_unit: Optional[str] = None,
    active: bool = True,
    histogram: bool = True,
) -> folium.Map:
    """Add a point GeoDataFrame as colour- and/or icon-coded markers.

    Non-point geometries are converted to centroids automatically (with a
    ``UserWarning``). Markers with no ``column``, ``marker``, and
    ``marker_column`` render as a Google-Maps-style teardrop pin; markers
    with an icon (fixed ``marker``, or a resolved ``marker_column`` value)
    render as a coloured/transparent disc with the icon text/emoji inside.

    Args:
        gdf: Source GeoDataFrame. Reprojected to EPSG:4326 automatically if
            it carries a different CRS (a ``UserWarning`` is raised if it
            has no CRS at all, assuming EPSG:4326).
        layer_name: Display name shown in the control panel and legend.
            Defaults to ``column``. Required if ``column`` is ``None``.
        column: Column used for the colormap (numeric, categorical, or
            count - see ``categorical``/``count``).
        marker_column: Column holding the (always categorical) class shown
            as the marker's label/icon, varying per row. Its raw values
            are shown as-is unless overridden by ``marker`` - so
            pre-populate it with emojis (see
            :func:`FancyFolium.emoji_for_categories`, or your own dict of
            category -> emoji) to have emoji markers.
        marker: Either:

            - ``str``: a single fixed symbol used for every row,
              regardless of ``marker_column``.
            - ``dict``: ``{category: symbol/emoji}`` overriding specific
              ``marker_column`` categories; categories not covered fall
              back to their own raw ``marker_column`` value.
            - ``None``: each row shows its own raw ``marker_column`` value.
        color: Uniform fill colour used when ``column`` is ``None``.
        cmap: Colour map argument - see :func:`FancyFolium.vector_layer`.
        vmin: Lower colour-scale bound for numeric/count columns.
        vmax: Upper colour-scale bound for numeric/count columns.
        categorical: Treat ``column`` as categorical. Mutually exclusive
            with ``count``.
        count: Treat ``column`` as a "counts" column (e.g. number of
            storeys, population): validated to hold whole-number values
            only (``TypeError`` otherwise), with the colour scale
            defaulting to ``vmin=0``/``vmax=column.max()`` instead of the
            numeric p10/p90 default. Mutually exclusive with
            ``categorical``.
        overlay: If ``True``, shown as an independently toggleable
            checkbox; otherwise a radio-style choice among non-overlay
            vector/marker layers.
        popup: ``None`` for no tooltip/popup; a list of column names to
            show in both; or a dict with ``"fields"`` and optional
            ``"tooltip"``/``"popup"`` bool toggles.
        m: Map to add the layer to. A new map is created if omitted.
        style: Style overrides - currently ``stroke_color`` and ``weight``
            (marker border colour/width).
        legend: Whether to show legend(s) for this layer - a colour
            legend for ``column`` and/or a marker-values legend for
            ``marker_column`` (see ``histogram`` below for when the latter
            is built).
        legend_unit: Unit string appended to numeric legend labels.
        active: Whether the layer starts visible.
        histogram: If both ``column`` and ``marker_column`` are given,
            expose ``marker_column`` to the map's statistics panel (the
            bottom-left 📊 button) so its per-category breakdown (with
            icons, class labels, and count/%, linear/log toggle buttons)
            can be generated for this layer on demand, and add a
            marker-values legend (when ``marker_column != column``). Set
            to ``False`` to have both ignore ``marker_column``.

    Returns:
        The map, for chaining.

    Raises:
        ValueError: If neither ``layer_name`` nor ``column`` is given, or
            if ``categorical`` and ``count`` are both ``True``.
        TypeError: If ``count=True`` and ``column`` isn't a valid counts
            column.
    """
    if categorical and count:
        raise ValueError("marker_layer: 'categorical' and 'count' are mutually exclusive.")
    if layer_name is None and column is None:
        raise ValueError("Either layer_name or column must be provided for marker_layer().")
    display_name = layer_name or column

    if count and column is not None and column in gdf.columns:
        validate_count_column(gdf[column], column)

    gdf = gdf.copy()
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    elif gdf.crs is None:
        warnings.warn(f"marker_layer('{display_name}'): no CRS, assuming EPSG:4326.", UserWarning, stacklevel=2)

    geom_type = gdf.geom_type.iloc[0] if len(gdf) else "Point"
    if geom_type not in ("Point", "MultiPoint"):
        warnings.warn(f"marker_layer('{display_name}'): using centroids.", UserWarning, stacklevel=2)
        gdf["geometry"] = gdf.geometry.centroid

    if m is None:
        m = _default_map()

    lid = _unique_id()
    st  = _state(m)

    if not overlay and active:
        for entry in st["vector_layers"]:
            if not entry["overlay"]:
                entry["active"] = False

    colors = (
        compute_feature_colors(
            gdf[column] if column and column in gdf.columns else pd.Series([color] * len(gdf), index=gdf.index),
            cmap=cmap if column else None, vmin=vmin, vmax=vmax, categorical=categorical, count=count,
        ) if column else {idx: color for idx in gdf.index}
    )

    style_dict    = style or {}
    border_color  = style_dict.get("stroke_color", "#333")
    border_weight = style_dict.get("weight", 1)

    if popup is not None:
        fields = popup if isinstance(popup, list) else popup.get("fields", [])
    else:
        fields = [column] if column else []

    is_num = None
    if column is not None and column in gdf.columns:
        is_num = bool(pd.api.types.is_numeric_dtype(gdf[column]) and not categorical)

    has_marker_col = bool(marker_column and marker_column in gdf.columns)
    categories = sorted(gdf[marker_column].dropna().astype(str).unique().tolist()) if has_marker_col else []
    marker_map = _resolve_marker_map(marker, categories)
    fixed_marker = marker if isinstance(marker, str) and marker else None
    # Full category -> symbol map (same resolution the per-row loop below uses),
    # reused to build the marker-values legend.
    full_marker_map = {c: fixed_marker or (marker_map or {}).get(c, c) for c in categories}

    # Always show=True; JS init will call removeLayer for inactive layers
    group = folium.FeatureGroup(name=display_name, control=False, show=True)
    group.options["name"] = display_name

    # Marker/CircleMarker instances don't carry GeoJSON-style properties like
    # a GeoJson layer does, so the stats panel can't introspect them client-side.
    # We collect the same per-row info here (color + column/marker_column values)
    # and hand it to the JS stats panel via the layer entry below.
    rows = []

    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        lat, lon = geom.y, geom.x
        fc = colors.get(idx, color)

        txt = ""
        if has_marker_col:
            cat = str(row[marker_column])
            txt = fixed_marker or (marker_map or {}).get(cat, cat)
        elif fixed_marker:
            txt = fixed_marker

        col_val = None
        if column is not None and not pd.isna(row.get(column)):
            raw = row[column]
            col_val = float(raw) if is_num else str(raw)
        rows.append({
            "v": col_val,
            "mk": (str(row[marker_column]) if has_marker_col and not pd.isna(row[marker_column]) else None),
            "icon": (txt or None) if has_marker_col else None,
            "color": fc,
        })

        tip_html = "<br>".join(f"<b>{f}</b>: {row.get(f, '')}" for f in fields) if fields else None

        if txt:
            # Without a colormap column there's no data-driven color to show, so
            # emoji/text markers get a plain background instead of a meaningless
            # solid-color disc; with a column, the disc still carries the colormap.
            if column:
                bg_style = f'background:{fc};border:{border_weight}px solid {border_color};box-shadow:0 1px 3px rgba(0,0,0,.4);'
                text_color = "#fff"
            else:
                bg_style = "background:transparent;border:none;"
                text_color = "#222"
            mk = folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(
                    html=(f'<div style="{bg_style}border-radius:50%;width:28px;height:28px;'
                          f'display:flex;align-items:center;justify-content:center;'
                          f'font-size:16px;font-weight:bold;color:{text_color};">{txt}</div>'),
                    icon_size=(28, 28), icon_anchor=(14, 14),
                ),
                tooltip=folium.Tooltip(tip_html, sticky=True) if tip_html else None,
                popup=folium.Popup(tip_html) if tip_html else None,
            )
        else:
            # A classic Google Maps-style teardrop pin reads better on a map than a
            # plain filled circle, and still carries the colormap fill when present.
            pin_svg = (
                f'<svg width="26" height="36" viewBox="0 0 26 36" xmlns="http://www.w3.org/2000/svg" '
                f'style="filter:drop-shadow(0 1px 2px rgba(0,0,0,.45));">'
                f'<path d="M13 0C5.8 0 0 5.8 0 13c0 9.4 11.2 21.6 12.6 23.1a.6.6 0 0 0 .8 0C14.8 34.6 26 22.4 26 13 26 5.8 20.2 0 13 0z" '
                f'fill="{fc}" stroke="{border_color}" stroke-width="{border_weight}"/>'
                f'<circle cx="13" cy="13" r="5" fill="#fff"/>'
                f'</svg>'
            )
            mk = folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(html=pin_svg, icon_size=(26, 36), icon_anchor=(13, 36)),
                tooltip=folium.Tooltip(tip_html, sticky=True) if tip_html else None,
                popup=folium.Popup(tip_html) if tip_html else None,
            )
        mk.add_to(group)

    group.add_to(m)

    entry = {
        "name": display_name, "overlay": overlay, "id": lid, "active": active,
        "js_var": group.get_name(), "column": column, "is_num": is_num,
        "marker_column": marker_column if (has_marker_col and histogram) else None,
        "rows": rows,
    }
    st["vector_layers"] = [l for l in st["vector_layers"] if l["name"] != display_name]
    st["vector_layers"].append(entry)

    if legend:
        specs = []
        if column and column in gdf.columns:
            leg = _build_legend_spec(
                layer_name=display_name, column=column, series=gdf[column],
                cmap=cmap, vmin=vmin, vmax=vmax, categorical=categorical, count=count, unit=legend_unit,
            )
            if leg:
                specs.append(leg)
        # A separate marker-values legend only makes sense when marker_column
        # isn't the same column already explained by the colour legend above.
        if has_marker_col and marker_column != column:
            marker_leg = _build_marker_legend_spec(
                layer_name=display_name, categories=categories, marker_map=full_marker_map,
            )
            if marker_leg:
                specs.append(marker_leg)
        if specs:
            st["legends"][display_name] = specs
        else:
            st["legends"].pop(display_name, None)

    b = gdf_bounds_wgs84(gdf)
    _accumulate_bounds(m, b)
    _rebuild_control_panel(m)
    return m