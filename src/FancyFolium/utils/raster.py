"""
utils/raster.py
===============
Raster I/O and conversion helpers for FancyFolium.

Includes:
  - raster_to_png_base64     : geo-raster → data-URI + bounds
  - image_to_png_base64      : plain image → data-URI
  - vector_to_raster         : burn a GeoDataFrame to a raster file
"""

from __future__ import annotations

import io
import base64
import json
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

import numpy as np

from .color import CmapArg

if TYPE_CHECKING:
    import geopandas as gpd


# ═══════════════════════════════════════════════════════════════════════════
#  Raster → PNG helpers
# ═══════════════════════════════════════════════════════════════════════════

def _normalize_array_to_uint8(arr: np.ndarray) -> np.ndarray:
    """Rescale any numeric array to ``uint8`` in ``[0, 255]``.

    Args:
        arr: Array of any numeric dtype.

    Returns:
        The array rescaled (min-max) to ``uint8``. Already-``uint8`` arrays
        are returned unchanged; a constant array becomes all zeros.
    """
    if arr.dtype == np.uint8:
        return arr
    mn, mx = arr.min(), arr.max()
    if mx > mn:
        return ((arr - mn) / (mx - mn) * 255).astype(np.uint8)
    return np.zeros_like(arr, dtype=np.uint8)


def raster_to_png_base64(
    raster_path: str,
    bounds: Optional[List[List[float]]] = None,
) -> Tuple[str, List[List[float]]]:
    """Read a geo-referenced raster and encode it as a base64 PNG data-URI.

    Args:
        raster_path: Path to a raster file readable by rasterio.
        bounds: Optional ``[[south, west], [north, east]]`` in EPSG:4326 —
            if given, only the overlapping window is read (via
            :func:`FancyFolium.utils.geo.clip_raster_to_bounds`).

    Returns:
        A tuple of the ``"data:image/png;base64,..."`` data-URI and the
        raster's bounds as ``[[south, west], [north, east]]`` in EPSG:4326.

    Raises:
        ValueError: If the file has no CRS and no ``bounds`` were supplied.
    """
    from PIL import Image

    if bounds is not None:
        from .geo import clip_raster_to_bounds
        rgba, clip_bounds = clip_raster_to_bounds(raster_path, bounds)
        img_pil = Image.fromarray(rgba, mode="RGBA")
        img_bounds = clip_bounds
    else:
        import rasterio
        from rasterio.warp import transform_bounds
        from rasterio.crs import CRS

        with rasterio.open(raster_path) as src:
            if not src.crs:
                raise ValueError(
                    f"'{raster_path}' has no CRS. "
                    "Pass bounds=[[S,W],[N,E]] to raster_layer() for plain images."
                )
            b = transform_bounds(src.crs, CRS.from_epsg(4326), *src.bounds)
            img_bounds = [[b[1], b[0]], [b[3], b[2]]]
            arr = src.read()

        if arr.shape[0] >= 3:
            rgb   = np.moveaxis(arr[:3], 0, -1)
            alpha = arr[3] if arr.shape[0] >= 4 else np.full(rgb.shape[:2], 255, np.uint8)
        else:
            band  = arr[0]
            rgb   = np.stack([band, band, band], axis=-1)
            alpha = np.full(band.shape, 255, np.uint8)

        rgb = _normalize_array_to_uint8(rgb)
        img_pil = Image.fromarray(np.dstack([rgb, alpha.astype(np.uint8)]), mode="RGBA")

    buf = io.BytesIO()
    img_pil.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}", img_bounds


def image_to_png_base64(image_path: str) -> str:
    """Convert any PIL-readable image to a base64-encoded PNG data-URI.

    CRS/bounds are not inferred here — pass ``bounds=`` to
    :func:`FancyFolium.raster_layer` for plain (non-geo-referenced) images.

    Args:
        image_path: Path to any image file Pillow can open.

    Returns:
        The image re-encoded as a ``"data:image/png;base64,..."`` data-URI.
    """
    from PIL import Image

    img = Image.open(image_path).convert("RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ═══════════════════════════════════════════════════════════════════════════
#  vector_to_raster
# ═══════════════════════════════════════════════════════════════════════════

def vector_to_raster(
    gdf: "gpd.GeoDataFrame",
    output_path: str,
    *,
    resolution: float = 100.0,
    column: Optional[str] = None,
    color: str = "#1f77b4",
    cmap: CmapArg = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    categorical: bool = False,
    count: bool = False,
    opacity: float = 1.0,
    fmt: str = "GTiff",
    bounds: Optional[List[List[float]]] = None,
) -> Path:
    """Burn a GeoDataFrame to a raster file (always with a transparent background).

    The output is always RGBA. For formats that don't support geo-metadata
    (PNG, JPEG) a ``<stem>.meta.json`` sidecar file is written alongside it
    with the CRS and bounds, so the data can be re-read correctly.

    Args:
        gdf: Source GeoDataFrame. Reprojected to EPSG:4326 automatically if
            it carries a different CRS.
        output_path: Destination raster file path.
        resolution: Approximate pixel size, in metres at the equator.
        column: Column to colour features by. Uniform ``color`` is used if
            omitted.
        color: Uniform fill colour used when ``column`` is ``None``, or as
            a fallback for rows with no computed colour.
        cmap: Colour map argument — see :func:`FancyFolium.vector_layer`.
        vmin: Lower colour-scale bound for numeric ``column`` values.
        vmax: Upper colour-scale bound for numeric ``column`` values.
        categorical: Treat ``column`` as categorical rather than continuous
            numeric. Mutually exclusive with ``count``.
        count: Treat ``column`` as a "counts" column (integer-only; see
            :func:`FancyFolium.validate_count_column`), with ``vmin``/
            ``vmax`` defaulting to ``0``/``column.max()``. Mutually
            exclusive with ``categorical``.
        opacity: Fill opacity applied to every feature, in ``[0, 1]``.
        fmt: rasterio driver name (``"GTiff"`` or ``"PNG"``).
        bounds: Explicit ``[[south, west], [north, east]]`` bounds in
            EPSG:4326; defaults to the GeoDataFrame's own bounding box.

    Returns:
        Path to the written raster file.

    Raises:
        ImportError: If rasterio is not installed.
        ValueError: If ``categorical`` and ``count`` are both ``True``, or
            ``column`` is not a column of *gdf*.
        TypeError: If ``count=True`` and ``column`` isn't a valid counts
            column (see :func:`FancyFolium.validate_count_column`).
    """
    if categorical and count:
        raise ValueError("vector_to_raster: 'categorical' and 'count' are mutually exclusive.")
    try:
        import rasterio
        from rasterio.transform import from_bounds as transform_from_bounds
        from rasterio.crs import CRS
        from rasterio.features import rasterize
    except ImportError as e:
        raise ImportError(
            "rasterio is required for vector_to_raster(). "
            "Install it with: pip install rasterio"
        ) from e

    from .color import compute_feature_colors, validate_count_column

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    gdf = gdf.copy()
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    elif not gdf.crs:
        warnings.warn(
            "GeoDataFrame has no CRS; assuming EPSG:4326.",
            UserWarning, stacklevel=2,
        )

    if bounds is not None:
        s, w = bounds[0]
        n, e = bounds[1]
    else:
        minx, miny, maxx, maxy = gdf.total_bounds
        w, s, e, n = minx, miny, maxx, maxy

    lat_mid = (s + n) / 2
    deg_per_m_lat = 1 / 111_320
    deg_per_m_lon = 1 / (111_320 * abs(np.cos(np.radians(lat_mid))) + 1e-9)
    px_lat = resolution * deg_per_m_lat
    px_lon = resolution * deg_per_m_lon

    width  = max(1, int(round((e - w) / px_lon)))
    height = max(1, int(round((n - s) / px_lat)))
    transform = transform_from_bounds(w, s, e, n, width, height)

    if column is not None and column not in gdf.columns:
        raise ValueError(
            f"Column '{column}' not found in GeoDataFrame. "
            f"Available columns: {list(gdf.columns)}"
        )

    if count and column is not None:
        validate_count_column(gdf[column], column)

    if column is not None:
        color_map = compute_feature_colors(
            gdf[column],
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            categorical=categorical,
            count=count,
        )
    else:
        color_map = {idx: color for idx in gdf.index}

    def _hex_to_rgba(h: str, alpha: int = 255) -> Tuple[int, int, int, int]:
        """Convert a ``"#rrggbb"`` hex string to an ``(r, g, b, alpha)`` tuple."""
        h = h.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return r, g, b, alpha

    alpha_val = int(opacity * 255)

    shapes = [
        (geom, i + 1)
        for i, (idx, geom) in enumerate(zip(gdf.index, gdf.geometry))
        if geom is not None and not geom.is_empty
    ]
    id_array = rasterize(
        shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype=np.uint32,
    )

    out_r = np.zeros((height, width), dtype=np.uint8)
    out_g = np.zeros((height, width), dtype=np.uint8)
    out_b = np.zeros((height, width), dtype=np.uint8)
    out_a = np.zeros((height, width), dtype=np.uint8)

    valid_indices = list(gdf.index)
    for i, idx in enumerate(valid_indices):
        mask = id_array == (i + 1)
        if not mask.any():
            continue
        hex_color = color_map.get(idx, color)
        r, g, b, a = _hex_to_rgba(hex_color, alpha_val)
        out_r[mask] = r
        out_g[mask] = g
        out_b[mask] = b
        out_a[mask] = a

    rgba_stack = np.stack([out_r, out_g, out_b, out_a])

    crs_4326 = CRS.from_epsg(4326)

    if fmt.lower() == "gtiff" or out_path.suffix.lower() in (".tif", ".tiff"):
        with rasterio.open(
            out_path, "w",
            driver="GTiff",
            height=height, width=width,
            count=4, dtype=np.uint8,
            crs=crs_4326, transform=transform,
        ) as dst:
            dst.write(rgba_stack)
        print(f"✓ Raster saved → {out_path}  ({width}×{height} px, GTiff/RGBA)")
    else:
        with rasterio.open(
            out_path, "w",
            driver=fmt.upper() if fmt.upper() != "PNG" else "PNG",
            height=height, width=width,
            count=4, dtype=np.uint8,
        ) as dst:
            dst.write(rgba_stack)

        meta = {
            "crs": "EPSG:4326",
            "bounds_wgs84": {"west": w, "south": s, "east": e, "north": n},
            "width_px": width,
            "height_px": height,
            "resolution_m": resolution,
        }
        meta_path = out_path.with_suffix(".meta.json")
        meta_path.write_text(json.dumps(meta, indent=2))
        print(
            f"✓ Raster saved → {out_path}  ({width}×{height} px)\n"
            f"  Metadata    → {meta_path}"
        )

    return out_path
