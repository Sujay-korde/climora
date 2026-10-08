# CLIMORA — Scientific Validation Hierarchy & Verification Framework

**Document Version:** 1.0.0  
**Phase:** Phase 1B Analytical Execution & Scientific Formulation Gate  
**Reference Register:** [`docs/science/climora-mathematical-formulation-register.md`](file:///c:/Users/lenovo/climora/docs/science/climora-mathematical-formulation-register.md)  
**Machine-Readable Contract:** [`data/manifests/scientific_formulation_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/scientific_formulation_contract.json)  
**Status:** **RATIFIED & CANONICAL**  
**Lead Roles:** Lead Scientific Systems Architect, Mathematical Modeler, Geospatial ML Engineer, Data Auditor  

---

## 1. Executive Mandate

In environmental data science and climate risk modeling, claiming "model accuracy" or "empirical validation" without authentic reference ground truth is scientific malpractice.

In accordance with Section 29 of the Scientific Formulation Gate:
1. CLIMORA establishes a **7-Tier Scientific Validation Hierarchy (Levels 0 through 6)**.
2. Every analytical layer, pipeline stage, and feature must be classified strictly according to what has been scientifically validated versus what remains an assumption.
3. **MANDATORY SCIENTIFIC RULE:** CLIMORA strictly prohibits claiming Level 5 or Level 6 validation when the necessary external reference datasets or field ground-truth observations do not exist in the repository.

---

## 2. Seven-Tier Scientific Validation Hierarchy

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                 CLIMORA 7-TIER SCIENTIFIC VALIDATION HIERARCHY              │
├─────────────────────────────────────────────────────────────────────────────┤
│ LEVEL 0: MATHEMATICAL CONSISTENCY                                           │
│ • Dimensional analysis, unit consistency, range bounds                      │
│ • Zero-exposure axiom: E_i = 0 => Risk_i = 0                                │
│ • Division-by-zero safeguards (epsilon = 0.001 C)                           │
│ • Status: FULLY VERIFIED (Automated Unit Tests)                             │
│                                    ↓                                        │
│ LEVEL 1: DATA INTEGRITY & PROVENANCE                                        │
│ • SHA-256 byte-for-byte checksum immutability                               │
│ • CRS projection conformity (EPSG:4326 native, EPSG:32643 planar metric)    │
│ • Complete traceability from raw byte to derived feature                    │
│ • Status: FULLY VERIFIED (Automated Manifest Checks)                        │
│                                    ↓                                        │
│ LEVEL 2: PHYSICAL PLAUSIBILITY                                              │
│ • Terrestrial thermodynamic limits: LST in [15.0°C, 65.0°C]                 │
│ • Spectral index physical bounds: NDVI in [-1, 1], NDBI in [-1, 1]          │
│ • Non-negative population and non-negative distance                         │
│ • Status: FULLY VERIFIED (Automated Clamping & Pipeline QA)                 │
│                                    ↓                                        │
│ LEVEL 3: SPATIAL CONSISTENCY & AUTOCORRELATION                              │
│ • Positive spatial autocorrelation verified: Moran's I > 0.0                │
│ • Hexagonal 6-neighbor isotropic DGGS topology (H3 Res 9)                   │
│ • Dasymetric demographic conservation within <= 0.05% of exact polygon      │
│ • Status: FULLY VERIFIED (Empirical Spatial Benchmarks)                     │
│                                    ↓                                        │
│ LEVEL 4: TEMPORAL CONSISTENCY & MICROCLIMATIC STABILITY                     │
│ • 5-Year Pre-Monsoon Baseline window (April 11–24, DOY 101–114, offset <=15)│
│ • Missing data eligibility gate: K_valid >= 4 of 5 years                    │
│ • Persistence denominator strictly K_valid                                  │
│ • Status: FULLY VERIFIED (Temporal Governance Gate)                         │
│                                    ↓                                        │
│ LEVEL 5: EXTERNAL / CROSS-SENSOR REFERENCE VALIDATION                       │
│ • Cross-sensor radiometric agreement: Landsat 30m vs Sentinel-2 10m         │
│ • Regional synoptic thermal alignment with MODIS 1km LST                    │
│ • Diurnal atmospheric context via NASA POWER surface meteorology            │
│ • Status: PARTIALLY VERIFIED (Satellite Radiometry / Reanalysis Context)    │
│                                    ↓                                        │
│ LEVEL 6: GROUND-TRUTH & CLINICAL IN-SITU VALIDATION                         │
│ • Handheld thermal pyrometer street-canyon field audits                     │
│ • In-situ IMD automated weather station networks                            │
│ • Sassoon Hospital / PMC heat morbidity & clinical heat-stroke records      │
│ • Status: PENDING_DATA / PENDING_VALIDATION (None currently exist in repo)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tier-by-Tier Audit & Evidence Criteria

### Level 0 — Mathematical Consistency
* **Objective:** Ensure mathematical formulations are well-posed, numerically stable, dimensionally sound, and strictly preserve boundary axioms.
* **Evidence Required:**
  1. Unit analysis confirms output units match physical definitions ($^\circ\text{C}$, $\text{persons / km}^2$, dimensionless).
  2. The Zero-Exposure Axiom ($\mathcal{E}_i = 0 \implies \text{Risk}_i = 0$) holds computationally and numerically for all parameter combinations ($\alpha, \beta, \gamma \in [0.0, 3.0]$).
  3. Division-by-zero is mathematically prevented in standardized anomaly calculations via the regularization constant $\varepsilon = 0.001^\circ\text{C}$.
  4. Missing values evaluate to explicit `null` / `NaN` with quality flags; no silent numerical zeroes are substituted.
* **Verification Status:** **`VERIFIED`** in [`tests/test_scientific_formulation_contracts.py`](file:///c:/Users/lenovo/climora/tests/test_scientific_formulation_contracts.py).

### Level 1 — Data Integrity & Provenance
* **Objective:** Ensure that every byte ingested or processed matches authoritative cryptographic baselines without corruption or unauthorized modification.
* **Evidence Required:**
  1. 100% of the 109 raw assets match `pune_temporal_baseline_v1_checksums.sha256`.
  2. 100% of the 160 processed assets match `pune_temporal_baseline_v1_processed_checksums.sha256`.
  3. All geometries and raster bounds align with statutory Pune Municipal Corporation polygon ([`data/aoi/pune.geojson`](file:///c:/Users/lenovo/climora/data/aoi/pune.geojson)).
  4. Planar metric calculations strictly project to UTM Zone 43N (`EPSG:32643`).
* **Verification Status:** **`VERIFIED`** in [`tests/test_temporal_governance.py`](file:///c:/Users/lenovo/climora/tests/test_temporal_governance.py).

### Level 2 — Physical Plausibility
* **Objective:** Confirm that derived values fall within realistic terrestrial environmental limits and obey thermodynamic conservation laws.
* **Evidence Required:**
  1. Land surface temperatures fall within the terrestrial Pune pre-monsoon envelope $[15.0^\circ\text{C}, 65.0^\circ\text{C}]$.
  2. Surface reflectance values $\rho_\lambda \in [0.0, 1.0]$.
  3. Biophysical indices $\text{NDVI}, \text{NDBI} \in [-1.0, 1.0]$.
  4. Population count $C_i \ge 0$ and population density $D_i \ge 0$.
  5. Post-intervention modeled temperatures $T_{\text{post}, i} \ge T_{\text{wet\_bulb}, \text{ambient}}$ (thermodynamic lower bound).
* **Verification Status:** **`VERIFIED`** in [`processing/landsat_processor.py`](file:///c:/Users/lenovo/climora/processing/landsat_processor.py) and [`processing/pipeline.py`](file:///c:/Users/lenovo/climora/processing/pipeline.py).

### Level 3 — Spatial Consistency
* **Objective:** Validate spatial topology, boundary clipping, neighbor adjacency, and spatial autocorrelation.
* **Evidence Required:**
  1. Canonical mesh Uber H3 DGGS Resolution 9 generates exactly 3,181 regular hexagons covering statutory Pune AOI.
  2. Every interior cell possesses exactly 6 equidistant neighbors with uniform center-to-center spacing of $347.8\text{ m}$.
  3. Positive spatial autocorrelation is empirically demonstrated ($\text{Global Moran's } I > 0.0$), confirming that adjacent cells share physical heat plumes.
  4. Dasymetric area-weighted population aggregation conserves municipal population mass with delta of $0.0033\% \le 0.05\%$ tolerance.
* **Verification Status:** **`VERIFIED`** in [`tests/test_phase_1b_analytical_contracts.py`](file:///c:/Users/lenovo/climora/tests/test_phase_1b_analytical_contracts.py).

### Level 4 — Temporal Consistency
* **Objective:** Confirm temporal harmonization, seasonal window adherence, and missing-data governance across the 5-year baseline.
* **Evidence Required:**
  1. Temporal scenes strictly conform to the approved April peak-summer window (DOY 101–114, offset $\le 15$ days from Canonical Target DOY 105).
  2. Zero unverified May scenes exist in the data lake.
  3. Minimum historical coverage requires $K_{\text{valid}} \ge 4$ years with $f_{\text{valid}} \ge 0.70$.
  4. Relative persistence denominator is strictly $K_{\text{valid}}$.
* **Verification Status:** **`VERIFIED`** in [`tests/test_temporal_governance.py`](file:///c:/Users/lenovo/climora/tests/test_temporal_governance.py).

### Level 5 — External & Reference Validation
* **Objective:** Cross-validate satellite observations against independent spaceborne radiometers, coarse regional sensors, and meteorological reanalysis.
* **Evidence Required:**
  1. Sentinel-2 MSI 10m current-state optical imagery shows high correlation ($R^2 > 0.90$) with Landsat 8/9 30m NDVI over stable vegetated surfaces.
  2. MODIS 1km 8-day composite thermal imagery confirms regional pre-monsoon heat wave timing without destructive upsampling.
  3. NASA POWER daily surface meteorology provides independent confirmation of cloud-free, high-solar-irradiance conditions on all five acquisition dates.
* **Verification Status:** **`PARTIALLY VERIFIED`** (radiometric cross-sensor agreement established; atmospheric reanalysis aligned).

### Level 6 — Ground-Truth Field Validation
* **Objective:** Ground-truth model predictions against calibrated in-situ thermal pyrometers, micro-meteorological weather stations, and hospital heat morbidity records.
* **Evidence Required:**
  1. Calibrated hand-held infrared radiometer (FLIR / Apogee pyrometer) transects across high-NDBI tin-roof settlements in Bhavani Peth, Kasba Peth, and Yerawada.
  2. Calibrated automatic weather stations measuring continuous ambient air temperature ($T_{2m}$), relative humidity, and black-globe temperature.
  3. Geocoded clinical heat exhaustion and heat stroke admission records from Sassoon General Hospital and PMC municipal clinics.
  4. Pre- and post-intervention field audits verifying actual physical cooling of cool-roof installations.
* **Verification Status:** **`PENDING_DATA / PENDING_VALIDATION`**
  > **MANDATORY GOVERNANCE DECLARATION:** Neither CLIMORA nor any hackathon participant possesses parcel-level ground-truth heat morbidity records for Pune. CLIMORA explicitly does NOT claim Level 6 ground-truth validation. All downstream risk prioritization is framed as **unsupervised physical thermal screening and spatial optimization**, never as a supervised epidemiological mortality predictor.
