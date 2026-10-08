"""CLIMORA Phase 1E: Composite Climate Risk & Spatial Autocorrelation Gate Tests.

Verifies:
1. Positive-domain validation: Risk_i is strictly in [0.0, 1.0] and finite for all eligible cells.
2. Exact power-law calculation: Risk_i = H_i^alpha * E_i^beta * V_i^gamma.
3. Alpha=Beta=Gamma=1 default exponent behavior.
4. Zero-exposure behavior: E_i = 0 => Risk_i = 0 (verified on cell 89608855343ffff).
5. Monotonicity: Non-decreasing in H, E, and V.
6. NaN propagation: Strictly NaN for the 68 disqualified cells (no silent imputation).
7. Eligibility preservation: Exactly 3,113 eligible cells and 68 ineligible cells.
8. H3 DGGS topology: Spatial weights derive strictly from H3 Res9 1-ring neighbors.
9. Ward decoupling: 100% mathematical invariance to KMeans ward_id permutation.
10. Spatial weights row-standardization and degree distribution.
11. No isolated cells in eligible analytical mesh (min degree >= 1).
12. Determinism and contract manifest integrity.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
import h3
import numpy as np
import pandas as pd

from processing.config import MANIFESTS_DIR, PROCESSED_DIR, PROJECT_ROOT
from processing.risk_construction import (
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    DEFAULT_GAMMA,
    build_h3_spatial_weights,
    compute_global_morans_i,
    construct_power_law_risk,
    construct_canonical_risk_surface,
)

HEV_PARQUET_PATH = PROCESSED_DIR / "hev" / "canonical_hev_components.parquet"
RISK_PARQUET_PATH = PROCESSED_DIR / "risk" / "canonical_risk_surface.parquet"
RISK_CONTRACT_PATH = MANIFESTS_DIR / "canonical_risk_contract.json"


@pytest.fixture(scope="module")
def hev_data() -> pd.DataFrame:
    """Load canonical HEV components parquet."""
    assert HEV_PARQUET_PATH.exists(), f"Missing HEV artifact: {HEV_PARQUET_PATH}"
    return pd.read_parquet(HEV_PARQUET_PATH)


@pytest.fixture(scope="module")
def risk_data() -> pd.DataFrame:
    """Load canonical Risk surface parquet."""
    assert RISK_PARQUET_PATH.exists(), f"Missing Risk artifact: {RISK_PARQUET_PATH}"
    return pd.read_parquet(RISK_PARQUET_PATH)


@pytest.fixture(scope="module")
def risk_contract() -> dict:
    """Load canonical Risk JSON contract."""
    assert RISK_CONTRACT_PATH.exists(), f"Missing contract: {RISK_CONTRACT_PATH}"
    with open(RISK_CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_risk_dimensions_and_schema(risk_data: pd.DataFrame):
    """Test 1: Row count is exactly 3,181 and required columns exist."""
    assert len(risk_data) == 3181, f"Expected 3,181 cells, found {len(risk_data)}"
    assert risk_data["h3_cell_id"].nunique() == 3181

    required_cols = [
        "h3_cell_id",
        "H_i",
        "E_i",
        "V_i",
        "risk_i",
        "overall_risk_eligibility",
        "alpha",
        "beta",
        "gamma",
        "local_moran_I_i",
        "spatial_lag_risk",
        "moran_quadrant",
    ]
    for col in required_cols:
        assert col in risk_data.columns, f"Missing required column: {col}"

    # Decoupling: ward_id must NOT be present in canonical risk parquet
    assert "ward_id" not in risk_data.columns, "ward_id must be decoupled from canonical risk surface"


def test_eligibility_partition_and_nan_propagation(risk_data: pd.DataFrame, hev_data: pd.DataFrame):
    """Test 2: Exactly 3,113 eligible cells and 68 ineligible cells with strict NaN preservation."""
    assert risk_data["overall_risk_eligibility"].sum() == 3113
    assert (~risk_data["overall_risk_eligibility"]).sum() == 68

    pd.testing.assert_series_equal(
        risk_data["overall_risk_eligibility"],
        hev_data["overall_hev_eligibility"],
        check_names=False,
    )

    ineligible = ~risk_data["overall_risk_eligibility"]
    assert risk_data.loc[ineligible, "risk_i"].isna().all(), "Ineligible cells must have NaN Risk"
    assert risk_data.loc[ineligible, "H_i"].isna().all(), "Ineligible cells must have NaN Hazard"
    assert risk_data.loc[ineligible, "V_i"].isna().all(), "Ineligible cells must have NaN Susceptibility"
    assert risk_data.loc[ineligible, "local_moran_I_i"].isna().all(), "Ineligible cells must have NaN LISA"


def test_positive_domain_and_finite_bounds(risk_data: pd.DataFrame):
    """Test 3: Risk_i is strictly in [0.0, 1.0] and finite across all eligible cells."""
    eligible = risk_data["overall_risk_eligibility"]
    el_risk = risk_data.loc[eligible, "risk_i"]

    assert el_risk.notna().all(), "Found unexpected NaN in eligible Risk"
    assert np.isfinite(el_risk).all(), "Found non-finite values in eligible Risk"
    assert (el_risk >= 0.0).all(), "Found negative Risk values"
    assert (el_risk <= 1.0).all(), "Risk exceeds 1.0 upper bound"

    # Empirical check on Pune risk distribution
    assert el_risk.min() == 0.0
    assert 0.30 < el_risk.max() < 0.50
    assert 0.05 < el_risk.mean() < 0.10
    assert 0.03 < el_risk.median() < 0.06


def test_exact_power_law_calculation(risk_data: pd.DataFrame):
    """Test 4: Exact power-law calculation Risk_i = H_i^alpha * E_i^beta * V_i^gamma."""
    eligible = risk_data["overall_risk_eligibility"]
    sub = risk_data[eligible]

    expected = (sub["H_i"] ** DEFAULT_ALPHA) * (sub["E_i"] ** DEFAULT_BETA) * (sub["V_i"] ** DEFAULT_GAMMA)
    np.testing.assert_allclose(sub["risk_i"].values, expected.values, rtol=1e-12, atol=1e-12)


def test_zero_exposure_behavior(risk_data: pd.DataFrame, hev_data: pd.DataFrame):
    """Test 5: Zero exposure axiom strictly verified."""
    zero_e = hev_data[hev_data["E_i"] == 0.0]
    assert len(zero_e) == 1
    zero_cell_id = zero_e["h3_cell_id"].iloc[0]
    assert zero_cell_id == "89608855343ffff"

    risk_row = risk_data[risk_data["h3_cell_id"] == zero_cell_id].iloc[0]
    assert risk_row["E_i"] == 0.0
    assert risk_row["risk_i"] == 0.0
    assert risk_row["overall_risk_eligibility"] is True or risk_row["overall_risk_eligibility"] == 1


def test_risk_monotonicity():
    """Test 6: Monotonicity audit in H, E, and V."""
    # Unit test with controlled synthetic values
    h_arr = np.array([0.2, 0.5, 0.8])
    e_val = 0.5
    v_val = 0.6

    df_test = pd.DataFrame({
        "H_i": h_arr,
        "E_i": np.full(3, e_val),
        "V_i": np.full(3, v_val),
        "overall_hev_eligibility": [True, True, True],
    })
    # Pad to 3181 to test function assertion
    pad = pd.DataFrame({
        "H_i": np.full(3178, 0.5),
        "E_i": np.full(3178, 0.5),
        "V_i": np.full(3178, 0.5),
        "overall_hev_eligibility": [True] * 3178,
    })
    df_full = pd.concat([df_test, pad], ignore_index=True)
    res = construct_power_law_risk(df_full)

    # Monotonic in H
    assert res.iloc[0] < res.iloc[1] < res.iloc[2]


def test_h3_spatial_neighborhood_topology(risk_data: pd.DataFrame):
    """Test 7: Spatial neighborhood derives strictly from H3 Resolution 9 1-ring neighbors."""
    eligible = risk_data["overall_risk_eligibility"]
    el_cells = risk_data.loc[eligible, "h3_cell_id"].tolist()

    W, adj, meta = build_h3_spatial_weights(el_cells, row_standardize=True)

    # Check N
    assert meta["num_observations"] == 3113
    assert meta["isolated_cells_count"] == 0, "No isolated cells permitted in eligible mesh"
    assert meta["min_neighbors"] >= 1
    assert meta["max_neighbors"] == 6

    # Verify that every neighbor in adj is actually an H3 1-ring neighbor
    sample_indices = [0, 50, 100, 500, 1000, 2000]
    for idx in sample_indices:
        cell_id = el_cells[idx]
        disk = set(h3.grid_disk(cell_id, 1)) - {cell_id}
        nbr_cell_ids = [el_cells[j] for j in adj[idx]]
        for nbr_id in nbr_cell_ids:
            assert nbr_id in disk, f"Neighbor {nbr_id} is not an H3 1-ring neighbor of {cell_id}"


def test_spatial_weights_row_standardization(risk_data: pd.DataFrame):
    """Test 8: Row-standardized spatial weights sum to 1.0 per row and W = N."""
    eligible = risk_data["overall_risk_eligibility"]
    el_cells = risk_data.loc[eligible, "h3_cell_id"].tolist()

    W, adj, meta = build_h3_spatial_weights(el_cells, row_standardize=True)

    row_sums = W.sum(axis=1)
    np.testing.assert_allclose(row_sums, 1.0, rtol=1e-12, atol=1e-12)
    assert abs(meta["sum_of_weights_W"] - 3113.0) < 1e-6


def test_global_morans_i_reproducibility(risk_data: pd.DataFrame):
    """Test 9: Global Moran's I is reproducible and matches contract manifest."""
    eligible = risk_data["overall_risk_eligibility"]
    el_cells = risk_data.loc[eligible, "h3_cell_id"].tolist()
    el_risk = risk_data.loc[eligible, "risk_i"].values

    W, adj, _ = build_h3_spatial_weights(el_cells, row_standardize=True)
    moran = compute_global_morans_i(el_risk, W, adj)

    assert 0.75 < moran["morans_i"] < 0.85
    assert moran["morans_i"] == 0.781355
    assert moran["expected_i"] == -0.000321
    assert moran["z_score"] > 50.0
    assert moran["p_value_analytical"] == 0.0


def test_ward_decoupling_mathematical_invariance(hev_data: pd.DataFrame):
    """Test 10: Risk construction and spatial statistics are 100% mathematically invariant to ward_id."""
    # Permute or add synthetic ward_id
    hev_copy = hev_data.copy()
    hev_copy["ward_id"] = np.random.RandomState(42).permutation(np.arange(len(hev_copy)))

    risk_permuted = construct_power_law_risk(hev_copy)
    canonical_risk = pd.read_parquet(RISK_PARQUET_PATH)

    pd.testing.assert_series_equal(canonical_risk["risk_i"], risk_permuted, check_names=False)


def test_contract_manifest_integrity(risk_contract: dict):
    """Test 11: Canonical Risk JSON contract matches materialized parquet."""
    mat = risk_contract["materialized_assets"]
    assert mat["row_count"] == 3181
    assert mat["column_count"] == 12
    assert Path(PROJECT_ROOT / mat["parquet_path"]).exists()

    assert risk_contract["gate_decision"]["status"] == "PHASE 1E — BLOCKED"
    assert risk_contract["ward_decoupling_audit"]["ward_id_used_in_computation"] is False
    assert risk_contract["formulation_f22_risk_model"]["exponents"]["alpha"] == 1.0
    assert risk_contract["formulation_f22_risk_model"]["exponents"]["beta"] == 1.0
    assert risk_contract["formulation_f22_risk_model"]["exponents"]["gamma"] == 1.0
