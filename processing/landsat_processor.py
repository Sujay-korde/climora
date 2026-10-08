"""Landsat Collection 2 Level-2 Processing & Derived Products Engine.

Executes:
1. Canonical AOI clipping for all 9 required bands at native 30m resolution.
2. Official USGS Collection 2 Level-2 reflectance and temperature scaling.
3. Deterministic QA_PIXEL and QA_RADSAT masking with machine-readable classification.
4. Physical index derivation (NDVI, NDBI, LST in Kelvin and Celsius).
5. Deflate-compressed GeoTIFF writing with spatial transform preservation.
6. Complete provenance tracking linking raw source assets to processed products.
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
    DERIVED_DIR,
    LANDSAT_REQUIRED_BANDS,
    LANDSAT_SR_OFFSET,
    LANDSAT_SR_SCALE,
    LANDSAT_ST_OFFSET,
    LANDSAT_ST_SCALE,
    LANDSAT_TEMPORAL_BASELINE,
    PROCESSED_DIR,
    PROCESSING_PHASE,
    PROCESSING_VERSION,
    PROJECT_ROOT,
    RAW_DIR,
    TIFF_FLOAT_PROFILE,
    TIFF_UINT8_PROFILE,
    TIFF_UINT16_PROFILE,
)
from processing.derived_indices import compute_lst, compute_ndbi, compute_ndvi
from processing.qa_masking import evaluate_landsat_quality_masks

logger = get_logger()


def write_geotiff(
    output_path: Path,
    data_2d: np.ndarray,
    transform: rasterio.Affine,
    crs: str,
    profile_template: Dict[str, Any],
) -> Path:
    """Write a 2D numpy array as an optimized GeoTIFF."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    height, width = data_2d.shape

    profile = profile_template.copy()
    profile.update({
        "height": height,
        "width": width,
        "count": 1,
        "crs": crs,
        "transform": transform,
    })

    # Atomic write to temporary file
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with rasterio.open(temp_path, "w", **profile) as dst:
        dst.write(data_2d, 1)

    if output_path.exists():
        output_path.unlink()
    temp_path.rename(output_path)
    return output_path


def process_single_landsat_scene(
    scene_spec: Dict[str, Any],
    aoi_geom_4326: Dict[str, Any],
    force: bool = False,
) -> Dict[str, Any]:
    """Process all 9 raw bands and generate derived products for a single Landsat scene.

    Args:
        scene_spec: Target scene specification dictionary from LANDSAT_TEMPORAL_BASELINE
        aoi_geom_4326: Canonical Pune AOI GeoJSON geometry (EPSG:4326)
        force: If True, reprocess even if products exist

    Returns:
        Structured audit dictionary with processed and derived file records
    """
    year = scene_spec["year"]
    scene_id = scene_spec["scene_id"]
    platform = scene_spec["platform"]
    sensor = scene_spec["sensor"]
    doy = scene_spec["doy"]
    date_str = scene_spec["date"]

    logger.info(f"Processing Landsat {year} ({scene_id}, {platform}, DOY {doy})...")

    raw_scene_dir = RAW_DIR / "landsat" / str(year) / scene_id
    processed_scene_dir = PROCESSED_DIR / "landsat" / str(year) / scene_id
    derived_scene_dir = DERIVED_DIR / "landsat" / str(year) / scene_id

    processed_scene_dir.mkdir(parents=True, exist_ok=True)
    derived_scene_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify all 9 raw band files exist
    raw_files: Dict[str, Path] = {}
    for band_name in LANDSAT_REQUIRED_BANDS:
        raw_path = raw_scene_dir / f"{band_name}.tif"
        if not raw_path.exists():
            raise FileNotFoundError(f"Missing raw Landsat band: {raw_path}")
        raw_files[band_name] = raw_path

    # 2. Read and clip QA bands first to establish common raster grid and quality mask
    with rasterio.open(raw_files["QA_PIXEL"]) as src_qp, rasterio.open(raw_files["QA_RADSAT"]) as src_qr:
        crs_str = str(src_qp.crs)
        geom_proj = transform_geom("EPSG:4326", src_qp.crs, aoi_geom_4326)

        # Clip QA rasters
        clipped_qp, transform = mask(src_qp, [geom_proj], crop=True, nodata=1)
        clipped_qr, _ = mask(src_qr, [geom_proj], crop=True, nodata=65535)

        qp_arr = clipped_qp[0]
        qr_arr = clipped_qr[0]

    # Evaluate QA masks
    qa_classification, is_valid_clear, qa_metrics = evaluate_landsat_quality_masks(qp_arr, qr_arr)

    # 3. Read and clip all Surface Reflectance bands & ST_B10
    raw_clipped_bands: Dict[str, np.ndarray] = {}
    scaled_bands: Dict[str, np.ndarray] = {}
    processed_assets: Dict[str, Any] = {}

    for band_name in LANDSAT_REQUIRED_BANDS:
        raw_path = raw_files[band_name]
        raw_sha = calculate_sha256(raw_path)
        raw_size = raw_path.stat().st_size

        if band_name == "QA_PIXEL":
            out_path = processed_scene_dir / "QA_PIXEL.tif"
            write_geotiff(out_path, qp_arr, transform, crs_str, TIFF_UINT16_PROFILE)
            out_sha = calculate_sha256(out_path)
            processed_assets[band_name] = {
                "asset_type": "quality_pixel",
                "local_path": str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "raw_source_asset": str(raw_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "raw_sha256": raw_sha,
                "processed_sha256": out_sha,
                "file_size_bytes": out_path.stat().st_size,
                "dimensions": list(qp_arr.shape),
                "resolution_m": [30.0, 30.0],
                "crs": crs_str,
                "dtype": "uint16",
                "nodata": 1,
            }
        elif band_name == "QA_RADSAT":
            out_path = processed_scene_dir / "QA_RADSAT.tif"
            write_geotiff(out_path, qr_arr, transform, crs_str, TIFF_UINT16_PROFILE)
            out_sha = calculate_sha256(out_path)
            processed_assets[band_name] = {
                "asset_type": "quality_radsat",
                "local_path": str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "raw_source_asset": str(raw_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "raw_sha256": raw_sha,
                "processed_sha256": out_sha,
                "file_size_bytes": out_path.stat().st_size,
                "dimensions": list(qr_arr.shape),
                "resolution_m": [30.0, 30.0],
                "crs": crs_str,
                "dtype": "uint16",
                "nodata": 65535,
            }
        elif band_name.startswith("SR_"):
            with rasterio.open(raw_path) as src:
                clipped, _ = mask(src, [geom_proj], crop=True, nodata=0)
                raw_clipped_bands[band_name] = clipped[0]

            raw_dn = raw_clipped_bands[band_name]
            # Convert to float32 surface reflectance: DN * 0.0000275 - 0.2
            # Mask fill pixels as NaN
            sr_float = np.full(raw_dn.shape, np.nan, dtype=np.float32)
            valid_dn = (raw_dn > 0) & (qp_arr != 1) & (qp_arr != 0)
            sr_float[valid_dn] = (raw_dn[valid_dn].astype(np.float32) * LANDSAT_SR_SCALE) + LANDSAT_SR_OFFSET
            scaled_bands[band_name] = sr_float

            out_path = processed_scene_dir / f"{band_name}.tif"
            write_geotiff(out_path, sr_float, transform, crs_str, TIFF_FLOAT_PROFILE)
            out_sha = calculate_sha256(out_path)

            valid_sr = sr_float[np.isfinite(sr_float)]
            processed_assets[band_name] = {
                "asset_type": "surface_reflectance",
                "band": band_name,
                "scale_factor": LANDSAT_SR_SCALE,
                "add_offset": LANDSAT_SR_OFFSET,
                "units": "unitless surface reflectance",
                "local_path": str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "raw_source_asset": str(raw_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "raw_sha256": raw_sha,
                "processed_sha256": out_sha,
                "file_size_bytes": out_path.stat().st_size,
                "dimensions": list(raw_dn.shape),
                "resolution_m": [30.0, 30.0],
                "crs": crs_str,
                "dtype": "float32",
                "nodata": "NaN",
                "valid_pixel_count": int(valid_sr.size),
                "min": float(np.nanmin(valid_sr)) if valid_sr.size > 0 else None,
                "max": float(np.nanmax(valid_sr)) if valid_sr.size > 0 else None,
                "mean": float(np.nanmean(valid_sr)) if valid_sr.size > 0 else None,
            }
        elif band_name == "ST_B10":
            with rasterio.open(raw_path) as src:
                clipped, _ = mask(src, [geom_proj], crop=True, nodata=0)
                raw_clipped_bands[band_name] = clipped[0]

            st_dn = raw_clipped_bands[band_name]
            st_kelvin = np.full(st_dn.shape, np.nan, dtype=np.float32)
            valid_dn = (st_dn > 0) & (qp_arr != 1) & (qp_arr != 0)
            st_kelvin[valid_dn] = (st_dn[valid_dn].astype(np.float32) * LANDSAT_ST_SCALE) + LANDSAT_ST_OFFSET
            scaled_bands[band_name] = st_kelvin

            out_path = processed_scene_dir / "ST_B10.tif"
            write_geotiff(out_path, st_kelvin, transform, crs_str, TIFF_FLOAT_PROFILE)
            out_sha = calculate_sha256(out_path)

            valid_st = st_kelvin[np.isfinite(st_kelvin)]
            processed_assets[band_name] = {
                "asset_type": "surface_temperature",
                "band": "ST_B10",
                "scale_factor": LANDSAT_ST_SCALE,
                "add_offset": LANDSAT_ST_OFFSET,
                "units": "Kelvin",
                "local_path": str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "raw_source_asset": str(raw_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "raw_sha256": raw_sha,
                "processed_sha256": out_sha,
                "file_size_bytes": out_path.stat().st_size,
                "dimensions": list(st_dn.shape),
                "resolution_m": [30.0, 30.0],
                "crs": crs_str,
                "dtype": "float32",
                "nodata": "NaN",
                "valid_pixel_count": int(valid_st.size),
                "min": float(np.nanmin(valid_st)) if valid_st.size > 0 else None,
                "max": float(np.nanmax(valid_st)) if valid_st.size > 0 else None,
                "mean": float(np.nanmean(valid_st)) if valid_st.size > 0 else None,
            }

    # 4. Save QA Classification Raster
    qa_mask_path = processed_scene_dir / "qa_mask.tif"
    write_geotiff(qa_mask_path, qa_classification, transform, crs_str, TIFF_UINT8_PROFILE)
    qa_mask_sha = calculate_sha256(qa_mask_path)
    processed_assets["qa_mask"] = {
        "asset_type": "deterministic_qa_classification",
        "local_path": str(qa_mask_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "processed_sha256": qa_mask_sha,
        "file_size_bytes": qa_mask_path.stat().st_size,
        "dimensions": list(qa_classification.shape),
        "resolution_m": [30.0, 30.0],
        "crs": crs_str,
        "dtype": "uint8",
        "nodata": 0,
        "metrics": qa_metrics,
    }

    # Save processed metadata
    proc_meta = {
        "dataset_category": "landsat",
        "year": year,
        "scene_id": scene_id,
        "platform": platform,
        "sensor": sensor,
        "collection": scene_spec["collection"],
        "processing_level": scene_spec["processing_level"],
        "date": date_str,
        "doy": doy,
        "canonical_target_doy": 105,
        "doy_offset": scene_spec["offset_days"],
        "path_row": scene_spec["path_row"],
        "processing_version": PROCESSING_VERSION,
        "phase": PROCESSING_PHASE,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "affine_transform": [round(v, 6) for v in transform[:6]],
        "crs": crs_str,
        "resolution_meters": [30.0, 30.0],
        "dimensions": list(qp_arr.shape),
        "aoi": "data/aoi/pune.geojson",
        "qa_summary": qa_metrics,
        "assets": processed_assets,
    }
    with open(processed_scene_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(proc_meta, f, indent=2)

    # 5. DERIVED PRODUCTS: NDVI, NDBI, LST (Kelvin & Celsius)
    derived_assets: Dict[str, Any] = {}

    # NDVI
    ndvi_arr, ndvi_metrics = compute_ndvi(
        scaled_bands["SR_B4"], scaled_bands["SR_B5"], is_valid_clear
    )
    ndvi_path = derived_scene_dir / "ndvi.tif"
    write_geotiff(ndvi_path, ndvi_arr, transform, crs_str, TIFF_FLOAT_PROFILE)
    ndvi_sha = calculate_sha256(ndvi_path)
    derived_assets["ndvi"] = {
        "index_name": "NDVI",
        "local_path": str(ndvi_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "sha256": ndvi_sha,
        "file_size_bytes": ndvi_path.stat().st_size,
        "dimensions": list(ndvi_arr.shape),
        "resolution_m": [30.0, 30.0],
        "crs": crs_str,
        "dtype": "float32",
        "nodata": "NaN",
        "metrics": ndvi_metrics,
        "lineage": [
            str(raw_files["SR_B4"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["SR_B5"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["QA_PIXEL"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["QA_RADSAT"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
        ],
    }

    # NDBI
    ndbi_arr, ndbi_metrics = compute_ndbi(
        scaled_bands["SR_B5"], scaled_bands["SR_B6"], is_valid_clear
    )
    ndbi_path = derived_scene_dir / "ndbi.tif"
    write_geotiff(ndbi_path, ndbi_arr, transform, crs_str, TIFF_FLOAT_PROFILE)
    ndbi_sha = calculate_sha256(ndbi_path)
    derived_assets["ndbi"] = {
        "index_name": "NDBI",
        "local_path": str(ndbi_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "sha256": ndbi_sha,
        "file_size_bytes": ndbi_path.stat().st_size,
        "dimensions": list(ndbi_arr.shape),
        "resolution_m": [30.0, 30.0],
        "crs": crs_str,
        "dtype": "float32",
        "nodata": "NaN",
        "metrics": ndbi_metrics,
        "lineage": [
            str(raw_files["SR_B5"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["SR_B6"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["QA_PIXEL"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["QA_RADSAT"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
        ],
    }

    # LST (Kelvin & Celsius)
    lst_k_arr, lst_c_arr, lst_metrics = compute_lst(raw_clipped_bands["ST_B10"], is_valid_clear)

    lst_k_path = derived_scene_dir / "lst_kelvin.tif"
    write_geotiff(lst_k_path, lst_k_arr, transform, crs_str, TIFF_FLOAT_PROFILE)
    lst_k_sha = calculate_sha256(lst_k_path)
    derived_assets["lst_kelvin"] = {
        "index_name": "LST_Kelvin",
        "local_path": str(lst_k_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "sha256": lst_k_sha,
        "file_size_bytes": lst_k_path.stat().st_size,
        "dimensions": list(lst_k_arr.shape),
        "resolution_m": [30.0, 30.0],
        "crs": crs_str,
        "dtype": "float32",
        "nodata": "NaN",
        "metrics": lst_metrics["kelvin"],
        "lineage": [
            str(raw_files["ST_B10"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["QA_PIXEL"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["QA_RADSAT"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
        ],
    }

    lst_c_path = derived_scene_dir / "lst_celsius.tif"
    write_geotiff(lst_c_path, lst_c_arr, transform, crs_str, TIFF_FLOAT_PROFILE)
    lst_c_sha = calculate_sha256(lst_c_path)
    derived_assets["lst_celsius"] = {
        "index_name": "LST_Celsius",
        "local_path": str(lst_c_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "sha256": lst_c_sha,
        "file_size_bytes": lst_c_path.stat().st_size,
        "dimensions": list(lst_c_arr.shape),
        "resolution_m": [30.0, 30.0],
        "crs": crs_str,
        "dtype": "float32",
        "nodata": "NaN",
        "metrics": lst_metrics["celsius"],
        "lineage": [
            str(raw_files["ST_B10"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["QA_PIXEL"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(raw_files["QA_RADSAT"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
        ],
    }

    # Save derived metadata
    der_meta = {
        "dataset_category": "landsat_derived_indices",
        "year": year,
        "scene_id": scene_id,
        "platform": platform,
        "sensor": sensor,
        "date": date_str,
        "doy": doy,
        "canonical_target_doy": 105,
        "doy_offset": scene_spec["offset_days"],
        "processing_version": PROCESSING_VERSION,
        "derived_at": datetime.now(timezone.utc).isoformat(),
        "indices": derived_assets,
    }
    with open(derived_scene_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(der_meta, f, indent=2)

    return {
        "year": year,
        "scene_id": scene_id,
        "platform": platform,
        "sensor": sensor,
        "date": date_str,
        "doy": doy,
        "offset_days": scene_spec["offset_days"],
        "processed_assets": processed_assets,
        "derived_assets": derived_assets,
        "qa_metrics": qa_metrics,
        "status": "VALID",
    }


def process_all_landsat_scenes() -> Dict[int, Dict[str, Any]]:
    """Process all 5 approved Landsat annual observations."""
    logger.info("Starting processing for all 5 Landsat temporal baseline scenes...")
    aoi_data = load_aoi(PROJECT_ROOT / "data" / "aoi" / "pune.geojson")
    aoi_geom_4326 = aoi_data["features"][0]["geometry"]

    results = {}
    for spec in LANDSAT_TEMPORAL_BASELINE:
        res = process_single_landsat_scene(spec, aoi_geom_4326)
        results[spec["year"]] = res

    return results
