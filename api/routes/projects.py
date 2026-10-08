"""CLIMORA Projects API Routes.

Handles HTTP routing, request parsing, serialization, and status codes.
Enforces the boundary: route handlers do NOT perform scientific calculations.
All domain actions are delegated to Domain Services and ZonalQueryEngine.
Hardened with input validation, deterministic pagination, and response bounds.
"""

from __future__ import annotations

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
from services.exceptions import (
    AllocationImmutableError,
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

def resolve_request_actor() -> Optional[str]:
    """Extracts actor identifier from header or query param, handling testing mode."""
    actor = request.headers.get("X-Climora-Actor")
    if not actor:
        actor = request.args.get("actor")
    if actor:
        return actor.strip()
    # In test mode without actor header, preserve backwards compatibility with Phase 2A tests
    if current_app.config.get("TESTING"):
        return None
    # In production, default to canonical municipal commissioner demo actor
    return "pmc_commissioner"

def enforce_cedar_authorization(
    action: str,
    project_id: str,
    project_state: str,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Any]:
    """Evaluates Cedar policy authorization.
    
    If denied:
        Returns a Flask 403 Response tuple with the structured denial contract.
    If allowed or in test-bypass:
        Returns None (caller proceeds with domain execution).
    """
    cedar_svc = get_cedar_service()
    if cedar_svc is None:
        return None

    actor_id = resolve_request_actor()
    if actor_id is None:
        return None

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
    actor = payload.get("actor") or resolve_request_actor() or "citizen_viewer"

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

    mrv_service = get_mrv_service()
    mrv_overview = mrv_service.get_mrv_overview(project_id)
    is_mrv_executable = mrv_overview.get("difference_in_differences_status", {}).get("is_executable", False)
    qc_passed = mrv_overview.get("qc_state") == "PASSED"

    # Cedar authorization boundary check
    denial = enforce_cedar_authorization(
        action="verify_impact",
        project_id=project_id,
        project_state=current_state,
        context={"is_mrv_executable": is_mrv_executable, "qc_passed": qc_passed},
    )
    if denial is not None:
        return denial

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
    action = STATE_ACTION_MAP.get(req.target_state, "propose_revision")

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

