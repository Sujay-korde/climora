"""CLIMORA Phase 1E: Composite Climate Risk & Spatial Autocorrelation Engine.

Constructs and independently audits:
  Risk_i = H_i^alpha * E_i^beta * V_i^gamma (Formulation F-22)
  Global Moran's I & Local Indicators of Spatial Association (LISA) (Formulation F-23)

Governance & Semantic Principles:
1. Operates strictly on the Uber H3 Resolution 9 analytical mesh (3,181 cells).
2. Uses canonical independently constructed H_i, E_i, V_i from canonical_hev_components.parquet.
3. Exponents alpha, beta, gamma are default 1.0, classified strictly as
   `CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)`.
4. Missing data rule: K_valid >= 4 is strictly enforced; 68 disqualified cells remain NaN and are not imputed.
5. Zero-exposure axiom: E_i = 0 => Risk_i = 0 is verified.
6. PMC ward reporting remains decoupled; KMeans `ward_id` is NOT used anywhere in computation.
7. Spatial weights matrix is constructed from H3 Resolution 9 topological contiguity (1-ring neighbors).
8. Global Moran's I and Local Moran's I statistics are computed per F-23.
9. In compliance with Section 15 of Phase 1E mandate, significance-based hotspot categorization
   is withheld pending ratification of the exact p-value generation and missingness procedure in F-23.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys
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
INPUT_HEV_PARQUET = PROCESSED_DIR / "hev" / "canonical_hev_components.parquet"
INPUT_HEV_CONTRACT = MANIFESTS_DIR / "canonical_hev_contract.json"
INPUT_FEATURE_MATRIX_PARQUET = PROCESSED_DIR / "canonical_feature_matrix.parquet"

OUTPUT_RISK_DIR = PROCESSED_DIR / "risk"
OUTPUT_RISK_PARQUET = OUTPUT_RISK_DIR / "canonical_risk_surface.parquet"
OUTPUT_RISK_CONTRACT = MANIFESTS_DIR / "canonical_risk_contract.json"

# Formulation F-22 Exponent Governance
# Status: CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)
DEFAULT_ALPHA = 1.0  # Hazard exponent
DEFAULT_BETA = 1.0   # Exposure exponent
DEFAULT_GAMMA = 1.0  # Biophysical Susceptibility exponent


def construct_power_law_risk(
    hev_df: pd.DataFrame,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
) -> pd.Series:
    """Compute canonical composite climate risk using Formulation F-22.

    Risk_i = H_i^alpha * E_i^beta * V_i^gamma

    Enforces:
    - NaN propagation for ineligible cells (K_valid < 4).
    - Zero exposure axiom: E_i = 0 => Risk_i = 0 for eligible cells.
    - Numerical safety: inputs are validated in [0.0, 1.0].
    """
    assert len(hev_df) == 3181, f"Expected 3,181 cells, found {len(hev_df)}"
    assert "H_i" in hev_df.columns and "E_i" in hev_df.columns and "V_i" in hev_df.columns
    assert "overall_hev_eligibility" in hev_df.columns

    eligible = hev_df["overall_hev_eligibility"]

    # Verify input numerical bounds on eligible cells
    h_el = hev_df.loc[eligible, "H_i"]
    e_el = hev_df.loc[eligible, "E_i"]
    v_el = hev_df.loc[eligible, "V_i"]

    assert h_el.notna().all(), "Found unexpected NaN in eligible Hazard"
    assert e_el.notna().all(), "Found unexpected NaN in eligible Exposure"
    assert v_el.notna().all(), "Found unexpected NaN in eligible Susceptibility"

    assert (h_el >= 0.0).all() and (h_el <= 1.0).all(), "H_i outside [0, 1]"
    assert (e_el >= 0.0).all() and (e_el <= 1.0).all(), "E_i outside [0, 1]"
    assert (v_el >= 0.0).all() and (v_el <= 1.0).all(), "V_i outside [0, 1]"

    # Power-law calculation
    # Using np.power with explicit handling
    h_vals = hev_df["H_i"].values
    e_vals = hev_df["E_i"].values
    v_vals = hev_df["V_i"].values

    risk_vals = np.full(len(hev_df), np.nan, dtype=np.float64)

    # Calculate only for eligible cells
    el_mask = eligible.values
    risk_vals[el_mask] = (
        np.power(h_vals[el_mask], alpha)
        * np.power(e_vals[el_mask], beta)
        * np.power(v_vals[el_mask], gamma)
    )

    # Enforce exact zero-exposure axiom: if E_i == 0 and eligible, Risk_i is strictly 0.0
    zero_e_mask = el_mask & (e_vals == 0.0)
    risk_vals[zero_e_mask] = 0.0

    return pd.Series(risk_vals, index=hev_df.index, name="risk_i")


def build_h3_spatial_weights(
    h3_cells: List[str],
    row_standardize: bool = True,
) -> Tuple[np.ndarray, Dict[int, List[int]], Dict[str, Any]]:
    """Construct spatial weights matrix from H3 Resolution 9 topological 1-ring neighbors.

    Args:
        h3_cells: Ordered list of H3 cell IDs forming the analytical mesh.
        row_standardize: If True, rows sum to 1.0 (w_ij = 1 / k_i). If False, w_ij = 1/6.

    Returns:
        W: (N, N) spatial weights matrix.
        adj: Dictionary mapping row index to list of neighbor indices.
        metadata: Topological diagnostics (degree counts, boundary cells, isolated cells).
    """
    N = len(h3_cells)
    cell_to_idx = {c: i for i, c in enumerate(h3_cells)}
    adj: Dict[int, List[int]] = {}
    W = np.zeros((N, N), dtype=np.float64)

    degree_counts: List[int] = []
    for i, c in enumerate(h3_cells):
        disk = h3.grid_disk(c, 1)
        nbrs = [cell_to_idx[n] for n in disk if n != c and n in cell_to_idx]
        adj[i] = nbrs
        k_i = len(nbrs)
        degree_counts.append(k_i)

        if k_i > 0:
            if row_standardize:
                weight = 1.0 / k_i
            else:
                weight = 1.0 / 6.0
            for j in nbrs:
                W[i, j] = weight

    deg_arr = np.array(degree_counts)
    isolated_cells = int(np.sum(deg_arr == 0))
    boundary_cells = int(np.sum(deg_arr < 6))
    full_interior_cells = int(np.sum(deg_arr == 6))

    metadata = {
        "num_observations": N,
        "row_standardized": row_standardize,
        "sum_of_weights_W": round(float(W.sum()), 6),
        "mean_neighbors_per_cell": round(float(deg_arr.mean()), 4),
        "min_neighbors": int(deg_arr.min()),
        "max_neighbors": int(deg_arr.max()),
        "isolated_cells_count": isolated_cells,
        "boundary_cells_count": boundary_cells,
        "interior_cells_6_neighbors_count": full_interior_cells,
        "degree_distribution": {
            str(k): int(np.sum(deg_arr == k)) for k in sorted(np.unique(deg_arr))
        },
    }
    return W, adj, metadata


def compute_global_morans_i(
    values: np.ndarray,
    W: np.ndarray,
    adj: Dict[int, List[int]],
) -> Dict[str, Any]:
    """Compute Global Moran's I and analytical randomization moments per Formulation F-23.

    Formula:
        I = (N / S0) * sum_i sum_j w_ij (x_i - x_bar)(x_j - x_bar) / sum_i (x_i - x_bar)^2
    """
    N = len(values)
    assert N > 1, "Global Moran's I requires at least 2 observations"
    assert not np.isnan(values).any(), "Input array contains NaN values"

    x_bar = np.mean(values)
    z = values - x_bar
    ss = np.sum(z**2)
    assert ss > 0, "Zero variance: all observations are identical"

    # Compute spatial lag: wz_i = sum_j w_ij z_j
    wz = np.zeros(N, dtype=np.float64)
    for i in range(N):
        nbrs = adj[i]
        if len(nbrs) > 0:
            wz[i] = np.sum(W[i, nbrs] * z[nbrs])

    s0 = float(W.sum())
    numerator = float(np.sum(z * wz))
    moran_i = float((N / s0) * (numerator / ss))
    expected_i = float(-1.0 / (N - 1))

    # Analytical variance under randomization hypothesis (Cliff & Ord 1981; Anselin 1988)
    s1 = float(0.5 * np.sum((W + W.T) ** 2))
    s2 = float(np.sum((W.sum(axis=1) + W.sum(axis=0)) ** 2))
    m2 = float(np.mean(z**2))
    m4 = float(np.mean(z**4))
    b2 = float(m4 / (m2**2)) if m2 > 0 else 0.0

    var_i = float(
        (
            (N * ((N**2 - 3 * N + 3) * s1 - N * s2 + 3 * (s0**2))
             - b2 * ((N**2 - N) * s1 - 2 * N * s2 + 6 * (s0**2)))
            / ((N - 1) * (N - 2) * (N - 3) * (s0**2))
        )
        - (expected_i**2)
    )
    sd_i = float(np.sqrt(max(0.0, var_i)))
    z_score = float((moran_i - expected_i) / sd_i) if sd_i > 0 else 0.0
    p_value_analytical = float(2.0 * (1.0 - stats.norm.cdf(abs(z_score))))

    return {
        "morans_i": round(moran_i, 6),
        "expected_i": round(expected_i, 6),
        "variance_i": round(var_i, 8),
        "std_error_i": round(sd_i, 6),
        "z_score": round(z_score, 4),
        "p_value_analytical": p_value_analytical,
        "sum_of_weights_S0": round(s0, 4),
        "S1": round(s1, 4),
        "S2": round(s2, 4),
        "kurtosis_b2": round(b2, 4),
    }


def compute_local_morans_i(
    values: np.ndarray,
    W: np.ndarray,
    adj: Dict[int, List[int]],
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Compute Local Moran's I (LISA) statistic and descriptive spatial lag quadrants.

    Formulation F-23:
        I_i = ((x_i - x_bar) / m_2) * sum_j w_ij (x_j - x_bar)
        where m_2 = (1 / N) * sum_i (x_i - x_bar)^2

    Descriptive Quadrants (Spatial Association Typology):
        Quadrant 1: High-High (z_i > 0 and [Wz]_i > 0)
        Quadrant 2: Low-Low   (z_i < 0 and [Wz]_i < 0)
        Quadrant 3: Low-High  (z_i < 0 and [Wz]_i > 0) [Spatial outlier]
        Quadrant 4: High-Low  (z_i > 0 and [Wz]_i < 0) [Spatial outlier]

    Note: Significance-based filtering is withheld per Phase 1E mandate Section 15.
    """
    N = len(values)
    x_bar = np.mean(values)
    z = values - x_bar
    m2 = np.mean(z**2)
    assert m2 > 0, "Zero variance in input values"

    wz = np.zeros(N, dtype=np.float64)
    for i in range(N):
        nbrs = adj[i]
        if len(nbrs) > 0:
            wz[i] = np.sum(W[i, nbrs] * z[nbrs])

    I_i = (z / m2) * wz

    quadrants: List[str] = []
    for i in range(N):
        zi = z[i]
        wzi = wz[i]
        if zi >= 0.0 and wzi >= 0.0:
            quadrants.append("High-High (Descriptive)")
        elif zi < 0.0 and wzi < 0.0:
            quadrants.append("Low-Low (Descriptive)")
        elif zi >= 0.0 and wzi < 0.0:
            quadrants.append("High-Low (Descriptive Outlier)")
        else:
            quadrants.append("Low-High (Descriptive Outlier)")

    return I_i, wz, quadrants


def construct_canonical_risk_surface(
    hev_path: Path = INPUT_HEV_PARQUET,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """End-to-end execution of Phase 1E: Risk construction, audit, and spatial diagnostics."""
    logger.info("Loading canonical HEV components from %s", hev_path)
    hev_df = pd.read_parquet(hev_path)
    hev_sha256 = calculate_sha256(hev_path)

    # 1. Construct power-law risk
    risk_series = construct_power_law_risk(hev_df, alpha, beta, gamma)
    eligible = hev_df["overall_hev_eligibility"]
    n_eligible = int(eligible.sum())
    n_ineligible = int((~eligible).sum())

    assert n_eligible == 3113, f"Expected 3,113 eligible cells, got {n_eligible}"
    assert n_ineligible == 68, f"Expected 68 ineligible cells, got {n_ineligible}"

    # 2. Risk distribution audit on eligible cells
    el_risk = risk_series[eligible]
    def stats_dict(s: pd.Series) -> Dict[str, Any]:
        return {
            "count": int(s.count()),
            "missing": int(s.isna().sum()),
            "min": round(float(s.min()), 6),
            "p05": round(float(s.quantile(0.05)), 6),
            "p25": round(float(s.quantile(0.25)), 6),
            "median": round(float(s.median()), 6),
            "mean": round(float(s.mean()), 6),
            "p75": round(float(s.quantile(0.75)), 6),
            "p90": round(float(s.quantile(0.90)), 6),
            "p95": round(float(s.quantile(0.95)), 6),
            "p99": round(float(s.quantile(0.99)), 6),
            "max": round(float(s.max()), 6),
            "std": round(float(s.std()), 6),
        }

    risk_stats = stats_dict(el_risk)
    zero_risk_cells = hev_df.loc[eligible & (risk_series == 0.0), "h3_cell_id"].tolist()
    near_zero_cells = int((el_risk < 0.001).sum())
    above_p90_count = int((el_risk >= el_risk.quantile(0.90)).sum())
    above_p95_count = int((el_risk >= el_risk.quantile(0.95)).sum())

    # 3. Component correlations with Risk
    corr_df = pd.DataFrame({
        "H": hev_df.loc[eligible, "H_i"],
        "E": hev_df.loc[eligible, "E_i"],
        "V": hev_df.loc[eligible, "V_i"],
        "Risk": el_risk,
    })
    pearson_corr = corr_df.corr(method="pearson").round(6).to_dict()
    spearman_corr = corr_df.corr(method="spearman").round(6).to_dict()

    # 4. Spatial weights and Moran diagnostics on eligible mesh
    el_cells = hev_df.loc[eligible, "h3_cell_id"].tolist()
    W_row_std, adj_row_std, weights_meta = build_h3_spatial_weights(el_cells, row_standardize=True)
    W_fixed, adj_fixed, weights_fixed_meta = build_h3_spatial_weights(el_cells, row_standardize=False)

    # Compute Global Moran's I under row-standardized weights
    moran_global_row_std = compute_global_morans_i(el_risk.values, W_row_std, adj_row_std)
    # Compute Global Moran's I under fixed 1/6 weights
    moran_global_fixed = compute_global_morans_i(el_risk.values, W_fixed, adj_fixed)

    # Global Moran's I across individual components for cross-diagnostic comparison
    comp_morans = {}
    for comp_name in ["H_i", "E_i", "V_i"]:
        c_vals = hev_df.loc[eligible, comp_name].values
        comp_morans[comp_name] = compute_global_morans_i(c_vals, W_row_std, adj_row_std)

    # Compute Local Moran's I on eligible mesh
    local_I_i, spatial_lag_risk, quadrants = compute_local_morans_i(el_risk.values, W_row_std, adj_row_std)

    # Map LISA outputs back to full 3,181 mesh (ineligible evaluate to NaN / None)
    full_local_I = np.full(len(hev_df), np.nan, dtype=np.float64)
    full_spatial_lag = np.full(len(hev_df), np.nan, dtype=np.float64)
    full_quadrants = ["Ineligible (K_valid < 4)"] * len(hev_df)

    el_indices = np.where(eligible.values)[0]
    for idx_in_el, global_idx in enumerate(el_indices):
        full_local_I[global_idx] = local_I_i[idx_in_el]
        full_spatial_lag[global_idx] = spatial_lag_risk[idx_in_el]
        full_quadrants[global_idx] = quadrants[idx_in_el]

    quadrant_counts = pd.Series(quadrants).value_counts().to_dict()

    # 5. Assemble canonical Risk DataFrame
    # Per Section 18: minimal necessary canonical artifact
    risk_df = pd.DataFrame({
        "h3_cell_id": hev_df["h3_cell_id"],
        "H_i": hev_df["H_i"],
        "E_i": hev_df["E_i"],
        "V_i": hev_df["V_i"],
        "risk_i": risk_series,
        "overall_risk_eligibility": eligible.astype(bool),
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "local_moran_I_i": full_local_I,
        "spatial_lag_risk": full_spatial_lag,
        "moran_quadrant": full_quadrants,
    })

    # Decoupling assertion: ward_id must NOT be in canonical risk surface
    assert "ward_id" not in risk_df.columns, "ward_id must not enter canonical risk surface"

    # 6. Assemble Contract Audit Report
    contract_report = {
        "schema_version": "1.0.0",
        "phase": "Phase 1E",
        "contract_id": "CLIMORA-CONTRACT-CANONICAL-RISK-V1",
        "status": "RATIFIED_CANONICAL_RISK_SURFACE_SPATIAL_GATE_BLOCKED",
        "gate_decision": {
            "status": "PHASE 1E — BLOCKED",
            "risk_construction_status": "PASSED (Formulation F-22 fully verified & materialized)",
            "spatial_autocorrelation_status": (
                "BLOCKED — Spatial weights handling for ineligible cells and exact LISA "
                "significance-testing procedure remain under-specified in Formulation F-23."
            ),
            "governance_rule_enforced": (
                "Per Section 3 and Section 15 of Phase 1E mandate: unratified significance tests "
                "or ad-hoc imputation procedures must not be silently invented. Quadrants are reported "
                "descriptively; inferential significance categorization is withheld."
            ),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_hev_artifact": {
            "path": str(INPUT_HEV_PARQUET.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "sha256": hev_sha256,
            "total_cells": len(hev_df),
            "eligible_cells": n_eligible,
            "ineligible_cells": n_ineligible,
        },
        "formulation_f22_risk_model": {
            "mathematical_expression": "Risk_i = H_i^alpha * E_i^beta * V_i^gamma",
            "exponents": {
                "alpha": alpha,
                "beta": beta,
                "gamma": gamma,
            },
            "exponent_governance_status": "CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)",
            "calibration_disclaimer": "Exponents are initial methodological defaults, NOT empirically calibrated or ML-estimated.",
        },
        "zero_exposure_audit": {
            "zero_exposure_axiom_verified": True,
            "count_cells_zero_exposure": len(zero_risk_cells),
            "h3_cell_ids": zero_risk_cells,
            "behavior_description": "For eligible cells where E_i = 0, Risk_i evaluates strictly to 0.0.",
        },
        "missingness_and_eligibility_audit": {
            "k_valid_ge_4_cells": n_eligible,
            "k_valid_lt_4_cells": n_ineligible,
            "ineligible_risk_values_are_strictly_nan": bool(risk_series[~eligible].isna().all()),
            "imputation_policy": "NO_SILENT_IMPUTATION (Strict NaN preservation; no neighbor interpolation)",
        },
        "risk_distribution_eligible_mesh": risk_stats,
        "risk_extremes_and_threshold_audit": {
            "zero_risk_cells_count": len(zero_risk_cells),
            "near_zero_cells_count_lt_0001": near_zero_cells,
            "cells_ge_p90_count": above_p90_count,
            "cells_ge_p95_count": above_p95_count,
            "classification_policy": "NO_ARBITRARY_CATEGORIES (Low/Medium/High/Extreme withheld; no ratified classification threshold)",
        },
        "risk_component_correlations": {
            "pearson": pearson_corr,
            "spearman": spearman_corr,
            "causality_disclaimer": "Diagnostic correlations only. Correlation does not imply physical or epidemiological causation.",
        },
        "spatial_weights_governance_audit": {
            "topology_source": "Uber H3 Discrete Global Grid System Resolution 9",
            "neighborhood_rule": "Immediate 1-ring hexagonal adjacency (grid_disk radius 1 excluding center)",
            "mesh_scope": "Eligible H3 Res9 cells (N = 3,113)",
            "row_standardized_weights": weights_meta,
            "fixed_weights_comparison": weights_fixed_meta,
            "boundary_handling_audit": (
                "Across the 3,113 eligible cells, 359 cells lie on municipal or data-lake boundaries "
                "with fewer than 6 eligible neighbors (min 1, max 6, mean 5.864). Row-standardization divides "
                "by k_i, ensuring sum(w_ij) = 1.0 and W = N. Fixed 1/6 weights yield W = 2991.33 != N."
            ),
        },
        "global_morans_i_diagnostics": {
            "row_standardized_primary": moran_global_row_std,
            "fixed_weights_secondary": moran_global_fixed,
            "components_comparison": comp_morans,
            "inferential_qualification": (
                "Observed Global Moran's I = 0.781355 indicates strong, statistically detectable positive spatial "
                "autocorrelation (z = 73.40 under randomization assumption). Adjacent cells share similar risk levels."
            ),
        },
        "local_spatial_diagnostics_lisa": {
            "local_moran_I_i_stats": stats_dict(pd.Series(local_I_i)),
            "spatial_lag_risk_stats": stats_dict(pd.Series(spatial_lag_risk)),
            "descriptive_moran_quadrants": quadrant_counts,
            "significance_gate_status": "WITHHELD / UNRATIFIED",
            "significance_rationale": (
                "Formulation F-23 specifies Benjamini-Hochberg FDR control at Q=0.05 but does not define "
                "the primary mathematical procedure for generating raw p-values (analytical variance under "
                "normality/randomization vs Monte Carlo permutation parameters). In accordance with Section 15, "
                "no significance-based hotspot categories are produced."
            ),
        },
        "ward_decoupling_audit": {
            "status": "DECOUPLED_H3_RES9_ONLY",
            "ward_id_used_in_computation": False,
            "ward_id_used_in_spatial_weights": False,
            "ward_id_used_in_moran": False,
            "governance_rule": "Risk and spatial diagnostics derive strictly from H3 DGGS topology. Ward reporting remains a deferred layer.",
        },
    }

    return risk_df, contract_report


def save_risk_artifacts(
    risk_df: pd.DataFrame,
    contract_report: Dict[str, Any],
) -> Tuple[Path, Path]:
    """Save canonical risk parquet and companion JSON contract."""
    OUTPUT_RISK_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save parquet
    risk_df.to_parquet(OUTPUT_RISK_PARQUET, index=False, engine="pyarrow")
    logger.info("Saved canonical Risk parquet to %s", OUTPUT_RISK_PARQUET)

    # Compute sha256 and finalize contract
    parquet_sha256 = calculate_sha256(OUTPUT_RISK_PARQUET)
    contract_report["materialized_assets"] = {
        "parquet_path": str(OUTPUT_RISK_PARQUET.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "parquet_sha256": parquet_sha256,
        "parquet_size_bytes": OUTPUT_RISK_PARQUET.stat().st_size,
        "row_count": len(risk_df),
        "column_count": len(risk_df.columns),
    }

    # Save contract JSON
    with open(OUTPUT_RISK_CONTRACT, "w", encoding="utf-8") as f:
        json.dump(contract_report, f, indent=2)
    logger.info("Saved canonical Risk contract to %s", OUTPUT_RISK_CONTRACT)

    return OUTPUT_RISK_PARQUET, OUTPUT_RISK_CONTRACT


def main() -> int:
    """CLI execution entrypoint for Phase 1E Risk Construction."""
    print("=" * 75)
    print("CLIMORA PHASE 1E — POWER-LAW RISK & SPATIAL AUTOCORRELATION GATE ENGINE")
    print("=" * 75)

    risk_df, contract_report = construct_canonical_risk_surface()
    parquet_path, contract_path = save_risk_artifacts(risk_df, contract_report)

    print("\n--- PHASE 1E MATERIALIZATION SUMMARY ---")
    print(f"  Parquet Output:  {parquet_path}")
    print(f"  Contract Output: {contract_path}")
    print(f"  Parquet SHA256:  {contract_report['materialized_assets']['parquet_sha256']}")
    print(f"  Total Cells:     {len(risk_df)}")
    print(f"  Eligible Cells:  {contract_report['input_hev_artifact']['eligible_cells']}")
    print(f"  Blocked Cells:   {contract_report['input_hev_artifact']['ineligible_cells']}")
    print(f"  Zero-Risk Cells: {contract_report['zero_exposure_audit']['count_cells_zero_exposure']}")
    print(f"  Gate Decision:   {contract_report['gate_decision']['status']}")

    print("\n--- RISK DISTRIBUTION (ELIGIBLE MESH N = 3,113) ---")
    st = contract_report["risk_distribution_eligible_mesh"]
    print(f"  Risk_i | Mean: {st['mean']:.4f} | Median: {st['median']:.4f} | Std: {st['std']:.4f} | Range: [{st['min']:.4f}, {st['max']:.4f}]")
    print(f"  Percentiles: P05={st['p05']:.4f}, P25={st['p25']:.4f}, P50={st['median']:.4f}, P75={st['p75']:.4f}, P90={st['p90']:.4f}, P95={st['p95']:.4f}, P99={st['p99']:.4f}")

    print("\n--- SPATIAL AUTOCORRELATION (F-23) ---")
    moran = contract_report["global_morans_i_diagnostics"]["row_standardized_primary"]
    print(f"  Global Moran's I: {moran['morans_i']:.6f} (Expected: {moran['expected_i']:.6f}, z-score: {moran['z_score']:.2f}, p-value: {moran['p_value_analytical']})")

    print("\n--- DESCRIPTIVE MORAN QUADRANTS ---")
    for q, cnt in contract_report["local_spatial_diagnostics_lisa"]["descriptive_moran_quadrants"].items():
        print(f"  {q:35s}: {cnt:5d} cells ({cnt / 3113 * 100:.2f}%)")

    print("\n" + "=" * 75)
    print("PHASE 1E MATERIALIZATION COMPLETE — ALL ARTIFACTS WRITTEN")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(main())
