import pytest

import FancyFolium as ff
from FancyFolium.map_core import _state


def test_raster_layer_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ff.raster_layer(str(tmp_path / "nope.tif"))


def test_vector_to_raster_and_raster_layer_roundtrip(tmp_path, polygon_gdf):
    out = tmp_path / "height.tif"
    path = ff.vector_to_raster(polygon_gdf, str(out), column="height", cmap="Reds", resolution=5000.0)
    assert path.exists()

    m = ff.raster_layer(str(path), layer_name="height raster")
    st = _state(m)
    assert len(st["raster_layers"]) == 1
    assert st["raster_layers"][0]["name"] == "height raster"


def test_vector_to_raster_requires_valid_column(tmp_path, polygon_gdf):
    with pytest.raises(ValueError):
        ff.vector_to_raster(polygon_gdf, str(tmp_path / "x.tif"), column="does_not_exist")


def test_raster_layer_background_category(tmp_path, polygon_gdf):
    out = tmp_path / "height.tif"
    ff.vector_to_raster(polygon_gdf, str(out), column="height", resolution=5000.0)
    m = ff.raster_layer(str(out), layer_name="bg raster", background=True)
    st = _state(m)
    assert len(st["bg_raster_layers"]) == 1
    assert st["raster_layers"] == []


def test_raster_layer_with_legend_dict(tmp_path, polygon_gdf):
    out = tmp_path / "height.tif"
    ff.vector_to_raster(polygon_gdf, str(out), column="height", resolution=5000.0)
    m = ff.raster_layer(
        str(out), layer_name="height raster",
        legend={"entries": [{"label": "low", "color": "#ffcccc"}]},
    )
    st = _state(m)
    leg = st["legends"]["height raster"][0]
    assert leg["type"] == "categorical"
