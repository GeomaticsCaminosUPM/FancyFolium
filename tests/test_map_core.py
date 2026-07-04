import FancyFolium as ff
from FancyFolium.map_core import _state
from shapely.geometry import Point, Polygon
import geopandas as gpd


def test_view_bounds_accumulate_across_layers():
    """Adding a second, disjoint layer should widen the view instead of
    re-centring on only the newest layer's extent."""
    far_away = gpd.GeoDataFrame(
        {"height": [1.0]},
        geometry=[Polygon([(50, 50), (50, 51), (51, 51), (51, 50)])],
        crs="EPSG:4326",
    )
    near_origin = gpd.GeoDataFrame(
        {"height": [1.0]},
        geometry=[Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])],
        crs="EPSG:4326",
    )

    m = ff.vector_layer(near_origin, layer_name="a", column="height")
    m = ff.vector_layer(far_away, layer_name="b", column="height", overlay=True, m=m)

    st = _state(m)
    minx, miny, maxx, maxy = st["_bounds"]
    assert minx <= 0 and miny <= 0
    assert maxx >= 51 and maxy >= 51


def test_vector_tab_is_default_active_when_present():
    gdf = gpd.GeoDataFrame(
        {"height": [1.0]}, geometry=[Point(0, 0)], crs="EPSG:4326"
    )
    m = ff.create_map()
    m = ff.background_layer("google hybrid", m=m)
    m = ff.marker_layer(gdf, layer_name="pts", column="height", m=m)

    panel_html = next(
        child.render() for child in m.get_root().html._children.values()
        if getattr(child, "_name", "") == "Element" and "maplib-panel" in child.render()
    )
    assert 'class="maplib-tab active" onclick="maplibTab(this,\'vector\')">Vector</button>' in panel_html
    assert 'id="maplib-panel-vector" class="maplib-panel-body active"' in panel_html
    assert 'class="maplib-tab active" onclick="maplibTab(this,\'bg\')"' not in panel_html
