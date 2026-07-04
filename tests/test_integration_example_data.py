"""
End-to-end tests exercising the full package against the real pilot-region
GeoPackages in examples/data/ (the same data used in examples/example.ipynb).
"""

import geopandas as gpd
import pytest

import FancyFolium as ff
from FancyFolium.map_core import _state


def test_full_workflow_against_real_data(real_gdf, real_gdf_points, tmp_path):
    m = ff.create_map()
    m = ff.background_layer("google hybrid", m=m)
    m = ff.background_layer("osm", m=m, overlay=False, active=False)

    m = ff.vector_layer(
        real_gdf, layer_name="footprints", column="height", cmap="Reds",
        vmin=0, vmax=10, popup=["height", "n_storeys", "year"], m=m,
    )
    m = ff.vector_layer(
        real_gdf, layer_name="structure", column="structural_system",
        categorical=True, overlay=False, active=False, m=m,
    )

    m = ff.marker_layer(
        real_gdf_points, layer_name="buildings", column="height", cmap="viridis",
        marker_column="roof", overlay=True, active=False, m=m,
    )

    raster_path = ff.vector_to_raster(
        real_gdf, str(tmp_path / "height.tif"), column="height", cmap="Reds", resolution=5.0,
    )
    m = ff.raster_layer(str(raster_path), layer_name="height raster", overlay=True, active=False, m=m)

    out_html = tmp_path / "map.html"
    ff.export(m, str(out_html))

    st = _state(m)
    assert out_html.exists()
    assert {"footprints", "structure", "buildings"} <= set(st["legends"].keys())
    assert st["legends"]["buildings"][0]["type"] == "numeric"
    buildings_entry = next(e for e in st["vector_layers"] if e["name"] == "buildings")
    assert buildings_entry["marker_column"] == "roof"
    assert len(st["background_layers"]) == 2
    assert len(st["raster_layers"]) == 1


def test_merge_maps_across_cities(tmp_path):
    from pathlib import Path

    data_dir = Path(__file__).parent.parent / "examples" / "data"
    files = {
        "San Jose": data_dir / "san_jose_pilot_region.gpkg",
        "Guatemala": data_dir / "guatemala_pilot_region.gpkg",
        "Santo Domingo": data_dir / "santo_domingo_pilot_region.gpkg",
    }
    for p in files.values():
        if not p.exists():
            pytest.skip(f"example data not found: {p}")

    maps = []
    for name, path in files.items():
        gdf = gpd.read_file(path).head(50)
        mi = ff.create_map()
        mi = ff.background_layer("google hybrid", m=mi)
        mi = ff.vector_layer(gdf, layer_name="footprints", column="height", cmap="Reds", m=mi)
        maps.append(mi)

    merged = ff.merge_maps(maps, list(files.keys()))
    out_html = tmp_path / "merged.html"
    ff.export(merged, str(out_html))
    assert out_html.exists()
