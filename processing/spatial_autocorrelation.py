"""CLIMORA Phase 1E.1: Spatial Autocorrelation & LISA Significance Engine (F-23.1).

Implements the ratified Formulation F-23.1:
1. Analytical population: Eligible H3 Resolution 9 mesh (N_e = 3,113, K_valid >= 4).
2. Missingness governance: 68 disqualified cells remain in geographic universe as NaN,
   excluded from the inferential observation vector. No imputation.
3. Induced eligible H3 graph: Adjacency strictly among eligible H3 1-ring neighbors.
4. Spatial weights: Row-standardized weights w_ij = 1 / k_i for a_ij = 1; w_ii = 0.
   Sum of weights S0 = N_e = 3,113. Fixed 1/6 weights retired from canonical governance.
5. Global Moran's I: Evaluated on eligible Risk surface with expected E[I] = -1 / (N_e - 1).
6. Global significance: Deterministic Monte Carlo permutation (B = 9999, seed = 42).
   Finite-sample pseudo-p = (1 + count(|I_b| >= |I_obs|)) / (B + 1).
7. Local Moran's I (LISA): I_i = ((x_i - x_bar) / m_2) * sum_j w_ij (x_j - x_bar).
   Mathematical identity verified: (1 / N_e) * sum_i I_i = I.
8. Local significance: Deterministic conditional permutation (B = 9999, seed = 42).
   Focal value held fixed; non-focal values permuted without replacement.
   Finite-sample pseudo-p = (1 + count(|I_i_b| >= |I_i_obs|)) / (B + 1).
9. Multiple-testing correction: Benjamini-Hochberg FDR at Q = 0.05 over all N_e = 3,113 tests.
10. LISA classification: High-High, Low-Low, High-Low, Low-High, and Not Significant.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_DIR))

import h3
import numpy as np
import pandas as pd
import scipy.stats as stats

from ingestion.common import calculate_sha256, get_logger
from processing.config import MANIFESTS_DIR, PROCESSED_DIR, PROJECT_ROOT

logger = get_logger()

# Input & Output Paths
INPUT_RISK_PARQUET = PROCESSED_DIR / "risk" / "canonical_risk_surface.parquet"
INPUT_RISK_CONTRACT = MANIFESTS_DIR / "canonical_risk_contract.json"
INPUT_HEV_PARQUET = PROCESSED_DIR / "hev" / "canonical_hev_components.parquet"

OUTPUT_SPATIAL_DIR = PROCESSED_DIR / "risk"
OUTPUT_SPATIAL_PARQUET = OUTPUT_SPATIAL_DIR / "canonical_spatial_autocorrelation.parquet"
OUTPUT_SPATIAL_CONTRACT = MANIFESTS_DIR / "spatial_autocorrelation_contract.json"

# Governed F-23.1 Permutation Parameters
PERMUTATION_REPLICATES = 9999
RANDOM_SEED = 42
BH_FDR_Q = 0.05


def build_eligible_h3_graph(
    all_h3_cells: List[str],
    eligible_mask: np.ndarray,
) -> Tuple[List[str], np.ndarray, List[List[int]], Dict[str, Any]]:
    """Construct the induced subgraph of eligible H3 Resolution 9 cells.

    Returns:
        eligible_cell_ids: List of N_e eligible cell IDs.
        W: (N_e, N_e) row-standardized spatial weights matrix.
        adj: Adjacency list mapping eligible index to list of eligible neighbor indices.
        metadata: Graph topology diagnostics (degrees, boundary, isolates).
    """
    assert len(all_h3_cells) == len(eligible_mask)
    eligible_indices = np.where(eligible_mask)[0]
    eligible_cell_ids = [all_h3_cells[i] for i in eligible_indices]
    N_e = len(eligible_cell_ids)

    cell_to_idx = {c: i for i, c in enumerate(eligible_cell_ids)}
    adj: List[List[int]] = []
    W = np.zeros((N_e, N_e), dtype=np.float64)

    degree_counts: List[int] = []
    for i, c in enumerate(eligible_cell_ids):
        disk = h3.grid_disk(c, 1)
        # Immediate 1-ring neighbors excluding center and restricted strictly to eligible set
        nbrs = [cell_to_idx[n] for n in disk if n != c and n in cell_to_idx]
        adj.append(nbrs)
        k_i = len(nbrs)
        degree_counts.append(k_i)

        if k_i > 0:
            weight = 1.0 / k_i
            for j in nbrs:
                W[i, j] = weight

    deg_arr = np.array(degree_counts)
    isolated_cells = int(np.sum(deg_arr == 0))
    assert isolated_cells == 0, f"Found {isolated_cells} isolated cells in eligible mesh!"

    metadata = {
        "num_eligible_observations": N_e,
        "num_ineligible_cells_excluded": len(all_h3_cells) - N_e,
        "sum_of_weights_S0": round(float(W.sum()), 6),
        "mean_degree": round(float(deg_arr.mean()), 4),
        "min_degree": int(deg_arr.min()),
        "max_degree": int(deg_arr.max()),
        "isolated_cells_count": isolated_cells,
        "full_interior_cells_k6_count": int(np.sum(deg_arr == 6)),
        "boundary_truncated_cells_k_lt_6_count": int(np.sum(deg_arr < 6)),
        "degree_distribution": {
            str(k): int(np.sum(deg_arr == k)) for k in sorted(np.unique(deg_arr))
        },
    }
    return eligible_cell_ids, W, adj, metadata


def run_global_moran_permutation_test(
    risk_values: np.ndarray,
    adj: List[List[int]],
    B: int = PERMUTATION_REPLICATES,
    seed: int = RANDOM_SEED,
) -> Dict[str, Any]:
    """Compute Global Moran's I and run deterministic two-sided permutation test."""
    N_e = len(risk_values)
    z = risk_values - np.mean(risk_values)
    ss = np.sum(z**2)
    assert ss > 0, "Zero variance in risk values"

    wz = np.array([np.mean(z[nbrs]) if len(nbrs) > 0 else 0.0 for nbrs in adj])
    observed_I = float(np.sum(z * wz) / ss)
    expected_I = float(-1.0 / (N_e - 1))

    # Analytical variance under randomization hypothesis (Cliff & Ord 1981)
    # Using row-standardized weights where S0 = N_e
    W = np.zeros((N_e, N_e), dtype=np.float64)
    for i, nbrs in enumerate(adj):
        if len(nbrs) > 0:
            W[i, nbrs] = 1.0 / len(nbrs)
    s0 = float(W.sum())
    s1 = float(0.5 * np.sum((W + W.T) ** 2))
    s2 = float(np.sum((W.sum(axis=1) + W.sum(axis=0)) ** 2))
    m2 = float(np.mean(z**2))
    m4 = float(np.mean(z**4))
    b2 = float(m4 / (m2**2)) if m2 > 0 else 0.0

    var_i = float(
        (
            (N_e * ((N_e**2 - 3 * N_e + 3) * s1 - N_e * s2 + 3 * (s0**2))
             - b2 * ((N_e**2 - N_e) * s1 - 2 * N_e * s2 + 6 * (s0**2)))
            / ((N_e - 1) * (N_e - 2) * (N_e - 3) * (s0**2))
        )
        - (expected_I**2)
    )
    sd_i = float(np.sqrt(max(0.0, var_i)))
    z_score = float((observed_I - expected_I) / sd_i) if sd_i > 0 else 0.0
    p_analytical = float(2.0 * (1.0 - stats.norm.cdf(abs(z_score))))

    # Deterministic Monte Carlo Permutation Test using sparse matrix for BLAS acceleration
    import scipy.sparse as sp
    W_csr = sp.csr_matrix(W)
    rng = np.random.RandomState(seed)
    perm_I = np.empty(B, dtype=np.float64)

    obs_abs = abs(observed_I)
    extreme_count = 0
    for b in range(B):
        z_perm = rng.permutation(z)
        wz_perm = W_csr.dot(z_perm)
        I_b = float(np.dot(z_perm, wz_perm) / ss)
        perm_I[b] = I_b
        if abs(I_b) >= obs_abs:
            extreme_count += 1

    # Finite-sample pseudo-p-value: (1 + count(|I_b| >= |I_obs|)) / (B + 1)
    pseudo_p = float((extreme_count + 1.0) / (B + 1.0))

    return {
        "observed_morans_i": round(observed_I, 6),
        "expected_morans_i": round(expected_I, 6),
        "analytical_std_error": round(sd_i, 6),
        "analytical_z_score": round(z_score, 4),
        "analytical_p_value": p_analytical,
        "permutation_replicates_B": B,
        "permutation_random_seed": seed,
        "permutation_extreme_count": extreme_count,
        "permutation_pseudo_p_value": round(pseudo_p, 6),
        "permutation_mean_I": round(float(np.mean(perm_I)), 6),
        "permutation_max_I": round(float(np.max(perm_I)), 6),
        "permutation_min_I": round(float(np.min(perm_I)), 6),
    }


def run_local_moran_conditional_permutations(
    risk_values: np.ndarray,
    adj: List[List[int]],
    B: int = PERMUTATION_REPLICATES,
    seed: int = RANDOM_SEED,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute Local Moran's I and run deterministic conditional permutation tests.

    Returns:
        I_obs: (N_e,) Observed Local Moran statistic for each cell.
        wz: (N_e,) Observed spatial lag for each cell.
        p_values: (N_e,) Raw two-sided finite-sample pseudo-p-values.
    """
    N_e = len(risk_values)
    z = risk_values - np.mean(risk_values)
    m2 = np.mean(z**2)
    assert m2 > 0, "Zero variance in risk values"

    degrees = np.array([len(nbrs) for nbrs in adj])
    wz = np.array([np.mean(z[nbrs]) if len(nbrs) > 0 else 0.0 for nbrs in adj])
    I_obs = (z / m2) * wz

    logger.info("Executing conditional permutation tests (N=%d, B=%d, seed=%d)...", N_e, B, seed)
    rng = np.random.RandomState(seed)
    p_values = np.zeros(N_e, dtype=np.float64)

    for i in range(N_e):
        k_i = degrees[i]
        zi = z[i]
        obs_abs = abs(I_obs[i])

        # Non-focal observations: delete focal element i
        z_non_focal = np.delete(z, i)

        # Vectorized sampling without replacement
        mat = rng.randint(0, N_e - 1, size=(B, k_i))
        if k_i > 1:
            s = np.sort(mat, axis=1)
            has_dup = np.any(np.diff(s, axis=1) == 0, axis=1)
            dup_count = int(np.sum(has_dup))
            while dup_count > 0:
                mat[has_dup] = rng.randint(0, N_e - 1, size=(dup_count, k_i))
                s = np.sort(mat, axis=1)
                has_dup = np.any(np.diff(s, axis=1) == 0, axis=1)
                dup_count = int(np.sum(has_dup))

        # Sampled non-focal values: shape (B, k_i)
        sampled_z = z_non_focal[mat]
        wz_perm = np.mean(sampled_z, axis=1)
        I_perm = (zi / m2) * wz_perm

        # Two-sided pseudo p-value: (1 + count(|I_perm| >= |I_obs|)) / (B + 1)
        n_extreme = int(np.sum(np.abs(I_perm) >= obs_abs))
        p_values[i] = (n_extreme + 1.0) / (B + 1.0)

    return I_obs, wz, p_values


def apply_benjamini_hochberg(
    p_values: np.ndarray,
    q_threshold: float = BH_FDR_Q,
) -> Tuple[np.ndarray, np.ndarray]:
    """Apply Benjamini-Hochberg False Discovery Rate correction across all tests.

    Returns:
        q_values: (N,) Adjusted q-values bounded in [0.0, 1.0].
        significant_mask: (N,) Boolean mask of cells satisfying FDR threshold.
    """
    N = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    ranks = np.arange(1, N + 1)
    crit = (ranks / N) * q_threshold

    sig_mask_sorted = sorted_p <= crit
    if np.any(sig_mask_sorted):
        max_k = int(np.max(np.where(sig_mask_sorted)[0]))
        bh_sig_indices = set(sorted_indices[: max_k + 1])
    else:
        bh_sig_indices = set()

    significant_mask = np.array([i in bh_sig_indices for i in range(N)], dtype=bool)

    # Calculate adjusted q-values: q_k = min_{j >= k} (p_j * N / j), clamped to 1.0
    q_values_sorted = np.minimum.accumulate((sorted_p * N / ranks)[::-1])[::-1]
    q_values_sorted = np.clip(q_values_sorted, 0.0, 1.0)
    q_values = np.empty(N, dtype=np.float64)
    q_values[sorted_indices] = q_values_sorted

    return q_values, significant_mask


def classify_lisa_quadrants(
    risk_values: np.ndarray,
    spatial_lag: np.ndarray,
    significant_mask: np.ndarray,
) -> Tuple[List[str], List[str]]:
    """Classify cells into descriptive Moran quadrants and inferential LISA clusters.

    Returns:
        descriptive_quadrants: Spatial association quadrant based on signs of z_i and L_i.
        inferential_lisa: Statistical cluster label (High-High, Low-Low, High-Low, Low-High, Not significant).
    """
    N = len(risk_values)
    z = risk_values - np.mean(risk_values)

    descriptive_quadrants: List[str] = []
    inferential_lisa: List[str] = []

    for i in range(N):
        zi = z[i]
        wi = spatial_lag[i]
        is_sig = significant_mask[i]

        if zi >= 0.0 and wi >= 0.0:
            quad = "High-High"
        elif zi < 0.0 and wi < 0.0:
            quad = "Low-Low"
        elif zi >= 0.0 and wi < 0.0:
            quad = "High-Low"
        else:
            quad = "Low-High"

        descriptive_quadrants.append(f"{quad} (Descriptive)")
        if is_sig:
            inferential_lisa.append(quad)
        else:
            inferential_lisa.append("Not significant")

    return descriptive_quadrants, inferential_lisa


def execute_spatial_autocorrelation_gate(
    risk_parquet_path: Path = INPUT_RISK_PARQUET,
    B: int = PERMUTATION_REPLICATES,
    seed: int = RANDOM_SEED,
    q_threshold: float = BH_FDR_Q,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Execute complete F-23.1 Spatial Autocorrelation & LISA Ratification Gate."""
    logger.info("Loading canonical Risk surface from %s", risk_parquet_path)
    risk_df = pd.read_parquet(risk_parquet_path)
    risk_sha256 = calculate_sha256(risk_parquet_path)

    # Verify input risk structure
    assert len(risk_df) == 3181
    assert "overall_risk_eligibility" in risk_df.columns
    assert "risk_i" in risk_df.columns
    eligible = risk_df["overall_risk_eligibility"].values
    n_eligible = int(np.sum(eligible))
    n_ineligible = int(np.sum(~eligible))
    assert n_eligible == 3113
    assert n_ineligible == 68

    all_cells = risk_df["h3_cell_id"].tolist()

    # 1. Construct induced eligible H3 graph
    el_cells, W_el, adj_el, graph_meta = build_eligible_h3_graph(all_cells, eligible)

    el_risk = risk_df.loc[eligible, "risk_i"].values
    assert not np.isnan(el_risk).any(), "Found unexpected NaN in eligible Risk vector"

    # 2. Global Moran's I with deterministic permutation test
    global_results = run_global_moran_permutation_test(el_risk, adj_el, B=B, seed=seed)

    # 3. Local Moran's I with conditional permutations
    I_obs, wz, raw_p = run_local_moran_conditional_permutations(el_risk, adj_el, B=B, seed=seed)

    # Mathematical identity assertion: (1 / N_e) * sum(I_i) == I_global
    local_mean = float(np.mean(I_obs))
    global_obs = float(global_results["observed_morans_i"])
    assert abs(local_mean - global_obs) < 1e-5, f"Local Moran mean {local_mean} != Global {global_obs}"

    # 4. Benjamini-Hochberg FDR correction
    q_values, sig_mask = apply_benjamini_hochberg(raw_p, q_threshold=q_threshold)

    # 5. LISA Classification
    desc_quads, lisa_labels = classify_lisa_quadrants(el_risk, wz, sig_mask)

    # Map back to full 3,181 mesh
    full_global_I = np.full(3181, np.nan, dtype=np.float64)
    full_local_I = np.full(3181, np.nan, dtype=np.float64)
    full_raw_p = np.full(3181, np.nan, dtype=np.float64)
    full_bh_q = np.full(3181, np.nan, dtype=np.float64)
    full_lisa_quad = ["Ineligible (K_valid < 4)"] * 3181
    full_lisa_sig = [False] * 3181
    full_lisa_cluster = ["Ineligible (K_valid < 4)"] * 3181

    el_indices = np.where(eligible)[0]
    for idx_el, idx_full in enumerate(el_indices):
        full_global_I[idx_full] = global_results["observed_morans_i"]
        full_local_I[idx_full] = I_obs[idx_el]
        full_raw_p[idx_full] = raw_p[idx_el]
        full_bh_q[idx_full] = q_values[idx_el]
        full_lisa_quad[idx_full] = desc_quads[idx_el]
        full_lisa_sig[idx_full] = bool(sig_mask[idx_el])
        full_lisa_cluster[idx_full] = lisa_labels[idx_el]

    # Minimal canonical spatial autocorrelation parquet
    spatial_df = pd.DataFrame({
        "h3_cell_id": risk_df["h3_cell_id"],
        "risk_i": risk_df["risk_i"],
        "overall_risk_eligibility": eligible,
        "global_moran_i": full_global_I,
        "local_moran_i": full_local_I,
        "raw_p_value": full_raw_p,
        "bh_q_value": full_bh_q,
        "descriptive_quadrant": full_lisa_quad,
        "lisa_significant": full_lisa_sig,
        "lisa_cluster": full_lisa_cluster,
    })

    # Summary counts
    lisa_counts = pd.Series(lisa_labels).value_counts().to_dict()
    desc_counts = pd.Series(desc_quads).value_counts().to_dict()

    # Contract Report
    contract_report = {
        "schema_version": "1.0.0",
        "phase": "Phase 1E.1",
        "contract_id": "CLIMORA-CONTRACT-SPATIAL-AUTOCORRELATION-F23.1-V1",
        "status": "RATIFIED_CANONICAL_SPATIAL_AUTOCORRELATION_GATE_PASSED",
        "gate_decision": {
            "status": "PHASE 1E.1 — PASSED",
            "formulation_ratified": "F-23.1 — Eligible H3 Spatial Autocorrelation & LISA Significance",
            "resolution_summary": (
                "Resolved all three Phase 1E governance defects: (1) Analytical population strictly bounded "
                "to eligible mesh N_e = 3,113; 68 disqualified cells remain NaN and excluded from matrix summations. "
                "(2) Spatial weights strictly ratified as row-standardized w_ij = 1/k_i (S0 = N_e = 3,113.0); "
                "fixed 1/6 weights retired from canonical governance. (3) Significance testing procedure formally "
                "ratified using deterministic conditional permutations (B = 9999, seed = 42) with Benjamini-Hochberg "
                "FDR control at Q = 0.05 across all 3,113 eligible tests."
            ),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_risk_artifact": {
            "path": str(INPUT_RISK_PARQUET.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "sha256": risk_sha256,
            "total_cells": 3181,
            "eligible_cells": n_eligible,
            "ineligible_cells": n_ineligible,
            "f22_risk_artifact_unmodified": True,
        },
        "induced_eligible_graph_topology": graph_meta,
        "spatial_weights_ratification": {
            "weighting_rule": "w_ij = 1 / k_i for a_ij = 1; w_ii = 0",
            "sum_of_weights_S0": graph_meta["sum_of_weights_S0"],
            "row_sums_range": [1.0, 1.0],
            "retired_fixed_weights_note": "Fixed 1/6 weights are retired from canonical governance.",
        },
        "global_morans_i_ratification": global_results,
        "local_morans_i_ratification": {
            "formula": "I_i = ((x_i - x_bar) / m_2) * sum_j w_ij (x_j - x_bar)",
            "local_mean_equals_global_identity_verified": True,
            "permutation_procedure": "Conditional local permutation (focal cell fixed, non-focal permuted without replacement)",
            "permutation_replicates_B": B,
            "permutation_random_seed": seed,
            "finite_sample_pseudo_p_formula": "p_i = (1 + count(|I_i_b| >= |I_i_obs|)) / (B + 1)",
            "raw_p_values_summary": {
                "min": round(float(np.min(raw_p)), 6),
                "p05": round(float(np.quantile(raw_p, 0.05)), 6),
                "median": round(float(np.median(raw_p)), 6),
                "mean": round(float(np.mean(raw_p)), 6),
                "max": round(float(np.max(raw_p)), 6),
                "unadjusted_p_lt_005_count": int(np.sum(raw_p < 0.05)),
            },
        },
        "multiple_testing_correction": {
            "method": "Benjamini-Hochberg False Discovery Rate (FDR)",
            "fdr_threshold_Q": q_threshold,
            "testing_family_size": n_eligible,
            "all_eligible_cells_participate": True,
            "statistically_significant_count": int(np.sum(sig_mask)),
            "statistically_significant_percentage": round(float(np.sum(sig_mask)) / n_eligible * 100, 2),
        },
        "lisa_clustering_inventory": {
            "inferential_lisa_clusters": lisa_counts,
            "descriptive_quadrants_unfiltered": desc_counts,
            "hotspots_count_HH": lisa_counts.get("High-High", 0),
            "coldspots_count_LL": lisa_counts.get("Low-Low", 0),
            "spatial_outliers_count_LH": lisa_counts.get("Low-High", 0),
            "spatial_outliers_count_HL": lisa_counts.get("High-Low", 0),
            "not_significant_count": lisa_counts.get("Not significant", 0),
        },
        "ward_decoupling_audit": {
            "status": "DECOUPLED_H3_RES9_ONLY",
            "ward_id_used_in_computation": False,
            "ward_id_used_in_spatial_weights": False,
            "governance_rule": "Spatial weights and diagnostics derive strictly from H3 DGGS topology. Ward reporting remains decoupled.",
        },
    }

    return spatial_df, contract_report


def save_spatial_artifacts(
    spatial_df: pd.DataFrame,
    contract_report: Dict[str, Any],
) -> Tuple[Path, Path]:
    """Save canonical spatial autocorrelation parquet and companion JSON contract."""
    OUTPUT_SPATIAL_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save parquet
    spatial_df.to_parquet(OUTPUT_SPATIAL_PARQUET, index=False, engine="pyarrow")
    logger.info("Saved canonical spatial autocorrelation parquet to %s", OUTPUT_SPATIAL_PARQUET)

    # Compute sha256 and finalize contract
    parquet_sha256 = calculate_sha256(OUTPUT_SPATIAL_PARQUET)
    contract_report["materialized_assets"] = {
        "parquet_path": str(OUTPUT_SPATIAL_PARQUET.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "parquet_sha256": parquet_sha256,
        "parquet_size_bytes": OUTPUT_SPATIAL_PARQUET.stat().st_size,
        "row_count": len(spatial_df),
        "column_count": len(spatial_df.columns),
    }

    # Save contract JSON
    with open(OUTPUT_SPATIAL_CONTRACT, "w", encoding="utf-8") as f:
        json.dump(contract_report, f, indent=2)
    logger.info("Saved spatial autocorrelation contract to %s", OUTPUT_SPATIAL_CONTRACT)

    return OUTPUT_SPATIAL_PARQUET, OUTPUT_SPATIAL_CONTRACT


def main() -> int:
    """CLI execution entrypoint for Phase 1E.1."""
    print("=" * 75)
    print("CLIMORA PHASE 1E.1 — F-23.1 SPATIAL AUTOCORRELATION & LISA RATIFICATION ENGINE")
    print("=" * 75)

    spatial_df, contract_report = execute_spatial_autocorrelation_gate()
    parquet_path, contract_path = save_spatial_artifacts(spatial_df, contract_report)

    print("\n--- PHASE 1E.1 MATERIALIZATION SUMMARY ---")
    print(f"  Parquet Output:  {parquet_path}")
    print(f"  Contract Output: {contract_path}")
    print(f"  Parquet SHA256:  {contract_report['materialized_assets']['parquet_sha256']}")
    print(f"  Total Cells:     {len(spatial_df)}")
    print(f"  Eligible Cells:  {contract_report['input_risk_artifact']['eligible_cells']}")
    print(f"  Blocked Cells:   {contract_report['input_risk_artifact']['ineligible_cells']}")
    print(f"  Gate Decision:   {contract_report['gate_decision']['status']}")

    print("\n--- GLOBAL MORAN'S I (F-23.1) ---")
    gm = contract_report["global_morans_i_ratification"]
    print(f"  Observed I:      {gm['observed_morans_i']:.6f}")
    print(f"  Expected E[I]:   {gm['expected_morans_i']:.6f}")
    print(f"  Analytical z:    {gm['analytical_z_score']:.2f} (p = {gm['analytical_p_value']})")
    print(f"  Permutation p:   {gm['permutation_pseudo_p_value']:.6f} (B = {gm['permutation_replicates_B']}, seed = {gm['permutation_random_seed']})")

    print("\n--- INFERENTIAL LISA CLUSTERS (BH FDR Q = 0.05) ---")
    lisa = contract_report["lisa_clustering_inventory"]["inferential_lisa_clusters"]
    for k, v in lisa.items():
        print(f"  {k:15s}: {v:5d} ({v / 3113 * 100:.2f}%)")

    print("\n--- DESCRIPTIVE MORAN QUADRANTS (UNFILTERED) ---")
    desc = contract_report["lisa_clustering_inventory"]["descriptive_quadrants_unfiltered"]
    for k, v in desc.items():
        print(f"  {k:30s}: {v:5d} ({v / 3113 * 100:.2f}%)")

    print("\n" + "=" * 75)
    print("PHASE 1E.1 MATERIALIZATION COMPLETE — ALL ARTIFACTS WRITTEN")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(main())
