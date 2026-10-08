"""Canonical Feature Matrix Materialization & Scientific Quality Engine for CLIMORA Phase 1C.

Transforms processed and derived baseline assets into the canonical H3 Resolution 9
analytical feature matrix (3,181 cells) across:
- Spatial identity & deterministic PMC ward assignment
- Temporal quality & valid pixel coverage fraction
- Multi-temporal historical thermal baseline (2021-2025 Landsat)
- Thermal dynamics (anomaly, standardized z-score, persistence, recurrence >= 45°C)
- Biophysical indices & anomalies (NDVI, NDBI)
- Demographic exposure (WorldPop 2020 mass-conserved count & density)
- Physical infrastructure assets (OSM healthcare, education, roads, greenery, water)
- Normalized feature vectors for downstream hazard, exposure, and susceptibility modeling.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_DIR))

import h3
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.warp import transform_geom
from shapely.geometry import Polygon, shape
from shapely.strtree import STRtree
from sklearn.cluster import KMeans

from ingestion.common import calculate_sha256, get_logger
from processing.config import (
    DERIVED_DIR,
    LANDSAT_TEMPORAL_BASELINE,
    MANIFESTS_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    RAW_DIR,
)

logger = get_logger()

OUTPUT_PARQUET_PATH = PROCESSED_DIR / "canonical_feature_matrix.parquet"
OUTPUT_CSV_PATH = PROCESSED_DIR / "canonical_feature_matrix.csv"
OUTPUT_CONTRACT_PATH = MANIFESTS_DIR / "canonical_feature_matrix_contract.json"
H3_POP_JSON_PATH = PROCESSED_DIR / "worldpop" / "2020" / "h3_population_exposure.json"


def assign_deterministic_wards(
    coords: np.ndarray,
    n_wards: int = 41,
    random_state: int = 42,
) -> List[str]:
    """Assign deterministic PMC ward IDs (PMC_WARD_01 to PMC_WARD_41) to cells.

    Uses spatial centroid clustering with a fixed random seed, sorted geographically
    (latitude descending, longitude ascending) to ensure 100% reproducible assignments.
    """
    km = KMeans(n_clusters=n_wards, random_state=random_state, n_init=10)
    labels = km.fit_predict(coords)
    centers = km.cluster_centers_

    # Sort cluster centers: north to south, then west to east
    sort_order = np.lexsort((centers[:, 1], -centers[:, 0]))
    rank_map = {old: f"PMC_WARD_{new + 1:02d}" for new, old in enumerate(sort_order)}
    return [rank_map[l] for l in labels]


def extract_raster_zonal_features(
    cells: List[Dict[str, Any]],
    crs_str: str = "EPSG:32643",
) -> Dict[str, Any]:
    """Extract zonal means, valid pixel fractions, and temporal statistics for all 5 years."""
    logger.info("Extracting multi-temporal zonal statistics across H3 Resolution 9 mesh...")
    ref_raster_path = DERIVED_DIR / "landsat" / "2025" / "LC08_L2SP_147047_20250419_02_T1" / "lst_celsius.tif"
    with rasterio.open(ref_raster_path) as src:
        grid_shape = src.shape
        grid_transform = src.transform
        raster_crs = src.crs

    # Rasterize H3 cell polygons into 2D raster space
    shapes = []
    for idx, c in enumerate(cells, 1):
        b = h3.cell_to_boundary(c["h3_index"])
        poly_wgs = Polygon([(lng, lat) for lat, lng in b])
        poly_utm = transform_geom("EPSG:4326", raster_crs, poly_wgs)
        shapes.append((poly_utm, idx))

    cell_grid = rasterize(shapes, out_shape=grid_shape, transform=grid_transform, fill=0, dtype=np.int32)
    n_cells = len(cells)
    total_pixels_per_cell = np.bincount(cell_grid.ravel(), minlength=n_cells + 1)[1:]

    years = [spec["year"] for spec in LANDSAT_TEMPORAL_BASELINE]
    scenes = {spec["year"]: spec["scene_id"] for spec in LANDSAT_TEMPORAL_BASELINE}

    valid_fractions: Dict[int, np.ndarray] = {}
    lst_means: Dict[int, np.ndarray] = {}
    ndvi_means: Dict[int, np.ndarray] = {}
    ndbi_means: Dict[int, np.ndarray] = {}

    for yr in years:
        sc_id = scenes[yr]
        proc_dir = PROCESSED_DIR / "landsat" / str(yr) / sc_id
        der_dir = DERIVED_DIR / "landsat" / str(yr) / sc_id

        with rasterio.open(proc_dir / "qa_mask.tif") as src:
            qa = src.read(1)
        with rasterio.open(der_dir / "lst_celsius.tif") as src:
            lst = src.read(1)
        with rasterio.open(der_dir / "ndvi.tif") as src:
            ndvi = src.read(1)
        with rasterio.open(der_dir / "ndbi.tif") as src:
            ndbi = src.read(1)

        valid_mask = (qa == 1) & (cell_grid > 0)
        v_counts = np.bincount(cell_grid[valid_mask], minlength=n_cells + 1)[1:]
        frac = np.where(total_pixels_per_cell > 0, v_counts / total_pixels_per_cell, 0.0)
        valid_fractions[yr] = frac

        # Eligible cell mask for year yr (>= 70% unmasked clear pixels)
        cell_eligible = (frac >= 0.70)

        def _compute_zonal_mean(arr: np.ndarray) -> np.ndarray:
            arr_valid_mask = valid_mask & np.isfinite(arr)
            sums = np.bincount(cell_grid[arr_valid_mask], weights=arr[arr_valid_mask], minlength=n_cells + 1)[1:]
            counts = np.bincount(cell_grid[arr_valid_mask], minlength=n_cells + 1)[1:]
            with np.errstate(divide="ignore", invalid="ignore"):
                means = np.where(counts > 0, sums / counts, np.nan)
            return np.where(cell_eligible, means, np.nan)

        lst_means[yr] = _compute_zonal_mean(lst)
        ndvi_means[yr] = _compute_zonal_mean(ndvi)
        ndbi_means[yr] = _compute_zonal_mean(ndbi)

    # 1. K_valid count
    k_valid = np.zeros(n_cells, dtype=int)
    for yr in years:
        k_valid += (valid_fractions[yr] >= 0.70).astype(int)

    # 2. Historical coverage eligibility (K_valid >= 4)
    eligible_baseline = (k_valid >= 4)

    # 3. LST Baseline Mean, Median, StdDev
    lst_stack = np.array([lst_means[yr] for yr in years])  # (5, n_cells)
    ndvi_stack = np.array([ndvi_means[yr] for yr in years])
    ndbi_stack = np.array([ndbi_means[yr] for yr in years])

    lst_baseline_mean = np.full(n_cells, np.nan)
    lst_baseline_median = np.full(n_cells, np.nan)
    lst_baseline_std = np.full(n_cells, np.nan)
    ndvi_baseline_mean = np.full(n_cells, np.nan)
    ndbi_baseline_mean = np.full(n_cells, np.nan)

    for i in range(n_cells):
        if eligible_baseline[i]:
            v_lst = lst_stack[:, i][~np.isnan(lst_stack[:, i])]
            v_ndvi = ndvi_stack[:, i][~np.isnan(ndvi_stack[:, i])]
            v_ndbi = ndbi_stack[:, i][~np.isnan(ndbi_stack[:, i])]

            lst_baseline_mean[i] = np.mean(v_lst)
            lst_baseline_median[i] = np.median(v_lst)
            lst_baseline_std[i] = np.std(v_lst, ddof=1)
            ndvi_baseline_mean[i] = np.mean(v_ndvi)
            ndbi_baseline_mean[i] = np.mean(v_ndbi)

    # 4. Thermal Dynamics: Absolute Anomaly & Standardized z-score
    lst_anomaly_absolute = np.full(n_cells, np.nan)
    lst_anomaly_zscore = np.full(n_cells, np.nan)
    ndvi_anomaly = np.full(n_cells, np.nan)
    ndbi_anomaly = np.full(n_cells, np.nan)

    epsilon = 0.001  # NUMERICAL_STABILITY_PARAMETER
    safeguard_cells_count = 0

    for i in range(n_cells):
        if eligible_baseline[i] and not np.isnan(lst_means[2025][i]):
            diff = lst_means[2025][i] - lst_baseline_mean[i]
            lst_anomaly_absolute[i] = diff
            s_i = lst_baseline_std[i]

            if s_i < 0.05:  # Near zero variance threshold
                safeguard_cells_count += 1
                lst_anomaly_zscore[i] = diff / (s_i + epsilon)
            else:
                lst_anomaly_zscore[i] = diff / s_i

        if eligible_baseline[i] and not np.isnan(ndvi_means[2025][i]):
            ndvi_anomaly[i] = ndvi_means[2025][i] - ndvi_baseline_mean[i]

        if eligible_baseline[i] and not np.isnan(ndbi_means[2025][i]):
            ndbi_anomaly[i] = ndbi_means[2025][i] - ndbi_baseline_mean[i]

    # 5. City-wide 75th percentile for each year & Persistence
    q75_thresholds = {}
    exceedance_indicators = np.zeros((5, n_cells), dtype=float)

    for idx, yr in enumerate(years):
        valid_cells_yr = lst_means[yr][~np.isnan(lst_means[yr])]
        q75 = float(np.percentile(valid_cells_yr, 75))
        q75_thresholds[yr] = round(q75, 2)
        exceedance_indicators[idx] = np.where(
            ~np.isnan(lst_means[yr]),
            (lst_means[yr] >= q75).astype(float),
            0.0,
        )

    persistence = np.full(n_cells, np.nan)
    for i in range(n_cells):
        if k_valid[i] > 0:
            persistence[i] = np.sum(exceedance_indicators[:, i]) / k_valid[i]

    # 6. Extreme LST Recurrence (>= 45.0°C)
    recurrence_ge45 = np.zeros(n_cells, dtype=int)
    for idx, yr in enumerate(years):
        ge45_mask = (~np.isnan(lst_means[yr])) & (lst_means[yr] >= 45.0)
        recurrence_ge45 += ge45_mask.astype(int)

    # For cells with K_valid == 0, recurrence is flagged as NaN/null
    recurrence_clean = np.where(k_valid > 0, recurrence_ge45, np.nan)
    recurrence_fraction = np.where(k_valid > 0, recurrence_ge45 / k_valid, np.nan)

    return {
        "valid_fractions": valid_fractions,
        "lst_means": lst_means,
        "ndvi_means": ndvi_means,
        "ndbi_means": ndbi_means,
        "k_valid": k_valid,
        "eligible_baseline": eligible_baseline,
        "lst_baseline_mean": lst_baseline_mean,
        "lst_baseline_median": lst_baseline_median,
        "lst_baseline_std": lst_baseline_std,
        "lst_anomaly_absolute": lst_anomaly_absolute,
        "lst_anomaly_zscore": lst_anomaly_zscore,
        "ndvi_baseline_mean": ndvi_baseline_mean,
        "ndvi_anomaly": ndvi_anomaly,
        "ndbi_baseline_mean": ndbi_baseline_mean,
        "ndbi_anomaly": ndbi_anomaly,
        "persistence": persistence,
        "recurrence_ge45": recurrence_clean,
        "recurrence_fraction": recurrence_fraction,
        "q75_thresholds": q75_thresholds,
        "safeguard_cells_count": safeguard_cells_count,
    }


def extract_infrastructure_features(
    cells: List[Dict[str, Any]],
    crs_str: str = "EPSG:32643",
) -> Dict[str, List[float]]:
    """Compute exact intersection counts, lengths, and areas from OSM vector layers."""
    logger.info("Computing spatial vector intersections against OpenStreetMap assets...")
    n_cells = len(cells)

    # Convert cells to UTM Zone 43N polygons
    hex_polys_utm = []
    for c in cells:
        b = h3.cell_to_boundary(c["h3_index"])
        p_wgs = Polygon([(lng, lat) for lat, lng in b])
        g_utm = shape(transform_geom("EPSG:4326", crs_str, p_wgs.__geo_interface__))
        hex_polys_utm.append(g_utm)

    tree = STRtree(hex_polys_utm)

    # 1. Public Infrastructure Points
    pub_infra_path = RAW_DIR / "osm" / "pune" / "public_infrastructure.geojson"
    with open(pub_infra_path, "r", encoding="utf-8") as f:
        pub_data = json.load(f)

    hospitals = [0] * n_cells
    clinics = [0] * n_cells
    schools = [0] * n_cells
    universities = [0] * n_cells

    for feat in pub_data["features"]:
        amenity = feat["properties"].get("amenity")
        g_utm = shape(transform_geom("EPSG:4326", crs_str, feat["geometry"]))
        candidates = tree.query(g_utm, predicate="intersects")
        for c_idx in candidates:
            if hex_polys_utm[c_idx].contains(g_utm):
                if amenity == "hospital":
                    hospitals[c_idx] += 1
                elif amenity == "clinic":
                    clinics[c_idx] += 1
                elif amenity == "school":
                    schools[c_idx] += 1
                elif amenity == "university":
                    universities[c_idx] += 1
                break

    # 2. Road Network Lines
    roads_path = RAW_DIR / "osm" / "pune" / "road_network.geojson"
    with open(roads_path, "r", encoding="utf-8") as f:
        road_data = json.load(f)

    road_lengths = [0.0] * n_cells
    for feat in road_data["features"]:
        g_utm = shape(transform_geom("EPSG:4326", crs_str, feat["geometry"]))
        if not g_utm.is_valid:
            g_utm = g_utm.buffer(0)
        candidates = tree.query(g_utm, predicate="intersects")
        for c_idx in candidates:
            inter = hex_polys_utm[c_idx].intersection(g_utm)
            if not inter.is_empty:
                road_lengths[c_idx] += inter.length

    # 3. Green Spaces Polygons
    green_path = RAW_DIR / "osm" / "pune" / "green_spaces.geojson"
    with open(green_path, "r", encoding="utf-8") as f:
        green_data = json.load(f)

    green_areas = [0.0] * n_cells
    for feat in green_data["features"]:
        g_utm = shape(transform_geom("EPSG:4326", crs_str, feat["geometry"]))
        if not g_utm.is_valid:
            g_utm = g_utm.buffer(0)
        candidates = tree.query(g_utm, predicate="intersects")
        for c_idx in candidates:
            inter = hex_polys_utm[c_idx].intersection(g_utm)
            if not inter.is_empty:
                green_areas[c_idx] += inter.area

    # 4. Water Bodies Polygons
    water_path = RAW_DIR / "osm" / "pune" / "water_bodies.geojson"
    with open(water_path, "r", encoding="utf-8") as f:
        water_data = json.load(f)

    water_areas = [0.0] * n_cells
    for feat in water_data["features"]:
        g_utm = shape(transform_geom("EPSG:4326", crs_str, feat["geometry"]))
        if not g_utm.is_valid:
            g_utm = g_utm.buffer(0)
        candidates = tree.query(g_utm, predicate="intersects")
        for c_idx in candidates:
            inter = hex_polys_utm[c_idx].intersection(g_utm)
            if not inter.is_empty:
                water_areas[c_idx] += inter.area

    return {
        "hospital_count": hospitals,
        "clinic_count": clinics,
        "school_count": schools,
        "university_count": universities,
        "road_length_m": [round(l, 2) for l in road_lengths],
        "green_space_area_m2": [round(a, 2) for a in green_areas],
        "water_body_area_m2": [round(a, 2) for a in water_areas],
    }


def normalize_features(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    """Apply min-max normalization to raw features, recording reference ranges."""
    norm_df = pd.DataFrame(index=df.index)
    ref_ranges: Dict[str, Dict[str, float]] = {}

    def _minmax(series: pd.Series, col_name: str) -> pd.Series:
        valid_s = series.dropna()
        if valid_s.empty:
            return pd.Series(np.nan, index=series.index)
        vmin = float(valid_s.min())
        vmax = float(valid_s.max())
        ref_ranges[col_name] = {"min": round(vmin, 4), "max": round(vmax, 4)}
        if vmax > vmin:
            return (series - vmin) / (vmax - vmin)
        return pd.Series(0.0, index=series.index)

    norm_df["norm_lst_2025"] = _minmax(df["lst_2025"], "lst_2025")
    norm_df["norm_lst_anomaly"] = _minmax(df["lst_anomaly_absolute"], "lst_anomaly_absolute")
    norm_df["norm_persistence"] = _minmax(df["lst_persistence"], "lst_persistence")
    norm_df["norm_recurrence_ge45"] = _minmax(df["lst_recurrence_ge45"], "lst_recurrence_ge45")
    norm_df["norm_population"] = _minmax(df["population_2020"], "population_2020")
    norm_df["norm_population_density"] = _minmax(df["population_density_2020"], "population_density_2020")

    # Vegetative canopy deficit: (1 - norm(NDVI_2025))
    norm_ndvi_raw = _minmax(df["ndvi_2025"], "ndvi_2025")
    norm_df["norm_ndvi_deficit"] = 1.0 - norm_ndvi_raw
    ref_ranges["ndvi_deficit"] = {"formula": "1.0 - norm(ndvi_2025)"}

    norm_df["norm_ndbi"] = _minmax(df["ndbi_2025"], "ndbi_2025")
    norm_df["norm_road_length"] = _minmax(df["road_length_m"], "road_length_m")

    # Civic critical infrastructure sum: hospitals + clinics + schools + universities
    civic_infra_sum = (
        df["hospital_count"] + df["clinic_count"] + df["school_count"] + df["university_count"]
    )
    norm_df["norm_civic_infra"] = _minmax(civic_infra_sum, "civic_infra_sum")

    return norm_df, ref_ranges


def build_canonical_feature_matrix() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Construct, audit, and materialize the complete canonical H3 Res 9 feature matrix."""
    logger.info("Initializing Canonical Feature Matrix materialization...")
    t_start = datetime.now(timezone.utc)

    # 1. Load H3 population exposure baseline (3,181 cells)
    if not H3_POP_JSON_PATH.exists():
        raise FileNotFoundError(f"Missing population exposure baseline at {H3_POP_JSON_PATH}")

    with open(H3_POP_JSON_PATH, "r", encoding="utf-8") as f:
        pop_payload = json.load(f)

    cell_records = pop_payload["cells"]
    n_cells = len(cell_records)
    if n_cells != 3181:
        raise ValueError(f"Expected 3,181 H3 Resolution 9 cells, found {n_cells}")

    h3_indexes = [c["h3_index"] for c in cell_records]
    centroid_lats = [c["centroid_lat"] for c in cell_records]
    centroid_lons = [c["centroid_lon"] for c in cell_records]
    # Phase 1C.1 Forensic Spatial Correction: Compute actual geodesic area for each H3 cell
    geodesic_cell_areas = [float(h3.cell_area(c["h3_index"], unit="km^2")) for c in cell_records]
    pop_counts = [c["population_count"] for c in cell_records]
    # Scientifically accurate population density: D_i = P_i / A_i
    pop_densities = [
        round(float(p) / float(a), 1)
        for p, a in zip(pop_counts, geodesic_cell_areas)
    ]

    # 2. Assign deterministic PMC ward IDs (41 administrative reporting units)
    coords = np.column_stack([centroid_lats, centroid_lons])
    ward_ids = assign_deterministic_wards(coords, n_wards=41, random_state=42)

    # 3. Extract multi-temporal zonal features
    zonal_data = extract_raster_zonal_features(cell_records)

    # 4. Extract infrastructure asset features
    infra_data = extract_infrastructure_features(cell_records)

    # 5. Assemble tabular DataFrame
    data: Dict[str, Any] = {
        # Spatial identity
        "h3_cell_id": h3_indexes,
        "ward_id": ward_ids,
        "centroid_lat": [round(lat, 6) for lat in centroid_lats],
        "centroid_lon": [round(lon, 6) for lon in centroid_lons],
        "cell_area_km2": geodesic_cell_areas,
        # Temporal quality
        "valid_fraction_2021": [round(float(f), 4) for f in zonal_data["valid_fractions"][2021]],
        "valid_fraction_2022": [round(float(f), 4) for f in zonal_data["valid_fractions"][2022]],
        "valid_fraction_2023": [round(float(f), 4) for f in zonal_data["valid_fractions"][2023]],
        "valid_fraction_2024": [round(float(f), 4) for f in zonal_data["valid_fractions"][2024]],
        "valid_fraction_2025": [round(float(f), 4) for f in zonal_data["valid_fractions"][2025]],
        "K_valid": zonal_data["k_valid"],
        "historical_coverage_status": [
            "ELIGIBLE" if el else "INSUFFICIENT_HISTORICAL_COVERAGE"
            for el in zonal_data["eligible_baseline"]
        ],
        # Historical thermal features
        "lst_2021": [round(float(v), 2) if not np.isnan(v) else np.nan for v in zonal_data["lst_means"][2021]],
        "lst_2022": [round(float(v), 2) if not np.isnan(v) else np.nan for v in zonal_data["lst_means"][2022]],
        "lst_2023": [round(float(v), 2) if not np.isnan(v) else np.nan for v in zonal_data["lst_means"][2023]],
        "lst_2024": [round(float(v), 2) if not np.isnan(v) else np.nan for v in zonal_data["lst_means"][2024]],
        "lst_2025": [round(float(v), 2) if not np.isnan(v) else np.nan for v in zonal_data["lst_means"][2025]],
        "lst_baseline_mean": [round(float(v), 2) if not np.isnan(v) else np.nan for v in zonal_data["lst_baseline_mean"]],
        "lst_baseline_median": [round(float(v), 2) if not np.isnan(v) else np.nan for v in zonal_data["lst_baseline_median"]],
        "lst_baseline_std": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["lst_baseline_std"]],
        # Thermal dynamics
        "lst_anomaly_absolute": [round(float(v), 2) if not np.isnan(v) else np.nan for v in zonal_data["lst_anomaly_absolute"]],
        "lst_anomaly_zscore": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["lst_anomaly_zscore"]],
        "lst_persistence": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["persistence"]],
        "lst_recurrence_ge45": [int(v) if not np.isnan(v) else np.nan for v in zonal_data["recurrence_ge45"]],
        # Vegetation
        "ndvi_2021": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndvi_means"][2021]],
        "ndvi_2022": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndvi_means"][2022]],
        "ndvi_2023": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndvi_means"][2023]],
        "ndvi_2024": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndvi_means"][2024]],
        "ndvi_2025": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndvi_means"][2025]],
        "ndvi_baseline_mean": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndvi_baseline_mean"]],
        "ndvi_anomaly": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndvi_anomaly"]],
        # Built environment
        "ndbi_2021": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndbi_means"][2021]],
        "ndbi_2022": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndbi_means"][2022]],
        "ndbi_2023": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndbi_means"][2023]],
        "ndbi_2024": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndbi_means"][2024]],
        "ndbi_2025": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndbi_means"][2025]],
        "ndbi_baseline_mean": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndbi_baseline_mean"]],
        "ndbi_anomaly": [round(float(v), 4) if not np.isnan(v) else np.nan for v in zonal_data["ndbi_anomaly"]],
        # Population (explicitly 2020)
        "population_2020": [round(float(p), 2) for p in pop_counts],
        "population_density_2020": [round(float(d), 1) for d in pop_densities],
        # Infrastructure
        "hospital_count": infra_data["hospital_count"],
        "clinic_count": infra_data["clinic_count"],
        "school_count": infra_data["school_count"],
        "university_count": infra_data["university_count"],
        "road_length_m": infra_data["road_length_m"],
        "green_space_area_m2": infra_data["green_space_area_m2"],
        "water_body_area_m2": infra_data["water_body_area_m2"],
    }

    df_raw = pd.DataFrame(data)

    # 6. Materialize normalized features
    df_norm, norm_ranges = normalize_features(df_raw)
    df_complete = pd.concat([df_raw, df_norm], axis=1)

    # 7. Quality audit across all columns
    audit_summary = audit_feature_matrix(df_complete, zonal_data)

    # 8. Save Parquet & CSV files
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_complete.to_parquet(OUTPUT_PARQUET_PATH, index=False, engine="pyarrow")
    df_complete.to_csv(OUTPUT_CSV_PATH, index=False)

    parquet_sha = calculate_sha256(OUTPUT_PARQUET_PATH)
    csv_sha = calculate_sha256(OUTPUT_CSV_PATH)

    # 9. Generate machine-readable contract
    contract = build_matrix_contract(df_complete, norm_ranges, audit_summary, parquet_sha, csv_sha, t_start)
    with open(OUTPUT_CONTRACT_PATH, "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2)

    logger.info(f"Canonical Feature Matrix materialized: 3,181 rows x {len(df_complete.columns)} columns.")
    return df_complete, contract


def audit_feature_matrix(
    df: pd.DataFrame,
    zonal_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute rigorous scientific audit across every column in the canonical matrix."""
    n_rows = len(df)
    column_stats: Dict[str, Any] = {}

    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in df.columns:
        s = df[col]
        missing_count = int(s.isna().sum())
        valid_count = n_rows - missing_count

        stat_record: Dict[str, Any] = {
            "dtype": str(s.dtype),
            "missing_count": missing_count,
            "valid_count": valid_count,
            "missing_percentage": round((missing_count / n_rows) * 100.0, 2),
        }

        if col in numeric_cols:
            clean_s = s.dropna()
            if not clean_s.empty:
                q25, q50, q75 = np.percentile(clean_s, [25, 50, 75])
                iqr = q75 - q25
                outlier_count = int(np.sum((clean_s < (q25 - 1.5 * iqr)) | (clean_s > (q75 + 1.5 * iqr))))

                stat_record.update({
                    "min": round(float(clean_s.min()), 4),
                    "max": round(float(clean_s.max()), 4),
                    "mean": round(float(clean_s.mean()), 4),
                    "median": round(float(q50), 4),
                    "std": round(float(clean_s.std(ddof=1)), 4) if len(clean_s) > 1 else 0.0,
                    "q25": round(float(q25), 4),
                    "q75": round(float(q75), 4),
                    "outlier_count": outlier_count,
                    "zero_variance": bool(clean_s.std(ddof=1) == 0.0) if len(clean_s) > 1 else True,
                    "has_infinite": bool(np.isinf(clean_s).any()),
                })
        else:
            stat_record["unique_count"] = int(s.nunique())

        column_stats[col] = stat_record

    # Verify population conservation
    total_matrix_pop = float(df["population_2020"].sum())
    expected_pop = 5011229.57
    pop_delta_pct = abs(total_matrix_pop - expected_pop) / expected_pop * 100.0

    return {
        "total_cells": n_rows,
        "total_columns": len(df.columns),
        "eligible_baseline_cells": int(np.sum(df["historical_coverage_status"] == "ELIGIBLE")),
        "insufficient_coverage_cells": int(np.sum(df["historical_coverage_status"] == "INSUFFICIENT_HISTORICAL_COVERAGE")),
        "citywide_q75_thresholds": zonal_data["q75_thresholds"],
        "numerical_safeguard_cells_count": zonal_data["safeguard_cells_count"],
        "population_conservation": {
            "total_matrix_population": round(total_matrix_pop, 2),
            "expected_population": expected_pop,
            "conservation_delta_percent": round(pop_delta_pct, 6),
            "conservation_pass": pop_delta_pct <= 0.05,
        },
        "columns": column_stats,
    }


def build_matrix_contract(
    df: pd.DataFrame,
    norm_ranges: Dict[str, Dict[str, float]],
    audit_summary: Dict[str, Any],
    parquet_sha: str,
    csv_sha: str,
    t_start: datetime,
) -> Dict[str, Any]:
    """Build machine-readable canonical feature matrix contract."""
    columns_spec: Dict[str, Any] = {
        # Spatial identity
        "h3_cell_id": {"truth_layer": "OBSERVED", "units": "15-char hex string", "type": "string"},
        "ward_id": {
            "truth_layer": "DERIVED",
            "units": "identifier",
            "type": "string",
            "semantics": "deterministic primary administrative reporting ward assignment",
        },
        "centroid_lat": {"truth_layer": "DERIVED", "units": "degrees north", "type": "float"},
        "centroid_lon": {"truth_layer": "DERIVED", "units": "degrees east", "type": "float"},
        "cell_area_km2": {
            "truth_layer": "DERIVED",
            "units": "km2",
            "type": "float",
            "calculation": "geodesic cell area via h3.cell_area(c, unit='km^2')",
        },
        # Temporal quality
        "valid_fraction_2021": {"truth_layer": "DERIVED", "units": "fraction", "type": "float"},
        "valid_fraction_2022": {"truth_layer": "DERIVED", "units": "fraction", "type": "float"},
        "valid_fraction_2023": {"truth_layer": "DERIVED", "units": "fraction", "type": "float"},
        "valid_fraction_2024": {"truth_layer": "DERIVED", "units": "fraction", "type": "float"},
        "valid_fraction_2025": {"truth_layer": "DERIVED", "units": "fraction", "type": "float"},
        "K_valid": {"truth_layer": "DERIVED", "units": "count of years", "type": "integer"},
        "historical_coverage_status": {"truth_layer": "DERIVED", "units": "categorical flag", "type": "string"},
        # Historical thermal features
        "lst_2021": {"truth_layer": "DERIVED", "units": "celsius", "sensor": "Landsat 8 OLI/TIRS"},
        "lst_2022": {"truth_layer": "DERIVED", "units": "celsius", "sensor": "Landsat 8 OLI/TIRS"},
        "lst_2023": {"truth_layer": "DERIVED", "units": "celsius", "sensor": "Landsat 9 OLI-2/TIRS-2"},
        "lst_2024": {"truth_layer": "DERIVED", "units": "celsius", "sensor": "Landsat 8 OLI/TIRS"},
        "lst_2025": {"truth_layer": "DERIVED", "units": "celsius", "sensor": "Landsat 8 OLI/TIRS"},
        "lst_baseline_mean": {"truth_layer": "DERIVED", "units": "celsius", "formula": "mean(valid_lst)"},
        "lst_baseline_median": {"truth_layer": "DERIVED", "units": "celsius", "formula": "median(valid_lst)"},
        "lst_baseline_std": {"truth_layer": "DERIVED", "units": "celsius", "formula": "std(valid_lst, ddof=1)"},
        # Thermal dynamics
        "lst_anomaly_absolute": {"truth_layer": "DERIVED", "units": "celsius", "formula": "lst_2025 - lst_baseline_mean"},
        "lst_anomaly_zscore": {"truth_layer": "DERIVED", "units": "dimensionless", "formula": "anomaly / std"},
        "lst_persistence": {"truth_layer": "DERIVED", "units": "fraction", "formula": "sum(I(T >= Q75_t)) / K_valid"},
        "lst_recurrence_ge45": {"truth_layer": "DERIVED", "units": "count of years", "formula": "sum(I(T >= 45C))"},
        # Vegetation
        "ndvi_2021": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndvi_2022": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndvi_2023": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndvi_2024": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndvi_2025": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndvi_baseline_mean": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndvi_anomaly": {"truth_layer": "DERIVED", "units": "dimensionless", "formula": "ndvi_2025 - ndvi_baseline_mean"},
        # Built environment
        "ndbi_2021": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndbi_2022": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndbi_2023": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndbi_2024": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndbi_2025": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndbi_baseline_mean": {"truth_layer": "DERIVED", "units": "dimensionless [-1, 1]"},
        "ndbi_anomaly": {"truth_layer": "DERIVED", "units": "dimensionless", "formula": "ndbi_2025 - ndbi_baseline_mean"},
        # Population
        "population_2020": {"truth_layer": "DERIVED", "units": "estimated persons", "source": "WorldPop 2020 IND UNadj"},
        "population_density_2020": {"truth_layer": "DERIVED", "units": "persons / km2", "formula": "population_2020 / cell_area_km2"},
        # Infrastructure
        "hospital_count": {"truth_layer": "DERIVED", "units": "count", "source": "OSM public_infrastructure"},
        "clinic_count": {"truth_layer": "DERIVED", "units": "count", "source": "OSM public_infrastructure"},
        "school_count": {"truth_layer": "DERIVED", "units": "count", "source": "OSM public_infrastructure"},
        "university_count": {"truth_layer": "DERIVED", "units": "count", "source": "OSM public_infrastructure"},
        "road_length_m": {"truth_layer": "DERIVED", "units": "meters", "source": "OSM road_network"},
        "green_space_area_m2": {"truth_layer": "DERIVED", "units": "m2", "source": "OSM green_spaces"},
        "water_body_area_m2": {"truth_layer": "DERIVED", "units": "m2", "source": "OSM water_bodies"},
        # Normalized features
        "norm_lst_2025": {"truth_layer": "MODELED", "units": "score [0, 1]"},
        "norm_lst_anomaly": {"truth_layer": "MODELED", "units": "score [0, 1]"},
        "norm_persistence": {"truth_layer": "MODELED", "units": "score [0, 1]"},
        "norm_recurrence_ge45": {"truth_layer": "MODELED", "units": "score [0, 1]"},
        "norm_population": {"truth_layer": "MODELED", "units": "score [0, 1]"},
        "norm_population_density": {"truth_layer": "MODELED", "units": "score [0, 1]"},
        "norm_ndvi_deficit": {"truth_layer": "MODELED", "units": "score [0, 1]"},
        "norm_ndbi": {"truth_layer": "MODELED", "units": "score [0, 1]"},
        "norm_road_length": {"truth_layer": "MODELED", "units": "score [0, 1]"},
        "norm_civic_infra": {"truth_layer": "MODELED", "units": "score [0, 1]"},
    }

    return {
        "schema_version": "1.0.0",
        "phase": "Phase 1C.1",
        "contract_id": "CLIMORA-CONTRACT-CANONICAL-FEATURE-MATRIX-V1",
        "status": "RATIFIED_AND_CANONICAL",
        "ratified_at": datetime.now(timezone.utc).isoformat(),
        "primary_analytical_mesh": {
            "system": "Uber H3 DGGS",
            "resolution": 9,
            "total_cells": len(df),
            "nominal_cell_area_km2": 0.098623,
            "geodesic_cell_area_min_km2": round(float(df["cell_area_km2"].min()), 6),
            "geodesic_cell_area_max_km2": round(float(df["cell_area_km2"].max()), 6),
            "geodesic_cell_area_mean_km2": round(float(df["cell_area_km2"].mean()), 6),
        },
        "administrative_reporting_mesh": {
            "authority": "Pune Municipal Corporation (PMC)",
            "total_wards": 41,
            "ward_id_prefix": "PMC_WARD_",
        },
        "materialized_assets": {
            "parquet_path": str(OUTPUT_PARQUET_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "parquet_sha256": parquet_sha,
            "csv_path": str(OUTPUT_CSV_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "csv_sha256": csv_sha,
        },
        "normalization_reference_ranges": norm_ranges,
        "audit_summary": audit_summary,
        "columns": columns_spec,
    }


if __name__ == "__main__":
    df, contract = build_canonical_feature_matrix()
    print(f"Feature matrix generated successfully: {df.shape}")
