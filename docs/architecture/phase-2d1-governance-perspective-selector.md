# CLIMORA — PHASE 2D.1: Authorization–Workspace Separation & Minimal Perspective Selector Implementation Report

**Document Version:** 1.0.0-FINAL  
**Status:** IMPLEMENTED, TESTED, VERIFIED & FROZEN  
**Phase:** Phase 2D.1 (Frontend Perspective Lenses & Authorization Decoupling)  
**Precondition:** Phase 2D.0R Ratified Architecture & Decision Gate  
**Date:** 2026-10-06  
**Target Artifact:** [`docs/architecture/phase-2d1-governance-perspective-selector.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-2d1-governance-perspective-selector.md)

---

## 1. Executive Implementation Summary

Phase 2D.1 successfully implements the **Authorization–Workspace Separation & Minimal Perspective Selector** within the canonical CLIMORA project console ([`frontend/src/pages/ProjectPage.tsx`](file:///c:/Users/lenovo/climora/frontend/src/pages/ProjectPage.tsx)) in strict accordance with the decisions ratified in Phase 2D.0R.

### Core Achievements
1. **Critical Security Reconciliation (Option A Fully Enforced):**
   * Solved the potential contradiction between D9 (*"Workspace selection must never affect authorization"*) and D11 (*"Perspective selector syncs demo actor"*).
   * Formally decoupled **Presentation (Perspective Lens)** from **Authorization (Demo Governance Persona)**:
     $$\text{Actor Identity} \longrightarrow \text{Server-Side Cedar Authorization}$$
     $$\text{Perspective Lens} \longrightarrow \text{Client-Side Presentation \& Action Prominence}$$
     $$\text{NEVER: Lens} \longrightarrow \text{Actor Identity} \longrightarrow \text{Authorization}$$
   * Selecting or switching a Perspective Lens modifies view emphasis and default tab focus only; it **NEVER mutates `currentActorId` or `X-Climora-Actor`**.
2. **Exactly Five (5) Perspective Lenses Implemented:**
   * **Civic Transparency** (`civic`): Public accountability, open canopy allocations, and verified cooling audit. Technical mutation controls are de-emphasized.
   * **Urban Planning** (`planning`): Spatial evidence, H3 cell prioritization, and allocation branch revision triggers.
   * **Municipal Sanction** (`sanction`): Standing Committee capital budget sanction and statutory tender authorization panel.
   * **Field Delivery** (`delivery`): Licensed EPC sapling procurement, roadside digging, and batch deployment quantities.
   * **Independent MRV** (`mrv`): ISO 14064-2 accredited audit, Landsat satellite QA, 5 mandatory QC criteria, and Difference-in-Differences gates.
3. **Explicit Demo Governance Persona Bar:**
   * Prominently labeled at the top of the project console:
     `DEMO GOVERNANCE PERSONA (Simulated actor for server-side Cedar evaluation · Not production authentication)`.
   * Displays the active principal identity and role (e.g., `Role::"municipal_officer"`).
   * Provides an optional one-click helper (*"Align simulated persona to [Suggested Name] →"*) if the user voluntarily wishes to align the simulated persona with the active presentation lens.
4. **Green Finance Readiness & Capital Diligence Case:**
   * Implemented in the `Budget & Finance Readiness` tab without fabricating non-existent funder roles, banking transactions, or disbursement models.
   * Exposes pre-calculated bankability metrics: ₹9,992,500 CAPEX, ₹10,000,000 budget envelope, ₹7,500 slack reserve, ₹84.01 CAPEX per beneficiary across 118,941 residents, and ISO 14064-2 MRV protocol alignment.
5. **Zero Backend & Cedar Impact:**
   * **Application code modified:** `0` backend files.
   * **Cedar policies modified:** `0` policies. All 7 compiled policies remain 100% frozen.
   * **Scientific artifacts modified:** `0` files. Canonical Parquet SHA-256 hashes preserved.
   * **AWS infrastructure modified:** `0` changes. Live ECS and Amplify production deployments verified.

---

## 2. Authorization / Lens Separation Decision (Option A)

### 2.1 The Security Vulnerability Prevented
If switching a presentation lens automatically mutated the client's `X-Climora-Actor` header, the frontend lens selector would become a de facto client-side authorization escalator. For example, a citizen navigating to the "Municipal Sanction" tab could inadvertently be granted Municipal Commissioner credentials in transit.

### 2.2 Reconciled Option A Architecture
CLIMORA implements **pure Option A**:
* **Presentation State:** `selectedLens: 'civic' | 'planning' | 'sanction' | 'delivery' | 'mrv'`. Managed as local React state in [`frontend/src/pages/ProjectPage.tsx`](file:///c:/Users/lenovo/climora/frontend/src/pages/ProjectPage.tsx). Controls which tabs are highlighted and whether mutation triggers are displayed.
* **Authorization Principal State:** `currentActor: string`. Managed in [`frontend/src/services/api.ts`](file:///c:/Users/lenovo/climora/frontend/src/services/api.ts). Injected into every outbound HTTP request as `X-Climora-Actor: <actor_id>`.
* **Zero Cross-Leakage:** Calling `handleLensChange(lensId)` executes:
  ```typescript
  setSelectedLens(lensId);
  const def = PERSPECTIVES.find((p) => p.id === lensId);
  if (def) {
    setActiveTab(def.defaultTab);
  }
  // CRITICAL: currentActorId is untouched!
  ```
* **Server-Side Security Proof:** If a user views the console through the **Municipal Sanction** lens while their Demo Persona is set to **Ananya Joshi (`citizen_viewer`)**, clicking *"Sanction project & issue tender"* dispatches a request with `X-Climora-Actor: citizen_viewer`.
  Amazon Cedar evaluates Policy 3 (`@id("policy_officer_approve_project")`):
  `principal in Role::"municipal_officer"` evaluates to `false`.
  The server responds with **HTTP 403 Forbidden**, logs structured diagnostics, and causes **zero state mutation** (formally verified in `tests/test_cedar_governance.py`).

---

## 3. Exact Files Modified & Created

### 3.1 Files Modified
1. [`frontend/src/pages/ProjectPage.tsx`](file:///c:/Users/lenovo/climora/frontend/src/pages/ProjectPage.tsx):
   * Added the 5 Perspective Lenses selector bar (`PERSPECTIVES`).
   * Added the top Demo Governance Persona Bar with independent actor dropdown (`DEMO_PERSONAS`).
   * Enforced Option A decoupling (lens selection adjusts presentation only).
   * Contextually tailored the Municipal Sanction panel (prominent in `sanction`, read-only accountability summary in `civic`).
   * Contextually tailored the Allocation blueprint table (revision branch buttons hidden in `civic`, prominent in `planning`).
   * Added the Green Finance Readiness & Capital Diligence card in the `Budget & Finance Readiness` tab.
2. [`frontend/src/components/CedarGovernancePanel.tsx`](file:///c:/Users/lenovo/climora/frontend/src/components/CedarGovernancePanel.tsx):
   * Subscribed to `onActorChange` to synchronize with external persona changes.
   * Updated the header label to read: `DEMO GOVERNANCE PERSONA SWITCHER (Simulated Principal Identity · Not Production Authentication)`.
3. [`frontend/src/services/api.ts`](file:///c:/Users/lenovo/climora/frontend/src/services/api.ts):
   * Added `onActorChange` subscription listener pattern to notify components when `setCurrentActor()` is called.
4. [`tests/test_cedar_governance.py`](file:///c:/Users/lenovo/climora/tests/test_cedar_governance.py):
   * Added explicit backend test suite covering **Tests A through J** validating workspace-authorization decoupling.

### 3.2 Files Created
1. [`frontend/src/tests/perspectiveSelector.test.tsx`](file:///c:/Users/lenovo/climora/frontend/src/tests/perspectiveSelector.test.tsx):
   * Unit and integration test suite (6 tests) verifying all 5 perspective lenses, Option A decoupling, civic de-emphasis, municipal sanction emphasis, and Finance Readiness rendering.
2. [`docs/architecture/phase-2d1-governance-perspective-selector.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-2d1-governance-perspective-selector.md):
   * Exactly this comprehensive implementation report.

---

## 4. Cedar & API Impact Audit

| System Boundary | Changes Made | Verification Status |
| :--- | :---: | :--- |
| **Amazon Cedar Policy Set** | `0` | All 7 compiled Cedar policies in `services/cedar_service.py:L33-L118` remain 100% frozen. |
| **Backend REST Endpoints** | `0` | Zero changes to endpoints, query schemas, or response envelopes. |
| **Project State Machine** | `0` | 12 lifecycle states and gating rules in `processing/project_mrv.py:L242-L311` remain 100% frozen. |
| **S3 Scientific Data Lake** | `0` | Canonical parquets and GeoTIFFs remain byte-for-byte immutable. |
| **AWS Cloud Infrastructure** | `0` | ECS Fargate Express Mode (`ap-south-1`) and Amplify Hosting intact. |

---

## 5. Frontend Presentation & User Experience Architecture

### 5.1 Perspective Lenses Breakdown

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CLIMORA CANONICAL PROJECT CONSOLE                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ASIDE: DEMO GOVERNANCE PERSONA                                                         │
│ [ DEMO GOVERNANCE PERSONA ] Simulated actor for server-side Cedar evaluation          │
│ Active Actor: [ Dr. Rajesh Patil — Municipal Sanctioning Authority (PMC) ▾ ] Role::"municipal_officer"
├────────────────────────────────────────────────────────────────────────────────────────┤
│ HEADER: PROJ-PUNE-2025-BA225D6A [ PROPOSED ]                                           │
│ Pune Urban Heat Island Mitigation & Street Canopy Initiative                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PERSPECTIVE LENSES (Presentation Filter):                                              │
│ [ 🌐 Civic Transparency ]   [ 📐 Urban Planning ]      [ 🏛️ Municipal Sanction ● ]     │
│ [ 🚜 Field Delivery ]       [ 🔬 Independent MRV ]                                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ ACTIVE PRESENTATION FOCUS: Municipal Sanction                                          │
│ Standing Committee capital budget sanction & statutory tender authorization            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TABS:                                                                                  │
│ [ Overview ] [ Governance (Cedar) ] [ Allocation ] [ Baseline ]                        │
│ [ Budget & Finance Readiness ] [ Verification ] [ Provenance ]                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Contextual Lens Behavior Matrix

| Lens | Default Tab | Visible Emphasis | Action Button Prominence | De-emphasized Elements |
| :--- | :---: | :--- | :--- | :--- |
| **1. Civic Transparency** | `overview` | Public purpose, canopy tree counts (2,695), treated area (28 cells), public budget, verified cooling status. | Mutation buttons omitted or replaced with *"Public Record (Read-Only)"*. Direct link to Cedar audit drawer. | Raw Cedar policy AST strings, branch revision buttons, tender sanction buttons. |
| **2. Urban Planning** | `allocation` | H3 cell prioritization, unit tree allocations, thermodynamic constraints, candidate pairs. | **[ Propose Revision ]** and row-level **[ Branch Revision ]** prominent. | Municipal sanction buttons. |
| **3. Municipal Sanction** | `overview` | ₹10M statutory envelope, ₹9.99M CAPEX, ₹7.5k slack, statutory tender mandate. | **[ Sanction Project & Issue Tender ]** prominent with accent border. | Ground digging batch logs. |
| **4. Field Delivery** | `allocation` | Quotas per cell, mobilization fixed costs (₹20,000/cell), tree intervals (15.0m), planting logistics. | Physical scope tables and mobilization receipts prominent. | Sanction approval modals, policy rule syntax. |
| **5. Independent MRV** | `verification` | Landsat 9 TIRS thermal observations, DOY 105±15 window, <5% cloud cover, 5 QC criteria. | **[ Certify Verification ]** (honestly gated until post-monsoon pass). | Pre-sanction revision tools. |

---

## 6. Verification of Tests A through J

The test suite in [`tests/test_cedar_governance.py`](file:///c:/Users/lenovo/climora/tests/test_cedar_governance.py) was augmented with explicit tests for all mandatory requirements:

| Test ID | Test Function | Verified Behavior | Result |
| :---: | :--- | :--- | :---: |
| **Test A** | `test_phase_2d1_test_a_workspace_lens_does_not_grant_authorization` | Supplying `X-Climora-Workspace: municipal_sanction` or `?lens=sanction` with `citizen_viewer` is strictly **DENIED** (HTTP 403, zero mutation). | `PASSED` |
| **Test B** | `test_phase_2d1_test_b_citizen_unable_to_sanction` | Citizen attempting project approval is strictly **DENIED** by Cedar Policy 3. | `PASSED` |
| **Test C** | `test_phase_2d1_test_c_planner_retains_permitted_actions` | Urban Planner proposing allocation revision is **ALLOWED** (HTTP 201) under Cedar Policy 2. | `PASSED` |
| **Test D** | `test_phase_2d1_test_d_municipal_authority_retains_sanction` | Municipal authority retains sanction capability in `PROPOSED` state (Cedar Policy 3). | `PASSED` |
| **Test E** | `test_phase_2d1_test_e_contractor_retains_implementation_capability` | Contractor implementation is **DENIED** in `PROPOSED` and **ALLOWED** in `IMPLEMENTING` (Policy 4). | `PASSED` |
| **Test F** | `test_phase_2d1_test_f_mrv_auditor_retains_verification_capability` | Auditor verification is **DENIED** when QC fails; **ALLOWED** when state is `MONITORING` and QC passes (Policy 6). | `PASSED` |
| **Test G** | `test_phase_2d1_test_g_no_lens_or_actor_can_mutate_canonical_truth` | Negative Policy 7 unconditionally forbids all actors from mutating canonical allocation parquet. | `PASSED` |
| **Test H** | `test_phase_2d1_test_h_workspace_selection_cannot_mutate_state` | Reading project with workspace/lens parameters causes zero state mutation. | `PASSED` |
| **Test I** | `test_phase_2d1_test_i_arbitrary_actor_defaults_to_least_privilege_viewer` | Unrecognized actor string (`unregistered_external_attacker`) defaults to `viewer` role; privileged calls return HTTP 403. | `PASSED` |
| **Test J** | `test_phase_2d1_test_j_mrv_restrictions_unchanged_synthetic_rejected` | Anti-contamination invariant blocks synthetic demo fixtures from certifying canonical projects to `VERIFIED`. | `PASSED` |

---

## 7. Test Execution Results

### 7.1 Frontend Test Suite
Executed via Vitest (`npm test -- --run`):
```text
Test Files  8 passed (8)
     Tests  21 passed (21)
  Duration  1.88s
Status: 100% GREEN (Zero failures, zero regressions)
```

### 7.2 Frontend Production Build
Executed via Vite (`npm run build`):
```text
✓ 93 modules transformed.
dist/index.html                   1.29 kB │ gzip:   0.70 kB
dist/assets/index-CUqLmwyN.css    2.67 kB │ gzip:   1.13 kB
dist/assets/index-DIhfIGP2.js   650.00 kB │ gzip: 185.65 kB
✓ built in 10.04s
Status: PRODUCTION BUNDLE VALIDATED
```

### 7.3 Backend Cedar Governance Suite
Executed via Pytest (`py -3.13 -m pytest tests/test_cedar_governance.py -v`):
```text
tests/test_cedar_governance.py: 22 passed in 1.64s
Status: 100% GREEN (Zero failures, zero regressions)
```

---

## 8. Canonical Invariants Preserved

| Canonical Invariant | Authoritative Value | Verified Status |
| :--- | :--- | :---: |
| **Canonical Project ID** | `PROJ-PUNE-2025-BA225D6A` | `PRESERVED` |
| **Optimization Run ID** | `OPT-PUNE-2025-SCENARIO-BA225D6A` | `PRESERVED` |
| **Prioritized Geography** | 28 H3 Resolution 9 Cells (~2.76 km²) | `PRESERVED` |
| **Physical Scope** | 2,695 Indigenous Street Trees (15.0m interval) | `PRESERVED` |
| **Modeled CapEx** | ₹9,992,500 INR | `PRESERVED` |
| **Statutory Envelope** | ₹10,000,000 INR | `PRESERVED` |
| **Retained Slack** | ₹7,500 INR | `PRESERVED` |
| **Beneficiary Population** | 118,941.21 exact / 118,941 display | `PRESERVED` |
| **Objective Score** | 0.10604830270054796 | `PRESERVED` |
| **Allocation Parquet Hash** | `2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555` | `PRESERVED` |
| **Truth-Layer Sequence** | $\text{OBSERVED} \rightarrow \text{DERIVED} \rightarrow \text{MODELED} \rightarrow \text{VERIFIED}$ | `PRESERVED` |

---

## 9. Live Cloud Deployment Status

* **AWS ECS Express Mode Backend:**
  URL: `https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws/health`  
  Status: `HEALTHY` (Phase AWS-3, containerized, S3-integrated data lake).
* **AWS Amplify Production Frontend:**
  URL: `https://main.dipd0dx7w10zl.amplifyapp.com`  
  Status: `ACTIVE` (HTTP 200 OK, Leaflet + Geist typography).

---

## 10. Remaining Limitations & Non-Goals

1. **Simulated Identity Context:** Demo persona switching is explicitly a hackathon demonstration mechanism for testing server-side Amazon Cedar policies. It does NOT represent enterprise IAM, SSO, or user login.
2. **Finance Readiness Scope:** The Green Finance Readiness view provides capital diligence structuring for municipal green bonds; it does NOT execute bank wire transfers or financial disbursements.
3. **No Dynamic Multi-Tenancy:** The platform operates on the canonical Pune Municipal Corporation demonstration scope. Multi-tenant administrative RBAC remains a post-hackathon extension.

---

## 11. Final Phase Conclusion & STOP Condition

**STOP CONDITION SATISFIED.**
* Phase 2D.1 implementation is complete, verified, and frozen.
* Zero changes made to scientific calculations, database layers, Cedar policies, or AWS infrastructure.
* Ready for hackathon presentation and judge evaluation.
