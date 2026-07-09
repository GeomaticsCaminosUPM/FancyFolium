FancyFolium
===========

A composable `Folium <https://python-visualization.github.io/folium/>`_
mapping library with a fully-styled three-panel layer control, automatic
legends, named colourmaps, emoji/icon markers, a statistics panel with live
histograms, per-layer opacity sliders, and vector-to-raster conversion.

FancyFolium was written to make it fast to turn geospatial research data -
building-footprint surveys, raster models, damage/risk assessments - into
interactive maps that both technical and non-technical audiences can explore,
without hand-writing Leaflet/JavaScript for every project.

📦 `GitHub repository <https://github.com/GeomaticsCaminosUPM/FancyFolium>`_

By `Miguel Ureña Pliego <https://miguelurenapliego.github.io/>`_ -
`GitHub <https://github.com/MiguelUrenaPliego>`_ ·
`ORCID <https://orcid.org/0000-0001-6594-2566>`_ ·
`LinkedIn <https://www.linkedin.com/in/miguel-urena-pliego>`_ -
`Advanced Geomatics Research Group (AGA) <https://blogs.upm.es/aga/en/>`_,
Universidad Politécnica de Madrid. See :doc:`author` for more.

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

See :doc:`getting-started` for the control-panel/statistics-panel tour,
:doc:`examples` for a longer step-by-step walkthrough (also runnable in
Google Colab), or jump straight to the API reference for every function's
parameters.

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   getting-started

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples

.. toctree::
   :maxdepth: 2
   :caption: API reference

   api/map
   api/background
   api/raster
   api/vector
   api/marker
   api/color
   api/geo
   api/raster_utils

.. toctree::
   :maxdepth: 1
   :caption: Author

   author

Indices
=======

* :ref:`genindex`
