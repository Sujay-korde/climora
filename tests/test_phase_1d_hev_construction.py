"""Unit tests for CLIMORA Phase 1D: Hazard-Exposure-Susceptibility Construction Gate.

Verifies:
1. Exact row count (3,181 H3 Res9 cells).
2. Complete mathematical decoupling from KMeans ward_id.
3. Numerical finiteness and strict [0, 1] bounds for eligible cells.
4. Strict NaN preservation for disqualified cells (K_valid < 4; no silent imputation).
5. Zero-exposure boundary semantics.
6. Component directionality (higher physical stress -> higher index).
7. Weight sum unity across all three dimensions.
8. Anti-double-counting boundary enforcement (no cross-contamination between H, E, V).
9. Checksum and contract integrity.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from processing.config import MANIFESTS_DIR, PROCESSED_DIR, PROJECT_ROOT
from processing.hev_construction import (
    HAZARD_WEIGHTS,
    EXPOSURE_WEIGHTS,
    SUSCEPTIBILITY_WEIGHTS,
    construct_hev_components,
)

PARQUET_PATH = PROCESSED_DIR / "hev" / "canonical_hev_components.parquet"
CONTRACT_PATH = MANIFESTS_DIR / "canonical_hev_contract.json"
FEATURE_MATRIX_PATH = PROCESSED_DIR / "canonical_feature_matrix.parquet"


@pytest.fixture(scope="module")
def hev_data() -> pd.DataFrame:
    """Load canonical HEV components parquet."""
    assert PARQUET_PATH.exists(), f"Missing HEV artifact: {PARQUET_PATH}"
    return pd.read_parquet(PARQUET_PATH)


@pytest.fixture(scope="module")
def feature_matrix() -> pd.DataFrame:
    """Load canonical feature matrix."""
    assert FEATURE_MATRIX_PATH.exists(), f"Missing canonical feature matrix: {FEATURE_MATRIX_PATH}"
    return pd.read_parquet(FEATURE_MATRIX_PATH)


@pytest.fixture(scope="module")
def hev_contract() -> dict:
    """Load canonical HEV JSON contract."""
    assert CONTRACT_PATH.exists(), f"Missing contract: {CONTRACT_PATH}"
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_hev_dimensions_and_schema(hev_data: pd.DataFrame):
    """Test 1: Row count is exactly 3,181 and required columns exist."""
    assert len(hev_data) == 3181, f"Expected 3,181 cells, found {len(hev_data)}"
    assert hev_data["h3_cell_id"].nunique() == 3181
    assert hev_data["h3_cell_id"].str.len().eq(15).all()

    required_cols = [
        "h3_cell_id",
        "H_i",
        "E_i",
        "V_i",
        "hazard_eligibility",
        "exposure_eligibility",
        "susceptibility_eligibility",
        "overall_hev_eligibility",
    ]
    for col in required_cols:
        assert col in hev_data.columns, f"Missing required column: {col}"

    # Decoupling check: ward_id must NOT be present in canonical HEV analytical mesh
    assert "ward_id" not in hev_data.columns, "ward_id must be decoupled from canonical HEV components"


def test_eligibility_partition(hev_data: pd.DataFrame, feature_matrix: pd.DataFrame):
    """Test 2: Exactly 3,113 eligible cells and 68 ineligible cells."""
    assert hev_data["hazard_eligibility"].sum() == 3113
    assert (~hev_data["hazard_eligibility"]).sum() == 68

    assert hev_data["exposure_eligibility"].sum() == 3181
    assert hev_data["susceptibility_eligibility"].sum() == 3113
    assert hev_data["overall_hev_eligibility"].sum() == 3113

    # Verification against source matrix K_valid >= 4
    expected_eligible = feature_matrix["K_valid"] >= 4
    pd.testing.assert_series_equal(
        hev_data["overall_hev_eligibility"],
        expected_eligible,
        check_names=False,
    )


def test_hazard_bounds_and_finite(hev_data: pd.DataFrame):
    """Test 3: H_i is strictly in [0.0, 1.0] and finite for all eligible cells."""
    eligible = hev_data["hazard_eligibility"]
    h_eligible = hev_data.loc[eligible, "H_i"]

    assert h_eligible.notna().all(), "Found unexpected NaN in eligible Hazard cells"
    assert np.isfinite(h_eligible).all(), "Found non-finite values in eligible Hazard cells"
    assert (h_eligible >= 0.0).all(), "Hazard contains negative values"
    assert (h_eligible <= 1.0).all(), "Hazard exceeds upper bound 1.0"

    # Empirical check on Pune data
    assert 0.05 < h_eligible.min() < 0.15
    assert 0.80 < h_eligible.max() < 0.95
    assert 0.40 < h_eligible.mean() < 0.50


def test_exposure_bounds_and_finite(hev_data: pd.DataFrame):
    """Test 4: E_i is strictly in [0.0, 1.0] and finite across all 3,181 cells."""
    e_all = hev_data["E_i"]

    assert e_all.notna().all(), "Found unexpected NaN in Exposure cells"
    assert np.isfinite(e_all).all(), "Found non-finite values in Exposure cells"
    assert (e_all >= 0.0).all(), "Exposure contains negative values"
    assert (e_all <= 1.0).all(), "Exposure exceeds upper bound 1.0"

    # Empirical check on Pune data
    assert e_all.min() == 0.0
    assert 0.75 < e_all.max() < 0.85
    assert 0.20 < e_all.mean() < 0.25


def test_susceptibility_bounds_and_finite(hev_data: pd.DataFrame):
    """Test 5: V_i is strictly in [0.0, 1.0] and finite for all eligible cells."""
    eligible = hev_data["susceptibility_eligibility"]
    v_eligible = hev_data.loc[eligible, "V_i"]

    assert v_eligible.notna().all(), "Found unexpected NaN in eligible Susceptibility cells"
    assert np.isfinite(v_eligible).all(), "Found non-finite values in eligible Susceptibility cells"
    assert (v_eligible >= 0.0).all(), "Susceptibility contains negative values"
    assert (v_eligible <= 1.0).all(), "Susceptibility exceeds upper bound 1.0"

    # Empirical check on Pune data
    assert 0.05 < v_eligible.min() < 0.15
    assert 0.90 < v_eligible.max() < 1.00
    assert 0.65 < v_eligible.mean() < 0.80


def test_ineligible_cells_strictly_nan(hev_data: pd.DataFrame):
    """Test 6: Ineligible cells (K_valid < 4) must strictly have NaN for H_i and V_i."""
    ineligible = ~hev_data["overall_hev_eligibility"]
    assert ineligible.sum() == 68

    h_ineligible = hev_data.loc[ineligible, "H_i"]
    v_ineligible = hev_data.loc[ineligible, "V_i"]

    assert h_ineligible.isna().all(), "Disqualified cells must NOT have imputed Hazard values"
    assert v_ineligible.isna().all(), "Disqualified cells must NOT have imputed Susceptibility values"


def test_zero_exposure_semantics(hev_data: pd.DataFrame, feature_matrix: pd.DataFrame):
    """Test 7: Zero exposure condition is verified for exactly 1 cell."""
    zero_e = hev_data[hev_data["E_i"] == 0.0]
    assert len(zero_e) == 1, f"Expected exactly 1 zero-exposure cell, found {len(zero_e)}"

    zero_cell_id = zero_e["h3_cell_id"].iloc[0]
    assert zero_cell_id == "89608855343ffff"

    # Verify input components evaluate to 0.0
    src_row = feature_matrix[feature_matrix["h3_cell_id"] == zero_cell_id].iloc[0]
    assert src_row["norm_population"] == 0.0
    assert src_row["norm_population_density"] == 0.0
    assert src_row["norm_civic_infra"] == 0.0
    assert src_row["norm_road_length"] == 0.0


def test_component_directionality(hev_data: pd.DataFrame):
    """Test 8: Component monotonicity / positive directionality."""
    eligible = hev_data["overall_hev_eligibility"]
    df_el = hev_data[eligible]

    # Hazard components have positive correlation with H_i
    assert df_el["H_i"].corr(df_el["norm_lst_2025"]) > 0.60
    assert df_el["H_i"].corr(df_el["norm_persistence"]) > 0.60
    assert df_el["H_i"].corr(df_el["norm_recurrence_ge45"]) > 0.70

    # Exposure components have positive correlation with E_i
    assert hev_data["E_i"].corr(hev_data["norm_population"]) > 0.80
    assert hev_data["E_i"].corr(hev_data["norm_population_density"]) > 0.80
    assert hev_data["E_i"].corr(hev_data["norm_civic_infra"]) > 0.30
    assert hev_data["E_i"].corr(hev_data["norm_road_length"]) > 0.20

    # Susceptibility components have positive correlation with V_i
    assert df_el["V_i"].corr(df_el["norm_ndvi_deficit"]) > 0.80
    assert df_el["V_i"].corr(df_el["norm_ndbi"]) > 0.80


def test_ward_decoupling_mathematical_invariance(feature_matrix: pd.DataFrame):
    """Test 9: H, E, V computations are 100% mathematically invariant to ward_id."""
    df_permuted = feature_matrix.copy()
    # Randomly shuffle ward_id
    df_permuted["ward_id"] = np.random.RandomState(99).permutation(df_permuted["ward_id"].values)

    # Save temporary copy and construct
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        df_permuted.to_parquet(tmp_path, index=False)
        hev_permuted, _ = construct_hev_components(tmp_path)
        canonical_hev = pd.read_parquet(PARQUET_PATH)

        pd.testing.assert_series_equal(canonical_hev["H_i"], hev_permuted["H_i"])
        pd.testing.assert_series_equal(canonical_hev["E_i"], hev_permuted["E_i"])
        pd.testing.assert_series_equal(canonical_hev["V_i"], hev_permuted["V_i"])
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_weight_sum_unity():
    """Test 10: Methodological weights sum strictly to 1.0 in all three dimensions."""
    assert abs(sum(HAZARD_WEIGHTS.values()) - 1.0) < 1e-9
    assert abs(sum(EXPOSURE_WEIGHTS.values()) - 1.0) < 1e-9
    assert abs(sum(SUSCEPTIBILITY_WEIGHTS.values()) - 1.0) < 1e-9


def test_anti_double_counting_boundary_separation():
    """Test 11: Feature names in H, E, and V weight dictionaries are strictly disjoint."""
    h_features = set(HAZARD_WEIGHTS.keys())
    e_features = set(EXPOSURE_WEIGHTS.keys())
    v_features = set(SUSCEPTIBILITY_WEIGHTS.keys())

    assert len(h_features.intersection(e_features)) == 0, "Hazard and Exposure share variables"
    assert len(h_features.intersection(v_features)) == 0, "Hazard and Susceptibility share variables"
    assert len(e_features.intersection(v_features)) == 0, "Exposure and Susceptibility share variables"


def test_contract_manifest_integrity(hev_contract: dict):
    """Test 12: Canonical contract JSON matches materialized parquet."""
    mat = hev_contract["materialized_assets"]
    assert mat["row_count"] == 3181
    assert mat["column_count"] == 19
    assert Path(PROJECT_ROOT / mat["parquet_path"]).exists()
    assert hev_contract["ward_decoupling"]["ward_id_used_in_computation"] is False
    assert hev_contract["weight_governance"]["status"] == "CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)"
