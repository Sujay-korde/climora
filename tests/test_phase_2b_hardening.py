"""CLIMORA Phase 2B Service Hardening & Read-Only Zonal Query Optimization Test Suite.

Comprehensive test suite verifying:
1. Query correctness: project query, H3 cell query, allocation query, baseline query, MRV query
2. Determinism: repeated requests return byte-identical / semantically identical JSON
3. Cache behavior: cold vs warm latency, key isolation, invalidation on revision, telemetry
4. Pagination & Bounds: default page size, explicit page size, max page size (100), invalid page size rejection,
   deterministic ordering, total preservation
5. Validation: malformed project ID, malformed H3 ID, NaN, Infinity, negative values
6. Immutability: PUT/PATCH/DELETE forbidden (405), byte-for-byte SHA256 preservation
7. Truth layers: OBSERVED vs DERIVED vs MODELED vs VERIFIED (null)
8. MRV safety: synthetic rejection, Sentinel-2 thermal rejection, DID non-executable
9. Integrity verification: all 5 canonical SHA-256 digests validated, tampering detected
10. Ward/H3 separation: wards are administrative only, analytical topology is H3 Res 9
11. Correlation & Telemetry: X-Correlation-ID, X-Request-ID, X-Response-Time-Ms
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import numpy as np
import pytest

from api.app import create_app
from ingestion.common import calculate_sha256
from processing.project_mrv import (
    CANONICAL_ALLOCATION_PARQUET,
    CANONICAL_FEATURE_MATRIX,
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
from services.query_layer import (
    ArtifactIntegrityError,
    CANONICAL_ARTIFACTS,
    ZonalQueryEngine,
)


@pytest.fixture
def app():
    """Create Flask application instance for testing."""
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


# ==============================================================================
# 1. Query Correctness & Zonal Queries
# ==============================================================================

def test_project_query_correctness(client):
    """Verifies project detail returns exact canonical 13-section representation."""
    res = client.get(f"/projects/{CANONICAL_PROJECT_ID}")
    assert res.status_code == 200
    p = res.json["project"]

    assert p["identity"]["project_id"] == CANONICAL_PROJECT_ID
    assert p["identity"]["price_basis_year"] == 2025
    assert p["status"] == "PROPOSED"
    assert p["geographic_scope"]["h3_resolution"] == 9
    assert len(p["geographic_scope"]["treated_h3_cells"]) == 28
    assert p["budget"]["modeled_optimized_capex_inr"] == 9992500.0
    assert p["budget"]["scenario_budget_envelope_inr"] == 10000000.0
    assert p["budget"]["budget_slack_unallocated_inr"] == 7500.0
    assert np.isclose(p["modeled_impact"]["modeled_aggregate_risk_reduction_score"], 0.10604830270054796)
    assert p["modeled_impact"]["truth_layer"] == "MODELED"


def test_h3_cell_filtered_query(client):
    """Verifies single-cell filtering by h3_cell_id for both allocation and baseline."""
    target_cell = "89608850003ffff"

    # Allocation single-cell query
    res_alloc = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation?h3_cell_id={target_cell}")
    assert res_alloc.status_code == 200
    data_alloc = res_alloc.json["data"]
    assert data_alloc["total_selected_cells"] == 28  # Portfolio total preserved
    assert len(data_alloc["allocations"]) == 1
    assert data_alloc["allocations"][0]["h3_cell_id"] == target_cell
    assert data_alloc["allocations"][0]["planned_quantity"] == 76.0

    # Baseline single-cell query
    res_base = client.get(f"/projects/{CANONICAL_PROJECT_ID}/baseline?h3_cell_id={target_cell}")
    assert res_base.status_code == 200
    data_base = res_base.json["data"]
    assert data_base["total_selected_cells"] == 28
    assert len(data_base["cells"]) == 1
    assert data_base["cells"][0]["h3_cell_id"] == target_cell
    assert data_base["cells"][0]["metrics"]["lst_2025"]["truth_layer"] == "OBSERVED"
    assert data_base["cells"][0]["metrics"]["lst_2025"]["unit"] == "degC"


# ==============================================================================
# 2. Determinism Contract
# ==============================================================================

def test_query_determinism(client):
    """Verifies repeated identical requests return semantically identical results."""
    res1 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation")
    res2 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation")
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json == res2.json

    res_b1 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/baseline")
    res_b2 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/baseline")
    assert res_b1.status_code == 200
    assert res_b2.status_code == 200
    assert res_b1.json == res_b2.json


# ==============================================================================
# 3. Safe Caching, Isolation & Invalidation
# ==============================================================================

def test_cache_hits_and_telemetry(client, app):
    """Verifies that cache tracks hits, misses, and exposes telemetry via /cache/stats."""
    engine = app.config["QUERY_ENGINE"]
    engine.cache.clear()

    # Cold request -> Miss
    r1 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation")
    assert r1.status_code == 200

    # Warm request -> Hit
    r2 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation")
    assert r2.status_code == 200

    stats_resp = client.get("/cache/stats")
    assert stats_resp.status_code == 200
    c_stats = stats_resp.json["cache"]
    assert c_stats["hits"] >= 1
    assert c_stats["misses"] >= 1
    assert c_stats["hit_ratio"] > 0.0


def test_cache_key_isolation(client, app):
    """Verifies cache key isolates requests with different query parameters."""
    engine = app.config["QUERY_ENGINE"]
    engine.cache.clear()

    # Query with page=1, page_size=10
    r1 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation?page=1&page_size=10")
    assert len(r1.json["data"]["allocations"]) == 10

    # Query with page=2, page_size=10 -> Must be a different cache entry
    r2 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation?page=2&page_size=10")
    assert len(r2.json["data"]["allocations"]) == 10
    assert r1.json["data"]["allocations"] != r2.json["data"]["allocations"]

    # Verify cache has stored both entries separately
    assert engine.cache.stats["cached_entries_count"] == 2


def test_cache_invalidation_on_revision(client, app):
    """Verifies that proposing an allocation revision invalidates cached allocation queries."""
    engine = app.config["QUERY_ENGINE"]
    engine.cache.clear()

    # Populate cache
    r1 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation")
    assert engine.cache.stats["cached_entries_count"] >= 1

    # Propose revision
    rev_res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/revisions",
        json={
            "h3_cell_id": "89608850003ffff",
            "intervention_code": "street_tree_shade",
            "proposed_quantity": 80.0,
            "reason": "Zonal field verification verge expansion.",
            "author": "Municipal Urban Forester",
        },
    )
    assert rev_res.status_code == 201

    # Allocation query cache must have been invalidated
    prefix_keys = [k for k in engine.cache._cache.keys() if "alloc_query" in k]
    assert len(prefix_keys) == 0


# ==============================================================================
# 4. Pagination & Response Bounds
# ==============================================================================

def test_pagination_bounds_and_defaults(client):
    """Verifies pagination default (28), custom page size, and total preservation."""
    # 1. Default page size (28 cells)
    r_default = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation")
    assert r_default.status_code == 200
    pag = r_default.json["data"]["pagination"]
    assert pag["page"] == 1
    assert pag["page_size"] == 28
    assert pag["total_items"] == 28
    assert pag["total_pages"] == 1
    assert len(r_default.json["data"]["allocations"]) == 28

    # 2. Bounded pagination: page_size=10
    r_p1 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation?page=1&page_size=10")
    assert len(r_p1.json["data"]["allocations"]) == 10
    assert r_p1.json["data"]["pagination"]["total_pages"] == 3

    r_p2 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation?page=2&page_size=10")
    assert len(r_p2.json["data"]["allocations"]) == 10

    r_p3 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation?page=3&page_size=10")
    assert len(r_p3.json["data"]["allocations"]) == 8

    # 3. Portfolio totals must remain UNCHANGED across paginated pages
    for r in [r_p1, r_p2, r_p3]:
        psum = r.json["data"]["portfolio_summary"]
        assert psum["total_planned_quantity"] == 2695.0
        assert psum["total_modeled_cost_inr"] == 9992500.0
        assert psum["total_population_protected"]["canonical_exact"] == 118941.21


def test_pagination_validation_rejections(client):
    """Verifies malformed pagination parameters are rejected with 400."""
    pid = CANONICAL_PROJECT_ID

    # Page < 1
    r0 = client.get(f"/projects/{pid}/allocation?page=0")
    assert r0.status_code == 400
    assert r0.json["error"]["code"] == "VALIDATION_ERROR"

    # Negative page
    r_neg = client.get(f"/projects/{pid}/allocation?page=-5")
    assert r_neg.status_code == 400

    # Page size > 100
    r_huge = client.get(f"/projects/{pid}/allocation?page_size=500")
    assert r_huge.status_code == 400
    assert r_huge.json["error"]["code"] == "VALIDATION_ERROR"

    # Non-integer page
    r_nan = client.get(f"/projects/{pid}/allocation?page=abc")
    assert r_nan.status_code == 400


# ==============================================================================
# 5. API Input Validation & NaN/Infinity Rejection
# ==============================================================================

def test_malformed_identifiers_rejection(client):
    """Verifies malformed project IDs and H3 cell IDs are rejected deterministically."""
    # Malformed project ID
    r_pid = client.get("/projects/invalid@project!id")
    assert r_pid.status_code == 400
    assert r_pid.json["error"]["code"] == "VALIDATION_ERROR"

    # Malformed H3 cell ID in query filter
    r_h3 = client.get(f"/projects/{CANONICAL_PROJECT_ID}/allocation?h3_cell_id=not-hex-index")
    assert r_h3.status_code == 400
    assert r_h3.json["error"]["code"] == "VALIDATION_ERROR"


def test_nan_infinity_negative_rejection_in_payloads(client):
    """Verifies NaN, Infinity, and negative physical values are rejected in JSON payloads."""
    pid = CANONICAL_PROJECT_ID

    # Negative quantity
    r_neg = client.post(
        f"/projects/{pid}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": -5.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/doc.pdf",
        },
    )
    assert r_neg.status_code == 400
    assert r_neg.json["error"]["code"] == "VALIDATION_ERROR"

    # String NaN in numeric field
    r_nan = client.post(
        f"/projects/{pid}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": "NaN",
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/doc.pdf",
        },
    )
    assert r_nan.status_code == 400

    # Negative revision quantity
    r_rev_neg = client.post(
        f"/projects/{pid}/revisions",
        json={
            "h3_cell_id": "89608850003ffff",
            "intervention_code": "street_tree_shade",
            "proposed_quantity": -10.0,
            "reason": "Negative quantity test",
            "author": "Forester",
        },
    )
    assert r_rev_neg.status_code == 400


# ==============================================================================
# 6. Allocation Immutability Contract
# ==============================================================================

def test_allocation_immutability(client):
    """Verifies PUT/PATCH/DELETE are rejected (405) and canonical parquet SHA is preserved."""
    pid = CANONICAL_PROJECT_ID
    sha_orig = calculate_sha256(CANONICAL_ALLOCATION_PARQUET)

    assert client.put(f"/projects/{pid}/allocation", json={"val": 1}).status_code == 405
    assert client.patch(f"/projects/{pid}/allocation", json={"val": 1}).status_code == 405
    assert client.delete(f"/projects/{pid}/allocation").status_code == 405

    # Parquet hash must be 100% byte-for-byte identical
    sha_after = calculate_sha256(CANONICAL_ALLOCATION_PARQUET)
    assert sha_after == sha_orig
    assert sha_after == CANONICAL_ALLOCATION_SHA256


# ==============================================================================
# 7. Truth-Layer Invariants
# ==============================================================================

def test_truth_layer_invariants_across_endpoints(client):
    """Verifies explicit truth classification: OBSERVED, DERIVED, MODELED, VERIFIED."""
    # Summary
    r_sum = client.get("/projects")
    proj = r_sum.json["projects"][0]
    assert proj["population"]["truth_layer"] == "OBSERVED"
    assert proj["modeled_objective"]["truth_layer"] == "MODELED"
    assert "UNOBSERVED" in proj["truth_layer_metadata"]["verified_impact"]

    # Baseline
    r_base = client.get(f"/projects/{CANONICAL_PROJECT_ID}/baseline?limit=1")
    cell = r_base.json["data"]["cells"][0]
    assert cell["metrics"]["lst_2025"]["truth_layer"] == "OBSERVED"
    assert cell["metrics"]["lst_baseline_mean"]["truth_layer"] == "DERIVED"
    assert cell["metrics"]["H_i"]["truth_layer"] == "MODELED"
    assert cell["metrics"]["risk_i"]["truth_layer"] == "MODELED"

    # MRV
    r_mrv = client.get(f"/projects/{CANONICAL_PROJECT_ID}/mrv")
    assert r_mrv.json["data"]["verified_impact"] is None
    assert r_mrv.json["data"]["difference_in_differences_status"]["current_operational_status"] == "PLANNED / NOT_YET_EXECUTABLE"


# ==============================================================================
# 8. MRV Safety & Anti-Contamination
# ==============================================================================

def test_mrv_safety_rules(client):
    """Verifies synthetic data rejection and Sentinel-2 thermal rejection."""
    pid = CANONICAL_PROJECT_ID

    # 1. Synthetic MRV rejection
    r_synth = client.post(
        f"/projects/{pid}/verification-events",
        json={
            "observation": {
                "sensor_platform": "Synthetic-Sensor",
                "acquisition_date": "2026-04-15",
                "doy": 105,
                "spatial_resolution_m": 30.0,
                "cloud_cover_aoi_pct": 0.0,
                "quality_flags_passed": True,
                "asset_uri": "s3://mock.tif",
                "is_synthetic_demo": True,
            },
            "verification": {
                "verification_status": "PASSED",
                "verification_date": "2026-05-01",
                "verifier_identity": "Synthetic Auditor",
                "methodology_standard": "MOCK-STD",
                "evidence_artifact_uri": "s3://verif.pdf",
                "is_synthetic_demo": True,
            },
            "is_synthetic_demo": True,
        },
    )
    assert r_synth.status_code == 422
    assert r_synth.json["error"]["code"] == "VERIFICATION_NOT_ELIGIBLE"
    assert SYNTHETIC_MRV_TAG in r_synth.json["error"]["message"]

    # 2. Seed physical implementation event first so verification eligibility passes to sensor inspection
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

    # 3. Sentinel-2 Thermal Rejection
    r_s2_thermal = client.post(
        f"/projects/{pid}/verification-events",
        json={
            "observation": {
                "sensor_platform": "Sentinel-2B-MSI",
                "acquisition_date": "2026-04-15",
                "doy": 105,
                "spatial_resolution_m": 10.0,
                "cloud_cover_aoi_pct": 0.0,
                "quality_flags_passed": True,
                "asset_uri": "s3://obs.tif",
            },
            "verification": {
                "verification_status": "PASSED",
                "verification_date": "2026-05-01",
                "verifier_identity": "Auditor",
                "methodology_standard": "ISO 14064-2",
                "evidence_artifact_uri": "s3://doc.pdf",
            },
            "target_metric": "lst",
        },
    )
    assert r_s2_thermal.status_code == 422
    assert "no thermal infrared payload" in str(r_s2_thermal.json["error"]["details"])


# ==============================================================================
# 9. Canonical Parquet Integrity & Tampering Detection
# ==============================================================================

def test_all_canonical_parquet_shas_match():
    """Audits SHA-256 digests of all 5 canonical Parquet artifacts against frozen values."""
    for name, (path, expected_sha) in CANONICAL_ARTIFACTS.items():
        assert path.exists(), f"Canonical file missing: {path}"
        actual_sha = calculate_sha256(path)
        assert actual_sha == expected_sha, (
            f"MUTATION DETECTED in canonical artifact {name} ({path.name})! "
            f"Expected {expected_sha}, got {actual_sha}"
        )


def test_query_engine_detects_sha_mismatch(monkeypatch):
    """Verifies ZonalQueryEngine raises an error if an artifact's SHA256 does not match."""
    # Monkeypatch expected hash to simulate corruption detection
    tampered_artifacts = dict(CANONICAL_ARTIFACTS)
    path, _ = tampered_artifacts["optimization_allocation"]
    tampered_artifacts["optimization_allocation"] = (
        path,
        "0000000000000000000000000000000000000000000000000000000000000000",
    )

    with monkeypatch.context() as m:
        m.setattr("services.query_layer.CANONICAL_ARTIFACTS", tampered_artifacts)
        with pytest.raises(ArtifactIntegrityError) as exc_info:
            ZonalQueryEngine()
        assert "CANONICAL_ARTIFACT_INTEGRITY_MISMATCH" == exc_info.value.code


# ==============================================================================
# 10. Ward / H3 Analytical Separation
# ==============================================================================

def test_ward_h3_analytical_separation(client):
    """Verifies administrative ward boundaries do not alter analytical H3 results."""
    res = client.get(f"/projects/{CANONICAL_PROJECT_ID}")
    p = res.json["project"]

    # Ward is contextual only
    assert "NONE" in p["geographic_scope"]["administrative_ward_dependency"]
    assert p["geographic_scope"]["h3_resolution"] == 9
    assert len(p["geographic_scope"]["treated_h3_cells"]) == 28


# ==============================================================================
# 11. Request Correlation & Observability Headers
# ==============================================================================

def test_request_correlation_headers(client):
    """Verifies correlation headers and execution timing are injected into responses."""
    # 1. Client-supplied correlation ID
    custom_corr = "corr-test-audit-12345"
    res1 = client.get("/projects", headers={"X-Correlation-ID": custom_corr})
    assert res1.status_code == 200
    assert res1.headers.get("X-Correlation-ID") == custom_corr
    assert res1.headers.get("X-Request-ID") == custom_corr
    assert "X-Response-Time-Ms" in res1.headers
    assert float(res1.headers["X-Response-Time-Ms"]) >= 0.0

    # 2. Auto-generated correlation ID when absent
    res2 = client.get("/projects")
    assert res2.status_code == 200
    auto_corr = res2.headers.get("X-Correlation-ID")
    assert auto_corr is not None
    assert auto_corr.startswith("corr-")
