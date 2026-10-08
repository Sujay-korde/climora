# CLIMORA — PHASE 2D.0R: Governance Model Reconciliation, Role/Permission Validation & Stakeholder Decision Gate

**Document Version:** 1.0.0-CANONICAL  
**Status:** READ-ONLY ARCHITECTURAL RECONCILIATION GATE — NO IMPLEMENTATION  
**Precondition:** Phase 2D.0 Completed  
**Class:** Non-Invasive Architectural Reconciliation & Decision Freeze  
**Roles:** Civic Governance Architect, Authorization Architect, Product Architect, Institutional Workflow Designer, Security Reviewer, Backward-Compatibility Auditor, Hackathon Scope Controller  
**Date:** 2026-10-06  
**Target Artifact:** [`docs/architecture/phase-2d0r-governance-reconciliation-gate.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-2d0r-governance-reconciliation-gate.md)

---

## 1. Executive Summary & Reconciliation Verdict

### 1.1 Context and Motivation
Phase 2D.0 established the foundational thesis:
> *"One Canonical Scientific Record, One Project Lifecycle, One Governance Authority Model, and Multiple Role-Aware Perspectives."*

It proposed introducing a contextual Perspective Lens on top of [`frontend/src/pages/ProjectPage.tsx`](file:///c:/Users/lenovo/climora/frontend/src/pages/ProjectPage.tsx). However, before authorizing any implementation in Phase 2D.1, critical governance, institutional, and authorization ambiguities were detected in Phase 2D.0:
1. **Persona vs. Role Conflation:** The demo personas (e.g., `pmc_commissioner`, `urban_planner_lead`) were partially conflated with Cedar functional roles (`municipal_officer`, `project_manager`), organization types (`PMC`), and project assignments.
2. **Lens Count Inconsistency:** Phase 2D.0 announced *"5 Contextual Workspace Lenses"* in text, yet enumerated **six** lenses (including an orphan *Capital Diligence* lens without an underlying persona or role).
3. **NGO / Implementing Partner Ambiguity:** NGO and implementing partner concepts were referenced without resolving whether they require new Cedar roles, organizational classifications, or complete deferral.
4. **Funder Capability Gap:** A funder review lens was proposed without evaluating whether the backend implements any actual funder identity, funding transactions, or disbursement mechanics.
5. **Security Boundary Integrity:** The boundary between frontend workspace selection and server-side authorization was underspecified.

### 1.2 Reconciliation Verdict
**VERDICT: RECONCILED WITH ZERO MUTATION & STRICT HACKATHON BOUNDARIES.**

* **Application Code Modified:** `0 files`
* **Cedar Policies Modified:** `0 policies`
* **API Contracts Modified:** `0 endpoints`
* **Scientific Artifacts Modified:** `0 files`
* **Dependencies Changed:** `0 packages`
* **AWS Infrastructure Modified:** `0 resources`

This report provides the authoritative reconciliation. It freezes all governance decisions, eliminates conceptual ambiguities, aligns the perspective lens count strictly to the **five verified system personas**, and defines the exact minimal Phase 2D.1 scope.

---

## 2. Absolute Non-Invasive Rule Adherence

In accordance with Phase 2D.0R constraints:
1. No application code, Cedar policy, API route, or frontend component has been altered.
2. No database, authentication provider (Cognito), or external service has been provisioned.
3. No dependencies were installed; no AWS CLI commands were executed.
4. Findings discovered during code auditing are recorded as architectural decisions rather than opportunistic code fixes.
5. This report is written to a dedicated file ([`docs/architecture/phase-2d0r-governance-reconciliation-gate.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-2d0r-governance-reconciliation-gate.md)) leaving the prior Phase 2D.0 document preserved as historical record.

---

## 3. First Principle: Separation of Five Governance Concepts

To avoid brittle role-based access control (RBAC) antipatterns and prevent confusing identity with authority, CLIMORA strictly separates five distinct architectural layers:

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             CLIMORA FIVE-LAYER GOVERNANCE                        │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 1. ACTOR (Principal)                                                             │
│    Who initiates the request? (Individual or service account identity)          │
│    e.g., Dr. Rajesh Patil ("pmc_commissioner"), Pooja Deshmukh ("urban_planner")│
├──────────────────────────────────────────────────────────────────────────────────┤
│ 2. ORGANIZATION / STAKEHOLDER TYPE                                               │
│    What institution or civic sector do they represent?                           │
│    e.g., Municipal Body (PMC), Commercial EPC Vendor, Independent Auditor, Civic │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 3. FUNCTIONAL ROLE                                                               │
│    What statutory or operational capacity is authorized in Cedar?               │
│    e.g., Role::"municipal_officer", Role::"project_manager", Role::"viewer"      │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 4. PROJECT ASSIGNMENT                                                            │
│    What is their binding to this specific project instance?                      │
│    e.g., Lead Urban Planner for PROJ-PUNE-2025-BA225D6A                          │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 5. CAPABILITY & AUTHORIZATION                                                    │
│    Can this Actor execute Action A on Project P at State S with MRV Gates G?     │
│    Evaluated via Cedar: cedarpy.is_authorized() + Domain State Machine Guards   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Status of the Five Concepts in CLIMORA

| Concept Layer | Implementation Status | Implementation Evidence | Architectural Role in Hackathon | Future Extension Path |
| :--- | :--- | :--- | :--- | :--- |
| **1. Actor** | `IMPLEMENTED` | `services/cedar_service.py:L135-L176` (`DEMO_ACTORS` registry, `resolve_actor()`) | Canonical demo identities passed via `X-Climora-Actor` header | JWT `sub` claim from AWS Cognito / OIDC provider |
| **2. Organization** | `PARTIALLY IMPLEMENTED` | `services/cedar_service.py:L141,L149,L157` (Metadata field in `DEMO_ACTORS`) | Informational display only; NOT an authorization boundary | First-class tenant entity for multi-city governance |
| **3. Functional Role** | `IMPLEMENTED` | `services/cedar_service.py:L33-L118` (Cedar entities `Role::"<role>"`) | The core authorization group in Cedar policy permits | Dynamic role-binding engine via AWS Verified Permissions |
| **4. Project Assignment** | `DESIGN-ONLY` | Implicit in canonical single-project scope (`CANONICAL_PROJECT_ID`) | Not enforced; unnecessary for single-project demonstration | Multi-project role assignment matrix (e.g., Planner on Proj A, Viewer on Proj B) |
| **5. Capability / Authorization** | `IMPLEMENTED` | `services/cedar_service.py:L297-L387`, `api/routes/projects.py:L67-L123` | Server-side Cedar evaluation (`cedarpy`) + FSM guards | Distributed policy store with AWS Verified Permissions API |

**Key Architectural Rule:** An Actor is NOT a Role; an Organization is NOT an Actor. Cedar policies evaluate strictly over **Functional Roles**, **Resources**, **States**, and **Evidence Gates**.

---

## 4. Audit of the Actual Cedar Model & Repository Evidence

A comprehensive inspection of the authoritative backend source code was conducted across [`services/cedar_service.py`](file:///c:/Users/lenovo/climora/services/cedar_service.py), [`api/routes/projects.py`](file:///c:/Users/lenovo/climora/api/routes/projects.py), [`processing/project_mrv.py`](file:///c:/Users/lenovo/climora/processing/project_mrv.py), and [`tests/test_cedar_governance.py`](file:///c:/Users/lenovo/climora/tests/test_cedar_governance.py).

### 4.1 Authoritative Cedar Governance Table

| Existing Actor (`actor_id`) | Cedar Principal Entity | Functional Cedar Role (`parents`) | Authorized Cedar Actions | Target Resource Type | Explicit State / Context Guards | Authoritative Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `citizen_viewer` | `Actor::"citizen_viewer"` | `Role::"viewer"` | `view_project` | `Project` | **None** (Universal Read under Policy 1) | [`services/cedar_service.py:L34-L41, L168-L176`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L34-L41) |
| `urban_planner_lead` | `Actor::"urban_planner_lead"` | `Role::"project_manager"` | `view_project`<br>`propose_revision`<br>`submit_for_sanction`<br>`request_mrv` | `Project` | Policy 2 permits without state clause; Domain FSM enforces transition validity | [`services/cedar_service.py:L43-L54, L144-L151`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L43-L54) |
| `pmc_commissioner` | `Actor::"pmc_commissioner"` | `Role::"municipal_officer"` | `view_project`<br>`approve_project` | `Project` | **State Guard:** `when { resource.state == "PROPOSED" }`<br>Domain FSM requires `sanction_id` + budget | [`services/cedar_service.py:L56-L66, L136-L143`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L56-L66) |
| `sharma_contractors` | `Actor::"sharma_contractors"` | `Role::"field_contractor"` | `view_project`<br>`record_implementation` | `Project` | **State Guard:** `when { resource.state == "FUNDED" \|\| resource.state == "IMPLEMENTING" }` | [`services/cedar_service.py:L68-L79, L152-L159`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L68-L79) |
| `sgs_environmental_auditor` | `Actor::"sgs_environmental_auditor"` | `Role::"mrv_verifier"` | `view_project`<br>`request_mrv`<br>`verify_impact` | `Project` | **MRV Evidence Gate Guard:** `when { resource.state == "MONITORING" && resource.is_mrv_executable == true && resource.qc_passed == true }` | [`services/cedar_service.py:L80-L101, L160-L167`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L80-L101) |
| *Any Principal* (Universal Negative Policy) | Any `principal` | Any / All | `modify_canonical_data`<br>`modify_observed_data`<br>`modify_derived_data`<br>`modify_modeled_result`<br>`rewrite_optimization`<br>`mark_modeled_as_verified` | `Project` | **Absolute Forbid:** No principal, regardless of role or state, may mutate canonical baselines or solver outputs | [`services/cedar_service.py:L103-L117`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L103-L117) |

### 4.2 Key Findings from Real Code Inspection
1. **Zero Client-Side Role Trust:** Role claims in request bodies are completely ignored. The backend derives the principal from `X-Climora-Actor` and maps it via `resolve_actor()` ([`services/cedar_service.py:L231`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L231)).
2. **Untrusted Fallback:** Any unknown or unauthenticated actor string defaults to `Role::"viewer"` ([`services/cedar_service.py:L246-L253`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L246-L253)).
3. **Double Guarding (Cedar + FSM):** Cedar authorization precedes state transitions in [`api/routes/projects.py:L498`](file:///c:/Users/lenovo/climora/api/routes/projects.py#L498). If Cedar allows, `ProjectStateMachine.can_transition()` ([`processing/project_mrv.py:L258`](file:///c:/Users/lenovo/climora/processing/project_mrv.py#L258)) executes secondary invariant checks. Both must pass.
4. **Anti-Contamination Enforcement:** In [`processing/project_mrv.py:L304-L309`](file:///c:/Users/lenovo/climora/processing/project_mrv.py#L304-L309), synthetic fixtures (`is_synthetic_demo == True`) are blocked by code from transitioning a canonical project to `VERIFIED`.

---

## 5. Validation of Existing Personas

### 5.1 Persona: `citizen_viewer` (Ananya Joshi)
* **Underlying Cedar Role:** `Role::"viewer"`.
* **Is `viewer` a genuine public-read role?** YES. Under Cedar Policy 1 (`policy_universal_view`), any principal can execute `Action::"view_project"`.
* **What can it actually read via API?** Complete project representation (`GET /projects/{id}`), H3 cell allocations (`GET /projects/{id}/allocation`), observed and derived baselines (`GET /projects/{id}/baseline`), MRV status (`GET /projects/{id}/mrv`), and governance audit trail (`GET /projects/{id}/governance-audit`).
* **Does it see scientific evidence?** Yes: Landsat 8/9 LST baseline (46.36°C), thermal anomaly (+5.19°C), NDVI, NDBI, and spatial LISA clusters.
* **Does it see allocation and cost?** Yes: 28 treated H3 cells, 2,695 planned street trees, ₹9,992,500 modeled CAPEX, and ₹7,500 slack.
* **Does it see internal governance details?** Yes, the read API allows viewing audit records.
* **Should it see internal Cedar AST diagnostics in the UI?** **NO.**
  * *Critical Reconciliation Distinction:* **API Authorization $\neq$ Presentation Hierarchy**.
  * While the public actor is authorized to read public records, presenting raw Cedar policy syntax, policy AST IDs (`policy0`, `policy2`), and execution micro-timings creates cognitive overload and degrades the civic story.
  * The Civic Transparency UI should present an editorial, human-understandable civic accountability view, while technical Cedar diagnostic details remain in an expandable audit drawer.
* **Recommendation:** Preserve `citizen_viewer` and `Role::"viewer"` unchanged. Do NOT create a separate citizen API. Tailor the frontend presentation lens.

### 5.2 Persona: `urban_planner_lead` (Pooja Deshmukh)
* **Underlying Cedar Role:** `Role::"project_manager"`.
* **Is `project_manager` semantically correct?**
  * In municipal environmental practice, the title is "Lead Urban Climate Planner" or "Senior Environmental Officer", whereas "Project Manager" is an IT/corporate term.
  * However, in municipal administrative workflow, this person manages the project scope, cell allocations, and revisions prior to sanction.
* **Recommendation:**
  * **Keep Cedar Role Unchanged:** Retain `Role::"project_manager"` in `services/cedar_service.py` to prevent breaking compiled Cedar policies and regression tests.
  * **Conceptual UX Label:** Display as **"Lead Urban Climate Planner"** in the frontend UI.
  * **Actual Capabilities:** Allowed to propose cell revisions (`POST /projects/{id}/revisions`), submit for sanction (`Action::"submit_for_sanction"`), and trigger MRV baselines (`Action::"request_mrv"`). Denied capital sanction approval.

### 5.3 Persona: `pmc_commissioner` (Dr. Rajesh Patil)
* **Underlying Cedar Role:** `Role::"municipal_officer"`.
* **Is `municipal_officer` too broad?**
  * YES. In municipal government (such as Pune Municipal Corporation), a junior engineer, ward inspector, or clerk is a "municipal officer". But only the Municipal Commissioner or the Standing Committee possesses statutory authority to sanction ₹10,000,000 public capital expenditure.
  * Implying that any municipal officer can sanction tenders is institutional inaccuracy.
* **Recommendation:**
  * **Keep Cedar Role Unchanged:** Retain `Role::"municipal_officer"` in Cedar policy code for 100% backward compatibility.
  * **Conceptual UX Label:** Treat and display conceptually as **"Municipal Sanctioning Authority / Commissioner"**.
  * **Actual Capabilities:** Authorized strictly to approve projects in `PROPOSED` state with `sanction_id` and `approved_budget_inr`. Forbidden from modifying canonical scientific baselines.

### 5.4 Persona: `sharma_contractors` (Sharma Agro & Forestry Ltd)
* **Underlying Cedar Role:** `Role::"field_contractor"`.
* **Is Contractor the right abstraction?**
  * In CLIMORA, this actor logs ground deployment batches: cell ID, tree quantity, completion date, and delivery receipts ([`api/routes/projects.py:L355-L401`](file:///c:/Users/lenovo/climora/api/routes/projects.py#L355-L401)).
  * Could an environmental NGO perform the same physical sapling planting? Yes. An NGO engaged in community greening performs the exact same operational task.
  * However, CLIMORA currently lacks contract bidding, tender procurement, or multi-contractor dispatch workflows.
* **Recommendation:**
  * Retain `sharma_contractors` and `Role::"field_contractor"`.
  * Conceptually recognize that "Field Contractor" is a subtype of the broader "Implementing Partner" concept.
  * For the hackathon, do not build generalized implementing partner machinery. The existing EPC contractor model is concrete, realistic, and fully implemented.

### 5.5 Persona: `sgs_environmental_auditor` (SGS Environmental Auditing)
* **Underlying Cedar Role:** `Role::"mrv_verifier"`.
* **Is `mrv_verifier` correct?** YES. It precisely represents an ISO 14064-2 accredited third-party greenhouse gas and microclimate verifier.
* **Separation of Concerns:**
  * *Requesting MRV analysis:* Permitted to `project_manager` and `mrv_verifier`.
  * *Executing MRV calculation:* Autonomous backend engine (`MRVDomainService`).
  * *Performing Quality Control (QC):* Deterministic rule engine (`MRVQualityControlEngine` in `processing/project_mrv.py:L313-L417`).
  * *Certifying Verification:* Strictly reserved to `mrv_verifier`, and double-guarded by Cedar Policy 6 (requires project in `MONITORING`, `is_mrv_executable == True`, `qc_passed == True`).
* **Recommendation:** Preserve without change. The MRV gate is one of CLIMORA's highest-value architectural differentiators and must not be weakened.

---

## 6. Mandatory Unresolved Decision: NGO / Implementing Partner

### 6.1 Evaluation of Options

| Option | Description | Backend Support | Hackathon Fit | Architectural Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Option A** | NGO is a distinct functional role in Cedar (`Role::"ngo_partner"`). | Zero backend policies, zero schemas, zero state guards. | High risk; requires Cedar modifications, test rewrites, and new state machine paths. | **REJECTED** |
| **Option B** | NGO is an Organization / Stakeholder Type that may hold existing functional roles (`viewer` or `field_contractor`). | Fully compatible with current layer separation. | Clean; conceptually sound; requires zero code changes. | **APPROVED (Conceptual Architecture)** |
| **Option C** | "Implementing Partner" is the formal abstraction encompassing contractors and NGOs. | Supported conceptually, but code uses `field_contractor`. | Over-engineering terminology for a hackathon. | **DEFERRED (Post-Hackathon Refactor)** |
| **Option D** | NGO functionality deferred entirely for the hackathon. | Requires zero new features. | Eliminates scope bloat and prevents judge confusion. | **APPROVED (Scope Discipline)** |

### 6.2 Definitive Reconciliation Decision
**DECISION: COMBINATION OF OPTION B (Conceptual Model) AND OPTION D (Hackathon Scope).**
* An NGO is an **Organization / Stakeholder Type**, NOT an authorization role.
* If a civil society NGO audits public tree canopy allocations, they utilize the `viewer` capability (`citizen_viewer`).
* If a community forestry NGO is contracted to plant saplings, they utilize the `field_contractor` capability.
* **No new Cedar role, no new API endpoint, and no new demo persona shall be added for NGOs in Phase 2D.1.**

---

## 7. Mandatory Unresolved Decision: Funder & Capital Diligence

### 7.1 Authoritative System Audit: What Does CLIMORA Actually Support?
A strict code audit of the current repository reveals:
* **Funder Identity:** `NOT IMPLEMENTED` (No funder persona in `DEMO_ACTORS`).
* **Funding Organization:** `NOT IMPLEMENTED` (No institutional entity in database or schema).
* **Funding Review:** `PARTIALLY IMPLEMENTED` (Exposed via read-only project cost breakdowns, budget envelopes, and population metrics).
* **Funding Decision / Commitment:** `NOT IMPLEMENTED` (Project state machine has `PROPOSED -> FUNDED`, but this is gated by **municipal budget sanction** via `sanction_id` and `approved_budget_inr`, NOT by a commercial or multilateral loan commitment).
* **Disbursement / Invoicing:** `NOT IMPLEMENTED` (No financial payment rails).
* **Finance Agreement:** `NOT IMPLEMENTED` (No term sheet or legal contract models).
* **Funding Audit Trail:** `NOT IMPLEMENTED` (Cedar audits municipal approvals, not capital disbursements).

### 7.2 Evaluation of Funder Alternatives

| Alternative | Evaluation & Architectural Reality | Recommendation |
| :--- | :--- | :--- |
| **Option A: Real Funder Role** | Requires adding `Role::"funder"`, new Cedar policies, transaction endpoints (`POST /fund`), disbursement models, and database persistence. Massive scope explosion. Fabricates mechanics that do not exist. | **STRICTLY REJECTED** |
| **Option B: Funder Read-Only Workspace Lens** | Adds a 6th perspective lens to the UI switcher. But who is the active persona? Reusing `citizen_viewer` creates confusion; creating a synthetic persona without distinct Cedar permissions is misleading. | **REJECTED (Avoids 6th Lens Dilemma)** |
| **Option C: Finance Readiness View (Section/Tab)** | CLIMORA already computes all metrics required for green bankability (₹9.99M CAPEX, ₹3,500 unit cost, ₹20k mobilization, 118,941 population, ISO 14064-2 MRV protocol). Present these in an existing project tab (`Budget` / `Finance Readiness`) without pretending a funder transactional identity exists. | **RECOMMENDED & APPROVED** |

### 7.3 Definitive Reconciliation Decision
**DECISION: OPTION C.**
* CLIMORA does NOT have a transactional funder role and will NOT fabricate one.
* CLIMORA produces **bankable environmental intervention assets**.
* Financial diligence information (CAPEX breakdown, slack reserve, cost per tree, population served, MRV standard) is presented within the project console's **Budget & Finance Readiness** views.
* No separate "Funder Reviewer" persona or Cedar role will be introduced.

---

## 8. Citizen & Public Transparency Decision

### 8.1 Seven Mandatory Architectural Questions

| Question | Architectural Determination | Code Evidence |
| :--- | :--- | :--- |
| **1. Is public access useful to the product?** | **YES.** Municipal climate-adaptation projects utilize public tax revenues (PMC budget). Civic trust requires public transparency. | Grounded in civic mandate of Pune Municipal Corporation. |
| **2. What public problem does it solve?** | Eliminates "ghost plantings", municipal fund diversion, and greenwashing by making spatial allocations and scientific verification verifiable by citizens. | Canonical allocation parquet is publicly verifiable via SHA-256 hash. |
| **3. What should citizens be able to understand?** | Which streets receive shade trees, why those cells were selected (high LST + high population), the total expenditure, current project state, and whether satellite cooling has been verified. | All exposed via `GET /projects/{id}`, `/allocation`, and `/baseline`. |
| **4. What should citizens NOT see?** | Raw Cedar policy AST strings, compiler diagnostics, internal debug traces, pre-sanction draft revisions, contractor dispute logs, or AWS infrastructure IDs. | Currently exposed in `CedarGovernancePanel.tsx:L285`; must be separated in UI. |
| **5. Does public visibility strengthen the hackathon story?** | **YES, decisively.** It proves CLIMORA is a complete civic decision instrument, not just an internal municipal spreadsheet. | Demonstrates end-to-end civic accountability to judges. |
| **6. Does it require new backend functionality?** | **NO.** The universal read permit (`@id("policy_universal_view")`) already authorizes full read access. | `services/cedar_service.py:L36-L41` already handles this. |
| **7. Can current read APIs support it?** | **YES, 100%.** No new endpoints, parameters, or schemas are required. | Supported by `GET /projects/{id}` and `/allocation`. |

### 8.2 Separation of Public Transparency from Internal Governance
The UI must enforce clean contextual separation:
* **Public Transparency Presentation:** Editorial, clean, visual map of interventions, ward-level summary, public cost breakdown, and certified cooling status.
* **Internal Governance Presentation:** Interactive Cedar pre-flight checks, state transition modals, revision proposals, and audit logs.

---

## 9. Reconciled End-to-End Stakeholder Lifecycle

Every stage of the canonical CLIMORA project lifecycle is mapped below to its exact technical reality:

```text
Scientific Evidence (S3 Data Lake)
        ↓
Spatial & Risk Analysis (HiGHS MILP Solver)
        ↓
Project Formation (Lead Urban Climate Planner)
        ↓
Municipal Review & Sanction (Municipal Commissioner)
        ↓
Finance Readiness & Bankability (Project Budget Summary)
        ↓
Physical Field Deployment (Licensed EPC Contractor)
        ↓
Post-Monsoon Observation (Landsat 9 Satellite TIRS)
        ↓
MRV Quality Control Audit (MRV Quality Control Engine)
        ↓
Independent Certification (Accredited MRV Verifier)
        ↓
Public Transparency & Verification (Civic Citizens & Observers)
```

### 9.1 Stage-by-Stage Implementation & Scope Matrix

| Stage | Primary Actor / User | Organization Type | Functional Role | Project State | Cedar Action Evaluated | Implementation Status & Repo Evidence | What They See | What They Cannot Do | Hackathon Scope |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Scientific Discovery** | Autonomous Pipeline | Scientific Core | System Service | `DISCOVERED` → `OPTIMIZED` | N/A (Data Lake Ingestion) | `IMPLEMENTED`<br>[`processing/project_mrv.py:L243`](file:///c:/Users/lenovo/climora/processing/project_mrv.py#L243) | Baseline satellite rasters, H3 grid, risk surfaces | Cannot bypass thermodynamic caps (F-26.1) | Production Frozen in S3 |
| **2. Project Formation** | `urban_planner_lead` | Municipal (PMC) | `project_manager` | `OPTIMIZED` → `PROPOSED` | `propose_revision`<br>`submit_for_sanction` | `IMPLEMENTED`<br>[`api/routes/projects.py:L532`](file:///c:/Users/lenovo/climora/api/routes/projects.py#L532) | Solver allocations, slack budget, revision draft history | Cannot approve budget sanction; cannot mutate canonical Parquet | **IMPLEMENT NOW** (Interactive in UI) |
| **3. Municipal Review & Sanction** | `pmc_commissioner` | Municipal Executive | `municipal_officer` | `PROPOSED` → `FUNDED` | `approve_project` | `IMPLEMENTED`<br>[`api/routes/projects.py:L459`](file:///c:/Users/lenovo/climora/api/routes/projects.py#L459) | Full capital budget (₹9.99M), statutory tender scope | Cannot approve without `sanction_id` & budget; cannot approve once `FUNDED` | **IMPLEMENT NOW** (Interactive in UI) |
| **4. Finance Readiness** | Open / Investor | Financial / MDB | `viewer` | `FUNDED` | `view_project` | `IMPLEMENTED` (Presentation View)<br>[`services/project_service.py:L213`](file:///c:/Users/lenovo/climora/services/project_service.py#L213) | CAPEX, OPEX, unit economics, WorldPop beneficiaries | Cannot disburse funds (no transactional finance API exists) | **IMPLEMENT NOW** (Readiness tab/section) |
| **5. Field Deployment** | `sharma_contractors` | EPC Commercial Vendor | `field_contractor` | `FUNDED` → `IMPLEMENTING` | `record_implementation` | `IMPLEMENTED`<br>[`api/routes/projects.py:L355`](file:///c:/Users/lenovo/climora/api/routes/projects.py#L355) | Treated H3 cells list, planting quotas, batch logs | Cannot record implementation when project is in `PROPOSED` | **IMPLEMENT NOW** (Interactive in UI) |
| **6. Physical Completion** | `sharma_contractors` / `urban_planner_lead` | Vendor / Municipal | `field_contractor` / `project_manager` | `IMPLEMENTING` → `IMPLEMENTED` | `record_implementation` | `IMPLEMENTED`<br>[`processing/project_mrv.py:L276`](file:///c:/Users/lenovo/climora/processing/project_mrv.py#L276) | Cumulative trees deployed (e.g., 2,695 units) | Cannot transition to `IMPLEMENTED` without documented events | **IMPLEMENT NOW** (Guarded by FSM) |
| **7. Baseline Monitoring** | `urban_planner_lead` / `sgs_environmental_auditor` | Municipal / Auditor | `project_manager` / `mrv_verifier` | `IMPLEMENTED` → `MONITORING` | `request_mrv` | `IMPLEMENTED`<br>[`services/cedar_service.py:L81`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L81) | Difference-in-Differences readiness status | Cannot certify verification prior to satellite pass | **IMPLEMENT NOW** (Guarded by FSM) |
| **8. Independent Verification** | `sgs_environmental_auditor` | Accredited Verifier (ISO) | `mrv_verifier` | `MONITORING` → `VERIFIED` | `verify_impact` | `IMPLEMENTED`<br>[`api/routes/projects.py:L403`](file:///c:/Users/lenovo/climora/api/routes/projects.py#L403) | Satellite observation QA, QC audit violations, DID model | Cannot certify if QC fails or if demo fixture is synthetic | **IMPLEMENT NOW** (Interactive in UI) |
| **9. Civic Transparency** | `citizen_viewer` | Civic Public / Civil Society | `viewer` | Any state (`PROPOSED` ... `VERIFIED`) | `view_project` | `IMPLEMENTED`<br>[`services/cedar_service.py:L36`](file:///c:/Users/lenovo/climora/services/cedar_service.py#L36) | Public canopy map, spend breakdown, verified cooling | Cannot mutate state, propose revisions, or approve tenders | **IMPLEMENT NOW** (Interactive in UI) |

---

## 10. Critical Evaluation: Does Workspace Selection Affect Authorization?

### 10.1 The Cardinal Principle
**NO. WORKSPACE SELECTION NEVER AFFECTS SERVER-SIDE AUTHORIZATION.**

```text
                  USER INTERACTION
                         │
                         ▼
             Frontend Workspace Lens Selection
       (Changes visible tab grouping & action prominence)
                         │
                         ▼
                  HTTP API Request
             Header: X-Climora-Actor: <actor_id>
                         │
═════════════════════════╪════════════════════════════════ (Security Boundary)
                         │
                         ▼
            Backend Actor Resolution (Server-Side)
            clean_actor_id, actor_meta = resolve_actor()
                         │
                         ▼
             Cedar Engine Authorization
            cedarpy.is_authorized(principal, action, resource, ...)
                         │
           ┌─────────────┴─────────────┐
        ALLOW                        DENY
           │                           │
           ▼                           ▼
  Domain State Machine        HTTP 403 Forbidden
    Validation (FSM)          Zero State Mutation
           │
           ▼
  Domain Action Executed
```

### 10.2 Proof and Security Implications
1. **The frontend is never the security boundary.** Selecting "Municipal Sanction" in the UI does NOT grant municipal authority.
2. If an actor header carries `X-Climora-Actor: citizen_viewer`, and the user attempts to trigger an approval request, the server executes Cedar Policy 3 evaluation:
   $$\text{Decision} = \text{is\_authorized}(\text{Actor::"citizen\_viewer"}, \text{Action::"approve\_project"}, \dots) \longrightarrow \mathbf{DENY}$$
   The request is immediately aborted with HTTP 403 Forbidden, structured diagnostics are logged, and **zero state mutation occurs** (verified in [`tests/test_cedar_governance.py:L164-L195`](file:///c:/Users/lenovo/climora/tests/test_cedar_governance.py#L164-L195)).
3. **Demo Persona Header Protocol:** In the hackathon demonstration interface, switching a persona updates the active client-side `currentActorId` passed in the `X-Climora-Actor` header ([`frontend/src/services/api.ts:L22-L37`](file:///c:/Users/lenovo/climora/frontend/src/services/api.ts#L22-L37)). This allows judges to test server-side Cedar policy boundaries live in the browser. But the authorization decision is calculated 100% server-side by Cedar.

---

## 11. Role vs. Workspace Architectural Model

### 11.1 Comparison of Models

| Architectural Model | Definition | Strengths | Fatal Flaws | Selection |
| :--- | :--- | :--- | :--- | :--- |
| **Model A: Role $\rightarrow$ Workspace** | Strict 1:1 mapping between each role and an isolated dashboard application. | Simple to conceptualize. | Fragments the platform; violates the "Shared Truth" principle; creates 5 disconnected web apps. | **REJECTED** |
| **Model B: Need $\rightarrow$ Workspace, Role $\rightarrow$ Capabilities** | Workspaces represent institutional workflows; roles define permissions within them. | Clean enterprise architecture. | Requires complex multi-tenant workspace configuration beyond hackathon scope. | **DEFERRED** |
| **Model C: One Project Console + Role-Aware Perspective Lenses** | A single canonical project console (`ProjectPage.tsx`) with a top-level **Perspective Lens** that adjusts information density and highlights relevant actions while preserving universal access to evidence. | Preserves canonical truth; lightweight; zero backend changes; instant judge comprehension. | Must avoid visual clutter (addressed via clean design). | **SELECTED & APPROVED** |

### 11.2 Architectural Decision
**Model C is definitively approved.**
All stakeholders view the **same project record** (`PROJ-PUNE-2025-BA225D6A`), but the Perspective Lens controls which actions are prominent and what level of detail leads.

---

## 12. Reconciliation of Lens Count: Exact Alignment to 5 Lenses

### 12.1 The Problem in Phase 2D.0
Phase 2D.0 contained an internal contradiction:
* Section 9 header announced: *"5 semantic workspace lenses"*.
* Section 9 body listed **six** lenses:
  1. Civic Transparency
  2. Urban Planning
  3. Municipal Decision
  4. Field Delivery
  5. Independent MRV
  6. Capital Diligence

The 6th lens ("Capital Diligence") was an orphan: there is no corresponding persona in `DEMO_ACTORS`, no corresponding role in Cedar, and no funding transactions in the backend.

### 12.2 Authoritative Resolution: EXACTLY FIVE PERSPECTIVE LENSES

CLIMORA reconciles this count to **EXACTLY FIVE (5) PERSPECTIVE LENSES**, creating a perfect 1:1 harmonic alignment with the 5 verified demo personas and 5 Cedar functional roles:

```text
┌───────────────────────────────┬─────────────────────────────┬──────────────────────────────┐
│ Perspective Lens Name         │ Active Demo Persona         │ Cedar Functional Role        │
├───────────────────────────────┼─────────────────────────────┼──────────────────────────────┤
│ 1. Civic Transparency         │ citizen_viewer              │ Role::"viewer"               │
│ 2. Urban Planning             │ urban_planner_lead          │ Role::"project_manager"      │
│ 3. Municipal Sanction         │ pmc_commissioner            │ Role::"municipal_officer"    │
│ 4. Field Delivery             │ sharma_contractors          │ Role::"field_contractor"     │
│ 5. Independent MRV            │ sgs_environmental_auditor   │ Role::"mrv_verifier"         │
└───────────────────────────────┴─────────────────────────────┴──────────────────────────────┘
```

### 12.3 Where Does "Capital Diligence" Go?
* Capital diligence and bankability are **attributes of the project**, NOT a separate user persona.
* The financial metrics (CAPEX, slack, unit costs, WorldPop beneficiaries, ISO 14064-2 MRV protocol) are incorporated directly into the **Budget & Finance Readiness** tab within the console.
* This completely eliminates the orphan 6th lens, resolves the Phase 2D.0 inconsistency, and ensures every single lens maps cleanly to an actual system identity.

---

## 13. Rebuilt and Reconciled Capability Matrix

This matrix establishes the definitive authorization and gating status for all actions across all personas and conceptual roles:

| Capability / Action | `citizen_viewer` (`viewer`) | `urban_planner_lead` (`project_manager`) | `pmc_commissioner` (`municipal_officer`) | `sharma_contractors` (`field_contractor`) | `sgs_environmental_auditor` (`mrv_verifier`) | Conceptual NGO Partner | Conceptual Funder Reviewer |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `view_project` | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** |
| `view_baseline` | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** |
| `view_allocation` | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** | **CURRENT ALLOW** |
| `propose_revision` | **CURRENT DENY** | **CURRENT ALLOW** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** |
| `submit_for_sanction` | **CURRENT DENY** | **CURRENT ALLOW** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** |
| `approve_project` *(PROPOSED)* | **CURRENT DENY** | **CURRENT DENY** | **CURRENT ALLOW** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** |
| `approve_project` *(Non-PROPOSED)*| **CURRENT DENY** | **CURRENT DENY** | **STATE-GATED** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** |
| `record_implementation` *(PROPOSED)* | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **STATE-GATED** | **CURRENT DENY** | **STATE-GATED** | **CURRENT DENY** |
| `record_implementation` *(FUNDED/IMPL)* | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT ALLOW** | **CURRENT DENY** | **CURRENT ALLOW** | **CURRENT DENY** |
| `request_mrv` | **CURRENT DENY** | **CURRENT ALLOW** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT ALLOW** | **CURRENT DENY** | **CURRENT DENY** |
| `verify_impact` *(Incomplete gate)* | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **DOMAIN-GATED** | **CURRENT DENY** | **CURRENT DENY** |
| `verify_impact` *(MONITORING + QC)* | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT ALLOW** | **CURRENT DENY** | **CURRENT DENY** |
| `modify_canonical_data` | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** | **CURRENT DENY** |
| `commit_funding` | **DEFERRED** | **DEFERRED** | **DEFERRED** | **DEFERRED** | **DEFERRED** | **DEFERRED** | **DEFERRED** |

*Legend:*
* **CURRENT ALLOW**: Cedar permit policy explicitly grants access in production code.
* **CURRENT DENY**: Cedar default-deny or negative forbid policy halts execution.
* **STATE-GATED**: Allowed for role in Cedar, but conditional on `resource.state`.
* **DOMAIN-GATED**: Allowed in Cedar only when contextual evidence criteria (`is_mrv_executable`, `qc_passed`) evaluate to true.
* **DEFERRED**: Not supported by system architecture; excluded from hackathon scope.

---

## 14. Information Architecture: Public UI vs. Institutional UI vs. Audit UI

| Information Type | Public Transparency Lens | Institutional Lenses (Planning/Sanction/Delivery) | Governance & Audit Lens |
| :--- | :---: | :---: | :---: |
| Project Geography & Target Cells (28 H3 cells) | **PROMINENT** | **PROMINENT** | **TABULAR** |
| Physical Intervention Quota (2,695 trees) | **PROMINENT** | **PROMINENT** | **TABULAR** |
| Thermal Baseline & Heat Vulnerability Index | **EDITORIAL SUMMARY** | **TECHNICAL METRICS** | **DATA LAKE ARTIFACT** |
| Transparent Cost Breakdown (₹9,992,500) | **PUBLIC OVERVIEW** | **DETAILED CAPEX/OPEX** | **AUDITED LINEAGE** |
| Current Lifecycle State (e.g., `PROPOSED`) | **BADGE** | **INTERACTIVE FLOW** | **FSM STATE TRANSITION** |
| Modeled Risk Reduction Score (0.106048) | **DISCLAIMED CONTEXT** | **OBJECTIVE ANALYSIS** | **SOLVER CONVERGENCE** |
| Verified Temperature Reduction (°C) | **ONLY WHEN VERIFIED** | **PRE/POST SATELLITE** | **DID EMPIRICAL ESTIMATE** |
| Action Mutation Triggers (Sanction / Revise / Log) | **HIDDEN** | **CONTEXTUALLY PROMINENT** | **DRY-RUN SIMULATOR** |
| Active Cedar Policy AST & Rule Compilation | **HIDDEN** | **DRAWER (Optional)** | **EXPANDED ACCORDION** |
| Chronological Decision Audit Trail | **AGGREGATE SUMMARY** | **RECENT ACTIONS** | **FULL CHRONOLOGICAL LOG** |
| Scientific Artifact SHA-256 Hashes | **PROVENANCE LINK** | **VERIFICATION BADGE** | **FULL CRYPTOGRAPHIC AUDIT** |
| Internal Diagnostic Error Blobs | **HIDDEN** | **TOAST / SUMMARY** | **STRUCTURED JSON VIEWER** |

---

## 15. Hackathon Scope Decision

### 15.1 Categorization

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 HACKATHON SCOPE DISCIPLINE                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. IMPLEMENT NOW (Phase 2D.1)                                                          │
│    • 5-Perspective Selector Bar on ProjectPage.tsx                                     │
│    • Contextual action prominence based on active lens                                 │
│    • Automatic synchronization of X-Climora-Actor header                               │
│    • Separation of Civic Transparency presentation from Cedar policy diagnostics       │
│    • Zero changes to Cedar policies, backend routes, schemas, or scientific parquets   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. IMPLEMENT ONLY IF VERY LOW RISK (Time Permitting)                                   │
│    • Enhanced Bankability & Finance Readiness metrics card in Budget tab               │
│    • Printable browser summary ("Municipal Sanction Certificate")                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. DEFER ENTIRELY (Post-Hackathon Roadmap)                                             │
│    • AWS Cognito / real authentication & login flows                                   │
│    • Multi-tenant organizational management                                            │
│    • Funder disbursement / transaction accounting                                      │
│    • Real-world procurement / tender bidding workflows                                 │
│    • NGO onboarding portal & citizen public commenting                                 │
│    • DynamoDB / S3 persistent event store for audit records                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Explicit Final Decisions (D1 through D12)

### D1: Are the existing five demo personas conceptually correct?
**YES.** They represent the essential civic-governance lifecycle: Civic Public (`citizen_viewer`), Urban Environment Planner (`urban_planner_lead`), Sanctioning Municipal Authority (`pmc_commissioner`), Ground EPC Vendor (`sharma_contractors`), and Independent GHG/MRV Auditor (`sgs_environmental_auditor`).

### D2: Which are actual functional roles versus merely demo actors?
* **Demo Actors (Principal identities):** `citizen_viewer`, `urban_planner_lead`, `pmc_commissioner`, `sharma_contractors`, `sgs_environmental_auditor`.
* **Actual Functional Roles (Cedar entities):** `Role::"viewer"`, `Role::"project_manager"`, `Role::"municipal_officer"`, `Role::"field_contractor"`, `Role::"mrv_verifier"`.

### D3: Should Municipal Officer become a narrower "Municipal Approver" concept?
**YES CONCEPTUALLY; NO IN CODE.**
In UI presentation, describe the actor as **"Municipal Sanctioning Authority / Commissioner"**. In Cedar code, preserve `Role::"municipal_officer"` to guarantee 100% backward compatibility.

### D4: Should Contractor become "Implementing Partner" or remain Contractor?
**REMAIN CONTRACTOR.**
"Implementing Partner" is an unnecessarily abstract term for the hackathon. The existing licensed EPC planting contractor model (`sharma_contractors`, `Role::"field_contractor"`) is concrete, realistic, and matches the implemented planting batch schema.

### D5: Should NGO be a role, organization type, implementing-partner subtype, or deferred?
**ORGANIZATION TYPE CONCEPTUALLY; DEFERRED FROM IMPLEMENTATION.**
An NGO is an organization type, not a Cedar permission role. An auditing NGO uses the `viewer` capability; a planting NGO uses the `field_contractor` capability. No new NGO role or persona will be added for the hackathon.

### D6: Should Funder be a role, read-only lens, Finance Readiness view, or deferred?
**FINANCE READINESS VIEW.**
No funder persona or backend transaction role exists or should be created. Financial bankability metrics (CAPEX, slack, unit economics, ISO 14064-2 MRV) will be highlighted within the project console's **Budget & Finance Readiness** section.

### D7: Does Citizen/Public Viewer need a dedicated public transparency experience?
**YES, IN PRESENTATION ONLY.**
The Civic Transparency lens will lead with the public climate story (maps, canopy quantities, public spend, verified impact) while collapsing raw Cedar policy syntax into an expandable audit drawer. Zero separate APIs required.

### D8: How many actual workspaces should CLIMORA have?
**ONE PROJECT CONSOLE WITH EXACTLY FIVE (5) PERSPECTIVE LENSES.**
No separate dashboard apps. Exactly five perspective lenses:
1. Civic Transparency
2. Urban Planning
3. Municipal Sanction
4. Field Delivery
5. Independent MRV

### D9: Should workspace selection affect authorization?
**NO, ABSOLUTELY NOT.**
The frontend is never a security boundary. Workspace selection only affects presentation density and action visibility. Authorization is evaluated 100% server-side via Amazon Cedar and Domain State Machine guards.

### D10: Which existing Cedar policies/actions must remain unchanged?
**ALL OF THEM (100%).**
All 7 compiled Cedar policies (`policy_universal_view`, `policy_pm_propose_revision`, `policy_officer_approve_project`, `policy_contractor_record_impl`, `policy_mrv_request`, `policy_mrv_verify_impact`, `policy_forbid_canonical_mutation`) remain frozen and untouched.

### D11: What is the minimum Phase 2D.1 implementation?
Add a clean 5-button Perspective Lens selector to [`frontend/src/pages/ProjectPage.tsx`](file:///c:/Users/lenovo/climora/frontend/src/pages/ProjectPage.tsx), contextually adjusting action button prominence, synchronizing `X-Climora-Actor`, and tucking raw Cedar debug panels into an audit drawer when in Civic Transparency view.

### D12: What should explicitly NOT be implemented?
No AWS Cognito authentication, no database schema changes, no new Cedar roles or policies, no transactional funder APIs, no NGO onboarding portal, no public commenting, and no mutation of canonical scientific Parquets.

---

## 17. Formal Approval Gate

| Decision Item | Reconciled Recommendation | Architectural Reason | Current System Support | Risk Rating | Requires Approval Before Phase 2D.1 |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **G-1: Lens Count Freeze** | Freeze Perspective Lenses to **exactly 5** | Aligns 1:1 with the 5 verified demo personas and Cedar roles; eliminates orphan 6th lens. | `100% SUPPORTED` | `VERY LOW` | **YES** |
| **G-2: Funder Modeling** | Present as **Finance Readiness View** in Budget section; no funder role | Avoids fabricating non-existent financial disbursement APIs; exposes real bankability metrics. | `100% SUPPORTED` | `VERY LOW` | **YES** |
| **G-3: NGO Handling** | Treat NGO as **Organization Type**; defer new roles/personas | Avoids modifying compiled Cedar policies; existing roles already handle auditing and planting. | `100% SUPPORTED` | `ZERO` | **YES** |
| **G-4: Security Decoupling**| Frontend lens **never** grants authority; server Cedar remains sole boundary | Enforces defense-in-depth and zero client trust. | `100% SUPPORTED` | `ZERO` | **YES** |
| **G-5: Civic UI Polish** | Hide raw Cedar AST syntax in Civic Transparency lens | Focuses judges on civic impact while preserving forensic audit in a dedicated drawer. | `100% SUPPORTED` | `LOW` | **YES** |

---

## 18. Recommended Hackathon Architecture

### Definitive Architectural Blueprint:
```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      CLIMORA CANONICAL PROJECT CONSOLE (ProjectPage.tsx)               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PERSPECTIVE LENSES (5):                                                                │
│ [ 🌐 Civic Transparency ]   [ 📐 Urban Planning ]      [ 🏛️ Municipal Sanction ]      │
│ [ 🚜 Field Delivery ]       [ 🔬 Independent MRV ]                                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ CONTEXTUAL BANNER:                                                                     │
│ "Active Lens: Municipal Sanction | Persona: Dr. Rajesh Patil (Municipal Commissioner)"  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TABS:                                                                                  │
│ [ Overview ] [ Spatial Allocation ] [ Baseline Evidence ] [ Budget & Finance Readiness]│
│ [ Field Implementation Log ] [ MRV & Verification ] [ Governance & Cedar Audit ]       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ CONTEXTUAL ACTIONS (Rendered based on active lens):                                    │
│ • Civic Lens:         Read-only navigation, inspect ward trees, download summary       │
│ • Planning Lens:      [ Propose Allocation Revision ] button prominent                 │
│ • Sanction Lens:      [ Sanction Project & Issue Tender ] button prominent             │
│ • Delivery Lens:      [ Record Physical Deployment ] button prominent                  │
│ • MRV Lens:           [ Certify Verification ] button prominent (gated)                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 19. Phase 2D.1 Minimum Implementation Plan (Post-Approval)

Following explicit user sign-off on this gate, Phase 2D.1 will execute the following exact, minimal, non-breaking modifications:

1. **`frontend/src/pages/ProjectPage.tsx`**:
   * Add a discreet horizontal Perspective Lens selector above the tab navigation.
   * State management: `selectedPerspective: 'civic' | 'planning' | 'sanction' | 'delivery' | 'mrv'` (default `'sanction'` or `'civic'`).
   * Selecting a lens updates the underlying `currentActorId` in `frontend/src/services/api.ts`, ensuring subsequent requests send the corresponding `X-Climora-Actor` header.
   * Filter action button prominence:
     * In `'civic'`: Show informational cards; hide mutation action buttons.
     * In `'sanction'`: Highlight Sanction Modal trigger.
     * In `'planning'`: Highlight Revision Modal trigger.
     * In `'delivery'`: Highlight Implementation Event logging.
     * In `'mrv'`: Highlight Verification Certification.
2. **`frontend/src/components/CedarGovernancePanel.tsx`**:
   * Add a collapsible toggle for raw Cedar policy AST strings so they do not dominate the visual layout.
3. **Zero Backend Changes**:
   * No edits to `services/cedar_service.py`.
   * No edits to `api/routes/projects.py`.
   * No edits to `processing/project_mrv.py`.
   * No edits to `tests/test_cedar_governance.py`.

---

## 20. Deferred Items (Explicitly Excluded)

* AWS Cognito or OAuth2 implementation.
* Real multi-tenant organization database tables.
* Funder disbursement or banking integration.
* Commercial contractor procurement or tender bidding portals.
* NGO volunteer management or community grievance portals.
* Persistent DynamoDB or S3 event store for Cedar audit records.
* Modification of any frozen Parquet or GeoTIFF data lake assets.

---

## 21. Non-Negotiable Safety Invariants Preserved

The reconciliation strictly validates and preserves:
* Existing demo actor IDs (`pmc_commissioner`, `urban_planner_lead`, `sharma_contractors`, `sgs_environmental_auditor`, `citizen_viewer`).
* Existing Cedar policy behavior and negative forbid rules.
* Existing 12-state project state machine.
* Existing frozen REST API contracts.
* Existing S3 data lake architecture and SHA-256 hashes.
* Existing ECS Express Mode backend deployment (`ap-south-1`).
* Existing Amplify frontend deployment.
* Truth hierarchy immutability: $\text{OBSERVED} \rightarrow \text{DERIVED} \rightarrow \text{MODELED} \rightarrow \text{VERIFIED}$.
* Zero client-side role trust.
* Zero state mutation on authorization denial.
* Zero synthetic-to-verified leakage.

---

## 22. System Audit & Invariant Metrics

```text
Application files modified: 0
Cedar policies modified: 0
Scientific artifacts modified: 0
Infrastructure modified: 0
Dependencies changed: 0
Files created: 1 (docs/architecture/phase-2d0r-governance-reconciliation-gate.md)
Tests run: 0 (Read-only architectural gate; test suite anchored to Phase AWS-5 pass status: 172 backend tests passed, 15 frontend tests passed)
Current system status: FROZEN, COMPATIBLE & FULLY PRESERVED
Recommended Phase 2D.1 scope: Minimum 5-Lens Perspective Selector on ProjectPage.tsx (zero backend changes)
```

---

## 23. STOP Condition & Approval Request

**STOP CONDITION MET.**  
In strict compliance with Phase 2D.0R instructions:
* No implementation of Phase 2D.1 has been started.
* No frontend code, backend code, or Cedar policy has been modified.
* No dependencies have been installed.
* All decisions are documented and frozen in this reconciliation report.

**Awaiting explicit user approval on the Formal Approval Gate (Section 17) before proceeding to Phase 2D.1.**
