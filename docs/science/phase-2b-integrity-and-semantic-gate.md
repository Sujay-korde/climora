# CLIMORA — Phase 2B Integrity & Semantic Governance Gate

## Scientific Integrity, Artifact Immutability, and Truth-Layer Preservation

### 1. Scientific Governance Ratification

This document formally certifies that the Phase 2B Service Hardening and Read-Only Zonal Query Optimization has been executed with absolute adherence to the scientific freeze governing CLIMORA.

```text
NEW SCIENTIFIC FORMULATION: NONE
```

No mathematical formulation has been introduced, redefined, refactored, or modified. The optimization engine was not re-run, candidate generation was not altered, and no competing scientific representations have been created.

---

### 2. Canonical Artifact SHA-256 Audit

All 5 canonical Parquet artifacts were audited at the beginning and end of Phase 2B implementation. Every artifact remains 100% byte-for-byte identical to its frozen Phase 1 baseline:

| Canonical Artifact Path | Frozen Expected SHA-256 | Verified Actual SHA-256 | Status |
| :--- | :--- | :--- | :---: |
| `data/processed/canonical_feature_matrix.parquet` | `76f344b147b349f3887259f64c97923414c74fd9a97ec679844fb8d9109f7c01` | `76f344b147b349f3887259f64c97923414c74fd9a97ec679844fb8d9109f7c01` | **MATCH** |
| `data/processed/hev/canonical_hev_components.parquet` | `1970c2da7863f5771b223c2f265344129ea3f7ed1e5119ece98dc56e37fa2be9` | `1970c2da7863f5771b223c2f265344129ea3f7ed1e5119ece98dc56e37fa2be9` | **MATCH** |
| `data/processed/risk/canonical_risk_surface.parquet` | `e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677` | `e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677` | **MATCH** |
| `data/processed/risk/canonical_spatial_autocorrelation.parquet` | `47cc7025ef150aec3980928912e35c96c46da437efbbeccfe1fc142321315bbd` | `47cc7025ef150aec3980928912e35c96c46da437efbbeccfe1fc142321315bbd` | **MATCH** |
| `data/processed/optimization/canonical_optimization_allocation.parquet` | `2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555` | `2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555` | **MATCH** |

---

### 3. Truth-Layer Taxonomy Invariants

The API enforces strict truth-layer semantics across all endpoints:

1. **`OBSERVED`:**
   Direct empirical physical sensor or cadastral measurements:
   - `lst_2025`: Landsat-8/9 TIRS thermal observations (target DOY 105, 30m resolution).
   - `ndvi_2025`: Sentinel-2 MSI optical reflectance.
   - `ndbi_2025`: Sentinel-2 MSI normalized difference built-up index.
   - `population_2020`: Exact 118,941.21 persons across the 28 cells (rounded display: 118,941).
   - `road_length_m`: OSM-derived physical road segments.
2. **`DERIVED`:**
   Mathematically processed multi-year or spatial aggregates from observational layers:
   - `lst_baseline_mean`: 5-year pre-monsoon peak-summer composite (2021–2025).
   - `lst_anomaly_absolute`: Difference between 2025 LST and historical composite.
   - `lst_persistence`: Fraction of multi-year summer seasons exhibiting anomalous heat.
   - `lst_recurrence_ge45`: Count of years exceeding the $45^\circ\text{C}$ threshold.
   - `population_density_2020`: Derived from population and H3 hexagon area ($\text{km}^2$).
   - `lisa_spatial_autocorrelation`: Anselin Local Moran's $I$ and quadrant spatial categorization.
3. **`MODELED`:**
   Ex-ante simulations and optimization outputs:
   - $H_i$, $E_i$, $V_i$: Hazard, Exposure, and Vulnerability formulations.
   - $\text{Risk}_i$: Canonical F-22 Climate Risk score.
   - Modeled Capex: ₹9,992,500 modeled cost under ₹10,000,000 budget constraint.
   - Modeled Objective Reduction: `0.10604830270054796`.
4. **`VERIFIED`:**
   Must strictly remain `null` / `UNOBSERVED` at the proposal and pre-implementation phases.
   - Verified status cannot be inferred from API access, schema validation, successful optimization, synthetic data, or baseline observations.

---

### 4. Canonical Project Metric Invariants

The demonstration project representation preserves exact canonical values:
- **Project Identifier:** `PROJ-PUNE-2025-BA225D6A`
- **Optimization Run Identifier:** `OPT-PUNE-2025-SCENARIO-BA225D6A`
- **Treated H3 Resolution 9 Cells:** 28 cells
- **Planned Street Tree Shading:** 2,695 trees
- **Modeled Total CapEx:** ₹9,992,500
- **Scenario Budget Envelope:** ₹10,000,000
- **Budget Slack / Unallocated:** ₹7,500
- **Protected Population:** 118,941.21 exact persons (118,941 rounded display)
- **Modeled Aggregate Risk-Objective Reduction:** `0.10604830270054796`
- **Semantic Metric Restriction:** This score is strictly defined as *"modeled aggregate risk-objective reduction under the canonical optimization formulation"*. It MUST NOT be marketed or represented as an empirical temperature decrease, clinical cooling, morbidity reduction, or verified risk reduction.

---

### 5. Topology & Administrative Decoupling

- **Analytical Topology:** All optimization, risk scoring, spatial autocorrelation, and intervention allocation exist strictly on the H3 Resolution 9 analytical topology (~0.10 $\text{km}^2$ hexagons).
- **Administrative Wards:** Ward identifiers and municipal ward boundaries are decoupled display context only. They are not used for spatial filtering, candidate generation, cost calculations, or optimization constraints.

---

### 6. MRV Anti-Contamination & Sensor Safety

1. **Synthetic Data Quarantine:**
   - Payloads bearing `DEMO_ONLY_SYNTHETIC_MRV_DATA` or `is_synthetic_demo == True` are strictly rejected by verification gates with HTTP 422 `VERIFICATION_NOT_ELIGIBLE`.
2. **Sensor Compatibility:**
   - Sentinel-2 MSI is certified for optical metrics (NDVI, NDBI) but rejected for thermal LST observations due to the absence of a thermal infrared payload.
   - Landsat-8/9 TIRS is certified for thermal LST.
3. **Difference-in-Differences (DID) Execution Status:**
   - DID remains `PLANNED / NOT_YET_EXECUTABLE`.
   - The API will not execute DID against baseline observations, synthetic mocks, or modeled projections.
4. **Temporal Window Governance:**
   - Canonical target DOY is 105 (April 15 in standard years, April 14 in leap years).
   - Preferred verification window: $95 \le \text{DOY} \le 115$.
   - Fallback window: $90 \le \text{DOY} \le 120$ ($|\text{DOY} - 105| \le 15$).
   - Acquisition outside this envelope is rejected with HTTP 422.
5. **Atmospheric & Pixel Quality Screen:**
   - AOI cloud cover ceiling: $\le 5.0\%$.
   - Pixel QA flags: 100% valid masked pixels.
