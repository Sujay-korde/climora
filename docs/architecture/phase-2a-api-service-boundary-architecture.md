# CLIMORA — PHASE 2A ARCHITECTURAL GATE REPORT
## Production API & Service Boundary Architecture

**Phase:** Phase 2A  
**Status:** PASSED — SERVICE BOUNDARY ARCHITECTURE RATIFIED  
**Date:** October 2026  
**Auditors & Roles:** Principal Systems Architect, Backend Architect, Geospatial Platform Engineer, Scientific Data Engineer, API Governance Engineer  

---

## 1. EXECUTIVE SUMMARY

Phase 2A establishes the first production-grade application and API service boundary enclosing the frozen CLIMORA scientific and data intelligence system.

In strict compliance with non-negotiable architectural mandates:
1. **Zero Scientific Recalculation:** The Phase 2 API is NOT a second implementation of CLIMORA's scientific logic. The canonical pipeline (`OBSERVED -> DERIVED -> FEATURE MATRIX -> HEV -> RISK -> SPATIAL AUTOCORRELATION -> OPTIMIZATION -> PROJECT -> IMPLEMENTATION -> MRV -> VERIFICATION`) remains authoritative. The API strictly exposes these precomputed canonical results and does not silently alter them.
2. **Three-Tier Boundary Architecture:** Cleanly isolates:
   - **Layer A (Scientific/Data Layer):** Canonical Parquet and JSON lake assets (`data/processed/`, `data/manifests/`).
   - **Layer B (Application/Domain Layer):** Encapsulates project lifecycle, allocation immutability, revision branching, operational deviation calculations, and MRV verification state machines (`services/`).
   - **Layer C (API Layer):** Lightweight Flask HTTP routing, Pydantic v2 serialization, structured error envelopes, and OpenAPI 3.0 documentation (`api/`).
3. **Frozen Canonical Pune Demonstration Baseline:** Permanently freezes project identity (`PROJ-PUNE-2025-BA225D6A`), optimization lineage (`OPT-PUNE-2025-SCENARIO-BA225D6A`), 28 H3 Res9 cells, 2,695 street trees, ₹9,992,500 modeled CapEx, ₹10,000,000 budget envelope, ₹7,500 budget slack, exact 118,941.21 protected population, and modeled objective reduction score of 0.10604830270054796.
4. **Strict Truth-Layer Taxonomy:** Every exposed metric carries explicit metadata (`OBSERVED`, `DERIVED`, `MODELED`, `VERIFIED`). Modeled microclimatic effects are quarantined from verified impact fields. Verified impact remains null/unobserved until empirical post-deployment verification.
5. **Rigorous MRV & Verification Safety:** State machine transitions to `VERIFIED` are algorithmically guarded by multi-tier prerequisites. Synthetic demo fixtures (`DEMO_ONLY_SYNTHETIC_MRV_DATA`) and incompatible optical sensors (Sentinel-2 MSI for thermal LST) are outright rejected.

---

## 2. SERVICE BOUNDARY ARCHITECTURE

```
+---------------------------------------------------------------------------------------+
|                                    API LAYER (api/)                                   |
|   HTTP Routing, Request Validation (Pydantic v2), JSON Serialization, Structured Errors|
|   Endpoints: /projects, /allocation, /baseline, /mrv, /events, /revisions, /docs     |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                             APPLICATION / DOMAIN LAYER (services/)                    |
|   ProjectDomainService, AllocationDomainService, BaselineDomainService, MRVDomainService|
|   - Governs project lifecycle state machine                                           |
|   - Guarantees allocation immutability & branches revisions                           |
|   - Calculates operational deviations (F-27.2 null handling)                          |
|   - Executes multi-tier MRV QC checks (sensor, temporal, cloud ceiling)              |
|   - Enforces anti-contamination guards against synthetic fixtures                     |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                             SCIENTIFIC / DATA LAYER (processing/, data/)             |
|   FROZEN CANONICAL ASSETS (Read-Only Local Parquet & Manifests)                       |
|   - canonical_optimization_allocation.parquet (SHA: 2519473a...)                      |
|   - canonical_feature_matrix.parquet (SHA: 76f344b1...)                               |
|   - canonical_risk_surface.parquet (SHA: e2d5df6c...)                                 |
|   - canonical_hev_components.parquet (SHA: 1970c2da...)                               |
|   - optimization_run_manifest.json & project_mrv_contract.json                        |
+---------------------------------------------------------------------------------------+
```

---

## 3. CANONICAL DEMONSTRATION VALUES

The API contract guarantees exact reconciliation with the ratified Pune municipal initiative:

| Analytical Parameter | Canonical Value | API Representation & Governance Constraints |
| :--- | :--- | :--- |
| **Project ID** | `PROJ-PUNE-2025-BA225D6A` | Immutable primary key; references optimization run hash |
| **Optimization Run ID** | `OPT-PUNE-2025-SCENARIO-BA225D6A` | Strict upstream provenance lineage |
| **Spatial Grid** | Uber H3 Res 9 | Decoupled from administrative ward boundaries |
| **Selected Treated Cells** | 28 cells | Exactly 28 rows in canonical allocation Parquet |
| **Intervention Type** | `street_tree_shade` | Nature-based roadside canopy deployment |
| **Planned Physical Quantity** | 2,695 trees | Unit: `tree_count` |
| **Direct Unit Cost** | ₹3,500 / tree | Direct planting and 2m tree guard procurement |
| **Cell Mobilization Cost** | ₹20,000 / cell | Site reconnaissance, utility clearance, nursery logistics |
| **Modeled Total CapEx** | ₹9,992,500 | `2,695 * 3,500 + 28 * 20,000` |
| **Scenario Budget Envelope**| ₹10,000,000 | Municipal scenario allocation ceiling |
| **Budget Slack** | ₹7,500 | Remaining unallocated municipal capital |
| **Protected Population** | `118,941.21` | Exact underlying float preserved; display rounding: `118,941` |
| **Modeled Risk Objective** | `0.10604830270054796` | Modeled aggregate risk-objective reduction under F-24 formulation |

---

## 4. TRUTH-LAYER ENFORCEMENT CONTRACT

Every scientifically meaningful response field explicitly specifies its truth layer:

```json
{
  "metric": "lst_2025",
  "value": 46.69,
  "unit": "degC",
  "truth_layer": "OBSERVED",
  "source_artifact": "canonical_feature_matrix.parquet"
}
```

```json
{
  "metric": "lst_baseline_mean",
  "value": 46.36,
  "unit": "degC",
  "truth_layer": "DERIVED",
  "source_artifact": "canonical_feature_matrix.parquet"
}
```

```json
{
  "metric": "modeled_cooling_degC",
  "value": 0.0543,
  "unit": "degC",
  "truth_layer": "MODELED"
}
```

```json
{
  "verified_impact": null,
  "verification_status": "UNOBSERVED / NOT YET VERIFIED",
  "truth_layer": "VERIFIED (Unobserved at proposal phase)"
}
```

---

## 5. API ENDPOINT MATRIX

### Read Endpoints
1. `GET /projects`: High-level summary of registered projects with financial, physical, population, and truth metadata.
2. `GET /projects/{project_id}`: Complete 13-section structured project representation.
3. `GET /projects/{project_id}/allocation`: Immutable cell-by-cell allocation records with portfolio totals.
4. `GET /projects/{project_id}/baseline`: Cell and portfolio baseline metrics with OBSERVED vs DERIVED labels.
5. `GET /projects/{project_id}/mrv`: Physical progress, deviations, observation audits, and DID readiness status.

### Write Endpoints
1. `POST /projects/{project_id}/implementation-events`: Logs physical deployment, computes deviation, handles F-27.2 null rate.
2. `POST /projects/{project_id}/verification-events`: Heavily guarded verification milestone evaluation.
3. `POST /projects/{project_id}/transition`: Lifecycle state machine transition guarded by `ProjectStateMachine`.
4. `POST /projects/{project_id}/revisions`: Transparent proposed allocation revision branching.

### Immutability Protection
- `PUT /projects/{id}/allocation`: HTTP 405 Method Not Allowed (`ALLOCATION_IMMUTABLE`).
- `PATCH /projects/{id}/allocation`: HTTP 405 Method Not Allowed (`ALLOCATION_IMMUTABLE`).
- `DELETE /projects/{id}/allocation`: HTTP 405 Method Not Allowed (`ALLOCATION_IMMUTABLE`).

---

## 6. MRV SAFETY & VERIFICATION GATING

The API strictly implements the five-stage MRV Quality Control Engine:
1. **Spatial Coverage:** Observed cells $\ge$ treated cells count (28).
2. **Temporal Window Comparability:**
   - Preferred Window: DOY 95–115 (April 5–25 non-leap).
   - Fallback Window: DOY 90–120 with $|DOY - 105| \le 15$ days.
   - Out-of-Window: Rejection (HTTP 422 `VERIFICATION_NOT_ELIGIBLE`).
3. **Cloud & Shadow Screening:** $\le 5.0\%$ AOI contamination ceiling and 100% pixel QA masking passed.
4. **Sensor Radiometric Consistency:**
   - Thermal LST: Landsat-8/9 TIRS, calibrated radiometric pyrometers.
   - Optical: Sentinel-2 MSI, Landsat OLI/OLI-2.
   - Anti-pattern: Sentinel-2 MSI submitted for thermal LST is rejected with explicit structural error.
5. **Anti-Contamination Guard:** Any observation or verification carrying `DEMO_ONLY_SYNTHETIC_MRV_DATA` or `is_synthetic_demo == True` is immediately rejected from certifying production projects.

---

## 7. DIFFERENCE-IN-DIFFERENCES (DID) CONTRACT

Empirical causal verification remains:

$$\text{DID Status} = \mathbf{PLANNED\ /\ NOT\_YET\_EXECUTABLE}$$

The API exposes this readiness status explicitly. It prohibits executing DID models against baseline-only, synthetic, or modeled projections.

---

## 8. TEST AUDIT SUMMARY

The complete test suite passed with 100% compliance:
- `tests/test_phase_2a_api.py`: 14 passed in 1.22s.
- `tests/test_phase_1h_project_mrv.py`: 12 passed in 0.59s.
- Scientific suites (9 suites): 92 passed.
- Processing suite (`test_phase_1a8_processing.py`): 12 passed.
- Ingestion suite (`test_ingestion.py`): 13 passed.
- Total test coverage: **143 tests passing, 0 failing, 0 skipped.**
