# CLIMORA — Phase 2E.0 Architecture & Forensic Audit Report

## Decision Intelligence Integration Audit
### Risk Surface → API → Spatial Visualization → Scenario Optimization → Dynamic Intervention Map

---

## 1. Executive Verdict

**VERDICT: PASS WITH CONSTRAINTS**

The implementation path to close the judge-facing decision loop is fully verified and requires **zero modifications to scientific formulations, zero changes to Cedar policies, zero modifications to canonical data artifacts, zero new AWS services, and zero second optimization engines.**

The existing SciPy HiGHS MILP solver (`processing/optimization_engine.py`) already supports variable budgets in memory without mutating canonical allocations.

**Key Architectural Constraints Identified:**
1. **API Missing Surface Endpoint:** The backend currently lacks an endpoint exposing the city-wide 3,181 H3 Resolution 9 analytical mesh from `canonical_risk_surface.parquet`. Existing baseline queries strictly restrict spatial output to the 28 canonical project cells.
2. **Compute & Solver Runtime Asymmetry:** On a multi-core workstation, solving Formulation F-24.6 requires 57.2s (`mip_rel_gap=0.05`) to 104.1s (`mip_rel_gap=0.01`). On the live deployed ECS Fargate container profile (**0.25 vCPU, 512 MiB RAM** with Gunicorn `--timeout 60`), an unmanaged synchronous solve will trigger a Gunicorn worker timeout (HTTP 502/504).
3. **Dual Delivery Strategy for Judge Demonstration:** To guarantee an interactive judge demonstration without dead air or gateway timeouts, the backend must support:
   - **Pre-computed Ratified Scenario Benchmarks** (e.g., ₹2.5M, ₹5.0M, ₹7.5M, and ₹10.0M canonical) solved via the exact ratified HiGHS solver pipeline and cached with full provenance.
   - **Live Solver Invocation** with an asynchronous or dedicated timeout-protected execution path displaying a clear, honest "Optimizing with HiGHS MILP (SciPy)..." state.

---

## 2. Current Decision Loop Audit

The current system exhibits broken links in the end-to-end decision intelligence chain:

```text
CANONICAL DATA LAKE (S3)
       │  [OK] canonical_risk_surface.parquet (3,181 cells) verified via SHA-256
       ▼
RUNTIME DATA LAYER (runtime_data.py)
       │  [OK] Downloaded and cached to /tmp/climora_data_cache
       ▼
QUERY LAYER (query_layer.py)
       │  [BROKEN LINK 1] ZonalQueryEngine.query_baseline() filters all queries by
       │  get_project_cells(project_id), restricting records to ONLY the 28 canonical cells.
       ▼
FLASK API ROUTES (api/routes/projects.py)
       │  [BROKEN LINK 2] No endpoint exposes the city-wide 3,181-cell risk surface.
       │  No endpoint exists for scenario optimization (POST /scenarios/optimize).
       ▼
FRONTEND API CLIENT (frontend/src/services/api.ts)
       │  [BROKEN LINK 3] Only requests climoraApi.getBaseline() (page_size=28 default).
       ▼
EXPLORE PAGE (ExplorePage.tsx)
       │  [BROKEN LINK 4] Receives only 28 cells; lacks budget scenario controls.
       ▼
SPATIAL MAP (SpatialMap.tsx)
       │  [BROKEN LINK 5] Renders ONLY 28 isolated cells; city-wide background risk
       │  surface is completely absent; no scenario overlay styling exists.
       ▼
MILP OPTIMIZATION ENGINE (processing/optimization_engine.py)
          [ISOLATED] Highly capable in-memory solver exists, but is not connected to API.
```

---

## 3. Risk Map Root Cause Forensic Analysis

A forensic trace was performed across the complete risk data flow:

### A. S3 Canonical Risk Artifact Retrieval
- S3 Object Key: `processed/risk/canonical_risk_surface.parquet` (SHA-256: `e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677`).
- `services/runtime_data.py`: Correctly syncs the file to `/tmp/climora_data_cache/risk/canonical_risk_surface.parquet` and cryptographically verifies the SHA-256 digest against `CANONICAL_EXPECTED_HASHES`.
- `ZonalQueryEngine`: Ingests the artifact into memory during initialization as `self._dfs["risk_surface"]`.

### B. Route & Query Layer Failure Path
- In `services/query_layer.py` (`ZonalQueryEngine.query_baseline`, lines 340–355):
  ```python
  all_selected_cells = self.get_project_cells(project_id)
  ```
  Where `get_project_cells(project_id)` extracts cell IDs exclusively from `canonical_optimization_allocation.parquet`:
  ```python
  alloc_df = self._dfs["optimization_allocation"]
  return sorted(alloc_df["h3_cell_id"].unique().tolist()) # Returns exactly 28 cells
  ```
- In `services/baseline_service.py` (`BaselineDomainService.get_project_baseline`):
  The service contract explicitly states: *"Provides analytical baseline evidence across the 28 selected cells in the project footprint"*.
- In `api/routes/projects.py`:
  The only spatial endpoint exposed is `GET /projects/<project_id>/baseline`, returning only those 28 cells.
- In `frontend/src/services/api.ts`:
  `getBaseline()` defaults to `pageSize = 28`.
- In `frontend/src/pages/ExplorePage.tsx`:
  Fetches `climoraApi.getBaseline(CANONICAL_PROJECT_ID)`, storing 28 cells into state.
- In `frontend/src/components/SpatialMap.tsx`:
  Renders polygons for `cells.map(...)`. Because only 28 cells are provided, the map displays 28 tiny isolated hexagons on top of a dark Leaflet basemap. The entire rest of Pune (3,153 cells) is invisible.

**Conclusion:** The failure is NOT caused by S3 loading, CORS, Leaflet, or H3 geometry generation. It is caused by the **absence of an API endpoint and query method designed to expose the full 3,181-cell canonical risk surface**.

---

## 4. Existing Optimization Capability Audit

A forensic inspection of `processing/optimization_engine.py` was conducted:

### A. Budget Parameter Definition
- Budget is defined in Formulation F-24.6 as an upper-bound parameter:
  $$\sum_{i \in \text{Eligible}} \sum_{a \in \text{Catalog}} (F_a x_{i,a} + c_a q_{i,a}) \le B_{\text{scenario}}$$
- In code, it is accepted as `budget_inr: float` in `build_milp_model(candidate_data, budget_inr)` and assigned to matrix constraint RHS row 0:
  `rhs = np.concatenate([[budget_inr], np.zeros(2 * n_cands), ground_rhs])`.

### B. Input Flexibility
- The budget is already an explicit, dynamic parameter. It is not hardcoded.

### C. Live Variable Budget Solver Verification
The solver was experimentally executed in a clean memory space against a ₹5,000,000 budget:
- **Status:** `OPTIMAL`
- **Objective Value:** `0.055865`
- **Total Allocated Cost:** ₹4,950,500.00
- **Budget Slack:** ₹49,500.00
- **Allocated Units:** 1,323 street trees across 16 H3 cells
- **Feasibility Verification:** `validate_solution_feasibility` confirmed 100% adherence to minimum lot sizes, physical capacities, ground compatibility, and the 4.0°C cooling cap.

### D. Canonical Immutability Preservation
- The core solver functions (`build_candidate_matrix`, `build_milp_model`, `solve_milp_model`, `validate_solution_feasibility`) are **pure, in-memory Python functions**.
- They do NOT write to disk, do NOT modify S3, and do NOT touch `canonical_optimization_allocation.parquet`.
- Only the batch script orchestrator `execute_production_optimization_pipeline()` writes files, which will NOT be invoked by the scenario API.

### E. Candidate Pool Decoupling
- The candidate pool (7,115 feasible candidate pairs across 3,113 eligible cells) depends solely on `canonical_feature_matrix.parquet` and `canonical_risk_surface.parquet`.
- Building the candidate matrix takes only **35 ms**.
- Building the MILP constraint matrix takes only **34 ms**.
- Total pre-solve construction time is **under 100 ms**.

### F. Valid Budget Domain
- **Minimum Feasible Budget:** The minimum lot size for the lowest-cost intervention (`street_tree_shade`: 25 trees @ ₹3,500 = ₹87,500 + ₹20,000 mobilization = ₹107,500). Any budget below ₹107,500 yields a trivial empty allocation ($q = 0$).
- **Maximum Meaningful Budget:** Sum of maximum physical capacities across the analytical mesh (~₹25,000,000 to ₹50,000,000).
- **Recommended Validation Range:** **₹500,000 to ₹25,000,000**.
- **Recommended UI Presets:** ₹2,500,000, ₹5,000,000, ₹7,500,000, and ₹10,000,000 (canonical baseline).

---

## 5. Minimal API Design

Two lightweight, backwards-compatible endpoints close the decision loop:

### Endpoint 1: Full Risk Surface
```http
GET /projects/{project_id}/risk-surface
```
- **Purpose:** Exposes the complete 3,181-cell canonical risk surface for spatial background rendering.
- **Query Parameters:**
  - `compact` (boolean, optional, default: `true`): Returns flat numeric arrays for maximum network efficiency.
- **Authorization:** Cedar `policy_universal_view` (Action: `view_project`).
- **Response Schema:**
  ```json
  {
    "status": "SUCCESS",
    "data": {
      "project_id": "PROJ-PUNE-2025-BA225D6A",
      "total_cells": 3181,
      "eligible_cells": 3113,
      "truth_layer": "MODELED",
      "cells": [
        {
          "h3_cell_id": "89601458003ffff",
          "risk_i": 0.2874,
          "H_i": 0.512,
          "E_i": 0.621,
          "V_i": 0.903,
          "lst_2025": 46.8,
          "lst_anomaly": 1.25,
          "population_2020": 4210.5,
          "lisa_cluster": "HH",
          "is_eligible": true
        }
      ]
    }
  }
  ```
- **Network Payload:** ~280 KB uncompressed JSON; ~60 KB with Gzip compression over HTTP/2 or HTTP/1.1 TLS. Instantaneous browser download.

### Endpoint 2: Modeled Scenario Optimization
```http
POST /projects/{project_id}/scenarios/optimize
```
- **Purpose:** Executes in-memory HiGHS MILP optimization for a user-specified budget envelope.
- **Request Schema:**
  ```json
  {
    "budget_inr": 5000000.0,
    "mip_rel_gap": 0.05
  }
  ```
- **Validation:**
  - `500,000 <= budget_inr <= 25,000,000` (HTTP 400 `DomainValidationError` on violation).
- **Authorization:** Cedar `policy_universal_view` (Action: `view_project` — read-only simulation).
- **Response Schema:**
  ```json
  {
    "status": "SUCCESS",
    "data": {
      "scenario_id": "SCEN-PUNE-2025-5M-E9F1",
      "truth_layer": "MODELED",
      "is_canonical": false,
      "disclaimer": "MODELED SCENARIO ONLY. Does not represent a sanctioned, funded, or verified intervention.",
      "budget_inr": 5000000.0,
      "total_allocated_cost_inr": 4950500.0,
      "budget_slack_inr": 49500.0,
      "budget_utilization_pct": 99.01,
      "optimal_objective_value": 0.055865,
      "objective_description": "Modeled aggregate climate risk reduction (dimensionless sum of marginal responses)",
      "solver_status": "OPTIMAL",
      "solver_duration_sec": 57.23,
      "total_cells_treated": 16,
      "allocations": [
        {
          "h3_cell_id": "8960145a4a7ffff",
          "intervention_type": "street_tree_shade",
          "quantity": 82.0,
          "unit": "tree_count",
          "unit_cost": 3500.0,
          "fixed_cost": 20000.0,
          "total_cost": 307000.0,
          "modeled_cooling_degC": 0.0586,
          "marginal_risk_reduction": 0.00346,
          "baseline_risk": 0.321,
          "population_2020": 4120.0
        }
      ],
      "summary_by_intervention": {
        "street_tree_shade": {
          "total_quantity": 1323.0,
          "unit": "tree_count",
          "total_cost_inr": 4950500.0,
          "cells_count": 16
        }
      }
    }
  }
  ```

---

## 6. Minimal Frontend Design

The frontend modifications strictly preserve the Phase 2C.2R design system:

```text
ExplorePage.tsx
├── MapControls (Layer Selector: Thermal / Exposure / Risk)
├── BudgetScenarioCard (Presets: ₹2.5M, ₹5.0M, ₹7.5M, ₹10.0M | Slider | Run Button)
├── SpatialMap.tsx
│   ├── Layer 1: Dark Matter TileLayer (CartoDB)
│   ├── Layer 2: 3,181 H3 Risk Polygons (Modeled Risk Fill)
│   ├── Layer 3: 28 Canonical Footprint Polygons (Botanical Sage Border #3B7A57)
│   ├── Layer 4: Scenario Overlay Polygons (Electric Cyan Border #4CC9F0)
│   └── Layer 5: Active Cell Focus (Acid Lime Border #C8FF3B)
└── CellInspector.tsx (Contextual Evidence: H, E, V, LST, Pop, Allocations)
```

### Components Requiring Modification
1. `frontend/src/services/api.ts`: Add `getRiskSurface()` and `optimizeScenario()`.
2. `frontend/src/types/api.ts`: Define `RiskSurfaceResponse`, `ScenarioOptimizeRequest`, and `ScenarioOptimizeResponse`.
3. `frontend/src/pages/ExplorePage.tsx`:
   - Ingest risk surface data alongside canonical baseline.
   - Maintain active scenario state and loading state.
   - Embed quiet budget scenario control card.
4. `frontend/src/components/SpatialMap.tsx`:
   - Render the complete 3,181-cell analytical mesh using `cellToBoundary()` from `h3-js`.
   - Separate visual styling of background risk surface vs. canonical footprint vs. dynamic scenario overlay.
5. `frontend/src/components/CellInspector.tsx`:
   - Display cell baseline metrics, LISA cluster, canonical allocation, and scenario allocation.

---

## 7. Scenario Architecture

To preserve scientific and governance truth, experimental scenarios must remain strictly separated from canonical project data:

```text
┌──────────────────────────────────────────────────────────────┐
│                    CANONICAL PROJECT                         │
│  - Project ID: PROJ-PUNE-2025-BA225D6A                       │
│  - Optimization Run: OPT-PUNE-2025-SCENARIO-BA225D6A         │
│  - Budget: ₹10,000,000 (Immutable)                           │
│  - Allocation: 28 Cells / 2,695 Trees / ₹9,992,500 Cost      │
│  - Parquet SHA-256: 2519473a32a2b4a3a22bc8beb43525c3f...     │
│  - Lifecycle State: PROPOSED / FUNDED / etc.                │
└──────────────────────────────────────────────────────────────┘
                               │
                      NO STATE CROSSOVER
                               │
┌──────────────────────────────────────────────────────────────┐
│                     MODELED SCENARIO                         │
│  - Ephemeral / Client-requested                              │
│  - Run ID: SCEN-PUNE-2025-{BUDGET}-{HASH}                   │
│  - Budget: Dynamic (e.g., ₹5,000,000)                        │
│  - Allocation: In-memory only (e.g., 16 Cells / 1,323 Trees) │
│  - Zero S3 mutation / Zero Parquet overwrite                 │
│  - Zero lifecycle transitions / Zero funding commitments     │
│  - Truth Layer: Strictly MODELED                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Map Visualization Architecture

Following the Phase 2C.2R quiet aesthetic system:

| Map Visual Element | Data Source | Styling Specification | Visual Role |
| :--- | :--- | :--- | :--- |
| **City-wide Risk Mesh** | `canonical_risk_surface.parquet` (3,181 cells) | Fill opacity: 0.25–0.50 (Ochre / Terracotta / Slate cyan). Border: Hairline `rgba(242, 244, 239, 0.08)`, width 0.5px. | Analytical backdrop showing spatial distribution of risk. |
| **Canonical Allocation** | `canonical_optimization_allocation.parquet` (28 cells) | Border: Botanical Sage (`#3B7A57`), width 2px, solid. Fill opacity: +0.15. | Approved project footprint. |
| **Active Scenario** | HiGHS Scenario Result (e.g., 16 cells for ₹5M) | Border: Electric Cyan (`#4CC9F0`), width 2px, dashed/accent. Fill: subtle cyan tint. | Modeled scenario overlay. |
| **Active Cell Selection** | User click on any cell | Border: Acid Lime (`#C8FF3B`), width 3px. Fill opacity: 0.75. | Active inspection target (<0.5% screen area). |

---

## 9. Governance Decision

- **Cedar Policy Impact:** **ZERO changes to Cedar policies.**
- **Enforcement Mapping:**
  - Scenario optimization is an analytical simulation that does not mutate canonical data or project state.
  - Evaluated against Action `Action::"view_project"` under `@id("policy_universal_view")`, which permits all principals (Citizens, Officers, Contractors, Verifiers, Viewers) to simulate scenarios.
  - The architectural immutability guardrail `@id("policy_forbid_canonical_mutation")` guarantees that scenario outputs can never be written into canonical tables or S3 objects.
  - If a Project Manager wishes to turn a modeled scenario into an official revision, they must explicitly submit it via `POST /projects/{id}/revisions` (`Action::"propose_revision"`).

---

## 10. Performance Assessment & Solver Mitigation

### Empirical Performance Measurements
- In-memory data load (`load_canonical_inputs`): **43 ms**
- Candidate matrix generation (`build_candidate_matrix`): **35 ms**
- MILP matrix construction (`build_milp_model`): **34 ms**
- Total pre-solve overhead: **112 ms**
- HiGHS MILP Solver (`solve_milp_model`):
  - Workstation (16-thread CPU), Budget ₹5.0M, `gap = 0.05`: **57.23 seconds**
  - Workstation, Budget ₹5.0M, `gap = 0.01`: **104.14 seconds**
  - Canonical Workstation run, Budget ₹10.0M, `gap = 0.01`: **70.13 seconds**

### Deployed Environment Reality (ECS Fargate)
- ECS Task Compute Profile: **0.25 vCPU (256 CPU units), 512 MiB RAM**.
- Gunicorn WSGI Timeout: **60 seconds** (`--timeout 60`).
- **Critical Risk:** A live MILP solve on 0.25 vCPU would take >200 seconds, causing Gunicorn to terminate the worker with HTTP 502/504 Bad Gateway.

### Recommended Mitigation Strategy (Two-Tier Response)
1. **Tier 1: Pre-computed Ratified Scenarios (Instantaneous, < 100 ms):**
   - Pre-solve the exact HiGHS MILP formulation for four canonical benchmark envelopes:
     - ₹2,500,000 (50% reduction)
     - ₹5,000,000 (Target scenario)
     - ₹7,500,000 (Intermediate scenario)
     - ₹10,000,000 (Canonical baseline comparison)
   - Store results in `data/processed/optimization/scenarios/` with full provenance manifests.
   - When a judge selects one of these benchmark presets, the response is served instantaneously with 100% solver fidelity.
2. **Tier 2: Live Solver Execution for Custom Budgets:**
   - For arbitrary custom budgets (e.g., ₹6,250,000), execute `solve_milp_model()` with `time_limit_sec = 45.0` and `mip_rel_gap = 0.05` to guarantee completion within Gunicorn's 60s timeout, or run asynchronously.

---

## 11. Security Assessment

1. **Input Validation:** Strict Pydantic schema on `POST /scenarios/optimize`:
   - `budget_inr`: Float clamped to `[500000.0, 25000000.0]`.
   - `time_limit_sec`: Float clamped to `[5.0, 45.0]`.
   - Rejects NaN, negative, non-numeric, or out-of-bound values with structured HTTP 400 errors.
2. **Resource Exhaustion Guard:** Clamping solver time limit prevents CPU denial-of-service.
3. **Immutability Guard:** Scenario logic has zero file-write permissions to S3 or `data/processed/`.
4. **CORS:** Handled via existing Flask CORS middleware configured for Amplify origin.

---

## 12. Scientific Integrity Assessment

1. **Formulation Invariant:** Formulations F-01 through F-28, F-24.1 through F-24.6, and F-25.1 remain 100% frozen.
2. **No Approximate Heuristic:** Scenarios are solved using the exact ratified HiGHS branch-and-cut MILP solver.
3. **Semantic Honesty:**
   - Objective value ($0.106048$ or $0.055865$) is strictly described as:
     *"Modeled optimization objective (dimensionless sum of marginal risk responses)"*.
   - Never presented as "10.6% temperature reduction" or "5.6% cooling".
   - Interventions use physical units (`trees` for street trees, `m²` for cool roofs).
   - Truth layer is explicitly labeled `MODELED`.

---

## 13. Exact Implementation File Plan (Phase 2E.1)

| File | Change | Reason | Risk |
| :--- | :--- | :--- | :--- |
| `services/query_layer.py` | Add `query_risk_surface(project_id)` method to `ZonalQueryEngine`. | Exposes 3,181 cells of `canonical_risk_surface.parquet` without modifying baseline queries. | Very Low; additive query method. |
| `services/allocation_service.py` | Add `solve_scenario(budget_inr)` method invoking `solve_milp_model`. | Provides domain-layer orchestration for in-memory scenario optimization. | Very Low; pure in-memory execution. |
| `api/routes/projects.py` | Add `GET /projects/{id}/risk-surface` and `POST /projects/{id}/scenarios/optimize`. | Exposes API contracts to frontend. | Low; protected by Cedar & Pydantic. |
| `frontend/src/services/api.ts` | Add `getRiskSurface()` and `optimizeScenario()` client methods. | Connects frontend to new endpoints. | Very Low; standard fetch wrappers. |
| `frontend/src/types/api.ts` | Add TypeScript interfaces for risk surface and scenario contracts. | Type safety across components. | Zero; compile-time types only. |
| `frontend/src/pages/ExplorePage.tsx` | Fetch risk surface; integrate budget scenario control and state. | Allows judge to observe risk and trigger scenario recalculations. | Low; uses standard React state. |
| `frontend/src/components/SpatialMap.tsx` | Render 3,181 background risk cells and dynamic scenario overlay. | Closes spatial visualization gap. | Low; uses existing `h3-js` & Leaflet. |
| `frontend/src/components/CellInspector.tsx` | Display cell baseline indicators, LISA cluster, and scenario status. | Provides full cell-level evidence drilldown. | Zero; presentation only. |

---

## 14. Test Plan

### Backend Test Plan
1. `tests/test_phase_2e_risk_surface_api.py`:
   - `test_risk_surface_endpoint_returns_3181_cells`: Verifies cell count, column presence ($H, E, V, \text{risk}$), and HTTP 200.
   - `test_risk_surface_unmodified_sha256`: Confirms parity with frozen S3 artifact.
2. `tests/test_phase_2e_scenario_api.py`:
   - `test_scenario_optimization_5m_budget`: Validates feasibility, ₹4.95M cost, 16 cells, and `status == "OPTIMAL"`.
   - `test_scenario_optimization_immutability`: Confirms canonical allocation parquet SHA-256 remains bitwise identical before and after scenario solve.
   - `test_scenario_budget_boundary_validation`: Validates HTTP 400 on budget < ₹500,000 or > ₹25,000,000.

### Frontend Test Plan
1. `frontend/src/tests/riskSurfaceMap.test.tsx`:
   - Verifies that `SpatialMap` renders city-wide background polygons.
   - Verifies that scenario overlays render in distinct styling.
2. `frontend/src/tests/scenarioBudgetControls.test.tsx`:
   - Verifies budget preset selection, slider interaction, and loading state during optimization.

---

## 15. Deployment Plan

1. **ECS Express Backend Deployment:**
   - Build updated container tag `v1.2.0` (with risk surface & scenario endpoints).
   - Push to Amazon ECR `434658845459.dkr.ecr.ap-south-1.amazonaws.com/climora-api:latest`.
   - Update ECS Express service `climora-api` via AWS CLI / CloudFormation.
   - Verify zero-downtime rolling update via `/health`.
2. **Amplify Frontend Deployment:**
   - Run `npm run build` in `frontend/`.
   - Deploy build artifact to AWS Amplify via existing pipeline.
   - Verify live HTTPS endpoint `https://main.dipd0dx7w10zl.amplifyapp.com`.

---

## 16. Judge Demo Flow (5–7 Minute Walkthrough)

1. **Minute 1: The Macro Problem (City Risk Map)**
   - Judge lands on **Explore**.
   - Instead of 28 isolated cells, the judge sees the complete **Pune Heat Risk Surface (3,181 H3 cells)**.
   - Demonstrates the thermal hotspot concentration in central and eastern Pune.
2. **Minute 2: Cell Evidence & Explainability**
   - Judge clicks on a high-risk cell in Nana Peth / Bhavani Peth.
   - Inspector displays: Peak LST ($47.2^\circ\text{C}$), Hazard ($0.58$), Exposure ($0.74$), Vulnerability ($0.91$), LISA "High-High" cluster.
3. **Minute 3: Canonical Baseline Recommendation**
   - Judge views the canonical project footprint (28 cells, ₹10M budget, 2,695 street trees).
   - Explains that this is the approved, immutable municipal plan.
4. **Minute 4: Interactive Scenario Optimization ("What If Budget Changes?")**
   - Judge asks: *"What if municipal budget is cut in half to ₹5,000,000?"*
   - Judge selects the **₹5.0M** preset and clicks **Run Scenario**.
   - UI displays optimization diagnostics from the HiGHS branch-and-cut solver.
5. **Minute 5: Spatial Portfolio Reallocation**
   - Map instantly renders the new **Scenario Intervention Overlay (16 cells, 1,323 trees, ₹4.95M cost)** in Electric Cyan overlaying the canonical Sage footprint.
   - Judge clearly sees which 16 cells remain prioritized and which 12 drop out under budget scarcity.
6. **Minute 6: Truth-Layer & Governance Discipline**
   - Judge observes the explicit `MODELED SCENARIO` banner confirming zero mutation of canonical municipal records or funding status.

---

## 17. Explicit Non-Goals

The implementation will NOT create:
- A second optimization engine or heuristic solver.
- GIS servers, Tilezen, GeoServer, or spatial SQL databases.
- Synthetic scientific datasets or altered physical coefficients.
- New AWS services (Lambda, DynamoDB, RDS, etc.).
- New Cedar authorization policies.
- Multi-user scenario sharing, collaboration, or versioning databases.

---

## 18. Decision Gates (D1 through D14)

### D1: Root Cause of Risk-Map Failure
- **Finding:** Missing API endpoint and query method for the 3,181-cell canonical risk surface. Existing baseline service was strictly designed to return the 28 project cells.

### D2: Can Canonical Risk Artifact Support the Map Directly?
- **Finding:** **YES.** `canonical_risk_surface.parquet` contains all necessary attributes ($H, E, V, \text{risk}$, LST, anomaly, population, eligibility) and compresses to ~60 KB over HTTP.

### D3: Exact API Contract Required
- **Finding:**
  - `GET /projects/{project_id}/risk-surface`
  - `POST /projects/{project_id}/scenarios/optimize`

### D4: Can Existing Optimization Engine Accept Arbitrary Valid Budgets?
- **Finding:** **YES.** Formulation F-24.6 and `build_milp_model()` natively treat budget as a linear RHS constraint.

### D5: Can Existing Engine Produce Isolated Modeled Scenarios?
- **Finding:** **YES.** Underlying solver functions execute entirely in memory and return structured dictionaries without disk or S3 side-effects.

### D6: Valid Budget Range
- **Finding:** **₹500,000 to ₹25,000,000**. Feasibility boundary is ₹107,500 (minimum lot size).

### D7: Measured Scenario Runtime
- **Finding:**
  - Pre-solve: 112 ms.
  - HiGHS Solver: 57.2s (`mip_rel_gap = 0.05`) to 104.1s (`mip_rel_gap = 0.01`).

### D8: Exact Map Layers Required
- **Finding:**
  1. Dark Matter TileLayer
  2. 3,181-cell Risk Surface Fill
  3. 28-cell Canonical Footprint Border (`#3B7A57`)
  4. Modeled Scenario Overlay Border (`#4CC9F0`)
  5. Selected Cell Active Focus Border (`#C8FF3B`)

### D9: Exact Frontend Files to Change
- **Finding:** `frontend/src/services/api.ts`, `frontend/src/types/api.ts`, `frontend/src/pages/ExplorePage.tsx`, `frontend/src/components/SpatialMap.tsx`, `frontend/src/components/CellInspector.tsx`.

### D10: Cedar Governance Capability
- **Finding:** Reuses existing `Action::"view_project"` under `@id("policy_universal_view")`. Zero Cedar policy modifications required.

### D11: Scientific Formulation Requirement
- **Finding:** **NO new formulation required.** Reuses ratified F-24.1 through F-24.6 and F-25.1.

### D12: Smallest Implementation for Full Decision Loop
- **Finding:** Add two Flask routes (`/risk-surface` and `/scenarios/optimize`), update frontend API client, and enhance `SpatialMap.tsx` and `ExplorePage.tsx` with layer separation and budget presets.

### D13: Static Canonical Invariants
- **Finding:** Project `PROJ-PUNE-2025-BA225D6A`, canonical budget ₹10,000,000, 28 cells, 2,695 trees, ₹9,992,500 cost, objective $0.106048$, SHA `2519473...`, all 5 Parquet files, Cedar policies, and S3 objects.

### D14: Recommended Implementation Order
- **Finding:**
  1. Implement risk surface query method and `GET /risk-surface` route.
  2. Update frontend API client and render full 3,181-cell risk map in `SpatialMap.tsx`.
  3. Render canonical 28-cell intervention overlay cleanly on the risk surface.
  4. Implement `POST /scenarios/optimize` reusing in-memory `solve_milp_model()`.
  5. Add budget scenario control card and dynamic scenario overlay rendering.
  6. Add unit and integration tests.
  7. Deploy to ECS and Amplify.
