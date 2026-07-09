"""
utils/color.py
==============
Colour helpers for FancyFolium.

Provides colour-scale functions (viridis, plasma, rdylgn, …),
HSL/RGB conversion, categorical palette generation, and the
central `resolve_cmap` entry-point used by layer builders.

All colour functions accept t ∈ [0, 1] and return a CSS hex string
unless documented otherwise.
"""

from __future__ import annotations

import hashlib
import math
import warnings
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Union

import numpy as np

if TYPE_CHECKING:
    import pandas as pd

# ── Public type alias ────────────────────────────────────────────────────────
CmapArg = Union[
    None,                         # use default (viridis for numeric, golden-angle for cat)
    str,                          # named palette: "viridis", "plasma", "rdylgn", "Reds", …
    Callable[[float], str],       # arbitrary t→hex callable
    Dict[str, str],               # category → hex  (categorical only)
    List[str],                    # ordered list of hex colours (categorical only)
]

# ── Named palette registry ───────────────────────────────────────────────────
_NAMED_CMAPS: Dict[str, Callable[[float], str]] = {}


def _register(name: str) -> Callable[[Callable[[float], str]], Callable[[float], str]]:
    """Build a decorator that registers a function as a named colourmap.

    Args:
        name: Case-insensitive name the colourmap will be looked up by.

    Returns:
        A decorator that registers the wrapped function and returns it
        unchanged.
    """
    def _dec(fn: Callable[[float], str]) -> Callable[[float], str]:
        _NAMED_CMAPS[name.lower()] = fn
        return fn
    return _dec


# ═══════════════════════════════════════════════════════════════════════════
#  HSL / RGB conversion
# ═══════════════════════════════════════════════════════════════════════════

def hsl_to_hex(h: float, s: float, l: float) -> str:  # noqa: E741 - `l` matches HSL convention
    """Convert an HSL colour to a CSS hex string.

    Args:
        h: Hue, in degrees (0-360).
        s: Saturation, as a percentage (0-100).
        l: Lightness, as a percentage (0-100).

    Returns:
        The colour as a ``"#rrggbb"`` hex string.
    """
    s /= 100
    l /= 100
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m_ = l - c / 2
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:          r, g, b = c, 0, x
    return "#{:02x}{:02x}{:02x}".format(
        int((r + m_) * 255),
        int((g + m_) * 255),
        int((b + m_) * 255),
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Built-in continuous colourmaps
# ═══════════════════════════════════════════════════════════════════════════

def _interp_stops(stops: List[tuple], t: float) -> str:
    """Linearly interpolate a hex colour between RGB colour stops.

    Args:
        stops: Ordered list of ``(r, g, b)`` float triples in ``[0, 1]``,
            evenly spaced across ``t ∈ [0, 1]``.
        t: Position to sample, clamped to ``[0, 1]``.

    Returns:
        The interpolated colour as a ``"#rrggbb"`` hex string.
    """
    t = max(0.0, min(1.0, t))
    idx = t * (len(stops) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(stops) - 1)
    f = idx - lo
    r = stops[lo][0] + f * (stops[hi][0] - stops[lo][0])
    g = stops[lo][1] + f * (stops[hi][1] - stops[lo][1])
    b = stops[lo][2] + f * (stops[hi][2] - stops[lo][2])
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


@_register("viridis")
def viridis(t: float) -> str:
    """Sample a 5-stop approximation of the viridis colourmap.

    Args:
        t: Position to sample in ``[0, 1]``.

    Returns:
        The colour at ``t`` as a ``"#rrggbb"`` hex string.
    """
    return _interp_stops([
        (0.267, 0.005, 0.329),
        (0.283, 0.301, 0.557),
        (0.129, 0.566, 0.551),
        (0.370, 0.788, 0.384),
        (0.993, 0.906, 0.144),
    ], t)


@_register("plasma")
def plasma(t: float) -> str:
    """Sample a 5-stop approximation of the plasma colourmap.

    Args:
        t: Position to sample in ``[0, 1]``.

    Returns:
        The colour at ``t`` as a ``"#rrggbb"`` hex string.
    """
    return _interp_stops([
        (0.050, 0.030, 0.528),
        (0.494, 0.012, 0.658),
        (0.799, 0.141, 0.462),
        (0.973, 0.464, 0.185),
        (0.940, 0.975, 0.131),
    ], t)


@_register("rdylgn")
def rdylgn(t: float) -> str:
    """Sample a red -> yellow -> green colour ramp.

    Args:
        t: Position to sample in ``[0, 1]`` (0 = red, 1 = green).

    Returns:
        The colour at ``t`` as a ``"#rrggbb"`` hex string.
    """
    return hsl_to_hex(t * 120, 80, 45)


@_register("rdylgn_r")
def rdylgn_r(t: float) -> str:
    """Sample a green -> yellow -> red colour ramp (reversed ``rdylgn``).

    Args:
        t: Position to sample in ``[0, 1]`` (0 = green, 1 = red).

    Returns:
        The colour at ``t`` as a ``"#rrggbb"`` hex string.
    """
    return hsl_to_hex((1 - t) * 120, 80, 45)


# ── Single-hue ramps (matplotlib-like names) ────────────────────────────────

def _single_hue_ramp(hue: float, t: float) -> str:
    """Sample a single-hue ramp from light to saturated.

    Args:
        hue: Fixed HSL hue, in degrees (0-360).
        t: Position to sample in ``[0, 1]`` (0 = light, 1 = saturated).

    Returns:
        The colour at ``t`` as a ``"#rrggbb"`` hex string.
    """
    s = 30 + t * 65
    l = 95 - t * 55
    return hsl_to_hex(hue, s, l)


for _hue, _names in [
    (0,   ["reds", "red"]),
    (240, ["blues", "blue"]),
    (120, ["greens", "green"]),
    (60,  ["yellows", "yellow"]),
    (280, ["purples", "purple"]),
    (30,  ["oranges", "orange"]),
]:
    for _n in _names:
        _NAMED_CMAPS[_n] = (lambda _h: (lambda t: _single_hue_ramp(_h, t)))(_hue)


# ═══════════════════════════════════════════════════════════════════════════
#  Categorical helpers
# ═══════════════════════════════════════════════════════════════════════════

def categorical_colors(values: List, seed: int = 0) -> Dict[str, str]:
    """Assign deterministic, distinct colours to a list of unique values.

    Uses the golden-angle hue-stepping method, so consecutive categories are
    always visually distinct regardless of how many there are.

    Args:
        values: Unique category values to assign colours to.
        seed: Hue offset (degrees) added to every assignment; change it to
            get a different (but still deterministic) palette.

    Returns:
        A mapping of each value to its ``"#rrggbb"`` hex colour.
    """
    out: Dict[str, str] = {}
    for i, v in enumerate(values):
        h = (i * 137.508 + seed) % 360
        out[v] = hsl_to_hex(h, 65, 50)
    return out


# ── Emoji markers ────────────────────────────────────────────────────────

EMOJI_PALETTE: List[str] = [
    "🔵", "🟢", "🟡", "🟠", "🔴", "🟣", "🟤", "⚫", "⚪",
    "🔺", "🔻", "⭐", "💠", "🔶", "🔷", "♦️", "✅", "❗",
    "🏠", "🏢", "🏭", "🌳", "🚗", "⚡", "💧", "🔥", "❄️", "☀️",
]


def emoji_for_categories(values: List) -> Dict[str, str]:
    """Assign a deterministic, distinct emoji to each unique category value.

    Values are sorted (by string form) before assignment, so the same set
    of categories always maps to the same emojis regardless of row order.
    Cycles through ``EMOJI_PALETTE`` if there are more categories than icons.

    Args:
        values: Category values (any hashable/stringable type) to assign
            emoji to. Duplicates are fine - only unique values get an entry.

    Returns:
        A mapping of each value's string form to its assigned emoji.
    """
    ordered = sorted({str(v) for v in values})
    return {v: EMOJI_PALETTE[i % len(EMOJI_PALETTE)] for i, v in enumerate(ordered)}


def stable_color(value: object, saturation: float = 65, lightness: float = 50) -> str:
    """Compute a deterministic colour for any hashable value.

    Uses an MD5 hash of the value's string form, so the same value always
    gets the same colour across processes and sessions (unlike
    :func:`categorical_colors`, which depends on assignment order).

    Args:
        value: Any value convertible to ``str``.
        saturation: HSL saturation, as a percentage (0-100).
        lightness: HSL lightness, as a percentage (0-100).

    Returns:
        The colour as a ``"#rrggbb"`` hex string.
    """
    h = int(hashlib.md5(str(value).encode()).hexdigest()[:4], 16) % 360
    return hsl_to_hex(h, saturation, lightness)


# ═══════════════════════════════════════════════════════════════════════════
#  Normalisation
# ═══════════════════════════════════════════════════════════════════════════

def percentile_range(series: "pd.Series", pmin: float = 10, pmax: float = 90) -> tuple:
    """Compute a percentile-based ``(vmin, vmax)`` range for a numeric series.

    Args:
        series: Numeric pandas Series (NaN/infinite values are ignored).
        pmin: Lower percentile (0-100).
        pmax: Upper percentile (0-100).

    Returns:
        A ``(vmin, vmax)`` tuple. Returns ``(0.0, 1.0)`` if *series* has no
        finite values.
    """
    vals = series.dropna().values.astype(float)
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return 0.0, 1.0
    return float(np.percentile(vals, pmin)), float(np.percentile(vals, pmax))


def normalise(value: float, vmin: float, vmax: float) -> float:
    """Clamp-normalise a scalar value to the ``[0, 1]`` range.

    Args:
        value: Value to normalise.
        vmin: Value that should map to 0.
        vmax: Value that should map to 1.

    Returns:
        The normalised value, clamped to ``[0, 1]``. Returns ``0.5`` if
        ``vmax <= vmin`` (a degenerate range).
    """
    if vmax <= vmin:
        return 0.5
    return max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))


# ═══════════════════════════════════════════════════════════════════════════
#  Central cmap resolver
# ═══════════════════════════════════════════════════════════════════════════

def resolve_cmap(
    cmap: CmapArg,
    *,
    is_categorical: bool,
    unique_vals: Optional[List] = None,
) -> Union[Callable[[float], str], Dict]:
    """Normalise a ``cmap`` argument into a concrete colour-mapping form.

    Args:
        cmap: Colour map argument - ``None``, a named palette string, a
            ``t -> hex`` callable, a ``{value: hex}`` dict, or an ordered
            list of hex colours (the last two are categorical-only).
        is_categorical: Whether the target column is categorical.
        unique_vals: The column's unique values. Required when ``cmap`` is
            a list; used to build a concrete ``{value: hex}`` dict for
            categorical named palettes when provided.

    Returns:
        For numeric (continuous) layers: a callable ``t ∈ [0, 1] -> hex``.
        For categorical layers: a ``{value: hex}`` dict if ``unique_vals``
        was given, otherwise a callable used per-value.

    Raises:
        TypeError: If ``cmap`` has an unrecognised type.
        ValueError: If ``cmap`` is a string name not in the registry, or a
            list given without ``unique_vals``.
    """
    if isinstance(cmap, dict):
        if not is_categorical:
            warnings.warn(
                "A dict cmap was supplied for a numeric column.  "
                "The layer will be treated as categorical.",
                UserWarning, stacklevel=3,
            )
        return cmap

    if isinstance(cmap, list):
        if not is_categorical:
            warnings.warn(
                "A list cmap was supplied for a numeric column.  "
                "The layer will be treated as categorical.",
                UserWarning, stacklevel=3,
            )
        if unique_vals is None:
            raise ValueError("unique_vals must be provided when cmap is a list.")
        if len(cmap) < len(unique_vals):
            warnings.warn(
                f"cmap list has {len(cmap)} colours but there are "
                f"{len(unique_vals)} unique values.  Colors will cycle.",
                UserWarning, stacklevel=3,
            )
        return {v: cmap[i % len(cmap)] for i, v in enumerate(unique_vals)}

    if callable(cmap):
        return cmap

    if cmap is None:
        if is_categorical:
            if unique_vals is not None:
                return categorical_colors(unique_vals)
            return categorical_colors
        return viridis

    if isinstance(cmap, str):
        key = cmap.lower()
        if key in _NAMED_CMAPS:
            fn = _NAMED_CMAPS[key]
            if is_categorical and unique_vals is not None:
                n = len(unique_vals)
                return {
                    v: fn(i / max(n - 1, 1))
                    for i, v in enumerate(unique_vals)
                }
            return fn
        raise ValueError(
            f"Unknown cmap name '{cmap}'.  "
            f"Available: {sorted(_NAMED_CMAPS.keys())}."
        )

    raise TypeError(
        f"cmap must be None, str, callable, dict, or list of hex strings; "
        f"got {type(cmap).__name__!r}."
    )


def validate_count_column(series: "pd.Series", column_name: str = "column") -> None:
    """Validate that a series is suitable for use as a "counts" column.

    Accepts both true integer dtypes and float dtypes whose non-null values
    are all integral (e.g. ``float64`` columns with missing values, which
    pandas/GeoPackage readers commonly produce even for count-like fields).

    Args:
        series: The column to validate.
        column_name: Name used in the error message, for context.

    Raises:
        TypeError: If *series* is not numeric, or holds any non-null value
            with a fractional part.
    """
    import pandas as pd

    if pd.api.types.is_integer_dtype(series):
        return
    if pd.api.types.is_float_dtype(series):
        vals = series.dropna()
        if len(vals) == 0 or (vals == vals.round()).all():
            return
        raise TypeError(
            f"'{column_name}' was passed with count=True but holds non-whole-number "
            f"values (e.g. {vals[vals != vals.round()].iloc[0]!r}). "
            "Count columns must hold whole numbers."
        )
    raise TypeError(
        f"'{column_name}' was passed with count=True but is not a numeric column "
        f"(dtype={series.dtype}). Count columns must hold whole numbers."
    )


def compute_feature_colors(
    series: "pd.Series",
    *,
    cmap: CmapArg,
    vmin: Optional[float],
    vmax: Optional[float],
    categorical: bool,
    count: bool = False,
    fallback_color: str = "#cccccc",
) -> Dict:
    """Compute a per-row colour mapping for a column's values.

    Args:
        series: Column values (pandas Series), indexed like the source
            GeoDataFrame.
        cmap: Colour map argument (see :func:`resolve_cmap`).
        vmin: Lower scale bound for numeric columns. Defaults to 0 for
            count columns, otherwise the 10th percentile.
        vmax: Upper scale bound for numeric columns. Defaults to the
            column max for count columns, otherwise the 90th percentile.
        categorical: Force categorical treatment even for numeric columns.
        count: Treat as a "counts" column (validated via
            :func:`validate_count_column`); changes the ``vmin``/``vmax``
            defaults as described above.
        fallback_color: Colour used for ``NaN``/missing values.

    Returns:
        A mapping of each row's series index to its ``"#rrggbb"`` hex
        colour.

    Raises:
        TypeError: If ``count=True`` and *series* isn't a valid counts
            column (see :func:`validate_count_column`).
    """
    import pandas as pd

    if count:
        validate_count_column(series)

    out: Dict = {}
    is_num = pd.api.types.is_numeric_dtype(series) and not categorical

    if not is_num or isinstance(cmap, (dict, list)):
        unique_vals = series.dropna().unique().tolist()
        resolved = resolve_cmap(cmap, is_categorical=True, unique_vals=unique_vals)

        if callable(resolved) and not isinstance(resolved, dict):
            color_map = resolved(unique_vals) if not isinstance(resolved, dict) else resolved
        else:
            color_map = resolved

        for idx, val in series.items():
            if val is None or (isinstance(val, float) and math.isnan(val)):
                out[idx] = fallback_color
            else:
                out[idx] = color_map.get(val, fallback_color)
    else:
        fn = resolve_cmap(cmap, is_categorical=False)
        vals_clean = series.dropna()
        if vmin is None:
            vmin = 0.0 if count else float(np.nanpercentile(vals_clean, 10))
        if vmax is None:
            vmax = float(vals_clean.max()) if count else float(np.nanpercentile(vals_clean, 90))

        for idx, val in series.items():
            if val is None or (isinstance(val, float) and math.isnan(val)):
                out[idx] = fallback_color
            else:
                t = normalise(float(val), vmin, vmax)
                out[idx] = fn(t)

    return out
