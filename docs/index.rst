FancyFolium
===========

A composable `Folium <https://python-visualization.github.io/folium/>`_
mapping library with a fully-styled three-panel layer control, automatic
legends, named colourmaps, emoji/icon markers, a statistics panel with live
histograms, per-layer opacity sliders, and vector-to-raster conversion.

.. code-block:: python

   import geopandas as gpd
   import FancyFolium as ff

   gdf = gpd.read_file("buildings.gpkg")

   m = ff.create_map()
   m = ff.background_layer("google hybrid", m=m)
   m = ff.vector_layer(
       gdf, column="height", cmap="Reds", vmin=0, vmax=50,
       overlay=True, popup=["height", "n_storeys"], legend_unit="m", m=m,
   )
   ff.export(m, "output/map.html")

See :doc:`getting-started` for the control-panel/statistics-panel tour, or
jump straight to the API reference below for every function's parameters.

The `example notebook
<https://github.com/MiguelUrenaPliego/FancyFolium/blob/main/examples/example.ipynb>`_
in the repository walks through every feature against real
building-footprint data.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   getting-started
   api/map
   api/background
   api/raster
   api/vector
   api/marker
   api/color
   api/geo
   api/raster_utils

Indices
=======

* :ref:`genindex`
* :ref:`modindex`
