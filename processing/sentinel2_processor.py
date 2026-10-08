"""Sentinel-2 2025 Current-State High-Resolution Processing Contract for CLIMORA.

Governance Constraints (Section 12):
- Frozen 2025 Sentinel-2 data is strictly maintained as "2025 CURRENT-STATE HIGH-RESOLUTION DATA".
- Sentinel-2 is NOT merged into the 2021-2025 historical Landsat baseline.
- No fake 5-year Sentinel temporal series is constructed.
- No unsupported cross-sensor normalization or empirical scaling is applied.
- Native 10m and 20m spatial resolutions are strictly preserved after AOI clipping.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom

from ingestion.common import calculate_sha256, get_logger, load_aoi
from processing.config import (
    PROCESSED_DIR,
    PROCESSING_PHASE,
    PROCESSING_VERSION,
    PROJECT_ROOT,
    RAW_DIR,
    TIFF_FLOAT_PROFILE,
    TIFF_UINT8_PROFILE,
    TIFF_UINT16_PROFILE,
)
from processing.landsat_processor import write_geotiff

logger = get_logger()

SENTINEL2_SCALE_FACTOR = 0.0001  # Copernicus BOA surface reflectance scale factor (1/10000)

S2_10M_BANDS = ["B02", "B03", "B04", "B08"]
S2_20M_BANDS = ["B05", "B06", "B07", "B11", "B12", "B8A"]


def process_sentinel2_current_state() -> Dict[str, Any]:
    """Process the frozen 2025 Sentinel-2 high-resolution observation under its explicit contract."""
    logger.info("Processing Sentinel-2 2025 current-state high-resolution reference data...")
    aoi_data = load_aoi(PROJECT_ROOT / "data" / "aoi" / "pune.geojson")
    aoi_geom_4326 = aoi_data["features"][0]["geometry"]

    raw_s2_base = RAW_DIR / "sentinel2" / "2025"
    item_dirs = [d for d in raw_s2_base.iterdir() if d.is_dir()]
    if not item_dirs:
        raise FileNotFoundError(f"No Sentinel-2 directories found in {raw_s2_base}")

    raw_item_dir = item_dirs[0]
    item_id = raw_item_dir.name

    out_dir = PROCESSED_DIR / "sentinel2" / "2025" / item_id
    out_dir.mkdir(parents=True, exist_ok=True)

    processed_assets: Dict[str, Any] = {}

    # Process 10m bands
    for band_name in S2_10M_BANDS:
        raw_band_path = raw_item_dir / f"{band_name}.tif"
        if not raw_band_path.exists():
            continue
        with rasterio.open(raw_band_path) as src:
            geom_proj = transform_geom("EPSG:4326", src.crs, aoi_geom_4326)
            clipped, tr = mask(src, [geom_proj], crop=True, nodata=0)
            raw_dn = clipped[0]
            crs_str = str(src.crs)

        raw_sha = calculate_sha256(raw_band_path)

        # Scale reflectance to float32 (DN * 0.0001)
        scaled_ref = np.full(raw_dn.shape, np.nan, dtype=np.float32)
        valid = raw_dn > 0
        scaled_ref[valid] = raw_dn[valid].astype(np.float32) * SENTINEL2_SCALE_FACTOR

        out_path = out_dir / f"{band_name}.tif"
        write_geotiff(out_path, scaled_ref, tr, crs_str, TIFF_FLOAT_PROFILE)
        out_sha = calculate_sha256(out_path)

        valid_vals = scaled_ref[np.isfinite(scaled_ref)]
        processed_assets[band_name] = {
            "band": band_name,
            "resolution_meters": [10.0, 10.0],
            "scale_factor": SENTINEL2_SCALE_FACTOR,
            "units": "surface_reflectance",
            "local_path": str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_source_asset": str(raw_band_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_sha256": raw_sha,
            "processed_sha256": out_sha,
            "file_size_bytes": out_path.stat().st_size,
            "dimensions": list(raw_dn.shape),
            "crs": crs_str,
            "dtype": "float32",
            "valid_count": int(valid_vals.size),
            "min": float(np.nanmin(valid_vals)) if valid_vals.size > 0 else None,
            "max": float(np.nanmax(valid_vals)) if valid_vals.size > 0 else None,
            "mean": float(np.nanmean(valid_vals)) if valid_vals.size > 0 else None,
        }

    # Process 20m bands
    for band_name in S2_20M_BANDS:
        raw_band_path = raw_item_dir / f"{band_name}.tif"
        if not raw_band_path.exists():
            continue
        with rasterio.open(raw_band_path) as src:
            geom_proj = transform_geom("EPSG:4326", src.crs, aoi_geom_4326)
            clipped, tr = mask(src, [geom_proj], crop=True, nodata=0)
            raw_dn = clipped[0]
            crs_str = str(src.crs)

        raw_sha = calculate_sha256(raw_band_path)

        scaled_ref = np.full(raw_dn.shape, np.nan, dtype=np.float32)
        valid = raw_dn > 0
        scaled_ref[valid] = raw_dn[valid].astype(np.float32) * SENTINEL2_SCALE_FACTOR

        out_path = out_dir / f"{band_name}.tif"
        write_geotiff(out_path, scaled_ref, tr, crs_str, TIFF_FLOAT_PROFILE)
        out_sha = calculate_sha256(out_path)

        valid_vals = scaled_ref[np.isfinite(scaled_ref)]
        processed_assets[band_name] = {
            "band": band_name,
            "resolution_meters": [20.0, 20.0],
            "scale_factor": SENTINEL2_SCALE_FACTOR,
            "units": "surface_reflectance",
            "local_path": str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_source_asset": str(raw_band_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_sha256": raw_sha,
            "processed_sha256": out_sha,
            "file_size_bytes": out_path.stat().st_size,
            "dimensions": list(raw_dn.shape),
            "crs": crs_str,
            "dtype": "float32",
            "valid_count": int(valid_vals.size),
            "min": float(np.nanmin(valid_vals)) if valid_vals.size > 0 else None,
            "max": float(np.nanmax(valid_vals)) if valid_vals.size > 0 else None,
            "mean": float(np.nanmean(valid_vals)) if valid_vals.size > 0 else None,
        }

    # Process SCL (Scene Classification Layer - 20m uint8)
    scl_path = raw_item_dir / "SCL.tif"
    if scl_path.exists():
        with rasterio.open(scl_path) as src:
            geom_proj = transform_geom("EPSG:4326", src.crs, aoi_geom_4326)
            clipped, tr = mask(src, [geom_proj], crop=True, nodata=0)
            scl_arr = clipped[0]
            crs_str = str(src.crs)

        raw_sha = calculate_sha256(scl_path)
        out_path = out_dir / "SCL.tif"
        write_geotiff(out_path, scl_arr, tr, crs_str, TIFF_UINT8_PROFILE)
        out_sha = calculate_sha256(out_path)

        processed_assets["SCL"] = {
            "band": "SCL",
            "description": "Scene Classification Layer (Copernicus 11-class classification)",
            "resolution_meters": [20.0, 20.0],
            "local_path": str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_source_asset": str(scl_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_sha256": raw_sha,
            "processed_sha256": out_sha,
            "file_size_bytes": out_path.stat().st_size,
            "dimensions": list(scl_arr.shape),
            "crs": crs_str,
            "dtype": "uint8",
            "nodata": 0,
        }

    meta = {
        "dataset_category": "sentinel2_current_state",
        "role": "2025 CURRENT-STATE HIGH-RESOLUTION REFERENCE DATA",
        "item_id": item_id,
        "platform": "Sentinel-2A",
        "instrument": "MSI",
        "processing_level": "Level-2A (BOA Surface Reflectance)",
        "observation_date": "2025-01-18",
        "governance_rule": "Excluded from 2021-2025 historical Landsat baseline. Used solely for high-resolution morphology & cross-sensor spatial reference.",
        "native_resolutions": ["10m", "20m"],
        "crs": "EPSG:32643",
        "processing_version": PROCESSING_VERSION,
        "phase": PROCESSING_PHASE,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "assets": processed_assets,
    }

    with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info("Sentinel-2 current-state processing contract established.")
    return meta
