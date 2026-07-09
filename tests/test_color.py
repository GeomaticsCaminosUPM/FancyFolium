import pandas as pd
import pytest

from FancyFolium.utils.color import (
    EMOJI_PALETTE,
    categorical_colors,
    compute_feature_colors,
    emoji_for_categories,
    hsl_to_hex,
    normalise,
    percentile_range,
    plasma,
    rdylgn,
    rdylgn_r,
    resolve_cmap,
    stable_color,
    validate_count_column,
    viridis,
)

HEX_RE = r"^#[0-9a-f]{6}$"


def test_hsl_to_hex_primary_colors():
    assert hsl_to_hex(0, 100, 50) == "#ff0000"
    assert hsl_to_hex(120, 100, 50) == "#00ff00"
    assert hsl_to_hex(240, 100, 50) == "#0000ff"


@pytest.mark.parametrize("fn", [viridis, plasma, rdylgn, rdylgn_r])
def test_named_ramps_return_hex(fn):
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        c = fn(t)
        assert isinstance(c, str) and c.startswith("#") and len(c) == 7


def test_rdylgn_and_reverse_are_mirrored():
    assert rdylgn(0.0) == rdylgn_r(1.0)
    assert rdylgn(1.0) == rdylgn_r(0.0)


def test_categorical_colors_deterministic_and_unique():
    vals = ["a", "b", "c", "d"]
    c1 = categorical_colors(vals)
    c2 = categorical_colors(vals)
    assert c1 == c2
    assert len(set(c1.values())) == len(vals)


def test_stable_color_deterministic():
    assert stable_color("masonry") == stable_color("masonry")
    assert stable_color("masonry") != stable_color("concrete")


def test_percentile_range_basic():
    s = pd.Series(range(0, 101))
    lo, hi = percentile_range(s, 10, 90)
    assert lo == pytest.approx(10, abs=1)
    assert hi == pytest.approx(90, abs=1)


def test_percentile_range_empty_series():
    assert percentile_range(pd.Series([], dtype=float)) == (0.0, 1.0)


def test_normalise_clamps_to_unit_range():
    assert normalise(-5, 0, 10) == 0.0
    assert normalise(15, 0, 10) == 1.0
    assert normalise(5, 0, 10) == 0.5
    assert normalise(5, 10, 10) == 0.5  # degenerate range


def test_resolve_cmap_none_numeric_defaults_to_viridis():
    fn = resolve_cmap(None, is_categorical=False)
    assert fn is viridis


def test_resolve_cmap_unknown_string_raises():
    with pytest.raises(ValueError):
        resolve_cmap("not-a-real-cmap", is_categorical=False)


def test_resolve_cmap_bad_type_raises():
    with pytest.raises(TypeError):
        resolve_cmap(123, is_categorical=False)


def test_resolve_cmap_dict_categorical_passthrough():
    d = {"a": "#111111", "b": "#222222"}
    assert resolve_cmap(d, is_categorical=True) == d


def test_resolve_cmap_dict_on_numeric_warns():
    d = {"a": "#111111"}
    with pytest.warns(UserWarning):
        resolve_cmap(d, is_categorical=False)


def test_resolve_cmap_list_cycles_with_warning_when_short():
    with pytest.warns(UserWarning):
        result = resolve_cmap(["#111111", "#222222"], is_categorical=True,
                               unique_vals=["a", "b", "c"])
    assert result == {"a": "#111111", "b": "#222222", "c": "#111111"}


def test_resolve_cmap_list_requires_unique_vals():
    with pytest.raises(ValueError):
        resolve_cmap(["#111111"], is_categorical=True)


def test_compute_feature_colors_numeric():
    s = pd.Series([0.0, 5.0, 10.0, None])
    colors = compute_feature_colors(s, cmap="viridis", vmin=0, vmax=10, categorical=False)
    assert len(colors) == 4
    assert colors[3] == "#cccccc"  # NaN fallback
    assert colors[0] != colors[2]


def test_emoji_for_categories_deterministic_and_distinct():
    cats = ["flat", "gable", "hip"]
    m1 = emoji_for_categories(cats)
    m2 = emoji_for_categories(list(reversed(cats)))
    assert m1 == m2  # order-independent (sorted internally)
    assert len(set(m1.values())) == len(cats)
    assert all(v in EMOJI_PALETTE for v in m1.values())


def test_emoji_for_categories_cycles_when_more_values_than_palette():
    cats = [f"cat{i:03d}" for i in range(len(EMOJI_PALETTE) + 3)]
    m = emoji_for_categories(cats)
    assert len(m) == len(cats)
    assert len(set(m.values())) == len(EMOJI_PALETTE)  # repeats once palette is exhausted


def test_compute_feature_colors_categorical():
    s = pd.Series(["a", "b", "a", None])
    colors = compute_feature_colors(s, cmap=None, vmin=None, vmax=None, categorical=True)
    assert colors[0] == colors[2]
    assert colors[3] == "#cccccc"


def test_validate_count_column_accepts_integers():
    validate_count_column(pd.Series([1, 2, 3], dtype="int64"))  # should not raise


def test_validate_count_column_accepts_whole_number_floats():
    """float64 columns are common for count-like fields once they contain
    NaNs (e.g. read from a GeoPackage) - accept them if every value is whole."""
    validate_count_column(pd.Series([1.0, 2.0, 3.0, None]))  # should not raise


def test_validate_count_column_rejects_fractional_floats():
    with pytest.raises(TypeError):
        validate_count_column(pd.Series([1.0, 2.5, 3.0]))


def test_validate_count_column_rejects_strings():
    with pytest.raises(TypeError):
        validate_count_column(pd.Series(["a", "b"]))


def test_compute_feature_colors_count_defaults_vmin_to_zero():
    s = pd.Series([5, 10, 15], dtype="int64")
    colors_count = compute_feature_colors(s, cmap="viridis", vmin=None, vmax=None, categorical=False, count=True)
    colors_plain = compute_feature_colors(
        s.astype(float), cmap="viridis", vmin=0, vmax=15, categorical=False,
    )
    assert colors_count == colors_plain


def test_compute_feature_colors_count_rejects_non_integer():
    s = pd.Series([1.5, 2.5])
    with pytest.raises(TypeError):
        compute_feature_colors(s, cmap=None, vmin=None, vmax=None, categorical=False, count=True)
