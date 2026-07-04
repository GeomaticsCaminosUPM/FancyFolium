import pytest

import FancyFolium as ff
from FancyFolium.map_core import _state


def test_vector_layer_requires_name_or_column(polygon_gdf):
    with pytest.raises(ValueError):
        ff.vector_layer(polygon_gdf)


def test_vector_layer_categorical_and_count_are_mutually_exclusive(polygon_gdf):
    with pytest.raises(ValueError):
        ff.vector_layer(polygon_gdf, column="n_storeys", categorical=True, count=True)


def test_vector_layer_count_requires_integer_dtype(polygon_gdf):
    with pytest.raises(TypeError):
        ff.vector_layer(polygon_gdf, column="height", count=True)  # height is float


def test_vector_layer_count_column_builds_numeric_legend_with_zero_vmin(polygon_gdf):
    m = ff.vector_layer(polygon_gdf, layer_name="storeys", column="n_storeys", count=True)
    st = _state(m)
    leg = st["legends"]["storeys"][0]
    assert leg["type"] == "numeric"
    assert leg["vmin"] == 0.0
    assert leg["vmax"] == float(polygon_gdf["n_storeys"].max())


def test_vector_layer_numeric_column_builds_numeric_legend(polygon_gdf):
    m = ff.vector_layer(polygon_gdf, layer_name="footprints", column="height", cmap="Reds")
    st = _state(m)
    assert len(st["vector_layers"]) == 1
    entry = st["vector_layers"][0]
    assert entry["name"] == "footprints"
    assert entry["is_num"] is True
    leg = st["legends"]["footprints"][0]
    assert leg["type"] == "numeric"
    assert "colors" in leg


def test_vector_layer_categorical_column_builds_categorical_legend(polygon_gdf):
    m = ff.vector_layer(
        polygon_gdf, layer_name="structure", column="structural_system", categorical=True
    )
    st = _state(m)
    entry = st["vector_layers"][0]
    assert entry["is_num"] is False
    leg = st["legends"]["structure"][0]
    assert leg["type"] == "categorical"
    labels = {e["label"] for e in leg["entries"]}
    assert labels == {"masonry", "concrete", "steel"}


def test_vector_layer_no_column_no_legend(polygon_gdf):
    m = ff.vector_layer(polygon_gdf, layer_name="plain", color="#123456")
    st = _state(m)
    assert "plain" not in st["legends"]
    assert st["vector_layers"][0]["is_num"] is None


def test_vector_layer_legend_false_removes_legend(polygon_gdf):
    m = ff.vector_layer(polygon_gdf, layer_name="footprints", column="height", legend=False)
    st = _state(m)
    assert "footprints" not in st["legends"]


def test_vector_layer_unknown_column_raises(polygon_gdf):
    with pytest.raises(ValueError):
        ff.vector_layer(polygon_gdf, layer_name="x", column="does_not_exist")


def test_vector_layer_non_overlay_deactivates_previous(polygon_gdf):
    m = ff.vector_layer(polygon_gdf, layer_name="a", column="height", m=ff.create_map())
    m = ff.vector_layer(polygon_gdf, layer_name="b", column="height", m=m)
    st = _state(m)
    active = {e["name"]: e["active"] for e in st["vector_layers"]}
    assert active["a"] is False
    assert active["b"] is True


def test_vector_layer_popup_list_and_dict(polygon_gdf):
    m = ff.vector_layer(polygon_gdf, layer_name="a", column="height", popup=["height"])
    m = ff.vector_layer(
        polygon_gdf, layer_name="b", column="height",
        popup={"fields": ["height", "roof"], "tooltip": True, "popup": False}, m=m,
    )
    assert isinstance(m, __import__("folium").Map)


def test_vector_layer_reprojects_non_4326(polygon_gdf):
    reprojected = polygon_gdf.to_crs(3857)
    m = ff.vector_layer(reprojected, layer_name="reproj", column="height")
    st = _state(m)
    assert len(st["vector_layers"]) == 1


def test_vector_layer_no_crs_warns(polygon_gdf):
    no_crs = polygon_gdf.copy()
    no_crs.crs = None
    with pytest.warns(UserWarning):
        ff.vector_layer(no_crs, layer_name="no-crs", column="height")
