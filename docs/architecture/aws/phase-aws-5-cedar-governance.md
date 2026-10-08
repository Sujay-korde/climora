# Phase AWS-5: Amazon Cedar Governance & Policy Enforcement

## 1. Executive Summary & Motivation

CLIMORA operates as a high-integrity scientific decision-support system that processes Earth Observation data (Landsat 8/9, Sentinel-2), spatial topology (Uber H3 Res-9 DGGS), and mixed-integer linear programming (HiGHS MILP) to discover and formulate urban heat island mitigation projects for Pune Municipal Corporation (PMC).

However, **climate science alone does not execute municipal interventions**. An optimal spatial allocation remains an academic exercise unless it is translated into a **governed environmental project**. In municipal governance, financial sanction, field deployment, and carbon/thermal accounting:
1. **Who** can approve a ₹10,000,000 public capital expenditure? (Only a statutory Municipal Officer, not an urban planner or a citizen).
2. **Who** can submit contractor implementation records and sapling batch logs? (Only a bonded Field Contractor).
3. **Who** can verify thermal impact? (Only an accredited, independent MRV Verifier).
4. **Who** can alter canonical scientific formulations, raw satellite rasters, or MILP allocations? (**NO ONE**—not even the Municipal Commissioner).

In **Phase AWS-5**, CLIMORA introduces **Amazon Cedar** as an explicit, mathematical authorization layer separating **application governance authorization** from **AWS cloud infrastructure IAM** and **scientific truth validation**.

---

## 2. Core Architectural Principles & Separation of Concerns

CLIMORA establishes five decoupled layers:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. AWS IAM: Infrastructure Authorization (ECS, ECR, S3 bucket policy) │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Amazon Cedar: CLIMORA Application Policy & Role-Based Governance   │
├────────────────────────────────────────────────────────────────────────┤
│ 3. State Machine: Project Lifecycle Correctness (FSM Guards)           │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Scientific Engine: Mathematical & Thermodynamic Invariants (F-24-26)│
├────────────────────────────────────────────────────────────────────────┤
│ 5. Amazon S3 Data Lake: Canonical Immutable Scientific Ground Truth   │
└────────────────────────────────────────────────────────────────────────┘
```

### Authorization Flow

```text
                              API HTTP Request
                                     │
                                     ▼
                      Resolve Actor & Headers
                      (X-Climora-Actor / Server Persona)
                                     │
                                     ▼
                        Cedar Policy Authorization
                        cedarpy.is_authorized(
                            principal, action, resource, context
                        )
                                     │
                        ┌────────────┴────────────┐
                        │                         │
                     ALLOW                      DENY
                        │                         │
                        ▼                         ▼
             Domain State-Machine        Return HTTP 403 Forbidden
             Validation (FSM Guards)     Structured Cedar Diagnostic
                        │                ZERO STATE MUTATION
                 ┌──────┴──────┐
                 │             │
               VALID        INVALID
                 │             │
                 ▼             ▼
              Execute     Return HTTP 400
              Mutation    Domain FSM Error
                 │
                 ▼
         Audit Record & Response
```

**Rule of Dual Validation:** Both Cedar authorization and application domain validation must succeed. A Cedar `ALLOW` cannot bypass an invalid state machine transition, and a valid state machine transition cannot execute if Cedar outputs `DENY`.

---

## 3. Cedar Policy Domain Specification

### 3.1 Entities

* **`Principal`**: `Actor::"<actor_id>"`
  * Attributes: `role: String`, `name: String`, `organization: String`
* **`Resource`**: `Project::"<project_id>"`
  * Attributes:
    * `state: String` (`"PROPOSED"`, `"FUNDED"`, `"IMPLEMENTING"`, `"MONITORING"`, `"VERIFIED"`)
    * `budget_inr: Long`
    * `is_mrv_executable: Bool`
    * `qc_passed: Bool`

### 3.2 Actions

1. `view_project` — Read project details, spatial polygons, allocations, and baseline reference data.
2. `propose_revision` — Propose administrative amendments or budget re-allocations.
3. `submit_for_sanction` — Submit project proposal to municipal treasury.
4. `approve_project` — Grant statutory financial sanction and move project to `FUNDED`.
5. `record_implementation` — Submit field contractor logs, batch receipts, and planting coordinates.
6. `request_mrv` — Initiate baseline vs. post-monsoon difference-in-differences analysis.
7. `verify_impact` — Certify empirical temperature reduction and sign off MRV audit.
8. `modify_canonical_data` — Attempted direct mutation of scientific matrices or solver allocations (Subject to Negative Policy).

---

## 4. Policy Implementation

The Cedar policy store is codified as follows:

```cedar
// 1. Universal Read-Only Access
@id("policy_universal_view")
permit(
    principal,
    action == Action::"view_project",
    resource
);

// 2. Project Manager Lifecycle Actions
@id("policy_pm_propose_revision")
permit(
    principal,
    action in [Action::"propose_revision", Action::"submit_for_sanction", Action::"request_mrv"],
    resource
)
when {
    principal.role == "project_manager"
};

// 3. Municipal Officer Statutory Sanction Authority
@id("policy_officer_approve_project")
permit(
    principal,
    action == Action::"approve_project",
    resource
)
when {
    principal.role == "municipal_officer" &&
    resource.state == "PROPOSED"
};

// 4. Field Contractor Implementation Records
@id("policy_contractor_record_impl")
permit(
    principal,
    action == Action::"record_implementation",
    resource
)
when {
    principal.role == "field_contractor" &&
    (resource.state == "FUNDED" || resource.state == "IMPLEMENTING")
};

// 5. MRV Verifier Analysis Request
@id("policy_mrv_request")
permit(
    principal,
    action == Action::"request_mrv",
    resource
)
when {
    principal.role == "mrv_verifier"
};

// 6. MRV Verifier Certification Gate
@id("policy_mrv_verify_impact")
permit(
    principal,
    action == Action::"verify_impact",
    resource
)
when {
    principal.role == "mrv_verifier" &&
    resource.state == "MONITORING" &&
    resource.is_mrv_executable == true &&
    resource.qc_passed == true
};

// 7. Critical Negative Policy: Immutable Scientific Ground Truth
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
```

---

## 5. Critical Negative Policy & Scientific Immutability

CLIMORA enforces that **no actor—regardless of rank, role, or credentials—may modify canonical scientific truth**.

Even if an authenticated Municipal Commissioner issues a `PUT /projects/<id>/allocation`, Cedar evaluates the action against `@id("policy_forbid_canonical_mutation")` and immediately produces `Decision.Deny`.

This guarantees:
* Observed Landsat surface temperature cannot be smoothed or altered.
* HiGHS MILP optimization allocations cannot be arbitrarily increased or decreased.
* `MODELED` data can never be directly renamed to `VERIFIED` via an administrative API call.

---

## 6. Server-Side Demo Actor Model (Zero Frontend Trust)

To satisfy hackathon evaluation requirements without forcing judges through a complex identity onboarding flow (e.g. AWS Cognito user pool verification), CLIMORA implements a **deterministic server-side persona directory**:

| Persona Key | Name | Organization | Role | Allowed Core Actions |
| :--- | :--- | :--- | :--- | :--- |
| `pmc_commissioner` | Dr. Rajesh Patil | Pune Municipal Corporation (PMC) | `municipal_officer` | `view_project`, `approve_project` |
| `urban_planner_lead` | Pooja Deshmukh | PMC Environment & Garden Dept | `project_manager` | `view_project`, `propose_revision`, `submit_for_sanction` |
| `sharma_contractors` | Sharma Agro & Forestry Ltd | PMC Vendor Registry #4402 | `field_contractor` | `view_project`, `record_implementation` |
| `sgs_environmental_auditor` | SGS Environmental Auditing | ISO 14064-2 Accredited Auditor | `mrv_verifier` | `view_project`, `request_mrv`, `verify_impact` |
| `citizen_viewer` | Ananya Joshi | Pune Civic Climate Forum | `viewer` | `view_project` |

The frontend passes the persona key via the `X-Climora-Actor` header. The backend resolves the trusted server-side persona dictionary. If an unrecognized or untrusted identity is passed, it defaults to `citizen_viewer` (least privilege), preventing client-side privilege escalation.

---

## 7. Structured Explainability & Denial Semantics

When Cedar evaluates an action, the API returns a structured diagnostic:

```json
{
  "action": "approve_project",
  "authorized": false,
  "decision": "DENY",
  "error": {
    "code": "GOVERNANCE_AUTHORIZATION_DENIED",
    "details": {
      "action": "approve_project",
      "actor_id": "citizen_viewer",
      "audit_id": "AUDIT-CEDAR-42BCD7AF",
      "authorized": false,
      "decision": "DENY",
      "policy_id": null,
      "policy_layer": "cedar",
      "project_state": "PROPOSED",
      "reason": "DENIED by Cedar Policy: Principal in role 'viewer' lacks statutory authority to sanction capital expenditure. Requires 'municipal_officer' role.",
      "role": "viewer",
      "timestamp_utc": "2026-10-05T18:03:06.707770+00:00"
    },
    "message": "DENIED by Cedar Policy: Principal in role 'viewer' lacks statutory authority to sanction capital expenditure. Requires 'municipal_officer' role."
  },
  "policy_layer": "cedar",
  "project_state": "PROPOSED",
  "reason": "DENIED by Cedar Policy: Principal in role 'viewer' lacks statutory authority to sanction capital expenditure. Requires 'municipal_officer' role."
}
```

### Zero Mutation Guarantee

A denied Cedar evaluation occurs **before** any database, file, or in-memory state transition logic runs. Project lifecycle state, budget amounts, and verification statuses remain strictly unmodified.

---

## 8. Verification & Test Evidence

### 8.1 Backend Test Suite

* File: `tests/test_cedar_governance.py` (12 dedicated Cedar governance tests)
* Test Suite Execution:
  ```text
  172 passed, 2 warnings in 191.13s (0:03:11)
  ```
  *(160 legacy scientific and API tests + 12 Cedar governance tests, 100% pass rate)*

Tested scenarios include:
1. Scenario A — `citizen_viewer` view project: `ALLOW` under `policy_universal_view`.
2. Scenario B — `citizen_viewer` sanction approval: `DENY` with statutory explanation.
3. Scenario C — `urban_planner_lead` propose revision: `ALLOW` under `policy_pm_propose_revision`.
4. Scenario D — `sharma_contractors` sanction approval: `DENY`.
5. Scenario E — `sharma_contractors` record implementation when funded: `ALLOW` under `policy_contractor_record_impl`.
6. Scenario F — `sgs_environmental_auditor` verify impact on unmonitored project: `DENY` (MRV gate separation).
7. Scenario G — Negative policy: `modify_canonical_data` denied for all principals.
8. Zero Mutation Verification: Project state remains `PROPOSED` after denied approval.
9. Dry-run Governance Check API (`POST /projects/<id>/governance-check`).
10. In-memory Decision Audit Trail API (`GET /projects/<id>/governance-audit`).
11. Governance Actor Directory API (`GET /projects/governance/actors`).
12. Role alias resolution and least-privilege fallback.

### 8.2 Frontend Test Suite

* File: `frontend/src/tests/cedarGovernance.test.tsx` (2 dedicated tests)
* Test Suite Execution:
  ```text
  Test Files  2 passed (2)
       Tests  15 passed (15)
  ```

### 8.3 Production ECS & Amplify Live Verification

* **ECS Fargate Production API**:
  * Health Endpoint: `https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws/health` (HTTP 200 OK)
  * Actor Directory: `https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws/projects/governance/actors` (HTTP 200 OK, 5 personas)
  * Live Negative Policy Rejection: `PUT /projects/PROJ-PUNE-2025-BA225D6A/allocation` -> HTTP 403 Forbidden under `policy_forbid_canonical_mutation`.
  * Live Audit Trail: `GET /projects/PROJ-PUNE-2025-BA225D6A/governance-audit` (HTTP 200 OK, returns real-time evaluations).
* **AWS Amplify Hosting**:
  * Live URL: `https://main.dipd0dx7w10zl.amplifyapp.com/projects/PROJ-PUNE-2025-BA225D6A`
  * Tab: `Governance (Cedar)` verified via automated headless browser subagent.
  * Console Errors: **0 console errors**.
  * Persona simulator tested for both `ALLOW` and `DENY` paths with live UI card updates.

---

## 9. Architectural Limitations & Production Roadmap

1. **In-Memory Decision Audit Trail**:
   * *Current State*: Audit records are stored in a process-local circular buffer (last 100 decisions) to avoid provisioning databases (DynamoDB/RDS) in compliance with AWS service discipline.
   * *Production Roadmap*: In enterprise production, audit logs should stream asynchronously via Amazon Kinesis Data Firehose into an S3-backed compliance lake with cryptographic hash chaining.
2. **Demo Persona Authentication**:
   * *Current State*: Relies on `X-Climora-Actor` header resolving server-side persona constants for zero-friction judge evaluation.
   * *Production Roadmap*: Replace header extraction with Amazon Cognito User Pools or PMC Okta/SAML enterprise Single Sign-On, injecting Cedar principal entities from validated JWT claims.
