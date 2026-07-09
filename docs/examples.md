# Examples

## Run it interactively (recommended)

The full version of the walkthrough below is a runnable Jupyter notebook at
[`examples/example.ipynb`](https://github.com/GeomaticsCaminosUPM/FancyFolium/blob/main/examples/example.ipynb),
written for people who have never used Python or Jupyter before:

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/GeomaticsCaminosUPM/FancyFolium/blob/main/examples/example.ipynb)

Click the badge to open and run it in Google Colab, no local install needed
- it installs FancyFolium and downloads the sample data automatically. Or
clone the repository and open `examples/example.ipynb` in your own Jupyter.

## The walkthrough

This is the same three-layer map built by the notebook, reproduced here for
reference: one raster layer, one polygon layer, one marker layer.

### 1. Load the data

`gdf` is a table of building footprints, one row per building, loaded with
[GeoPandas](https://geopandas.org/):

```python
import geopandas as gpd
import FancyFolium as ff

gdf = gpd.read_file("data/san_jose_pilot_region.gpkg")
```

### 2. Create the map and pick a background

```python
m = ff.create_map()
m = ff.background_layer("google hybrid", m=m)
```

### 3. Add one raster layer

A raster layer is a picture placed on the map at the right location.
{func}`~FancyFolium.vector_to_raster` turns the `height` column into a
small coloured image file; {func}`~FancyFolium.raster_layer` places it on
the map. If you already have an image file (`.tif`, `.png`, ...), skip
straight to `raster_layer(...)`.

```python
raster_path = ff.vector_to_raster(
    gdf,
    "output/height.tif",
    column="height",
    cmap="Reds",
    resolution=3.0,
)

m = ff.raster_layer(
    str(raster_path),
    layer_name="height (raster)",
    opacity=0.8,
    m=m,
)
```

### 4. Add one polygon layer, with a black outline

`style={"stroke_color": "#000000"}` gives every polygon a black outline so
building edges stay visible against any background.

```python
m = ff.vector_layer(
    gdf,
    layer_name="buildings (polygons)",
    column="height",
    cmap="Reds",
    vmin=0, vmax=10,
    style={"stroke_color": "#000000"},
    popup=["height", "n_storeys", "year"],
    m=m,
)
```

### 5. Add one marker layer

Markers need point geometries, so building footprints (polygons) are first
reduced to their centre point (centroid):

```python
points = gdf.copy()
points["geometry"] = points.to_crs(3857).geometry.centroid.to_crs(4326)

m = ff.marker_layer(
    points,
    layer_name="buildings (markers)",
    column="height",
    cmap="Reds",
    popup=["height", "n_storeys", "year"],
    overlay=True,
    active=False,
    m=m,
)
```

### 6. View and save

```python
m   # shows the interactive map inline in a notebook

ff.export(m, "output/example_map.html", raster_path="rasters")
```

`export()` writes a single `.html` file that opens in any web browser, no
Python needed - see {func}`~FancyFolium.export`.

## Result

This is the actual map produced by the code above - drag, zoom, and try the
control panel (top-right) and statistics panel (bottom-left, 📊) directly:

```{raw} html
<iframe src="_static/example/index.html" title="FancyFolium example map"
        style="width: 100%; height: 600px; border: 1px solid var(--color-background-border, #ccc); border-radius: 4px;"
        loading="lazy"></iframe>
```

## Next steps

- {doc}`getting-started` for the control panel and statistics panel tour.
- The {doc}`API reference <api/map>` for every function's full parameter list.
