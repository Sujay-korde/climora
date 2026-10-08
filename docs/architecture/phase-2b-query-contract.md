# CLIMORA — Phase 2B Query Contract Specification

## Machine-Readable & Client Integration Query Contract

### 1. Governing Boundary

This document specifies the authoritative HTTP and data-access contract for the CLIMORA production API following Phase 2B Service Hardening.
- **Scientific Formulations:** FROZEN (Phase 1A through 1H).
- **New Scientific Formulations:** NONE.
- **Analytical Topology:** H3 Resolution 9 hexagons. Administrative wards are decoupled display context only.
- **Canonical Parquet Datasets:** Immutable, byte-for-byte verified by SHA-256 digests.

---

### 2. Endpoints & Query Operations

#### 2.1 GET `/health`
- **Method:** `GET`
- **Purpose:** System operational health, pipeline freeze status, and canonical project identity.
- **Parameters:** None.
- **Response Headers:** `X-Correlation-ID`, `X-Response-Time-Ms`.
- **Response Schema:**
  ```json
  {
    "status": "HEALTHY",
    "service": "CLIMORA Production API & Service Boundary",
    "version": "1.1.0",
    "phase": "Phase 2B (Hardened & Optimized)",
    "scientific_architecture": "FROZEN",
    "canonical_project_id": "PROJ-PUNE-2025-BA225D6A",
    "optimization_run_id": "OPT-PUNE-2025-SCENARIO-BA225D6A",
    "h3_resolution": 9,
    "cache": { "hits": 0, "misses": 0, "hit_ratio": 0.0, "cached_entries_count": 0, "max_entries": 500 },
    "timestamp_utc": "2026-10-03T00:00:00.000000Z"
  }
  ```

#### 2.2 GET `/cache/stats`
- **Method:** `GET`
- **Purpose:** Query cache telemetry, hits, misses, hit ratio, and occupancy.
- **Parameters:** None.
- **Response Schema:**
  ```json
  {
    "status": "SUCCESS",
    "cache": {
      "hits": 100,
      "misses": 2,
      "total_requests": 102,
      "hit_ratio": 0.9804,
      "cached_entries_count": 2,
      "max_entries": 500
    }
  }
  ```

#### 2.3 GET `/projects`
- **Method:** `GET`
- **Purpose:** List high-level project proposal summaries.
- **Parameters:** None.
- **Truth Layers:** Explicit truth layer tags on all exposed financial, demographic, and objective metrics.

#### 2.4 GET `/projects/{project_id}`
- **Method:** `GET`
- **Path Parameters:**
  - `project_id` (string, required): Format `^PROJ-[A-Z0-9_-]+$`.
- **Purpose:** Authoritative 13-section structured project proposal representation.
- **Error Codes:** 400 (`VALIDATION_ERROR`), 404 (`PROJECT_NOT_FOUND`).

#### 2.5 GET `/projects/{project_id}/allocation`
- **Method:** `GET`
- **Path Parameters:**
  - `project_id` (string, required): Format `^PROJ-[A-Z0-9_-]+$`.
- **Query Parameters:**
  - `page` (integer, optional, default: 1, min: 1): 1-indexed page number.
  - `page_size` (integer, optional, default: 28, min: 1, max: 100): Number of allocation items per page.
  - `h3_cell_id` (string, optional): 15-character lowercase hex H3 Resolution 9 index. Filters allocations to a single cell.
- **Pagination Semantics:**
  - Bounded items in `allocations` array.
  - `portfolio_summary` is **never truncated** by pagination. Canonical totals (28 cells, 2,695 trees, ₹9,992,500 cost, ₹7,500 slack, 118,941.21 exact population, 0.106048 objective reduction score) remain invariant.
- **Immutability Contract:**
  - `PUT`, `PATCH`, `DELETE` are rejected with HTTP 405 `METHOD_NOT_ALLOWED` (`ALLOCATION_IMMUTABLE`).

#### 2.6 GET `/projects/{project_id}/baseline`
- **Method:** `GET`
- **Path Parameters:**
  - `project_id` (string, required): Format `^PROJ-[A-Z0-9_-]+$`.
- **Query Parameters:**
  - `page` (integer, optional, default: 1, min: 1).
  - `page_size` (integer, optional, default: 28, min: 1, max: 100).
  - `h3_cell_id` (string, optional): 15-char hex H3 Resolution 9 index.
  - `limit` (integer, optional, min: 1, max: 100): Backward-compatible cell count limit.
- **Truth Layer Classification:**
  - `OBSERVED`: LST 2025, NDVI 2025, NDBI 2025, Population 2020, Road length.
  - `DERIVED`: Baseline mean LST, Anomaly, Persistence, Recurrence $\ge 45^\circ\text{C}$, Population density, LISA Moran's $I$.
  - `MODELED`: Hazard score ($H_i$), Exposure ($E_i$), Vulnerability ($V_i$), Climate Risk ($\text{Risk}_i$).

#### 2.7 GET `/projects/{project_id}/mrv`
- **Method:** `GET`
- **Purpose:** MRV tracking, physical deployment deviations, and DID readiness.
- **Invariant:** `verified_impact` remains `null`. DID operational status is `PLANNED / NOT_YET_EXECUTABLE`.

#### 2.8 POST `/projects/{project_id}/implementation-events`
- **Method:** `POST`
- **Purpose:** Record real-world contractor physical plantings. Computes physical deviations against frozen allocation.

#### 2.9 POST `/projects/{project_id}/verification-events`
- **Method:** `POST`
- **Purpose:** Submit post-intervention verification milestone.
- **Safety Gates:**
  - Rejects synthetic data (`DEMO_ONLY_SYNTHETIC_MRV_DATA` / `is_synthetic_demo == True`) with HTTP 422.
  - Rejects Sentinel-2 MSI for thermal LST observations with HTTP 422.
  - Enforces temporal window: target DOY 105, preferred 95–115, fallback 90–120 ($|\text{DOY} - 105| \le 15$).
  - Enforces AOI cloud cover $\le 5.0\%$ and 100% pixel QA screening.

#### 2.10 POST `/projects/{project_id}/revisions`
- **Method:** `POST`
- **Purpose:** Proposes an auditable allocation revision branch without mutating canonical Parquet files.

---

### 3. Unified Error Contract

All API error responses deterministically adhere to the following schema:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable explanation",
    "details": {}
  }
}
```

Standard error codes:
| HTTP Status | Error Code | Description |
| :--- | :--- | :--- |
| 400 | `BAD_REQUEST` | Malformed HTTP request body or unparseable query |
| 400 | `VALIDATION_ERROR` | Schema validation failure, NaN/Inf rejection, invalid ID format |
| 404 | `PROJECT_NOT_FOUND` | Requested project identifier does not exist |
| 404 | `RESOURCE_NOT_FOUND` | Non-existent route or resource |
| 405 | `ALLOCATION_IMMUTABLE` | Direct PUT/PATCH/DELETE mutation attempt on canonical allocation |
| 405 | `METHOD_NOT_ALLOWED` | Disallowed HTTP verb on route |
| 422 | `ILLEGAL_STATE_TRANSITION` | Disallowed lifecycle transition (e.g. PROPOSED $\to$ VERIFIED jump) |
| 422 | `VERIFICATION_NOT_ELIGIBLE` | Prerequisite missing, synthetic data rejected, sensor incompatible |
| 500 | `INTERNAL_SERVER_ERROR` | Sanitized server error. Details logged securely, no stack trace leak |

---

### 4. Deterministic Caching Rules

1. **Deterministic Cache Key:** Bound to canonical artifact SHA-256 digests, project ID, and query parameters.
2. **Cache Isolation:** Query parameter variations (`page`, `page_size`, `h3_cell_id`) produce distinct isolated cache entries.
3. **Automatic Invalidation:**
   - Any canonical file modification changes the artifact SHA, invalidating all cached entries.
   - Any proposed allocation revision clears the `alloc_query` cache prefix.
4. **Zero Cache Leakage:** The cache stores serialized query projections; it never acts as a second data store or overrides scientific truth.
