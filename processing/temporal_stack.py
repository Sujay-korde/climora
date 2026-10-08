"""Temporal Normalization & 5-Year Temporal Stack Manifest Engine for CLIMORA.

Executes:
1. Generation of unified temporal stack manifest linking 2021-2025 observations.
2. Complete end-to-end lineage preservation:
   year -> scene_id -> platform/sensor -> raw_assets -> processed_assets -> derived_assets -> quality_metadata.
3. Common temporal metadata model across the five-year baseline.
4. Calculation of annual multi-temporal persistence and thermal baseline statistics.
5. Strict adherence to Section 15 scientific caveats:
   - Not a statistically established long-term climate trend
   - Zero warming attribution
   - No causal climate change inference from five annual observations
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import rasterio

from ingestion.common import calculate_sha256, get_logger
from processing.config import (
    CANONICAL_TARGET_DOY,
    DATA_DIR,
    DERIVED_DIR,
    HARD_MAX_OFFSET_DAYS,
    LANDSAT_TEMPORAL_BASELINE,
    PREFERRED_WINDOW,
    PROCESSED_DIR,
    PROCESSING_PHASE,
    PROCESSING_VERSION,
    PROJECT_ROOT,
    RAW_DIR,
)

logger = get_logger()


def build_temporal_stack_manifest(
    landsat_results: Dict[int, Dict[str, Any]],
    nasa_power_summary: Dict[str, Any],
    modis_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Construct machine-readable 5-year temporal stack manifest preserving complete lineage."""
    logger.info("Building 5-year temporal stack manifest...")
    temporal_proc_dir = PROCESSED_DIR / "temporal"
    temporal_der_dir = DERIVED_DIR / "temporal"
    temporal_proc_dir.mkdir(parents=True, exist_ok=True)
    temporal_der_dir.mkdir(parents=True, exist_ok=True)

    annual_stack: Dict[str, Any] = {}

    for spec in LANDSAT_TEMPORAL_BASELINE:
        year = spec["year"]
        scene_id = spec["scene_id"]
        l_res = landsat_results.get(year, {})

        # NASA POWER target window stats for this year
        np_year_info = nasa_power_summary.get("annual_summaries", {}).get(year, {})
        np_window_stats = np_year_info.get("target_window_doy_95_115_stats", {})

        # MODIS matching DOY 105 observation for this year
        modis_items_for_year = [
            item_id for item_id, m in modis_results.items()
            if m.get("year") == year and "105" in item_id
        ]
        matching_modis_id = modis_items_for_year[0] if modis_items_for_year else None

        annual_stack[str(year)] = {
            "year": year,
            "temporal_metadata": {
                "date": spec["date"],
                "doy": spec["doy"],
                "canonical_target_doy": CANONICAL_TARGET_DOY,
                "doy_offset": spec["offset_days"],
                "season": "peak_pre_monsoon_summer",
                "within_preferred_window": PREFERRED_WINDOW[0] <= spec["doy"] <= PREFERRED_WINDOW[1],
                "within_hard_max_offset": spec["offset_days"] <= HARD_MAX_OFFSET_DAYS,
            },
            "sensor_governance": {
                "platform": spec["platform"],
                "sensor": spec["sensor"],
                "collection": spec["collection"],
                "processing_level": spec["processing_level"],
                "path_row": spec["path_row"],
                "scene_id": scene_id,
                "is_landsat_9": spec["platform"] == "Landsat 9",
            },
            "quality_metrics": l_res.get("qa_metrics", {}),
            "lineage": {
                "raw_directory": f"data/raw/landsat/{year}/{scene_id}",
                "processed_directory": f"data/processed/landsat/{year}/{scene_id}",
                "derived_directory": f"data/derived/landsat/{year}/{scene_id}",
                "processed_assets": l_res.get("processed_assets", {}),
                "derived_assets": l_res.get("derived_assets", {}),
            },
            "ancillary_context": {
                "nasa_power_target_window_meteorology": np_window_stats,
                "modis_context_item_id": matching_modis_id,
            },
        }

    manifest = {
        "manifest_id": "climora_temporal_stack_v1",
        "dataset_name": "CLIMORA Pune 5-Year Temporal Baseline Stack (2021-2025)",
        "processing_version": PROCESSING_VERSION,
        "phase": PROCESSING_PHASE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_target_doy": CANONICAL_TARGET_DOY,
        "preferred_window": list(PREFERRED_WINDOW),
        "hard_max_offset_days": HARD_MAX_OFFSET_DAYS,
        "sensor_governance": {
            "statement": (
                "Four Landsat 8 observations (2021, 2022, 2024, 2025) and one Landsat 9 observation "
                "in 2023. Explicit platform identity preserved across all layers. Zero unsupported "
                "cross-sensor calibration factors applied."
            ),
            "platforms": {
                "2021": "Landsat 8",
                "2022": "Landsat 8",
                "2023": "Landsat 9",
                "2024": "Landsat 8",
                "2025": "Landsat 8",
            },
        },
        "scientific_caveats": {
            "intended_analytic_uses": [
                "Baseline normalization",
                "Spatial persistence analysis",
                "Recurrence identification",
                "Annual comparative anomaly analysis (relative to 5-year mean)",
                "2025 current-state contextualization",
            ],
            "explicit_prohibitions": [
                "Do NOT describe these five annual pre-monsoon snapshots as a long-term climate trend.",
                "Do NOT infer warming attribution.",
                "Do NOT infer causal climate change from this dataset.",
            ],
        },
        "annual_observations": annual_stack,
    }

    manifest_file = temporal_proc_dir / "pune_temporal_stack_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Compute multi-temporal summary across 5 years
    temporal_summary = compute_temporal_summary_metrics(landsat_results)
    summary_file = temporal_der_dir / "pune_temporal_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(temporal_summary, f, indent=2)

    logger.info("Temporal stack manifest & multi-temporal summary generated.")
    return manifest


def compute_temporal_summary_metrics(
    landsat_results: Dict[int, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute 5-year mean, min, max, and valid pixel counts for NDVI, NDBI, and LST."""
    years = sorted(landsat_results.keys())

    # Load 2D derived arrays for all years
    ndvi_stack: List[np.ndarray] = []
    ndbi_stack: List[np.ndarray] = []
    lst_k_stack: List[np.ndarray] = []
    lst_c_stack: List[np.ndarray] = []

    transform = None
    crs = None

    for yr in years:
        sc_id = landsat_results[yr]["scene_id"]
        der_dir = DERIVED_DIR / "landsat" / str(yr) / sc_id

        with rasterio.open(der_dir / "ndvi.tif") as src:
            if transform is None:
                transform = src.transform
                crs = str(src.crs)
            ndvi_stack.append(src.read(1))

        with rasterio.open(der_dir / "ndbi.tif") as src:
            ndbi_stack.append(src.read(1))

        with rasterio.open(der_dir / "lst_kelvin.tif") as src:
            lst_k_stack.append(src.read(1))

        with rasterio.open(der_dir / "lst_celsius.tif") as src:
            lst_c_stack.append(src.read(1))

    ndvi_arr = np.array(ndvi_stack)      # (5, 706, 954)
    ndbi_arr = np.array(ndbi_stack)      # (5, 706, 954)
    lst_k_arr = np.array(lst_k_stack)    # (5, 706, 954)
    lst_c_arr = np.array(lst_c_stack)    # (5, 706, 954)

    # Compute pixel-wise multi-year statistics (ignoring NaNs)
    with np.errstate(divide="ignore", invalid="ignore"):
        valid_counts = np.sum(np.isfinite(lst_c_arr), axis=0)
        mean_ndvi = np.nanmean(ndvi_arr, axis=0)
        mean_ndbi = np.nanmean(ndbi_arr, axis=0)
        mean_lst_c = np.nanmean(lst_c_arr, axis=0)

    # Overall AOI-wide summary metrics
    def _stats(arr_3d: np.ndarray, unit: str) -> Dict[str, Any]:
        all_vals = arr_3d[np.isfinite(arr_3d)]
        return {
            "unit": unit,
            "min": round(float(np.min(all_vals)), 3) if all_vals.size > 0 else None,
            "max": round(float(np.max(all_vals)), 3) if all_vals.size > 0 else None,
            "mean": round(float(np.mean(all_vals)), 3) if all_vals.size > 0 else None,
            "std": round(float(np.std(all_vals)), 3) if all_vals.size > 0 else None,
            "total_evaluated_pixels": int(all_vals.size),
        }

    annual_breakdown = {}
    for idx, yr in enumerate(years):
        sc_id = landsat_results[yr]["scene_id"]
        v_ndvi = ndvi_arr[idx][np.isfinite(ndvi_arr[idx])]
        v_ndbi = ndbi_arr[idx][np.isfinite(ndbi_arr[idx])]
        v_lst_c = lst_c_arr[idx][np.isfinite(lst_c_arr[idx])]
        annual_breakdown[yr] = {
            "year": yr,
            "scene_id": sc_id,
            "platform": landsat_results[yr]["platform"],
            "doy": landsat_results[yr]["doy"],
            "valid_pixels": int(v_lst_c.size),
            "ndvi_mean": round(float(np.mean(v_ndvi)), 3) if v_ndvi.size > 0 else None,
            "ndbi_mean": round(float(np.mean(v_ndbi)), 3) if v_ndbi.size > 0 else None,
            "lst_celsius_mean": round(float(np.mean(v_lst_c)), 2) if v_lst_c.size > 0 else None,
            "lst_celsius_min": round(float(np.min(v_lst_c)), 2) if v_lst_c.size > 0 else None,
            "lst_celsius_max": round(float(np.max(v_lst_c)), 2) if v_lst_c.size > 0 else None,
        }

    # Pixels valid across all 5 years
    five_year_complete_pixels = int(np.count_nonzero(valid_counts == 5))
    four_or_more_pixels = int(np.count_nonzero(valid_counts >= 4))

    return {
        "title": "CLIMORA Pune 5-Year Pre-Monsoon Multi-Temporal Summary (2021-2025)",
        "years_analyzed": years,
        "platforms": [landsat_results[yr]["platform"] for yr in years],
        "native_grid": {
            "crs": crs,
            "resolution_meters": [30.0, 30.0],
            "dimensions": list(mean_lst_c.shape),
            "affine_transform": [round(v, 6) for v in transform[:6]] if transform else None,
        },
        "spatial_completeness": {
            "total_pixels_in_grid": int(valid_counts.size),
            "statutory_aoi_pixels": 346809,
            "pixels_valid_all_5_years": five_year_complete_pixels,
            "pixels_valid_all_5_years_pct": round((five_year_complete_pixels / 346809) * 100.0, 2),
            "pixels_valid_at_least_4_years": four_or_more_pixels,
            "pixels_valid_at_least_4_years_pct": round((four_or_more_pixels / 346809) * 100.0, 2),
        },
        "aggregate_5_year_metrics": {
            "NDVI": _stats(ndvi_arr, "dimensionless [-1.0, 1.0]"),
            "NDBI": _stats(ndbi_arr, "dimensionless [-1.0, 1.0]"),
            "LST_Kelvin": _stats(lst_k_arr, "Kelvin (K)"),
            "LST_Celsius": _stats(lst_c_arr, "Degrees Celsius (°C)"),
        },
        "annual_breakdown": annual_breakdown,
        "scientific_limitations": (
            "Temporal observations represent single pre-monsoon summer snapshots (DOY 101-114). "
            "Data must not be cited as a multi-decadal warming trend or causal attribution."
        ),
    }
