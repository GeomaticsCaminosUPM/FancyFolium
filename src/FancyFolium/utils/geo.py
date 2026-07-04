"""
utils/geo.py
============
Geometry, bounds, and coordinate-system helpers for FancyFolium.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple

import numpy as np

if TYPE_CHECKING:
    import geopandas as gpd


# ═══════════════════════════════════════════════════════════════════════════
#  Bounds helpers
# ═══════════════════════════════════════════════════════════════════════════

def bounds_center(bounds: Sequence[float]) -> Tuple[float, float]:
    """Compute the centre point of a bounding box.

    Args:
        bounds: ``(minx, miny, maxx, maxy)`` in EPSG:4326.

    Returns:
        The ``(lat, lon)`` centre of the bounding box.
    """
    return ((bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2)


def gdf_bounds_wgs84(gdf: "gpd.GeoDataFrame") -> Tuple[float, float, float, float]:
    """Get the total bounds of a GeoDataFrame in EPSG:4326.

    Reprojects *gdf* to EPSG:4326 first if it carries a different CRS.

    Args:
        gdf: A GeoDataFrame with a valid ``crs`` (or ``None``, assumed
            already EPSG:4326).

    Returns:
        The total bounds as ``(minx, miny, maxx, maxy)``.
    """
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    return tuple(gdf.total_bounds)  # type: ignore[return-value]


def bounds_to_folium(bounds_4326: Sequence[float]) -> List[List[float]]:
    """Convert ``(minx, miny, maxx, maxy)`` bounds to Folium/Leaflet form.

    Args:
        bounds_4326: ``(minx, miny, maxx, maxy)`` in EPSG:4326.

    Returns:
        Bounds as ``[[south, west], [north, east]]``, the form expected by
        ``folium.raster_layers.ImageOverlay``.
    """
    return [[bounds_4326[1], bounds_4326[0]], [bounds_4326[3], bounds_4326[2]]]


def folium_bounds_to_tuple(folium_bounds: Sequence[Sequence[float]]) -> Tuple[float, float, float, float]:
    """Convert Folium/Leaflet bounds back to a ``(minx, miny, maxx, maxy)`` tuple.

    Args:
        folium_bounds: Bounds as ``[[south, west], [north, east]]``.

    Returns:
        Bounds as ``(minx, miny, maxx, maxy)``.
    """
    s, w = folium_bounds[0]
    n, e = folium_bounds[1]
    return (w, s, e, n)


def expand_bounds(
    bounds_4326: Tuple[float, float, float, float],
    *,
    factor: float = 0.05,
) -> Tuple[float, float, float, float]:
    """Expand a bounding box outward, useful for setting a sensible map view.

    Args:
        bounds_4326: ``(minx, miny, maxx, maxy)`` in EPSG:4326.
        factor: Fraction of each axis's span to pad on every side.

    Returns:
        The expanded bounds as ``(minx, miny, maxx, maxy)``.
    """
    minx, miny, maxx, maxy = bounds_4326
    dx = (maxx - minx) * factor
    dy = (maxy - miny) * factor
    return (minx - dx, miny - dy, maxx + dx, maxy + dy)


# ═══════════════════════════════════════════════════════════════════════════
#  CRS helpers (rasterio-optional)
# ═══════════════════════════════════════════════════════════════════════════

def raster_bounds_wgs84(raster_path: str) -> Optional[List[List[float]]]:
    """Read the bounding box of a geo-referenced raster file.

    Args:
        raster_path: Path to a raster file readable by rasterio.

    Returns:
        Bounds as ``[[south, west], [north, east]]`` in EPSG:4326, or
        ``None`` if the file carries no CRS (or cannot be read).
    """
    try:
        import rasterio
        from rasterio.warp import transform_bounds
        from rasterio.crs import CRS

        with rasterio.open(raster_path) as src:
            if not src.crs:
                return None
            b = transform_bounds(src.crs, CRS.from_epsg(4326), *src.bounds)
            return [[b[1], b[0]], [b[3], b[2]]]
    except Exception:
        return None


def clip_raster_to_bounds(
    raster_path: str,
    user_bounds: List[List[float]],
) -> Tuple[np.ndarray, List[List[float]]]:
    """Read only the window of a raster overlapping the given bounds.

    Args:
        raster_path: Path to a geo-referenced raster file.
        user_bounds: Bounds to clip to, as ``[[south, west], [north, east]]``
            in EPSG:4326.

    Returns:
        A tuple of:

        - An RGBA ``uint8`` numpy array of the clipped window.
        - The actual clipped bounds as ``[[south, west], [north, east]]``
          (may differ slightly from ``user_bounds`` due to pixel alignment).

    Raises:
        ImportError: If rasterio is not installed.
        ValueError: If the raster has no embedded CRS.
    """
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.crs import CRS
    from rasterio.windows import from_bounds as window_from_bounds

    s, w = user_bounds[0]
    n, e = user_bounds[1]

    with rasterio.open(raster_path) as src:
        if not src.crs:
            raise ValueError(
                f"Raster '{raster_path}' has no embedded CRS. "
                "Supply bounds= for a plain image, or use a geo-referenced file."
            )

        crs_4326 = CRS.from_epsg(4326)
        native_bounds = transform_bounds(crs_4326, src.crs, w, s, e, n)
        win = window_from_bounds(*native_bounds, transform=src.transform)
        win = win.intersection(
            rasterio.windows.Window(0, 0, src.width, src.height)
        )

        data = src.read(window=win)
        win_transform = src.window_transform(win)

        rows, cols = data.shape[1], data.shape[2]
        actual_native = rasterio.transform.array_bounds(rows, cols, win_transform)
        actual_4326 = transform_bounds(src.crs, crs_4326, *actual_native)
        clip_bounds = [[actual_4326[1], actual_4326[0]], [actual_4326[3], actual_4326[2]]]

    if data.shape[0] >= 3:
        rgb = np.moveaxis(data[:3], 0, -1)
        alpha = data[3] if data.shape[0] >= 4 else np.full(rgb.shape[:2], 255, np.uint8)
    else:
        band = data[0]
        rgb = np.stack([band, band, band], axis=-1)
        alpha = np.full(band.shape, 255, np.uint8)

    if rgb.dtype != np.uint8:
        mn, mx = rgb.min(), rgb.max()
        if mx > mn:
            rgb = ((rgb - mn) / (mx - mn) * 255).astype(np.uint8)
        else:
            rgb = np.zeros_like(rgb, np.uint8)

    rgba = np.dstack([rgb, alpha.astype(np.uint8)])
    return rgba, clip_bounds
