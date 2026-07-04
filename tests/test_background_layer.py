import FancyFolium as ff
from FancyFolium.map_core import _state


def test_background_layer_known_provider_active_by_default():
    m = ff.background_layer("google hybrid")
    st = _state(m)
    assert len(st["background_layers"]) == 1
    entry = st["background_layers"][0]
    assert entry["name"] == "google hybrid"
    assert entry["active"] is True
    assert entry["overlay"] is False


def test_background_layer_custom_url():
    m = ff.background_layer(
        "https://example.com/{z}/{x}/{y}.png", layer_name="Custom Tiles"
    )
    st = _state(m)
    assert st["background_layers"][0]["name"] == "Custom Tiles"


def test_background_layer_second_non_overlay_deactivates_first():
    m = ff.background_layer("google hybrid")
    m = ff.background_layer("osm", m=m)
    st = _state(m)
    names_active = {e["name"]: e["active"] for e in st["background_layers"]}
    assert names_active["google hybrid"] is False
    assert names_active["osm"] is True


def test_background_layer_google_hybrid_defaults_to_dimmed_opacity():
    m = ff.background_layer("google hybrid")
    tile_layer = list(m._children.values())[-1]
    assert tile_layer.options["opacity"] == 0.6


def test_background_layer_explicit_opacity_overrides_default():
    m = ff.background_layer("google hybrid", opacity=1.0)
    tile_layer = list(m._children.values())[-1]
    assert tile_layer.options["opacity"] == 1.0


def test_background_layer_other_provider_defaults_to_full_opacity():
    m = ff.background_layer("osm")
    tile_layer = list(m._children.values())[-1]
    assert tile_layer.options["opacity"] == 1.0


def test_background_layer_overlay_does_not_deactivate_others():
    m = ff.background_layer("google hybrid")
    m = ff.background_layer("osm", m=m, overlay=True)
    st = _state(m)
    names_active = {e["name"]: e["active"] for e in st["background_layers"]}
    assert names_active["google hybrid"] is True
    assert names_active["osm"] is True
