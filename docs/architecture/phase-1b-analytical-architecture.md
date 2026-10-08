# CLIMORA — Phase 1B: Analytical Architecture & Foundation Decision Gate

**Document Version:** 1.0.0  
**Phase:** Phase 1B (Analytical Architecture, Spatial Unit Evaluation, Population Exposure & Feature Contract Decision Gate)  
**Previous Phase:** Phase 1A.8 (Temporal Processing, AOI Clipping & Spatial Harmonization — PASSED)  
**Status:** **RATIFIED & FROZEN**  
**Role:** Senior Geospatial Systems Architect, Climate-Risk Data Engineer, ML Systems Architect, and Scientific Data Auditor  

---

## 1. Executive Summary & Architectural Freeze

Phase 1B establishes the immutable **Analytical Architecture Contract** for CLIMORA before downstream machine learning, database migrations, API development, or UI rendering begin.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CLIMORA ANALYTICAL FLOWCHART                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ PROCESSED NATIVE DATA                                                       │
│ • Landsat 8/9 C2 L2 Peak-Summer (2021-2025) at 30m                          │
│ • Sentinel-2 MSI L2A (2025) at 10m/20m                                      │
│ • WorldPop 2020 UN-adjusted Population at ~1km (30")                        │
│ • Copernicus GLO-30 DEM Elevation/Slope at 30m                              │
│ • OpenStreetMap Infrastructure & Road Vectors                               │
│ • NASA POWER Daily Surface Meteorology                                      │
│                                    ↓                                        │
│ CANONICAL ANALYTICAL UNIT                                                   │
│ • Primary Modeling Mesh: Uber H3 DGGS Resolution 9 (grid_hex_h9, 3,181 cells)│
│ • Secondary Administrative Unit: PMC Statutory Wards (ward, 41 wards)       │
│ • Native Rasters Preserved: Never destructively resampled                   │
│                                    ↓                                        │
│ POPULATION / EXPOSURE INTEGRATION                                           │
│ • Dasymetric Area-Weighted Conservation (Sum)                               │
│ • Pune Total Pop: 5,011,229 residents (Conservation Delta: 0.0033%)         │
│                                    ↓                                        │
│ TEMPORAL FEATURE CONTRACT                                                   │
│ • 5-Year Pre-Monsoon Baseline (2021-2025)                                   │
│ • Persistence (P75 Frequency), Recurrence (>=45C Count), 2025 Anomaly       │
│                                    ↓                                        │
│ RISK TARGET / LABEL STRATEGY                                                │
│ • Ground truth heat mortality/morbidity labels audited: NONE EXIST          │
│ • Supervised ML on synthetic labels STRICTLY PROHIBITED                     │
│ • Canonical Strategy: IPCC AR6 Composite Risk (Hazard × Exposure × Vuln)    │
│   + Unsupervised Thermal Anomaly Clustering & Spatial Pareto Optimization   │
│                                    ↓                                        │
│ LOGICAL ANALYTICAL DATA MODEL                                               │
│ • Normalized relational schema (spatial_unit, feature_observation, etc.)    │
│ • Full traceability: cell + time + feature + value + quality + provenance   │
│                                    ↓                                        │
│ PHASE 1B ARCHITECTURE FREEZE (PASSED)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Spatial Unit Decision: Dual-Tier Architecture

Following empirical evaluation on the statutory Pune Municipal Corporation boundary (312.11 km², [`data/aoi/pune.geojson`](file:///c:/Users/lenovo/climora/data/aoi/pune.geojson)), CLIMORA establishes a **Dual-Tier Spatial Architecture**:

### 2.1 Primary Modeling Mesh: Uber H3 DGGS Resolution 9 (`grid_hex_h9`)
- **Cell Count:** 3,181 regular hexagons.
- **Nominal Area:** $0.0986\text{ km}^2$ ($9.86\text{ ha}$, $98,623\text{ m}^2$).
- **Geometry:** Edge $200.8\text{ m}$, Spacing $347.8\text{ m}$, Perimeter/Area ratio $0.0122\text{ m}^{-1}$.
- **Native CRS:** `EPSG:4326` with bitwise 64-bit unsigned integer (`uint64`) indexing.
- **Topological Isotropy:** Exactly 6 equidistant neighbors ($347.8\text{ m}$ spacing), eliminating directional Cartesian biases in spatial heat diffusion and Moran's $I$ spatial lag models.
- **Pixel Sample Stability:** $\sim 109.6$ Landsat 30m pixels and $\sim 986$ Sentinel-2 10m pixels per cell, suppressing uncorrelated sensor noise by over $90\%$.

### 2.2 Secondary Administrative Reporting Unit: PMC Wards (`ward`)
- **Unit Count:** 41 statutory administrative wards (or 76 Prabhag electoral divisions).
- **Mean Area:** $7.61\text{ km}^2$ (range $0.8\text{ km}^2$ to $>35\text{ km}^2$).
- **Role:** Municipal accountability, councillor reporting, municipal budget allocation, tender packaging.
- **Spatial Join:** Every H3 cell records its primary parent ward (largest intersection area) and area-intersection fractions in a relational join table (`spatial_unit_ward_membership`).

### 2.3 Native Data Preservation Policy
Underlying 30m Landsat, 10m/20m Sentinel-2, 1km MODIS, and DEM GeoTIFFs remain immutable raster assets in `data/processed/`. The analytical unit accesses these rasters via zonal queries; native source rasters are **never destructively resampled**.

---

## 3. WorldPop Population Exposure Validation & Conservation

Human exposure was audited, acquired, and validated:
- **Product:** WorldPop Global 2000–2020 1km UN-adjusted Population Count (IND 2020).
- **Official URL:** `https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/IND/ind_ppp_2020_1km_Aggregated_UNadj.tif`
- **File Size:** 18,313,124 bytes (SHA-256: `27d08e3eabf59f63a2147901c25c046d584c3295f9ceb4c4cf08a902a5bec911`).
- **Native CRS:** `EPSG:4326`, 30 arc-seconds ($\sim 0.008333^\circ$, $\sim 0.92\text{ km}$).
- **Clipped Asset:** `data/processed/worldpop/2020/worldpop_pune_2020_clipped.tif`.

### 3.1 Dasymetric Conservation Results
- **Exact Polygon-Clipped Population:** $5,011,396.9$ persons.
- **H3 Res 9 Aggregated Population:** $5,011,229.6$ persons.
- **Observed Demographic Conservation Delta:** **$0.0033\%$** (error of only $167.3$ people across $5.01\text{M}$ residents).
- **Population Count Semantics:** Strictly additive sum ($\sum C_P \frac{A_{h \cap P}}{A_P}$).
- **Population Density Semantics:** Derived as $\text{persons / km}^2 = \text{Count} / 0.098623\text{ km}^2$.
- **Bounding Raster Buffer:** $5,297,719.0$ persons (the $5.408\%$ difference represents boundary 1km pixels spilling outside statutory municipal limits into PCMC and Haveli).

---

## 4. Multi-Sensor Spatial Aggregation Contract

| Native Layer | Native Res | Variable | Operator | Quality Gate | Units |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Landsat 8/9 C2 L2** | $30\text{ m}$ | LST ($^\circ\text{C}$), NDVI, NDBI | Zonal Mean, Median, P75, P90, StdDev | $\ge 70\%$ valid cloud-free pixels | $^\circ\text{C}$, dimensionless index |
| **Sentinel-2 MSI L2A** | $10\text{ m} / 20\text{ m}$ | Current 2025 High-Res NDVI, NDBI | Zonal Mean, Variance | $\ge 80\%$ cloud-free | dimensionless index |
| **WorldPop 2020 UNadj**| $\sim 1\text{ km}$ | Population Count | **Area-Weighted Sum (Conservation)** | Complete AOI coverage | estimated persons |
| **Copernicus GLO-30 DEM**| $30\text{ m}$ | Elevation ($m$), Slope ($^\circ$) | Zonal Mean, Zonal StdDev | 100% valid coverage | meters, degrees |
| **OpenStreetMap** | Vector | Road Length, Facility Counts | Line length sum, Point count | Planar clipping (`EPSG:32643`)| meters, integer count |
| **NASA POWER** | $0.5^\circ \times 0.5^\circ$ | Daily $T_{2m,\max}$, $RH_{2m}$, Radiation | Nearest Grid Point | Complete daily series | $^\circ\text{C}$, %, $\text{MJ/m}^2$ |
| **MODIS Terra/Aqua** | $\sim 1\text{ km}$ | 8-day composite LST | Zonal AOI Mean (Macro Context) | Daily complete | $^\circ\text{C}$ (**NEVER upscaled to 30m**) |

---

## 5. Temporal Feature Contract (2021–2025 Baseline)

The 5-year pre-monsoon baseline encompasses the approved April peak-summer scenes (Canonical DOY 105, Preferred Window 95–115):
- 2021-04-24 (Landsat 8 OLI/TIRS-1, `LC08_L2SP_147047_20210424_02_T1`, DOY 114)
- 2022-04-11 (Landsat 8 OLI/TIRS-1, `LC08_L2SP_147047_20220411_02_T1`, DOY 101)
- 2023-04-22 (Landsat 9 OLI-2/TIRS-2, `LC09_L2SP_147047_20230422_02_T1`, DOY 112)
- 2024-04-16 (Landsat 8 OLI/TIRS-1, `LC08_L2SP_147047_20240416_02_T1`, DOY 107)
- 2025-04-19 (Landsat 8 OLI/TIRS-1, `LC08_L2SP_147047_20250419_02_T1`, DOY 109)

### 5.1 Temporal Semantics & Missing-Data Rules
1. **Annual Cell Eligibility:** A cell is valid in year $k$ iff its unmasked clear pixel coverage $\ge 70\%$.
2. **Baseline Central Tendency:** 5-year arithmetic mean and median computed over valid years, requiring $K_{\text{valid}} \ge 4$. If $K_{\text{valid}} < 4$, marked `INSUFFICIENT_HISTORICAL_COVERAGE`.
3. **Spatial Persistence ($\text{Persistence}_{\text{P75}}$):** Fraction of valid baseline years where cell was in the top quartile of hottest urban areas ($[0.0, 1.0]$), with denominator strictly $K_{\text{valid}}$.
4. **Extreme LST Recurrence ($\text{Recurrence}_{\ge 45^\circ\text{C}}$):** Integer count of valid years where cell mean LST $\ge 45.0^\circ\text{C}$ (CLIMORA methodological threshold, not human heat-health threshold).
5. **Current State:** 2025-04-19 peak-summer observation.
6. **Thermal Anomaly ($\Delta \text{LST}_{2025}$):** Absolute difference and standardized $z$-score relative to historical baseline mean.
7. **Scientific Boundary:** Five annual scenes do **NOT** constitute a 30-year climate trend; they define a **5-Year Pre-Monsoon Microclimatic Baseline**.

---

## 6. Truth-Layer Governance & Label Strategy

Every feature strictly belongs to one of four truth layers:
- `OBSERVED`: Raw instrument measurements, satellite radiance, GLO-30 DEM elevation, WorldPop counts, OSM vectors, NASA POWER meteorology.
- `DERIVED`: Deterministic mathematical functions (NDVI, NDBI, LST in Celsius, Slope, Persistence, Recurrence, Anomalies, Population Density).
- `MODELED`: Composite risk indices, hotspot clustering, intervention cooling projections, optimization allocations.
- `VERIFIED`: Empirical ground truth, post-intervention MRV audit logs, handheld thermal pyrometer measurements.

### 6.1 Risk Target Strategy
- **Ground-Truth Label Audit:** Parcel-level or ward-level heat mortality/morbidity labels do NOT exist in Pune or India.
- **Prohibition:** CLIMORA strictly prohibits fabricating synthetic labels and claiming supervised ML accuracy/F1 scores.
- **Canonical Strategy:**
  1. **IPCC AR6 Conceptual Framework vs CLIMORA Implementation:** Risk is framed conceptually around Hazard, Exposure, and Vulnerability. CLIMORA implements this via a multiplicative power-law aggregation: $\text{Risk}_i = \mathcal{H}_i^{\alpha} \times \mathcal{E}_i^{\beta} \times \mathcal{V}_i^{\gamma}$ (governed under [`data/manifests/risk_parameter_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/risk_parameter_contract.json)), where $\alpha, \beta, \gamma$ default to `1.0` and are classified as `PENDING_METHODOLOGICAL_CALIBRATION`.
  2. **Biophysical Susceptibility vs Socioeconomic Vulnerability:** $\mathcal{V}$ is strictly designated as *Biophysical and Structural Susceptibility* ($1 - \text{NDVI}$, $\text{NDBI}$). True socioeconomic human vulnerability is explicitly classified as *UNAVAILABLE / PENDING STATUTORY SURVEYS*.
  3. **Unsupervised Anomaly Clustering:** Spatial autocorrelation (Local Moran's $I$) isolating High-High acute hotspots.
  4. **Multi-Objective Spatial Optimization (MILP):** Allocating cooling interventions to maximize population-weighted heat hazard reduction.

---

## 7. Logical Analytical Data Model

The analytical database architecture follows the Phase 1A canonical entity specifications:

```text
study_area (pune, EPSG:4326 / EPSG:32643)
    ├── spatial_unit (grid_hex_h9, 3181 records)
    │     ├── spatial_unit_ward_membership (H3 cell ↔ Ward join table)
    │     ├── feature_observation (unit_id, feat_id, obs_date, val_numeric, val_std, confidence)
    │     └── risk_assessment (unit_id, model_run_id, hazard_idx, exposure_idx, vuln_idx, risk_score)
    ├── dataset & dataset_version (landsat-c2-l2, worldpop-2020, glo30-dem, osm, etc.)
    │     └── dataset_asset (raw GeoTIFFs, checksums, footprints)
    ├── processing_run (pipeline provenance, timestamps, parameters)
    │     ├── processing_run_input (asset_id / artifact_id DAG edges)
    │     └── derived_artifact (clipped LST, NDVI, NDBI, Population GeoTIFFs)
    └── feature_definition (28 canonical features across Groups A through J)
```

No database DDL or migrations are prematurely deployed in Phase 1B; all logical models are validated against the manifest contracts.

---

## 8. Multi-Sensor Operational Roles

- **Landsat 8 & 9 (30m):** Authoritative historical baseline (2021–2025) and current thermal state.
- **Sentinel-2 (10m/20m):** Current-state (2025) high-resolution optical reference; strictly isolated from the historical baseline.
- **MODIS (1km):** Synoptic regional thermal context; never upscaled to replace 30m data.
- **NASA POWER (0.5°):** Daily meteorological context on acquisition days.

---

## 9. Parameterized Planning Heuristics (§30)

- **Parameter:** `impervious_roof_fraction_potential = 0.60`
- **Context:** Represents the theoretical upper bound of built roof area suitable for cool roof intervention in dense built-up cells ($\text{NDBI} > 0.10$).
- **Governance:** Parameterized as a user-configurable scenario coefficient; never treated as an observed statistic.

---

## 10. Audit & Decision Record

| Decision | Evidence | Alternatives Evaluated | Consequence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Analytical Unit** | Pune AOI empirical benchmark | 250m Cartesian Grid, H3 Res 8, PMC Wards | H3 Res 9 chosen for isotropic 6-neighbor topology, minimal perimeter-to-area, 64-bit uint64 index, and 9.86 ha micro-neighborhood scale. Wards retained as reporting units. | **FROZEN** |
| **Population Source** | WorldPop 2020 IND UN-adjusted | Gridded Population of the World (GPWv4), Kontur | 18.3 MB official raster validated; dasymetric area-weighted sum achieves 0.0033% conservation against exact statutory polygon. | **FROZEN** |
| **Temporal Semantics** | Validated 5-year Landsat series | 1-year snapshot, synthetic 30-year trend | 5-year pre-monsoon baseline frozen; persistence, recurrence, anomaly defined; no invalid climate change trend claimed. | **FROZEN** |
| **Risk Target Strategy** | Label availability audit | Supervised ML classification, arbitrary weighted index | Supervised ML rejected due to absent ground-truth labels; IPCC AR6 modular $\mathcal{H} \times \mathcal{E} \times \mathcal{V}$ + Unsupervised Anomaly + Spatial MILP optimization adopted. | **FROZEN** |
| **Truth Layers** | Phase 1A governance | Flattened feature schema | 4 strict layers enforced (`OBSERVED`, `DERIVED`, `MODELED`, `VERIFIED`). | **FROZEN** |
| **Sentinel-2 Role** | Phase 1A.8 isolation rule | Merging into 5-year baseline | Kept strictly as 2025 high-res reference; baseline remains pure Landsat. | **FROZEN** |
