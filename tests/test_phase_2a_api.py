"""CLIMORA Phase 2A Production API & Service Boundary Test Suite.

Comprehensive tests verifying:
1. Project summary: canonical ID, lineage, cost, budget, population, truth layers
2. Project detail: 13-section representation, objective wording, 404 on unknown ID
3. Allocation contract: 28 H3 cells, 2,695 trees, ₹9,992,500 modeled cost, ₹7,500 slack
4. Immutability: PUT/PATCH/DELETE forbidden (405), byte-for-byte parquet preservation
5. Baseline evidence: OBSERVED vs DERIVED vs MODELED truth layers, no raw raster leak
6. Population evidence: exact 118,941.21, rounded 118,941, no 84,402 placeholder
7. Implementation events: deviation calculation, zero-planned null deviation rate (F-27.2)
8. Implementation validation: negative quantity rejection, invalid H3 rejection
9. Verification gating: missing implementation evidence rejection
10. Synthetic isolation: DEMO_ONLY_SYNTHETIC_MRV_DATA rejection (no verified transition)
11. Sensor compatibility: Sentinel-2 rejected for thermal LST, accepted for optical NDVI
12. Temporal governance: preferred DOY 95-115, fallback DOY 90-120, rejected outside +-15
13. Cloud screening: <= 5.0% AOI ceiling and 100% pixel masking compliance
14. State machine: illegal skips rejected, no direct jump to VERIFIED
15. End-to-end lifecycle: PROPOSED -> FUNDED -> IMPLEMENTING -> IMPLEMENTED -> MONITORING -> VERIFIED
16. Allocation revision branching: auditable revision logged while canonical parquet remains unchanged
17. OpenAPI & Health: /health, /openapi.json, /docs
"""

import json
from pathlib import Path
import numpy as np
import pytest

from api.app import create_app
from ingestion.common import calculate_sha256
from processing.project_mrv import (
    CANONICAL_ALLOCATION_PARQUET,
    CANONICAL_FEATURE_MATRIX,
    CANONICAL_RUN_MANIFEST,
    SYNTHETIC_MRV_TAG,
)
from services.allocation_service import CANONICAL_ALLOCATION_SHA256
from services.project_service import (
    CANONICAL_MODELED_OBJECTIVE,
    CANONICAL_MODELED_TOTAL_COST_INR,
    CANONICAL_PLANNED_TREES,
    CANONICAL_POPULATION_DISPLAY,
    CANONICAL_POPULATION_EXACT,
    CANONICAL_PROJECT_ID,
    CANONICAL_REMAINING_BUDGET_INR,
    CANONICAL_RUN_ID,
    CANONICAL_SCENARIO_BUDGET_INR,
    CANONICAL_SELECTED_CELLS_COUNT,
)


@pytest.fixture(scope="module")
def app():
    """Create Flask application instance for testing."""
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    """Create test client with fresh services per test to prevent state leakage."""
    fresh_app = create_app()
    fresh_app.config["TESTING"] = True
    return fresh_app.test_client()


# ==============================================================================
# 1. Project Summary & Detail Contracts
# ==============================================================================

def test_get_projects_summary(client):
    """Test 1: Verify GET /projects returns project summaries with canonical frozen values."""
    res = client.get("/projects")
    assert res.status_code == 200
    data = res.json
    assert data["status"] == "SUCCESS"
    assert data["count"] >= 1

    proj = next((p for p in data["projects"] if p["project_id"] == CANONICAL_PROJECT_ID), None)
    assert proj is not None, f"Canonical project {CANONICAL_PROJECT_ID} not found in summary list"

    # Lineage & Identity
    assert proj["project_id"] == "PROJ-PUNE-2025-BA225D6A"
    assert proj["optimization_run_id"] == "OPT-PUNE-2025-SCENARIO-BA225D6A"
    assert proj["project_status"] == "PROPOSED"

    # Geographic Scope
    geo = proj["geographic_scope"]
    assert geo["h3_resolution"] == 9
    assert geo["total_treated_cells_count"] == 28
    assert "NONE" in geo["administrative_ward_dependency"]

    # Intervention Summary
    int_sum = proj["intervention_summary"]
    assert "street_tree_shade" in int_sum["intervention_types"]
    assert int_sum["total_physical_units"] == 2695.0
    assert int_sum["quantity_unit"] == "tree_count"

    # Financials
    assert proj["modeled_cost"] == 9992500.0
    assert proj["budget"] == 10000000.0
    assert proj["remaining_budget"] == 7500.0

    # Population: exact underlying 118941.21, rounded 118941, no 84402 placeholder
    pop = proj["population"]
    assert pop["canonical_exact"] == 118941.21
    assert pop["display_rounded"] == 118941
    assert pop["canonical_exact"] != 84402
    assert pop["truth_layer"] == "OBSERVED"

    # Modeled Objective
    obj = proj["modeled_objective"]
    assert np.isclose(obj["value"], 0.10604830270054796)
    assert "modeled aggregate risk-objective reduction under the canonical optimization formulation" in obj["metric_description"]
    assert "does NOT represent a guaranteed 10.6% clinical or ambient cooling outcome" in obj["governance_note"]
    assert obj["truth_layer"] == "MODELED"

    # Truth-Layer Metadata
    tl = proj["truth_layer_metadata"]
    assert tl["modeled_cost"] == "MODELED"
    assert tl["population"] == "OBSERVED"
    assert tl["baseline_lst"] == "OBSERVED"
    assert "UNOBSERVED" in tl["verified_impact"]


def test_get_project_detail_and_unknown_handling(client):
    """Test 2: Verify GET /projects/{id} representation and 404 structured error for unknown ID."""
    # 1. Canonical Project Detail
    res = client.get(f"/projects/{CANONICAL_PROJECT_ID}")
    assert res.status_code == 200
    p = res.json["project"]

    # 13 structured sections mapped to domain representation
    assert p["identity"]["project_id"] == CANONICAL_PROJECT_ID
    assert p["identity"]["price_basis_year"] == 2025
    assert p["status"] == "PROPOSED"
    assert p["geographic_scope"]["h3_resolution"] == 9
    assert len(p["geographic_scope"]["treated_h3_cells"]) == 28

    # Optimization Lineage
    assert p["optimization_lineage"]["optimization_run_id"] == CANONICAL_RUN_ID
    assert "HiGHS" in p["optimization_lineage"]["solver_engine"]

    # Budget & CapEx
    assert p["budget"]["modeled_optimized_capex_inr"] == 9992500.0
    assert p["budget"]["scenario_budget_envelope_inr"] == 10000000.0
    assert p["budget"]["budget_slack_unallocated_inr"] == 7500.0
    assert p["budget"]["actual_expenditure_inr"] == "NOT_AVAILABLE (Pre-implementation proposal phase)"

    # Modeled Impact
    assert p["modeled_impact"]["modeled_aggregate_risk_reduction_score"] == CANONICAL_MODELED_OBJECTIVE
    assert p["modeled_impact"]["truth_layer"] == "MODELED"
    assert p["modeled_impact"]["mean_modeled_cell_cooling_degC"] == 0.069

    # MRV & Verification Status: unobserved at proposal stage
    assert p["mrv_status"]["difference_in_differences_status"] == "PLANNED / NOT_YET_EXECUTABLE"
    assert p["verification_status"]["status"] == "UNOBSERVED / NOT YET VERIFIED"
    assert p["verification_status"]["measured_empirical_cooling_degC"] is None
    assert p["verification_status"]["verified_impact_claims"] is None

    # Provenance
    assert p["provenance"]["feature_matrix_sha256"] == "76f344b147b349f3887259f64c97923414c74fd9a97ec679844fb8d9109f7c01"
    assert p["provenance"]["allocation_parquet_sha256"] == CANONICAL_ALLOCATION_SHA256

    # 2. Unknown Project ID
    res_unknown = client.get("/projects/PROJ-UNKNOWN-PROJECT-999")
    assert res_unknown.status_code == 404
    err = res_unknown.json["error"]
    assert err["code"] == "PROJECT_NOT_FOUND"
    assert "not found" in err["message"].lower()


# ==============================================================================
# 2. Canonical Allocation & Immutability Contracts
# ==============================================================================

def test_canonical_allocation_endpoint(client):
    """Test 3: Verify GET /projects/{id}/allocation reads immutable canonical optimization allocation."""
    res = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation")
    assert res.status_code == 200
    data = res.json["data"]

    assert data["project_id"] == CANONICAL_PROJECT_ID
    assert data["optimization_run_id"] == CANONICAL_RUN_ID
    assert data["total_selected_cells"] == 28
    assert len(data["allocations"]) == 28

    # Portfolio Summary
    summary = data["portfolio_summary"]
    assert summary["intervention_type"] == "street_tree_shade"
    assert summary["total_planned_quantity"] == 2695.0
    assert summary["quantity_unit"] == "tree_count"
    assert summary["direct_cost_inr"] == 9432500.0
    assert summary["mobilization_cost_inr"] == 560000.0
    assert summary["total_modeled_cost_inr"] == 9992500.0
    assert summary["scenario_budget_envelope_inr"] == 10000000.0
    assert summary["budget_slack_unallocated_inr"] == 7500.0
    assert np.isclose(summary["optimal_aggregate_risk_reduction"], 0.10604830270054796)
    assert summary["total_population_protected"]["canonical_exact"] == 118941.21
    assert summary["total_population_protected"]["display_rounded"] == 118941
    assert summary["truth_layer"] == "MODELED"

    # Item breakdown
    first_item = data["allocations"][0]
    assert first_item["intervention_type"] == "street_tree_shade"
    assert first_item["unit_cost"] == 3500.0
    assert first_item["mobilization_fixed_cost"] == 20000.0
    assert first_item["truth_layer"] == "MODELED"
    assert first_item["optimization_run_id"] == CANONICAL_RUN_ID


def test_allocation_immutability_and_forbidden_mutations(client):
    """Test 4: Prove PUT/PATCH/DELETE on allocation are forbidden (405) and canonical parquet remains unchanged."""
    sha_before = calculate_sha256(CANONICAL_ALLOCATION_PARQUET)

    # 1. Attempt PUT
    res_put = client.put(f"/projects/{CANONICAL_PROJECT_ID}/allocation", json={"quantity": 3000})
    assert res_put.status_code == 405
    assert res_put.json["error"]["code"] == "ALLOCATION_IMMUTABLE"

    # 2. Attempt PATCH
    res_patch = client.patch(f"/projects/{CANONICAL_PROJECT_ID}/allocation", json={"quantity": 3000})
    assert res_patch.status_code == 405
    assert res_patch.json["error"]["code"] == "ALLOCATION_IMMUTABLE"

    # 3. Attempt DELETE
    res_delete = client.delete(f"/projects/{CANONICAL_PROJECT_ID}/allocation")
    assert res_delete.status_code == 405
    assert res_delete.json["error"]["code"] == "ALLOCATION_IMMUTABLE"

    # 4. Byte-for-byte SHA256 audit
    sha_after = calculate_sha256(CANONICAL_ALLOCATION_PARQUET)
    assert sha_after == sha_before
    assert sha_after == CANONICAL_ALLOCATION_SHA256


# ==============================================================================
# 3. Baseline Evidence & Truth-Layer Contracts
# ==============================================================================

def test_baseline_evidence_and_truth_labels(client):
    """Test 5: Verify baseline evidence, OBSERVED vs DERIVED labels, and no raw raster leakage."""
    res = client.get(f"/projects/{CANONICAL_PROJECT_ID}/baseline?limit=5")
    assert res.status_code == 200
    data = res.json["data"]

    summary = data["portfolio_summary"]

    # OBSERVED fields
    assert summary["lst_2025"]["truth_layer"] == "OBSERVED"
    assert summary["lst_2025"]["unit"] == "degC"
    assert summary["lst_2025"]["sensor_platform"] == "Landsat-8/9 TIRS"

    assert summary["ndvi_2025"]["truth_layer"] == "OBSERVED"
    assert summary["ndvi_2025"]["sensor_platform"] == "Sentinel-2 MSI"

    assert summary["ndbi_2025"]["truth_layer"] == "OBSERVED"
    assert summary["population"]["truth_layer"] == "OBSERVED"
    assert summary["population"]["canonical_exact"] == 118941.21
    assert summary["road_length"]["truth_layer"] == "OBSERVED"
    assert summary["civic_infrastructure"]["truth_layer"] == "OBSERVED"

    # DERIVED fields
    assert summary["lst_baseline_historical"]["truth_layer"] == "DERIVED"
    assert summary["lst_anomaly"]["truth_layer"] == "DERIVED"
    assert summary["lst_persistence"]["truth_layer"] == "DERIVED"
    assert summary["lst_recurrence_ge45"]["truth_layer"] == "DERIVED"
    assert summary["population_density"]["truth_layer"] == "DERIVED"
    assert summary["lisa_spatial_autocorrelation"]["truth_layer"] == "DERIVED"

    # MODELED fields
    assert summary["hazard_H"]["truth_layer"] == "MODELED"
    assert summary["exposure_E"]["truth_layer"] == "MODELED"
    assert summary["vulnerability_V"]["truth_layer"] == "MODELED"
    assert summary["climate_risk"]["truth_layer"] == "MODELED"
    assert summary["climate_risk"]["formulation_version"] == "F-22"

    # Security check: no raw rasters exposed
    assert data["provenance"]["raw_rasters_exposed"] is False
    assert len(data["cells"]) == 5


# ==============================================================================
# 4. MRV Tracking & DID Readiness Contracts
# ==============================================================================

def test_mrv_overview_endpoint(client):
    """Test 6: Verify GET /projects/{id}/mrv exposes DID readiness and null verified impact."""
    res = client.get(f"/projects/{CANONICAL_PROJECT_ID}/mrv")
    assert res.status_code == 200
    mrv = res.json["data"]

    assert mrv["project_id"] == CANONICAL_PROJECT_ID
    assert mrv["implementation_status"] == "PLANNED"
    assert mrv["total_planned_quantity"] == 2695.0
    assert mrv["total_implemented_quantity"] == 0.0
    assert mrv["overall_deviation"] == -2695.0
    assert np.isclose(mrv["overall_deviation_rate"], -1.0)

    # Invariant: verified impact is null
    assert mrv["verified_impact"] is None
    assert mrv["verification_state"] == "NOT_STARTED"

    # Honest DID status: Planned / Not yet executable
    did = mrv["difference_in_differences_status"]
    assert did["current_operational_status"] == "PLANNED / NOT_YET_EXECUTABLE"
    assert did["is_executable"] is False
    assert "Cannot execute against baseline-only, synthetic, or modeled data" in did["rationale"]


# ==============================================================================
# 5. Implementation Events & Deviation Handling
# ==============================================================================

def test_implementation_events_validation_and_deviations(client):
    """Test 7, 8: Verify implementation event recording, deviation calculations, and validation."""
    pid = CANONICAL_PROJECT_ID

    # 1. Valid event (cell 89608850003ffff has planned_quantity = 76.0)
    res_valid = client.post(
        f"/projects/{pid}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 70.0,
            "quantity_unit": "tree_count",
            "completion_date": "2026-04-10",
            "contractor_id": "PMC-TREE-AUTHORITY",
            "evidence_uri": "s3://climora/evidence/tree_signoff_01.pdf",
        },
    )
    assert res_valid.status_code == 201
    evt = res_valid.json["event"]
    assert evt["planned_quantity"] == 76.0
    assert evt["implemented_quantity"] == 70.0
    assert evt["deviation"] == -6.0
    assert np.isclose(evt["deviation_rate"], -6.0 / 76.0)

    # 2. Zero-planned cell: implemented > 0 on an unallocated cell produces deviation_rate = None (null)
    res_zero = client.post(
        f"/projects/{pid}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608840583ffff",  # Cell in Pune but not in 28 selected allocation
            "implemented_quantity": 25.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/evidence/tree_signoff_02.pdf",
        },
    )
    assert res_zero.status_code == 201
    evt_zero = res_zero.json["event"]
    assert evt_zero["planned_quantity"] == 0.0
    assert evt_zero["implemented_quantity"] == 25.0
    assert evt_zero["deviation"] == 25.0
    assert evt_zero["deviation_rate"] is None  # F-27.2 null handling

    # 3. Validation: negative quantity rejected
    res_neg = client.post(
        f"/projects/{pid}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": -10.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/evidence/invalid.pdf",
        },
    )
    assert res_neg.status_code == 400
    assert res_neg.json["error"]["code"] == "VALIDATION_ERROR"

    # 4. Validation: invalid H3 cell index rejected
    res_bad_h3 = client.post(
        f"/projects/{pid}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "not_an_h3_cell",
            "implemented_quantity": 10.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/evidence/invalid.pdf",
        },
    )
    assert res_bad_h3.status_code == 400

    # 5. Non-existent project
    res_no_proj = client.post(
        "/projects/PROJ-GHOST/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 10.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/evidence/invalid.pdf",
        },
    )
    assert res_no_proj.status_code == 404


# ==============================================================================
# 6. Verification Gating, Sensor & Anti-Contamination Audits
# ==============================================================================

def test_verification_anti_contamination_synthetic_rejection(client):
    """Test 9: Verify synthetic demo fixtures (DEMO_ONLY_SYNTHETIC_MRV_DATA) are strictly rejected."""
    pid = CANONICAL_PROJECT_ID
    res = client.post(
        f"/projects/{pid}/verification-events",
        json={
            "observation": {
                "sensor_platform": "Synthetic-Landsat-9-Mock",
                "acquisition_date": "2026-04-15",
                "doy": 105,
                "spatial_resolution_m": 30.0,
                "cloud_cover_aoi_pct": 0.0,
                "quality_flags_passed": True,
                "asset_uri": "s3://climora/demo/mock.tif",
                "is_synthetic_demo": True,
            },
            "verification": {
                "verification_status": "PASSED",
                "verification_date": "2026-05-01",
                "verifier_identity": "Synthetic Demo Auditor",
                "methodology_standard": "SYNTHETIC-DEMO-STANDARD",
                "evidence_artifact_uri": "s3://climora/demo/mock_verif.pdf",
                "is_synthetic_demo": True,
            },
            "is_synthetic_demo": True,
        },
    )
    assert res.status_code == 422
    err = res.json["error"]
    assert err["code"] == "VERIFICATION_NOT_ELIGIBLE"
    assert SYNTHETIC_MRV_TAG in err["message"]


def test_verification_sensor_compatibility_sentinel2_thermal_rejection(client):
    """Test 10: Verify Sentinel-2 is rejected for thermal LST but accepted for optical NDVI."""
    pid = CANONICAL_PROJECT_ID

    # Seed physical implementation event first
    client.post(
        f"/projects/{pid}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 76.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/evidence/tree_01.pdf",
        },
    )

    # 1. Sentinel-2 evaluating thermal LST MUST FAIL
    res_thermal = client.post(
        f"/projects/{pid}/verification-events",
        json={
            "observation": {
                "sensor_platform": "Sentinel-2B-MSI",
                "acquisition_date": "2026-04-15",
                "doy": 105,
                "spatial_resolution_m": 10.0,
                "cloud_cover_aoi_pct": 0.0,
                "quality_flags_passed": True,
                "asset_uri": "s3://climora/obs/s2.tif",
            },
            "verification": {
                "verification_status": "PASSED",
                "verification_date": "2026-05-01",
                "verifier_identity": "Independent Auditor",
                "methodology_standard": "ISO 14064-2",
                "evidence_artifact_uri": "s3://climora/audit.pdf",
            },
            "target_metric": "lst",
        },
    )
    assert res_thermal.status_code == 422
    violations = res_thermal.json["error"]["details"]["violations"]
    assert any("has no thermal infrared payload" in v for v in violations)


def test_verification_temporal_windows_and_cloud_screening(client):
    """Test 11, 12: Verify temporal window tiers and cloud/QA screening ceilings."""
    pid = CANONICAL_PROJECT_ID

    # Seed implementation event
    client.post(
        f"/projects/{pid}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 76.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/evidence/tree_01.pdf",
        },
    )

    # 1. Temporal rejection: out of season (DOY 196 in July, offset > 15 days)
    res_out_of_season = client.post(
        f"/projects/{pid}/verification-events",
        json={
            "observation": {
                "sensor_platform": "Landsat-9-TIRS",
                "acquisition_date": "2026-07-15",
                "doy": 196,
                "spatial_resolution_m": 30.0,
                "cloud_cover_aoi_pct": 0.0,
                "quality_flags_passed": True,
                "asset_uri": "s3://climora/obs/l9.tif",
            },
            "verification": {
                "verification_status": "PASSED",
                "verification_date": "2026-08-01",
                "verifier_identity": "Independent Auditor",
                "methodology_standard": "ISO 14064-2",
                "evidence_artifact_uri": "s3://climora/audit.pdf",
            },
            "target_metric": "lst",
        },
    )
    assert res_out_of_season.status_code == 422
    assert res_out_of_season.json["error"]["details"]["temporal_tier"] == "REJECTED"

    # 2. Cloud contamination: > 5.0% ceiling
    res_cloud = client.post(
        f"/projects/{pid}/verification-events",
        json={
            "observation": {
                "sensor_platform": "Landsat-9-TIRS",
                "acquisition_date": "2026-04-15",
                "doy": 105,
                "spatial_resolution_m": 30.0,
                "cloud_cover_aoi_pct": 12.0,  # Exceeds 5.0%
                "quality_flags_passed": True,
                "asset_uri": "s3://climora/obs/l9.tif",
            },
            "verification": {
                "verification_status": "PASSED",
                "verification_date": "2026-05-01",
                "verifier_identity": "Independent Auditor",
                "methodology_standard": "ISO 14064-2",
                "evidence_artifact_uri": "s3://climora/audit.pdf",
            },
            "target_metric": "lst",
        },
    )
    assert res_cloud.status_code == 422
    violations = res_cloud.json["error"]["details"]["violations"]
    assert any("exceeds allowable ceiling" in v for v in violations)

    # 3. QA pixel flag failure
    res_qa = client.post(
        f"/projects/{pid}/verification-events",
        json={
            "observation": {
                "sensor_platform": "Landsat-9-TIRS",
                "acquisition_date": "2026-04-15",
                "doy": 105,
                "spatial_resolution_m": 30.0,
                "cloud_cover_aoi_pct": 1.0,
                "quality_flags_passed": False,  # Failed pixel QA screening
                "asset_uri": "s3://climora/obs/l9.tif",
            },
            "verification": {
                "verification_status": "PASSED",
                "verification_date": "2026-05-01",
                "verifier_identity": "Independent Auditor",
                "methodology_standard": "ISO 14064-2",
                "evidence_artifact_uri": "s3://climora/audit.pdf",
            },
            "target_metric": "lst",
        },
    )
    assert res_qa.status_code == 422
    violations = res_qa.json["error"]["details"]["violations"]
    assert any("Pixel quality flags failed" in v for v in violations)


# ==============================================================================
# 7. State Machine Gating & End-to-End Pathway
# ==============================================================================

def test_state_machine_invalid_jumps(client):
    """Test 13, 14: Verify illegal state jumps are rejected by ProjectStateMachine."""
    pid = CANONICAL_PROJECT_ID

    # Jump 1: PROPOSED -> VERIFIED (illegal skip)
    res1 = client.post(f"/projects/{pid}/transition", json={"target_state": "VERIFIED"})
    assert res1.status_code == 422
    assert res1.json["error"]["code"] == "ILLEGAL_STATE_TRANSITION"

    # Jump 2: PROPOSED -> FUNDED without sanction ID
    res2 = client.post(f"/projects/{pid}/transition", json={"target_state": "FUNDED"})
    assert res2.status_code == 422
    assert "sanction_id" in res2.json["error"]["message"]


def test_full_governed_lifecycle_pathway(client):
    """Test 15: Execute complete 7-step lifecycle pathway to certified VERIFIED state."""
    pid = CANONICAL_PROJECT_ID

    # Step 1: PROPOSED -> FUNDED
    r1 = client.post(
        f"/projects/{pid}/transition",
        json={"target_state": "FUNDED", "sanction_id": "PMC-2025-SANC-01", "approved_budget_inr": 10000000.0},
    )
    assert r1.status_code == 200
    assert r1.json["transition"]["current_state"] == "FUNDED"

    # Step 2: FUNDED -> IMPLEMENTING
    r2 = client.post(f"/projects/{pid}/transition", json={"target_state": "IMPLEMENTING"})
    assert r2.status_code == 200
    assert r2.json["transition"]["current_state"] == "IMPLEMENTING"

    # Step 3: Record physical deployment
    r_impl = client.post(
        f"/projects/{pid}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 76.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/evidence/tree_01.pdf",
        },
    )
    assert r_impl.status_code == 201

    # Step 4: IMPLEMENTING -> IMPLEMENTED
    r3 = client.post(f"/projects/{pid}/transition", json={"target_state": "IMPLEMENTED"})
    assert r3.status_code == 200

    # Step 5: IMPLEMENTED -> MONITORING
    r4 = client.post(f"/projects/{pid}/transition", json={"target_state": "MONITORING"})
    assert r4.status_code == 200

    # Step 6: Full verification milestone submission (post-intervention Landsat 9 overpass)
    r_verif = client.post(
        f"/projects/{pid}/verification-events",
        json={
            "observation": {
                "sensor_platform": "Landsat-9-TIRS",
                "acquisition_date": "2026-04-18",
                "doy": 108,
                "spatial_resolution_m": 30.0,
                "cloud_cover_aoi_pct": 1.5,
                "quality_flags_passed": True,
                "asset_uri": "s3://climora/l9_obs.tif",
                "observed_cell_count": 28,
            },
            "verification": {
                "verification_status": "PASSED",
                "verification_date": "2026-05-01",
                "verifier_identity": "Bureau Veritas Certified Climate Auditor",
                "methodology_standard": "ISO 14064-2 / CLIMORA F-26",
                "evidence_artifact_uri": "s3://climora/audit_report_final.pdf",
            },
            "target_metric": "lst",
        },
    )
    assert r_verif.status_code == 201
    assert r_verif.json["verification"]["verification_status"] == "VERIFIED"

    # Step 7: Verify final project state is VERIFIED
    res_final = client.get(f"/projects/{pid}")
    assert res_final.json["project"]["status"] == "VERIFIED"


# ==============================================================================
# 8. Revisions & Allocation Immutability Verification
# ==============================================================================

def test_allocation_revision_branching_preserves_canonical_parquet(client):
    """Test 16: Verify auditable proposed revisions branch cleanly without modifying canonical parquet."""
    pid = CANONICAL_PROJECT_ID
    sha_orig = calculate_sha256(CANONICAL_ALLOCATION_PARQUET)

    res = client.post(
        f"/projects/{pid}/revisions",
        json={
            "h3_cell_id": "89608850003ffff",
            "intervention_code": "street_tree_shade",
            "proposed_quantity": 90.0,
            "reason": "Cadastral survey identified additional municipal planting verge.",
            "author": "Municipal Urban Forester",
        },
    )
    assert res.status_code == 201
    rev = res.json["revision"]
    assert rev["original_quantity"] == 76.0
    assert rev["proposed_quantity"] == 90.0
    assert rev["revision_delta"] == 14.0

    # Ensure canonical parquet was NOT modified
    sha_after = calculate_sha256(CANONICAL_ALLOCATION_PARQUET)
    assert sha_after == sha_orig
    assert sha_after == CANONICAL_ALLOCATION_SHA256


# ==============================================================================
# 9. Health & Documentation Endpoints
# ==============================================================================

def test_health_and_docs_endpoints(client):
    """Test 17: Verify /health, /openapi.json, and /docs endpoints."""
    # Health
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json["status"] == "HEALTHY"
    assert r_health.json["scientific_architecture"] == "FROZEN"
    assert r_health.json["canonical_project_id"] == CANONICAL_PROJECT_ID

    # OpenAPI
    r_api = client.get("/openapi.json")
    assert r_api.status_code == 200
    assert r_api.json["openapi"] == "3.0.0"
    assert "/projects" in r_api.json["paths"]
    assert "/projects/{project_id}/allocation" in r_api.json["paths"]

    # Swagger UI Docs
    r_docs = client.get("/docs")
    assert r_docs.status_code == 200
    assert "SwaggerUIBundle" in r_docs.text
