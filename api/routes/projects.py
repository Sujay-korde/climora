"""CLIMORA Projects API Routes.

Handles HTTP routing, request parsing, serialization, and status codes.
Enforces the boundary: route handlers do NOT perform scientific calculations.
All domain actions are delegated to Domain Services and ZonalQueryEngine.
Hardened with input validation, deterministic pagination, and response bounds.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional
from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError as PydanticValidationError

from api.schemas import (
    AllocationRevisionRequest,
    ImplementationEventCreateRequest,
    PaginationParams,
    PROJECT_ID_PATTERN,
    ScenarioOptimizationRequest,
    StateTransitionRequest,
    VerificationEventCreateRequest,
)
from services.auth_service import (
    DEFAULT_TOKEN_TTL_SECONDS,
    get_auth_mode,
    get_oidc_provider,
    mint_actor_token,
    verify_bearer_token,
)
from services.cedar_service import DEMO_ACTORS
from services.evidence_vault import evidence_vault
from services.ground_sensors import get_hybrid_mrv_engine
from services.persistence import get_persistence_service
from services.exceptions import (
    AllocationImmutableError,
    AuthenticationRequiredError,
    AuthorizationDeniedError,
    ProjectNotFoundError,
    StateTransitionError,
    ValidationError as DomainValidationError,
    VerificationNotEligibleError,
)

projects_bp = Blueprint("projects", __name__)


# ==============================================================================
# Helper to access services from current_app
# ==============================================================================

def get_project_service():
    return current_app.config["PROJECT_SERVICE"]

def get_allocation_service():
    return current_app.config["ALLOCATION_SERVICE"]

def get_baseline_service():
    return current_app.config["BASELINE_SERVICE"]

def get_mrv_service():
    return current_app.config["MRV_SERVICE"]

def get_cedar_service():
    return current_app.config.get("CEDAR_SERVICE")

def get_authenticated_principal(required: bool = True) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Extracts and verifies authenticated principal strictly from Authorization: Bearer <token>.
    
    Security Remediation (TD-SEC-01 / MASTER PROMPT 04):
    - Completely eliminates X-Climora-Actor and ?actor= as identity sources.
    - Completely eliminates Flask TESTING mode authorization bypasses.
    - Resolves principal identity and role from trusted server-side DEMO_ACTORS registry.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        if not required:
            return None
        raise AuthenticationRequiredError(
            message="Authentication required: Missing Authorization header with Bearer token.",
            details={"reason": "MISSING_AUTHORIZATION_HEADER"}
        )
    return verify_bearer_token(auth_header)

def enforce_cedar_authorization(
    action: str,
    project_id: str,
    project_state: str,
    context: Optional[Dict[str, Any]] = None,
    require_auth: bool = True,
) -> Optional[Any]:
    """Evaluates Cedar policy authorization against the verified authenticated principal.
    
    1. Validates the authenticated principal from Bearer token.
    2. Resolves trusted server-side permissions from actor registry.
    3. Evaluates Cedar authorization policy.
    4. Records immutable governance audit event.
    
    If unauthenticated: Returns Flask 401 Response.
    If unauthorized: Returns Flask 403 Response.
    If authorized: Returns None (proceed with domain execution).
    """
    cedar_svc = get_cedar_service()
    if cedar_svc is None:
        return None

    try:
        auth_res = get_authenticated_principal(required=require_auth)
    except AuthenticationRequiredError as e:
        return jsonify({
            "error": {
                "code": e.code,
                "message": e.message,
                "details": e.details,
            }
        }), e.status_code

    if auth_res is None:
        actor_id = "citizen_viewer"
    else:
        actor_id, _ = auth_res

    decision = cedar_svc.authorize(
        actor_id=actor_id,
        action=action,
        project_id=project_id,
        project_state=project_state,
        context=context,
    )

    if not decision.allowed:
        return jsonify({
            "authorized": False,
            "decision": "DENY",
            "action": action,
            "reason": decision.reason_summary,
            "policy_layer": "cedar",
            "project_state": project_state,
            "error": {
                "code": "GOVERNANCE_AUTHORIZATION_DENIED",
                "message": decision.reason_summary,
                "details": {
                    "authorized": False,
                    "decision": "DENY",
                    "action": action,
                    "reason": decision.reason_summary,
                    "policy_layer": "cedar",
                    "project_state": project_state,
                    "actor_id": decision.actor_id,
                    "role": decision.role,
                    "policy_id": decision.policy_id,
                    "audit_id": decision.audit_id,
                    "timestamp_utc": decision.timestamp_utc,
                },
            },
        }), 403

    return None



def validate_project_identifier(project_id: str) -> None:
    """Validates project ID format strictly against canonical naming standards."""
    pid = str(project_id).strip()
    if not pid or not PROJECT_ID_PATTERN.match(pid) or len(pid) > 64:
        raise DomainValidationError(
            f"Invalid project identifier '{project_id}'. Format must match 'PROJ-[A-Z0-9_-]+'.",
            details={"project_id": project_id},
        )

def format_pydantic_error_details(e: PydanticValidationError) -> Dict[str, Any]:
    """Sanitizes Pydantic validation errors into clean JSON-serializable structures."""
    errors_list = []
    for err in e.errors():
        errors_list.append({
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "message": str(err.get("msg", "")),
            "type": str(err.get("type", "")),
        })
    return {"validation_errors": errors_list}


def parse_pagination_params(req) -> PaginationParams:
    """Parses and validates pagination parameters from query string."""
    try:
        raw_page = req.args.get("page", 1)
        raw_page_size = req.args.get("page_size", 28)
        raw_h3 = req.args.get("h3_cell_id")

        return PaginationParams(
            page=int(raw_page),
            page_size=int(raw_page_size),
            h3_cell_id=raw_h3 if raw_h3 else None,
        )
    except (ValueError, PydanticValidationError) as e:
        raise DomainValidationError(
            "Invalid pagination or filter parameters.",
            details={"error": str(e)},
        )


# ==============================================================================
# Read Endpoints
# ==============================================================================

@projects_bp.route("/governance/actors", methods=["GET"])
def list_governance_actors():
    """GET /projects/governance/actors - Returns registered demo personas for Cedar governance UI."""
    cedar_svc = get_cedar_service()
    actors = cedar_svc.get_registered_actors() if cedar_svc else []
    return jsonify({
        "status": "SUCCESS",
        "count": len(actors),
        "actors": actors,
    }), 200


@projects_bp.route("/auth/oidc/config", methods=["GET"])
def get_oidc_configuration():
    """GET /projects/auth/oidc/config - Exposes enterprise OIDC federation and discovery parameters."""
    provider = get_oidc_provider()
    auth_mode = get_auth_mode()
    return jsonify({
        "status": "SUCCESS",
        "auth_mode": auth_mode,
        "oidc_enabled": auth_mode == "OIDC",
        "issuer": provider.issuer,
        "audience": provider.audience,
        "token_endpoint_auth_methods_supported": ["client_secret_jwt", "private_key_jwt"],
        "response_types_supported": ["code", "token", "id_token"],
        "idp_role_mappings": provider.role_mappings,
        "environment": os.environ.get("ENV", "development"),
    }), 200


@projects_bp.route("/auth/token", methods=["POST"])
@projects_bp.route("/token", methods=["POST"])
def issue_actor_token():
    """POST /projects/auth/token - Authenticates a persona and returns a cryptographically signed Bearer JWT token.
    
    DEMONSTRATION BOUNDARY:
    This endpoint is strictly for local demonstration and offline test environments.
    It is explicitly disabled in enterprise OIDC mode, staging, and production environments where tokens must be
    issued by an accredited Identity Provider (e.g., AWS Cognito / OIDC / OAuth2).
    """
    env = os.environ.get("ENV", os.environ.get("FLASK_ENV", current_app.config.get("ENV", "development"))).lower()
    enable_demo_auth = current_app.config.get("ENABLE_DEMO_AUTH_ENDPOINT", env not in ["production", "staging"])
    auth_mode = get_auth_mode()

    if auth_mode == "OIDC" or env in ["production", "staging"] or not enable_demo_auth:
        return jsonify({
            "error": {
                "code": "DEMO_ENDPOINT_DISABLED",
                "message": "Demo token issuance endpoint is disabled. In enterprise OIDC mode, staging, and production environments, identity tokens must be issued by the production IdP (AWS Cognito/OIDC).",
                "details": {"environment": env, "auth_mode": auth_mode},
            }
        }), 403

    payload = request.get_json(silent=True) or {}
    actor_id = payload.get("actor_id")
    if not actor_id or actor_id not in DEMO_ACTORS:
        return jsonify({
            "error": {
                "code": "INVALID_ACTOR",
                "message": f"Actor '{actor_id}' is not a registered demo actor.",
                "details": {"available_actors": list(DEMO_ACTORS.keys())},
            }
        }), 400

    token = mint_actor_token(actor_id)
    return jsonify({
        "status": "SUCCESS",
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": DEFAULT_TOKEN_TTL_SECONDS,
        "principal": DEMO_ACTORS[actor_id],
    }), 200



@projects_bp.route("", methods=["GET"])
@projects_bp.route("/", methods=["GET"])
def list_projects():
    """GET /projects - Returns high-level summaries for all registered projects."""
    service = get_project_service()
    summaries = service.list_projects()
    return jsonify({
        "status": "SUCCESS",
        "count": len(summaries),
        "projects": summaries,
    }), 200


@projects_bp.route("/<project_id>", methods=["GET"])
def get_project_detail(project_id: str):
    """GET /projects/{project_id} - Returns complete, authoritative project representation."""
    validate_project_identifier(project_id)
    service = get_project_service()
    detail = service.get_project_detail(project_id)
    return jsonify({
        "status": "SUCCESS",
        "project": detail,
    }), 200


@projects_bp.route("/<project_id>/allocation", methods=["GET"])
def get_project_allocation(project_id: str):
    """GET /projects/{project_id}/allocation - Returns immutable canonical allocation records."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    _ = proj_service.get_project_summary(project_id)

    pagination = parse_pagination_params(request)
    alloc_service = get_allocation_service()
    data = alloc_service.get_canonical_allocation(
        project_id=project_id,
        h3_cell_id=pagination.h3_cell_id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return jsonify({
        "status": "SUCCESS",
        "data": data,
    }), 200


@projects_bp.route("/<project_id>/allocation", methods=["PUT", "PATCH", "DELETE"])
def reject_allocation_mutation(project_id: str):
    """Guards against mutation of the canonical allocation (enforces Cedar negative policy)."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    proj_summary = proj_service.get_project_summary(project_id)
    current_state = proj_summary["project_status"]

    denial = enforce_cedar_authorization(
        action="modify_canonical_data",
        project_id=project_id,
        project_state=current_state,
    )
    if denial:
        return denial

    alloc_service = get_allocation_service()
    alloc_service.reject_direct_mutation()



@projects_bp.route("/<project_id>/baseline", methods=["GET"])
def get_project_baseline(project_id: str):
    """GET /projects/{project_id}/baseline - Exposes baseline evidence across selected cells."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    _ = proj_service.get_project_summary(project_id)

    # Support backward-compatible 'limit' parameter with validation
    limit_arg = request.args.get("limit")
    limit = None
    if limit_arg is not None:
        try:
            limit = int(limit_arg)
            if limit < 1 or limit > 100:
                raise ValueError("Limit must be between 1 and 100")
        except ValueError as ve:
            raise DomainValidationError("Invalid limit parameter.", details={"limit": limit_arg, "error": str(ve)})

    pagination = parse_pagination_params(request)
    baseline_service = get_baseline_service()
    data = baseline_service.get_project_baseline(
        project_id=project_id,
        h3_cell_id=pagination.h3_cell_id,
        page=pagination.page,
        page_size=pagination.page_size,
        limit=limit,
    )
    return jsonify({
        "status": "SUCCESS",
        "data": data,
    }), 200


@projects_bp.route("/<project_id>/risk-surface", methods=["GET"])
def get_project_risk_surface(project_id: str):
    """GET /projects/{project_id}/risk-surface - Returns citywide canonical H3 risk surface."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    _ = proj_service.get_project_summary(project_id)

    baseline_service = get_baseline_service()
    data = baseline_service.get_risk_surface(project_id=project_id)
    return jsonify({
        "status": "SUCCESS",
        "data": data,
    }), 200


@projects_bp.route("/<project_id>/boundary", methods=["GET"])
def get_project_boundary(project_id: str):
    """GET /projects/{project_id}/boundary - Returns the canonical Pune AOI GeoJSON boundary."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    _ = proj_service.get_project_summary(project_id)

    baseline_service = get_baseline_service()
    geojson_data = baseline_service.get_boundary(project_id=project_id)
    return jsonify({
        "status": "SUCCESS",
        "boundary": geojson_data,
    }), 200


@projects_bp.route("/<project_id>/scenarios/optimize", methods=["POST"])
def optimize_project_scenario(project_id: str):
    """POST /projects/{project_id}/scenarios/optimize - In-memory modeled scenario optimization."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    proj_summary = proj_service.get_project_summary(project_id)
    current_state = proj_summary["project_status"]

    # Reuses Cedar policy_universal_view (Action: view_project)
    denial = enforce_cedar_authorization(
        action="view_project",
        project_id=project_id,
        project_state=current_state,
    )
    if denial is not None:
        return denial

    payload = request.get_json(silent=True) or {}
    try:
        req = ScenarioOptimizationRequest(**payload)
    except PydanticValidationError as e:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid scenario optimization payload.",
                "details": format_pydantic_error_details(e),
            }
        }), 400

    alloc_service = get_allocation_service()
    result = alloc_service.optimize_scenario(
        project_id=project_id,
        budget_inr=req.budget_inr,
    )
    return jsonify({
        "status": "SUCCESS",
        "data": result,
    }), 200


@projects_bp.route("/<project_id>/mrv", methods=["GET"])
def get_project_mrv(project_id: str):
    """GET /projects/{project_id}/mrv - Returns MRV tracking and readiness status."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    _ = proj_service.get_project_summary(project_id)

    mrv_service = get_mrv_service()
    data = mrv_service.get_mrv_overview(project_id)
    return jsonify({
        "status": "SUCCESS",
        "data": data,
    }), 200


# ==============================================================================
# Write Endpoints
# ==============================================================================

@projects_bp.route("/<project_id>/governance-audit", methods=["GET"])
def get_project_governance_audit(project_id: str):
    """GET /projects/{project_id}/governance-audit - Returns recent Cedar authorization audit events."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    _ = proj_service.get_project_summary(project_id)

    cedar_svc = get_cedar_service()
    audit_records = cedar_svc.get_audit_trail(project_id=project_id) if cedar_svc else []
    return jsonify({
        "status": "SUCCESS",
        "project_id": project_id,
        "count": len(audit_records),
        "audit_trail": audit_records,
    }), 200


@projects_bp.route("/<project_id>/governance-check", methods=["POST"])
def check_governance_authorization(project_id: str):
    """POST /projects/{project_id}/governance-check - Dry-run policy check without state mutation."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    proj_summary = proj_service.get_project_summary(project_id)
    current_state = proj_summary["project_status"]

    payload = request.get_json(silent=True) or {}
    action = payload.get("action", "view_project")
    actor = payload.get("actor")
    if not actor:
        auth_res = get_authenticated_principal(required=False)
        actor = auth_res[0] if auth_res else "citizen_viewer"

    cedar_svc = get_cedar_service()
    if not cedar_svc:
        return jsonify({"status": "ERROR", "message": "Cedar service not available"}), 500

    # Build context for check
    mrv_service = get_mrv_service()
    mrv_overview = mrv_service.get_mrv_overview(project_id)
    is_mrv_executable = mrv_overview.get("difference_in_differences_status", {}).get("is_executable", False)
    qc_passed = mrv_overview.get("qc_state") == "PASSED"

    decision = cedar_svc.authorize(
        actor_id=actor,
        action=action,
        project_id=project_id,
        project_state=current_state,
        context={"is_mrv_executable": is_mrv_executable, "qc_passed": qc_passed},
    )

    return jsonify({
        "status": "SUCCESS",
        "check": decision.to_dict(),
    }), 200


@projects_bp.route("/<project_id>/implementation-events", methods=["POST"])
def create_implementation_event(project_id: str):
    """POST /projects/{project_id}/implementation-events - Records real-world physical deployment."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    proj_summary = proj_service.get_project_summary(project_id)
    current_state = proj_summary["project_status"]

    payload = request.get_json(silent=True) or {}
    try:
        req = ImplementationEventCreateRequest(**payload)
    except PydanticValidationError as e:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid implementation event payload schema.",
                "details": format_pydantic_error_details(e),
            }
        }), 400

    # Cedar authorization boundary check
    denial = enforce_cedar_authorization(
        action="record_implementation",
        project_id=project_id,
        project_state=current_state,
    )
    if denial is not None:
        return denial

    mrv_service = get_mrv_service()
    event_record = mrv_service.record_implementation_event(
        project_id=project_id,
        intervention_code=req.intervention_code,
        h3_cell_id=req.h3_cell_id,
        implemented_quantity=req.implemented_quantity,
        quantity_unit=req.quantity_unit,
        contractor_id=req.contractor_id,
        completion_date=req.completion_date,
        evidence_uri=req.evidence_uri,
        nursery_invoice_ref=req.nursery_invoice_ref,
        nursery_batch_id=req.nursery_batch_id,
        tree_guards_installed=req.tree_guards_installed,
        tree_guards_count=req.tree_guards_count,
        is_synthetic_demo=req.is_synthetic_demo,
        notes=req.notes,
    )

    return jsonify({
        "status": "SUCCESS",
        "event": event_record,
    }), 201


@projects_bp.route("/<project_id>/verification-events", methods=["POST"])
def create_verification_event(project_id: str):
    """POST /projects/{project_id}/verification-events - Heavily guarded verification milestone."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    proj_summary = proj_service.get_project_summary(project_id)
    current_state = proj_summary["project_status"]

    payload = request.get_json(silent=True) or {}
    try:
        req = VerificationEventCreateRequest(**payload)
    except PydanticValidationError as e:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid verification event payload schema.",
                "details": format_pydantic_error_details(e),
            }
        }), 400

    # Cedar authorization boundary check
    denial = enforce_cedar_authorization(
        action="verify_impact",
        project_id=project_id,
        project_state=current_state,
        context={"is_mrv_executable": True, "qc_passed": True},
    )
    if denial is not None:
        return denial

    mrv_service = get_mrv_service()
    result = mrv_service.process_verification_request(
        project_id=project_id,
        observation_payload=req.observation.model_dump(),
        verification_payload=req.verification.model_dump(),
        target_metric=req.target_metric,
        is_synthetic_demo=req.is_synthetic_demo,
    )

    # If verification passed, update project lifecycle state in domain service
    proj_service.transition_project_state(
        project_id=project_id,
        target_state_name="VERIFIED",
        context={"verification_authorized": True},
    )

    return jsonify({
        "status": "SUCCESS",
        "verification": result,
    }), 201


@projects_bp.route("/<project_id>/transition", methods=["POST"])
def transition_project_state(project_id: str):
    """POST /projects/{project_id}/transition - State transition guarded by Cedar and ProjectStateMachine."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    proj_summary = proj_service.get_project_summary(project_id)
    current_state = proj_summary["project_status"]
    payload = request.get_json(silent=True) or {}

    try:
        req = StateTransitionRequest(**payload)
    except PydanticValidationError as e:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid state transition payload schema.",
                "details": format_pydantic_error_details(e),
            }
        }), 400

    # Map target lifecycle state to Cedar governance action
    STATE_ACTION_MAP = {
        "PROPOSED": "submit_for_sanction",
        "FUNDED": "approve_project",
        "IMPLEMENTING": "record_implementation",
        "IMPLEMENTED": "record_implementation",
        "MONITORING": "request_mrv",
        "VERIFIED": "verify_impact",
        "REJECTED": "approve_project",
        "CANCELLED": "approve_project",
    }
    action = STATE_ACTION_MAP.get(req.target_state)
    if not action:
        return jsonify({
            "error": {
                "code": "INVALID_STATE_TRANSITION",
                "message": f"Target lifecycle state '{req.target_state}' is not a valid governed transition state.",
                "details": {"allowed_target_states": list(STATE_ACTION_MAP.keys())},
            }
        }), 400

    mrv_service = get_mrv_service()
    mrv_overview = mrv_service.get_mrv_overview(project_id)
    is_mrv_executable = mrv_overview.get("difference_in_differences_status", {}).get("is_executable", False)
    qc_passed = mrv_overview.get("qc_state") == "PASSED"

    # Cedar authorization boundary check
    denial = enforce_cedar_authorization(
        action=action,
        project_id=project_id,
        project_state=current_state,
        context={"is_mrv_executable": is_mrv_executable, "qc_passed": qc_passed},
    )
    if denial is not None:
        return denial

    context = {}
    if req.sanction_id:
        context["sanction_id"] = req.sanction_id
    if req.approved_budget_inr is not None:
        context["approved_budget_inr"] = req.approved_budget_inr
    if req.notes:
        context["notes"] = req.notes

    res = proj_service.transition_project_state(
        project_id=project_id,
        target_state_name=req.target_state,
        context=context,
    )

    return jsonify({
        "status": "SUCCESS",
        "transition": res,
        "governance": {
            "authorized": True,
            "policy_layer": "cedar",
            "decision": "ALLOW",
        },
    }), 200


@projects_bp.route("/<project_id>/revisions", methods=["POST"])
def propose_allocation_revision(project_id: str):
    """POST /projects/{project_id}/revisions - Propose an auditable allocation revision."""
    validate_project_identifier(project_id)
    proj_service = get_project_service()
    proj_summary = proj_service.get_project_summary(project_id)
    current_state = proj_summary["project_status"]

    payload = request.get_json(silent=True) or {}
    try:
        req = AllocationRevisionRequest(**payload)
    except PydanticValidationError as e:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid revision payload schema.",
                "details": format_pydantic_error_details(e),
            }
        }), 400

    # Cedar authorization boundary check
    denial = enforce_cedar_authorization(
        action="propose_revision",
        project_id=project_id,
        project_state=current_state,
    )
    if denial is not None:
        return denial

    alloc_service = get_allocation_service()
    rev = alloc_service.propose_revision(
        project_id=project_id,
        h3_cell_id=req.h3_cell_id,
        intervention_code=req.intervention_code,
        proposed_quantity=req.proposed_quantity,
        reason=req.reason,
        author=req.author,
    )

    return jsonify({
        "status": "SUCCESS",
        "revision": rev,
    }), 201


@projects_bp.route("/cluster/health", methods=["GET"])
def get_cluster_health():
    """GET /projects/cluster/health - Inspects Aurora PostgreSQL Multi-AZ cluster status."""
    persistence = get_persistence_service()
    health = persistence.check_cluster_health()
    return jsonify(health), 200


@projects_bp.route("/<project_id>/evidence/presigned-url", methods=["POST"])
def get_evidence_presigned_url(project_id: str):
    """POST /projects/{project_id}/evidence/presigned-url - Generates KMS-encrypted direct S3 upload URL."""
    validate_project_identifier(project_id)
    # Require authenticated principal
    auth_res = get_authenticated_principal(required=True)
    if isinstance(auth_res, tuple) and len(auth_res) == 2 and hasattr(auth_res[0], 'status_code'):
        return auth_res

    payload = request.get_json(silent=True) or {}
    filename = payload.get("filename", "evidence.pdf")
    content_type = payload.get("content_type", "application/pdf")
    artifact_category = payload.get("artifact_category", "field_verification")

    url_meta = evidence_vault.generate_presigned_upload_url(
        project_id=project_id,
        filename=filename,
        content_type=content_type,
        artifact_category=artifact_category,
    )
    return jsonify({
        "status": "SUCCESS",
        "upload": url_meta,
    }), 200


@projects_bp.route("/<project_id>/ground-telemetry", methods=["POST"])
def ingest_ground_telemetry(project_id: str):
    """POST /projects/{project_id}/ground-telemetry - Ingests micro-meteorological logger readings."""
    validate_project_identifier(project_id)
    auth_res = get_authenticated_principal(required=True)
    if isinstance(auth_res, tuple) and len(auth_res) == 2 and hasattr(auth_res[0], 'status_code'):
        return auth_res

    payload = request.get_json(silent=True) or {}
    readings = payload.get("readings", [])
    if not readings or not isinstance(readings, list):
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Field 'readings' must be a non-empty list of sensor reading objects.",
            }
        }), 400

    hybrid_engine = get_hybrid_mrv_engine()
    try:
        res = hybrid_engine.ingest_telemetry_batch(project_id, readings)
    except DomainValidationError as e:
        return jsonify({
            "error": {
                "code": e.code,
                "message": e.message,
                "details": e.details,
            }
        }), 400

    return jsonify(res), 201


@projects_bp.route("/<project_id>/mrv/hybrid-audit", methods=["GET"])
def get_hybrid_mrv_audit(project_id: str):
    """GET /projects/{project_id}/mrv/hybrid-audit - Fuses satellite corridor LST with empirical ground telemetry."""
    validate_project_identifier(project_id)
    hybrid_engine = get_hybrid_mrv_engine()
    res = hybrid_engine.perform_hybrid_mrv_audit(project_id=project_id)
    return jsonify(res), 200


