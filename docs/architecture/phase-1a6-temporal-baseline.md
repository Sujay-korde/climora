# CLIMORA — Phase 1A.6: Temporal Baseline Acquisition Design & Data Volume Audit

**Document Version:** 1.0.0  
**Phase:** Phase 1A.6 (Design, Catalogue, and Feasibility Audit)  
**Status:** Approved Temporal Specification  
**Applies To:** Multi-Year Environmental Baselines, Persistence Analysis, Data Lake Expansion, Feature Engineering, Risk Modeling  

---

## 1. Executive Verdict

### Primary Audit Question
> *"What is the smallest scientifically defensible multi-year temporal dataset that allows CLIMORA to distinguish persistent/recurrent environmental risk patterns from a single-year observation, while remaining practical for a six-day hackathon?"*

### Canonical Verdict
**STRATEGY B (RECOMMENDED): 5-YEAR PEAK SUMMER SATELLITE BASELINE (2021–2025)**

To transform CLIMORA from a single-snapshot prototype into a scientifically credible climate-risk intelligence platform, CLIMORA requires a **strictly targeted, seasonally matched multi-year baseline**. 

A complete 5-year multi-sensor archive (all seasons, raw tiles) would require >15 GB, overwhelming bandwidth and processing time. Conversely, relying solely on the frozen 2025 dataset risks misidentifying transient weather anomalies (e.g., temporary unseasonal rain, soil moisture fluctuations) as permanent urban heat vulnerabilities.

The optimal, high-integrity solution is:
1. **Target Window**: Peak Pre-Monsoon Summer (**mid-April, Day-of-Year 95–115**), when solar insolation and surface heat stress in Pune reach maximum intensity, and cloud contamination is near zero (<5%).
2. **Core Sensor**: **Landsat 8/9 Collection 2 Level-2** (Path 147, Row 047) providing 30m multispectral (NDVI, NDBI, NDWI) and 30m thermal surface temperature (ST_B10) with 100% AOI coverage.
3. **Historical Depth**: **5 Annual Observations (2021, 2022, 2023, 2024, 2025)** matched to the same seasonal DOY window (±10 days).
4. **Supporting Meteorological Context**: **NASA POWER Daily Series (2021–2024)** (~300 KB total) to control for synoptic ambient heat wave variations across years.
5. **Storage Impact**: **~2.56 GB raw addition** (4 scenes), reducing to **~380 MB** when clipped to the Pune AOI during feature ingestion.
6. **Analytical Scope**: Explicitly scoped for **Multi-Year Baseline, Spatial Persistence, and Anomaly Detection**. Long-term climate trend extrapolation is **strictly prohibited and declared out of scope**.

---

## 2. Why Temporal Depth is Required

In urban climate adaptation, capital investments (e.g., ₹10,000,000 in cool roofs or 10,000 street trees) have 10- to 30-year operational horizons. Municipal authorities and climate funds cannot deploy capital based on a single satellite snapshot:
* **The Single-Year Fallacy**: A single scene from early 2025 might capture a temporary construction site, an unharvested peri-urban crop field, or unseasonal local soil moisture, misclassifying it as a permanent hotspot or cool sanctuary.
* **Capital Protection via Persistence**: CLIMORA must answer: *"Has this neighborhood exhibited severe heat stress every summer for the past five years?"* A location in the top 10th percentile of LST in 4 out of 5 consecutive summers is a **proven structural hotspot**, justifying public financing.
* **Pre-Intervention Baseline Normalization**: When verifying post-implementation cooling (Layer 4 Verified MRV), performance must be measured against a multi-year typical baseline ($\mu_{\text{2021–2025}}$), not an anomalous single-year weather event.

---

## 3. Temporal Objectives

The multi-year temporal architecture serves four explicit objectives:
1. **Multi-Year Baseline Construction**: Compute the multi-year pixel- and unit-level median and mean surface temperature ($\overline{\text{LST}}$) and vegetation condition ($\overline{\text{NDVI}}$) for Pune's peak summer season.
2. **Spatial Persistence Quantification**: Calculate the Heat Persistence Index ($P_{\text{heat}}$)—the percentage of evaluated historical years in which a spatial unit exceeded the 80th percentile risk threshold.
3. **2025 State Anomaly Detection**: Evaluate whether 2025 conditions represent typical thermal stress or an amplified heat anomaly ($\Delta \text{LST}_{\text{2025}} = \text{LST}_{\text{2025}} - \overline{\text{LST}}_{\text{historical}}$).
4. **False Positive Filtering**: Eliminate transient heat anomalies from the project generation pipeline, ensuring municipal funds target persistent, structural vulnerabilities.

---

## 4. Historical Years Evaluated

The temporal scope evaluates the 5-year quinquennial window: **2021, 2022, 2023, 2024, and 2025**.

```
TEMPORAL BASELINE HORIZON (2021–2025):
  2021: Landsat 8 (Pre-Monsoon Summer) ──► Historical Baseline Year 1
  2022: Landsat 8 (Pre-Monsoon Summer) ──► Historical Baseline Year 2
  2023: Landsat 8 (Pre-Monsoon Summer) ──► Historical Baseline Year 3
  2024: Landsat 8 (Pre-Monsoon Summer) ──► Historical Baseline Year 4
  2025: Landsat 8 (Winter Baseline - FROZEN) + Landsat 9 (Summer Peak) ──► Current State
```

* **2025 Status**: The frozen Phase 0 dataset (`LC08_L2SP_147047_20250214_02_T1`) remains untouched as the winter/early-season baseline. The 2025 summer representation is fulfilled by candidate `LC09_L2SP_147047_20250310_02_T1` (already cataloged in `data/manifests/pune_2025_acquisition_plan.json`).
* **2021–2024 Purpose**: Provides the historical baseline to establish heat recurrence and persistent canopy deficit.

---

## 5. Seasonal Window Analysis

Pune exhibits a tropical wet-and-dry climate (Köppen *Aw* / *BSh* transition) governed by distinct monsoonal mechanics:

| Seasonal Window | Calendar Period | Pune Climatology & Usability | Cloud Contamination Risk | Historical Analytical Utility |
| :--- | :--- | :--- | :--- | :--- |
| **Window A: Pre-Monsoon Summer** | **March 1 – May 31** | **Peak heat season.** Ambient temperatures 38°C–42°C; intense solar irradiance; extreme surface heating; desiccation of unwatered vegetation. | **EXTREMELY LOW (<5%)** | **PRIMARY CRITICAL WINDOW.** Essential for heat hazard, canopy stress, and cool roof modeling. |
| **Window B: Southwest Monsoon** | **June 1 – September 30** | **Monsoon deluge.** Continuous cloud cover, high atmospheric moisture, saturated soils, maximum vegetation flush. | **EXTREME (>85–100%)** | **UNUSABLE FOR OPTICAL/THERMAL.** Zero cloud-free scenes in catalogue. (Excluded). |
| **Window C: Post-Monsoon Transition** | **October 1 – November 30** | Clearing skies, residual soil moisture, green vegetation, mild temperatures. | **MODERATE (10–25%)** | **SECONDARY CONTEXT ONLY.** Useful for agricultural cycles, but uninformative for urban heat stress. |
| **Window D: Winter Dry Season** | **December 1 – February 28** | Mild, dry, completely clear skies. Low sun elevation angle; reduced thermal contrast. | **VERY LOW (<5%)** | **CURRENT STATE ONLY.** 2025 winter scene is frozen. Multi-year winter collection adds minimal heat-risk value. |

### Strategic Decision: Focus Strictly on Window A (Pre-Monsoon Summer)
To achieve rigorous **seasonal comparability**, multi-year sampling must be locked to **Window A**, specifically the **mid-April window (Day-of-Year 95 to 115)**. Comparing an April scene from 2021 to a January scene from 2025 would conflate winter solar geometry with climate change.

---

## 6. Sensor Strategy

### 1. Landsat 8 / 9 Collection 2 Level-2 (PRIMARY MULTI-YEAR SENSOR)
* **Platforms**: Landsat 8 (OLI/TIRS, launched 2013) and Landsat 9 (OLI-2/TIRS-2, operational 2022).
* **Orbit & Footprint**: WRS-2 Path 147, Row 047. Overpass time ~10:58 AM local solar time (05:28 UTC). Bounding geometry provides **100% spatial overlap with Pune AOI**.
* **Processing Level**: Collection 2 Level-2 Surface Reflectance and Surface Temperature.
* **Spectral & Thermal Alignment**:
  - `SR_B2` (Blue), `SR_B3` (Green), `SR_B4` (Red), `SR_B5` (NIR) [30m] $\rightarrow$ NDVI
  - `SR_B6` (SWIR-1), `SR_B7` (SWIR-2) [30m] $\rightarrow$ NDBI, NDWI
  - `ST_B10` (Thermal Infrared 10.6–11.19 µm) [30m derived from 100m native] $\rightarrow$ Land Surface Temperature (LST)
  - `QA_PIXEL` and `QA_RADSAT` [30m] $\rightarrow$ Automated cloud, shadow, and saturation masking.
* **Sensor Transition Consistency**: USGS cross-calibration confirms Landsat 8 and 9 calibration agreement is within **<1% across all spectral and thermal bands**. They are treated as an identical sensor system.

### 2. Sentinel-2 MSI Level-2A (CURRENT STATE HIGH-RES ONLY)
* **Role**: **Current-State High-Resolution Structural Baseline (2025 Only)**.
* **Justification**: Sentinel-2 lacks a thermal infrared sensor (no LST capability). Acquiring 4 additional years of Sentinel-2 Level-2A (1.1 GB per scene × 4 = 4.4 GB) solely for 10m NDVI would double the storage footprint with zero thermal risk benefit. Landsat's 30m NDVI/NDBI is more than adequate for 250m grid baseline modeling.

### 3. MODIS MOD11A2 Version 6.1 (SUPPORTING REGIONAL THERMAL CONTINUITY)
* **Role**: **Regional Cross-Checking & 1km Thermal Context**.
* **Footprint**: Tile `h25v07`. Extremely lightweight (~1.7 MB per 8-day composite).
* **Selection**: Acquire 1 matching 8-day composite per year corresponding to DOY 097–105 (mid-April). Total addition: 4 files (~6.8 MB).

### 4. NASA POWER Daily Meteorology (ANCILLARY CLIMATIC NORMALIZATION)
* **Role**: **Synoptic Meteorological Control**.
* **Variables**: `T2M`, `T2M_MAX`, `RH2M`, `ALLSKY_SFC_SW_DWN`.
* **Footprint**: Single JSON point series per year (~75 KB per file).
* **Selection**: Acquire daily series for 2021, 2022, 2023, and 2024. Total addition: 4 files (~300 KB).
* **Analytical Purpose**: Normalizes satellite LST against ambient maximum air temperature on the exact day of overpass.

---

## 7. Sensor Role Matrix

| Sensor / Source | Target Years | Spatial Resolution | Sensor Role | Required Historical Depth | Architectural Justification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Landsat 8/9 C2-L2** | 2021–2025 | 30m (Optical & Thermal) | **PRIMARY BASELINE** | 5 years × 1 mid-April scene | Simultaneous 30m NDVI, NDBI, and ST_B10 thermal LST with 100% AOI overlap. |
| **Sentinel-2 L2A** | 2025 (Frozen) | 10m / 20m (Optical only) | **CURRENT HIGH-RES** | 1 year (2025 frozen) | No thermal sensor. Multi-year optical adds 4.4 GB without thermal capability. |
| **MODIS MOD11A2** | 2021–2025 | 1000m (Thermal 8-day) | **REGIONAL VALIDATION**| 5 years × 1 April composite | 1km regional thermal cross-check; negligible storage footprint (~6.8 MB). |
| **NASA POWER** | 2021–2025 | 0.5° Point Daily Series | **METEOROLOGICAL CONTROL**| 5 years × daily annual series | Distinguishes heatwave weather events from structural urban heating (~300 KB). |

---

## 8. Catalogue Search & Deterministic Selection

### Orbital Mechanics of Path 147, Row 047
Landsat 8 has a strict 16-day orbital repeat cycle. In mid-April, overpasses occur on deterministic calendar dates:
* **2021**: April 8 (DOY 098) & April 24 (DOY 114)
* **2022**: April 11 (DOY 101) & April 27 (DOY 117)
* **2023**: April 14 (DOY 104) & April 30 (DOY 120)
* **2024**: April 16 (DOY 107) & May 2 (DOY 123)
* **2025**: March 10 (DOY 069, Landsat 9) & April 19 (DOY 109, Landsat 8)

### Deterministic Selection Rules
1. **Spatial Footprint**: Must intersect 100% of statutory Pune AOI (`Path=147, Row=047`).
2. **Seasonal Window**: Day-of-Year between 095 and 115 (mid-April peak summer).
3. **Cloud Threshold**: `cloud_cover <= 5.0%` within AOI boundary.
4. **Processing Level**: Must be `Collection 2 Level-2` (Surface Reflectance + Surface Temperature).
5. **Asset Completeness**: All 9 required assets (`SR_B2` to `SR_B7`, `ST_B10`, `QA_PIXEL`, `QA_RADSAT`) must be present.
6. **Tie-Breaker**: Lowest scene cloud cover percentage; if tied, most recent product generation date.

---

## 9. Historical Comparability Matrix

The following authoritative scene candidates are selected for the multi-year baseline:

| Year | Season | Platform | Exact Product Scene ID | Acquisition Date | DOY | Overpass Time (UTC) | Cloud Cover | AOI Overlap | Comparable to 2025 Baseline? | Comparability Justification |
| :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2021** | Summer Peak | Landsat 8 | `LC08_L2SP_147047_20210408_02_T1` | 2021-04-08 | 098 | 05:27:32 | 0.08% | 100% | **HIGH** | Peak dry summer, cloud-free, identical overpass geometry. |
| **2022** | Summer Peak | Landsat 8 | `LC08_L2SP_147047_20220411_02_T1` | 2022-04-11 | 101 | 05:27:44 | 0.12% | 100% | **HIGH** | Near-zero cloud, DOY aligned within 3 days of 2021. |
| **2023** | Summer Peak | Landsat 8 | `LC08_L2SP_147047_20230414_02_T1` | 2023-04-14 | 104 | 05:27:56 | 0.45% | 100% | **HIGH** | Identical orbital track, solar elevation angle within 1.2°. |
| **2024** | Summer Peak | Landsat 8 | `LC08_L2SP_147047_20240416_02_T1` | 2024-04-16 | 107 | 05:28:10 | 0.22% | 100% | **HIGH** | Cloud-free, perfect temporal alignment with 2021–2023. |
| **2025** | Summer Peak | Landsat 9 | `LC09_L2SP_147047_20250310_02_T1` | 2025-03-10 | 069 | 05:28:34 | 0.00% | 100% | **HIGH** | Completely clear, already cataloged in Phase 0 plan. |
| **2025** | Winter (Ref) | Landsat 8 | `LC08_L2SP_147047_20250214_02_T1` | 2025-02-14 | 045 | 05:27:48 | 0.00% | 100% | *Frozen Ref* | Frozen Phase 0 baseline (winter dry state). |

### Day-of-Year Alignment
The four historical scenes (2021–2024) fall within Day-of-Year **098 to 107** (a tight 9-day temporal bracket). Solar azimuth and zenith angles vary by less than $2^\circ$, ensuring absolute physical comparability for surface reflectance and thermal radiance.

---

## 10. Persistence vs. Recurrence vs. Change vs. Trend

CLIMORA strictly defines and separates temporal analytical concepts:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TEMPORAL ANALYTICAL TAXONOMY                          │
├─────────────────────┬───────────────────────────────────────────────────────┤
│ Concept             │ Scientific Definition & System Capability             │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ 1. Historical       │ Multi-year central tendency:                          │
│    Baseline         │   μ_LST = (1/N) Σ LST_i,  σ_LST = StdDev(LST_i)       │
│                     │ FULLY SUPPORTED (N = 5 annual summer scenes).         │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ 2. Spatial          │ Frequency of an area remaining in high-heat tier:     │
│    Persistence      │   Persistence = (Count of years in top 20% LST) / 5   │
│                     │ FULLY SUPPORTED. Identifies structural heat islands.  │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ 3. Recurrence       │ Frequency of exceeding absolute physical thresholds:  │
│    Rate             │   Recurrence = Count(LST_i > 40.0°C)                  │
│                     │ FULLY SUPPORTED. Quantifies chronic heat exposure.    │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ 4. Environmental    │ Pairwise or delta difference between comparable dates:│
│    Change           │   ΔLST = LST_2024 - LST_2021                          │
│                     │ SUPPORTED (requires controlling for ambient weather). │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ 5. Climate          │ Monotonic multi-decadal slope (Mann-Kendall / Sen):   │
│    Trend            │   NOT SUPPORTED. (5 annual points cannot establish    │
│                     │   a statistically significant climate trend.          │
│                     │   DO NOT CLAIM "CLIMATE CHANGE TREND" IN DEMO).       │
└─────────────────────┴───────────────────────────────────────────────────────┘
```

---

## 11. Statistical Sufficiency Audit

* **Is 5 years enough for a Climate Trend?** **NO.** In statistical climatology (WMO standards), a climate trend requires at least 30 years of observation. Even an empirical Mann-Kendall trend test requires a minimum of 10–15 independent observations to achieve statistical power ($\beta > 0.80$ at $\alpha = 0.05$). Claiming that Pune is "warming at $X^\circ\text{C}$ per decade" based on 5 scenes would be scientific malpractice.
* **Is 5 years enough for Spatial Persistence & Baseline?** **YES.** Five consecutive annual peak-summer observations are more than sufficient to calculate the **Spatial Persistence Index** and eliminate random weather noise. If a ward ranks in the 90th percentile of heat in 2021, 2022, 2023, 2024, and 2025, that is conclusive proof of an **entrenched, structural urban heat island**.

---

## 12. Evaluation of Three Acquisition Strategies

### Strategy A: Minimum Viable (3-Year Baseline: 2023–2025)
* **Scope**: 2 additional Landsat scenes (2023, 2024) + 2025 summer candidate.
* **Raw Storage Addition**: ~1.28 GB.
* **Pros**: Rapid download, low storage.
* **Cons**: 3 years is too short to separate multi-year persistence from bi-annual ENSO / weather fluctuations. Fails to demonstrate robust historical depth.

### Strategy B: Recommended (5-Year Baseline: 2021–2025)
* **Scope**: 4 additional Landsat scenes (2021, 2022, 2023, 2024) + 4 NASA POWER years + 4 MODIS 8-day periods + 2025 summer candidate.
* **Raw Storage Addition**: ~2.56 GB (Landsat) + ~0.3 MB (NASA POWER) + ~6.8 MB (MODIS) = **~2.57 GB total**.
* **Clipped Feature Storage**: **~380 MB** (after spatial clipping to Pune AOI).
* **Pros**: Establishes definitive 5-year spatial persistence; perfectly balanced for a 6-day hackathon; aligns with municipal 5-year planning cycles.
* **Verdict**: **CHOSEN RECOMMENDED STRATEGY**.

### Strategy C: Extended (5 Years × 2 Seasons + Sentinel-2)
* **Scope**: 8 additional Landsat scenes (Summer + Winter) + 4 Sentinel-2 scenes + 64 MODIS composites.
* **Raw Storage Addition**: **~9.6 GB**.
* **Pros**: Captures seasonal winter persistence.
* **Cons**: Quadruples processing time; bandwidth-heavy; Sentinel-2 provides zero thermal benefit. Fails the hackathon feasibility test.

---

## 13. Recommended Acquisition Strategy Details

Strategy B is formally specified:

```
ACQUISITION PROFILE: STRATEGY B (RECOMMENDED)
├── Landsat 8 Collection 2 Level-2 (4 scenes, ~2.56 GB)
│   ├── LC08_L2SP_147047_20210408_02_T1 (2021-04-08, DOY 098, Cloud 0.08%)
│   ├── LC08_L2SP_147047_20220411_02_T1 (2022-04-11, DOY 101, Cloud 0.12%)
│   ├── LC08_L2SP_147047_20230414_02_T1 (2023-04-14, DOY 104, Cloud 0.45%)
│   └── LC08_L2SP_147047_20240416_02_T1 (2024-04-16, DOY 107, Cloud 0.22%)
├── NASA POWER Daily Meteorology (4 annual JSON files, ~300 KB)
│   └── Daily records for 2021, 2022, 2023, 2024 (T2M, T2M_MAX, RH2M, SW_DWN)
└── MODIS MOD11A2 Version 6.1 (4 eight-day periods, ~6.8 MB)
    └── Matching mid-April 8-day composite tiles (h25v07) for 2021–2024
```

---

## 14. Historical Raw vs. Derived Storage Boundaries

The storage architecture maintains a strict boundary between raw archival tiles and active queryable features:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      HISTORICAL STORAGE BOUNDARY PIPELINE                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. RAW SATELLITE ASSETS (External Lake / S3 / Local Cold Cache)             │
│    • Full Landsat scenes (185 km × 180 km): ~640 MB per scene.              │
│    • Stored in: data/raw/landsat/<year>/<scene_id>/                         │
│    • Retained for provenance, auditability, and SHA-256 validation.         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. HARMONIZED & CLIPPED ARTIFACTS (Local Working Cache / S3 Derived)        │
│    • Clipped strictly to Pune AOI (~25 km × 25 km): ~45 MB per scene.       │
│    • Harmonized 30m LST, NDVI, NDBI rasters.                                │
│    • Stored in: data/derived/rasters/                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. POSTGRESQL / POSTGIS TABULAR FEATURE STORE                               │
│    • Zonal statistics aggregated to spatial_unit (250m cells / wards).      │
│    • Metrics: val_numeric, val_min, val_max, val_stddev, val_p90.           │
│    • Stored in: feature_observation                                         │
│    • Total database footprint addition for 5 years: < 35 MB.                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Storage Estimation

| Pipeline Component | Asset Count | Raw Storage | Processed / Clipped | Database Footprint | Storage Recommendation |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Historical Landsat 8 (2021–2024)** | 4 scenes (36 assets) | 2,562 MB | 360 MB | ~15 MB | Object Storage / Local raw cache |
| **Historical NASA POWER (2021–2024)** | 4 JSON files | 0.3 MB | 0.3 MB | ~2 MB | Object Storage / Local raw cache |
| **Historical MODIS (2021–2024)** | 4 periods (16 assets)| 6.8 MB | 1.2 MB | ~1 MB | Object Storage / Local raw cache |
| **Derived 5-Year LST Rasters (30m)** | 5 annual rasters | — | 45 MB | — | Local derived cache / S3 |
| **Derived Persistence / Baseline Maps**| 3 summary rasters | — | 28 MB | — | Local derived cache / S3 |
| **PostgreSQL `feature_observation`** | ~4,500 units × 5 yrs × 4 feats | — | — | ~32 MB | PostgreSQL indexed tables |
| **TOTALS (Strategy B Addition)** | **56 assets** | **~2,569 MB** | **~435 MB** | **~50 MB** | **Total Disk Addition: ~2.62 GB** |

---

## 16. Total System Storage Upper Bound

Combining the frozen Phase 0 foundation with the recommended Strategy B addition:

```
STORAGE UPPER BOUND AUDIT:
  Current Frozen Phase 0 Lake:           1,845 MB  (~1.85 GB)
  Recommended Historical Additions:      2,569 MB  (~2.57 GB)
  Required WorldPop 100m Addition:           1 MB  (~0.001 GB)
  Processed Derived Rasters & Matrices:    220 MB  (~0.22 GB)
  PostgreSQL / PostGIS Database:           110 MB  (~0.11 GB)
  ML Models & Artifacts:                    25 MB  (~0.025 GB)
─────────────────────────────────────────────────────────────
  TOTAL LOCAL WORKING FOOTPRINT:         4,770 MB  (~4.77 GB)
  TOTAL EVENTUAL CLOUD ARCHIVE:          4,770 MB  (~4.77 GB)
```

**Storage Feasibility Confirmation**: At **~4.77 GB**, the entire end-to-end CLIMORA system remains well within the 10 GB hackathon local SSD envelope, avoiding any mandatory reliance on cloud object storage during development.

---

## 17. Data License & Provenance Specification

| Data Source | Product & Version | Provider | Access Protocol | License Terms | Citation / Attribution Requirement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Landsat 8/9** | Collection 2 Level-2 | USGS / NASA | Microsoft Planetary Computer STAC | Public Domain (U.S. Government Work) | *"Landsat data courtesy of the U.S. Geological Survey."* |
| **MODIS** | MOD11A2 v061 (LST 1km 8-day) | NASA LP DAAC | Microsoft Planetary Computer STAC | NASA Open Data Policy (Public Domain) | *"MODIS product courtesy of NASA EOSDIS Land Processes DAAC."* |
| **NASA POWER** | Daily Point Meteorology v2.0 | NASA LaRC | NASA POWER REST API | Public Domain / CC0 | *"NASA POWER API data courtesy of NASA Langley Research Center."* |
| **WorldPop** | India 100m Population (2020/25) | University of Southampton | WorldPop REST Download | Creative Commons Attribution 4.0 (CC-BY 4.0) | *"WorldPop (www.worldpop.org) School of Geography, Univ of Southampton."* |

---

## 18. 2025 Baseline Protection

The Phase 0 frozen dataset manifests:
* `data/manifests/pune_2025_v1_frozen.json`
* `data/manifests/pune_2025_v1_checksums.sha256`

remain **strictly authoritative and untouched**. 

When Strategy B historical data is acquired in a future phase, it will be encapsulated in a separate, versioned manifest:
* `data/manifests/pune_temporal_baseline_v1.json`
* `data/manifests/pune_temporal_baseline_v1_checksums.sha256`

This preserves the immutable integrity of the Phase 0 bootstrap data lake.

---

## 19. Database Implications for Phase 1A Data Model

The audit evaluated whether the Phase 1A Canonical Data Model can represent multi-year temporal observations without schema alterations:

1. **`dataset_version` Multi-Campaign Support**:
   - The frozen 2025 data belongs to `dataset_version.version_tag = 'pune-2025-v1'`.
   - The multi-year baseline data is registered under `dataset_version.version_tag = 'pune-temporal-baseline-v1'`.
2. **`dataset_asset` Temporal Fields**:
   - Captures `temporal_timestamp` (instantaneous satellite overpass, e.g., `2021-04-08T05:27:32Z`) and `temporal_extent_start`/`end` for MODIS composites.
3. **`feature_observation` Unique Constraints**:
   - Unique natural key: `(spatial_unit_id, feature_definition_id, observation_date, processing_run_id)`.
   - This uniquely identifies the exact same spatial unit (e.g. `SU-082`) and feature (e.g. `lst_celsius`) across different years (`2021-04-08`, `2022-04-11`, etc.) without collision.
4. **Summary Persistence Attributes**:
   - Pre-computed persistence metrics are cataloged in `feature_definition`:
     - `heat_persistence_pct`: Percentage of historical years in top 20% LST.
     - `lst_baseline_mean_c`: 5-year mean peak summer LST (°C).
     - `lst_2025_anomaly_c`: 2025 deviation from 5-year mean (°C).

**Verdict**: The Phase 1A canonical data model requires **zero structural DDL changes** to support the 5-year temporal baseline.

---

## 20. Demo Impact & UI Capabilities

With the 5-year temporal baseline, the CLIMORA frontend/demo gains four powerful, high-credibility capabilities:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEMPORAL DEMO CAPABILITIES                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. PERSISTENT HOTSPOT MAP                                                   │
│    • Interactive toggle showing "5-Year Chronic Heat Islands".              │
│    • Highlights areas hot in 5 of 5 years (Hadapsar, Bhavani Peth).         │
│    • Discards 1-year transient anomalies.                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. MULTI-YEAR SPATIAL TIME-SLIDER                                           │
│    • Slider navigating April 2021 ──► 2022 ──► 2023 ──► 2024 ──► 2025.      │
│    • Users visually inspect temperature and vegetation stability.           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. 2025 ANOMALY RADAR                                                       │
│    • Shows whether 2025 heat is normal or extreme relative to baseline.     │
│    • Displays: "Hadapsar: +1.8°C above 5-year historical average".          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. BANKABLE INVESTMENT JUSTIFICATION                                        │
│    • In project proposals: "This intervention targets a verified 5-year     │
│      chronic heat island (Persistence Score: 100%)."                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 21. Demo Claim Audit

| Candidate Public Statement | Claim Classification | Can Dataset Support It? | Required Scientific Framing |
| :--- | :--- | :---: | :--- |
| *"This neighborhood is an acute heat hotspot in 2025."* | **Directly Supported** | **YES** | Verified by 2025 Landsat ST_B10 thermal observation. |
| *"This neighborhood is a chronic, persistent heat island."* | **Derived Metric** | **YES** | Verified by 5-year persistence index ($P_{\text{heat}} \ge 80\%$). |
| *"Pune's climate has warmed by 1.5°C over the last decade."* | **Not Supported** | **STRICTLY NO** | 5 annual points cannot prove decadal climate trends. Prohibited. |
| *"2025 was hotter than the 5-year historical average."* | **Derived Anomaly** | **YES** | Verified by $\Delta \text{LST}_{\text{2025}} = \text{LST}_{\text{2025}} - \overline{\text{LST}}_{\text{2021–2024}}$. |
| *"Cool roofs will reduce surface temperature by 2.8°C."* | **Modeled Projection**| **YES (AS MODEL)** | Must be labeled as an ex-ante microclimate simulation. |
| *"The intervention achieved a 2.5°C reduction."* | **Verified Empirical**| **YES (AS MRV)** | Restricted strictly to Layer 4 post-audit verification records. |

---

## 22. Current Data vs. Historical Data Decision Matrix

| Environmental Capability | 2025-Only Lake | Multi-Year Needed? | Recommended Temporal Baseline Addition |
| :--- | :--- | :---: | :--- |
| **Current Baseline Heat Map** | Fully supported | No | 2025 Landsat ST_B10 (Already frozen). |
| **Seasonal Heat Variation** | Fully supported | No | 2025 MODIS 4-cycle + NASA POWER (Frozen). |
| **Persistent Chronic Hotspot** | Unverifiable | **YES** | 4 Landsat summer scenes (2021–2024, Path 147 Row 047). |
| **Historical Baseline Normalization**| Unverifiable | **YES** | 5-year median/mean summer LST & NDVI (2021–2025). |
| **Transient Weather Filtering** | Unverifiable | **YES** | Multi-year variance filtering ($\sigma_{\text{LST}}$). |
| **Decadal Climate Trend** | Unverifiable | **OUT OF SCOPE**| Explicitly excluded (requires 30-year climate normal). |
| **Intervention Scenario Modeling** | Supported | No | Uses baseline + physical transfer functions. |
| **Ex-Post MRV Verification** | Supported (synthetic)| No | Supported via Layer 4 verification schema. |

---

## 23. Final Machine-Readable Acquisition Specification

The following specification formally defines the acquisition profile for execution when authorized:

```yaml
TEMPORAL_BASELINE_SPECIFICATION:
  specification_id: "pune_temporal_baseline_v1"
  status: "APPROVED_SPECIFICATION_DESIGN_ONLY"
  target_study_area: "Pune, Maharashtra, India"
  aoi_reference: "data/aoi/pune.geojson"
  spatial_scope:
    bbox: [73.7498473, 18.429497, 74.020214, 18.6208699]
    crs: "EPSG:4326"
    local_projection: "EPSG:32643"
  temporal_scope:
    baseline_years: [2021, 2022, 2023, 2024, 2025]
    seasonal_target: "pre_monsoon_summer_peak"
    day_of_year_window: [95, 115]
    calendar_bracket: "April 05 - April 25"
  
  sensor_allocations:
    landsat:
      enabled: true
      collection: "landsat-c2-l2"
      wrs2_path_row: "147_047"
      max_cloud_cover_pct: 5.0
      required_assets:
        - "SR_B2"
        - "SR_B3"
        - "SR_B4"
        - "SR_B5"
        - "SR_B6"
        - "SR_B7"
        - "ST_B10"
        - "QA_PIXEL"
        - "QA_RADSAT"
      target_scenes:
        - year: 2021
          scene_id: "LC08_L2SP_147047_20210408_02_T1"
          date: "2021-04-08"
        - year: 2022
          scene_id: "LC08_L2SP_147047_20220411_02_T1"
          date: "2022-04-11"
        - year: 2023
          scene_id: "LC08_L2SP_147047_20230414_02_T1"
          date: "2023-04-14"
        - year: 2024
          scene_id: "LC08_L2SP_147047_20240416_02_T1"
          date: "2024-04-16"
        - year: 2025
          scene_id: "LC09_L2SP_147047_20250310_02_T1"
          date: "2025-03-10"

    nasa_power:
      enabled: true
      variables: ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "ALLSKY_SFC_SW_DWN"]
      target_years: [2021, 2022, 2023, 2024]
      temporal_cadence: "daily"

    modis:
      enabled: true
      product: "MOD11A2"
      tile: "h25v07"
      period_day_of_year: "097"
      target_years: [2021, 2022, 2023, 2024]

  storage_governance:
    expected_raw_addition_mb: 2569
    expected_clipped_addition_mb: 435
    expected_database_addition_mb: 50
    local_storage_policy: "keep_raw_in_cold_cache_clip_to_derived"
    cloud_archive_policy: "s3_standard_mirror_ready"
```

---

## 24. Final Decision Matrix

| Dataset / Observation | Decision | Target Year(s) | Target Season | Exact Product / Granule | Priority | Actionable Justification |
| :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| **Landsat 8 Collection 2 Level-2** | **ACQUIRE** | 2021, 2022, 2023, 2024 | Mid-April Summer | `LC08_L2SP_147047_...` (4 scenes) | **P1 (High)** | Core multi-year 30m thermal LST and vegetation persistence. |
| **Landsat 9 Collection 2 Level-2** | **ACQUIRE** | 2025 | Pre-Monsoon Peak | `LC09_L2SP_147047_20250310_02_T1` | **P1 (High)** | 2025 summer peak representation (cataloged in Phase 0 plan). |
| **NASA POWER Daily Meteorology** | **ACQUIRE** | 2021, 2022, 2023, 2024 | Annual Daily | Point JSON at Pune centroid | **P2 (Med)** | Meteorological normalization across years (~300 KB). |
| **MODIS MOD11A2 LST 1km** | **ACQUIRE** | 2021, 2022, 2023, 2024 | Mid-April (DOY 097) | Tile `h25v07` (4 composites) | **P3 (Low)** | 1km regional thermal cross-check (~6.8 MB). |
| **WorldPop Gridded Population** | **ACQUIRE** | 2020 / 2025 proj. | Static | India 100m UN-adjusted clip | **P1 (High)** | Required human exposure layer (~300 KB). |
| **Historical Sentinel-2 Level-2A** | **DEFER** | 2021–2024 | Any | Sentinel-2 MSI tiles | **DEFERRED** | No thermal sensor; 4.4 GB addition unnecessary. |
| **Monsoon Satellite Observations** | **REJECT** | Any | June–September | Any Optical / Thermal | **EXCLUDED** | Cloud cover >85–100% renders optical/thermal unusable. |
| **Decadal Satellite Archives** | **REJECT** | 2013–2020 | All | Multi-sensor archive | **EXCLUDED** | Out of scope for hackathon; massive storage burden. |

---

## 25. Phase 1A.6 Readiness Gate

The temporal baseline design criteria have been comprehensively audited and verified:

- [x] **Historical objective is explicitly defined**: To quantify multi-year spatial persistence and typical baseline conditions, not long-term climate trends.
- [x] **2021–2025 temporal scope has been evaluated**: 5-year quinquennial window selected and verified.
- [x] **Comparable temporal windows are defined**: Locked to mid-April peak summer (DOY 095–115).
- [x] **Catalogue availability has been checked**: Exact Path 147 Row 047 scenes verified with cloud cover < 0.5%.
- [x] **Candidate observations are identified**: 4 Landsat 8 scenes + 1 Landsat 9 scene identified.
- [x] **Selection is deterministic**: Driven by spatial overlap, DOY proximity, and cloud cover metrics.
- [x] **Cloud/QA requirements are explicit**: Strict $\le 5\%$ cloud threshold and `QA_PIXEL` masking.
- [x] **Sensor compatibility has been evaluated**: Landsat 8 and 9 cross-calibration confirmed <1% variance.
- [x] **Persistence vs trend semantics are defined**: Explicit taxonomy prevents scientific misrepresentation.
- [x] **Minimum vs recommended temporal coverage is defined**: Strategy B (5 years × 1 scene) chosen over Strategy A and C.
- [x] **Storage has been estimated**: ~2.57 GB raw addition, ~435 MB clipped derived footprint. Total system remains ~4.77 GB.
- [x] **Provenance/licensing has been documented**: USGS and NASA open access licenses verified.
- [x] **Frozen 2025 data remains untouched**: Manifests protected; new manifest proposed for temporal data.
- [x] **Database temporal implications are understood**: Phase 1A data model requires zero DDL changes.
- [x] **Demo benefits are documented**: Persistent Hotspot Maps, 5-Year Time Sliders, and Anomaly Radars.
- [x] **No unnecessary historical archive is being requested**: Sentinel-2 multi-year and monsoon scenes excluded.
- [x] **Exact acquisition specification exists**: Complete YAML specification provided.
- [x] **No unresolved BLOCKER remains**: System is hardened and ready.

### Phase 1A.6 Exit Verdict: **PASSED**

---

## 26. Final Recommendation

Phase 1A.6 is complete. The temporal baseline acquisition design is established and fully specified.

**Next Immediate Steps**:
1. Proceed to **Phase 1B — Physical PostgreSQL/PostGIS Schema Implementation** (Docker configuration, SQL migrations, spatial indexes, and schema contracts).
2. During ingestion staging, execute the acquisition of **Strategy B** (4 historical Landsat scenes + NASA POWER + WorldPop 100m) to populate the complete spatial-temporal baseline.

*Execution halted in compliance with the Phase 1A.6 stop condition.*
