# CLIMORA — Phase 1B: Feature Contract, Temporal Semantics & Feature Dictionary

**Document Version:** 1.0.0  
**Phase:** Phase 1B (Analytical Architecture & Decision Gate)  
**Status:** **RATIFIED & FROZEN**  
**Truth-Layer Classification:** Architecture Specification  
**Machine-Readable Contracts:**
- Feature Dictionary: [`data/manifests/feature_dictionary.json`](file:///c:/Users/lenovo/climora/data/manifests/feature_dictionary.json)
- Temporal Contract: [`data/manifests/temporal_feature_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/temporal_feature_contract.json)
- Spatial Aggregation Contract: [`data/manifests/analytical_unit_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/analytical_unit_contract.json)

---

## 1. Spatial Aggregation Contract

The spatial aggregation contract governs the deterministic conversion of multi-scale, multi-sensor native datasets into canonical analytical unit (`grid_hex_h9`, Uber H3 Resolution 9) features.

### 1.1 Multi-Sensor Spatial Aggregation Matrix

| Sensor / Layer | Native Resolution & CRS | Primary Variable(s) | Truth Layer | Spatial Aggregation Operator | Weighting Scheme | Valid-Pixel Threshold | Nodata Handling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Landsat 8/9 C2 L2** | $30\text{ m}$ (`EPSG:32643`) | LST (Celsius), NDVI, NDBI | `OBSERVED` / `DERIVED` | Zonal Mean, Median, P75, P90, StdDev, Min, Max | Equal-area pixel sampling ($\sim 110$ pixels / hex) | $\ge 70\%$ cloud-free pixels within hex | Exclude masked pixels; if $<70\%$ valid, mark cell `INSUFFICIENT_COVERAGE` |
| **Sentinel-2 MSI L2A** | $10\text{ m} / 20\text{ m}$ (`EPSG:32643`) | High-res NDVI (10m), NDBI (20m) | `DERIVED` (Current 2025 Reference Only) | Zonal Mean, Zonal Variance | Equal-area pixel sampling ($\sim 986$ pixels 10m / hex) | $\ge 80\%$ cloud-free pixels | Exclude SCL clouds/shadows |
| **WorldPop 2020 UNadj** | $\sim 1\text{ km}$ ($30''$, `EPSG:4326`) | Population Count (persons/cell) | `OBSERVED` | **Area-Weighted Zonal Sum (Dasymetric Conservation)** | Geometric polygon intersection area: $\sum C_P \frac{A_{h \cap P}}{A_P}$ | Complete AOI coverage | Negative / Nodata $\to 0.0$; verify global sum conservation $\pm 0.1\%$ |
| **Copernicus GLO-30 DEM** | $30\text{ m}$ (`EPSG:32643`) | Elevation ($m$), Slope ($^\circ$) | `OBSERVED` / `DERIVED` | Zonal Mean, Zonal StdDev (Roughness) | Equal-area pixel sampling ($\sim 110$ pixels / hex) | $100\%$ valid | Interpolate fill voids if any |
| **OpenStreetMap (OSM)** | Vector Point/Line/Polygon (`EPSG:4326`) | Road lengths ($m$), Health/School facility counts | `OBSERVED` | Point count within polygon; Line length intersection within polygon; Polygon area intersection | Exact planar clipping in `EPSG:32643` | Complete vector coverage | Empty $\to 0$ |
| **NASA POWER** | $0.5^\circ \times 0.5^\circ$ Grid (`EPSG:4326`) | $T_{2m,\max}$, $RH_{2m}$, $ALLSKY\_SFC\_SW\_DWN$ | `OBSERVED` | Nearest Grid Point / Bilinear Regional Context | Regional synoptic context (applied to all AOI cells for acquisition date) | Daily complete | Fail-closed if acquisition day missing |
| **MODIS Terra/Aqua** | $\sim 1\text{ km}$ ($926.6\text{ m}$, Sinusoidal) | 8-day composite LST ($^\circ\text{C}$) | `OBSERVED` | Zonal Mean over AOI (Macro-thermal context) | Area-weighted | Daily/8-day complete | Macro-climatic validation only; **NEVER downscaled to 30m** |

### 1.2 Raster Aggregation Rules by Variable Type
- **Continuous Variables (LST, NDVI, NDBI, Elevation, Slope):**
  Aggregated using robust central tendency estimators (mean, median) and dispersion metrics (standard deviation, 75th/90th percentiles). Zonal averaging is valid only when valid pixel count $N_{\text{valid}} \ge 0.70 \times N_{\text{total}}$.
- **Additive Count Variables (WorldPop Population):**
  Aggregated strictly using **area-weighted sum conservation**. Averaging population counts across overlapping cells is strictly forbidden, as it violates demographic mass balance.
- **Derived Intensity Variables (Population Density):**
  Calculated strictly as:
  $$D_{\text{pop}, h} = \frac{\text{PopCount}_h}{\text{Area}_h\text{ (km}^2\text{)}} \quad [\text{persons / km}^2]$$
- **Vector Features (OSM Infrastructure):**
  Points (clinics, hospitals, schools) are counted via spatial containment (`ST_Contains`). Linear features (highways, arterial roads) are clipped to hex boundaries and summed by length (`ST_Length`). Polygons (parks, lakes) are intersected and summed by area (`ST_Area`).

---

## 2. Temporal Feature Contract (2021–2025 Baseline)

CLIMORA operates on an audited, frozen 5-year pre-monsoon baseline (Canonical target DOY 105, Preferred window 95–115):
- **2021-04-24** (Landsat 8 OLI/TIRS-1, `LC08_L2SP_147047_20210424_02_T1`, DOY 114)
- **2022-04-11** (Landsat 8 OLI/TIRS-1, `LC08_L2SP_147047_20220411_02_T1`, DOY 101)
- **2023-04-22** (Landsat 9 OLI-2/TIRS-2, `LC09_L2SP_147047_20230422_02_T1`, DOY 112)
- **2024-04-16** (Landsat 8 OLI/TIRS-1, `LC08_L2SP_147047_20240416_02_T1`, DOY 107)
- **2025-04-19** (Landsat 8 OLI/TIRS-1, `LC08_L2SP_147047_20250419_02_T1`, DOY 109)

### 2.1 Scientific Scope & Boundary
**Crucial Scientific Clarification:** Five annual peak-summer satellite observations do **NOT** constitute a "long-term climate change trend" (which requires a 30-year climatological normal according to WMO specifications). Instead, they provide a rigorous **5-Year Pre-Monsoon Microclimatic Baseline** capturing inter-annual variability, structural spatial persistence, and current-state anomalies.

### 2.2 Mathematical Definitions of Temporal Features & Missing-Data Rules
A cell observation is valid in year $k$ iff its clear, unmasked pixel coverage fraction $\ge 0.70$ (`qa_mask == 1`).

#### 1. Baseline Central Tendency
The expected pre-monsoon surface condition across the 5-year historical window:
$$\text{LST}_{\text{baseline\_mean}}(h) = \frac{1}{K_{\text{valid}}} \sum_{k \in \text{valid}} \text{LST}_{k}(h) \quad (K_{\text{valid}} \ge 4)$$
$$\text{LST}_{\text{baseline\_median}}(h) = \text{Median}\left(\{\text{LST}_{k}(h) \mid k \in \text{valid}\}\right) \quad (K_{\text{valid}} \ge 4)$$
$$\text{LST}_{\text{baseline\_std}}(h) = \sqrt{\frac{1}{K_{\text{valid}}-1} \sum_{k \in \text{valid}} \left(\text{LST}_{k}(h) - \text{LST}_{\text{baseline\_mean}}(h)\right)^2}$$
- **Missing Data Policy:** If $K_{\text{valid}} < 4$, the cell is flagged as `INSUFFICIENT_HISTORICAL_COVERAGE`, and baseline statistics evaluate to `null` / `NaN`.

#### 2. Spatial Heat Persistence ($\text{Persistence}_{\text{P75}}$)
Measures whether a cell consistently experiences extreme thermal stress relative to the rest of the city across valid baseline years:
$$\text{Persistence}_{\text{P75}}(h) = \frac{1}{K_{\text{valid}}} \sum_{k \in \text{valid}} \mathbb{I}\left(\text{LST}_{k}(h) \ge P_{75}(\text{LST}_{\text{citywide}, k})\right) \in [0.0, 1.0]$$
Where $P_{75}(\text{LST}_{\text{citywide}, k})$ is the city-wide 75th percentile LST in year $k$, and $\mathbb{I}$ is the indicator function.
- The denominator is strictly $K_{\text{valid}}$, and $K_{\text{valid}}$ is explicitly recorded in cell metadata.

#### 3. Extreme LST Recurrence ($\text{Recurrence}_{\ge 45^\circ\text{C}}$)
The integer count of valid baseline years where the cell's mean LST reached or exceeded the CLIMORA methodological threshold of $45.0^\circ\text{C}$:
$$\text{Recurrence}_{\ge 45}(h) = \sum_{k \in \text{valid}} \mathbb{I}\left(\text{LST}_{k}(h) \ge 45.0^\circ\text{C}\right) \in \{0, 1, 2, 3, 4, 5\}$$
- **Governance:** $45.0^\circ\text{C}$ is a surface temperature threshold for high-albedo radiant heat screening, NOT an epidemiological human air-temperature threshold. If $K_{\text{valid}} < 5$, the cell is flagged as `partial_temporal_record`.

#### 4. Current State (2025 Observation)
The latest validated pre-monsoon observation from 2025-04-19 (DOY 109):
$$\text{LST}_{2025}(h) = \text{ZonalMean}(\text{Landsat 8 LST 2025-04-19}, h)$$

#### 5. Current-State Anomaly ($\Delta \text{LST}_{2025}$)
The absolute thermal deviation of 2025 relative to the 5-year historical baseline:
$$\Delta \text{LST}_{2025}(h) = \text{LST}_{2025}(h) - \text{LST}_{\text{baseline\_mean}}(h) \quad [^\circ\text{C}]$$
$$z_{\text{LST}, 2025}(h) = \frac{\text{LST}_{2025}(h) - \text{LST}_{\text{baseline\_mean}}(h)}{\text{LST}_{\text{baseline\_std}}(h) + \epsilon}$$
- **Eligibility:** Valid iff both $K_{\text{valid}} \ge 4$ and 2025 observation valid pixel coverage $\ge 70\%$.

### 2.3 Cross-Sensor Alignment (Landsat 8 vs Landsat 9)
- **Year 2023** was acquired by Landsat 9 OLI-2/TIRS-2; years 2021, 2022, 2024, 2025 by Landsat 8 OLI/TIRS-1.
- Both sensors are calibrated to USGS Collection 2 Level-2 Surface Reflectance and Surface Temperature standards. Inter-calibration studies (USGS EROS, 2022) confirm cross-sensor temperature agreement within $\pm 0.3\text{ K}$, well within the natural diurnal noise floor.
- No empirical fudge factors are applied; sensor identity is permanently tracked in provenance metadata (`provenance_sensor_id`).

---

## 3. Four Truth Layers Architecture

Every feature in the CLIMORA Feature Dictionary belongs to exactly one Truth Layer:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CLIMORA FOUR TRUTH LAYERS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. OBSERVED                                                                 │
│    Direct physical measurements from calibrated instruments, spatial surveys│
│    • Landsat ST_B10 thermal radiance, QA pixel flags                        │
│    • Sentinel-2 MSI surface reflectances (B02, B03, B04, B08, B11, B12)     │
│    • WorldPop 2020 dasymetric population counts                             │
│    • Copernicus GLO-30 DEM elevation heights                                │
│    • OpenStreetMap surveyed road centrelines, hospital points               │
│    • NASA POWER surface meteorology measurements                            │
│    • MODIS MOD11A2 Land Surface Temperature                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. DERIVED                                                                  │
│    Deterministic mathematical transformations of observed data               │
│    • Normalized Difference Vegetation Index (NDVI)                          │
│    • Normalized Difference Built-Up Index (NDBI)                            │
│    • Land Surface Temperature in Celsius ($T_{\text{Kelvin}} - 273.15$)     │
│    • DEM Slope ($^\circ$) and Aspect                                        │
│    • Historical Baseline Means, Medians, and Standard Deviations            │
│    • Heat Persistence ($P_{75}$) and Extreme Recurrence ($\ge 45^\circ\text{C}$)│
│    • Thermal Anomalies ($\Delta \text{LST}$) and Z-scores                   │
│    • Population Density (persons / km²)                                     │
│    • Road Length Density (km / km²)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. MODELED                                                                  │
│    Outputs of statistical models, clustering algorithms, and optimizations  │
│    • IPCC Composite Risk Index ($\mathcal{H} \times \mathcal{E} \times \mathcal{V}$)│
│    • LISA / Moran's I Hotspot cluster classifications                       │
│    • Projected temperature reduction from cool roof interventions ($\Delta T$)│
│    • Pareto-optimal intervention parcel allocations                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. VERIFIED                                                                 │
│    Field-audited post-intervention measurements and ground truth            │
│    • Handheld thermal infrared pyrometer ground audit logs                  │
│    • Post-cool-roof installation MRV (Measurement, Reporting & Verification)│
│    • PMC municipal councillor signed completion certificates                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Parameterized Planning Assumptions (§30)

To avoid confusing planning heuristics with observed physical realities, the following municipal assumptions are strictly isolated as **Configurable Scenario Parameters**:

### Parameter: `impervious_roof_fraction_potential`
- **Default Value:** `0.60` ($60\%$)
- **Context:** Represents the theoretical upper bound of built roof area suitable for high-albedo cool roof coating within highly built-up H3 cells ($\text{NDBI} > 0.10$).
- **Source:** Municipal cool-roof retrofit guidelines (NRDC / Mahila Housing Trust Ahmedabad & Pune Heat Action Plans).
- **Governance Mandate:** This is **NOT** an observed Pune statistic. It must remain a user-adjustable scenario parameter in optimization runs, never hard-coded as ground truth.
- **Sensitivity Bounds:** Evaluated between $0.30$ (conservative) and $0.75$ (aggressive).

---

## 5. Comprehensive Uncertainty Framework (§27)

Every feature in CLIMORA is subject to documented physical and analytical uncertainties:

| Uncertainty Dimension | Primary Source | Value / Range | Scientific Classification | Action / Governance Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **Measurement Uncertainty** | USGS Landsat Collection 2 Level 2 Surface Temperature (Cook et al. 2014; Malakar et al. 2018) | $\pm 1.0\text{ K}$ to $\pm 1.5\text{ K}$ RMSE | `DOCUMENTED_EXTERNAL` | Formally cited; valid under clear sky and low atmospheric water vapor. Relative anomalies across cells reduce systematic calibration offsets. |
| **Processing Uncertainty** | Surface emissivity, atmospheric correction residuals | $\pm 0.5\text{ K}$ | `CLIMORA_ASSUMPTION` | Reclassified as a methodological sensitivity parameter (unvalidated assumption). |
| **Demographic Disaggregation Uncertainty** | WorldPop 1km dasymetric disaggregation to H3 Res 9 | $\pm 15\%$ | `CLIMORA_ASSUMPTION` | Reclassified as a methodological sensitivity parameter. WorldPop publishes national/coarse validation metrics, but parcel-scale downscaling uncertainty is unquantified at urban hexagon scale in India. |
| **Spatial Aggregation Sampling** | Zonal aggregation across $\sim 110$ Landsat pixels per H3 Res 9 cell | Nominal sample variance $\sigma^2$ | `METHODOLOGICAL_QUALIFICATION` (Formerly `UNSUPPORTED`) | Standard error $\sigma / \sqrt{N}$ is explicitly rejected as a statistical error estimate because adjacent satellite pixels exhibit positive spatial autocorrelation (Moran's $I > 0$). Spatial averaging suppresses uncorrelated high-frequency instrument noise, but effective degrees of freedom are smaller than nominal pixel counts. |
| **Temporal Sampling Uncertainty** | Single peak-summer pre-monsoon morning snapshot (10:30 AM local time) per year | Diurnal range: $10^\circ\text{C}$ to $18^\circ\text{C}$ | `DOCUMENTED_EXTERNAL` | All LST features are explicitly designated as "Morning Peak-Summer Surface Temperature", NEVER to be confused with 24-hr mean ambient air temperature. |
| **Proxy Uncertainty** | Biophysical surface indices ($1 - \text{NDVI}$, $\text{NDBI}$) as proxies for heat susceptibility | Qualitative | `METHODOLOGICAL_BOUNDARY` | Strictly designated as *Biophysical and Structural Susceptibility*. Claims of measuring human poverty or socioeconomic vulnerability are strictly prohibited. |
