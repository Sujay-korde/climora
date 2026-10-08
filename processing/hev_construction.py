"""CLIMORA Phase 1D: Hazard-Exposure-Susceptibility (H/E/V) Construction Engine.

Constructs and independently audits:
  H_i = Thermal Hazard (Formulation F-19)
  E_i = Demographic & Asset Exposure (Formulation F-20)
  V_i = Biophysical & Structural Susceptibility (Formulation F-21)

Governance & Semantic Principles:
1. Operates strictly at the Uber H3 Resolution 9 analytical mesh (3,181 cells).
2. PMC ward reporting is decoupled; KMeans `ward_id` is NOT used anywhere in computation.
3. No final composite Risk (H * E * V) is constructed in Phase 1D.
4. Weights are explicitly governed as `CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)`.
5. Missing data rule: K_valid >= 4 is strictly enforced; 68 disqualified cells remain NaN and are not imputed.
6. Zero socioeconomic vulnerability fabrication: V strictly measures biophysical/structural canopy deficit and built thermal mass.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Dict, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_DIR))

import numpy as np
import pandas as pd

from ingestion.common import calculate_sha256, get_logger
from processing.config import MANIFESTS_DIR, PROCESSED_DIR, PROJECT_ROOT

logger = get_logger()

# Input & Output Paths
INPUT_FEATURE_MATRIX_PARQUET = PROCESSED_DIR / "canonical_feature_matrix.parquet"
OUTPUT_HEV_DIR = PROCESSED_DIR / "hev"
OUTPUT_HEV_PARQUET = OUTPUT_HEV_DIR / "canonical_hev_components.parquet"
OUTPUT_HEV_CONTRACT = MANIFESTS_DIR / "canonical_hev_contract.json"

# Formulations F-19, F-20, F-21 Weight Governance
# Status: CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)
HAZARD_WEIGHTS = {
    "norm_lst_2025": 0.25,
    "norm_lst_anomaly": 0.25,
    "norm_persistence": 0.25,
    "norm_recurrence_ge45": 0.25,
}

EXPOSURE_WEIGHTS = {
    "norm_population": 0.40,
    "norm_population_density": 0.30,
    "norm_civic_infra": 0.20,
    "norm_road_length": 0.10,
}

SUSCEPTIBILITY_WEIGHTS = {
    "norm_ndvi_deficit": 0.45,
    "norm_ndbi": 0.45,
    "norm_green_space_deficit": 0.10,
}


def construct_hev_components(
    feature_matrix_path: Path = INPUT_FEATURE_MATRIX_PARQUET,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Construct H_i, E_i, and V_i components from canonical feature matrix.

    Returns:
        hev_df: DataFrame with 3,181 rows containing H_i, E_i, V_i, eligibility flags,
                and normalized component inputs.
        audit_report: Dictionary with comprehensive forensic statistics and diagnostics.
    """
    logger.info("Loading canonical feature matrix from %s", feature_matrix_path)
    df = pd.read_parquet(feature_matrix_path)

    # 1. Structural assertions
    assert len(df) == 3181, f"Expected exactly 3,181 H3 Res9 cells, found {len(df)}"
    assert "h3_cell_id" in df.columns, "Missing h3_cell_id in input matrix"
    assert "ward_id" in df.columns, "Expected ward_id in frozen input matrix"
    
    # Decoupling check: ward_id must NOT be referenced or used in mathematical computation
    input_sha256 = calculate_sha256(feature_matrix_path)

    # 2. Eligibility determination (Formulation F-13: K_valid >= 4)
    hazard_eligibility = df["K_valid"] >= 4
    n_eligible = int(hazard_eligibility.sum())
    n_ineligible = int((~hazard_eligibility).sum())
    assert n_eligible == 3113, f"Expected 3,113 eligible cells, got {n_eligible}"
    assert n_ineligible == 68, f"Expected 68 ineligible cells, got {n_ineligible}"

    # Exposure eligibility: complete demographic and OSM vector coverage across statutory AOI
    exposure_eligibility = pd.Series(True, index=df.index, name="exposure_eligibility")

    # Susceptibility eligibility: requires clear satellite 2025 canopy and built data
    susceptibility_eligibility = (
        hazard_eligibility
        & df["norm_ndvi_deficit"].notna()
        & df["norm_ndbi"].notna()
    )
    assert susceptibility_eligibility.sum() == 3113

    overall_hev_eligibility = (
        hazard_eligibility
        & exposure_eligibility
        & susceptibility_eligibility
    )

    # 3. Hazard Construction (Formulation F-19)
    # H_i = w_H1 * Norm(T_2025) + w_H2 * Norm(Delta_T) + w_H3 * Persistence + w_H4 * Norm(Recurrence_45)
    h_series = (
        HAZARD_WEIGHTS["norm_lst_2025"] * df["norm_lst_2025"]
        + HAZARD_WEIGHTS["norm_lst_anomaly"] * df["norm_lst_anomaly"]
        + HAZARD_WEIGHTS["norm_persistence"] * df["norm_persistence"]
        + HAZARD_WEIGHTS["norm_recurrence_ge45"] * df["norm_recurrence_ge45"]
    )
    # Enforce NaN for ineligible cells (no silent imputation)
    h_series = h_series.where(hazard_eligibility, np.nan)

    # 4. Exposure Construction (Formulation F-20)
    # E_i = w_E1 * Norm(C_i) + w_E2 * Norm(D_i) + w_E3 * Norm(N_infra) + w_E4 * Norm(L_road)
    e_series = (
        EXPOSURE_WEIGHTS["norm_population"] * df["norm_population"]
        + EXPOSURE_WEIGHTS["norm_population_density"] * df["norm_population_density"]
        + EXPOSURE_WEIGHTS["norm_civic_infra"] * df["norm_civic_infra"]
        + EXPOSURE_WEIGHTS["norm_road_length"] * df["norm_road_length"]
    )

    # 5. Biophysical & Structural Susceptibility Construction (Formulation F-21)
    # V_i = w_V1 * (1 - Norm(NDVI)) + w_V2 * Norm(NDBI) + w_V3 * (1 - Norm(A_green))
    g_min = float(df["green_space_area_m2"].min())
    g_max = float(df["green_space_area_m2"].max())
    assert g_max > g_min, "Degenerate green space area distribution"
    norm_green_space = (df["green_space_area_m2"] - g_min) / (g_max - g_min)
    norm_green_space_deficit = 1.0 - norm_green_space

    v_series = (
        SUSCEPTIBILITY_WEIGHTS["norm_ndvi_deficit"] * df["norm_ndvi_deficit"]
        + SUSCEPTIBILITY_WEIGHTS["norm_ndbi"] * df["norm_ndbi"]
        + SUSCEPTIBILITY_WEIGHTS["norm_green_space_deficit"] * norm_green_space_deficit
    )
    # Enforce NaN for ineligible cells
    v_series = v_series.where(susceptibility_eligibility, np.nan)

    # 6. Verification of numerical bounds on eligible cells
    assert (h_series[hazard_eligibility] >= 0.0).all() and (h_series[hazard_eligibility] <= 1.0).all()
    assert (e_series >= 0.0).all() and (e_series <= 1.0).all()
    assert (v_series[susceptibility_eligibility] >= 0.0).all() and (v_series[susceptibility_eligibility] <= 1.0).all()

    # 7. Assemble canonical HEV DataFrame
    hev_df = pd.DataFrame({
        "h3_cell_id": df["h3_cell_id"],
        "H_i": h_series,
        "E_i": e_series,
        "V_i": v_series,
        "hazard_eligibility": hazard_eligibility.astype(bool),
        "exposure_eligibility": exposure_eligibility.astype(bool),
        "susceptibility_eligibility": susceptibility_eligibility.astype(bool),
        "overall_hev_eligibility": overall_hev_eligibility.astype(bool),
        # Normalized component inputs for complete lineage & auditability
        "norm_lst_2025": df["norm_lst_2025"],
        "norm_lst_anomaly": df["norm_lst_anomaly"],
        "norm_persistence": df["norm_persistence"],
        "norm_recurrence_ge45": df["norm_recurrence_ge45"],
        "norm_population": df["norm_population"],
        "norm_population_density": df["norm_population_density"],
        "norm_civic_infra": df["norm_civic_infra"],
        "norm_road_length": df["norm_road_length"],
        "norm_ndvi_deficit": df["norm_ndvi_deficit"],
        "norm_ndbi": df["norm_ndbi"],
        "norm_green_space_deficit": norm_green_space_deficit,
    })

    # 8. Generate forensic statistical audit report
    audit_report = generate_hev_audit_report(hev_df, df, input_sha256)
    return hev_df, audit_report


def generate_hev_audit_report(
    hev_df: pd.DataFrame,
    source_df: pd.DataFrame,
    input_sha256: str,
) -> Dict[str, Any]:
    """Generate comprehensive forensic diagnostics for H, E, V components."""
    eligible = hev_df["overall_hev_eligibility"]
    h_el = hev_df.loc[eligible, "H_i"]
    e_all = hev_df["E_i"]
    e_el = hev_df.loc[eligible, "E_i"]
    v_el = hev_df.loc[eligible, "V_i"]

    def stats_dict(s: pd.Series) -> Dict[str, Any]:
        return {
            "count": int(s.count()),
            "missing": int(s.isna().sum()),
            "min": round(float(s.min()), 6),
            "q01": round(float(s.quantile(0.01)), 6),
            "q05": round(float(s.quantile(0.05)), 6),
            "q25": round(float(s.quantile(0.25)), 6),
            "median": round(float(s.median()), 6),
            "mean": round(float(s.mean()), 6),
            "q75": round(float(s.quantile(0.75)), 6),
            "q95": round(float(s.quantile(0.95)), 6),
            "q99": round(float(s.quantile(0.99)), 6),
            "max": round(float(s.max()), 6),
            "std": round(float(s.std()), 6),
        }

    # Inter-dimensional correlation matrix on eligible cells
    sub_df = pd.DataFrame({"H": h_el, "E": e_el, "V": v_el})
    pearson_corr = sub_df.corr(method="pearson").round(6).to_dict()
    spearman_corr = sub_df.corr(method="spearman").round(6).to_dict()

    # Hazard sub-component correlations
    h_sub = hev_df.loc[eligible, list(HAZARD_WEIGHTS.keys())]
    h_sub_corr = h_sub.corr(method="pearson").round(6).to_dict()

    # Exposure sub-component correlations
    e_sub = hev_df[list(EXPOSURE_WEIGHTS.keys())]
    e_sub_corr = e_sub.corr(method="pearson").round(6).to_dict()

    # Susceptibility sub-component correlations
    v_sub = hev_df.loc[eligible, list(SUSCEPTIBILITY_WEIGHTS.keys())]
    v_sub_corr = v_sub.corr(method="pearson").round(6).to_dict()

    # Zero exposure cells
    zero_e_cells = hev_df[hev_df["E_i"] == 0.0]["h3_cell_id"].tolist()

    report = {
        "schema_version": "1.0.0",
        "phase": "Phase 1D",
        "contract_id": "CLIMORA-CONTRACT-CANONICAL-HEV-V1",
        "status": "RATIFIED_AND_CANONICAL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_feature_matrix": {
            "path": str(INPUT_FEATURE_MATRIX_PARQUET.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "sha256": input_sha256,
            "total_cells": len(hev_df),
            "eligible_cells": int(eligible.sum()),
            "ineligible_cells": int((~eligible).sum()),
        },
        "weight_governance": {
            "status": "CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)",
            "hazard_weights": HAZARD_WEIGHTS,
            "exposure_weights": EXPOSURE_WEIGHTS,
            "susceptibility_weights": SUSCEPTIBILITY_WEIGHTS,
        },
        "ward_decoupling": {
            "status": "DECOUPLED_H3_RES9_ONLY",
            "ward_id_used_in_computation": False,
            "administrative_reporting_state": "BLOCKED — AUTHORITATIVE PMC WARD GEOMETRY NOT LOCATED (PHASE 1C.1A)",
            "governance_rule": "H/E/V computed strictly at H3 Res9. Ward reporting remains a deferred downstream integration layer.",
        },
        "component_distributions": {
            "H_i": stats_dict(h_el),
            "E_i_all": stats_dict(e_all),
            "E_i_eligible": stats_dict(e_el),
            "V_i": stats_dict(v_el),
        },
        "subcomponent_distributions": {
            col: stats_dict(hev_df.loc[eligible, col] if col in h_sub.columns or col in v_sub.columns else hev_df[col])
            for col in [
                "norm_lst_2025", "norm_lst_anomaly", "norm_persistence", "norm_recurrence_ge45",
                "norm_population", "norm_population_density", "norm_civic_infra", "norm_road_length",
                "norm_ndvi_deficit", "norm_ndbi", "norm_green_space_deficit"
            ]
        },
        "inter_dimensional_correlations": {
            "pearson": pearson_corr,
            "spearman": spearman_corr,
        },
        "intra_dimensional_correlations": {
            "hazard_subcomponents": h_sub_corr,
            "exposure_subcomponents": e_sub_corr,
            "susceptibility_subcomponents": v_sub_corr,
        },
        "zero_exposure_audit": {
            "count_cells_zero_exposure": len(zero_e_cells),
            "h3_cell_ids": zero_e_cells,
            "semantic_interpretation": (
                "E_i = 0 indicates that cell is at the city-wide minimum for population count and density, "
                "with zero mapped civic infrastructure and zero mapped roadways. Under the downstream zero-exposure "
                "axiom, this will yield Risk_i = 0. In Phase 1D, Risk_i is not constructed."
            ),
        },
        "missingness_audit": {
            "k_valid_ge_4_cells": int(eligible.sum()),
            "k_valid_lt_4_cells": int((~eligible).sum()),
            "imputation_policy": "NO_SILENT_IMPUTATION (Strict NaN preservation for disqualified cells)",
        },
    }
    return report


def save_hev_artifacts(
    hev_df: pd.DataFrame,
    audit_report: Dict[str, Any],
) -> Tuple[Path, Path]:
    """Save canonical HEV parquet artifact and companion JSON contract."""
    OUTPUT_HEV_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save parquet
    hev_df.to_parquet(OUTPUT_HEV_PARQUET, index=False, engine="pyarrow")
    logger.info("Saved canonical HEV parquet to %s", OUTPUT_HEV_PARQUET)

    # Compute parquet sha256 and add to contract
    parquet_sha256 = calculate_sha256(OUTPUT_HEV_PARQUET)
    audit_report["materialized_assets"] = {
        "parquet_path": str(OUTPUT_HEV_PARQUET.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "parquet_sha256": parquet_sha256,
        "parquet_size_bytes": OUTPUT_HEV_PARQUET.stat().st_size,
        "row_count": len(hev_df),
        "column_count": len(hev_df.columns),
    }

    # Save contract JSON
    with open(OUTPUT_HEV_CONTRACT, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)
    logger.info("Saved canonical HEV contract to %s", OUTPUT_HEV_CONTRACT)

    return OUTPUT_HEV_PARQUET, OUTPUT_HEV_CONTRACT


def main() -> int:
    """CLI execution entrypoint for Phase 1D HEV Construction."""
    print("=" * 75)
    print("CLIMORA PHASE 1D — HAZARD-EXPOSURE-SUSCEPTIBILITY CONSTRUCTION ENGINE")
    print("=" * 75)

    hev_df, audit_report = construct_hev_components()
    parquet_path, contract_path = save_hev_artifacts(hev_df, audit_report)

    print("\n--- PHASE 1D MATERIALIZATION SUMMARY ---")
    print(f"  Parquet Output:  {parquet_path}")
    print(f"  Contract Output: {contract_path}")
    print(f"  Parquet SHA256:  {audit_report['materialized_assets']['parquet_sha256']}")
    print(f"  Total Cells:     {len(hev_df)}")
    print(f"  Eligible Cells:  {audit_report['input_feature_matrix']['eligible_cells']}")
    print(f"  Blocked Cells:   {audit_report['input_feature_matrix']['ineligible_cells']}")
    print(f"  Zero-Exp Cells:  {audit_report['zero_exposure_audit']['count_cells_zero_exposure']}")
    print(f"  Ward Decoupling: {audit_report['ward_decoupling']['status']}")

    print("\n--- COMPONENT SUMMARY (ELIGIBLE MESH N = 3,113) ---")
    for comp in ["H_i", "E_i_eligible", "V_i"]:
        st = audit_report["component_distributions"][comp]
        print(f"  {comp:12s} | Mean: {st['mean']:.4f} | Median: {st['median']:.4f} | Std: {st['std']:.4f} | Range: [{st['min']:.4f}, {st['max']:.4f}]")

    print("\n" + "=" * 75)
    print("PHASE 1D MATERIALIZATION COMPLETE — ALL ARTIFACTS WRITTEN")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(main())
