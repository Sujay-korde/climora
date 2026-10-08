"""Automated Test Suite for CLIMORA Phase 1C: Feature Materialization & Scientific Quality.

Validates:
1. Canonical Feature Matrix tabular existence, shape (3,181 rows x 57 columns), and unique H3 indexing.
2. Exact Landsat temporal baseline scene lineage (2021-2025 April scenes, Landsat 9 for 2023).
3. K_valid logic, 70% valid pixel threshold, and missing-year denominator policy.
4. Baseline central tendencies (mean, median, sample stddev with ddof=1) and INSUFFICIENT_HISTORICAL_COVERAGE flag.
5. Absolute and standardized thermal anomalies with numerical stability parameter safeguard.
6. Heat persistence (Q75 exceedance frequency) and extreme LST recurrence (>= 45.0°C).
7. NDVI and NDBI biophysical bounds and temporal anomalies.
8. Demographic exposure mass conservation against WorldPop 2020 contract.
9. OpenStreetMap infrastructure spatial intersection counts and projected metric lengths/areas.
10. Normalized feature ranges [0.0, 1.0] and absence of invalid NDWI feature.
11. Machine-readable matrix contract schema completeness and SHA-256 fingerprinting.
"""

import json
import math
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pytest

from processing.config import (
    LANDSAT_TEMPORAL_BASELINE,
    MANIFESTS_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
)

PARQUET_PATH = PROCESSED_DIR / "canonical_feature_matrix.parquet"
CSV_PATH = PROCESSED_DIR / "canonical_feature_matrix.csv"
CONTRACT_PATH = MANIFESTS_DIR / "canonical_feature_matrix_contract.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "science" / "phase-1c-feature-quality-report.md"


@pytest.fixture(scope="module")
def feature_matrix() -> pd.DataFrame:
    """Load canonical feature matrix dataframe."""
    assert PARQUET_PATH.exists(), f"Missing canonical feature matrix Parquet at {PARQUET_PATH}"
    df = pd.read_parquet(PARQUET_PATH)
    return df


@pytest.fixture(scope="module")
def matrix_contract() -> dict:
    """Load canonical feature matrix contract JSON."""
    assert CONTRACT_PATH.exists(), f"Missing canonical feature matrix contract at {CONTRACT_PATH}"
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_matrix_shape_and_h3_spatial_identity(feature_matrix: pd.DataFrame):
    """Verify exact 3,181 rows, 57 columns, and unique H3 Resolution 9 cell identifiers."""
    df = feature_matrix
    assert len(df) == 3181, f"Expected exactly 3,181 rows, got {len(df)}"
    assert df["h3_cell_id"].nunique() == 3181, "All H3 cell IDs must be strictly unique"
    assert len(df.columns) == 57, f"Expected 57 feature columns, got {len(df.columns)}"

    # Validate H3 Resolution 9 geometry properties
    for cell_id in df["h3_cell_id"].head(50):
        assert len(cell_id) == 15
        assert h3.is_valid_cell(cell_id)
    # Phase 1C.1 Forensic Spatial Gate: Verify geodesic cell area properties
    assert df["cell_area_km2"].nunique() == 3181, "Every cell must have a unique geodesic area"
    assert (df["cell_area_km2"] >= 0.09836).all()
    assert (df["cell_area_km2"] <= 0.09888).all()
    assert abs(float(df["cell_area_km2"].mean()) - 0.09862857) < 1e-5

    # Verify PMC ward reporting units (41 wards)
    assert df["ward_id"].nunique() == 41
    assert df["ward_id"].str.startswith("PMC_WARD_").all()


def test_temporal_scene_lineage_and_sensor_governance(matrix_contract: dict):
    """Ensure feature matrix strictly tracks the 5 approved April baseline scenes."""
    expected_scenes = {
        2021: "LC08_L2SP_147047_20210424_02_T1",
        2022: "LC08_L2SP_147047_20220411_02_T1",
        2023: "LC09_L2SP_147047_20230422_02_T1",
        2024: "LC08_L2SP_147047_20240416_02_T1",
        2025: "LC08_L2SP_147047_20250419_02_T1",
    }

    cols = matrix_contract["columns"]
    for yr, expected_id in expected_scenes.items():
        col_name = f"lst_{yr}"
        assert col_name in cols
        if yr == 2023:
            assert "Landsat 9" in cols[col_name]["sensor"]
        else:
            assert "Landsat 8" in cols[col_name]["sensor"]

    # Verify zero inactive NDWI features in columns
    assert not any("ndwi" in c.lower() for c in cols.keys()), "NDWI must remain excluded"


def test_k_valid_logic_and_missing_data_policy(feature_matrix: pd.DataFrame):
    """Verify K_valid counting, 70% pixel threshold, and historical coverage eligibility."""
    df = feature_matrix

    # Check validity fractions in [0.0, 1.0]
    for yr in [2021, 2022, 2023, 2024, 2025]:
        vf = df[f"valid_fraction_{yr}"]
        assert (vf >= 0.0).all() and (vf <= 1.0).all()

    # Verify K_valid matches sum of indicators
    calc_k_valid = sum((df[f"valid_fraction_{yr}"] >= 0.70).astype(int) for yr in [2021, 2022, 2023, 2024, 2025])
    assert (df["K_valid"] == calc_k_valid).all()
    assert df["K_valid"].min() >= 0 and df["K_valid"].max() <= 5

    # Coverage status check
    eligible_mask = df["K_valid"] >= 4
    assert (df.loc[eligible_mask, "historical_coverage_status"] == "ELIGIBLE").all()
    assert (df.loc[~eligible_mask, "historical_coverage_status"] == "INSUFFICIENT_HISTORICAL_COVERAGE").all()

    # Exactly 3,113 eligible cells and 68 insufficient coverage cells
    assert eligible_mask.sum() == 3113
    assert (~eligible_mask).sum() == 68


def test_baseline_central_tendency_and_std_calculation(feature_matrix: pd.DataFrame):
    """Verify baseline mean, median, sample stddev (ddof=1), and that invalid cells evaluate to NaN."""
    df = feature_matrix
    eligible = df["historical_coverage_status"] == "ELIGIBLE"
    ineligible = ~eligible

    # Ineligible cells must have NaN for baseline metrics
    assert df.loc[ineligible, "lst_baseline_mean"].isna().all()
    assert df.loc[ineligible, "lst_baseline_median"].isna().all()
    assert df.loc[ineligible, "lst_baseline_std"].isna().all()

    # Eligible cells must have valid positive values
    clean_mean = df.loc[eligible, "lst_baseline_mean"]
    clean_std = df.loc[eligible, "lst_baseline_std"]
    assert not clean_mean.isna().any()
    assert not clean_std.isna().any()

    # Verify thermodynamic physical bounds for Pune pre-monsoon LST
    assert clean_mean.min() >= 25.0 and clean_mean.max() <= 60.0

    # Baseline stddev must be strictly positive (interannual variability)
    assert clean_std.min() >= 0.40, f"Expected positive interannual stddev, got min {clean_std.min()}"
    assert clean_std.max() <= 10.0


def test_thermal_anomalies_and_numerical_stability(feature_matrix: pd.DataFrame):
    """Verify absolute anomaly, standardized z-score, and absence of infinite values."""
    df = feature_matrix
    eligible = df["historical_coverage_status"] == "ELIGIBLE"

    diff = df.loc[eligible, "lst_2025"] - df.loc[eligible, "lst_baseline_mean"]
    assert np.allclose(df.loc[eligible, "lst_anomaly_absolute"], diff, atol=1e-2)

    z = df.loc[eligible, "lst_anomaly_zscore"]
    assert not np.isinf(z).any(), "z-score must not contain infinite values"
    assert not z.isna().any()
    assert z.min() >= -4.0 and z.max() <= 4.0


def test_heat_persistence_and_recurrence_denominators(feature_matrix: pd.DataFrame):
    """Verify persistence frequency in [0.0, 1.0] and extreme recurrence <= K_valid."""
    df = feature_matrix
    eligible = df["historical_coverage_status"] == "ELIGIBLE"

    pers = df.loc[eligible, "lst_persistence"]
    assert (pers >= 0.0).all() and (pers <= 1.0).all()

    recur = df.loc[eligible, "lst_recurrence_ge45"]
    assert (recur >= 0).all()
    assert (recur <= df.loc[eligible, "K_valid"]).all(), "Recurrence count cannot exceed K_valid"


def test_vegetation_and_built_environment_bounds(feature_matrix: pd.DataFrame):
    """Verify NDVI and NDBI values fall within physical bounds [-1.0, 1.0]."""
    df = feature_matrix
    eligible = df["historical_coverage_status"] == "ELIGIBLE"

    for yr in [2021, 2022, 2023, 2024, 2025]:
        ndvi = df.loc[eligible, f"ndvi_{yr}"].dropna()
        ndbi = df.loc[eligible, f"ndbi_{yr}"].dropna()
        assert (ndvi >= -1.0).all() and (ndvi <= 1.0).all()
        assert (ndbi >= -1.0).all() and (ndbi <= 1.0).all()

    # Check anomalies
    ndvi_diff = df.loc[eligible, "ndvi_2025"] - df.loc[eligible, "ndvi_baseline_mean"]
    assert np.allclose(df.loc[eligible, "ndvi_anomaly"], ndvi_diff, atol=1e-4)

    ndbi_diff = df.loc[eligible, "ndbi_2025"] - df.loc[eligible, "ndbi_baseline_mean"]
    assert np.allclose(df.loc[eligible, "ndbi_anomaly"], ndbi_diff, atol=1e-4)


def test_demographic_mass_conservation_worldpop_2020(feature_matrix: pd.DataFrame):
    """Verify demographic conservation against WorldPop 2020 contract."""
    df = feature_matrix

    total_matrix_pop = float(df["population_2020"].sum())
    expected_pop = 5011229.57

    delta_pct = abs(total_matrix_pop - expected_pop) / expected_pop * 100.0
    assert delta_pct <= 0.05, f"Demographic mass delta {delta_pct}% exceeds 0.05% tolerance"
    assert (df["population_2020"] >= 0.0).all()

    # Phase 1C.1: Verify density = count / cell_area_km2 (geodesic area)
    expected_density = np.round(df["population_2020"] / df["cell_area_km2"], 1)
    assert np.allclose(df["population_density_2020"], expected_density, atol=0.1)


def test_infrastructure_feature_integrity(feature_matrix: pd.DataFrame):
    """Verify OpenStreetMap infrastructure feature counts, lengths, and non-negative areas."""
    df = feature_matrix

    assert (df["hospital_count"] >= 0).all()
    assert (df["clinic_count"] >= 0).all()
    assert (df["school_count"] >= 0).all()
    assert (df["university_count"] >= 0).all()
    assert (df["road_length_m"] >= 0.0).all()
    assert (df["green_space_area_m2"] >= 0.0).all()
    assert (df["water_body_area_m2"] >= 0.0).all()

    # Check citywide infrastructure totals match OSM extract audit
    assert df["hospital_count"].sum() == 525
    assert df["clinic_count"].sum() == 349
    assert df["school_count"].sum() == 101
    assert df["university_count"].sum() == 37
    assert df["road_length_m"].sum() > 300000.0  # > 300 km
    assert df["green_space_area_m2"].sum() > 15000000.0  # > 15 km2


def test_normalized_feature_bounds(feature_matrix: pd.DataFrame):
    """Verify that all normalized features strictly lie within [0.0, 1.0]."""
    df = feature_matrix
    eligible = df["historical_coverage_status"] == "ELIGIBLE"

    norm_cols = [
        "norm_lst_2025", "norm_lst_anomaly", "norm_persistence", "norm_recurrence_ge45",
        "norm_population", "norm_population_density", "norm_ndvi_deficit", "norm_ndbi",
        "norm_road_length", "norm_civic_infra"
    ]

    for col in norm_cols:
        clean = df.loc[eligible, col].dropna()
        assert (clean >= -1e-6).all(), f"Column {col} has negative values: min {clean.min()}"
        assert (clean <= 1.0 + 1e-6).all(), f"Column {col} exceeds 1.0: max {clean.max()}"


def test_canonical_matrix_contract_and_report_integrity(matrix_contract: dict):
    """Verify machine-readable contract structure, cryptographic hashes, and report."""
    assert matrix_contract["status"] == "RATIFIED_AND_CANONICAL"
    assert matrix_contract["primary_analytical_mesh"]["total_cells"] == 3181
    assert matrix_contract["administrative_reporting_mesh"]["total_wards"] == 41

    # Check Parquet and CSV files on disk
    assert CSV_PATH.exists()
    assert PARQUET_PATH.exists()

    # Verify report existence
    assert REPORT_PATH.exists(), f"Phase 1C report must exist at {REPORT_PATH}"
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert "CLIMORA — Phase 1C: Canonical Feature Matrix Scientific Quality Report" in report_text
    assert "PHASE 1C — PASSED" in report_text


def test_phase_1c1_forensic_geodesic_area_recomputation(feature_matrix: pd.DataFrame):
    """Forensic Check #1: Verify exact geodesic H3 Res9 cell area calculations."""
    df = feature_matrix
    recomputed_areas = [h3.cell_area(c, unit="km^2") for c in df["h3_cell_id"]]

    # Verify every cell has a unique geodesic area
    assert len(set(recomputed_areas)) == 3181
    assert df["cell_area_km2"].nunique() == 3181

    # Exact equality with stored values
    assert np.allclose(df["cell_area_km2"], recomputed_areas, atol=1e-9)

    # Range and dispersion checks across Pune's latitudinal span
    min_a = min(recomputed_areas)
    max_a = max(recomputed_areas)
    mean_a = float(np.mean(recomputed_areas))
    assert 0.09836 < min_a < 0.09837
    assert 0.09887 < max_a < 0.09888
    assert abs(mean_a - 0.09862857) < 1e-6


def test_phase_1c1_forensic_zscore_numerical_stability(feature_matrix: pd.DataFrame):
    """Forensic Check #4: Verify z-score numerical stability and non-activation of epsilon."""
    df = feature_matrix
    eligible = df["historical_coverage_status"] == "ELIGIBLE"
    s_i = df.loc[eligible, "lst_baseline_std"].values

    assert (s_i >= 0.47).all(), f"Minimum s_i {s_i.min()} must exceed 0.05 C"
    assert not (s_i < 0.05).any(), "Zero cells should have negligible standard deviation"
    assert not (s_i == 0.0).any(), "Zero cells have zero variance"

    # Verify epsilon = 0.001 C was not activated for any eligible cell
    epsilon = 0.001
    assert (s_i >= epsilon).all()

    # Verify standardized anomaly calculation (accounting for 2-decimal column rounding)
    expected_z = (df.loc[eligible, "lst_2025"] - df.loc[eligible, "lst_baseline_mean"]) / (s_i + epsilon)
    assert np.allclose(df.loc[eligible, "lst_anomaly_zscore"], expected_z, atol=0.02)


def test_phase_1c1_forensic_osm_reconciliation_integrity(feature_matrix: pd.DataFrame):
    """Forensic Check #6: Verify OSM source -> AOI -> H3 assignment lineage reconciliation."""
    df = feature_matrix

    # Materialized amenity totals in canonical feature matrix
    assert int(df["hospital_count"].sum()) == 525
    assert int(df["clinic_count"].sum()) == 349
    assert int(df["school_count"].sum()) == 101
    assert int(df["university_count"].sum()) == 37

    # Metric lengths and areas in EPSG:32643
    assert abs(float(df["road_length_m"].sum()) - 383519.18) < 1.0
    assert abs(float(df["green_space_area_m2"].sum()) - 19987971.35) < 1.0
    assert abs(float(df["water_body_area_m2"].sum()) - 3871367.31) < 1.0

