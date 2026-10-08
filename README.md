# CLIMORA — Climate-Risk Assessment & Intervention-Planning Platform

**Prototype Geography:** Pune, Maharashtra, India  
**Core Problem:** Urban heat and climate-risk assessment  
**Current Phase:** Phase 0 — Pune Data Acquisition & Local Data Lake Foundation  

---

## 1. Architecture & Raw Data Immutability

CLIMORA follows a strict pipeline:
```
RAW DATA → STANDARDIZED DATA → DERIVED FEATURES → RISK MODEL → INTERVENTIONS → SCENARIOS → OPTIMIZATION → IMPACT → VALIDATION → FUNDABLE PROJECT
```

- **Local Data Lake First**: Ingested raw datasets reside locally in `data/raw/` and can be mirrored directly to `s3://climora-data/raw/...` without changing the logical schema.
- **Raw Data Immutability**: Files in `data/raw/` are strictly read-only and never overwritten.
- **Full Provenance**: Every dataset item tracks source provider, acquisition timestamp, observation date, AOI bounding box, requested assets, SHA-256 checksum, and file size.
- **Strict Idempotency**: Repeated acquisition runs check existence, size, and checksums to skip already-valid local assets without redundant re-downloads.

---

## 2. Directory Structure

```
CLIMORA/
├── .gitignore
├── .env.example
├── README.md
├── config.yaml
├── data/
│   ├── aoi/
│   │   └── pune.geojson
│   ├── manifests/
│   │   └── pune_2025_acquisition_plan.json
│   └── raw/
│       ├── landsat/2025/<scene_id>/
│       ├── sentinel2/2025/<product_id>/
│       ├── modis/2025/<period_id>/
│       ├── nasa_power/pune/2025/
│       ├── osm/pune/
│       └── dem/pune/
├── ingestion/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── common.py
│   ├── landsat.py
│   ├── sentinel2.py
│   ├── modis.py
│   ├── nasa_power.py
│   ├── osm.py
│   └── dem.py
└── tests/
    └── test_ingestion.py
```

---

## 3. Data Stack (Phase 0)

1. **Pune AOI (`data/aoi/pune.geojson`)**: Statutory Pune City administrative boundary (LGD Sub-District Code: `4194`, Wikidata: `Q7260101`, OSM Relation: `10351626`).
2. **Landsat Collection 2 Level-2**: Landsat 8/9, 2025 period, cloud cover <= 20%. Assets: `SR_B2`, `SR_B3`, `SR_B4`, `SR_B5`, `SR_B6`, `SR_B7`, `ST_B10` (thermal LST), `QA_PIXEL`, `QA_RADSAT`.
3. **Sentinel-2 MSI Level-2A**: 2025 period, cloud cover <= 20%. Bands: `B02`, `B03`, `B04`, `B05`, `B06`, `B07`, `B08`, `B8A`, `B11`, `B12`, `SCL`.
4. **MODIS MOD11A2 Version 6.1**: Tile `h25v07` (~1 km native resolution, 8-day composite). Assets: `LST_Day_1km`, `LST_Night_1km`, `QC_Day`, `QC_Night`.
5. **NASA POWER**: Daily meteorology for 2025 (`T2M`, `T2M_MAX`, `T2M_MIN`, `RH2M`, `WS10M`, `PRECTOTCORR`, `ALLSKY_SFC_SW_DWN`).
6. **OpenStreetMap**: Pune-only vector extractions (green spaces, water bodies, public infrastructure, arterial road network).
7. **Copernicus DEM GLO-30**: 30m Cloud-Optimized GeoTIFF (`Copernicus_DSM_COG_10_N18_00_E073_00_DEM`) with documented GLO-90 fallback.

---

## 4. Usage & CLI Commands

### Search Before Download (Milestone 1)
Discovers candidate scenes and assets across STAC / REST endpoints, applies cloud and geographic filters, reports summary, and writes `data/manifests/pune_2025_acquisition_plan.json` without downloading any imagery:
```bash
# Search across all sources for 2025
python -m ingestion search --year 2025

# Search specific source
python -m ingestion search --source landsat --year 2025
```

### Download Approved Candidates (Idempotent)
Downloads only approved candidates and required assets to `data/raw/` with atomic `.part` renames and SHA-256 verification:
```bash
# Download all sources (or specific source)
python -m ingestion download --source landsat --limit 1
python -m ingestion download --source sentinel2 --limit 1 --bands SCL,B05
python -m ingestion download --source modis --limit 1
python -m ingestion download --source nasa_power
python -m ingestion download --source osm
python -m ingestion download --source dem
```

### Validate Ingested Lake
Validates raster dimensions, CRS, vector topology, file sizes, and SHA-256 checksums:
```bash
python -m ingestion validate
```

### Check Acquisition Status
Displays high-level status of AOI, candidates, selected products, valid files, and storage footprint:
```bash
python -m ingestion status
```

---

## 5. Running Tests

```bash
pytest tests/ -v
```
