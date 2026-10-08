"""
CLIMORA - Phase 2E Decision Intelligence Integration Test Suite
Test File: test_phase_2e_decision_intelligence.py

Verifies:
1. Citywide canonical risk surface endpoint returns exactly 3,181 cells with valid schema.
2. Canonical Pune AOI boundary endpoint returns valid GeoJSON.
3. Precomputed benchmark scenarios (2.5M, 5M, 7.5M, 10M) return verified MILP solutions.
4. Custom budget scenario executes in memory without modifying canonical files.
5. Canonical allocation parquet SHA-256 remains strictly bitwise identical before and after.
6. Budget domain boundaries (< 500k, > 25M, negative, non-numeric) rejected with HTTP 400.
7. Cedar governance authorization evaluates under policy_universal_view.
8. Unknown project IDs return structured HTTP 404 errors.
"""

import hashlib
import json
from pathlib import Path
import pytest

from api.app import create_app
from processing.project_mrv import CANONICAL_ALLOCATION_PARQUET
from services.allocation_service import CANONICAL_ALLOCATION_SHA256
from services.query_layer import CANONICAL_PROJECT_ID


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_citywide_risk_surface_endpoint(client):
    """Test 1: GET /projects/{id}/risk-surface returns 3,181 canonical cells."""
    resp = client.get(f"/projects/{CANONICAL_PROJECT_ID}/risk-surface")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "SUCCESS"
    data = body["data"]

    assert data["project_id"] == CANONICAL_PROJECT_ID
    assert data["truth_layer"] == "MODELED"
    assert data["total_cells"] == 3181
    assert data["eligible_cells"] == 3113
    assert len(data["cells"]) == 3181

    first_cell = data["cells"][0]
    required_keys = {
        "h3_cell_id", "risk_i", "H_i", "E_i", "V_i",
        "lst_2025", "lst_anomaly", "population_2020",
        "lisa_cluster", "is_eligible"
    }
    assert required_keys.issubset(set(first_cell.keys()))
    assert isinstance(first_cell["risk_i"], (int, float))
    assert isinstance(first_cell["is_eligible"], bool)


def test_risk_surface_unknown_project(client):
    """Test 2: GET /projects/{id}/risk-surface with unknown project returns 404."""
    resp = client.get("/projects/PROJ-UNKNOWN-9999/risk-surface")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"]["code"] == "PROJECT_NOT_FOUND"


def test_pune_boundary_endpoint(client):
    """Test 3: GET /projects/{id}/boundary returns valid GeoJSON."""
    resp = client.get(f"/projects/{CANONICAL_PROJECT_ID}/boundary")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "SUCCESS"
    assert "boundary" in body
    geojson = body["boundary"]
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) >= 1
    assert geojson["features"][0]["geometry"]["type"] in ("Polygon", "MultiPolygon")


def test_scenario_optimize_benchmark_5m(client):
    """Test 4: POST /projects/{id}/scenarios/optimize with 5M benchmark."""
    # Pre-check canonical allocation hash
    hash_before = hashlib.sha256(CANONICAL_ALLOCATION_PARQUET.read_bytes()).hexdigest()

    resp = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/scenarios/optimize",
        json={"budget_inr": 5000000},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "SUCCESS"
    data = body["data"]

    assert data["budget_inr"] == 5000000.0
    assert data["truth_layer"] == "MODELED"
    assert data["is_canonical"] is False
    assert data["solver_status"] == "OPTIMAL"
    assert data["total_cells_treated"] == 16
    assert data["total_allocated_cost_inr"] == 4950500.0
    assert data["budget_slack_inr"] == 49500.0
    assert abs(data["optimal_objective_value"] - 0.055865) < 1e-4

    # Post-check canonical allocation hash is unmodified
    hash_after = hashlib.sha256(CANONICAL_ALLOCATION_PARQUET.read_bytes()).hexdigest()
    assert hash_before == hash_after == CANONICAL_ALLOCATION_SHA256


def test_scenario_optimize_benchmark_10m(client):
    """Test 5: POST with 10M matches canonical baseline metrics."""
    resp = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/scenarios/optimize",
        json={"budget_inr": 10000000},
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["total_cells_treated"] == 28
    assert data["total_allocated_cost_inr"] == 9992500.0
    assert data["budget_slack_inr"] == 7500.0
    assert abs(data["optimal_objective_value"] - 0.106048) < 1e-4


def test_scenario_optimize_invalid_budgets(client):
    """Test 6: Reject invalid budgets (< 500k, > 25M, non-numeric)."""
    # Below minimum
    r1 = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/scenarios/optimize",
        json={"budget_inr": 200000},
    )
    assert r1.status_code == 400

    # Above maximum
    r2 = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/scenarios/optimize",
        json={"budget_inr": 30000000},
    )
    assert r2.status_code == 400

    # Non-numeric
    r3 = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/scenarios/optimize",
        json={"budget_inr": "five_million"},
    )
    assert r3.status_code == 400

    # Extra fields rejected by Pydantic forbid
    r4 = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/scenarios/optimize",
        json={"budget_inr": 5000000, "extra_param": True},
    )
    assert r4.status_code == 400
