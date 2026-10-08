"""CLIMORA Cedar Governance & Policy Enforcement Service.

Enforces fine-grained, state-aware authorization for environmental project lifecycle actions
using Amazon Cedar (via cedarpy).

Architectural Principles:
- IAM: AWS cloud infrastructure security.
- Cedar: CLIMORA application governance authorization.
- State Machine: Project lifecycle transitions and scientific prerequisites.
- S3: Immutable canonical scientific data lake.

Zero client-side role trust: All requests are evaluated through server-side Cedar policies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional, Tuple

import cedarpy
from cedarpy import Decision, is_authorized

from ingestion.common import get_logger

logger = get_logger()

# ==============================================================================
# Canonical Cedar Policy Set
# ==============================================================================

CEDAR_POLICY_SET = """
// Policy 1: Universal Read Access
// Any actor (Viewer, Citizen, Officer, Contractor, Verifier) may inspect project evidence.
@id("policy_universal_view")
permit(
    principal,
    action == Action::"view_project",
    resource
);

// Policy 2: Project Planning & Proposal Revisions
// Project Managers can propose cell allocation revisions, request MRV baselines, and submit proposals.
@id("policy_pm_propose_revision")
permit(
    principal in Role::"project_manager",
    action in [
        Action::"propose_revision",
        Action::"submit_for_sanction",
        Action::"request_mrv"
    ],
    resource
);

// Policy 3: Municipal Sanction Governance
// Only Municipal Officers may approve/sanction projects, and strictly when the project is in PROPOSED state.
@id("policy_officer_approve_project")
permit(
    principal in Role::"municipal_officer",
    action == Action::"approve_project",
    resource
)
when {
    resource.state == "PROPOSED"
};

// Policy 4: Field Contractor Physical Implementation
// Contractors can record physical deployment events, strictly when the project is FUNDED or IMPLEMENTING.
@id("policy_contractor_record_impl")
permit(
    principal in Role::"field_contractor",
    action == Action::"record_implementation",
    resource
)
when {
    resource.state == "FUNDED" || resource.state == "IMPLEMENTING"
};

// Policy 5: MRV Operations & Baseline Monitoring
@id("policy_mrv_request")
permit(
    principal in Role::"mrv_verifier",
    action == Action::"request_mrv",
    resource
);

// Policy 6: Independent MRV Verification Certification
// Accredited MRV Verifiers may certify verification events only when the project is in MONITORING state,
// the MRV scientific gate is executable, and 100% of QC checks have passed.
@id("policy_mrv_verify_impact")
permit(
    principal in Role::"mrv_verifier",
    action == Action::"verify_impact",
    resource
)
when {
    resource.state == "MONITORING" &&
    resource.is_mrv_executable == true &&
    resource.qc_passed == true
};

// Policy 7: Architectural Immutability Guardrail (Explicit Negative Policy)
// Absolute forbid: No principal, regardless of role or state, may mutate canonical scientific baselines.
@id("policy_forbid_canonical_mutation")
forbid(
    principal,
    action in [
        Action::"modify_canonical_data",
        Action::"modify_observed_data",
        Action::"modify_derived_data",
        Action::"modify_modeled_result",
        Action::"rewrite_optimization",
        Action::"mark_modeled_as_verified"
    ],
    resource
);
"""

POLICY_INDEX_MAP = {
    "policy0": "policy_universal_view",
    "policy1": "policy_pm_propose_revision",
    "policy2": "policy_officer_approve_project",
    "policy3": "policy_contractor_record_impl",
    "policy4": "policy_mrv_request",
    "policy5": "policy_mrv_verify_impact",
    "policy6": "policy_forbid_canonical_mutation",
}


# ==============================================================================
# Demo Actor Personas Registry
# ==============================================================================

DEMO_ACTORS: Dict[str, Dict[str, Any]] = {
    "pmc_commissioner": {
        "actor_id": "pmc_commissioner",
        "name": "Dr. Rajesh Patil",
        "role": "municipal_officer",
        "title": "Municipal Commissioner",
        "organization": "Pune Municipal Corporation (PMC)",
        "description": "Authorized municipal signatory for capital budget sanctions and official tenders.",
    },
    "urban_planner_lead": {
        "actor_id": "urban_planner_lead",
        "name": "Pooja Deshmukh",
        "role": "project_manager",
        "title": "Lead Urban Climate Planner",
        "organization": "PMC Environment & Garden Dept",
        "description": "Manages tree canopy interventions, spatial allocations, and stakeholder proposals.",
    },
    "sharma_contractors": {
        "actor_id": "sharma_contractors",
        "name": "Sharma Agro & Forestry Ltd",
        "role": "field_contractor",
        "title": "Licensed EPC Planting Contractor",
        "organization": "PMC Vendor Registry #4402",
        "description": "Responsible for ground sapling procurement, roadside digging, and batch deployment.",
    },
    "sgs_environmental_auditor": {
        "actor_id": "sgs_environmental_auditor",
        "name": "SGS Environmental Auditing",
        "role": "mrv_verifier",
        "title": "Accredited GHG/MRV Verifier",
        "organization": "ISO 14064-2 Certified Independent Auditor",
        "description": "Performs post-monsoon satellite observation checks and difference-in-differences audits.",
    },
    "citizen_viewer": {
        "actor_id": "citizen_viewer",
        "name": "Ananya Joshi",
        "role": "viewer",
        "title": "Public Observer / Resident",
        "organization": "Pune Civic Climate Forum",
        "description": "Citizen auditor inspecting open municipal climate allocations and expenditure transparency.",
    },
}

DEFAULT_DEMO_ACTOR = "pmc_commissioner"


# ==============================================================================
# Decision & Audit Data Models
# ==============================================================================

@dataclass
class CedarAuthorizationDecision:
    """Structured decision returned by the Cedar governance authorization engine."""
    allowed: bool
    decision: str  # "ALLOW" or "DENY"
    actor_id: str
    actor_name: str
    role: str
    action: str
    project_id: str
    project_state: str
    policy_id: Optional[str]
    reason_summary: str
    audit_id: str
    timestamp_utc: str
    correlation_id: Optional[str] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


ROLE_TO_ACTOR_MAP: Dict[str, str] = {
    "municipal_officer": "pmc_commissioner",
    "project_manager": "urban_planner_lead",
    "field_contractor": "sharma_contractors",
    "mrv_verifier": "sgs_environmental_auditor",
    "viewer": "citizen_viewer",
}


# ==============================================================================
# Cedar Governance Service Implementation
# ==============================================================================

class CedarGovernanceService:
    """Centralized authorization boundary executing Cedar policy evaluation."""

    def __init__(self, policy_set_text: str = CEDAR_POLICY_SET):
        self.policy_set_text = policy_set_text
        self._audit_log: List[Dict[str, Any]] = []

    def get_registered_actors(self) -> List[Dict[str, Any]]:
        """Returns metadata for all available demo actor personas."""
        return list(DEMO_ACTORS.values())

    def resolve_actor(self, actor_header_or_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Resolves an actor ID to a known persona, defaulting safely if unspecified."""
        if not actor_header_or_id:
            actor_id = DEFAULT_DEMO_ACTOR
        else:
            actor_id = str(actor_header_or_id).strip().lower()

        # Map role alias directly to canonical actor persona
        if actor_id in ROLE_TO_ACTOR_MAP:
            actor_id = ROLE_TO_ACTOR_MAP[actor_id]

        if actor_id in DEMO_ACTORS:
            return actor_id, DEMO_ACTORS[actor_id]

        # Handle unknown actors as anonymous viewers for least-privilege safety
        anonymous = {
            "actor_id": actor_id,
            "name": f"Unregistered Actor ({actor_id})",
            "role": "viewer",
            "title": "External Observer",
            "organization": "Unknown",
            "description": "Default untrusted principal with view-only privileges.",
        }
        return actor_id, anonymous

    def _build_entities(
        self,
        actor_id: str,
        role: str,
        project_id: str,
        project_state: str,
        is_mrv_executable: bool = False,
        qc_passed: bool = False,
    ) -> List[Dict[str, Any]]:
        """Constructs Cedar entity hierarchy connecting Actor -> Role and Project attributes."""
        entities = [
            # Role Entity
            {
                "uid": {"type": "Role", "id": role},
                "attrs": {},
                "parents": [],
            },
            # Actor Entity
            {
                "uid": {"type": "Actor", "id": actor_id},
                "attrs": {
                    "role_name": role,
                },
                "parents": [
                    {"type": "Role", "id": role}
                ],
            },
            # Project Entity
            {
                "uid": {"type": "Project", "id": project_id},
                "attrs": {
                    "state": project_state,
                    "is_mrv_executable": bool(is_mrv_executable),
                    "qc_passed": bool(qc_passed),
                    "study_area": "Pune Municipal Corporation",
                },
                "parents": [],
            },
        ]
        return entities

    def authorize(
        self,
        actor_id: str,
        action: str,
        project_id: str,
        project_state: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> CedarAuthorizationDecision:
        """Evaluates an authorization request against the Cedar policy set.

        Returns a structured decision with deterministic explanation and audit trail.
        """
        ctx = dict(context or {})
        clean_actor_id, actor_meta = self.resolve_actor(actor_id)
        role = actor_meta["role"]

        is_mrv_executable = ctx.get("is_mrv_executable", False)
        qc_passed = ctx.get("qc_passed", False)

        entities = self._build_entities(
            actor_id=clean_actor_id,
            role=role,
            project_id=project_id,
            project_state=project_state,
            is_mrv_executable=is_mrv_executable,
            qc_passed=qc_passed,
        )

        request_payload = {
            "principal": f'Actor::"{clean_actor_id}"',
            "action": f'Action::"{action}"',
            "resource": f'Project::"{project_id}"',
            "context": {},
        }

        authz_result = is_authorized(request_payload, self.policy_set_text, entities)
        is_allow = authz_result.decision == Decision.Allow

        # Extract matching policies or reasons
        reasons = list(authz_result.diagnostics.reasons if authz_result.diagnostics else [])
        raw_policy_id = reasons[0] if reasons else None
        policy_id = POLICY_INDEX_MAP.get(raw_policy_id, raw_policy_id) if raw_policy_id else None

        # Build human-readable explainability summary
        reason_summary = self._generate_explanation(
            is_allow=is_allow,
            actor_name=actor_meta["name"],
            role=role,
            action=action,
            project_state=project_state,
            is_mrv_executable=is_mrv_executable,
            qc_passed=qc_passed,
            policy_id=policy_id,
        )

        audit_id = f"AUDIT-CEDAR-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()

        decision = CedarAuthorizationDecision(
            allowed=is_allow,
            decision="ALLOW" if is_allow else "DENY",
            actor_id=clean_actor_id,
            actor_name=actor_meta["name"],
            role=role,
            action=action,
            project_id=project_id,
            project_state=project_state,
            policy_id=policy_id,
            reason_summary=reason_summary,
            audit_id=audit_id,
            timestamp_utc=timestamp,
            correlation_id=correlation_id,
            diagnostics={
                "cedar_decision": str(authz_result.decision),
                "reasons": reasons,
                "errors": list(authz_result.diagnostics.errors if authz_result.diagnostics else []),
            },
        )

        # Record in process-local audit trail
        self._record_audit(decision)

        logger.info(
            f"[CEDAR GOVERNANCE] decision={decision.decision} actor={decision.actor_id} "
            f"role={decision.role} action={decision.action} project={decision.project_id} "
            f"state={decision.project_state} policy={decision.policy_id} audit_id={decision.audit_id}"
        )

        return decision

    def _generate_explanation(
        self,
        is_allow: bool,
        actor_name: str,
        role: str,
        action: str,
        project_state: str,
        is_mrv_executable: bool,
        qc_passed: bool,
        policy_id: Optional[str],
    ) -> str:
        """Produces clear, auditable explanations for allow and deny decisions."""
        if action in [
            "modify_canonical_data",
            "modify_observed_data",
            "modify_derived_data",
            "modify_modeled_result",
            "rewrite_optimization",
            "mark_modeled_as_verified",
        ]:
            return (
                "FORBIDDEN: Immutable Scientific Truth Policy explicitly denies direct manipulation of "
                "canonical features, matrices, or mathematical solver results."
            )

        if is_allow:
            if action == "view_project":
                return f"Access granted under policy '{policy_id}': Project evidence is public and verifiable."
            if action == "approve_project":
                return (
                    f"Access granted under policy '{policy_id}': Municipal Officer '{actor_name}' is authorized "
                    f"to sanction projects currently in 'PROPOSED' state."
                )
            if action == "propose_revision":
                return (
                    f"Access granted under policy '{policy_id}': Project Manager '{actor_name}' is authorized "
                    "to propose auditable allocation revisions without mutating canonical baselines."
                )
            if action == "record_implementation":
                return (
                    f"Access granted under policy '{policy_id}': Field Contractor '{actor_name}' is authorized "
                    f"to record deployment progress for project in '{project_state}' state."
                )
            if action == "verify_impact":
                return (
                    f"Access granted under policy '{policy_id}': Accredited MRV Verifier '{actor_name}' authorized "
                    "following verified post-intervention observation and 100% passing QC audit."
                )
            return f"Authorization granted under policy '{policy_id}'."

        # Denial explanations
        if action == "approve_project":
            if role != "municipal_officer":
                return (
                    f"DENIED by Cedar Policy: Principal in role '{role}' lacks statutory authority to sanction "
                    "capital expenditure. Requires 'municipal_officer' role."
                )
            if project_state != "PROPOSED":
                return (
                    f"DENIED by Cedar Policy: Project state is '{project_state}'. Sanctions are only permitted "
                    "for projects in 'PROPOSED' state."
                )

        if action == "record_implementation":
            if role != "field_contractor":
                return (
                    f"DENIED by Cedar Policy: Principal in role '{role}' is not authorized to log contractor "
                    "implementation events. Requires 'field_contractor' role."
                )
            if project_state not in ["FUNDED", "IMPLEMENTING"]:
                return (
                    f"DENIED by Cedar Policy: Cannot record physical deployment because project is in '{project_state}' state. "
                    "Contractor deployment requires 'FUNDED' or 'IMPLEMENTING' state."
                )

        if action == "verify_impact":
            if role != "mrv_verifier":
                return (
                    f"DENIED by Cedar Policy: Principal in role '{role}' is not accredited to certify MRV impacts. "
                    "Requires 'mrv_verifier' role."
                )
            if project_state != "MONITORING":
                return (
                    f"DENIED by Cedar Policy: Cannot certify verification because project is in '{project_state}' state. "
                    "MRV certification requires 'MONITORING' state."
                )
            if not is_mrv_executable or not qc_passed:
                return (
                    "DENIED by Cedar Policy: Scientific MRV gating criteria unmet (is_executable=False or qc_passed=False). "
                    "Cedar authorization requires prior completion of empirical observation and passing QC audit."
                )

        if action in ["propose_revision", "submit_for_sanction"]:
            if role not in ["project_manager", "municipal_officer"]:
                return (
                    f"DENIED by Cedar Policy: Principal in role '{role}' cannot propose allocation revisions. "
                    "Requires 'project_manager' role."
                )

        return f"DENIED by Cedar Policy: Default deny. No permit policy authorized role '{role}' for action '{action}' on resource state '{project_state}'."

    def _record_audit(self, decision: CedarAuthorizationDecision) -> None:
        """Appends decision record to the internal in-memory audit log."""
        self._audit_log.insert(0, decision.to_dict())
        # Keep recent 200 records to prevent unbounded memory growth
        if len(self._audit_log) > 200:
            self._audit_log = self._audit_log[:200]

    def get_audit_trail(self, project_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns chronological list of recent Cedar authorization decisions."""
        records = self._audit_log
        if project_id:
            records = [r for r in records if r.get("project_id") == project_id]
        return records[:limit]
