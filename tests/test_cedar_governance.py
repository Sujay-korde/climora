"""CLIMORA Phase AWS-5: Cedar Governance & Policy Enforcement Test Suite.

Verifies:
1. Scenario A — Viewer: view_project allowed.
2. Scenario B — Viewer attempts approval: approve_project DENIED with zero mutation.
3. Scenario C — Project Manager proposes revision: propose_revision allowed.
4. Scenario D — Contractor attempts approval: approve_project DENIED with zero mutation.
5. Scenario E — Contractor records implementation: state-aware gating (DENY in PROPOSED, ALLOW in IMPLEMENTING).
6. Scenario F — MRV verifier attempts verification too early: DENY (Cedar authorization != scientific gate).
7. Scenario G — Authorized MRV verification: ALLOW when state is MONITORING and QC passed.
8. Architectural Negative Policy: Absolute forbid on mutating canonical scientific baselines.
9. Explainability & Structured Error Schema: HTTP 403 structured contract on denial.
10. Governance Audit Trail: Chronological in-memory decision logging.
11. Registered Actors Endpoint: Listing available demo personas.
12. Dry-run Governance Check: Non-mutating pre-flight authorization evaluation.
"""

from __future__ import annotations

import json
import pytest

from api.app import create_app
from ingestion.common import calculate_sha256
from services.allocation_service import CANONICAL_ALLOCATION_SHA256
from services.cedar_service import CedarGovernanceService
from services.project_service import CANONICAL_PROJECT_ID


@pytest.fixture
def app():
    """Create a fresh Flask application configured for Cedar testing."""
    application = create_app({"TESTING": True})
    return application


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


# ==============================================================================
# Unit Tests for CedarGovernanceService
# ==============================================================================

def test_cedar_service_direct_unit():
    """Unit test for CedarGovernanceService policy evaluation directly."""
    svc = CedarGovernanceService()

    # 1. Viewer can view
    dec_view = svc.authorize(
        actor_id="citizen_viewer",
        action="view_project",
        project_id=CANONICAL_PROJECT_ID,
        project_state="PROPOSED",
    )
    assert dec_view.allowed is True
    assert dec_view.decision == "ALLOW"
    assert dec_view.policy_id == "policy_universal_view"

    # 2. Viewer cannot approve
    dec_deny_view = svc.authorize(
        actor_id="citizen_viewer",
        action="approve_project",
        project_id=CANONICAL_PROJECT_ID,
        project_state="PROPOSED",
    )
    assert dec_deny_view.allowed is False
    assert dec_deny_view.decision == "DENY"
    assert "lacks statutory authority" in dec_deny_view.reason_summary

    # 3. Project Manager can propose revision
    dec_pm = svc.authorize(
        actor_id="urban_planner_lead",
        action="propose_revision",
        project_id=CANONICAL_PROJECT_ID,
        project_state="PROPOSED",
    )
    assert dec_pm.allowed is True
    assert dec_pm.decision == "ALLOW"
    assert dec_pm.policy_id == "policy_pm_propose_revision"

    # 4. Contractor cannot approve
    dec_contr_app = svc.authorize(
        actor_id="sharma_contractors",
        action="approve_project",
        project_id=CANONICAL_PROJECT_ID,
        project_state="PROPOSED",
    )
    assert dec_contr_app.allowed is False
    assert dec_contr_app.decision == "DENY"

    # 5. Contractor cannot record in PROPOSED
    dec_contr_prop = svc.authorize(
        actor_id="sharma_contractors",
        action="record_implementation",
        project_id=CANONICAL_PROJECT_ID,
        project_state="PROPOSED",
    )
    assert dec_contr_prop.allowed is False
    assert dec_contr_prop.decision == "DENY"

    # 6. Contractor CAN record in IMPLEMENTING
    dec_contr_impl = svc.authorize(
        actor_id="sharma_contractors",
        action="record_implementation",
        project_id=CANONICAL_PROJECT_ID,
        project_state="IMPLEMENTING",
    )
    assert dec_contr_impl.allowed is True
    assert dec_contr_impl.decision == "ALLOW"
    assert dec_contr_impl.policy_id == "policy_contractor_record_impl"

    # 7. MRV verifier cannot verify when unexecutable
    dec_mrv_early = svc.authorize(
        actor_id="sgs_environmental_auditor",
        action="verify_impact",
        project_id=CANONICAL_PROJECT_ID,
        project_state="MONITORING",
        context={"is_mrv_executable": False, "qc_passed": False},
    )
    assert dec_mrv_early.allowed is False
    assert dec_mrv_early.decision == "DENY"
    assert "gating criteria unmet" in dec_mrv_early.reason_summary

    # 8. MRV verifier CAN verify when executable and QC passed
    dec_mrv_ok = svc.authorize(
        actor_id="sgs_environmental_auditor",
        action="verify_impact",
        project_id=CANONICAL_PROJECT_ID,
        project_state="MONITORING",
        context={"is_mrv_executable": True, "qc_passed": True},
    )
    assert dec_mrv_ok.allowed is True
    assert dec_mrv_ok.decision == "ALLOW"
    assert dec_mrv_ok.policy_id == "policy_mrv_verify_impact"

    # 9. Explicit Negative Policy: forbid canonical mutation
    dec_forbid = svc.authorize(
        actor_id="pmc_commissioner",
        action="modify_canonical_data",
        project_id=CANONICAL_PROJECT_ID,
        project_state="PROPOSED",
    )
    assert dec_forbid.allowed is False
    assert dec_forbid.decision == "DENY"
    assert "Immutable Scientific Truth Policy" in dec_forbid.reason_summary


# ==============================================================================
# Scenario Tests via REST API
# ==============================================================================

def test_scenario_a_viewer_read_access(client):
    """Scenario A: Viewer can read project evidence under universal permit policy."""
    pid = CANONICAL_PROJECT_ID
    res = client.get(f"/projects/{pid}", headers={"X-Climora-Actor": "citizen_viewer"})
    assert res.status_code == 200
    assert res.json["status"] == "SUCCESS"
    assert res.json["project"]["identity"]["project_id"] == pid


def test_scenario_b_viewer_attempts_approval_denied_zero_mutation(client):
    """Scenario B: Viewer attempts capital expenditure approval -> DENY (403), zero mutation."""
    pid = CANONICAL_PROJECT_ID

    # Initial state is PROPOSED
    res_before = client.get(f"/projects/{pid}")
    assert res_before.json["project"]["status"] == "PROPOSED"

    # Viewer attempts approval
    res_deny = client.post(
        f"/projects/{pid}/transition",
        headers={"X-Climora-Actor": "citizen_viewer"},
        json={
            "target_state": "FUNDED",
            "sanction_id": "PMC-SANC-FAKE",
            "approved_budget_inr": 10000000.0,
        },
    )
    assert res_deny.status_code == 403
    body = res_deny.json
    assert body["authorized"] is False
    assert body["decision"] == "DENY"
    assert body["action"] == "approve_project"
    assert body["policy_layer"] == "cedar"
    assert body["project_state"] == "PROPOSED"
    assert "municipal_officer" in body["reason"]

    # CRITICAL: Verify zero state mutation occurred
    res_after = client.get(f"/projects/{pid}")
    assert res_after.json["project"]["status"] == "PROPOSED"


def test_scenario_c_pm_proposes_revision_allowed(client):
    """Scenario C: Project Manager proposes allocation revision -> ALLOW (201)."""
    pid = CANONICAL_PROJECT_ID
    res = client.post(
        f"/projects/{pid}/revisions",
        headers={"X-Climora-Actor": "urban_planner_lead"},
        json={
            "h3_cell_id": "89608850003ffff",
            "intervention_code": "street_tree_shade",
            "proposed_quantity": 80.0,
            "reason": "Road widening accommodation near Swargate junction.",
            "author": "Pooja Deshmukh",
        },
    )
    assert res.status_code == 201
    assert res.json["status"] == "SUCCESS"
    assert res.json["revision"]["proposed_quantity"] == 80.0


def test_scenario_d_contractor_attempts_approval_denied(client):
    """Scenario D: Field Contractor attempts project approval -> DENY (403), zero mutation."""
    pid = CANONICAL_PROJECT_ID

    res_deny = client.post(
        f"/projects/{pid}/transition",
        headers={"X-Climora-Actor": "sharma_contractors"},
        json={
            "target_state": "FUNDED",
            "sanction_id": "PMC-SANC-CONTRACTOR",
            "approved_budget_inr": 10000000.0,
        },
    )
    assert res_deny.status_code == 403
    assert res_deny.json["decision"] == "DENY"
    assert res_deny.json["action"] == "approve_project"

    # State unchanged
    res_state = client.get(f"/projects/{pid}")
    assert res_state.json["project"]["status"] == "PROPOSED"


def test_scenario_e_contractor_state_aware_implementation(client):
    """Scenario E: Contractor records implementation only when project reaches FUNDED/IMPLEMENTING."""
    pid = CANONICAL_PROJECT_ID

    # 1. In PROPOSED: Contractor recording implementation is DENIED
    res_prop_deny = client.post(
        f"/projects/{pid}/implementation-events",
        headers={"X-Climora-Actor": "sharma_contractors"},
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 76.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/evidence/tree_01.pdf",
        },
    )
    assert res_prop_deny.status_code == 403
    assert res_prop_deny.json["decision"] == "DENY"
    assert "FUNDED" in res_prop_deny.json["reason"]

    # 2. Municipal Officer sanctions project (PROPOSED -> FUNDED)
    res_sanc = client.post(
        f"/projects/{pid}/transition",
        headers={"X-Climora-Actor": "pmc_commissioner"},
        json={
            "target_state": "FUNDED",
            "sanction_id": "PMC-2025-SANC-8801",
            "approved_budget_inr": 10000000.0,
        },
    )
    assert res_sanc.status_code == 200
    assert res_sanc.json["transition"]["current_state"] == "FUNDED"

    # 3. Transition to IMPLEMENTING
    res_impl_trans = client.post(
        f"/projects/{pid}/transition",
        headers={"X-Climora-Actor": "sharma_contractors"},
        json={"target_state": "IMPLEMENTING"},
    )
    assert res_impl_trans.status_code == 200
    assert res_impl_trans.json["transition"]["current_state"] == "IMPLEMENTING"

    # 4. Now Contractor records physical implementation -> ALLOW (201)
    res_impl_ok = client.post(
        f"/projects/{pid}/implementation-events",
        headers={"X-Climora-Actor": "sharma_contractors"},
        json={
            "intervention_code": "street_tree_shade",
            "h3_cell_id": "89608850003ffff",
            "implemented_quantity": 76.0,
            "completion_date": "2026-04-10",
            "evidence_uri": "s3://climora/evidence/tree_01.pdf",
        },
    )
    assert res_impl_ok.status_code == 201
    assert res_impl_ok.json["status"] == "SUCCESS"
    assert res_impl_ok.json["event"]["implemented_quantity"] == 76.0


def test_scenario_f_mrv_verifier_premature_verification_denied(client):
    """Scenario F: MRV verifier attempts verification when gate is unexecutable -> DENY (403)."""
    pid = CANONICAL_PROJECT_ID

    # Project is in PROPOSED state and MRV is not executable
    res_verif_deny = client.post(
        f"/projects/{pid}/verification-events",
        headers={"X-Climora-Actor": "sgs_environmental_auditor"},
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
                "verifier_identity": "SGS Environmental Auditing",
                "methodology_standard": "ISO 14064-2",
                "evidence_artifact_uri": "s3://climora/audit.pdf",
            },
            "target_metric": "lst",
        },
    )
    assert res_verif_deny.status_code == 403
    assert res_verif_deny.json["decision"] == "DENY"
    assert res_verif_deny.json["action"] == "verify_impact"
    assert "MONITORING" in res_verif_deny.json["reason"] or "gating" in res_verif_deny.json["reason"].lower()


def test_scenario_g_authorized_mrv_verification(app, client):
    """Scenario G: Authorized MRV verification permitted only when scientific gate is executable."""
    pid = CANONICAL_PROJECT_ID
    cedar_svc = app.config["CEDAR_SERVICE"]

    # In MONITORING state with is_mrv_executable=True and qc_passed=True
    decision = cedar_svc.authorize(
        actor_id="sgs_environmental_auditor",
        action="verify_impact",
        project_id=pid,
        project_state="MONITORING",
        context={"is_mrv_executable": True, "qc_passed": True},
    )
    assert decision.allowed is True
    assert decision.decision == "ALLOW"
    assert decision.policy_id == "policy_mrv_verify_impact"
    assert "Accredited MRV Verifier" in decision.reason_summary

    # Prove that even with role=mrv_verifier, if is_mrv_executable is False, Cedar DENIES
    decision_denied = cedar_svc.authorize(
        actor_id="sgs_environmental_auditor",
        action="verify_impact",
        project_id=pid,
        project_state="MONITORING",
        context={"is_mrv_executable": False, "qc_passed": True},
    )
    assert decision_denied.allowed is False
    assert decision_denied.decision == "DENY"
    assert "Scientific MRV gating criteria unmet" in decision_denied.reason_summary



def test_critical_negative_policy_forbid_canonical_mutation(client):
    """Critical Negative Policy: Absolute Cedar forbid against mutating canonical baselines."""
    pid = CANONICAL_PROJECT_ID

    # Even Municipal Commissioner cannot mutate canonical allocation
    res_put = client.put(
        f"/projects/{pid}/allocation",
        headers={"X-Climora-Actor": "pmc_commissioner"},
        json={"quantity": 9999},
    )
    assert res_put.status_code == 403
    body = res_put.json
    assert body["authorized"] is False
    assert body["decision"] == "DENY"
    assert body["action"] == "modify_canonical_data"
    assert "Immutable Scientific Truth Policy" in body["reason"]

    # Byte-for-byte SHA256 integrity check
    from processing.project_mrv import CANONICAL_ALLOCATION_PARQUET
    current_sha = calculate_sha256(CANONICAL_ALLOCATION_PARQUET)
    assert current_sha == CANONICAL_ALLOCATION_SHA256


def test_governance_actors_endpoint(client):
    """GET /projects/governance/actors returns registered demo personas."""
    res = client.get("/projects/governance/actors")
    assert res.status_code == 200
    actors = res.json["actors"]
    assert len(actors) >= 5
    roles = {a["role"] for a in actors}
    assert {"municipal_officer", "project_manager", "field_contractor", "mrv_verifier", "viewer"}.issubset(roles)


def test_dry_run_governance_check_endpoint(client):
    """POST /projects/{id}/governance-check evaluates policy without state mutation."""
    pid = CANONICAL_PROJECT_ID

    # Check officer approval
    res_check = client.post(
        f"/projects/{pid}/governance-check",
        json={
            "actor": "pmc_commissioner",
            "action": "approve_project",
        },
    )
    assert res_check.status_code == 200
    check = res_check.json["check"]
    assert check["allowed"] is True
    assert check["decision"] == "ALLOW"
    assert check["role"] == "municipal_officer"

    # Check contractor approval
    res_check2 = client.post(
        f"/projects/{pid}/governance-check",
        json={
            "actor": "sharma_contractors",
            "action": "approve_project",
        },
    )
    assert res_check2.status_code == 200
    check2 = res_check2.json["check"]
    assert check2["allowed"] is False
    assert check2["decision"] == "DENY"


def test_governance_audit_trail_endpoint(client):
    """GET /projects/{id}/governance-audit returns chronological decision trail."""
    pid = CANONICAL_PROJECT_ID

    # Trigger an authorization check to ensure records exist
    client.get(f"/projects/{pid}", headers={"X-Climora-Actor": "citizen_viewer"})

    res = client.get(f"/projects/{pid}/governance-audit")
    assert res.status_code == 200
    trail = res.json["audit_trail"]
    assert isinstance(trail, list)
    if len(trail) > 0:
        first = trail[0]
        assert "audit_id" in first
        assert "decision" in first
        assert "actor_id" in first
        assert "timestamp_utc" in first


# ==============================================================================
# Phase 2D.1: Workspace-Authorization Separation & Tests A through J
# ==============================================================================

def test_phase_2d1_test_a_workspace_lens_does_not_grant_authorization(client):
    """Test A: Supplying a client workspace/lens header or param does NOT grant Cedar authorization."""
    pid = CANONICAL_PROJECT_ID

    # A citizen attempting sanction while claiming 'municipal_sanction' workspace/lens
    res = client.post(
        f"/projects/{pid}/transition?lens=municipal_sanction",
        headers={
            "X-Climora-Actor": "citizen_viewer",
            "X-Climora-Workspace": "municipal_sanction",
            "X-Climora-Lens": "sanction",
        },
        json={
            "target_state": "FUNDED",
            "sanction_id": "PMC-SANC-ATTACK",
            "approved_budget_inr": 10000000.0,
        },
    )
    assert res.status_code == 403
    assert res.json["authorized"] is False
    assert res.json["decision"] == "DENY"
    assert "municipal_officer" in res.json["reason"]

    # Verify project state untouched
    res_state = client.get(f"/projects/{pid}")
    assert res_state.json["project"]["status"] == "PROPOSED"


def test_phase_2d1_test_b_citizen_unable_to_sanction(client):
    """Test B: Citizen remains unable to perform municipal sanction actions."""
    pid = CANONICAL_PROJECT_ID
    res = client.post(
        f"/projects/{pid}/transition",
        headers={"X-Climora-Actor": "citizen_viewer"},
        json={"target_state": "FUNDED", "sanction_id": "PMC-1", "approved_budget_inr": 10000000.0},
    )
    assert res.status_code == 403
    assert res.json["decision"] == "DENY"


def test_phase_2d1_test_c_planner_retains_permitted_actions(client):
    """Test C: Planner retains existing permitted actions (propose revision)."""
    pid = CANONICAL_PROJECT_ID
    res = client.post(
        f"/projects/{pid}/revisions",
        headers={"X-Climora-Actor": "urban_planner_lead"},
        json={
            "h3_cell_id": "89608850003ffff",
            "intervention_code": "street_tree_shade",
            "proposed_quantity": 85.0,
            "reason": "Test C planner revision",
            "author": "Pooja Deshmukh",
        },
    )
    assert res.status_code == 201
    assert res.json["status"] == "SUCCESS"


def test_phase_2d1_test_d_municipal_authority_retains_sanction(client):
    """Test D: Municipal authority retains existing sanction capability in PROPOSED state."""
    pid = CANONICAL_PROJECT_ID
    res_check = client.post(
        f"/projects/{pid}/governance-check",
        json={"actor": "pmc_commissioner", "action": "approve_project"},
    )
    assert res_check.status_code == 200
    assert res_check.json["check"]["allowed"] is True
    assert res_check.json["check"]["decision"] == "ALLOW"


def test_phase_2d1_test_e_contractor_retains_implementation_capability(app):
    """Test E: Contractor retains existing implementation capability gated by state."""
    cedar_svc = app.config["CEDAR_SERVICE"]
    # Denied in PROPOSED
    dec_prop = cedar_svc.authorize(
        actor_id="sharma_contractors",
        action="record_implementation",
        project_id=CANONICAL_PROJECT_ID,
        project_state="PROPOSED",
    )
    assert dec_prop.allowed is False

    # Allowed in IMPLEMENTING
    dec_impl = cedar_svc.authorize(
        actor_id="sharma_contractors",
        action="record_implementation",
        project_id=CANONICAL_PROJECT_ID,
        project_state="IMPLEMENTING",
    )
    assert dec_impl.allowed is True


def test_phase_2d1_test_f_mrv_auditor_retains_verification_capability(app):
    """Test F: MRV auditor retains verification capability strictly when gates pass."""
    cedar_svc = app.config["CEDAR_SERVICE"]
    # Denied when QC fails
    dec_fail = cedar_svc.authorize(
        actor_id="sgs_environmental_auditor",
        action="verify_impact",
        project_id=CANONICAL_PROJECT_ID,
        project_state="MONITORING",
        context={"is_mrv_executable": True, "qc_passed": False},
    )
    assert dec_fail.allowed is False

    # Allowed when all pass
    dec_pass = cedar_svc.authorize(
        actor_id="sgs_environmental_auditor",
        action="verify_impact",
        project_id=CANONICAL_PROJECT_ID,
        project_state="MONITORING",
        context={"is_mrv_executable": True, "qc_passed": True},
    )
    assert dec_pass.allowed is True


def test_phase_2d1_test_g_no_lens_or_actor_can_mutate_canonical_truth(client):
    """Test G: Negative Policy: No lens, actor, or officer can mutate canonical data."""
    pid = CANONICAL_PROJECT_ID
    for actor in ["pmc_commissioner", "urban_planner_lead", "citizen_viewer", "sharma_contractors", "sgs_environmental_auditor"]:
        res = client.put(
            f"/projects/{pid}/allocation",
            headers={"X-Climora-Actor": actor, "X-Climora-Lens": "sanction"},
            json={"quantity": 9999},
        )
        assert res.status_code == 403
        assert res.json["decision"] == "DENY"
        assert res.json["action"] == "modify_canonical_data"


def test_phase_2d1_test_h_workspace_selection_cannot_mutate_state(client):
    """Test H: Workspace/lens parameter on read requests cannot mutate state."""
    pid = CANONICAL_PROJECT_ID
    res = client.get(f"/projects/{pid}?lens=municipal_sanction&workspace=sanction")
    assert res.status_code == 200
    assert res.json["project"]["status"] == "PROPOSED"


def test_phase_2d1_test_i_arbitrary_actor_defaults_to_least_privilege_viewer(client):
    """Test I: Arbitrary actor values default to viewer role and are denied privileged actions."""
    pid = CANONICAL_PROJECT_ID
    res = client.post(
        f"/projects/{pid}/transition",
        headers={"X-Climora-Actor": "unregistered_external_attacker"},
        json={"target_state": "FUNDED", "sanction_id": "FAKE", "approved_budget_inr": 10000000.0},
    )
    assert res.status_code == 403
    assert res.json["decision"] == "DENY"
    assert "viewer" in res.json["reason"]


def test_phase_2d1_test_j_mrv_restrictions_unchanged_synthetic_rejected():
    """Test J: Synthetic demo fixtures cannot certify project to VERIFIED."""
    from processing.project_mrv import ProjectStateMachine, ProjectLifecycleState
    res, msg = ProjectStateMachine.can_transition(
        current_state=ProjectLifecycleState.MONITORING,
        target_state=ProjectLifecycleState.VERIFIED,
        context={
            "implementation_events": [type("Obj", (), {"is_synthetic_demo": False})()],
            "observation_event": type("Obj", (), {"is_synthetic_demo": False})(),
            "qc_result": type("Obj", (), {"all_passed": True})(),
            "verification_event": type("Obj", (), {"verification_status": "PASSED", "is_synthetic_demo": True})(),
        },
    )
    assert res is False
    assert "Demo fixture" in msg or "REJECTED" in msg
