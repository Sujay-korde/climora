# CLIMORA — Phase 1A.7: Historical Temporal Dataset Acquisition, Validation & Dataset Freeze

**Document Version:** 2.0.0 (Post-Amendment A1 Execution & Dataset Freeze)  
**Phase:** Phase 1A.7 (Historical Acquisition, Validation & Dataset Freeze)  
**Status:** **PASSED & DATASET FROZEN**  
**Applies To:** Multi-Year Environmental Baselines, Data Lake Expansion, Remote Sensing Provenance, Dataset Freeze Governance  
**Authoritative Frozen Manifest:** [`data/manifests/pune_temporal_baseline_v1_frozen.json`](file:///c:/Users/lenovo/climora/data/manifests/pune_temporal_baseline_v1_frozen.json)  
**Authoritative Checksums Manifest:** [`data/manifests/pune_temporal_baseline_v1_checksums.sha256`](file:///c:/Users/lenovo/climora/data/manifests/pune_temporal_baseline_v1_checksums.sha256)  

---

## 1. Executive Summary

Phase 1A.7 has successfully executed the complete acquisition, validation, checksumming, and formal freezing of the **5-year peak-summer temporal baseline (2021–2025)** for Pune, India, following ratification of the **Phase 1A.7.1 Amendment A1** acquisition contract.

### Key Milestones Completed:
1. **Frozen Lake Protection:** All 44 authoritative Phase 0 assets verified 100% byte-for-byte intact before and after historical ingestion.
2. **STAC Catalogue Revalidation:** Pre-download catalogue revalidation confirmed metadata, platforms, dates, WRS-2 Path/Row (147/047), and asset availability for all 5 target scenes.
3. **NASA POWER Ingestion:** Acquired 4 historical annual daily meteorological JSON files (2021–2024; 1,461 daily records total); reused frozen 2025 file without duplication.
4. **MODIS Ingestion:** Acquired 16 historical MOD11A2 v061 GeoTIFF assets (2021–2024, DOY 105 composite, tile `h25v07`); reused frozen 2025 MODIS assets without duplication.
5. **Landsat Ingestion:** Acquired 45 Landsat Collection 2 Level-2 GeoTIFF assets across the 5 approved peak-summer scenes (1 scene per year, 9 assets per scene) via atomic `.part` transfer and hash verification.
6. **QA_PIXEL AOI Cloud Validation:** Evaluated cloud contamination over the statutory Pune Municipal Corporation AOI. All 5 observations demonstrated $\le 1.71\%$ AOI cloud contamination (well below the $\le 5.0\%$ quality gate).
7. **Storage Measurement:** Measured actual storage footprint: **3.211 GB (2.990 GiB)** of new raw data acquired, resulting in a total raw lake footprint of **5.192 GB (4.835 GiB)** across 109 verified files.
8. **Freeze Gate Status:** **PASSED**. Manifests generated and dataset frozen.

---

## 2. Acquisition Scope & Inventory

The authoritative raw data lake now houses the complete 5-year temporal baseline:

| Dataset Category | Historical Files Acquired (Phase 1A.7) | Reused Frozen Files (Phase 0) | Total Lake Files | Status |
| :--- | :---: | :---: | :---: | :--- |
| **Landsat C2 L2 (30m)** | 45 GeoTIFFs (5 scenes × 9 bands) | 9 GeoTIFFs (2025 winter scene) | 54 GeoTIFFs | VALID & FROZEN |
| **MODIS MOD11A2 (1km)** | 16 GeoTIFFs (4 years × 4 bands) | 16 GeoTIFFs (4 periods in 2025) | 32 GeoTIFFs | VALID & FROZEN |
| **NASA POWER Daily** | 4 JSON files (2021–2024) | 1 JSON file (2025 daily series) | 5 JSON files | VALID & FROZEN |
| **Copernicus DEM (GLO-30)** | 0 (Reused Phase 0) | 1 GeoTIFF tile | 1 GeoTIFF | VALID & FROZEN |
| **OpenStreetMap Layers** | 0 (Reused Phase 0) | 4 GeoJSON layers | 4 GeoJSONs | VALID & FROZEN |
| **Sentinel-2 L2A (10m)** | 0 (Reused Phase 0 structural) | 11 GeoTIFF bands | 11 GeoTIFFs | VALID & FROZEN |
| **Metadata / Sidecars** | 4 JSON sidecars | 2 JSON files | 6 JSON files | VALID & FROZEN |
| **TOTAL** | **65 assets** | **44 assets** | **109 assets** | **PASSED** |

---

## 3. Temporal Audit Table

Every acquired Landsat observation satisfies canonical DOY target $\text{DOY} = 105$, preferred seasonal window $[95, 115]$, hard maximum offset limit $\le 15\text{ days}$, and AOI cloud contamination $\le 5.0\%$:

| Year | Platform | Scene ID | Overpass Date | DOY | Offset (DOY 105) | STAC Scene Cloud | Pune AOI Cloud | Pune AOI Shadow | Validation Result |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2021** | Landsat 8 | `LC08_L2SP_147047_20210424_02_T1` | 2021-04-24 | 114 | 9 days | 0.88% | **0.00%** | 0.00% | **PASSED_VALID** |
| **2022** | Landsat 8 | `LC08_L2SP_147047_20220411_02_T1` | 2022-04-11 | 101 | 4 days | 15.21% | **1.71%** | 3.22% | **PASSED_VALID** |
| **2023** | Landsat 9 | `LC09_L2SP_147047_20230422_02_T1` | 2023-04-22 | 112 | 7 days | 0.09% | **0.00%** | 0.03% | **PASSED_VALID** |
| **2024** | Landsat 8 | `LC08_L2SP_147047_20240416_02_T1` | 2024-04-16 | 107 | 2 days | 4.01% | **0.00%** | 0.00% | **PASSED_VALID** |
| **2025** | Landsat 8 | `LC08_L2SP_147047_20250419_02_T1` | 2025-04-19 | 109 | 4 days | 0.35% | **0.00%** | 0.00% | **PASSED_VALID** |

*Note: In 2022, while the scene-wide cloud cover was 15.21% due to clouds over the Western Ghats ridgeline far to the west, pixel-level extraction over the statutory Pune Municipal Corporation polygon confirms Pune AOI cloud contamination is only 1.71%, which is fully compliant with the $\le 5.0\%$ spatial quality gate.*

---

## 4. Spatial Audit

| Parameter | Specification | Evaluated Actual | Compliance Status |
| :--- | :--- | :--- | :---: |
| **Statutory AOI** | Pune Municipal Corporation (`data/aoi/pune.geojson`) | `[73.7498473, 18.429497, 74.020214, 18.6208699]` | PASSED |
| **Landsat Coordinate Reference System** | `EPSG:32643` (WGS 84 / UTM Zone 43N) | `EPSG:32643` across all 45 GeoTIFFs | PASSED |
| **Landsat Native Resolution** | 30.0 m × 30.0 m | 30.0 m × 30.0 m (Thermal resampled to 30m in L2) | PASSED |
| **Landsat Dimensions** | Standard Level-2 Frame | 7,651 × 7,781 pixels (nominal) | PASSED |
| **Landsat AOI Intersection & Coverage** | 100% statutory coverage without nodata voids | 346,809 valid Pune AOI pixels across all scenes | PASSED |
| **MODIS Projection & Grid** | MODIS Sinusoidal Tile `h25v07` | Custom Sinusoidal Grid (`+proj=sinu +R=6371007.181`) | PASSED |
| **MODIS Resolution** | 1.0 km (nominal) | 926.625 m × 926.625 m (1,200 × 1,200 pixels) | PASSED |
| **NASA POWER Spatial Grid** | MERRA-2 Global Grid (0.5° × 0.625°) | Single-point series at `[73.8735, 18.5279]` | PASSED |

---

## 5. Integrity Audit

- **Files Expected:** 65 new historical assets (45 Landsat + 16 MODIS + 4 NASA POWER) + 44 frozen Phase 0 assets = 109 total.
- **Files Acquired:** 65 new historical assets.
- **Files Validated:** 109 / 109 files validated (100%).
- **Checksums Passed:** 109 / 109 files pass SHA-256 integrity verification against [`pune_temporal_baseline_v1_checksums.sha256`](file:///c:/Users/lenovo/climora/data/manifests/pune_temporal_baseline_v1_checksums.sha256).
- **Failures / Corruptions:** 0. Zero `.part` files remain on disk.
- **Test Suite Results:** 23 / 23 pytest tests pass (`tests/test_ingestion.py` and `tests/test_temporal_governance.py`).

---

## 6. Storage Audit (Actual Measurements)

All storage values are empirically measured from the live filesystem. Convention: $1\text{ GiB} = 1,024^3\text{ bytes} \approx 1.074\times 10^9\text{ bytes}$; $1\text{ MiB} = 1,024^2\text{ bytes}$.

| Storage Component | Actual Bytes | Megabytes (MiB) | Gigabytes (GiB) |
| :--- | --: | --: | --: |
| **Existing Frozen Raw (Phase 0 Lake)** | 1,981,009,311 B | 1,889.24 MiB | 1.845 GiB |
| **New Landsat Raw (45 GeoTIFFs)** | 3,196,458,468 B | 3,048.38 MiB | 2.977 GiB |
| **New MODIS Raw (16 GeoTIFFs)** | 13,942,237 B | 13.30 MiB | 0.013 GiB |
| **New NASA POWER Raw (4 JSON files)** | 288,260 B | 0.27 MiB | 0.0003 GiB |
| **New Historical Raw Total** | **3,210,688,965 B** | **3,061.95 MiB** | **2.990 GiB** |
| **Final Authoritative Raw Temporal Lake** | **5,191,698,276 B** | **4,951.19 MiB** | **4.835 GiB** |

*Note: The actual new raw temporal footprint (2.990 GiB) is within 7% of the Phase 1A.6 planning estimate (3.203 GiB) due to dynamic deflate compression efficiency in Landsat Collection 2 surface reflectance bands.*

---

## 7. Provenance & Retrieval Audit

1. **Landsat Collection 2 Level-2:**
   - **Provider:** USGS / NASA via Microsoft Planetary Computer STAC API.
   - **STAC Endpoint:** `https://planetarycomputer.microsoft.com/api/stac/v1`
   - **Collection ID:** `landsat-c2-l2`
   - **Processing Level:** Collection 2 Level-2 Surface Reflectance and Surface Temperature.
   - **Access Method:** SAS-token authenticated chunked HTTPS stream to atomic `.part` with SHA-256 verification.
2. **MODIS MOD11A2 Version 061:**
   - **Provider:** NASA LP DAAC via Microsoft Planetary Computer STAC API.
   - **Collection ID:** `modis-11A2-061`
   - **Product:** Land Surface Temperature and Emissivity 8-Day Global 1km SIN Grid.
   - **Tile:** `h25v07`
3. **NASA POWER Daily Meteorology:**
   - **Provider:** NASA Langley Research Center POWER Project.
   - **API Endpoint:** `https://power.larc.nasa.gov/api/temporal/daily/point`
   - **Community:** Agrometeorology (`ag`)
   - **Variables:** `T2M`, `T2M_MAX`, `T2M_MIN`, `RH2M`, `WS10M`, `PRECTOTCORR`, `ALLSKY_SFC_SW_DWN`.

---

## 8. Excluded and Deferred Data

In compliance with project data governance:
- **Historical Sentinel-2 L2A:** Strictly **EXCLUDED**. Multi-year historical Sentinel-2 data lacks a thermal infrared sensor; adding ~4.5 GB of historical optical imagery without thermal capabilities would consume storage without advancing heat risk intelligence. The high-resolution 2025 Sentinel-2 structural observation is retained in the frozen lake for urban morphology cross-referencing.
- **Monsoon Optical Archive:** Strictly **EXCLUDED**. Monsoonal cloud cover over Pune exceeds 85–100% during July–August, rendering optical and thermal sensors unusable.
- **WorldPop Gridded Population:** **DEFERRED**. Will be acquired during a dedicated demographic ingestion phase prior to Layer 4 social vulnerability risk modeling.
- **Cloud S3 Mirror & Database DDL:** **DEFERRED**. Maintained local-only until schema implementation in Phase 1B.

---

## 9. Limitations & Analytic Caveats

Downstream analysis in Phase 1A.8 and beyond must observe these explicit scientific limitations:
1. **Seasonal Snapshot Baseline:** The 5-year baseline represents peak pre-monsoon summer conditions (DOY 101–114) and does not represent continuous annual phenology or winter temperatures.
2. **Monsoon Optical Void:** Satellite thermal infrared observation is fundamentally interrupted during the southwest monsoon (June–September) due to cloud opacity.
3. **Multi-Platform Provenance:** The Landsat baseline comprises four Landsat 8 observations (2021, 2022, 2024, 2025) and one Landsat 9 observation (2023). Downstream processing must preserve platform identity as metadata.
4. **Resolution Differences:** Landsat Level-2 products have a native 30m resolution (thermal resampled from 100m OLI/TIRS), whereas MODIS has a native 1km Sinusoidal resolution and NASA POWER operates on a 0.5° × 0.625° grid. MODIS is an ancillary regional control, not a 30m baseline.

---

## 10. Sensor Governance Compliance Statement

In strict adherence to Section 19 of the Phase 1A.7 specification:

> **Canonical Sensor Governance Statement:**  
> *"A five-year Landsat Collection 2 Level-2 temporal baseline using the same WRS-2 Path/Row 147/047 and peak pre-monsoon acquisition window, comprising four Landsat 8 observations and one Landsat 9 observation in 2023. Platform identity is retained explicitly for downstream quality control and temporal normalization."*

Zero unsupported claims of sensor homogeneity or artificial cross-sensor calibration offsets have been introduced.

---

## 11. Freeze Gate Declaration

```text
============================================================
CLIMORA PHASE 1A.7 FREEZE GATE AUDIT CHECKLIST:
============================================================
[PASSED] 1.  5 approved Landsat scenes acquired and validated.
[PASSED] 2.  45/45 required Landsat Level-2 assets present and valid GeoTIFFs.
[PASSED] 3.  All scene identities match the amended contract.
[PASSED] 4.  Platform metadata explicitly records 4x Landsat 8 and 1x Landsat 9.
[PASSED] 5.  All DOYs within preferred window [95, 115] (DOY 101-114).
[PASSED] 6.  All temporal offsets <= 9 days (well within <= 15-day limit).
[PASSED] 7.  Pune AOI cloud contamination validated <= 1.71% across all scenes.
[PASSED] 8.  16 historical MODIS assets (2021-2024, DOY 105) acquired and valid.
[PASSED] 9.  4 historical NASA POWER files (2021-2024, 1,461 daily records) acquired.
[PASSED] 10. All 44 original Phase 0 frozen assets verified unchanged (100% match).
[PASSED] 11. No duplicate downloads or overwrites occurred.
[PASSED] 12. Actual storage measured and recorded (4.835 GiB total raw lake).
[PASSED] 13. Authoritative checksums manifest generated (109 verified assets).
[PASSED] 14. Acquisition manifest and frozen manifest generated.
[PASSED] 15. Full test suite passes: 23 passed in 2.02s.

FINAL VERDICT:
PHASE 1A.7 = PASSED
DATASET STATUS = FROZEN
============================================================
```
