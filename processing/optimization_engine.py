"""
CLIMORA - Phase 1G: Intervention Optimization Engine & Production Solver Pipeline.

Direct realization of the ratified Phase 1F optimization mathematics:
- F-24.1: Semi-Continuous Intervention Decision Variables & Minimum Lot-Size Linking
- F-24.2: Candidate-Site Spatial Eligibility & Physical Capacity Bounds
- F-24.3: Intervention Cost Model (CapEx & Fixed Mobilization Overhead)
- F-24.4: Linearized Modeled Microclimate & Biophysical Impact (4.0°C saturation cap)
- F-24.5: Marginal Climate Risk Reduction Response (First-order Taylor on Risk = H * E * V)
- F-24.6: Canonical Budget-Constrained Risk Reduction MILP Optimization Problem
- F-25.1: Modeled Post-Intervention State & Thermodynamic Safety Boundaries

Solver: SciPy MILP interface with HiGHS branch-and-cut backend.
Decoupling: Strictly decoupled from administrative PMC ward geometry (0 dependency).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_DIR))

import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import coo_matrix, csc_matrix

from ingestion.common import calculate_sha256, get_logger
from processing.config import MANIFESTS_DIR, PROCESSED_DIR, PROJECT_ROOT

logger = get_logger()

# Canonical Input Paths
DEFAULT_FEATURE_MATRIX_PARQUET = PROCESSED_DIR / "canonical_feature_matrix.parquet"
DEFAULT_HEV_PARQUET = PROCESSED_DIR / "hev" / "canonical_hev_components.parquet"
DEFAULT_RISK_PARQUET = PROCESSED_DIR / "risk" / "canonical_risk_surface.parquet"
DEFAULT_SPATIAL_PARQUET = PROCESSED_DIR / "risk" / "canonical_spatial_autocorrelation.parquet"
DEFAULT_OPTIMIZATION_CONTRACT = MANIFESTS_DIR / "optimization_formulation_contract.json"

# Canonical Output Paths
DEFAULT_OUTPUT_DIR = PROCESSED_DIR / "optimization"
DEFAULT_ALLOCATION_PARQUET = DEFAULT_OUTPUT_DIR / "canonical_optimization_allocation.parquet"
DEFAULT_RUN_MANIFEST = MANIFESTS_DIR / "optimization_run_manifest.json"

# Thermodynamic & Normalization Constants (F-24.4, F-24.5, F-25.1)
DELTA_T_SCALE_DEGC = 15.0  # Phase 1C normalization span
MAX_MODELED_COOLING_CAP_DEGC = 4.0  # F-24.4 intra-cell saturation cap
HAZARD_LST_WEIGHT = 0.25  # F-19 weight for LST component within Hazard


@dataclass(frozen=True)
class InterventionDefinition:
    """Canonical specification of a physical cooling intervention (F-24.1 to F-24.6)."""
    code: str
    name: str
    category: str
    unit: str
    unit_cost_inr: float
    mobilization_fixed_cost_inr: float
    minimum_lot_size: float
    cooling_coefficient_degC_per_unit: float
    biophysical_susceptibility_factor: float
    is_ground_intervention: bool


def get_ratified_intervention_catalog() -> Dict[str, InterventionDefinition]:
    """Returns the five canonical heat resilience interventions ratified in Phase 1F."""
    return {
        "cool_roof": InterventionDefinition(
            code="cool_roof",
            name="High-Albedo Solar Reflective Roof Coating",
            category="albedo_modification",
            unit="m2_roof_area",
            unit_cost_inr=250.0,
            mobilization_fixed_cost_inr=25000.0,
            minimum_lot_size=500.0,
            cooling_coefficient_degC_per_unit=2.380952e-05,
            biophysical_susceptibility_factor=0.0,
            is_ground_intervention=False,
        ),
        "street_tree_shade": InterventionDefinition(
            code="street_tree_shade",
            name="Urban Street Tree Canopy Planting",
            category="nature_based",
            unit="tree_count",
            unit_cost_inr=3500.0,
            mobilization_fixed_cost_inr=20000.0,
            minimum_lot_size=25.0,
            cooling_coefficient_degC_per_unit=7.142857e-04,
            biophysical_susceptibility_factor=11.25,
            is_ground_intervention=False,
        ),
        "green_corridor": InterventionDefinition(
            code="green_corridor",
            name="Urban Green Corridor & Vegetated Buffer",
            category="nature_based",
            unit="m2_surface_area",
            unit_cost_inr=800.0,
            mobilization_fixed_cost_inr=50000.0,
            minimum_lot_size=200.0,
            cooling_coefficient_degC_per_unit=3.047619e-05,
            biophysical_susceptibility_factor=0.315,
            is_ground_intervention=True,
        ),
        "permeable_surface": InterventionDefinition(
            code="permeable_surface",
            name="Permeable Pavement & Porous Ground Cover",
            category="water_infrastructure",
            unit="m2_surface_area",
            unit_cost_inr=1800.0,
            mobilization_fixed_cost_inr=40000.0,
            minimum_lot_size=200.0,
            cooling_coefficient_degC_per_unit=1.428571e-05,
            biophysical_susceptibility_factor=0.225,
            is_ground_intervention=True,
        ),
        "bioswale": InterventionDefinition(
            code="bioswale",
            name="Bioretention Swale & Roadside Water Retention",
            category="water_infrastructure",
            unit="m2_surface_area",
            unit_cost_inr=2200.0,
            mobilization_fixed_cost_inr=40000.0,
            minimum_lot_size=100.0,
            cooling_coefficient_degC_per_unit=1.904762e-05,
            biophysical_susceptibility_factor=0.270,
            is_ground_intervention=True,
        ),
    }


def normalize_intervention_code(code: str) -> str:
    """Maps plural/alias intervention names to canonical singular codes."""
    mapping = {
        "cool_roofs": "cool_roof",
        "cool_roof": "cool_roof",
        "street_trees": "street_tree_shade",
        "street_tree_shade": "street_tree_shade",
        "green_corridor": "green_corridor",
        "green_corridors": "green_corridor",
        "permeable_surfaces": "permeable_surface",
        "permeable_surface": "permeable_surface",
        "bioswales": "bioswale",
        "bioswale": "bioswale",
    }
    return mapping.get(code.lower(), code)


def load_canonical_inputs(
    feature_parquet_path: Path = DEFAULT_FEATURE_MATRIX_PARQUET,
    risk_parquet_path: Path = DEFAULT_RISK_PARQUET,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads and validates frozen upstream inputs for the optimization engine."""
    if not feature_parquet_path.exists():
        raise FileNotFoundError(f"Canonical feature matrix not found: {feature_parquet_path}")
    if not risk_parquet_path.exists():
        raise FileNotFoundError(f"Canonical risk surface not found: {risk_parquet_path}")

    df_feat = pd.read_parquet(feature_parquet_path)
    df_risk = pd.read_parquet(risk_parquet_path)

    # Pre-solve validation of required columns
    required_risk_cols = {"h3_cell_id", "H_i", "E_i", "V_i", "risk_i", "overall_risk_eligibility"}
    missing_risk = required_risk_cols - set(df_risk.columns)
    if missing_risk:
        raise ValueError(f"Missing required risk surface columns: {missing_risk}")

    required_feat_cols = {
        "h3_cell_id", "cell_area_km2", "norm_ndbi", "road_length_m",
        "green_space_area_m2", "water_body_area_m2", "norm_ndvi_deficit", "population_2020"
    }
    missing_feat = required_feat_cols - set(df_feat.columns)
    if missing_feat:
        raise ValueError(f"Missing required feature matrix columns: {missing_feat}")

    return df_feat, df_risk


def build_candidate_matrix(
    df_feat: pd.DataFrame,
    df_risk: pd.DataFrame,
    catalog: Optional[Dict[str, InterventionDefinition]] = None,
    enabled_interventions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Constructs candidate eligibility, physical capacities, and marginal risk response
    coefficients across eligible H3 cells under Formulations F-24.1, F-24.2, and F-24.5.
    """
    if catalog is None:
        catalog = get_ratified_intervention_catalog()

    if enabled_interventions is not None:
        norm_enabled = {normalize_intervention_code(c) for c in enabled_interventions}
        catalog = {k: v for k, v in catalog.items() if k in norm_enabled}

    # Merge on h3_cell_id
    df_merged = df_risk[["h3_cell_id", "H_i", "E_i", "V_i", "risk_i", "overall_risk_eligibility"]].merge(
        df_feat[[
            "h3_cell_id", "cell_area_km2", "norm_ndbi", "road_length_m",
            "green_space_area_m2", "water_body_area_m2", "norm_ndvi_deficit", "population_2020"
        ]],
        on="h3_cell_id",
        how="inner"
    )

    # Filter to eligible analytical mesh only (N_e = 3,113)
    eligible_df = df_merged[df_merged["overall_risk_eligibility"] == True].copy().reset_index(drop=True)
    n_cells = len(eligible_df)
    intervention_list = list(catalog.values())
    n_interv = len(intervention_list)

    if n_cells == 0 or n_interv == 0:
        return {
            "eligible_df": eligible_df,
            "intervention_list": intervention_list,
            "cand_df": pd.DataFrame(),
            "n_candidates": 0,
        }

    A_cell = eligible_df["cell_area_km2"].values * 1e6  # km^2 to m^2
    norm_ndbi = eligible_df["norm_ndbi"].values
    road_length = eligible_df["road_length_m"].values
    norm_ndvi_def = eligible_df["norm_ndvi_deficit"].values
    green_space = eligible_df["green_space_area_m2"].values
    water_body = eligible_df["water_body_area_m2"].values
    H = eligible_df["H_i"].values
    E = eligible_df["E_i"].values
    V = eligible_df["V_i"].values

    # Treatable open ground area (F-24.2 item 3 & F-24.6 item 4)
    open_area = np.maximum(0.0, A_cell - green_space - water_body - norm_ndbi * A_cell)

    cand_records = []

    for a_idx, inv in enumerate(intervention_list):
        code = inv.code
        e_a = inv.cooling_coefficient_degC_per_unit
        v_a = inv.biophysical_susceptibility_factor
        q_min = inv.minimum_lot_size

        # F-24.5: Marginal risk response coefficient
        # r_{i, a} = E_i * [ V_i * (0.25 * e_a / Delta_T_scale) + H_i * (v_a / A_cell_i) ]
        r_col = E * (V * (HAZARD_LST_WEIGHT * e_a / DELTA_T_SCALE_DEGC) + H * (v_a / A_cell))

        # F-24.2: Candidate eligibility and capacity rules
        if code == "cool_roof":
            elig = (norm_ndbi > 0.05)
            cap = 0.40 * norm_ndbi * A_cell
        elif code == "street_tree_shade":
            elig = (road_length > 0)
            cap = np.minimum(800.0, np.floor(2.0 * road_length / 15.0))
        elif code == "green_corridor":
            elig = (norm_ndvi_def > 0.15)
            cap = 0.10 * open_area
        elif code == "permeable_surface":
            elig = (norm_ndbi > 0.10) & (road_length > 0)
            cap = 0.20 * road_length * 3.0
        elif code == "bioswale":
            elig = (road_length >= 100.0)
            cap = 0.05 * road_length * 2.0
        else:
            elig = np.zeros(n_cells, dtype=bool)
            cap = np.zeros(n_cells, dtype=float)

        # Enforce minimum lot size feasibility: cap >= q_min
        feasible = elig & (cap >= q_min)

        for cell_idx in np.where(feasible)[0]:
            cand_records.append({
                "cell_idx": cell_idx,
                "h3_cell_id": eligible_df.at[cell_idx, "h3_cell_id"],
                "intervention_idx": a_idx,
                "intervention_code": code,
                "q_min": q_min,
                "Q_max": float(cap[cell_idx]),
                "unit_cost": inv.unit_cost_inr,
                "fixed_cost": inv.mobilization_fixed_cost_inr,
                "marginal_risk_r": float(r_col[cell_idx]),
                "cooling_e": e_a,
                "is_ground": inv.is_ground_intervention,
                "open_area": float(open_area[cell_idx]),
            })

    cand_df = pd.DataFrame(cand_records)

    return {
        "eligible_df": eligible_df,
        "intervention_list": intervention_list,
        "cand_df": cand_df,
        "n_candidates": len(cand_df),
        "open_area": open_area,
    }


def build_milp_model(
    candidate_data: Dict[str, Any],
    budget_inr: float,
) -> Dict[str, Any]:
    """
    Constructs standard-form MILP matrices and constraints under Formulation F-24.6.
    Standard form: min c^T y s.t. A_ub y <= b_ub, y_lb <= y <= y_ub, y_j in {0, 1}
    """
    cand_df = candidate_data["cand_df"]
    n_cands = len(cand_df)

    if n_cands == 0 or budget_inr <= 0:
        return {
            "n_vars": 0,
            "n_constraints": 0,
            "c_obj": np.array([]),
            "integrality": np.array([]),
            "bounds": None,
            "constraints": None,
            "cand_df": cand_df,
            "budget_inr": budget_inr,
        }

    # Variables: y = [x_0..x_{K-1} (binary), q_0..q_{K-1} (continuous)] -> 2 * n_cands
    n_vars = 2 * n_cands

    # Objective: max sum r_k q_k => min -sum r_k q_k
    r_vec = cand_df["marginal_risk_r"].values
    c_obj = np.concatenate([np.zeros(n_cands), -r_vec])

    integrality = np.concatenate([np.ones(n_cands), np.zeros(n_cands)])
    bounds = Bounds(
        np.zeros(n_vars),
        np.concatenate([np.ones(n_cands), np.full(n_cands, np.inf)])
    )

    F_vec = cand_df["fixed_cost"].values
    c_vec = cand_df["unit_cost"].values
    q_min_vec = cand_df["q_min"].values
    Q_max_vec = cand_df["Q_max"].values

    # Sparse Matrix Assembly
    rows = []
    cols = []
    data = []

    # Constraint 1: Budget Envelope (sum F*x + c*q <= B)
    rows.extend([0] * n_vars)
    cols.extend(range(n_vars))
    data.extend(np.concatenate([F_vec, c_vec]))

    # Constraint 2: Semi-continuous lower bounds (q_min * x - q <= 0)
    k_range = np.arange(n_cands)
    rows.extend(1 + k_range)
    cols.extend(k_range)
    data.extend(q_min_vec)

    rows.extend(1 + k_range)
    cols.extend(n_cands + k_range)
    data.extend([-1.0] * n_cands)

    # Constraint 3: Semi-continuous upper bounds (-Q_max * x + q <= 0)
    rows.extend(1 + n_cands + k_range)
    cols.extend(k_range)
    data.extend(-Q_max_vec)

    rows.extend(1 + n_cands + k_range)
    cols.extend(n_cands + k_range)
    data.extend([1.0] * n_cands)

    # Constraint 4: Ground surface mutual compatibility
    # Identify cells with multiple ground-based candidates
    ground_mask = cand_df["is_ground"].values
    ground_indices = np.where(ground_mask)[0]
    cell_to_ground_cands = {}
    for k in ground_indices:
        c_idx = cand_df.at[k, "cell_idx"]
        if c_idx not in cell_to_ground_cands:
            cell_to_ground_cands[c_idx] = []
        cell_to_ground_cands[c_idx].append(k)

    ground_rhs = []
    for row_offset, (c_idx, k_list) in enumerate(cell_to_ground_cands.items()):
        r_idx = 1 + 2 * n_cands + row_offset
        for k in k_list:
            rows.append(r_idx)
            cols.append(n_cands + k)
            data.append(1.0)
        ground_rhs.append(cand_df.at[k_list[0], "open_area"])

    total_rows = 1 + 2 * n_cands + len(ground_rhs)
    lhs = np.full(total_rows, -np.inf)
    rhs = np.concatenate([[budget_inr], np.zeros(2 * n_cands), ground_rhs])

    A_csc = coo_matrix((data, (rows, cols)), shape=(total_rows, n_vars)).tocsc()
    constraints = LinearConstraint(A_csc, lhs, rhs)

    return {
        "n_vars": n_vars,
        "n_constraints": total_rows,
        "c_obj": c_obj,
        "integrality": integrality,
        "bounds": bounds,
        "constraints": constraints,
        "cand_df": cand_df,
        "budget_inr": budget_inr,
    }


def solve_milp_model(
    milp_data: Dict[str, Any],
    time_limit_sec: float = 120.0,
    mip_rel_gap: float = 0.01,
) -> Dict[str, Any]:
    """
    Executes the HiGHS branch-and-cut solver and records complete run diagnostics.
    """
    cand_df = milp_data["cand_df"]
    n_vars = milp_data["n_vars"]
    budget_inr = milp_data["budget_inr"]

    # Handle zero budget or empty candidates immediately
    if n_vars == 0 or budget_inr <= 0:
        return {
            "solver_name": "HiGHS (scipy.optimize.milp)",
            "solve_status": "OPTIMAL",
            "is_feasible": True,
            "optimal_objective_value": 0.0,
            "total_allocated_cost_inr": 0.0,
            "budget_slack_inr": max(0.0, budget_inr),
            "execution_duration_sec": 0.0,
            "x_solution": np.array([]),
            "q_solution": np.array([]),
            "allocation_df": pd.DataFrame(),
            "termination_message": "Trivial empty portfolio for zero budget or empty candidates.",
        }

    t_start = time.time()
    options = {
        "time_limit": time_limit_sec,
        "mip_rel_gap": mip_rel_gap,
    }

    res = milp(
        c=milp_data["c_obj"],
        integrality=milp_data["integrality"],
        bounds=milp_data["bounds"],
        constraints=milp_data["constraints"],
        options=options,
    )
    t_end = time.time()
    duration = t_end - t_start

    n_cands = len(cand_df)
    status_map = {
        0: "OPTIMAL",
        1: "FEASIBLE",
        2: "INFEASIBLE",
        3: "UNBOUNDED",
    }
    solve_status = status_map.get(res.status, "SOLVER_ERROR")
    is_feasible = res.success or res.status in (0, 1)

    if not is_feasible:
        return {
            "solver_name": "HiGHS (scipy.optimize.milp)",
            "solve_status": solve_status,
            "is_feasible": False,
            "optimal_objective_value": 0.0,
            "total_allocated_cost_inr": 0.0,
            "budget_slack_inr": budget_inr,
            "execution_duration_sec": duration,
            "x_solution": np.zeros(n_cands),
            "q_solution": np.zeros(n_cands),
            "allocation_df": pd.DataFrame(),
            "termination_message": res.message,
        }

    x_sol = res.x[:n_cands]
    q_sol = res.x[n_cands:]

    # Build granular allocation table
    active_indices = np.where(x_sol > 0.5)[0]
    alloc_records = []

    for k in active_indices:
        q_val = float(q_sol[k])
        f_cost = float(cand_df.at[k, "fixed_cost"])
        u_cost = float(cand_df.at[k, "unit_cost"])
        tot_cost = f_cost + u_cost * q_val
        risk_red = float(cand_df.at[k, "marginal_risk_r"] * q_val)
        modeled_cooling = float(cand_df.at[k, "cooling_e"] * q_val)

        alloc_records.append({
            "h3_cell_id": cand_df.at[k, "h3_cell_id"],
            "intervention_type": cand_df.at[k, "intervention_code"],
            "activation": 1,
            "quantity": q_val,
            "unit": cand_df.at[k, "intervention_code"],  # will map to catalog unit
            "unit_cost": u_cost,
            "fixed_cost": f_cost,
            "total_cost": tot_cost,
            "modeled_effect": modeled_cooling,
            "modeled_risk_reduction": risk_red,
        })

    alloc_df = pd.DataFrame(alloc_records)
    total_cost = float(np.sum(alloc_df["total_cost"])) if len(alloc_df) > 0 else 0.0
    obj_val = float(-res.fun) if res.fun is not None else 0.0

    return {
        "solver_name": "HiGHS (scipy.optimize.milp)",
        "solve_status": solve_status,
        "is_feasible": is_feasible,
        "optimal_objective_value": obj_val,
        "total_allocated_cost_inr": total_cost,
        "budget_slack_inr": budget_inr - total_cost,
        "execution_duration_sec": duration,
        "x_solution": x_sol,
        "q_solution": q_sol,
        "allocation_df": alloc_df,
        "termination_message": res.message,
    }


def validate_solution_feasibility(
    candidate_data: Dict[str, Any],
    solution: Dict[str, Any],
    budget_inr: float,
    tol: float = 1e-4,
) -> Dict[str, Any]:
    """
    Independent post-solve audit verifying all hard constraints and objective reconstruction.
    """
    cand_df = candidate_data["cand_df"]
    x_sol = solution["x_solution"]
    q_sol = solution["q_solution"]

    if len(x_sol) == 0:
        return {
            "all_constraints_satisfied": True,
            "budget_valid": True,
            "lot_sizes_valid": True,
            "capacities_valid": True,
            "ground_compatibility_valid": True,
            "objective_reconstructed_accurately": True,
            "max_cooling_cap_respected": True,
            "violations": [],
        }

    violations = []

    # 1. Budget Verification
    F_vec = cand_df["fixed_cost"].values
    c_vec = cand_df["unit_cost"].values
    recalc_cost = float(np.sum(F_vec * (x_sol > 0.5) + c_vec * q_sol))
    if recalc_cost > budget_inr + tol:
        violations.append(f"Budget exceeded: {recalc_cost:.2f} > {budget_inr:.2f}")

    # 2. Semi-continuous Lot and Capacity Bounds
    q_min_vec = cand_df["q_min"].values
    Q_max_vec = cand_df["Q_max"].values

    for k in range(len(cand_df)):
        if x_sol[k] > 0.5:
            if q_sol[k] < q_min_vec[k] - tol:
                violations.append(f"Candidate {k} below minimum lot: {q_sol[k]} < {q_min_vec[k]}")
            if q_sol[k] > Q_max_vec[k] + tol:
                violations.append(f"Candidate {k} exceeds max capacity: {q_sol[k]} > {Q_max_vec[k]}")
        else:
            if abs(q_sol[k]) > tol:
                violations.append(f"Inactive candidate {k} has non-zero quantity: {q_sol[k]}")

    # 3. Ground Surface Compatibility
    ground_mask = cand_df["is_ground"].values
    ground_indices = np.where(ground_mask)[0]
    cell_to_ground_cands = {}
    for k in ground_indices:
        c_idx = cand_df.at[k, "cell_idx"]
        if c_idx not in cell_to_ground_cands:
            cell_to_ground_cands[c_idx] = []
        cell_to_ground_cands[c_idx].append(k)

    for c_idx, k_list in cell_to_ground_cands.items():
        total_ground_q = sum(q_sol[k] for k in k_list)
        open_a = cand_df.at[k_list[0], "open_area"]
        if total_ground_q > open_a + tol:
            violations.append(f"Cell {c_idx} ground area over-allocated: {total_ground_q} > {open_a}")

    # 4. Objective Reconstruction
    r_vec = cand_df["marginal_risk_r"].values
    recalc_obj = float(np.sum(r_vec * q_sol))
    solver_obj = solution["optimal_objective_value"]
    if abs(recalc_obj - solver_obj) > 1e-4:
        violations.append(f"Objective mismatch: solver={solver_obj:.6f} vs recalc={recalc_obj:.6f}")

    # 5. F-24.4 Modeled Intra-Cell Cooling Cap Verification (4.0°C)
    cell_to_cands = {}
    for k in range(len(cand_df)):
        c_idx = cand_df.at[k, "cell_idx"]
        if c_idx not in cell_to_cands:
            cell_to_cands[c_idx] = []
        cell_to_cands[c_idx].append(k)

    cooling_cap_respected = True
    for c_idx, k_list in cell_to_cands.items():
        total_dT = sum(cand_df.at[k, "cooling_e"] * q_sol[k] for k in k_list)
        if total_dT > MAX_MODELED_COOLING_CAP_DEGC + tol:
            cooling_cap_respected = False
            violations.append(f"Cell {c_idx} exceeds modeled cooling cap: {total_dT:.2f}°C > 4.0°C")

    return {
        "all_constraints_satisfied": len(violations) == 0,
        "recalculated_cost_inr": recalc_cost,
        "recalculated_objective": recalc_obj,
        "max_cooling_cap_respected": cooling_cap_respected,
        "violations": violations,
    }


def execute_production_optimization_pipeline(
    scenario_budget_inr: float = 10_000_000.0,
    time_limit_sec: float = 120.0,
    mip_rel_gap: float = 0.01,
    feature_parquet_path: Path = DEFAULT_FEATURE_MATRIX_PARQUET,
    risk_parquet_path: Path = DEFAULT_RISK_PARQUET,
    output_parquet_path: Path = DEFAULT_ALLOCATION_PARQUET,
    output_manifest_path: Path = DEFAULT_RUN_MANIFEST,
) -> Dict[str, Any]:
    """
    End-to-end execution of the CLIMORA Phase 1G production solver pipeline.
    """
    run_id = f"OPT-PUNE-2025-SCENARIO-{uuid.uuid4().hex[:8].upper()}"
    t0 = time.time()

    logger.info(f"Initiating CLIMORA Optimization Run: {run_id}")
    logger.info(f"Scenario Budget: INR {scenario_budget_inr:,.2f}")

    # 1. Load canonical inputs
    df_feat, df_risk = load_canonical_inputs(feature_parquet_path, risk_parquet_path)
    feat_sha256 = calculate_sha256(feature_parquet_path)
    risk_sha256 = calculate_sha256(risk_parquet_path)

    # 2. Build candidate matrix
    catalog = get_ratified_intervention_catalog()
    candidate_data = build_candidate_matrix(df_feat, df_risk, catalog)
    logger.info(f"Built {candidate_data['n_candidates']} feasible candidate pairs across {len(candidate_data['eligible_df'])} eligible cells.")

    # 3. Build MILP model
    milp_data = build_milp_model(candidate_data, scenario_budget_inr)
    logger.info(f"MILP constructed with {milp_data['n_vars']} variables and {milp_data['n_constraints']} constraints.")

    # 4. Solve with HiGHS
    solution = solve_milp_model(milp_data, time_limit_sec=time_limit_sec, mip_rel_gap=mip_rel_gap)
    logger.info(f"Solver terminated with status {solution['solve_status']} in {solution['execution_duration_sec']:.2f}s.")

    # 5. Independent feasibility validation
    validation = validate_solution_feasibility(candidate_data, solution, scenario_budget_inr)
    if not validation["all_constraints_satisfied"]:
        logger.error(f"Post-solve validation failed: {validation['violations']}")
        raise ValueError(f"Post-solve feasibility violations detected: {validation['violations']}")

    # 6. Format and materialize canonical allocation parquet
    alloc_df = solution["allocation_df"].copy()
    if len(alloc_df) > 0:
        alloc_df["optimization_run_id"] = run_id
        # Map units to human-readable standard
        unit_map = {code: inv.unit for code, inv in catalog.items()}
        alloc_df["unit"] = alloc_df["intervention_type"].map(unit_map)

        # Merge cell contextual attributes for explainability
        cell_info = candidate_data["eligible_df"][["h3_cell_id", "risk_i", "population_2020"]].set_index("h3_cell_id")
        alloc_df["baseline_cell_risk"] = alloc_df["h3_cell_id"].map(cell_info["risk_i"])
        alloc_df["population_2020"] = alloc_df["h3_cell_id"].map(cell_info["population_2020"])
        alloc_df["marginal_roi"] = alloc_df["modeled_risk_reduction"] / alloc_df["total_cost"]

        # Reorder columns per contract specification
        cols_order = [
            "optimization_run_id", "h3_cell_id", "intervention_type", "activation",
            "quantity", "unit", "unit_cost", "fixed_cost", "total_cost",
            "modeled_effect", "modeled_risk_reduction", "baseline_cell_risk",
            "population_2020", "marginal_roi"
        ]
        alloc_df = alloc_df[[c for c in cols_order if c in alloc_df.columns]]
    else:
        alloc_df = pd.DataFrame(columns=[
            "optimization_run_id", "h3_cell_id", "intervention_type", "activation",
            "quantity", "unit", "unit_cost", "fixed_cost", "total_cost",
            "modeled_effect", "modeled_risk_reduction"
        ])

    output_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    alloc_df.to_parquet(output_parquet_path, index=False)
    alloc_sha256 = calculate_sha256(output_parquet_path)

    # 7. Generate run manifest
    total_runtime = time.time() - t0
    manifest = {
        "schema_version": "1.0.0",
        "phase": "Phase 1G",
        "manifest_type": "CLIMORA_OPTIMIZATION_RUN_PROVENANCE",
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "formulations_ratified": [
            "F-24.1", "F-24.2", "F-24.3", "F-24.4", "F-24.5", "F-24.6", "F-25.1"
        ],
        "input_artifacts": {
            "feature_matrix_path": str(feature_parquet_path.relative_to(PROJECT_ROOT)),
            "feature_matrix_sha256": feat_sha256,
            "risk_surface_path": str(risk_parquet_path.relative_to(PROJECT_ROOT)),
            "risk_surface_sha256": risk_sha256,
        },
        "scenario_parameters": {
            "budget_inr": scenario_budget_inr,
            "time_limit_sec": time_limit_sec,
            "mip_rel_gap": mip_rel_gap,
            "modeled_cooling_cap_degC": MAX_MODELED_COOLING_CAP_DEGC,
        },
        "solver_performance": {
            "solver_engine": solution["solver_name"],
            "solve_status": solution["solve_status"],
            "is_feasible": solution["is_feasible"],
            "solver_runtime_sec": solution["execution_duration_sec"],
            "total_pipeline_runtime_sec": total_runtime,
            "candidate_pairs_count": candidate_data["n_candidates"],
            "variables_count": milp_data["n_vars"],
            "constraints_count": milp_data["n_constraints"],
        },
        "portfolio_summary": {
            "total_allocated_cost_inr": solution["total_allocated_cost_inr"],
            "budget_slack_inr": solution["budget_slack_inr"],
            "budget_utilization_pct": (solution["total_allocated_cost_inr"] / scenario_budget_inr * 100.0) if scenario_budget_inr > 0 else 0.0,
            "optimal_risk_reduction": solution["optimal_objective_value"],
            "active_allocations_count": len(alloc_df),
            "unique_cells_treated_count": alloc_df["h3_cell_id"].nunique() if len(alloc_df) > 0 else 0,
            "interventions_deployed": alloc_df["intervention_type"].value_counts().to_dict() if len(alloc_df) > 0 else {},
        },
        "output_artifacts": {
            "allocation_parquet_path": str(output_parquet_path.relative_to(PROJECT_ROOT)),
            "allocation_parquet_sha256": alloc_sha256,
            "row_count": len(alloc_df),
        },
        "governance_audit": {
            "f22_risk_surface_unmodified": True,
            "f23_1_spatial_autocorrelation_unmodified": True,
            "ward_dependency": "NONE (H3 Resolution 9 analytical mesh only)",
            "post_solve_validation_passed": validation["all_constraints_satisfied"],
        }
    }

    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Optimization run completed successfully. Allocation saved to {output_parquet_path}")

    return {
        "run_id": run_id,
        "manifest": manifest,
        "allocation_df": alloc_df,
        "solution": solution,
        "validation": validation,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = execute_production_optimization_pipeline()
    print(f"Run ID: {res['run_id']}")
    print(f"Status: {res['solution']['solve_status']}")
    print(f"Allocations: {len(res['allocation_df'])}")
    print(f"Cost: INR {res['solution']['total_allocated_cost_inr']:,.2f}")
    print(f"Objective: {res['solution']['optimal_objective_value']:.6f}")
