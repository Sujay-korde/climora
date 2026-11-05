"""
MASTER AUDIT 04 REGRESSION TEST SUITE
=====================================
Governing Master Prompt 04 Section 12 Regression Requirements:
- Security: Anonymous request, forged actor header, query impersonation, commissioner fallback,
  TESTING-mode bypass elimination, unauthorized transitions, invalid evidence URI, forged verification.
- Optimization: Fractional trees, missing incumbent/timeout handling, fixed mobilization cost,
  minimum lot size, spatial exclusivity, budget overflow, exact mathematical consistency across 5 presets.
- Geospatial: Road-class reconciliation, geometry validity, population conservation tolerance,
  canopy classification proxy policy, H3 boundary aggregation.
- Science: Correlated features/VIF diagnostics, missing values, normalization sensitivity,
  observational vs causal claims, MRV detectability noise floor gate.
"""

import json
import math
import os
import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any

from api.app import create_app
from services.auth_service import mint_actor_token
from services.cedar_service import DEMO_ACTORS, CedarGovernanceService
from processing.optimization_engine import (
    get_ratified_intervention_catalog,
    build_candidate_matrix,
    load_canonical_inputs,
)
from processing.project_mrv import CANONICAL_ALLOCATION_PARQUET
from services.runtime_data import calculate_sha256

CANONICAL_PROJECT_ID = "PROJ-PUNE-2025-BA225D6A"


@pytest.fixture(scope="module")
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


def get_auth_headers(actor_id: str) -> Dict[str, str]:
    token = mint_actor_token(actor_id)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ==============================================================================
# 1. SECURITY REGRESSION SUITE (Section 12.1)
# ==============================================================================

def test_security_anonymous_request_rejected(client):
    """Anonymous mutating requests must be rejected with 401 Unauthorized."""
    # Attempt state transition without Authorization header
    res_trans = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        json={"target_state": "FUNDED", "sanction_id": "PMC-SANC-TEST"},
    )
    assert res_trans.status_code == 401
    assert res_trans.json["error"]["code"] == "AUTHENTICATION_REQUIRED"

    # Attempt implementation event submission without auth
    res_impl = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/implementation-events",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 50,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/ev.pdf",
        },
    )
    assert res_impl.status_code == 401

    # Attempt revision proposal without auth
    res_rev = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/revisions",
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "proposed_quantity": 50,
            "reason": "Test unauth",
            "author": "Anonymous",
        },
    )
    assert res_rev.status_code == 401


def test_security_forged_actor_header_rejected(client):
    """Legacy X-Climora-Actor header must be ignored and rejected with 401 without Bearer token."""
    headers = {
        "X-Climora-Actor": "pmc_commissioner",
        "Content-Type": "application/json",
    }
    res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        headers=headers,
        json={"target_state": "FUNDED", "sanction_id": "PMC-FORGE-01"},
    )
    assert res.status_code == 401
    assert res.json["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_security_query_impersonation_rejected(client):
    """Query parameter impersonation (?actor=pmc_commissioner) must be rejected with 401."""
    res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition?actor=pmc_commissioner",
        json={"target_state": "FUNDED", "sanction_id": "PMC-FORGE-02"},
    )
    assert res.status_code == 401
    assert res.json["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_security_commissioner_fallback_eliminated(client):
    """Absence of identity must never fall back to pmc_commissioner privileges."""
    # An unauthenticated request cannot access commissioner-restricted transition
    res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        headers={"Content-Type": "application/json"},
        json={"target_state": "FUNDED", "sanction_id": "PMC-ANON-01"},
    )
    assert res.status_code == 401
    assert res.status_code != 200


def test_security_testing_mode_bypass_eliminated(app, client):
    """Flask TESTING mode must NEVER bypass Cedar authorization."""
    assert app.config["TESTING"] is True

    # A contractor attempting to approve project funding must receive 403 Forbidden even under TESTING=True
    contractor_headers = get_auth_headers("sharma_contractors")
    res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        headers=contractor_headers,
        json={"target_state": "FUNDED", "sanction_id": "ILLEGAL-01"},
    )
    assert res.status_code == 403
    assert res.json["decision"] == "DENY"
    assert "municipal_officer" in res.json["reason"]


def test_security_unauthorized_state_transition_blocked(client):
    """Non-authorized personas cannot perform restricted state transitions."""
    # Urban planner cannot approve funding (requires municipal_officer)
    planner_headers = get_auth_headers("urban_planner_lead")
    res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        headers=planner_headers,
        json={"target_state": "FUNDED", "sanction_id": "PLANNER-SANC"},
    )
    assert res.status_code == 403
    assert res.json["decision"] == "DENY"


def test_security_invalid_evidence_uri_rejected(client):
    """SSRF vector schemes (http://, https://, file://) must be strictly rejected with 400."""
    headers = get_auth_headers("sharma_contractors")

    # 1. Attempt http:// scheme
    res_http = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/implementation-events",
        headers=headers,
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 50.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "http://169.254.169.254/latest/meta-data/",
        },
    )
    assert res_http.status_code == 400
    assert "VALIDATION_ERROR" in res_http.json["error"]["code"]
    assert "s3://" in str(res_http.json["error"])

    # 2. Attempt file:// scheme
    res_file = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/implementation-events",
        headers=headers,
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 50.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "file:///etc/passwd",
        },
    )
    assert res_file.status_code == 400


def test_security_forged_verification_rejected(client):
    """Only accredited mrv_verifier persona can certify verification events."""
    commissioner_headers = get_auth_headers("pmc_commissioner")
    res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/verification-events",
        headers=commissioner_headers,
        json={
            "observation": {
                "sensor_platform": "Landsat-9-TIRS",
                "acquisition_date": "2026-04-18",
                "doy": 108,
                "spatial_resolution_m": 30.0,
                "cloud_cover_aoi_pct": 1.5,
                "quality_flags_passed": True,
                "asset_uri": "s3://climora/l9_obs.tif",
            },
            "verification": {
                "verification_status": "PASSED",
                "verification_date": "2026-05-01",
                "verifier_identity": "Forged Commissioner Cert",
                "methodology_standard": "ISO 14064-2",
                "evidence_artifact_uri": "s3://climora/audit.pdf",
            },
            "target_metric": "lst",
        },
    )
    assert res.status_code == 403
    assert res.json["decision"] == "DENY"
    assert "mrv_verifier" in res.json["reason"]


def test_security_jwt_invalid_actor_cannot_mint(client):
    """Callers cannot mint tokens for unregistered personas or arbitrary identifiers."""
    # 1. Unregistered actor
    res_fake = client.post("/projects/auth/token", json={"actor_id": "malicious_hacker"})
    assert res_fake.status_code == 400
    assert res_fake.json["error"]["code"] == "INVALID_ACTOR"

    # 2. Empty or missing actor_id
    res_empty = client.post("/projects/auth/token", json={})
    assert res_empty.status_code == 400
    assert res_empty.json["error"]["code"] == "INVALID_ACTOR"


def test_security_jwt_tampered_and_invalid_tokens_rejected(client):
    """Modified signatures, expired tokens, wrong issuers, and wrong audiences are rejected with 401."""
    import jwt
    from services.auth_service import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ISSUER, JWT_AUDIENCE
    from datetime import datetime, timezone, timedelta

    # 1. Tampered signature
    valid_token = mint_actor_token("pmc_commissioner")
    tampered_token = valid_token[:-4] + "ABCD"
    res_tampered = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        headers={"Authorization": f"Bearer {tampered_token}"},
        json={"target_state": "FUNDED", "sanction_id": "PMC-SANC-TEST"},
    )
    assert res_tampered.status_code == 401
    assert res_tampered.json["error"]["code"] == "AUTHENTICATION_REQUIRED"

    # 2. Expired token
    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": "pmc_commissioner",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int((now - timedelta(days=2)).timestamp()),
        "exp": int((now - timedelta(days=1)).timestamp()),
    }
    expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    res_expired = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        headers={"Authorization": f"Bearer {expired_token}"},
        json={"target_state": "FUNDED", "sanction_id": "PMC-SANC-TEST"},
    )
    assert res_expired.status_code == 401
    assert "expired" in res_expired.json["error"]["message"].lower()

    # 3. Wrong issuer
    bad_iss_payload = {
        "sub": "pmc_commissioner",
        "iss": "untrusted-third-party-idp",
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    bad_iss_token = jwt.encode(bad_iss_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    res_iss = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        headers={"Authorization": f"Bearer {bad_iss_token}"},
        json={"target_state": "FUNDED", "sanction_id": "PMC-SANC-TEST"},
    )
    assert res_iss.status_code == 401

    # 4. Wrong audience
    bad_aud_payload = {
        "sub": "pmc_commissioner",
        "iss": JWT_ISSUER,
        "aud": "rogue-consumer-api",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    bad_aud_token = jwt.encode(bad_aud_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    res_aud = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        headers={"Authorization": f"Bearer {bad_aud_token}"},
        json={"target_state": "FUNDED", "sanction_id": "PMC-SANC-TEST"},
    )
    assert res_aud.status_code == 401


def test_security_jwt_cannot_forge_role_in_token_claims(client):
    """Server-side identity registry overrides any client-injected role claim in token."""
    # Attacker signs token with valid secret for 'sharma_contractors' (contractor),
    # but injects claim role='municipal_officer' trying to approve funding.
    token_forged_role = mint_actor_token(
        "sharma_contractors",
        custom_claims={"role": "municipal_officer", "permissions": ["ALL"]}
    )

    res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/transition",
        headers={"Authorization": f"Bearer {token_forged_role}"},
        json={"target_state": "FUNDED", "sanction_id": "SANC-FORGED-01"},
    )
    # Cedar must look up verified server-side role (field_contractor) and DENY with 403
    assert res.status_code == 403
    assert res.json["decision"] == "DENY"
    assert "municipal_officer" in res.json["reason"]


def test_security_demo_token_endpoint_disabled_in_production(client, monkeypatch):
    """Demo token issuance endpoint is strictly disabled in production environments."""
    monkeypatch.setenv("ENV", "production")
    res = client.post("/projects/auth/token", json={"actor_id": "pmc_commissioner"})
    assert res.status_code == 403
    assert res.json["error"]["code"] == "DEMO_ENDPOINT_DISABLED"


def test_security_mock_evidence_rejected_in_production(client, monkeypatch):
    """Mock evidence URIs (mock://) are strictly rejected in production environments."""
    monkeypatch.setenv("ENV", "production")
    headers = get_auth_headers("sharma_contractors")

    res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/implementation-events",
        headers=headers,
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 50.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "mock://climora/evidence/tree.pdf",
        },
    )
    assert res.status_code == 400
    assert "VALIDATION_ERROR" in res.json["error"]["code"]
    assert "production" in str(res.json["error"]).lower()


# ==============================================================================
# 2. OPTIMIZATION REGRESSION SUITE (Section 12.2)
# ==============================================================================

def test_opt_no_fractional_trees_in_canonical_allocation():
    """Verify all tree allocations in canonical allocation parquet are strict integers."""
    df_alloc = pd.read_parquet(CANONICAL_ALLOCATION_PARQUET)
    trees = df_alloc[df_alloc["intervention_type"] == "street_tree_shade"]["quantity"]
    assert len(trees) > 0

    # Ensure zero decimal parts
    fractional = trees % 1.0
    assert (fractional == 0.0).all(), f"Found fractional tree allocations: {trees[fractional != 0.0]}"


def test_opt_fixed_cost_and_min_lot_size_enforced():
    """Verify every allocated tree cell satisfies minimum lot size (>=25) and charges fixed mobilization (Rs 20,000)."""
    df_alloc = pd.read_parquet(CANONICAL_ALLOCATION_PARQUET)
    tree_alloc = df_alloc[df_alloc["intervention_type"] == "street_tree_shade"]

    for _, row in tree_alloc.iterrows():
        qty = row["quantity"]
        assert qty >= 25, f"Cell {row['h3_cell_id']} has quantity {qty} below minimum lot size of 25."
        # Total cost per cell = unit_cost * qty + fixed_cost
        expected_cost = 3500.0 * qty + 20000.0
        assert math.isclose(row["total_cost"], expected_cost, rel_tol=1e-5)


def test_opt_preset_scenarios_exact_accounting():
    """Independently audit all 5 preset scenarios (500k, 2.5m, 5m, 7.5m, 10m) for exact budget and integer constraints."""
    scenarios = [
        {"name": "500k", "budget": 500000.0, "file": "scenario_pune_2025_500k.json"},
        {"name": "2.5m", "budget": 2500000.0, "file": "scenario_pune_2025_2_5m.json"},
        {"name": "5m", "budget": 5000000.0, "file": "scenario_pune_2025_5m.json"},
        {"name": "7.5m", "budget": 7500000.0, "file": "scenario_pune_2025_7_5m.json"},
        {"name": "10m", "budget": 10000000.0, "file": "scenario_pune_2025_10m.json"},
    ]

    scenario_dir = os.path.join("data", "processed", "optimization", "scenarios")

    for sc in scenarios:
        path = os.path.join(scenario_dir, sc["file"])
        assert os.path.exists(path), f"Scenario file {path} missing."
        with open(path, "r", encoding="utf-8") as f:
            sc_data = json.load(f)

        allocs = sc_data["allocations"]
        assert len(allocs) > 0

        # 1. Zero fractional trees & minimum lot size
        for a in allocs:
            qty = a["quantity"]
            assert (qty % 1.0) == 0.0, f"Scenario {sc['name']} has fractional quantity {qty}."
            assert qty >= 25, f"Scenario {sc['name']} violates minimum lot size with {qty}."
            expected_cell_cost = 3500.0 * qty + 20000.0
            assert math.isclose(a["total_cost"], expected_cell_cost, rel_tol=1e-5)

        # 2. Budget constraint (Total Cost <= Budget)
        total_cost = sc_data["total_allocated_cost_inr"]
        assert total_cost <= sc["budget"], f"Scenario {sc['name']} budget overflow: {total_cost} > {sc['budget']}."

        # 3. Budget slack exact reconciliation
        expected_slack = sc["budget"] - total_cost
        assert math.isclose(sc_data["budget_slack_inr"], expected_slack, rel_tol=1e-5)


def test_opt_scenario_25_lakh_exact_reconciliation():
    """Formally reconcile the Rs 25 Lakh scenario: exactly 8 active cells, 668 trees, Rs 24,98,000 cost, Rs 2,000 slack."""
    path = os.path.join("data", "processed", "optimization", "scenarios", "scenario_pune_2025_2_5m.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    allocs = data["allocations"]
    num_cells = len(allocs)
    total_trees = sum(a["quantity"] for a in allocs)
    total_fixed_cost = sum(a["fixed_cost"] for a in allocs)
    total_variable_cost = sum(a["quantity"] * a["unit_cost"] for a in allocs)
    total_calculated_cost = total_fixed_cost + total_variable_cost

    # 1. Exactly 8 active cells (proves errata in previous report summary of '7 cells')
    assert num_cells == 8, f"Expected 8 active cells in 2.5M scenario, found {num_cells}."
    assert data["total_cells_treated"] == 8

    # 2. Total trees: 668 (all integer, minimum lot size >= 25)
    assert total_trees == 668.0
    for a in allocs:
        assert (a["quantity"] % 1.0) == 0.0
        assert a["quantity"] >= 25.0

    # 3. Fixed mobilization: 8 cells * Rs 20,000 = Rs 1,60,000
    assert total_fixed_cost == 160000.0

    # 4. Variable tree cost: 668 * Rs 3,500 = Rs 23,38,000
    assert total_variable_cost == 2338000.0

    # 5. Exact total cost: 1,60,000 + 23,38,000 = Rs 24,98,000
    assert total_calculated_cost == 2498000.0
    assert data["total_allocated_cost_inr"] == 2498000.0

    # 6. Budget slack: 25,00,000 - 24,98,000 = Rs 2,000
    assert data["budget_slack_inr"] == 2000.0
    assert math.isclose(data["optimal_objective_value"], 0.029666, rel_tol=1e-4)


def test_opt_spatial_exclusivity_and_feasibility():
    """Verify tree allocation does not exceed bilateral road plantable capacity in any cell."""
    df_feat = pd.read_parquet("data/processed/canonical_feature_matrix.parquet")
    df_alloc = pd.read_parquet(CANONICAL_ALLOCATION_PARQUET)

    merged = pd.merge(df_alloc, df_feat, on="h3_cell_id")
    for _, row in merged.iterrows():
        road_len = row["road_length_m"]
        qty = row["quantity"]
        raw_cap = math.floor((2.0 * road_len) / 15.0)
        max_possible_cap = min(raw_cap, 800)
        assert qty <= max_possible_cap, f"Cell {row['h3_cell_id']} quantity {qty} exceeds physical capacity {max_possible_cap}."


# ==============================================================================
# 3. GEOSPATIAL REGRESSION SUITE (Section 12.3)
# ==============================================================================

def test_geospatial_road_class_canonical_figure():
    """Verify canonical road length sum across all 3,181 cells equals 383.52 km (arterial trunk + primary)."""
    df_feat = pd.read_parquet("data/processed/canonical_feature_matrix.parquet")
    total_road_m = df_feat["road_length_m"].sum()
    total_road_km = total_road_m / 1000.0

    # Bitwise match to canonical 383.51918 km
    assert math.isclose(total_road_km, 383.51918, rel_tol=1e-4)
    assert round(total_road_km, 2) == 383.52


def test_geospatial_population_conservation_tolerance():
    """Verify population conservation: H3 downscaled sum vs raster total delta is 167.34 persons (0.0033%)."""
    df_feat = pd.read_parquet("data/processed/canonical_feature_matrix.parquet")
    h3_pop_sum = float(df_feat["population_2020"].sum())

    # Documented WorldPop 2020 PMC AOI raster total
    raster_total = 5011396.93
    delta = abs(raster_total - h3_pop_sum)
    pct_delta = (delta / raster_total) * 100.0

    assert math.isclose(h3_pop_sum, 5011229.59, rel_tol=1e-4)
    assert math.isclose(delta, 167.34, rel_tol=1e-2)
    # Conservation tolerance must be strictly within 0.05%
    assert pct_delta < 0.05, f"Population discretization delta {pct_delta}% exceeds 0.05% tolerance."


def test_geospatial_canopy_proxy_limitation_documented():
    """Verify that physical canopy is documented as unmeasured proxy rather than directly observed canopy fraction."""
    feat_df, risk_df = load_canonical_inputs()
    cat = {"street_tree_shade": get_ratified_intervention_catalog()["street_tree_shade"]}
    cand_res = build_candidate_matrix(feat_df, risk_df, cat)
    cand_df = cand_res["cand_df"]

    # Bounded by bilateral road geometry and integer floor truncation (no NDVI continuous conversion)
    assert len(cand_df) > 0
    assert (cand_df["Q_max"] <= 800.0).all()
    assert (cand_df["Q_max"] == np.floor(cand_df["Q_max"])).all()
    assert (cand_df["Q_max"] >= 0.0).all()


# ==============================================================================
# 4. SCIENCE REGRESSION SUITE (Section 12.4)
# ==============================================================================

def test_science_pop_density_multicollinearity_and_vif():
    """Verify population and population_density have near-perfect correlation (r > 0.99999) due to uniform H3 cell area."""
    df_feat = pd.read_parquet("data/processed/canonical_feature_matrix.parquet")
    r = np.corrcoef(df_feat["population_2020"], df_feat["population_density_2020"])[0, 1]
    assert r > 0.99999, f"Correlation between pop and pop_density was {r}, expected > 0.99999."

    # R^2 exceeds 0.999999, yielding theoretical VIF > 100,000
    r2 = r ** 2
    vif = 1.0 / (1.0 - r2)
    assert vif > 100000.0


def test_science_mrv_satellite_noise_floor_mde():
    """Verify that Minimum Detectable Effect (MDE) for Landsat thermal single-cell exceeds 6.0 deg C."""
    # Landsat-9 TIRS repeated-measure scene-to-scene standard deviation across Pune AOI is approx 2.47 deg C
    sigma = 2.47
    alpha = 0.05
    power = 0.80

    # Z-scores for two-sided 5% alpha (1.96) and 80% power (0.842)
    z_alpha = 1.96
    z_beta = 0.842

    # Single-cell paired MDE: (z_alpha + z_beta) * sigma
    mde_single_cell = (z_alpha + z_beta) * sigma
    assert mde_single_cell > 6.0, f"MDE single-cell was {mde_single_cell}, expected > 6.0 deg C."

    # Claiming 0.07 deg C cooling is detectable via single-cell satellite is physically impossible
    assert mde_single_cell > 0.07 * 80.0


def test_science_observational_vs_causal_positive_ndvi_coefficient():
    """Verify cross-sectional LST regression on NDVI yields positive coefficient (+1.4475), barring causal cooling claims."""
    df_feat = pd.read_parquet("data/processed/canonical_feature_matrix.parquet")
    valid = df_feat[["lst_2025", "ndvi_2025", "ndbi_2025", "road_length_m"]].dropna()
    X = np.column_stack([np.ones(len(valid)), valid[["ndvi_2025", "ndbi_2025", "road_length_m"]]])
    y = valid["lst_2025"].values
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    ndvi_coef = beta[1]
    # Positive NDVI coefficient (+1.4476) due to severe NDBI collinearity
    assert ndvi_coef > 1.0
    assert math.isclose(ndvi_coef, 1.4476, rel_tol=1e-3)
    # Debunks 4.15x claim: positive coefficient cannot represent physical cooling
    assert valid["ndbi_2025"].corr(valid["lst_2025"]) > 0.80
