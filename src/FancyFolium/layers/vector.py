"""
layers/vector.py
================
``vector_layer()`` - add a polygon/line/point GeoDataFrame as a styled
GeoJSON overlay.
"""

from __future__ import annotations
import warnings
from typing import Callable, Dict, List, Optional, Tuple, Union
import folium
import geopandas as gpd
import pandas as pd

from ..map_core import _state, _unique_id, _rebuild_control_panel, _accumulate_bounds, _default_map, _build_legend_spec
from ..utils.color import CmapArg, compute_feature_colors, validate_count_column
from ..utils.geo import gdf_bounds_wgs84

PopupArg = Union[None, List[str], Dict]
StyleArg = Union[None, str, Dict]


def _build_popup_tooltip(
    popup: PopupArg,
    layer_id: str,
    gdf: gpd.GeoDataFrame,
) -> Tuple[Optional[folium.GeoJsonTooltip], Optional[folium.GeoJsonPopup]]:
    """Build the tooltip/popup pair for a GeoJson layer from a ``popup`` argument.

    Args:
        popup: ``None`` for no tooltip/popup; a list of column names to
            show in both; or a dict with ``"fields"`` (list of column
            names) and optional ``"tooltip"``/``"popup"`` bool toggles to
            show each independently.
        layer_id: Unique id of the layer (currently unused, reserved for
            future per-layer popup customisation).
        gdf: The layer's GeoDataFrame, used to filter ``popup`` fields down
            to columns that actually exist.

    Returns:
        A ``(tooltip, popup)`` tuple, each ``None`` if not requested.

    Raises:
        TypeError: If ``popup`` is not ``None``, a list, or a dict.
    """
    if popup is None:
        return None, None
    if isinstance(popup, list):
        fields = [f for f in popup if f in gdf.columns]
        tooltip = folium.GeoJsonTooltip(fields=fields, labels=True, sticky=True) if fields else None
        popup_obj = folium.GeoJsonPopup(fields=fields, labels=True) if fields else None
        return tooltip, popup_obj
    if not isinstance(popup, dict):
        raise TypeError(f"popup must be None, list, or dict; got {type(popup).__name__!r}.")
    fields   = popup.get("fields", [])
    show_tip = popup.get("tooltip", True)
    show_pop = popup.get("popup", True)
    tooltip_obj = folium.GeoJsonTooltip(fields=fields, labels=True, sticky=True) if fields and show_tip else None
    popup_obj   = folium.GeoJsonPopup(fields=fields, labels=True) if fields and show_pop else None
    return tooltip_obj, popup_obj


def _build_style_function(
    gdf: gpd.GeoDataFrame,
    column: Optional[str],
    color: str,
    cmap: CmapArg,
    vmin: Optional[float],
    vmax: Optional[float],
    categorical: bool,
    count: bool,
    opacity: float,
    style: StyleArg,
    color_by_column: bool = True,
) -> Tuple[Callable[[dict], dict], gpd.GeoDataFrame]:
    """Compute per-feature colours and build the GeoJson ``style_function``.

    Args:
        gdf: The layer's GeoDataFrame.
        column: Column to colour features by, or ``None`` for a uniform
            ``color``.
        color: Uniform fill/stroke colour used when ``column`` is ``None``
            or ``color_by_column`` is ``False``.
        cmap: Colour map argument (see
            :func:`FancyFolium.utils.color.resolve_cmap`).
        vmin: Lower colour-scale bound for numeric columns.
        vmax: Upper colour-scale bound for numeric columns.
        categorical: Treat ``column`` as categorical.
        count: Treat ``column`` as a "counts" column (see
            :func:`FancyFolium.utils.color.validate_count_column`).
        opacity: Default fill opacity, overridden by ``style["fill_opacity"]``.
        style: Style overrides - a dict of ``stroke_color``, ``stroke_width``/
            ``weight``, ``stroke_opacity``, ``dashArray``/``dash_array``,
            ``fill``/``fill_opacity``; or a plain string (reserved, stored
            as ``{"css": style}`` but currently unused by the style
            function).
        color_by_column: Whether ``column`` (when given) drives per-feature
            colour via ``cmap``. If ``False``, every feature uses the
            uniform ``color`` instead, but ``column`` is still attached to
            the GeoJSON output (and tracked by the caller for the stats
            panel) - lets a layer keep a fixed colour while still exposing
            a real column for its histogram.

    Returns:
        A tuple of the GeoJson ``style_function`` callable and a copy of
        ``gdf`` with a ``"__color"`` column added (read by the style
        function and by the stats panel).

    Raises:
        ValueError: If ``column`` is given but not a column of *gdf*.
    """
    style_dict = style if isinstance(style, dict) else ({"css": style} if isinstance(style, str) else {}) if style else {}
    if column is not None and column not in gdf.columns:
        raise ValueError(f"Column '{column}' not found. Available: {list(gdf.columns)}")
    if column is not None and color_by_column:
        colors = compute_feature_colors(
            gdf[column], cmap=cmap, vmin=vmin, vmax=vmax, categorical=categorical, count=count,
        )
    else:
        colors = {idx: color for idx in gdf.index}
    gdf = gdf.copy()
    gdf["__color"] = [colors.get(idx, color) for idx in gdf.index]

    stroke_color   = style_dict.get("stroke_color", None)
    stroke_width   = style_dict.get("stroke_width", style_dict.get("weight", 0.8))
    stroke_opacity = style_dict.get("stroke_opacity", 0.8)
    dash_array     = style_dict.get("dashArray", style_dict.get("dash_array", None))
    fill_val       = style_dict.get("fill", None)
    fill_opacity   = float(fill_val) if fill_val is not None else style_dict.get("fill_opacity", opacity)

    def style_fn(feature: dict) -> dict:
        """Per-feature Leaflet style dict, reading colour from ``__color``.

        Args:
            feature: A single GeoJSON feature dict, as passed by Folium/Leaflet,
                whose ``properties.__color`` holds this row's fill colour.

        Returns:
            A Leaflet path-style dict (``fillColor``, ``fillOpacity``,
            ``color``, ``weight``, ``opacity``, and optionally ``dashArray``).
        """
        fc = feature["properties"].get("__color", color)
        s = {
            "fillColor":   fc,
            "fillOpacity": fill_opacity,
            "color":       stroke_color if stroke_color else fc,
            "weight":      stroke_width,
            "opacity":     stroke_opacity,
        }
        if dash_array:
            s["dashArray"] = str(dash_array)
        return s

    return style_fn, gdf


def vector_layer(
    gdf: gpd.GeoDataFrame,
    opacity: float = 1.0,
    layer_name: Optional[str] = None,
    column: Optional[str] = None,
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
    color_by_column: bool = True,
) -> folium.Map:
    """Add a polygon/line/point GeoDataFrame as a styled vector layer.

    Args:
        gdf: Source GeoDataFrame. Reprojected to EPSG:4326 automatically if
            it carries a different CRS (a ``UserWarning`` is raised if it
            has no CRS at all, assuming EPSG:4326).
        opacity: Default fill opacity in ``[0, 1]``, overridden by
            ``style["fill_opacity"]`` if given.
        layer_name: Display name shown in the control panel and legend.
            Defaults to ``column``. Required if ``column`` is ``None``.
        column: Column to colour features by (numeric, categorical, or
            count - see ``categorical``/``count``).
        color: Uniform fill/stroke colour used when ``column`` is ``None``.
        cmap: Colour map argument - ``None`` (default palette), a named
            palette string (``"viridis"``, ``"Reds"``, ...), a
            ``t -> hex`` callable, a ``{value: hex}`` dict, or an ordered
            list of hex colours (dict/list imply categorical treatment).
        vmin: Lower colour-scale bound for numeric/count columns. Defaults
            to the 10th percentile (or 0 for count columns).
        vmax: Upper colour-scale bound for numeric/count columns. Defaults
            to the 90th percentile (or the column max for count columns).
        categorical: Treat ``column`` as categorical (string labels)
            rather than a continuous numeric scale. Mutually exclusive
            with ``count``.
        count: Treat ``column`` as a "counts" column (e.g. number of
            storeys, population): validated to hold whole-number values
            only (``TypeError`` otherwise), with the colour scale
            defaulting to ``vmin=0``/``vmax=column.max()`` instead of the
            numeric p10/p90 default. Mutually exclusive with
            ``categorical``.
        overlay: If ``True``, shown as an independently toggleable
            checkbox; otherwise a radio-style choice among non-overlay
            vector layers.
        popup: ``None`` for no tooltip/popup; a list of column names to
            show in both; or a dict with ``"fields"`` and optional
            ``"tooltip"``/``"popup"`` bool toggles.
        m: Map to add the layer to. A new map is created if omitted.
        style: Style overrides - see :func:`_build_style_function` for the
            supported keys (``stroke_color``, ``weight``, ``dashArray``,
            ``fill_opacity``, etc.).
        legend: Whether to show a legend for this layer's ``column``.
        legend_unit: Unit string appended to numeric legend labels.
        active: Whether the layer starts visible.
        color_by_column: Whether ``column`` (when given) drives per-feature
            colour via ``cmap``. Set to ``False`` to keep every feature at
            the uniform ``color`` while still attaching ``column``'s real
            values to the layer, so the stats panel can histogram it (no
            legend is auto-built in this case, since the map isn't
            actually coloured by the column).

    Returns:
        The map, for chaining.

    Raises:
        ValueError: If neither ``layer_name`` nor ``column`` is given, if
            ``categorical`` and ``count`` are both ``True``, or if
            ``column`` is not a column of *gdf*.
        TypeError: If ``count=True`` and ``column`` isn't a valid counts
            column, or ``popup`` has an unsupported type.
    """
    if categorical and count:
        raise ValueError("vector_layer: 'categorical' and 'count' are mutually exclusive.")
    if layer_name is None and column is None:
        raise ValueError("Either layer_name or column must be provided.")
    display_name = layer_name or column

    if count and column is not None and column in gdf.columns:
        validate_count_column(gdf[column], column)

    gdf = gdf.copy()
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    elif gdf.crs is None:
        warnings.warn(f"vector_layer('{display_name}'): no CRS, assuming EPSG:4326.", UserWarning, stacklevel=2)

    if m is None:
        m = _default_map()

    lid = _unique_id()
    st  = _state(m)

    if not overlay and active:
        for entry in st["vector_layers"]:
            if not entry["overlay"]:
                entry["active"] = False

    style_dict = style if isinstance(style, dict) else {}
    style_fn, gdf = _build_style_function(
        gdf, column, color, cmap, vmin, vmax, categorical, count, opacity, style,
        color_by_column=color_by_column,
    )

    popup_result = _build_popup_tooltip(popup, lid, gdf)
    if len(popup_result) == 3:
        tooltip_obj, popup_obj, gdf = popup_result
    else:
        tooltip_obj, popup_obj = popup_result

    geojson = folium.GeoJson(
        gdf.__geo_interface__,
        name=display_name,
        style_function=style_fn,
        tooltip=tooltip_obj,
        popup=popup_obj,
        zoom_on_click=False,
        control=False,
        show=True,
    )

    group = folium.FeatureGroup(name=display_name, control=False, show=True)
    group.options["name"] = display_name
    geojson.add_to(group)
    group.add_to(m)

    # Determine if column is numeric (for stats panel)
    is_num = None
    if column is not None and column in gdf.columns:
        is_num = bool(pd.api.types.is_numeric_dtype(gdf[column]) and not categorical)

    entry = {
        "name":    display_name,
        "overlay": overlay,
        "id":      lid,
        "active":  active,
        "js_var":  group.get_name(),
        "column":  column,
        "is_num":  is_num,
    }
    st["vector_layers"] = [l for l in st["vector_layers"] if l["name"] != display_name]
    st["vector_layers"].append(entry)

    if legend and column is not None and color_by_column:
        leg = _build_legend_spec(
            layer_name=display_name, column=column, series=gdf[column],
            cmap=cmap, vmin=vmin, vmax=vmax, categorical=categorical, count=count, unit=legend_unit,
        )
        if leg:
            st["legends"][display_name] = [leg]
    else:
        st["legends"].pop(display_name, None)

    b = gdf_bounds_wgs84(gdf)
    _accumulate_bounds(m, b)
    _rebuild_control_panel(m)
    return m