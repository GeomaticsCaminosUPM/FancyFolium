"""Shared pytest fixtures for the FancyFolium test suite."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon

DATA_DIR = Path(__file__).parent.parent / "examples" / "data"


@pytest.fixture
def polygon_gdf() -> gpd.GeoDataFrame:
    """A small synthetic polygon GeoDataFrame with numeric + categorical columns."""
    polys = [
        Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
        Polygon([(1, 0), (1, 1), (2, 1), (2, 0)]),
        Polygon([(2, 0), (2, 1), (3, 1), (3, 0)]),
        Polygon([(3, 0), (3, 1), (4, 1), (4, 0)]),
    ]
    return gpd.GeoDataFrame(
        {
            "height": [3.0, 7.5, 12.0, 5.5],
            "n_storeys": [1, 2, 4, 2],
            "structural_system": ["masonry", "concrete", "concrete", "steel"],
            "roof": ["flat", "gable", "flat", "gable"],
        },
        geometry=polys,
        crs="EPSG:4326",
    )


@pytest.fixture
def point_gdf() -> gpd.GeoDataFrame:
    """A small synthetic point GeoDataFrame with numeric + categorical columns."""
    pts = [Point(0.5, 0.5), Point(1.5, 0.5), Point(2.5, 0.5), Point(3.5, 0.5)]
    return gpd.GeoDataFrame(
        {
            "height": [3.0, 7.5, 12.0, 5.5],
            "n_storeys": [1, 2, 4, 2],
            "structural_system": ["masonry", "concrete", "concrete", "steel"],
            "roof": ["flat", "gable", "flat", "gable"],
        },
        geometry=pts,
        crs="EPSG:4326",
    )


@pytest.fixture
def real_gdf() -> gpd.GeoDataFrame:
    """Real pilot-region building footprints, trimmed for fast tests."""
    path = DATA_DIR / "san_jose_pilot_region.gpkg"
    if not path.exists():
        pytest.skip(f"example data not found: {path}")
    return gpd.read_file(path).head(80)


@pytest.fixture
def real_gdf_points(real_gdf) -> gpd.GeoDataFrame:
    pts = real_gdf.copy()
    pts["geometry"] = pts.to_crs(3857).geometry.centroid.to_crs(4326)
    return pts
