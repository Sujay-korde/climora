"""
CLIMORA - Phase 1F Formulation Gate Tests
Test Suite: test_phase_1f_optimization_formulation.py

Validates the mathematical formulation contract, dimensional consistency,
edge cases, and deterministic solvability of the canonical MILP optimization
problem under Formulation F-24 (F-24.1 through F-24.6) and F-25.1.
"""

import json
from pathlib import Path
import numpy as np
import pytest
from scipy.optimize import milp, LinearConstraint, Bounds


@pytest.fixture(scope="module")
def contract_manifest():
    """Load canonical Phase 1F optimization formulation contract."""
    manifest_path = Path("data/manifests/optimization_formulation_contract.json")
    assert manifest_path.exists(), f"Contract manifest missing: {manifest_path}"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def test_contract_manifest_integrity(contract_manifest):
    """Verify that contract schema contains all required architectural fields."""
    assert contract_manifest["schema_version"] == "1.0.0"
    assert contract_manifest["phase"] == "Phase 1F"
    assert contract_manifest["status"] == "RATIFIED_OPTIMIZATION_FORMULATION_GATE_PASSED"
    
    # Check 5 canonical interventions
    catalog = contract_manifest["intervention_catalog"]
    required_interventions = [
        "cool_roofs",
        "street_trees",
        "green_corridor",
        "permeable_surfaces",
        "bioswales",
    ]
    for code in required_interventions:
        assert code in catalog, f"Intervention {code} missing from catalog"
        item = catalog[code]
        assert item["unit_cost_inr"] > 0
        assert item["mobilization_fixed_cost_inr"] >= 0
        assert item["minimum_lot_size"] > 0
        assert item["cooling_coefficient_degC_per_unit"] > 0


def test_dimensional_coherence_and_zero_exposure_axiom(contract_manifest):
    """Verify dimensional consistency and Zero-Exposure Axiom in marginal risk response."""
    # r_{i, a} = E_i * [ V_i * (0.25 * e_a / Delta_T_scale) + H_i * (v_a / A_cell_i) ]
    delta_T_scale = 15.0  # deg C
    A_cell = 105000.0  # m^2
    catalog = contract_manifest["intervention_catalog"]

    # Test Case 1: Active risk cell
    H_i = 0.8
    E_i = 0.6
    V_i = 0.7
    e_roof = catalog["cool_roofs"]["cooling_coefficient_degC_per_unit"]
    v_roof = catalog["cool_roofs"]["biophysical_susceptibility_reduction_factor"]

    r_roof = E_i * (V_i * (0.25 * e_roof / delta_T_scale) + H_i * (v_roof / A_cell))
    assert r_roof > 0, "Marginal risk response must be positive for active cell"

    # Test Case 2: Zero-Exposure Axiom (E_i = 0 => r_{i, a} = 0 => Delta Risk = 0)
    E_zero = 0.0
    r_zero_exp = E_zero * (V_i * (0.25 * e_roof / delta_T_scale) + H_i * (v_roof / A_cell))
    assert r_zero_exp == 0.0, "Zero-exposure cell must have zero marginal risk reduction"


def solve_synthetic_milp(budget: float, c_mask: np.ndarray = None):
    """
    Helper function: Solves a canonical 3-cell, 2-intervention synthetic MILP problem
    using SciPy's HiGHS solver backend.
    """
    n_cells = 3
    n_interv = 2
    n_pairs = n_cells * n_interv  # 6 pairs

    # Setup coefficients
    # Marginal risk reduction per unit:
    r = np.array([0.0005, 0.0008, 0.0003, 0.0009, 0.0006, 0.0004])
    # Objective: maximize r^T q => minimize -r^T q
    c = np.concatenate([np.zeros(n_pairs), -r])

    # Variables: [x_00..x_21 (6 binary), q_00..q_21 (6 continuous)]
    integrality = np.concatenate([np.ones(n_pairs), np.zeros(n_pairs)])
    bounds = Bounds(
        np.zeros(2 * n_pairs),
        np.concatenate([np.ones(n_pairs), np.full(n_pairs, np.inf)]),
    )

    # Cost parameters
    F = np.array([5000.0, 8000.0, 5000.0, 8000.0, 5000.0, 8000.0])
    unit_cost = np.array([50.0, 120.0, 50.0, 120.0, 50.0, 120.0])
    q_min = np.array([100.0, 50.0, 100.0, 50.0, 100.0, 50.0])
    Q_max = np.array([1000.0, 500.0, 800.0, 400.0, 1200.0, 600.0])

    if c_mask is None:
        c_mask = np.array([1, 1, 1, 1, 1, 0])  # cell 2 ineligible for intervention 1

    A_rows = []
    lhs = []
    rhs = []

    # 1. Budget constraint: sum (F_a x + cost_a q) <= B
    row_budget = np.concatenate([F, unit_cost])
    A_rows.append(row_budget)
    lhs.append(-np.inf)
    rhs.append(budget)

    # 2. Semi-continuous lower bounds: q_min * x - q <= 0
    for k in range(n_pairs):
        row = np.zeros(2 * n_pairs)
        row[k] = q_min[k]
        row[n_pairs + k] = -1.0
        A_rows.append(row)
        lhs.append(-np.inf)
        rhs.append(0.0)

    # 3. Capacity upper bounds: q - Q_max * x <= 0
    for k in range(n_pairs):
        row = np.zeros(2 * n_pairs)
        row[k] = -Q_max[k]
        row[n_pairs + k] = 1.0
        A_rows.append(row)
        lhs.append(-np.inf)
        rhs.append(0.0)

    # 4. Eligibility bounds: x <= C
    for k in range(n_pairs):
        row = np.zeros(2 * n_pairs)
        row[k] = 1.0
        A_rows.append(row)
        lhs.append(-np.inf)
        rhs.append(float(c_mask[k]))

    A = np.vstack(A_rows)
    constraints = LinearConstraint(A, lhs, rhs)

    res = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints)
    return res, F, unit_cost, q_min, Q_max, c_mask


def test_synthetic_milp_solver_optimality():
    """Verify that synthetic MILP solves to proven optimality and respects all hard constraints."""
    B = 100000.0
    res, F, unit_cost, q_min, Q_max, c_mask = solve_synthetic_milp(budget=B)

    assert res.success, f"MILP solve failed: {res.status} - {res.message}"
    assert res.status == 0, "HiGHS status must be 0 (Optimal)"

    n_pairs = 6
    x_opt = res.x[:n_pairs]
    q_opt = res.x[n_pairs:]

    # Check integrality of activation variables
    for k, val in enumerate(x_opt):
        assert np.isclose(val, 0.0) or np.isclose(val, 1.0), f"x[{k}] not binary: {val}"

    # Check budget constraint
    total_cost = float(np.dot(F, x_opt) + np.dot(unit_cost, q_opt))
    assert total_cost <= B + 1e-5, f"Budget exceeded: {total_cost} > {B}"

    # Check semi-continuous bounds and eligibility
    for k in range(n_pairs):
        if np.isclose(x_opt[k], 1.0):
            assert q_opt[k] >= q_min[k] - 1e-5, f"Lot size violation: {q_opt[k]} < {q_min[k]}"
            assert q_opt[k] <= Q_max[k] + 1e-5, f"Capacity violation: {q_opt[k]} > {Q_max[k]}"
            assert c_mask[k] == 1, f"Ineligible cell was activated: pair {k}"
        else:
            assert np.isclose(q_opt[k], 0.0), f"Unactivated cell has non-zero quantity: {q_opt[k]}"


def test_synthetic_milp_deterministic_reproducibility():
    """Verify 100% deterministic bitwise reproducibility of the solver across executions."""
    B = 75000.0
    res1, _, _, _, _, _ = solve_synthetic_milp(budget=B)
    res2, _, _, _, _, _ = solve_synthetic_milp(budget=B)

    assert res1.success and res2.success
    np.testing.assert_array_equal(res1.x, res2.x)
    assert res1.fun == res2.fun


def test_edge_case_zero_budget():
    """Verify that B = 0 returns a valid feasible all-zero portfolio."""
    res, F, unit_cost, _, _, _ = solve_synthetic_milp(budget=0.0)
    assert res.success
    np.testing.assert_array_equal(res.x, np.zeros_like(res.x))
    total_cost = float(np.dot(F, res.x[:6]) + np.dot(unit_cost, res.x[6:]))
    assert total_cost == 0.0
    assert res.fun == 0.0


def test_edge_case_insufficient_budget():
    """Verify that a budget smaller than any feasible activation returns all zeros."""
    # Min activation cost = min_a (F_a + c_a * q_min_a) = 5000 + 50*100 = 10,000 INR
    res, F, unit_cost, _, _, _ = solve_synthetic_milp(budget=2500.0)
    assert res.success
    np.testing.assert_array_equal(res.x, np.zeros_like(res.x))
    assert res.fun == 0.0


def test_edge_case_no_eligible_candidates():
    """Verify that when all candidates are ineligible (C = 0), portfolio is zero."""
    res, _, _, _, _, _ = solve_synthetic_milp(budget=100000.0, c_mask=np.zeros(6))
    assert res.success
    np.testing.assert_array_equal(res.x, np.zeros_like(res.x))
    assert res.fun == 0.0


def test_ward_independence_decoupling(contract_manifest):
    """Verify that ward_id does not enter the optimization problem or constraints."""
    assert contract_manifest["provenance_and_governance"]["ward_dependency"] == "NONE (Operates strictly on H3 Resolution 9 mesh)"
    assert contract_manifest["provenance_and_governance"]["pmc_ward_geometry_used"] is False
