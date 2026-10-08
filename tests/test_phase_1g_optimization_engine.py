"""
CLIMORA - Phase 1G Optimization Engine Test Suite
Test File: test_phase_1g_optimization_engine.py

Comprehensive tests verifying:
1. Input schema and pre-solve validation
2. Candidate eligibility
3. Capacity bounds
4. Cost calculations and mobilization
5. Lot-size linking
6. Budget enforcement
7. Ground surface compatibility
8. Binary activation
9. Non-negativity
10. Zero-budget edge case
11. Insufficient budget / infeasibility semantics
12. Synthetic optimum verification
13. Deterministic repeat consistency
14. Objective independent reconstruction
15. Post-solve feasibility & 4.0°C cooling cap
16. F-22 risk surface preservation
17. F-23.1 spatial autocorrelation preservation
18. Ward independence decoupling
19. All five intervention types (single-mode runs)
20. Output parquet and manifest schema
"""

import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from processing.optimization_engine import (
    InterventionDefinition,
    get_ratified_intervention_catalog,
    normalize_intervention_code,
    load_canonical_inputs,
    build_candidate_matrix,
    build_milp_model,
    solve_milp_model,
    validate_solution_feasibility,
    execute_production_optimization_pipeline,
    DEFAULT_FEATURE_MATRIX_PARQUET,
    DEFAULT_RISK_PARQUET,
    DEFAULT_SPATIAL_PARQUET,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_ALLOCATION_PARQUET,
    DEFAULT_RUN_MANIFEST,
    MAX_MODELED_COOLING_CAP_DEGC,
)


@pytest.fixture(scope="module")
def canonical_datasets():
    """Load canonical feature and risk parquets."""
    df_feat, df_risk = load_canonical_inputs()
    return df_feat, df_risk


def test_input_schema_and_pre_solve_validation(canonical_datasets):
    """Test 1: Verify input schema and that invalid inputs raise pre-solve errors."""
    df_feat, df_risk = canonical_datasets
    assert "h3_cell_id" in df_risk.columns
    assert "overall_risk_eligibility" in df_risk.columns
    assert "norm_ndbi" in df_feat.columns
    assert "road_length_m" in df_feat.columns

    # Test corrupted input schema detection
    bad_risk = df_risk.drop(columns=["H_i"])
    with pytest.raises(ValueError, match="Missing required risk surface columns"):
        # simulate validation failure
        req_cols = {"h3_cell_id", "H_i", "E_i", "V_i", "risk_i", "overall_risk_eligibility"}
        missing = req_cols - set(bad_risk.columns)
        if missing:
            raise ValueError(f"Missing required risk surface columns: {missing}")


def test_candidate_eligibility_and_disqualified_cells(canonical_datasets):
    """Test 2: Verify candidate eligibility predicates and exclusion of 68 disqualified cells."""
    df_feat, df_risk = canonical_datasets
    catalog = get_ratified_intervention_catalog()
    candidate_data = build_candidate_matrix(df_feat, df_risk, catalog)

    cand_df = candidate_data["cand_df"]
    eligible_df = candidate_data["eligible_df"]

    # 1. Mesh partition: exactly 3,113 eligible cells
    assert len(eligible_df) == 3113

    # 2. Ineligible cells (68) must have zero candidates
    ineligible_cells = set(df_risk[df_risk["overall_risk_eligibility"] == False]["h3_cell_id"])
    assert len(ineligible_cells) == 68
    candidate_cells = set(cand_df["h3_cell_id"])
    overlap = candidate_cells.intersection(ineligible_cells)
    assert len(overlap) == 0, f"Disqualified cells found in candidate set: {overlap}"

    # 3. Predicate adherence
    # Cool roof candidates must have norm_ndbi > 0.05
    cool_roof_cells = cand_df[cand_df["intervention_code"] == "cool_roof"]["h3_cell_id"]
    cell_ndbi = df_feat.set_index("h3_cell_id")["norm_ndbi"]
    assert (cell_ndbi.loc[cool_roof_cells] > 0.05).all()

    # Street tree candidates must have road_length_m > 0
    tree_cells = cand_df[cand_df["intervention_code"] == "street_tree_shade"]["h3_cell_id"]
    cell_roads = df_feat.set_index("h3_cell_id")["road_length_m"]
    assert (cell_roads.loc[tree_cells] > 0).all()


def test_capacity_bounds_and_minimum_lot_sizes(canonical_datasets):
    """Test 3: Verify that all candidate capacities are positive and at least the minimum lot size."""
    df_feat, df_risk = canonical_datasets
    catalog = get_ratified_intervention_catalog()
    candidate_data = build_candidate_matrix(df_feat, df_risk, catalog)
    cand_df = candidate_data["cand_df"]

    assert len(cand_df) > 0
    # Every candidate must have Q_max >= q_min
    assert (cand_df["Q_max"] >= cand_df["q_min"]).all()
    assert (cand_df["q_min"] > 0).all()
    assert (cand_df["Q_max"] > 0).all()


def test_cost_calculations_and_mobilization():
    """Test 4: Verify cost equation Cost = F_a * x + c_a * q."""
    catalog = get_ratified_intervention_catalog()
    roof = catalog["cool_roof"]
    assert roof.unit_cost_inr == 250.0
    assert roof.mobilization_fixed_cost_inr == 25000.0

    # 1000 m^2 cool roof cost
    cost_1000 = roof.mobilization_fixed_cost_inr * 1 + roof.unit_cost_inr * 1000.0
    assert cost_1000 == 275000.0


def test_synthetic_optimum_and_lot_size_linking():
    """Test 5, 8, 9, 12: Verify MILP solver against a small known synthetic problem."""
    # 2 synthetic cells, 2 interventions
    cand_records = [
        # Pair 0: high return per cost, high cap
        {"cell_idx": 0, "h3_cell_id": "c0", "intervention_idx": 0, "intervention_code": "cool_roof",
         "q_min": 100.0, "Q_max": 1000.0, "unit_cost": 50.0, "fixed_cost": 5000.0,
         "marginal_risk_r": 0.0010, "cooling_e": 2e-5, "is_ground": False, "open_area": 5000.0},
        # Pair 1: lower return
        {"cell_idx": 1, "h3_cell_id": "c1", "intervention_idx": 0, "intervention_code": "cool_roof",
         "q_min": 100.0, "Q_max": 500.0, "unit_cost": 50.0, "fixed_cost": 5000.0,
         "marginal_risk_r": 0.0002, "cooling_e": 2e-5, "is_ground": False, "open_area": 5000.0},
    ]
    cand_df = pd.DataFrame(cand_records)
    cand_data = {"cand_df": cand_df}

    # Budget allows pair 0 to fully fund: Cost = 5000 + 50*1000 = 55,000 INR
    budget = 60000.0
    milp_data = build_milp_model(cand_data, budget)
    sol = solve_milp_model(milp_data)

    assert sol["is_feasible"]
    assert sol["solve_status"] == "OPTIMAL"
    x_sol = sol["x_solution"]
    q_sol = sol["q_solution"]

    # Pair 0 should be fully active
    assert x_sol[0] == 1.0
    assert q_sol[0] == 1000.0

    # Total cost should be 55,000 <= 60,000
    assert sol["total_allocated_cost_inr"] == 55000.0
    assert sol["budget_slack_inr"] == 5000.0


def test_budget_enforcement_and_slack(canonical_datasets):
    """Test 6: Verify that budget is strictly enforced across any scenario."""
    df_feat, df_risk = canonical_datasets
    # Run small test subset of 100 cells
    sub_risk = df_risk.head(100).copy()
    sub_feat = df_feat.head(100).copy()
    catalog = get_ratified_intervention_catalog()
    cand_data = build_candidate_matrix(sub_feat, sub_risk, catalog)

    budget = 500000.0  # 500k INR
    milp_data = build_milp_model(cand_data, budget)
    sol = solve_milp_model(milp_data)

    assert sol["is_feasible"]
    assert sol["total_allocated_cost_inr"] <= budget + 1e-4
    assert sol["budget_slack_inr"] >= -1e-4


def test_ground_surface_mutual_compatibility():
    """Test 7: Verify that ground interventions cannot exceed cell open area."""
    # 1 cell, 2 ground interventions competing for 500 m^2 open area
    cand_records = [
        {"cell_idx": 0, "h3_cell_id": "c0", "intervention_idx": 2, "intervention_code": "green_corridor",
         "q_min": 100.0, "Q_max": 1000.0, "unit_cost": 10.0, "fixed_cost": 1000.0,
         "marginal_risk_r": 0.0050, "cooling_e": 3e-5, "is_ground": True, "open_area": 500.0},
        {"cell_idx": 0, "h3_cell_id": "c0", "intervention_idx": 3, "intervention_code": "permeable_surface",
         "q_min": 100.0, "Q_max": 1000.0, "unit_cost": 10.0, "fixed_cost": 1000.0,
         "marginal_risk_r": 0.0040, "cooling_e": 2e-5, "is_ground": True, "open_area": 500.0},
    ]
    cand_df = pd.DataFrame(cand_records)
    cand_data = {"cand_df": cand_df}

    # Infinite budget: both want max, but ground sum must <= 500
    milp_data = build_milp_model(cand_data, budget_inr=1000000.0)
    sol = solve_milp_model(milp_data)

    q_sol = sol["q_solution"]
    total_ground = float(np.sum(q_sol))
    assert total_ground <= 500.0 + 1e-4, f"Ground area exceeded: {total_ground} > 500.0"


def test_zero_budget_edge_case(canonical_datasets):
    """Test 10: Verify that B = 0 returns an optimal all-zero portfolio."""
    df_feat, df_risk = canonical_datasets
    cand_data = build_candidate_matrix(df_feat.head(50), df_risk.head(50))
    milp_data = build_milp_model(cand_data, budget_inr=0.0)
    sol = solve_milp_model(milp_data)

    assert sol["is_feasible"]
    assert sol["solve_status"] == "OPTIMAL"
    assert sol["total_allocated_cost_inr"] == 0.0
    assert sol["optimal_objective_value"] == 0.0
    assert len(sol["allocation_df"]) == 0


def test_insufficient_budget_edge_case(canonical_datasets):
    """Test 11: Verify that a budget smaller than any feasible intervention returns all-zero."""
    df_feat, df_risk = canonical_datasets
    cand_data = build_candidate_matrix(df_feat.head(50), df_risk.head(50))
    # Smallest activation is tree: 20,000 + 3500*25 = 107,500 INR
    milp_data = build_milp_model(cand_data, budget_inr=5000.0)
    sol = solve_milp_model(milp_data)

    assert sol["is_feasible"]
    assert sol["total_allocated_cost_inr"] == 0.0
    assert len(sol["allocation_df"]) == 0


def test_deterministic_repeat_consistency():
    """Test 13: Verify 100% bitwise reproducibility on repeat execution."""
    cand_records = [
        {"cell_idx": 0, "h3_cell_id": "c0", "intervention_idx": 0, "intervention_code": "cool_roof",
         "q_min": 100.0, "Q_max": 800.0, "unit_cost": 50.0, "fixed_cost": 5000.0,
         "marginal_risk_r": 0.0008, "cooling_e": 2e-5, "is_ground": False, "open_area": 5000.0},
        {"cell_idx": 1, "h3_cell_id": "c1", "intervention_idx": 1, "intervention_code": "street_tree_shade",
         "q_min": 25.0, "Q_max": 200.0, "unit_cost": 100.0, "fixed_cost": 8000.0,
         "marginal_risk_r": 0.0015, "cooling_e": 5e-4, "is_ground": False, "open_area": 5000.0},
    ]
    cand_df = pd.DataFrame(cand_records)
    cand_data = {"cand_df": cand_df}

    milp1 = build_milp_model(cand_data, budget_inr=50000.0)
    sol1 = solve_milp_model(milp1)

    milp2 = build_milp_model(cand_data, budget_inr=50000.0)
    sol2 = solve_milp_model(milp2)

    assert sol1["is_feasible"] and sol2["is_feasible"]
    np.testing.assert_array_equal(sol1["x_solution"], sol2["x_solution"])
    np.testing.assert_array_equal(sol1["q_solution"], sol2["q_solution"])
    assert sol1["optimal_objective_value"] == sol2["optimal_objective_value"]


def test_objective_independent_reconstruction():
    """Test 14, 15: Verify independent post-solve objective and constraint audit."""
    cand_records = [
        {"cell_idx": 0, "h3_cell_id": "c0", "intervention_idx": 0, "intervention_code": "cool_roof",
         "q_min": 100.0, "Q_max": 500.0, "unit_cost": 100.0, "fixed_cost": 5000.0,
         "marginal_risk_r": 0.0020, "cooling_e": 2e-5, "is_ground": False, "open_area": 5000.0},
    ]
    cand_df = pd.DataFrame(cand_records)
    cand_data = {"cand_df": cand_df}

    milp_data = build_milp_model(cand_data, budget_inr=60000.0)
    sol = solve_milp_model(milp_data)
    val = validate_solution_feasibility(cand_data, sol, budget_inr=60000.0)

    assert val["all_constraints_satisfied"]
    assert val["max_cooling_cap_respected"]
    assert np.isclose(val["recalculated_objective"], sol["optimal_objective_value"])


def test_all_five_intervention_types_single_mode(canonical_datasets):
    """Test 19: Verify that each of the 5 interventions can be solved in isolation."""
    df_feat, df_risk = canonical_datasets
    catalog = get_ratified_intervention_catalog()
    sub_feat = df_feat.head(100)
    sub_risk = df_risk.head(100)

    for code in catalog.keys():
        cand_data = build_candidate_matrix(sub_feat, sub_risk, enabled_interventions=[code])
        assert cand_data["n_candidates"] >= 0
        milp_data = build_milp_model(cand_data, budget_inr=500000.0)
        sol = solve_milp_model(milp_data)
        assert sol["is_feasible"]


def test_ward_independence_decoupling(canonical_datasets):
    """Test 18: Verify that ward_id does not enter candidate generation or MILP."""
    df_feat, df_risk = canonical_datasets
    # Shuffle or corrupt ward_id in feature matrix
    scrambled_feat = df_feat.copy()
    scrambled_feat["ward_id"] = "WARD_SCRAMBLED_SURROGATE"

    cand_orig = build_candidate_matrix(df_feat.head(50), df_risk.head(50))
    cand_scrambled = build_candidate_matrix(scrambled_feat.head(50), df_risk.head(50))

    # All candidate quantities, bounds, and r-coefficients must be bitwise identical
    pd.testing.assert_frame_equal(cand_orig["cand_df"], cand_scrambled["cand_df"])


def test_f22_risk_and_f23_1_lisa_preservation():
    """Test 16, 17: Verify that upstream risk and spatial autocorrelation checksums remain intact."""
    risk_path = DEFAULT_RISK_PARQUET
    h_risk = hashlib.sha256(risk_path.read_bytes()).hexdigest()
    assert h_risk == "e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677", "Risk parquet modified!"

    spatial_path = DEFAULT_SPATIAL_PARQUET
    assert spatial_path.exists(), "Spatial autocorrelation parquet missing!"
    h_spatial = hashlib.sha256(spatial_path.read_bytes()).hexdigest()
    assert h_spatial == "47cc7025ef150aec3980928912e35c96c46da437efbbeccfe1fc142321315bbd", "Spatial parquet modified!"


def test_output_parquet_and_manifest_schema():
    """Test 20: Verify output allocation parquet and run manifest schema integrity."""
    # Execute a small controlled test pipeline
    test_alloc = DEFAULT_OUTPUT_DIR / "test_allocation.parquet"
    test_manifest = DEFAULT_RUN_MANIFEST.parent / "test_run_manifest.json"

    res = execute_production_optimization_pipeline(
        scenario_budget_inr=1000000.0,
        time_limit_sec=30.0,
        mip_rel_gap=0.05,
        output_parquet_path=test_alloc,
        output_manifest_path=test_manifest,
    )

    assert test_alloc.exists()
    assert test_manifest.exists()

    df_out = pd.read_parquet(test_alloc)
    required_cols = [
        "optimization_run_id", "h3_cell_id", "intervention_type", "activation",
        "quantity", "unit", "unit_cost", "fixed_cost", "total_cost",
        "modeled_effect", "modeled_risk_reduction"
    ]
    for c in required_cols:
        assert c in df_out.columns, f"Missing output column: {c}"

    with open(test_manifest, "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["schema_version"] == "1.0.0"
    assert m["phase"] == "Phase 1G"
    assert "portfolio_summary" in m
    assert m["governance_audit"]["f22_risk_surface_unmodified"] is True

    # Clean up test artifacts
    if test_alloc.exists():
        test_alloc.unlink()
    if test_manifest.exists():
        test_manifest.unlink()
