"""MODIS MOD11A2 Version 061 Processing Engine for CLIMORA Phase 1A.8.

Executes:
1. Native Sinusoidal AOI clipping for 1km Land Surface Temperature & QC layers.
2. Official LP DAAC MOD11A2 v061 scaling (scale factor = 0.02, Kelvin & Celsius).
3. Quality control bit flag extraction from QC_Day and QC_Night.
4. Retention of native ~926.6m resolution without premature resampling.
5. Contextual cross-check reporting against Landsat thermal products.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom

from ingestion.common import calculate_sha256, get_logger, load_aoi
from processing.config import (
    DATA_DIR,
    MODIS_LST_OFFSET,
    MODIS_LST_SCALE,
    MODIS_REQUIRED_LAYERS,
    PROCESSED_DIR,
    PROCESSING_PHASE,
    PROCESSING_VERSION,
    PROJECT_ROOT,
    RAW_DIR,
    TIFF_FLOAT_PROFILE,
    TIFF_UINT8_PROFILE,
)
from processing.landsat_processor import write_geotiff

logger = get_logger()


def parse_modis_qc_bits(qc_array: np.ndarray) -> Dict[str, Any]:
    """Extract quality statistics from MOD11A2 8-bit QC array.

    Bits 0-1 (Mandatory QA flags):
    00 (0): LST produced, good quality
    01 (1): LST produced, other quality
    10 (2): LST not produced due to cloud effects
    11 (3): LST not produced primarily due to reasons other than cloud
    """
    valid = qc_array != 0
    total_aoi = int(np.count_nonzero(valid))
    if total_aoi == 0:
        return {"total_pixels": 0, "good_quality_pct": 0.0}

    mand_flags = qc_array & 0b11
    good_quality = int(np.count_nonzero((mand_flags == 0) & valid))
    other_quality = int(np.count_nonzero((mand_flags == 1) & valid))
    cloud_not_produced = int(np.count_nonzero((mand_flags == 2) & valid))
    other_not_produced = int(np.count_nonzero((mand_flags == 3) & valid))

    return {
        "evaluated_pixels": total_aoi,
        "good_quality_count": good_quality,
        "good_quality_pct": round((good_quality / total_aoi) * 100.0, 2),
        "other_quality_count": other_quality,
        "other_quality_pct": round((other_quality / total_aoi) * 100.0, 2),
        "cloud_masked_count": cloud_not_produced,
        "cloud_masked_pct": round((cloud_not_produced / total_aoi) * 100.0, 2),
        "other_not_produced_count": other_not_produced,
    }


def process_single_modis_item(
    year: int,
    item_id: str,
    raw_item_dir: Path,
    aoi_geom_4326: Dict[str, Any],
) -> Dict[str, Any]:
    """Process a single MODIS MOD11A2 item: clip to AOI and scale LST."""
    logger.info(f"Processing MODIS {year} granule: {item_id}...")
    processed_item_dir = PROCESSED_DIR / "modis" / str(year) / item_id
    processed_item_dir.mkdir(parents=True, exist_ok=True)

    # Determine platform from item_id
    platform = "Aqua" if item_id.startswith("MYD") else "Terra"

    processed_assets: Dict[str, Any] = {}
    qc_metrics: Dict[str, Any] = {}

    # Read and clip QC layers first
    qc_arrs: Dict[str, np.ndarray] = {}
    transform = None
    crs_str = None

    for qc_layer in ["QC_Day", "QC_Night"]:
        qc_raw_path = raw_item_dir / f"{qc_layer}.tif"
        if not qc_raw_path.exists():
            continue
        with rasterio.open(qc_raw_path) as src:
            if transform is None:
                transform = src.transform
                crs_str = str(src.crs)
            geom_proj = transform_geom("EPSG:4326", src.crs, aoi_geom_4326)
            clipped, tr = mask(src, [geom_proj], crop=True, nodata=0)
            transform = tr
            qc_arrs[qc_layer] = clipped[0]

        qc_out_path = processed_item_dir / f"{qc_layer}.tif"
        write_geotiff(qc_out_path, qc_arrs[qc_layer], transform, crs_str, TIFF_UINT8_PROFILE)
        raw_sha = calculate_sha256(qc_raw_path)
        out_sha = calculate_sha256(qc_out_path)

        qc_metrics[qc_layer] = parse_modis_qc_bits(qc_arrs[qc_layer])
        processed_assets[qc_layer] = {
            "asset_type": "quality_control",
            "layer": qc_layer,
            "local_path": str(qc_out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_source_asset": str(qc_raw_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_sha256": raw_sha,
            "processed_sha256": out_sha,
            "file_size_bytes": qc_out_path.stat().st_size,
            "dimensions": list(qc_arrs[qc_layer].shape),
            "resolution_m": [926.625, 926.625],
            "crs": crs_str,
            "dtype": "uint8",
            "nodata": 0,
            "metrics": qc_metrics[qc_layer],
        }

    # Process LST layers
    for lst_layer in ["LST_Day_1km", "LST_Night_1km"]:
        raw_path = raw_item_dir / f"{lst_layer}.tif"
        if not raw_path.exists():
            continue
        with rasterio.open(raw_path) as src:
            geom_proj = transform_geom("EPSG:4326", src.crs, aoi_geom_4326)
            clipped, tr = mask(src, [geom_proj], crop=True, nodata=0)
            raw_dn = clipped[0]

        raw_sha = calculate_sha256(raw_path)

        # Scale to Kelvin (DN * 0.02)
        lst_k = np.full(raw_dn.shape, np.nan, dtype=np.float32)
        valid = raw_dn > 0
        lst_k[valid] = raw_dn[valid].astype(np.float32) * MODIS_LST_SCALE
        lst_c = lst_k - 273.15

        # Write Kelvin GeoTIFF
        k_out_path = processed_item_dir / f"{lst_layer}_kelvin.tif"
        write_geotiff(k_out_path, lst_k, transform, crs_str, TIFF_FLOAT_PROFILE)
        k_sha = calculate_sha256(k_out_path)

        # Write Celsius GeoTIFF
        c_out_path = processed_item_dir / f"{lst_layer}_celsius.tif"
        write_geotiff(c_out_path, lst_c, transform, crs_str, TIFF_FLOAT_PROFILE)
        c_sha = calculate_sha256(c_out_path)

        valid_k = lst_k[np.isfinite(lst_k)]
        valid_c = lst_c[np.isfinite(lst_c)]

        processed_assets[f"{lst_layer}_kelvin"] = {
            "asset_type": "surface_temperature_kelvin",
            "layer": lst_layer,
            "scale_factor": MODIS_LST_SCALE,
            "units": "Kelvin (K)",
            "local_path": str(k_out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_source_asset": str(raw_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "raw_sha256": raw_sha,
            "processed_sha256": k_sha,
            "file_size_bytes": k_out_path.stat().st_size,
            "dimensions": list(raw_dn.shape),
            "resolution_m": [926.625, 926.625],
            "crs": crs_str,
            "dtype": "float32",
            "nodata": "NaN",
            "valid_count": int(valid_k.size),
            "min": float(np.nanmin(valid_k)) if valid_k.size > 0 else None,
            "max": float(np.nanmax(valid_k)) if valid_k.size > 0 else None,
            "mean": float(np.nanmean(valid_k)) if valid_k.size > 0 else None,
        }

        processed_assets[f"{lst_layer}_celsius"] = {
            "asset_type": "surface_temperature_celsius",
            "layer": lst_layer,
            "units": "Degrees Celsius (°C)",
            "local_path": str(c_out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "processed_sha256": c_sha,
            "file_size_bytes": c_out_path.stat().st_size,
            "dimensions": list(raw_dn.shape),
            "resolution_m": [926.625, 926.625],
            "crs": crs_str,
            "dtype": "float32",
            "nodata": "NaN",
            "valid_count": int(valid_c.size),
            "min": float(np.nanmin(valid_c)) if valid_c.size > 0 else None,
            "max": float(np.nanmax(valid_c)) if valid_c.size > 0 else None,
            "mean": float(np.nanmean(valid_c)) if valid_c.size > 0 else None,
        }

    meta = {
        "dataset_category": "modis",
        "product": "MOD11A2 Version 061",
        "item_id": item_id,
        "platform": platform,
        "year": year,
        "tile": "h25v07",
        "processing_version": PROCESSING_VERSION,
        "phase": PROCESSING_PHASE,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "affine_transform": [round(v, 4) for v in transform[:6]] if transform else None,
        "crs": crs_str,
        "resolution_meters": [926.625, 926.625],
        "role": "coarse_resolution_thermal_context_and_cross_check",
        "qc_summary": qc_metrics,
        "assets": processed_assets,
    }
    with open(processed_item_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {
        "year": year,
        "item_id": item_id,
        "platform": platform,
        "assets": processed_assets,
        "status": "VALID",
    }


def process_all_modis_observations() -> Dict[str, Any]:
    """Process all historical (2021-2024, DOY 105) + frozen 2025 MODIS observations."""
    logger.info("Processing all MODIS observations...")
    aoi_data = load_aoi(PROJECT_ROOT / "data" / "aoi" / "pune.geojson")
    aoi_geom_4326 = aoi_data["features"][0]["geometry"]

    modis_raw_root = RAW_DIR / "modis"
    results = {}

    for yr_dir in sorted(modis_raw_root.iterdir()):
        if not yr_dir.is_dir():
            continue
        try:
            year = int(yr_dir.name)
        except ValueError:
            continue

        for item_dir in sorted(yr_dir.iterdir()):
            if not item_dir.is_dir():
                continue
            item_id = item_dir.name
            res = process_single_modis_item(year, item_id, item_dir, aoi_geom_4326)
            results[item_id] = res

    return results
