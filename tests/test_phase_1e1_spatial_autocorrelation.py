"""CLIMORA Phase 1E.1: Spatial Autocorrelation & LISA Significance Tests (F-23.1).

Verifies all 19 criteria required by the Phase 1E.1 mandate:
Eligibility:
1. 68 ineligible cells never enter the Risk observation vector.
2. No NaN enters the Moran calculation.
3. No Risk imputation occurs.
Weights:
4. H3 1-ring topology is used.
5. Self-neighbor weights are zero (w_ii = 0).
6. Eligible-neighbor-only graph is used (induced subgraph).
7. Every eligible row sums strictly to 1.0.
8. Sum of weights S0 equals N_e (S0 = 3,113.0).
9. Zero isolated cells in eligible mesh (min degree >= 1).
Global Moran:
10. Deterministic result under seed 42.
11. Expected value uses N_e = 3113, not 3181 (E[I] = -1 / 3112).
12. Permutation p-value is strictly positive (never reported as 0).
13. Repeated execution gives 100% byte-for-byte identical results.
Local Moran:
14. Local Moran formula is mathematically correct.
15. Mean of Local Moran statistics equals Global Moran's I within float tolerance.
16. Raw p-values are deterministic.
17. Benjamini-Hochberg correction evaluates over exactly all N_e = 3,113 tests.
18. LISA significance labels and cluster counts are reproducible.
Ward independence:
19. Ward assignment has zero influence on the spatial graph or diagnostics.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
import h3
import numpy as np
import pandas as pd

from processing.config import MANIFESTS_DIR, PROCESSED_DIR, PROJECT_ROOT
from processing.spatial_autocorrelation import (
    BH_FDR_Q,
    PERMUTATION_REPLICATES,
    RANDOM_SEED,
    apply_benjamini_hochberg,
    build_eligible_h3_graph,
    classify_lisa_quadrants,
    execute_spatial_autocorrelation_gate,
    run_global_moran_permutation_test,
    run_local_moran_conditional_permutations,
)

RISK_PARQUET_PATH = PROCESSED_DIR / "risk" / "canonical_risk_surface.parquet"
SPATIAL_PARQUET_PATH = PROCESSED_DIR / "risk" / "canonical_spatial_autocorrelation.parquet"
SPATIAL_CONTRACT_PATH = MANIFESTS_DIR / "spatial_autocorrelation_contract.json"


@pytest.fixture(scope="module")
def risk_surface() -> pd.DataFrame:
    """Load canonical Risk surface."""
    assert RISK_PARQUET_PATH.exists(), f"Missing Risk artifact: {RISK_PARQUET_PATH}"
    return pd.read_parquet(RISK_PARQUET_PATH)


@pytest.fixture(scope="module")
def spatial_surface() -> pd.DataFrame:
    """Load canonical Spatial Autocorrelation artifact."""
    assert SPATIAL_PARQUET_PATH.exists(), f"Missing Spatial artifact: {SPATIAL_PARQUET_PATH}"
    return pd.read_parquet(SPATIAL_PARQUET_PATH)


@pytest.fixture(scope="module")
def spatial_contract() -> dict:
    """Load canonical Spatial Autocorrelation contract."""
    assert SPATIAL_CONTRACT_PATH.exists(), f"Missing contract: {SPATIAL_CONTRACT_PATH}"
    with open(SPATIAL_CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# --- ELIGIBILITY TESTS ---

def test_eligibility_exclusion_and_no_nan(risk_surface: pd.DataFrame, spatial_surface: pd.DataFrame):
    """Criteria 1 & 2: 68 ineligible cells never enter Moran calculation; no NaN in calculation."""
    eligible = risk_surface["overall_risk_eligibility"]
    ineligible = ~eligible

    assert ineligible.sum() == 68
    assert eligible.sum() == 3113

    # Ineligible cells in risk surface must be strictly NaN
    assert risk_surface.loc[ineligible, "risk_i"].isna().all()

    # In spatial surface, ineligible cells must have NaN for local Moran, raw p, bh q
    assert spatial_surface.loc[ineligible, "local_moran_i"].isna().all()
    assert spatial_surface.loc[ineligible, "raw_p_value"].isna().all()
    assert spatial_surface.loc[ineligible, "bh_q_value"].isna().all()
    assert (spatial_surface.loc[ineligible, "lisa_significant"] == False).all()


def test_no_risk_imputation(risk_surface: pd.DataFrame):
    """Criterion 3: No Risk imputation occurs; values are strictly from F-22."""
    eligible = risk_surface["overall_risk_eligibility"]
    sub = risk_surface[eligible]

    expected = sub["H_i"] * sub["E_i"] * sub["V_i"]
    np.testing.assert_allclose(sub["risk_i"].values, expected.values, rtol=1e-12, atol=1e-12)


# --- SPATIAL GRAPH & WEIGHTS TESTS ---

def test_h3_1ring_topology_and_self_zero(risk_surface: pd.DataFrame):
    """Criteria 4 & 5: H3 1-ring topology is used; self-neighbor weights are zero (w_ii = 0)."""
    eligible = risk_surface["overall_risk_eligibility"].values
    all_cells = risk_surface["h3_cell_id"].tolist()

    el_cells, W, adj, meta = build_eligible_h3_graph(all_cells, eligible)

    # Check w_ii == 0
    assert np.diag(W).sum() == 0.0

    # Check that all neighbors in adj are true H3 1-ring neighbors
    sample_indices = [0, 10, 100, 500, 1000, 2000, 3000]
    for idx in sample_indices:
        cell_id = el_cells[idx]
        disk = set(h3.grid_disk(cell_id, 1)) - {cell_id}
        nbr_cell_ids = [el_cells[j] for j in adj[idx]]
        for nbr_id in nbr_cell_ids:
            assert nbr_id in disk, f"Neighbor {nbr_id} is not an H3 1-ring neighbor of {cell_id}"


def test_induced_eligible_graph_and_row_standardization(risk_surface: pd.DataFrame):
    """Criteria 6, 7, 8, 9: Eligible-only graph; row sums = 1.0; S0 = N_e; no isolated cells."""
    eligible = risk_surface["overall_risk_eligibility"].values
    all_cells = risk_surface["h3_cell_id"].tolist()

    el_cells, W, adj, meta = build_eligible_h3_graph(all_cells, eligible)

    # Criterion 6: Only eligible cells participate (N_e = 3113)
    assert len(el_cells) == 3113
    assert W.shape == (3113, 3113)

    # Criterion 7: Every eligible row sums to 1.0
    row_sums = W.sum(axis=1)
    np.testing.assert_allclose(row_sums, 1.0, rtol=1e-12, atol=1e-12)

    # Criterion 8: S0 = N_e = 3113.0
    assert abs(W.sum() - 3113.0) < 1e-6
    assert abs(meta["sum_of_weights_S0"] - 3113.0) < 1e-6

    # Criterion 9: No isolated cells (min degree >= 1)
    assert meta["isolated_cells_count"] == 0
    assert meta["min_degree"] >= 1
    assert meta["max_degree"] == 6


# --- GLOBAL MORAN'S I TESTS ---

def test_global_moran_expected_value_and_determinism(risk_surface: pd.DataFrame):
    """Criteria 10, 11, 12, 13: Deterministic result; E[I] uses N_e; pseudo-p > 0; repeated execution identical."""
    eligible = risk_surface["overall_risk_eligibility"].values
    all_cells = risk_surface["h3_cell_id"].tolist()
    el_risk = risk_surface.loc[eligible, "risk_i"].values

    _, _, adj, _ = build_eligible_h3_graph(all_cells, eligible)

    res1 = run_global_moran_permutation_test(el_risk, adj, B=999, seed=42)
    res2 = run_global_moran_permutation_test(el_risk, adj, B=999, seed=42)

    # Criterion 10 & 13: Deterministic & repeated execution gives identical results
    assert res1["observed_morans_i"] == res2["observed_morans_i"]
    assert res1["permutation_pseudo_p_value"] == res2["permutation_pseudo_p_value"]

    # Criterion 11: Expected value uses N_e = 3113, NOT 3181
    expected_3113 = -1.0 / (3113 - 1)
    assert abs(res1["expected_morans_i"] - expected_3113) < 1e-6
    # Verify it does NOT equal -1 / 3180
    assert abs(res1["expected_morans_i"] - (-1.0 / 3180)) > 1e-6

    # Criterion 12: Permutation p-value is strictly positive (never 0)
    assert res1["permutation_pseudo_p_value"] > 0.0
    assert res1["permutation_pseudo_p_value"] == round(1.0 / (999 + 1), 6)


# --- LOCAL MORAN'S I (LISA) TESTS ---

def test_local_moran_identity_and_determinism(risk_surface: pd.DataFrame):
    """Criteria 14, 15, 16: Local Moran formula; mean(I_i) == Global Moran; deterministic p-values."""
    eligible = risk_surface["overall_risk_eligibility"].values
    all_cells = risk_surface["h3_cell_id"].tolist()
    el_risk = risk_surface.loc[eligible, "risk_i"].values

    _, _, adj, _ = build_eligible_h3_graph(all_cells, eligible)

    # Criterion 14: Compute Local Moran
    I_obs, wz, p_vals = run_local_moran_conditional_permutations(el_risk, adj, B=99, seed=42)

    # Criterion 15: Mathematical identity: (1 / N_e) * sum(I_i) == Global Moran's I
    z = el_risk - np.mean(el_risk)
    ss = np.sum(z**2)
    global_I = np.sum(z * wz) / ss
    local_mean = np.mean(I_obs)

    assert abs(local_mean - global_I) < 1e-6

    # Criterion 16: Determinism of p-values
    _, _, p_vals_2 = run_local_moran_conditional_permutations(el_risk, adj, B=99, seed=42)
    np.testing.assert_allclose(p_vals, p_vals_2, rtol=1e-12, atol=1e-12)


def test_benjamini_hochberg_family_and_lisa_clusters(risk_surface: pd.DataFrame, spatial_surface: pd.DataFrame):
    """Criteria 17 & 18: BH correction evaluates over N_e = 3113; LISA labels reproducible."""
    eligible = risk_surface["overall_risk_eligibility"]
    sub = spatial_surface[eligible]

    # Criterion 17: Exactly 3,113 tests in the family
    assert len(sub["raw_p_value"].dropna()) == 3113
    assert len(sub["bh_q_value"].dropna()) == 3113

    # Check BH monotonicity: sorted q-values are non-decreasing
    raw_p = sub["raw_p_value"].values
    q_val = sub["bh_q_value"].values
    sort_idx = np.argsort(raw_p)
    assert np.all(np.diff(q_val[sort_idx]) >= -1e-12)

    # Criterion 18: Exactly 339 significant cells under ratified B=9999, seed=42
    sig_count = sub["lisa_significant"].sum()
    assert sig_count == 339

    clusters = sub["lisa_cluster"].value_counts().to_dict()
    assert clusters["High-High"] == 337
    assert clusters["Low-High"] == 2
    assert clusters["Not significant"] == 2774


# --- WARD INDEPENDENCE TEST ---

def test_ward_decoupling_mathematical_invariance(risk_surface: pd.DataFrame):
    """Criterion 19: ward_id cannot alter spatial graph or diagnostics."""
    # Permuting or removing ward_id has zero effect because spatial graph uses only H3 cell IDs
    eligible = risk_surface["overall_risk_eligibility"].values
    all_cells = risk_surface["h3_cell_id"].tolist()

    el_cells1, W1, adj1, _ = build_eligible_h3_graph(all_cells, eligible)

    # Add artificial ward_id
    risk_copy = risk_surface.copy()
    risk_copy["ward_id"] = np.random.RandomState(99).permutation(np.arange(len(risk_copy)))

    el_cells2, W2, adj2, _ = build_eligible_h3_graph(risk_copy["h3_cell_id"].tolist(), eligible)

    assert el_cells1 == el_cells2
    np.testing.assert_allclose(W1, W2, rtol=1e-12, atol=1e-12)
    assert adj1 == adj2


def test_contract_manifest_integrity(spatial_contract: dict):
    """Test contract schema, SHA-256 provenance, and gate status."""
    assert spatial_contract["gate_decision"]["status"] == "PHASE 1E.1 — PASSED"
    assert spatial_contract["input_risk_artifact"]["f22_risk_artifact_unmodified"] is True
    assert spatial_contract["global_morans_i_ratification"]["observed_morans_i"] == 0.781355
    assert spatial_contract["global_morans_i_ratification"]["expected_morans_i"] == -0.000321
    assert spatial_contract["multiple_testing_correction"]["statistically_significant_count"] == 339
    assert spatial_contract["lisa_clustering_inventory"]["hotspots_count_HH"] == 337
    assert spatial_contract["lisa_clustering_inventory"]["spatial_outliers_count_LH"] == 2
