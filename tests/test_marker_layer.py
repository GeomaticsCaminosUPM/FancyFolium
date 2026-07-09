import pytest

import FancyFolium as ff
from FancyFolium.map_core import _state


def test_marker_layer_requires_name_or_column(point_gdf):
    with pytest.raises(ValueError):
        ff.marker_layer(point_gdf)


def test_marker_layer_plain_no_column(point_gdf):
    m = ff.marker_layer(point_gdf, layer_name="plain", color="#2b6cb0")
    st = _state(m)
    assert st["vector_layers"][0]["name"] == "plain"
    assert "plain" not in st["legends"]


def test_marker_layer_categorical_and_count_are_mutually_exclusive(point_gdf):
    with pytest.raises(ValueError):
        ff.marker_layer(point_gdf, column="n_storeys", categorical=True, count=True)


def test_marker_layer_count_requires_integer_dtype(point_gdf):
    with pytest.raises(TypeError):
        ff.marker_layer(point_gdf, column="height", count=True)  # height is float


def test_marker_layer_count_column_builds_numeric_legend_with_zero_vmin(point_gdf):
    m = ff.marker_layer(point_gdf, layer_name="storeys", column="n_storeys", count=True)
    st = _state(m)
    leg = st["legends"]["storeys"][0]
    assert leg["type"] == "numeric"
    assert leg["vmin"] == 0.0
    assert leg["vmax"] == float(point_gdf["n_storeys"].max())


def test_marker_layer_plain_uses_pin_marker_not_circle(point_gdf):
    """No column, no marker/marker_column -> a Google-Maps-style teardrop pin,
    not a plain filled circle."""
    m = ff.marker_layer(point_gdf, layer_name="plain", color="#2b6cb0")
    html = m.get_root().render()
    assert "svg" in html  # JSON-escaped as <svg ... in the rendered <script>
    assert "L.circleMarker(" not in html


def test_marker_layer_emoji_without_column_has_transparent_background(point_gdf):
    """Without a colormap `column`, an emoji/text marker shouldn't get a
    meaningless solid-color disc behind it."""
    m = ff.marker_layer(point_gdf, layer_name="pts", marker_column="roof")
    html = m.get_root().render()
    assert "background:transparent;border:none;" in html


def test_marker_layer_emoji_with_column_keeps_colored_background(point_gdf):
    m = ff.marker_layer(point_gdf, layer_name="pts", column="height", marker_column="roof")
    html = m.get_root().render()
    assert "background:transparent;border:none;" not in html


def test_marker_layer_column_only_builds_numeric_legend(point_gdf):
    m = ff.marker_layer(point_gdf, layer_name="pts", column="height", cmap="viridis")
    st = _state(m)
    leg = st["legends"]["pts"][0]
    assert leg["type"] == "numeric"


def test_marker_layer_fixed_marker_no_histogram(point_gdf):
    """column + marker (fixed) but no marker_column -> ordinary numeric legend."""
    m = ff.marker_layer(point_gdf, layer_name="pts", column="height", marker="H")
    st = _state(m)
    leg = st["legends"]["pts"][0]
    assert leg["type"] == "numeric"


def test_marker_layer_polygon_input_uses_centroid_with_warning(polygon_gdf):
    with pytest.warns(UserWarning, match="centroid"):
        m = ff.marker_layer(polygon_gdf, layer_name="centroids", column="height")
    st = _state(m)
    assert st["vector_layers"][0]["name"] == "centroids"


def test_marker_layer_never_builds_a_histogram_legend(point_gdf):
    """Histograms are a stats-panel (bottom-left button) feature, not a map
    legend - marker_layer should only ever produce numeric/categorical/markers legends."""
    m = ff.marker_layer(
        point_gdf, layer_name="pts", column="height", cmap="viridis", marker_column="roof",
    )
    st = _state(m)
    types = {leg["type"] for leg in st["legends"]["pts"]}
    assert "histogram" not in types


def test_marker_layer_separate_legend_for_marker_and_color_when_different_columns(point_gdf):
    """column (colour) and marker_column are different -> two legends: one for
    the colormap, one for the marker/icon values."""
    m = ff.marker_layer(
        point_gdf, layer_name="pts", column="height", cmap="viridis", marker_column="roof",
        marker={"flat": "🏠"},
    )
    st = _state(m)
    legs = st["legends"]["pts"]
    assert len(legs) == 2
    color_leg = next(l for l in legs if l["type"] == "numeric")
    marker_leg = next(l for l in legs if l["type"] == "markers")
    assert color_leg["name"].endswith("height")
    labels_to_icons = {e["label"]: e["icon"] for e in marker_leg["entries"]}
    assert labels_to_icons["flat"] == "🏠"
    assert labels_to_icons["gable"] == "gable"


def test_marker_layer_no_separate_marker_legend_when_same_column(point_gdf):
    """marker_column == column -> only one legend (no redundant duplicate)."""
    m = ff.marker_layer(
        point_gdf, layer_name="pts", column="roof", categorical=True, marker_column="roof",
    )
    st = _state(m)
    legs = st["legends"]["pts"]
    assert len(legs) == 1
    assert legs[0]["type"] == "categorical"


def test_marker_layer_marker_legend_without_color_column(point_gdf):
    """marker_column given but no column -> just the marker-values legend."""
    m = ff.marker_layer(point_gdf, layer_name="pts", marker_column="roof")
    st = _state(m)
    legs = st["legends"]["pts"]
    assert len(legs) == 1
    assert legs[0]["type"] == "markers"


def test_marker_layer_exposes_marker_column_and_rows_for_stats_panel(point_gdf):
    """The JS stats panel can't read GeoJSON properties off Marker/CircleMarker
    instances, so marker_layer hands it precomputed per-row data instead."""
    m = ff.marker_layer(
        point_gdf, layer_name="pts", column="height", cmap="viridis", marker_column="roof",
    )
    st = _state(m)
    entry = next(e for e in st["vector_layers"] if e["name"] == "pts")
    assert entry["marker_column"] == "roof"
    assert len(entry["rows"]) == len(point_gdf)
    row = entry["rows"][0]
    assert set(row) == {"v", "mk", "icon", "color"}
    assert all(r["mk"] in ("flat", "gable") for r in entry["rows"])
    assert all(isinstance(r["v"], float) for r in entry["rows"])  # height is numeric


def test_marker_layer_rows_icon_uses_fixed_marker(point_gdf):
    m = ff.marker_layer(
        point_gdf, layer_name="pts", column="height", marker_column="roof", marker="H",
    )
    st = _state(m)
    entry = next(e for e in st["vector_layers"] if e["name"] == "pts")
    assert all(r["icon"] == "H" for r in entry["rows"])


def test_marker_layer_rows_icon_defaults_to_raw_category(point_gdf):
    """Without marker=, each row's icon is the marker_column's own value -
    e.g. if the caller pre-populated it with emojis, those are shown as-is."""
    m = ff.marker_layer(point_gdf, layer_name="pts", column="height", marker_column="roof")
    st = _state(m)
    entry = next(e for e in st["vector_layers"] if e["name"] == "pts")
    icons = {r["icon"] for r in entry["rows"]}
    assert icons == {"flat", "gable"}


def test_marker_layer_marker_column_with_emoji_values_passes_through(point_gdf):
    """A marker_column already containing emojis (built by the caller) is used
    as-is, not overwritten by any automatic assignment."""
    gdf = point_gdf.copy()
    gdf["roof_symbol"] = gdf["roof"].map({"flat": "⬜", "gable": "⬛"})
    m = ff.marker_layer(gdf, layer_name="pts", column="height", marker_column="roof_symbol")
    st = _state(m)
    entry = next(e for e in st["vector_layers"] if e["name"] == "pts")
    icons = {r["icon"] for r in entry["rows"]}
    assert icons == {"⬜", "⬛"}


def test_marker_layer_marker_dict_overrides_per_category(point_gdf):
    m = ff.marker_layer(
        point_gdf, layer_name="pts", column="height", marker_column="roof",
        marker={"flat": "🏠"},
    )
    st = _state(m)
    entry = next(e for e in st["vector_layers"] if e["name"] == "pts")
    icon_by_mk = {r["mk"]: r["icon"] for r in entry["rows"]}
    assert icon_by_mk["flat"] == "🏠"
    assert icon_by_mk["gable"] == "gable"  # uncovered category falls back to its raw value


def test_marker_layer_categorical_column_rows_carry_string_values(point_gdf):
    m = ff.marker_layer(
        point_gdf, layer_name="pts", column="structural_system", categorical=True,
        marker_column="roof",
    )
    st = _state(m)
    entry = next(e for e in st["vector_layers"] if e["name"] == "pts")
    assert entry["is_num"] is False
    values = {r["v"] for r in entry["rows"]}
    assert values == {"masonry", "concrete", "steel"}


def test_marker_layer_histogram_false_hides_marker_column_from_stats_panel(point_gdf):
    m = ff.marker_layer(
        point_gdf, layer_name="pts", column="height", marker_column="roof", histogram=False,
    )
    st = _state(m)
    entry = next(e for e in st["vector_layers"] if e["name"] == "pts")
    assert entry["marker_column"] is None
    leg = st["legends"]["pts"][0]
    assert leg["type"] == "numeric"


def test_marker_layer_legend_false_skips_legend_but_keeps_rows(point_gdf):
    m = ff.marker_layer(
        point_gdf, layer_name="pts", column="height", marker_column="roof", legend=False,
    )
    st = _state(m)
    assert "pts" not in st["legends"]
    entry = next(e for e in st["vector_layers"] if e["name"] == "pts")
    assert entry["marker_column"] == "roof"
    assert len(entry["rows"]) == len(point_gdf)


def test_marker_layer_non_overlay_deactivates_previous(point_gdf):
    m = ff.marker_layer(point_gdf, layer_name="a", column="height", m=ff.create_map())
    m = ff.marker_layer(point_gdf, layer_name="b", column="height", m=m)
    st = _state(m)
    active = {e["name"]: e["active"] for e in st["vector_layers"]}
    assert active["a"] is False
    assert active["b"] is True


def test_marker_layer_real_data_integration(real_gdf_points):
    m = ff.marker_layer(
        real_gdf_points, layer_name="buildings", column="height", cmap="viridis",
        marker_column="roof",
    )
    st = _state(m)
    leg = st["legends"]["buildings"][0]
    assert leg["type"] == "numeric"
    entry = next(e for e in st["vector_layers"] if e["name"] == "buildings")
    assert entry["marker_column"] == "roof"
    assert len(entry["rows"]) > 0
