"""Spatial Harmonization Framework & Multi-Resolution Profile Engine for CLIMORA.

Governance Constraints (Section 10 & 17):
- Landsat products remain at their native ~30m spatial resolution.
- Sentinel-2 products remain at native 10m/20m spatial resolution.
- MODIS products remain at native ~1km Sinusoidal resolution.
- DEM remains at native ~30m (1 arc-second) resolution.
- OSM vector layers remain vector GeoJSON polygons/linestrings.
- NASA POWER remains point/grid-cell meteorological forcing data.
- The final analytical spatial unit is explicitly NOT locked in Phase 1A.8.
- Evaluates candidate units: 250m planar metric grid, H3 Resolution 9, H3 Resolution 8, administrative wards.
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
    DATA_DIR,
    PROCESSED_DIR,
    PROCESSING_PHASE,
    PROCESSING_VERSION,
    PROJECT_ROOT,
    RAW_DIR,
    TIFF_FLOAT_PROFILE,
)
from processing.landsat_processor import write_geotiff

logger = get_logger()


def clip_dem_to_aoi() -> Dict[str, Any]:
    """Clip Copernicus DEM to Pune AOI at native resolution."""
    raw_dem_path = RAW_DIR / "dem" / "pune" / "Copernicus_DSM_COG_10_N18_00_E073_00_DEM.tif"
    if not raw_dem_path.exists():
        raise FileNotFoundError(f"Missing Copernicus DEM: {raw_dem_path}")

    aoi_data = load_aoi(PROJECT_ROOT / "data" / "aoi" / "pune.geojson")
    aoi_geom = aoi_data["features"][0]["geometry"]

    out_dem_dir = PROCESSED_DIR / "dem"
    out_dem_dir.mkdir(parents=True, exist_ok=True)
    out_dem_path = out_dem_dir / "Copernicus_DEM_30m_pune_clipped.tif"

    with rasterio.open(raw_dem_path) as src:
        crs_str = str(src.crs)
        geom_proj = transform_geom("EPSG:4326", src.crs, aoi_geom)
        clipped, tr = mask(src, [geom_proj], crop=True, nodata=-9999.0)
        dem_arr = clipped[0]
        res = src.res

    raw_sha = calculate_sha256(raw_dem_path)

    profile = TIFF_FLOAT_PROFILE.copy()
    profile.update({"nodata": -9999.0})
    write_geotiff(out_dem_path, dem_arr, tr, crs_str, profile)
    out_sha = calculate_sha256(out_dem_path)

    valid_vals = dem_arr[dem_arr != -9999.0]

    return {
        "dataset": "Copernicus GLO-30 DSM",
        "role": "topographic_elevation_and_slope",
        "native_crs": crs_str,
        "native_resolution": list(res),
        "resolution_description": "~30m (1 arc-second)",
        "dimensions": list(dem_arr.shape),
        "local_path": str(out_dem_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "raw_source_asset": str(raw_dem_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "raw_sha256": raw_sha,
        "processed_sha256": out_sha,
        "elevation_min_m": float(np.min(valid_vals)) if valid_vals.size > 0 else None,
        "elevation_max_m": float(np.max(valid_vals)) if valid_vals.size > 0 else None,
        "elevation_mean_m": float(np.mean(valid_vals)) if valid_vals.size > 0 else None,
    }


def build_spatial_harmonization_framework() -> Dict[str, Any]:
    """Generate multi-resolution spatial harmonization registry & candidate grid evaluation."""
    logger.info("Building multi-resolution spatial harmonization registry...")
    out_dir = PROCESSED_DIR / "temporal"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Process DEM to complete multi-resolution catalog
    dem_info = clip_dem_to_aoi()

    # 2. Compile resolution profiles for all active data modalities
    spatial_profiles = {
        "landsat_30m": {
            "modality": "Optical / Thermal Pre-Monsoon Baseline",
            "datasets": ["Landsat 8 OLI/TIRS", "Landsat 9 OLI-2/TIRS-2"],
            "native_spatial_resolution": "30.0 m x 30.0 m",
            "crs": "EPSG:32643 (WGS 84 / UTM Zone 43N)",
            "clipped_dimensions": [706, 954],
            "total_pixels_in_bbox": 673524,
            "statutory_aoi_valid_pixels": 346809,
            "affine_transform": [30.0, 0.0, 368025.0, 0.0, -30.0, 2059245.0],
            "bounding_box_utm": [368025.0, 2038065.0, 396645.0, 2059245.0],
            "status": "NATIVE_RESOLUTION_PRESERVED",
        },
        "sentinel2_10m_20m": {
            "modality": "Current-State High-Resolution Optical Reference",
            "datasets": ["Sentinel-2A MSI L2A (2025-01-18)"],
            "native_spatial_resolution": "10.0 m (B2, B3, B4, B8) and 20.0 m (B5, B6, B7, B11, B12, B8A, SCL)",
            "crs": "EPSG:32643 (WGS 84 / UTM Zone 43N)",
            "clipped_dimensions_10m": [2118, 2858],
            "clipped_dimensions_20m": [1060, 1430],
            "spatial_nesting_ratio_to_landsat": "Exact 3:1 integer sub-grid commensurability (10m x 3 = 30m)",
            "status": "NATIVE_RESOLUTION_PRESERVED",
        },
        "modis_1km": {
            "modality": "Coarse-Resolution Regional Thermal Context",
            "datasets": ["MODIS MOD11A2 v061 (Terra)", "MODIS MYD11A2 v061 (Aqua)"],
            "native_spatial_resolution": "926.625 m x 926.625 m (~1 km nominal)",
            "crs": "Sinusoidal (tile h25v07)",
            "clipped_dimensions": [24, 19],
            "valid_aoi_pixels": 284,
            "status": "NATIVE_RESOLUTION_PRESERVED",
        },
        "dem_30m": {
            "modality": "Topography / Digital Elevation Model",
            "datasets": ["Copernicus DEM GLO-30 DSM"],
            "native_spatial_resolution": "1 arc-second (~30 m at equator, ~28.5 m at 18.5°N)",
            "crs": "EPSG:4326 (WGS 84)",
            "clipped_dimensions": [824, 1083],
            "status": "NATIVE_RESOLUTION_PRESERVED",
        },
        "osm_vectors": {
            "modality": "Urban Morphology & Infrastructure Vector Geometry",
            "datasets": [
                "data/raw/osm/pune/green_spaces.geojson",
                "data/raw/osm/pune/water_bodies.geojson",
                "data/raw/osm/pune/road_network.geojson",
                "data/raw/osm/pune/public_infrastructure.geojson",
            ],
            "geometry_types": ["Polygon", "MultiPolygon", "LineString", "Point"],
            "native_crs": "EPSG:4326",
            "status": "NATIVE_VECTOR_PRESERVED",
        },
        "nasa_power_point": {
            "modality": "Meteorological Forcing Time Series",
            "datasets": ["NASA POWER Daily Meteorology (2021-2025)"],
            "spatial_representation": "Centroid point [73.8735, 18.5279] on MERRA-2 0.5° x 0.625° Grid",
            "status": "NATIVE_POINT_PRESERVED",
        },
    }

    # 3. Candidate Analytical Spatial Units Evaluation (Architecture Options)
    candidate_units = {
        "candidate_1_planar_metric_grid_250m": {
            "unit_name": "Planar Metric Grid (250 m x 250 m)",
            "target_crs": "EPSG:32643",
            "cell_area_km2": 0.0625,  # 250 x 250 = 62,500 m2
            "landsat_aggregation_factor": "~8.33 x 8.33 pixels per cell (~69.4 Landsat pixels)",
            "sentinel2_aggregation_factor": "25 x 25 pixels per cell (625 pixels)",
            "modis_downscaling_factor": "~3.7 x 3.7 cells per MODIS pixel",
            "pros": [
                "Cartesian metric uniformity across Pune municipal extent",
                "Standard 2D array representation directly consumable by CNNs and PyTorch tensors",
                "Simple zonal statistics without area distortion",
            ],
            "cons": [
                "Artificial square boundaries do not follow natural street corridors or wards",
                "Fractional boundary intersection with municipal limits",
            ],
            "suitability_score": "HIGH (for raster risk modeling)",
        },
        "candidate_2_uber_h3_resolution_9": {
            "unit_name": "Uber H3 Discrete Global Grid System (Resolution 9)",
            "spatial_type": "Hexagonal Geodesic DGGS",
            "average_cell_area_km2": 0.105,
            "average_edge_length_m": 174.38,
            "average_inter_cell_distance_m": 302.04,
            "approximate_cells_over_pune": "~3,300 cells",
            "landsat_aggregation_factor": "~116 Landsat 30m pixels per hexagon",
            "pros": [
                "Uniform distance to all 6 adjacent neighbors (optimal for heat diffusion & contagion)",
                "Invariant to directional orientation artifacts",
                "Standardized integer cell indexing (int64) for ultra-fast database joins",
                "Global scalability and direct mapping to mobility/demographic datasets",
            ],
            "cons": [
                "Non-hierarchical aperture-7 area nesting across resolutions",
                "Requires geodesic zonal aggregation rather than planar array slicing",
            ],
            "suitability_score": "HIGH (for spatial connectivity and intervention modeling)",
        },
        "candidate_3_uber_h3_resolution_8": {
            "unit_name": "Uber H3 Discrete Global Grid System (Resolution 8)",
            "spatial_type": "Hexagonal Geodesic DGGS",
            "average_cell_area_km2": 0.737,
            "average_edge_length_m": 461.35,
            "approximate_cells_over_pune": "~470 cells",
            "suitability_score": "MEDIUM (good for macro-neighborhood analysis, too coarse for block-level cool roofs)",
        },
        "candidate_4_administrative_wards": {
            "unit_name": "PMC Statutory Administrative Prabhag Wards",
            "spatial_type": "Administrative Vector Polygons",
            "pros": ["Direct alignment with civic budgetary and municipal implementation mechanisms"],
            "cons": ["High variance in ward area (Modifiable Areal Unit Problem - MAUP)"],
            "suitability_score": "REPORTING_ONLY (downstream aggregation target, not primary modeling mesh)",
        },
    }

    framework_doc = {
        "title": "CLIMORA Spatial Harmonization Framework & Multi-Resolution Registry",
        "phase": PROCESSING_PHASE,
        "processing_version": PROCESSING_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "governance_status": "DECISION_DEFERRED_UNTIL_PHASE_1B",
        "lock_status": "UNLOCKED (Native resolutions preserved to prevent scientific degradation)",
        "spatial_profiles": spatial_profiles,
        "candidate_analytical_units": candidate_units,
        "deferred_decision_statement": (
            "The final analytical spatial unit (e.g., 250m planar metric grid vs. H3 resolution 9) "
            "is intentionally deferred to Phase 1B. All Phase 1A.8 products are strictly stored at "
            "their native resolutions to enable lossless, mathematically rigorous aggregation "
            "to whichever target geometry is formally ratified."
        ),
    }

    framework_path = out_dir / "spatial_harmonization_framework.json"
    with open(framework_path, "w", encoding="utf-8") as f:
        json.dump(framework_doc, f, indent=2)

    logger.info("Spatial harmonization framework recorded.")
    return framework_doc
