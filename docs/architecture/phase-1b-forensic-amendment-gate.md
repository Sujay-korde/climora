# CLIMORA — Phase 1B: Forensic Amendment Gate Report

**Document Version:** 1.0.0  
**Phase:** Phase 1B (Forensic Amendment & Integrity Gate)  
**Status:** **AUDITED, AMENDED & FROZEN**  
**Role:** Senior Systems Architect, Geospatial Data Engineer, Scientific Data Auditor, and Governance Lead  

---

## 1. Audit Scope & Objective

This forensic audit was commissioned to determine whether the CLIMORA Phase 1B analytical architecture freeze is genuinely traceable, internally consistent, scientifically defensible, and safe to lock. Operating strictly under the **minimum-change principle**, no parallel competing schemas were created, no raw/processed baseline data was mutated, and the canonical H3 Res 9 spatial unit was preserved based on verified empirical properties.

---

## 2. Repository State Prior to Amendment

- **Frozen Raw Assets (Phase 1A.7):** 109 physical files across Landsat, Sentinel-2, MODIS, DEM, OSM, and NASA POWER. Verified 100% byte-for-byte immutable against `pune_temporal_baseline_v1_checksums.sha256`.
- **Frozen Processed Assets (Phase 1A.8):** 160 physical files across scaled rasters, QA masks, derived indices, and meteorological normalization. Verified 100% byte-for-byte immutable against `pune_temporal_baseline_v1_processed_checksums.sha256`.
- **Phase 1B Documentation Defect Identified:** Erroneous temporal acquisition dates (May dates) and fictitious file paths were found in `temporal_feature_contract.json`, `feature_dictionary.json`, and architecture markdown files, conflicting with the frozen April baseline scenes approved in Phase 1A.7.1.

---

## 3. Temporal Lineage Findings

The canonical frozen five-year Landsat temporal baseline was approved during Phase 1A.7.1 Amendment A1 around Canonical Target DOY 105 (mid-April peak summer, preferred window DOY 95–115):

| Observation Year | Approved Frozen Scene ID | Platform / Sensor | Target Date | Approved DOY | DOY Offset | AOI Cloud % | AOI Shadow % |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **2021** | `LC08_L2SP_147047_20210424_02_T1` | Landsat 8 OLI/TIRS-1 | 2021-04-24 | 114 | +9 | 0.00% | 0.00% |
| **2022** | `LC08_L2SP_147047_20220411_02_T1` | Landsat 8 OLI/TIRS-1 | 2022-04-11 | 101 | -4 | 1.71% | 3.22% |
| **2023** | `LC09_L2SP_147047_20230422_02_T1` | Landsat 9 OLI-2/TIRS-2 | 2023-04-22 | 112 | +7 | 0.00% | 0.03% |
| **2024** | `LC08_L2SP_147047_20240416_02_T1` | Landsat 8 OLI/TIRS-1 | 2024-04-16 | 107 | +2 | 0.00% | 0.00% |
| **2025** | `LC08_L2SP_147047_20250419_02_T1` | Landsat 8 OLI/TIRS-1 | 2025-04-19 | 109 | +4 | 0.00% | 0.00% |

All five physical scenes exist on disk in `data/raw/landsat/`, `data/processed/landsat/`, and `data/derived/landsat/`.

---

## 4. May-Date Reconciliation

### 4.1 Root-Cause Analysis
During Phase 1B documentation drafting, an unverified speculative date range (May 8 to May 21, DOY 128 to 141) was erroneously written into markdown documents and JSON manifests.

### 4.2 Forensic Proof of Data Lake Concordance
An exhaustive inspection of the local filesystem confirmed:
- **Zero May Landsat scenes** exist in `data/raw/` or `data/processed/`.
- All processed and derived rasters (LST, NDVI, NDBI, QA masks) originate **exclusively** from the April scenes listed in Section 3.
- `pune_temporal_stack_manifest.json` and `pune_temporal_summary.json` correctly link the April scenes.

### 4.3 Corrective Action Taken
All erroneous May dates and non-existent file paths were completely eradicated from:
- [`data/manifests/temporal_feature_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/temporal_feature_contract.json)
- [`data/manifests/analytical_unit_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/analytical_unit_contract.json)
- [`data/manifests/feature_dictionary.json`](file:///c:/Users/lenovo/climora/data/manifests/feature_dictionary.json)
- [`docs/architecture/phase-1b-analytical-architecture.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-1b-analytical-architecture.md)
- [`docs/architecture/phase-1b-feature-contract.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-1b-feature-contract.md)
- [`docs/architecture/phase-1b-risk-target-strategy.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-1b-risk-target-strategy.md)

---

## 5. Uncertainty Governance & Classification Audit

In accordance with Section 5 of the audit mandate, every numerical uncertainty claim was systematically audited, classified, and bounded:

| Parameter / Claim | Current Value | Primary Evidence / Citation | Scientific Classification | Governance Action Taken |
| :--- | :---: | :--- | :--- | :--- |
| **Landsat LST Measurement Uncertainty** | $\pm 1.0\text{ K}$ to $\pm 1.5\text{ K}$ RMSE | USGS Landsat Collection 2 Level 2 Surface Temperature Technical Documentation (Cook et al. 2014; Malakar et al. 2018) | `DOCUMENTED_EXTERNAL` | **Retained as documented.** Formally cited; applies to clear-sky conditions with low atmospheric water vapor. |
| **Atmospheric / Emissivity Processing Uncertainty** | $\pm 0.5\text{ K}$ | Unvalidated rule of thumb | `CLIMORA_ASSUMPTION` | **Reclassified as Methodological Assumption.** Forbidden from being presented as empirically verified truth. |
| **WorldPop Demographic Disaggregation Uncertainty** | $\pm 15\%$ | Stevens et al. (2015); WorldPop regional documentation | `CLIMORA_ASSUMPTION` | **Reclassified as Sensitivity Parameter.** WorldPop validates at regional administrative boundaries; urban parcel-scale uncertainty in India is unquantified. |
| **Pixel Averaging Uncertainty ($\sigma / \sqrt{109.6}$)** | $0.095\sigma$ | Elementary standard error formula | `METHODOLOGICAL_QUALIFICATION` (Formerly `UNSUPPORTED`) | **Statistical claim removed.** The i.i.d. assumption is mathematically invalid due to strong positive spatial autocorrelation (Moran's $I > 0$). Qualified as nominal sample variance. |
| **Temporal Morning Sampling Uncertainty** | $10^\circ\text{C}$ to $18^\circ\text{C}$ diurnal swing | Pune IMD / NASA POWER diurnal cycle observations | `DOCUMENTED_EXTERNAL` | **Retained as documented.** All LST metrics are formally qualified as *Morning Peak-Summer Surface Temperature*, not 24-hr mean ambient air temperature. |
| **Proxy Uncertainty (NDVI/NDBI)** | Qualitative | Biophysical radiation physics | `METHODOLOGICAL_BOUNDARY` | **Enforced strict boundary.** Biophysical surface indicators must never be conflated with socioeconomic human poverty. |

---

## 6. Risk Formulation Attribution Correction

### 6.1 Conceptual Framework vs Implementation
- **IPCC AR6 Working Group II Attribution:** The IPCC defines Risk conceptually as the result of the dynamic interaction between physical **Hazard**, human/asset **Exposure**, and **Vulnerability** ($\text{Risk} = f(\mathcal{H}, \mathcal{E}, \mathcal{V})$). The IPCC does **NOT** prescribe a mathematical power-law equation.
- **CLIMORA Methodological Implementation:** CLIMORA specifically implements this conceptual triad through a multiplicative power-law aggregation:
  $$\text{Risk}_i = \mathcal{H}_i^{\alpha} \times \mathcal{E}_i^{\beta} \times \mathcal{V}_i^{\gamma}$$
- **Axiomatic Rationale:** The multiplicative structure was chosen by CLIMORA to enforce the fundamental risk axiom:
  $$\text{If Exposure } \mathcal{E}_i = 0 \implies \text{Human Climate Risk } = 0$$
  This prevents unpopulated industrial quarries or bare basalt outcrops from generating false disaster alarms.

---

## 7. Alpha, Beta, Gamma Governance Contract

To ensure complete mathematical transparency, the exponent parameters are formally governed under a dedicated contract: [`data/manifests/risk_parameter_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/risk_parameter_contract.json):

```json
{
  "risk_parameters": [
    {
      "parameter_name": "risk_weight_alpha",
      "target_component": "Hazard (H)",
      "default_value": 1.0,
      "allowed_range": [0.0, 3.0],
      "calibration_status": "PENDING_METHODOLOGICAL_CALIBRATION",
      "normalization_applied": "Min-Max scaling to [0.0, 1.0]"
    },
    {
      "parameter_name": "risk_weight_beta",
      "target_component": "Exposure (E)",
      "default_value": 1.0,
      "allowed_range": [0.0, 3.0],
      "calibration_status": "PENDING_METHODOLOGICAL_CALIBRATION",
      "normalization_applied": "Min-Max scaling to [0.0, 1.0]"
    },
    {
      "parameter_name": "risk_weight_gamma",
      "target_component": "Biophysical and Structural Susceptibility (V)",
      "default_value": 1.0,
      "allowed_range": [0.0, 3.0],
      "calibration_status": "PENDING_METHODOLOGICAL_CALIBRATION",
      "normalization_applied": "Min-Max scaling to [0.0, 1.0]"
    }
  ]
}
```

The parameters are declared as **`PENDING_METHODOLOGICAL_CALIBRATION`** and must not be claimed as empirically validated physical constants.

---

## 8. Vulnerability vs Susceptibility Terminology Governance

In strict compliance with Critical Audit E:
1. **Biophysical and Structural Susceptibility:** Applies exclusively to observable physical surface conditions: lack of photosynthesizing canopy cover ($1 - \text{NDVI}$) and impervious built-up thermal mass ($\text{NDBI}$).
2. **Prohibition:** CLIMORA strictly prohibits stating or implying that low NDVI or high NDBI represent socioeconomic human poverty.
3. **Socioeconomic Vulnerability & Adaptive Capacity:** Explicitly declared as **`UNAVAILABLE / PENDING STATUTORY SURVEYS`** (requiring Slum Rehabilitation Authority or Census household data).

---

## 9. Temporal Missing-Data & 70% Valid Pixel Policy

In accordance with Critical Audit F, the behavior for missing or partially cloud-obscured annual scenes is now explicitly formalized:
1. **Annual Cell Eligibility:** A cell observation is valid in year $k$ iff its unmasked clear pixel coverage fraction $\ge 0.70$ (`qa_mask == 1`).
2. **Minimum Historical Window:** Baseline central tendency (mean, median, standard deviation) requires at least **4 valid annual observations** ($K_{\text{valid}} \ge 4$ out of 5).
3. **Insufficient Coverage Rule:** If $K_{\text{valid}} < 4$, baseline statistics evaluate to `null` / `NaN`, and the cell is assigned the quality flag `INSUFFICIENT_HISTORICAL_COVERAGE`.
4. **Persistence Denominator:** Persistence frequency is strictly calculated over valid years:
   $$\text{Persistence}_{\text{P75}}(h) = \frac{1}{K_{\text{valid}}} \sum_{k \in \text{valid}} \mathbb{I}\left(\text{LST}_{k}(h) \ge P_{75}(\text{LST}_{\text{citywide}, k})\right)$$
   The exact count $K_{\text{valid}}$ is permanently recorded in cell metadata.
5. **Recurrence Denominator:** Extreme recurrence is an integer count over valid years; if $K_{\text{valid}} < 5$, the cell is flagged as `partial_temporal_record`.
6. **Current-State Anomaly Eligibility:** $\Delta \text{LST}_{2025}$ is valid iff both $K_{\text{valid}} \ge 4$ AND the 2025 observation has valid pixel coverage $\ge 70\%$.

---

## 10. 45°C Extreme LST Recurrence Governance

In accordance with Critical Audit G:
- `lst_recurrence_ge45` is defined neutrally as:
  > *"Integer count of valid baseline annual pre-monsoon observations where cell zonal mean LST was $\ge 45.0^\circ\text{C}$."*
- **Governance Constraint:** It is explicitly classified as a **CLIMORA Methodological Surface Temperature Threshold** for radiant heat on impervious/tin roofs, NOT an internationally standardized epidemiological heat-health threshold.

---

## 11. NDWI Lineage Audit

- **Audit Finding:** `feat_ndwi_current_2025` was declared in the draft dictionary, but an exhaustive scan of the repository confirmed that **no NDWI GeoTIFF exists** in `data/`, and no NDWI routine exists in `processing/pipeline.py`.
- **Corrective Action Taken:** In strict adherence to Section 11, `feat_ndwi_current_2025` was **completely removed** from the canonical feature dictionary. Lineage was not fabricated.

---

## 12. OpenStreetMap Infrastructure Lineage Audit

- **Audit Finding:** The draft dictionary referenced non-existent paths `pune_roads.geojson` and `pune_health_facilities.geojson`.
- **Actual Frozen Assets Identified & Validated:**
  - `data/raw/osm/pune/road_network.geojson`: 2,138 features (LineString/Polygon)
  - `data/raw/osm/pune/public_infrastructure.geojson`: 1,268 features:
    * `hospital`: 666 features
    * `clinic`: 417 features
    * `school`: 128 features
    * `university`: 57 features
  - `data/raw/osm/pune/green_spaces.geojson`: 602 features (Polygon)
  - `data/raw/osm/pune/water_bodies.geojson`: 357 features (LineString/Polygon)
- **Corrective Action Taken:** Feature definitions in `feature_dictionary.json` were reconciled to reference the exact frozen assets and exact Overpass amenity filter queries.

---

## 13. Spatial Unit Verification (H3 Res 9 & PMC Wards)

- **Primary Analytical Mesh (`grid_hex_h9`):** Exactly 3,181 cells; nominal area $0.0986\text{ km}^2$; 6-neighbor isotropic adjacency ($347.8\text{ m}$ spacing); bitwise `uint64` indexing. Verified 100% mathematically and geometrically sound.
- **Administrative Tier (`ward`):** 41 statutory PMC administrative wards; retained strictly as reporting units via `spatial_unit_ward_membership`.
- **Native Data Preservation:** Native 30m Landsat, 10m/20m Sentinel-2, 1km MODIS, and DEM remain untouched raw/processed GeoTIFFs; destructive resampling is strictly prohibited.
- **Decision:** **RATIFIED & PRESERVED WITHOUT REDESIGN.**

---

## 14. Feature Dictionary Verification

The reconciled [`data/manifests/feature_dictionary.json`](file:///c:/Users/lenovo/climora/data/manifests/feature_dictionary.json) contains **29 canonical features** across 10 groups:
- **Group A (Thermal):** 8 features
- **Group B (Vegetation):** 4 features
- **Group C (Built Environment):** 3 features
- **Group D (Moisture):** 1 feature (`feat_water_body_area_m2`)
- **Group E (Terrain):** 2 features (`feat_dem_elevation_mean_m`, `feat_dem_slope_mean_deg`)
- **Group F (Population Exposure):** 2 features (`feat_pop_count_2020`, `feat_pop_density_per_km2`)
- **Group G (Infrastructure Exposure):** 3 features (Road length, health count, education count)
- **Group H (Meteorological Context):** 2 features (NASA POWER daily $T_{2m,\max}$, $RH_{2m}$)
- **Group I (Temporal Quality):** 2 features (Valid pixel fraction, observation count)
- **Group J (Current-State Reference):** 2 features (Sentinel-2 10m NDVI, 20m NDBI reference)

**Lineage Verification:** 100% of declared source assets exist on disk and were verified.

---

## 15. Truth-Layer Verification

Every feature belongs to exactly one Truth Layer:
- `OBSERVED`: Raw satellite radiance, GLO-30 DEM elevation, WorldPop counts, OSM vectors, NASA POWER records.
- `DERIVED`: Deterministic mathematical calculations (NDVI, NDBI, LST in Celsius, Slope, Persistence, Recurrence, Anomalies, Density).
- `MODELED`: Composite risk indices, Moran's $I$ clustering, projected cooling impacts, MILP parcel allocations.
- `VERIFIED`: Empirical ground truth, post-intervention MRV audit logs, handheld thermal pyrometer logs.

No modeled predictions are misclassified as observed or derived.

---

## 16. Test Suite Results

The comprehensive test suite was executed:
```bash
pytest tests/ -v
```
**Result:** **42 / 42 PASSED** (0 failures, 0 errors, 100% green).

---

## 17. Files Changed

1. [`data/manifests/temporal_feature_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/temporal_feature_contract.json)
2. [`data/manifests/analytical_unit_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/analytical_unit_contract.json)
3. [`data/manifests/population_exposure_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/population_exposure_contract.json)
4. [`data/manifests/feature_dictionary.json`](file:///c:/Users/lenovo/climora/data/manifests/feature_dictionary.json)
5. [`data/manifests/risk_parameter_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/risk_parameter_contract.json) *(Newly created)*
6. [`scripts/generate_feature_dictionary.py`](file:///c:/Users/lenovo/climora/scripts/generate_feature_dictionary.py)
7. [`docs/architecture/phase-1b-analytical-architecture.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-1b-analytical-architecture.md)
8. [`docs/architecture/phase-1b-feature-contract.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-1b-feature-contract.md)
9. [`docs/architecture/phase-1b-risk-target-strategy.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-1b-risk-target-strategy.md)
10. [`docs/architecture/phase-1b-spatial-unit-decision.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-1b-spatial-unit-decision.md)
11. [`docs/architecture/phase-1b-forensic-amendment-gate.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-1b-forensic-amendment-gate.md) *(This report)*

---

## 18. Files Intentionally Unchanged

1. All 109 raw baseline assets in `data/raw/` (Phase 1A.7)
2. All 160 processed baseline assets in `data/processed/` (Phase 1A.8)
3. All derived Landsat rasters in `data/derived/` (Phase 1A.8)
4. `data/manifests/pune_temporal_baseline_v1_frozen.json`
5. `data/manifests/pune_temporal_baseline_v1_checksums.sha256`
6. `data/manifests/pune_temporal_baseline_v1_processed_frozen.json`
7. `data/manifests/pune_temporal_baseline_v1_processed_checksums.sha256`
8. Canonical AOI definition `data/aoi/pune.geojson`

---

## 19. Remaining Limitations

1. **Parcel-Scale Socioeconomic Data:** True socioeconomic vulnerability and household adaptive capacity remain unobserved at hexagon scale in Pune.
2. **Ground-Truth Heat Health Labels:** Parcel-level morbidity/mortality records do not exist. Downstream modeling must operate under unsupervised anomaly clustering and multi-objective optimization, not supervised classification.
3. **Diurnal Thermal Sampling:** Satellite LST represents a single morning snapshot (~10:30 AM local time), which differs from peak afternoon air temperatures.
4. **WorldPop Dasymetric Uncertainty:** Urban hexagon downscaling carries an unquantified empirical uncertainty, treated as a methodological sensitivity parameter.

---

## 20. Final Gate Decision

```text
============================================================
FINAL GATE DECISION:
PHASE 1B — PASSED / ARCHITECTURE FROZEN
============================================================
```
All critical lineage defects, date discrepancies, fictitious paths, uncertainty claims, and formula attributions have been forensically investigated, reconciled against authoritative assets, and ratified into machine-readable contracts.
