import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from FancyFolium.utils.geo import (
    bounds_center,
    bounds_to_folium,
    expand_bounds,
    folium_bounds_to_tuple,
    gdf_bounds_wgs84,
)


def test_bounds_center():
    lat, lon = bounds_center((0, 0, 10, 20))
    assert (lat, lon) == (10, 5)


def test_gdf_bounds_wgs84_no_reprojection_needed():
    gdf = gpd.GeoDataFrame(
        geometry=[Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])], crs="EPSG:4326"
    )
    bounds = gdf_bounds_wgs84(gdf)
    assert bounds == pytest.approx((0, 0, 1, 1))


def test_gdf_bounds_wgs84_reprojects():
    gdf = gpd.GeoDataFrame(
        geometry=[Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])], crs="EPSG:4326"
    ).to_crs(3857)
    bounds = gdf_bounds_wgs84(gdf)
    assert bounds == pytest.approx((0, 0, 1, 1), abs=1e-6)


def test_bounds_to_folium_and_back_roundtrip():
    b4326 = (-10.0, -20.0, 10.0, 20.0)
    fb = bounds_to_folium(b4326)
    assert fb == [[-20.0, -10.0], [20.0, 10.0]]
    assert folium_bounds_to_tuple(fb) == b4326


def test_expand_bounds_grows_symmetrically():
    b = (0.0, 0.0, 10.0, 10.0)
    expanded = expand_bounds(b, factor=0.1)
    assert expanded[0] < b[0]
    assert expanded[1] < b[1]
    assert expanded[2] > b[2]
    assert expanded[3] > b[3]
