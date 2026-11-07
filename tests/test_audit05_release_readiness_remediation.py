"""Audit 05 Release Readiness Remediation Verification Test Suite.

Exhaustively verifies the remediation of all 7 checklist items from Audit 04/05:
1. Frontend Bearer JWT token injection compatibility.
2. Multi-cell corridor aggregation binding (>= 2 cells) respecting sensor noise floor.
3. Ground nursery audit protocols, invoice lineage, and physical tree guard placement.
4. Enterprise OIDC authentication provider, token decoding, and IdP group role mapping.
5. Production S3 KMS evidence bucket with HeadObject existence and CMK encryption validation.
6. Relational persistence architecture (Aurora PostgreSQL Multi-AZ cluster and connection pooling).
7. Multi-year empirical thermal ground sensor network, Difference-in-Differences (DiD), and hybrid MRV fusion.
"""

from __future__ import annotations

import os
from unittest.mock import patch
import pytest

from api.app import create_app
from services.auth_service import (
    OIDCAuthenticationProvider,
    get_auth_mode,
    get_oidc_provider,
    mint_actor_token,
    verify_bearer_token,
)
from services.evidence_vault import (
    EvidenceEncryptionViolationError,
    EvidenceObjectNotFoundError,
    evidence_vault,
)
from services.exceptions import ValidationError, VerificationNotEligibleError
from services.ground_sensors import (
    DifferenceInDifferencesEngine,
    HybridMRVFusionEngine,
    get_hybrid_mrv_engine,
)
from services.mrv_service import MRVDomainService
from services.persistence import get_persistence_service
from services.project_service import CANONICAL_PROJECT_ID, ProjectDomainService


@pytest.fixture
def app():
    os.environ["ENV"] = "development"
    os.environ["CLIMORA_AUTH_MODE"] = "DEMO"
    app = create_app({"TESTING": True, "PROPAGATE_EXCEPTIONS": True})
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# ==============================================================================
# Checklist Item 1: Frontend Bearer JWT Compatibility
# ==============================================================================

def test_checklist_1_bearer_jwt_auth_headers_and_verification():
    """Confirms token format produced by auth service matches frontend Authorization: Bearer <token>."""
    token = mint_actor_token("urban_planner_lead")
    assert isinstance(token, str) and len(token) > 20
    auth_header = f"Bearer {token}"

    actor_id, actor_info = verify_bearer_token(auth_header)
    assert actor_id == "urban_planner_lead"
    assert actor_info["role"] == "project_manager"
    assert "PMC" in actor_info["organization"]


# ==============================================================================
# Checklist Item 2: Multi-Cell Corridor Aggregation (>= 2 cells) Noise Floor Gate
# ==============================================================================

def test_checklist_2_corridor_aggregation_single_cell_rejected(app):
    """Verifies that an observation of a single isolated cell is rejected due to sensor noise floor."""
    with app.app_context():
        mrv_service = MRVDomainService()
        pid = CANONICAL_PROJECT_ID

        # Record implementation on one cell
        mrv_service.record_implementation_event(
            project_id=pid,
            intervention_code="street_tree_shade",
            h3_cell_id="89608850003ffff",
            implemented_quantity=76.0,
            contractor_id="PMC-FORESTRY-CONTRACTOR",
            completion_date="2026-04-15",
            evidence_uri="s3://climora-evidence-vault-pune/pune/2026/04/impl_89608850003ffff.tar.gz",
        )

        obs_payload = {
            "observation_id": "OBS-2026-SINGLE-CELL",
            "sensor_platform": "LANDSAT_9",
            "acquisition_date": "2026-05-15",
            "doy": 135,
            "spatial_resolution_m": 30.0,
            "cloud_cover_aoi_pct": 2.1,
            "quality_flags_passed": True,
            "asset_uri": "s3://climora-pune-mrv/l9_obs.tif",
            "target_metric": "lst",
            "corridor_cells": ["89608850003ffff"],  # Single cell only!
        }

        verif_payload = {
            "verification_status": "PASSED",
            "verification_date": "2026-05-20",
            "verifier_identity": "ISO-14064-ACCREDITED-AUDITOR",
            "methodology_standard": "ISO 14064-2:2019",
            "evidence_artifact_uri": "s3://climora-pune-mrv/audit_report_sgs_2026.pdf",
        }

        with pytest.raises(VerificationNotEligibleError) as exc_info:
            mrv_service.record_verification_event(
                project_id=pid,
                observation_payload=obs_payload,
                verification_payload=verif_payload,
            )

        assert exc_info.value.code == "VERIFICATION_NOT_ELIGIBLE"
        assert exc_info.value.details["observed_cell_count"] == 1
        assert exc_info.value.details["required_aggregation_minimum"] == 2
        assert exc_info.value.details["sensor_noise_floor_mde_degc"] == 6.91


def test_checklist_2_corridor_aggregation_multi_cell_accepted(app):
    """Verifies that an aggregated corridor observation (>= 2 cells) passes the noise floor gate."""
    with app.app_context():
        mrv_service = MRVDomainService()
        pid = CANONICAL_PROJECT_ID
        all_cells = list(mrv_service._df_alloc["h3_cell_id"].unique())

        # Record implementation on all treated cells
        for cell in all_cells:
            mrv_service.record_implementation_event(
                project_id=pid,
                intervention_code="street_tree_shade",
                h3_cell_id=cell,
                implemented_quantity=76.0,
                completion_date="2026-04-15",
                evidence_uri="s3://climora-evidence-vault-pune/pune/2026/04/impl_89608850003ffff.tar.gz",
            )

        obs_payload = {
            "observation_id": "OBS-2026-MULTI-CELL",
            "sensor_platform": "Landsat-9-TIRS",
            "acquisition_date": "2026-04-18",
            "doy": 108,
            "spatial_resolution_m": 30.0,
            "cloud_cover_aoi_pct": 1.5,
            "quality_flags_passed": True,
            "asset_uri": "s3://climora-pune-mrv/l9_obs.tif",
            "target_metric": "lst",
            "corridor_cells": all_cells,  # 28 cells (aggregated corridor)
            "observed_cell_count": len(all_cells),
        }

        verif_payload = {
            "verification_status": "PASSED",
            "verification_date": "2026-05-20",
            "verifier_identity": "ISO-14064-ACCREDITED-AUDITOR",
            "methodology_standard": "ISO 14064-2:2019",
            "evidence_artifact_uri": "s3://climora-pune-mrv/audit_report_sgs_2026.pdf",
        }

        result = mrv_service.record_verification_event(
            project_id=pid,
            observation_payload=obs_payload,
            verification_payload=verif_payload,
        )

        assert result["verification_id"] is not None
        assert result["corridor_cell_count"] >= 2
        assert result["aggregation_status"] == "CORRIDOR_AGGREGATED_VALID"


# ==============================================================================
# Checklist Item 3: Ground Nursery Audit & Physical Tree Guards
# ==============================================================================

def test_checklist_3_ground_nursery_and_tree_guards_validation(app):
    """Verifies nursery invoice lineage and tree guard physical placement tracking."""
    with app.app_context():
        mrv_service = MRVDomainService()
        pid = CANONICAL_PROJECT_ID

        # 1. Valid implementation event with tree guards and nursery invoice
        res = mrv_service.record_implementation_event(
            project_id=pid,
            intervention_code="street_tree_shade",
            h3_cell_id="89608850003ffff",
            implemented_quantity=100.0,
            nursery_invoice_ref="s3://climora-evidence-vault-pune/invoices/PMC_NURSERY_INV_2026_04.pdf",
            nursery_batch_id="BATCH-PUNE-NEEM-2026-01",
            tree_guards_installed=True,
            tree_guards_count=100.0,
            evidence_uri="s3://climora-evidence-vault-pune/pune/2026/04/impl_89608850003ffff.tar.gz",
        )

        assert res["nursery_audit"] is not None
        assert res["nursery_audit"]["audit_protocol"] == "PMC-GROUND-NURSERY-GUARD-V1"
        assert res["nursery_audit"]["tree_guards_installed"] is True
        assert res["nursery_audit"]["tree_guards_count"] == 100.0
        assert res["nursery_audit"]["nursery_batch_id"] == "BATCH-PUNE-NEEM-2026-01"

        # 2. Invalid nursery reference scheme (SSRF prevention)
        with pytest.raises(ValidationError) as exc:
            mrv_service.record_implementation_event(
                project_id=pid,
                intervention_code="street_tree_shade",
                h3_cell_id="89608850003ffff",
                implemented_quantity=50.0,
                nursery_invoice_ref="http://malicious-site.com/invoice.pdf",
                evidence_uri="s3://climora-evidence-vault-pune/pune/2026/04/impl_89608850003ffff.tar.gz",
            )
        assert "Invalid nursery invoice reference" in exc.value.message


# ==============================================================================
# Checklist Item 4: Enterprise OIDC Authentication Provider
# ==============================================================================

def test_checklist_4_oidc_config_endpoint(client):
    """Verifies that GET /projects/auth/oidc/config returns enterprise federation parameters."""
    res = client.get("/projects/auth/oidc/config")
    assert res.status_code == 200
    data = res.json
    assert data["status"] == "SUCCESS"
    assert "cognito-idp" in data["issuer"]
    assert data["audience"] == "climora-enterprise-pune"
    assert "pmc_urban_planners" in data["idp_role_mappings"]


def test_checklist_4_oidc_token_verification_and_claim_mapping():
    """Verifies decoding and role claim mapping for enterprise OIDC tokens."""
    provider = get_oidc_provider()

    # Planner role mapping
    token_planner = provider.mint_test_oidc_token(
        sub="usr_planner_001",
        role="pmc_urban_planners",
        email="lead.planner@pmc.gov.in",
    )
    actor_id, actor_info = provider.verify_oidc_token(token_planner)
    assert actor_id == "oidc_usr_planner_001"
    assert actor_info["role"] == "project_manager"
    assert actor_info["email"] == "lead.planner@pmc.gov.in"
    assert actor_info["auth_provider"] == "OIDC"

    # Verifier role mapping
    token_verifier = provider.mint_test_oidc_token(
        sub="usr_auditor_002",
        role="iso_14064_auditors",
        email="auditor@sgs.com",
    )
    _, verif_info = provider.verify_oidc_token(token_verifier)
    assert verif_info["role"] == "mrv_verifier"


def test_checklist_4_demo_minting_disabled_in_oidc_mode(client):
    """Verifies that POST /projects/auth/token is strictly blocked when CLIMORA_AUTH_MODE == 'OIDC'."""
    with patch.dict(os.environ, {"CLIMORA_AUTH_MODE": "OIDC"}):
        res = client.post(
            "/projects/auth/token",
            json={"actor_id": "urban_planner_lead"},
        )
        assert res.status_code == 403
        assert res.json["error"]["code"] == "DEMO_ENDPOINT_DISABLED"
        assert "enterprise OIDC" in res.json["error"]["message"]


# ==============================================================================
# Checklist Item 5: Production S3 KMS Evidence Vault
# ==============================================================================

def test_checklist_5_unapproved_s3_bucket_rejected():
    """Verifies that S3 URIs outside approved municipal namespaces are rejected."""
    with pytest.raises(ValidationError) as exc:
        evidence_vault.validate_evidence_object("s3://unauthorized-random-bucket/evidence.pdf")
    assert "Unapproved evidence bucket" in exc.value.message


def test_checklist_5_nonexistent_s3_object_rejected():
    """Verifies that non-existent objects in approved buckets raise EvidenceObjectNotFoundError."""
    with pytest.raises(EvidenceObjectNotFoundError) as exc:
        evidence_vault.validate_evidence_object("s3://climora-evidence-vault-pune/non_existent_file.xyz")
    assert exc.value.code == "EVIDENCE_OBJECT_NOT_FOUND"


def test_checklist_5_kms_encryption_violation_rejected():
    """Verifies that unencrypted or non-KMS artifacts raise EvidenceEncryptionViolationError."""
    # Register an object with standard AES256 (missing KMS)
    evidence_vault.register_mock_object(
        bucket="climora-evidence-vault-pune",
        key="unencrypted_artifact.pdf",
        sha256="abc123",
        kms_encrypted=False,
    )
    with pytest.raises(EvidenceEncryptionViolationError) as exc:
        evidence_vault.validate_evidence_object("s3://climora-evidence-vault-pune/unencrypted_artifact.pdf")
    assert exc.value.code == "EVIDENCE_KMS_ENCRYPTION_MISSING"


def test_checklist_5_presigned_upload_url_endpoint(client):
    """Verifies generation of KMS-constrained pre-signed upload URLs."""
    token = mint_actor_token("urban_planner_lead")
    res = client.post(
        f"/projects/{CANONICAL_PROJECT_ID}/evidence/presigned-url",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "filename": "nursery_delivery_slip.pdf",
            "artifact_category": "nursery_audit",
            "content_type": "application/pdf",
        },
    )
    assert res.status_code == 200
    upload = res.json["upload"]
    assert "upload_url" in upload
    assert upload["storage_ref"].startswith("s3://")
    assert upload["required_headers"]["x-amz-server-side-encryption"] == "aws:kms"


# ==============================================================================
# Checklist Item 6: Aurora PostgreSQL Multi-AZ Persistence Architecture
# ==============================================================================

def test_checklist_6_cluster_health_endpoint(client):
    """Verifies that GET /projects/cluster/health returns Multi-AZ cluster status."""
    res = client.get("/projects/cluster/health")
    assert res.status_code == 200
    health = res.json
    assert health["status"] == "HEALTHY"
    assert "cluster_topology" in health
    assert health["cluster_topology"]["multi_az_active"] is True
    assert "ap-south-1a" in health["cluster_topology"]["multi_az_availability_zones"]
    assert health["connection_pool"]["health"] == "OK"


def test_checklist_6_relational_crud_operations():
    """Verifies relational persistence of projects, events, and telemetry."""
    persistence = get_persistence_service()

    # 1. Save and retrieve project
    mock_proj = {
        "section_1_project_identity": {
            "project_id": "PROJ-PUNE-TEST-2026",
            "project_name": "Kothrud Urban Canopy Test",
            "city_id": "pune",
            "lifecycle_state": "PROPOSED",
            "target_metric": "lst_celsius",
        },
        "section_3_portfolio_allocation": {
            "budget_constraint_inr": 10000000.0,
            "allocated_cost_inr": 9992500.0,
        },
    }
    persistence.save_project(mock_proj)
    fetched = persistence.get_project("PROJ-PUNE-TEST-2026")
    assert fetched is not None
    assert fetched["section_1_project_identity"]["project_id"] == "PROJ-PUNE-TEST-2026"

    # 2. Update lifecycle state
    persistence.update_project_state("PROJ-PUNE-TEST-2026", "FUNDED")
    updated = persistence.get_project("PROJ-PUNE-TEST-2026")
    assert updated["section_1_project_identity"]["lifecycle_state"] == "FUNDED"

    # 3. List projects
    plist = persistence.list_projects()
    assert any(p["project_id"] == "PROJ-PUNE-TEST-2026" for p in plist)


# ==============================================================================
# Checklist Item 7: Multi-Year Ground Sensor Network & Hybrid MRV Fusion
# ==============================================================================

def test_checklist_7_ground_telemetry_physical_validation(client):
    """Verifies temperature bounds and physical validation on ground telemetry ingestion."""
    token = mint_actor_token("sharma_contractors")
    pid = CANONICAL_PROJECT_ID

    # 1. Unphysical temperature reading (e.g. 65°C)
    res_bad = client.post(
        f"/projects/{pid}/ground-telemetry",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "readings": [
                {
                    "sensor_id": "SENSOR-01",
                    "h3_cell_id": "89608850003ffff",
                    "timestamp": "2026-04-10T12:00:00Z",
                    "ambient_temp_degc": 68.5,  # Unphysical
                }
            ]
        },
    )
    assert res_bad.status_code == 400
    assert "out of realistic physical bounds" in res_bad.json["error"]["message"]

    # 2. Valid readings ingestion
    res_ok = client.post(
        f"/projects/{pid}/ground-telemetry",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "readings": [
                {
                    "sensor_id": "SENSOR-01",
                    "h3_cell_id": "89608850003ffff",
                    "timestamp": "2026-04-10T12:00:00Z",
                    "ambient_temp_degc": 36.8,
                    "surface_temp_degc": 39.2,
                    "relative_humidity": 44.0,
                    "is_treated_corridor": True,
                }
            ]
        },
    )
    assert res_ok.status_code == 201
    assert res_ok.json["ingested_count"] == 1


def test_checklist_7_difference_in_differences_and_hybrid_mrv_audit(client):
    """Verifies the DiD causal cooling estimation and hybrid satellite-ground fusion audit."""
    hybrid_engine = get_hybrid_mrv_engine()
    pid = "PROJ-PUNE-DID-TEST-2026"

    # Perform hybrid audit
    audit_res = hybrid_engine.perform_hybrid_mrv_audit(
        project_id=pid,
        satellite_lst_delta=-0.85,
    )

    assert audit_res["status"] == "SUCCESS"
    assert audit_res["hybrid_audit_verdict"] == "VERIFIED_EMPIRICAL"
    assert audit_res["confidence_score"] >= 0.70

    # Verify DiD calculation metrics
    did = audit_res["ground_sensor_network"]["did_results"]
    assert did["did_cooling_effect_degc"] < 0.0  # Demonstrates net cooling relative to control
    assert did["statistically_significant"] is True
    assert did["empirical_mde_degc"] < 0.5  # Far below satellite noise floor of 6.91°C!
    assert "ISO 14064-2:2019" in audit_res["methodology"]

    # Test endpoint GET /projects/{project_id}/mrv/hybrid-audit
    res_api = client.get(f"/projects/{CANONICAL_PROJECT_ID}/mrv/hybrid-audit")
    assert res_api.status_code == 200
    assert res_api.json["hybrid_audit_verdict"] == "VERIFIED_EMPIRICAL"
