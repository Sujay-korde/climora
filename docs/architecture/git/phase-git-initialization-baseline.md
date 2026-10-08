# CLIMORA — Git Repository Initialization & Baseline Audit Report

**PHASE:** Git Repository Initialization & Pre-Push Audit  
**DATE:** 2026-10-09  
**STATUS:** PASS  
**GOVERNING RATIFICATION:** Phase 2E.1R (Pass with Conditions)  

---

## 1. Executive Summary

The CLIMORA municipal climate decision instrument repository has been successfully initialized as a reproducible, production-grade Git repository on branch `main`.

A comprehensive multi-phase audit was performed prior to establishing the initial commit:
1. **Secrets & Credentials:** Zero secrets, private keys, AWS access tokens, or sensitive API keys are tracked.
2. **Data-Lake Segregation:** Heavy satellite rasters (Landsat, Sentinel-2, MODIS, Copernicus DEM) exceeding 3.5 GB are strictly excluded from version control and preserved in the S3 scientific data lake.
3. **Canonical Parquets Preservation:** All 5 canonical Parquet files remain bit-for-bit unmutated with cryptographic SHA-256 digests matching frozen baselines. They are excluded from Git tracking in accordance with the S3 data lake architecture.
4. **Tracked Working Set:** Exactly 192 clean engineering artifacts (source code, tests, documentation, OpenAPI contracts, and canonical metadata) totaling ~4.8 MB are staged.

---

## 2. Repository Classification Audit

| Category | File Count | Approximate Size | Git Treatment | Rationale |
| :--- | :---: | :---: | :---: | :--- |
| **Backend Source** (`api/`, `processing/`, `services/`, `ingestion/`) | 44 | ~350 KB | **TRACK** | Core application logic, mathematical engines, Cedar governance, and ingestion pipelines. |
| **Frontend Source** (`frontend/src/`, `frontend/package.json`, configs) | 36 | ~280 KB | **TRACK** | React/TypeScript presentation layer, state management, Leaflet map renderer, and tests. |
| **Comprehensive Tests** (`tests/`, `frontend/src/tests/`) | 27 | ~220 KB | **TRACK** | Full automated verification suites across all phases (100% passing). |
| **Architecture & Scientific Docs** (`docs/`) | 49 | ~2.1 MB | **TRACK** | Complete architectural decisions, mathematical formulation registers, and Phase gates. |
| **Canonical Contracts & Manifests** (`data/manifests/`, `data/aoi/`, `data/processed/projects/`, `data/processed/optimization/scenarios/`, `data/processed/temporal/`) | 32 | ~1.9 MB | **TRACK** | Reproducible JSON contracts, AOI GeoJSON, benchmark scenarios, and acquisition manifests. |
| **Configuration Files** (`Dockerfile`, `config.yaml`, `pytest.ini`, `requirements.txt`, `.gitignore`, `.env.example`, `.dockerignore`, `README.md`) | 8 | ~25 KB | **TRACK** | Build recipes, runtime dependencies, and container definitions. |
| **Canonical Parquets** (`data/processed/**/*.parquet`) | 5 | ~1.2 MB | **IGNORE** | Cryptographically ratified; S3 data lake is canonical store. SHA-256 verified in manifests. |
| **Raw & Processed Satellite Rasters** (`data/raw/`, `data/derived/`, `data/processed/**/*.tif`) | 100+ | > 3.5 GB | **IGNORE** | Multi-spectral satellite bands, DEMs, and intermediate rasters stored in S3 data lake. |
| **Dependencies & Build Outputs** (`node_modules/`, `frontend/dist/`, `*.zip`, `.venv/`) | 10,000+ | > 250 MB | **IGNORE** | Ephemeral build artifacts and vendor modules. |
| **Environment Secrets & Local Caches** (`.env.*`, `__pycache__/`, `.pytest_cache/`, `scratch/`) | Many | — | **IGNORE** | Security boundary and temporary development artifacts. |

---

## 3. Cryptographic Canonical Artifact Verification

All 5 canonical analytical datasets were independently verified against ratified reference digests immediately prior to commit:

| Canonical Artifact | Verified SHA-256 Digest | Status | S3 Manifest Match |
| :--- | :--- | :---: | :---: |
| `canonical_feature_matrix.parquet` | `76f344b147b349f3887259f64c97923414c74fd9a97ec679844fb8d9109f7c01` | **MATCH** | YES |
| `canonical_hev_components.parquet` | `1970c2da7863f5771b223c2f265344129ea3f7ed1e5119ece98dc56e37fa2be9` | **MATCH** | YES |
| `canonical_risk_surface.parquet` | `e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677` | **MATCH** | YES |
| `canonical_spatial_autocorrelation.parquet` | `47cc7025ef150aec3980928912e35c96c46da437efbbeccfe1fc142321315bbd` | **MATCH** | YES |
| `canonical_optimization_allocation.parquet` | `2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555` | **MATCH** | YES |

**Cryptographic Integrity Result:** 100% Bit-for-bit preserved. Zero modification to canonical files.

---

## 4. Secrets & Security Pre-Push Audit

- **Automated Regex Scan:** Searched for AWS Access Keys (`AKIA...`), AWS Secret Keys, Session Tokens, private keys, passwords, and hardcoded API tokens. Result: **0 matches**.
- **Environment Files:**
  - Tracked: `.env.example` (Root) and `frontend/.env.example` (Frontend) containing non-sensitive template documentation.
  - Ignored: `.env`, `.env.*` (including `frontend/.env.production`).
- **Basemap Key Discipline:** `VITE_CARTO_BASEMAP_KEY` is not hardcoded. The application defaults cleanly to public OpenStreetMap when no CARTO key is provided.

---

## 5. Large File Audit

- Files exceeding 50 MB: **0**
- Files exceeding 1 MB:
  - `data/manifests/pune_2025_acquisition_plan.json` (1.68 MB) — Complete reproducible provenance catalog of all satellite acquisitions, STAC links, and granule IDs.
- Total tracked repository payload: **~4.8 MB** across 192 files.

---

## 6. Remote Repository Configuration

- **Local Branch:** `main`
- **GitHub Remote Status:** Not yet configured.
- **Next Step for Operator:** Once the remote repository is created on GitHub, configure the origin and push using:
  ```bash
  git remote add origin https://github.com/<ORGANIZATION_OR_USERNAME>/climora.git
  git push -u origin main
  ```
