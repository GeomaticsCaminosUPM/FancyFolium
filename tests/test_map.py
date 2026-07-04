import folium
import pytest

import FancyFolium as ff
from FancyFolium.map_core import _state


def test_create_map_default_location_and_zoom():
    m = ff.create_map()
    assert isinstance(m, folium.Map)
    assert m.location == [0, 0]
    st = _state(m)
    assert st["background_layers"] == []
    assert st["vector_layers"] == []


def test_create_map_custom_location_and_zoom():
    m = ff.create_map(location=[10, 20], zoom=8)
    assert m.location == [10, 20]
    assert m.options.get("zoom") == 8


def test_export_writes_html(tmp_path):
    m = ff.create_map()
    out = tmp_path / "sub" / "map.html"
    ff.export(m, str(out))
    assert out.exists()
    assert "<html" in out.read_text(encoding="utf-8").lower()


def test_merge_maps_requires_matching_lengths():
    m1, m2 = ff.create_map(), ff.create_map()
    with pytest.raises(ValueError):
        ff.merge_maps([m1, m2], ["only one name"])


def test_merge_maps_requires_at_least_two():
    m1 = ff.create_map()
    with pytest.raises(ValueError):
        ff.merge_maps([m1], ["one"])


def test_merge_maps_builds_switcher(polygon_gdf):
    m1 = ff.vector_layer(polygon_gdf, layer_name="a", column="height", m=ff.create_map())
    m2 = ff.vector_layer(polygon_gdf, layer_name="b", column="height", m=ff.create_map())
    merged = ff.merge_maps([m1, m2], ["Map A", "Map B"])
    assert isinstance(merged, folium.Map)
    assert "maplib_switcher" in merged.get_root().html._children
