# CLIMORA Claims Audit & Reconciliation Ledger
**Audit Target:** Novex 2026 Evaluation Committee & Municipal Finance Authorities  
**Sign-Off Roles:** Project Head, Market Head, Video Director  
**Date:** 2026-11-07  
**Database Reference:** Canonical Project `PROJ-PUNE-2025-BA225D6A`  

---

### 1. Numerical Claims Reconciliation

| Metric / Parameter | Script / Pitch Claim | Live Application Reality | Audit Status | Resolution / Source |
| :--- | :--- | :--- | :--- | :--- |
| **Pune AOI Area** | `312.11 km²` | `312.11 km²` | **VERIFIED** | Official PMC statutory administrative boundary (`data/aoi/pune.geojson`). |
| **Pune Population** | `5,011,229 citizens` | `5,011,229 citizens` | **VERIFIED** | WorldPop 2020 dasymetric population sum aggregated over 3,181 cells. |
| **H3 Spatial Mesh** | `3,181 cells (Res-9)` | `3,181 cells` | **VERIFIED** | `query_layer.py` indexed full Pune boundary with Uber H3 Resolution-9 (~0.0986 km²/cell). |
| **Peak Surface Temp (LST)** | `46.36°C` | `46.36°C` | **VERIFIED** | Landsat 8/9 Collection 2 Level-2 5-year peak-summer pre-monsoon composite (2021–2025). |
| **Sample Cell ID** | `8960144d577ffff` (initial prompt draft) | `89608850003ffff` | **RECONCILED** | Pune H3 Res-9 cells have statutory prefix `896088...`. Script updated to canonical cell `89608850003ffff` (Pop: 4,757; Trees: 76; LST: 47.06°C). |
| **Benchmark Budget** | `₹1 Crore` (`10,000,000 INR`) | `₹10,000,000 INR` | **VERIFIED** | Formally defined as `₹10,000,000 INR` (approx. $120,000 USD). Script prohibits "$10M INR". |
| **Optimal Allocated Budget** | `₹99,92,500` (`₹9.99M`) | `₹9,992,500.0` | **VERIFIED** | HiGHS solver output under ₹10.0M ceiling with ₹7,500 budget slack. |
| **Optimal Priority Footprint** | `28 cells (0.88%)` | `28 cells` | **VERIFIED** | Exactly 28 priority H3 cells selected out of 3,181 (28 / 3181 = 0.8802%). |
| **Planned Tree Count** | `2,695 shade trees` | `2,695.0 trees` | **VERIFIED** | Exact integer sum of discrete street tree allocations at 15.0m interval. |
| **Citizens Protected** | `118,941 residents` | `118,941.2 residents` | **VERIFIED** | Population residing in the 28 prioritized intervention hex cells (mean 4,248/cell vs 1,575 citywide). |
| **Per-Citizen Cost** | `₹84 / person sheltered` | `₹84.01 / person` | **VERIFIED** | `₹9,992,500 / 118,941 = ₹84.012`. |
| **DiD Evaluation Status** | Real-world cooling verified | `PLANNED / NOT_YET_EXECUTABLE` | **RECONCILED** | Live API returns status `PLANNED`. Post-deployment satellite passes are pending. Script strictly frames DiD as a planned protocol with honest single-cell uncertainty limits (6.91°C MDE). |
| **Cedar Policy Engine** | "Amazon Cedar" | `Cedar policy engine` | **RECONCILED** | Open-source Cedar language and evaluator (`cedarpy` v4.12). Removed "Amazon" branding from voiceover. |

---

### 2. Language & Scientific Discipline Sign-Off

1. **Simulated vs Verified:**
   - Any scenario optimization run by users in the UI is labeled `[MODELED] / SIMULATED`.
   - The canonical baseline is stamped `[OBSERVED]` (Landsat/Sentinel) or `[DERIVED]` (IPCC formulations).
   - Post-implementation verification is marked `[PLANNED]` with documented detectability noise floors.
2. **Access Control & Integrity:**
   - Auth is executed via the open-source Cedar policy engine with 5 distinct actors and ratified ABAC policies.
   - SHA-256 cryptographic provenance guarantees dossier immutability without making unfounded legal claims.
3. **Currency Standardization:**
   - Formatted exclusively as `₹1 Crore` or `₹10,000,000 INR`. The ambiguous term "$10M INR" is strictly eliminated.

**Sign-off:** Approved by Project Head & Market Head for Phase 1 Capture.

