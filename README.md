# FancyFolium

A composable [Folium](https://python-visualization.github.io/folium/) mapping
library with a fully-styled three-panel layer control, automatic legends,
named colourmaps, emoji/icon markers, a statistics panel with live
histograms, per-layer opacity sliders, and vector-to-raster conversion.

FancyFolium exists to make it fast to turn geospatial research data - building-footprint surveys, raster models, structural/damage assessments - into interactive maps that both technical and non-technical audiences can
explore, without hand-writing Leaflet/JavaScript for every project.

[![PyPI](https://img.shields.io/pypi/v/fancyfolium)](https://pypi.org/project/fancyfolium/)
[![Python](https://img.shields.io/pypi/pyversions/fancyfolium)](https://pypi.org/project/fancyfolium/)
[![Docs](https://readthedocs.org/projects/fancyfolium/badge/?version=stable)](https://fancyfolium.readthedocs.io/en/stable/)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/GeomaticsCaminosUPM/FancyFolium/blob/main/examples/example.ipynb)

By [Miguel Ureña Pliego](https://miguelurenapliego.github.io/) - [GitHub](https://github.com/MiguelUrenaPliego) ·
[ORCID](https://orcid.org/0000-0001-6594-2566) ·
[LinkedIn](https://www.linkedin.com/in/miguel-urena-pliego) - [Advanced Geomatics Research Group (AGA)](https://blogs.upm.es/aga/en/),
Universidad Politécnica de Madrid. See [Author](#author) below for more.

---

## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [Control panel](#control-panel)
- [Public API](#public-api)
  - [`create_map`](#create_maplocationnone-zoom16)
  - [`background_layer`](#background_layername_or_url-)
  - [`raster_layer`](#raster_layerraster-)
  - [`vector_layer`](#vector_layergdf-)
  - [`marker_layer`](#marker_layergdf-)
  - [`merge_maps`](#merge_mapsmaps-names)
  - [`export`](#exportm-path-raster_pathnone)
- [Colourmaps (`cmap`)](#colourmaps-cmap)
- [Count columns (`count=True`)](#count-columns-counttrue)
- [Popups](#popups)
- [Style](#style)
- [Statistics panel & histograms](#statistics-panel--histograms)
- [`vector_to_raster`](#vector_to_raster)
- [Colour & geometry helpers](#colour--geometry-helpers)
- [Errors and warnings](#errors-and-warnings)
- [Documentation](#documentation)
- [Development](#development)
- [Author](#author)

---

## Installation

```bash
pip install fancyfolium
```

Or, for local development (see [Development](#development)):

```bash
pip install -r requirements.txt
pip install -e .
```

**Requirements:** Python ≥ 3.9, `folium`, `geopandas`, `shapely`, `pandas`,
`numpy`, `mapclassify`, and `rasterio` (raster features only - importing
`FancyFolium` itself does not require it).

---

## Quick start

```python
import geopandas as gpd
import FancyFolium as ff

gdf = gpd.read_file("buildings.gpkg")

m = ff.create_map()
m = ff.background_layer("google hybrid", m=m)
m = ff.vector_layer(
    gdf,
    column="height",
    cmap="Reds",
    vmin=0, vmax=50,
    overlay=True,
    popup=["height", "n_storeys"],
    legend_unit="m",
    m=m,
)
ff.export(m, "output/map.html")
```

See [`examples/example.ipynb`](examples/example.ipynb) for a short, beginner-friendly
walkthrough (one raster layer, one polygon layer, one marker layer) against real
building-footprint data - it also has an "Open in Colab" button, so you can run it
without installing anything locally.

---

## Control panel

Every map gets a floating control panel (top-right), a legend stack
(bottom-right), and a statistics-panel button (bottom-left, 📊) - all
injected automatically, no extra setup required.

```
┌──────────────────────────────────┐
│ Vector │ Background │ Raster     │  ← tabs (Vector opens first)
├──────────────────────────────────┤
│ [dropdown – single active]  ⚙    │  ← overlay=False layers, + opacity slider
│ ──────────────────────────────── │
│ ☑ Layer A  ⚙                     │  ← overlay=True layers (independent)
│ ☐ Layer B  ⚙                     │
└──────────────────────────────────┘
```

- **Dropdown** (`overlay=False`): radio-style, only one active at a time.
- **Checkboxes** (`overlay=True`): any combination can be toggled.
- **⚙** next to each layer reveals an opacity slider for that layer alone.
- Legends (bottom-right) update automatically as layers are toggled.
- **📊** (bottom-left) opens the statistics panel: pick any vector/marker
  layer to see a live histogram of its colormap column (see
  [Statistics panel & histograms](#statistics-panel--histograms)).

---

## Public API

### `create_map(location=None, zoom=16)`

Create a blank map with the control panel attached. No background tile is
added - call `background_layer()` for that.

```python
m = ff.create_map(location=[14.6, -90.5], zoom=14)
```

---

### `background_layer(name_or_url, ...)`

```python
def background_layer(
    name_or_url: str,
    layer_name: str | None = None,
    opacity: float | None = None,
    overlay: bool = False,
    active: bool = True,
    m: folium.Map | None = None,
) -> folium.Map
```

Add a tile background. Built-in provider keys (case-insensitive):
`"google hybrid"`, `"google satellite"`, `"google roads"`, `"osm"` /
`"openstreetmap"`, `"cartodb light"`, `"cartodb dark"`, `"esri satellite"`,
`"stamen toner"`, `"stamen terrain"` - or pass any Leaflet tile URL template
(`{x}`/`{y}`/`{z}`) directly.

`opacity` defaults to each provider's own default (Google Hybrid defaults to
`0.6` so the underlying imagery stays visible through its labels; everything
else defaults to `1.0`) unless you override it.

```python
m = ff.background_layer("google hybrid", m=m)                      # opacity 0.6 by default
m = ff.background_layer("cartodb light", overlay=True, m=m)        # independently toggleable
```

---

### `raster_layer(raster, ...)`

```python
def raster_layer(
    raster: str,
    layer_name: str | None = None,
    opacity: float = 1.0,
    bounds: list[list[float]] | None = None,
    *,
    m: folium.Map | None = None,
    overlay: bool = False,
    background: bool = False,
    active: bool = True,
    legend: dict | None = None,
) -> folium.Map
```

Add a raster image (GeoTIFF, PNG, JPEG, …).

| Parameter | Notes |
|---|---|
| `raster` | Path to a geo-referenced or plain image file. |
| `bounds` | `[[south, west], [north, east]]` in EPSG:4326. For geo-referenced files, only the overlapping window is read (efficient for very large rasters); for plain images it defines the map placement and is required. |
| `background` | `True` → grouped with tile backgrounds in the control panel. |
| `legend` | A dict describing the legend, or `None` for no legend (see below). |

**Legend dict shapes:**

```python
# Numeric
legend={"vmin": 0, "vmax": 3000, "cmap": "viridis", "unit": "m"}

# Categorical
legend={"entries": [{"label": "Forest", "color": "#2ca02c"},
                    {"label": "Water",  "color": "#1f77b4"}]}
```

```python
m = ff.raster_layer(
    "/data/dem.tif", layer_name="DEM", opacity=0.7, overlay=True,
    legend={"vmin": 0, "vmax": 4000, "cmap": "viridis", "unit": "m"},
)

# Clip a huge raster to a specific area on load:
m = ff.raster_layer(
    "/data/world.tif", bounds=[[14.5, -91], [15.5, -90]],
    layer_name="Clipped DEM", overlay=True,
)
```

---

### `vector_layer(gdf, ...)`

```python
def vector_layer(
    gdf: gpd.GeoDataFrame,
    opacity: float = 1.0,
    layer_name: str | None = None,
    column: str | None = None,
    color: str = "blue",
    cmap: CmapArg = None,
    vmin: float | None = None,
    vmax: float | None = None,
    categorical: bool = False,
    count: bool = False,
    overlay: bool = False,
    popup: list[str] | dict | None = None,
    m: folium.Map | None = None,
    style: dict | None = None,
    legend: bool = True,
    legend_unit: str | None = None,
    active: bool = True,
) -> folium.Map
```

Add any polygon/line/point GeoDataFrame as a styled GeoJSON layer.

| Parameter | Default | Notes |
|---|---|---|
| `gdf` | - | Any geometry; auto-reprojected to EPSG:4326. |
| `layer_name` | `column` | Required when `column` is `None`. |
| `column` | `None` | Attribute used for colour mapping (numeric, categorical, or count). |
| `color` | `"blue"` | Uniform fill colour when no column. |
| `cmap` | `None` | See [Colourmaps](#colourmaps-cmap). |
| `vmin` / `vmax` | `None` | P10/P90 by default (0/max for count columns - see below). |
| `categorical` | `False` | Force categorical treatment. Mutually exclusive with `count`. |
| `count` | `False` | Treat `column` as a "counts" column - see [Count columns](#count-columns-counttrue). |
| `overlay` | `False` | `True` → checkbox; `False` → dropdown. |
| `popup` | `None` | See [Popups](#popups). |
| `style` | `None` | See [Style](#style). |
| `legend` | `True` | Show a legend for this layer's `column`. |
| `legend_unit` | `None` | Unit appended to numeric legend labels. |

```python
m = ff.vector_layer(
    gdf, opacity=0.8, layer_name="footprints", column="height",
    cmap="Reds", vmin=0, vmax=50, overlay=True,
    popup=["height", "n_storeys"], legend_unit="m", m=m,
)
```

---

### `marker_layer(gdf, ...)`

```python
def marker_layer(
    gdf: gpd.GeoDataFrame,
    layer_name: str | None = None,
    column: str | None = None,
    marker_column: str | None = None,
    marker: str | dict | None = None,
    color: str = "blue",
    cmap: CmapArg = None,
    vmin: float | None = None,
    vmax: float | None = None,
    categorical: bool = False,
    count: bool = False,
    overlay: bool = False,
    popup: list[str] | dict | None = None,
    m: folium.Map | None = None,
    style: dict | None = None,
    legend: bool = True,
    legend_unit: str | None = None,
    active: bool = True,
    histogram: bool = True,
) -> folium.Map
```

Same as `vector_layer`, for point data, plus:

| Extra parameter | Notes |
|---|---|
| `marker` | Fixed text/emoji (`str`) for every row, or a `{category: symbol}` dict overriding specific `marker_column` values. `None` shows each row's raw `marker_column` value as-is. |
| `marker_column` | Column whose value is shown inside each marker (always categorical). Pre-populate it with emojis for emoji markers - see `FancyFolium.emoji_for_categories`. |
| `histogram` | If `column` (colormap) and `marker_column` are both given, expose `marker_column` to the map's **statistics panel** (bottom-left 📊 button) so its per-category breakdown - with icons, class labels, and **#/%** / **lin/log** toggle buttons - can be viewed for this layer on demand, and add a marker-values legend. Default `True`. |

Markers with no `column`, `marker`, or `marker_column` render as a
Google-Maps-style teardrop pin instead of a plain circle. When
`marker_column` differs from `column`, a **second** legend box lists each
category's icon, separate from the colormap legend; if they're the same
column, only one legend is shown.

```python
gdf["geometry"] = gdf.to_crs(3857).geometry.centroid.to_crs(4326)

m = ff.marker_layer(
    gdf, layer_name="buildings", column="height", cmap="viridis",
    marker_column="roof", marker={"flat": "⬜", "gable": "⬛", "metallic": "⚙️"},
    m=m,
)
```

---

### `merge_maps(maps, names)`

Combine independent maps into one with a top-centre dropdown switcher.
Every layer from every map lives on the first map's Leaflet instance - switching just toggles visibility, so it's instant and never re-renders.

```python
merged = ff.merge_maps([m_city_a, m_city_b], ["Guatemala City", "San José"])
ff.export(merged, "merged.html")
```

---

### `export(m, path, raster_path=None)`

```python
ff.export(m, "maps/my_map.html")
# Extract base64-embedded rasters to separate PNG files:
ff.export(m, "maps/my_map.html", raster_path="rasters")
```

---

## Colourmaps (`cmap`)

`cmap` accepts four forms:

**1. Named string**

```python
cmap="viridis"    # default for numeric columns
cmap="plasma"
cmap="rdylgn"     # Red -> Yellow -> Green
cmap="rdylgn_r"   # reversed
cmap="Reds"       # single-hue ramp (light -> dark); also Blues/Greens/Purples/Oranges/Yellows
```

For categorical columns, a continuous named palette is sampled at
evenly-spaced points; `None` uses a deterministic golden-angle palette
(see `categorical_colors`).

**2. Callable `t ∈ [0, 1] -> hex`**

```python
cmap=lambda t: f"#{int(t*255):02x}00{int((1-t)*255):02x}"
```

**3. Dict (categorical)**

```python
cmap={"Residential": "#e05c5c", "Commercial": "#5c7de0", "Park": "#5ce07d"}
```

**4. List of hex colours (categorical; cycles if there are more categories than colours)**

```python
cmap=["#e05c5c", "#5c7de0", "#5ce07d", "#e0c45c"]
```

---

## Count columns (`count=True`)

Pass `count=True` on `vector_layer`/`marker_layer`/`vector_to_raster` to
treat a column as a **counts** field (number of storeys, population,
occurrences, …) rather than a general continuous numeric column:

- Validated via `FancyFolium.validate_count_column` - raises `TypeError`
  unless every non-null value is a whole number (true integer dtypes and
  float dtypes with only whole-number values, e.g. from a GeoPackage column
  with missing values, are both accepted).
- The colour scale defaults to `vmin=0` / `vmax=column.max()` instead of the
  general numeric default (10th/90th percentile), since counts are
  naturally bounded below by zero.
- Mutually exclusive with `categorical` (`ValueError` if both are `True`).

```python
m = ff.vector_layer(gdf, column="n_storeys", count=True, cmap="Blues", m=m)
```

---

## Popups

```python
# Simple list of column names, shown in both tooltip (hover) and popup (click)
popup=["height", "n_storeys", "year"]

# Dict form - control tooltip/popup independently
popup={
    "fields":  ["height", "n_storeys", "year"],
    "tooltip": True,   # hover tooltip
    "popup":   True,   # click popup
}
```

---

## Style

`vector_layer`'s `style=` dict:

```python
style={
    "stroke_color": "#ffffff",   # outline colour; defaults to the fill colour
    "weight":        0.8,        # outline width (also "stroke_width")
    "stroke_opacity": 0.8,
    "dashArray":     "4 2",      # also "dash_array"
    "fill_opacity":  0.8,        # overrides the layer's `opacity`
}
```

`marker_layer`'s `style=` dict supports `stroke_color` and `weight` (marker
border colour/width) only.

---

## Statistics panel & histograms

The bottom-left **📊** button opens a panel where you pick any vector or
marker layer and see a live histogram of its colormap `column`:

- **Numeric columns:** binned histogram with a **Bins** count input.
- **Categorical columns:** one bar per category.
- **Marker layers with `marker_column`:** grouped by `marker_column`
  category instead, with each bar's icon and class label drawn above it.

Two toggle buttons apply to every histogram:

- **`#` / `%`** - switch the y-axis between raw count and percent-of-total.
- **`lin` / `log`** - switch how numeric histogram **bin edges** are chosen
  (not the y-axis scale). Log-spaced bins give skewed data - e.g. a
  handful of 100 m towers among many 3–12 m buildings - much better
  resolution at the common end of the distribution than evenly-spaced
  bins would.

---

## `vector_to_raster`

Burn a GeoDataFrame to a raster file (always RGBA with a transparent
background).

```python
from FancyFolium import vector_to_raster

vector_to_raster(
    gdf,
    output_path="output/heights.tif",   # .tif/.tiff -> GTiff (preserves CRS)
    column="height",
    cmap="viridis",
    vmin=0, vmax=50,
    resolution=10,                       # ~10 m/pixel at the equator
    opacity=1.0,
)

# PNG output writes a .meta.json sidecar with CRS + bounds
vector_to_raster(
    gdf,
    output_path="tiles/layer.png",
    column="category",
    cmap={"A": "#e05c5c", "B": "#5c7de0"},
    categorical=True,
    resolution=50,
)
```

| Parameter | Default | Notes |
|---|---|---|
| `output_path` | - | `.tif`/`.tiff` → GTiff; anything else → PNG + `.meta.json` sidecar. |
| `resolution` | `100.0` | Approximate pixel size in metres at the equator. |
| `column` | `None` | Colour-mapping attribute (same as `vector_layer`). |
| `cmap` | `None` | Same options as `vector_layer`. |
| `vmin` / `vmax` | `None` | P10/P90 by default (0/max for `count=True`). |
| `categorical` | `False` | Force categorical. Mutually exclusive with `count`. |
| `count` | `False` | Treat `column` as a counts column - see [Count columns](#count-columns-counttrue). |
| `opacity` | `1.0` | Alpha multiplier, 0–1. |
| `fmt` | `"GTiff"` | rasterio driver name. |
| `bounds` | `None` | Restrict to `[[S,W],[N,E]]`; defaults to the GeoDataFrame's bbox. |

---

## Colour & geometry helpers

| Function | Description |
|---|---|
| `viridis(t)` / `plasma(t)` | 5-stop colourmap approximations → hex. |
| `rdylgn(t)` / `rdylgn_r(t)` | Red→Yellow→Green ramp (and reversed). |
| `hsl_to_hex(h, s, l)` | Raw HSL → hex. |
| `categorical_colors(values)` | Deterministic golden-angle categorical palette. |
| `stable_color(value)` | Deterministic colour from an MD5 hash (stable across sessions). |
| `emoji_for_categories(values)` | Deterministic, distinct emoji per category (`EMOJI_PALETTE`). |
| `percentile_range(series)` | P10/P90 `(vmin, vmax)` for a numeric series. |
| `resolve_cmap(cmap, ...)` | Normalise any `cmap` argument to a callable or dict. |
| `compute_feature_colors(series, ...)` | Compute `{index: hex}` for a full column. |
| `validate_count_column(series)` | Raise `TypeError` unless a series holds whole numbers. |
| `bounds_center` / `gdf_bounds_wgs84` / `bounds_to_folium` | Bounding-box helpers. |
| `raster_bounds_wgs84` / `clip_raster_to_bounds` | Raster CRS/bounds helpers (rasterio). |

---

## Errors and warnings

| Situation | Behaviour |
|---|---|
| `cmap` is a string not in the registry | `ValueError` with the list of valid names |
| `column` not in the GeoDataFrame | `ValueError` |
| `categorical` and `count` both `True` | `ValueError` |
| `count=True` and `column` isn't whole numbers | `TypeError` |
| GeoDataFrame has no CRS | `UserWarning` (assumes EPSG:4326) |
| `cmap` is dict/list but column is numeric | `UserWarning` (treated as categorical) |
| `marker_layer` with non-point geometry | `UserWarning` (centroids used) |
| Raster has no CRS and no `bounds=` | `ValueError` |
| Raster file not found | `FileNotFoundError` |
| `merge_maps` length mismatch | `ValueError` |
| `merge_maps` fewer than 2 maps | `ValueError` |
| `popup` has an unsupported type | `TypeError` |

---

## Documentation

Full API reference (generated from the Google-style docstrings in the
source via `sphinx.ext.autodoc` + `sphinx.ext.napoleon`) is built with
[Sphinx](https://www.sphinx-doc.org/) + the [Furo](https://github.com/pradyunsg/furo)
theme. To build and view it locally:

```bash
pip install -r requirements-docs.txt
sphinx-build -b html docs docs/_build/html
python -m http.server -d docs/_build/html 8000   # http://127.0.0.1:8000
```

See [`docs/`](docs/) for the source pages (`conf.py`, `index.rst`,
`getting-started.md`, `api/*.rst`). For a runnable, hands-on introduction
instead, see [`examples/example.ipynb`](examples/example.ipynb) - no local
installation needed thanks to its "Open in Colab" button.

---

## Development

```bash
git clone <repo-url>
cd FancyFolium
uv sync --all-groups     # or: pip install -e ".[dev]" / pip install -r requirements.txt
pytest                    # run the test suite
```

The `examples/` folder contains `example.ipynb`, a full walkthrough of every
feature, and `data/*.gpkg` sample building-footprint datasets it runs
against.

Releases are cut via `.github/workflows/release.yml`: pushing a `vX.Y.Z` tag
builds the package, publishes to PyPI, and creates the GitHub Release
automatically; the `latest`/`stable` documentation versions on Read the Docs
stay in sync on their own from there.

---

## Author

FancyFolium is developed by **Miguel Ureña Pliego**, as part of the
[Advanced Geomatics Research Group (AGA)](https://blogs.upm.es/aga/en/) at the
Universidad Politécnica de Madrid. The package grew out of the group's need to
turn geospatial research data - building-footprint surveys,
structural/damage assessments, raster models - into shareable, interactive
maps for both technical and non-technical audiences, without hand-writing
Leaflet/JavaScript for every project.

- GitHub: [github.com/MiguelUrenaPliego](https://github.com/MiguelUrenaPliego)
- Personal website: [miguelurenapliego.github.io](https://miguelurenapliego.github.io/)
- ORCID: [orcid.org/0000-0001-6594-2566](https://orcid.org/0000-0001-6594-2566)
- LinkedIn: [linkedin.com/in/miguel-urena-pliego](https://www.linkedin.com/in/miguel-urena-pliego)
- Research group: [Advanced Geomatics Research Group (AGA)](https://blogs.upm.es/aga/en/),
  Universidad Politécnica de Madrid
