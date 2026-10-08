# CLIMORA — Phase AWS-4 Architecture & Verification Report

## AWS Amplify Public Frontend Deployment & Production End-to-End Integration

---

## 1. Executive Summary & Phase Status

| Attribute | Value |
| :--- | :--- |
| **Phase** | **Phase AWS-4 (Amplify Public Frontend Deployment)** |
| **Status** | **PASSED** |
| **Amplify App ID** | `dipd0dx7w10zl` |
| **Amplify App Name** | `climora-frontend` |
| **Amplify App ARN** | `arn:aws:amplify:ap-south-1:434658845459:apps/dipd0dx7w10zl` |
| **Public Production URL** | **`https://main.dipd0dx7w10zl.amplifyapp.com`** |
| **AWS Region** | `ap-south-1` (Asia Pacific - Mumbai) |
| **Connected ECS API Endpoint**| `https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws` |
| **Scientific Data Lake Bucket**| `climora-scientific-lake-434658845459-pune25` |
| **Billing Boundary Verification**| Active ($15 CloudWatch Billing Alarm in `us-east-1`) |

Phase AWS-4 establishes the public presentation layer for the CLIMORA decision-support system by deploying the React/Vite Single Page Application (SPA) onto **AWS Amplify Hosting** in region `ap-south-1` and integrating it end-to-end with the existing **Amazon ECS Express Mode** backend and **Amazon S3 Scientific Data Lake**.

A judge, municipal official, or external user can access CLIMORA directly via HTTPS on any browser across the globe with **zero prerequisite tooling**: no Python, no Node.js, no Docker, no AWS credentials, no local dataset, and no `.env` files.

---

## 2. End-to-End Architectural Blueprint

```text
Judge / Municipal Officer Browser (Global)
       │
       │ HTTPS / TLS 1.3 (Port 443)
       ▼
AWS Amplify Hosting (CloudFront Global CDN)
   URL: https://main.dipd0dx7w10zl.amplifyapp.com
   ├── SPA Rewrite Rule: </^[^.]+$|\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/> -> /index.html
   ├── Static Bundles: POSIX-structured Vite assets (JS 610.4 kB, CSS 2.7 kB)
   └── Canonical Boundary: frontend/src/services/api.ts (VITE_API_BASE_URL)
       │
       │ HTTPS REST Fetch (TLS 1.3 / Port 443)
       │ Strict CORS Allowlist: https://main.dipd0dx7w10zl.amplifyapp.com
       ▼
Amazon ECS Express Mode (Managed Application Load Balancer)
   URL: https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws
       │
       │ HTTP / Port 8000
       ▼
AWS Fargate Task (Container: climora-api:latest / Revision 3)
   ├── Environment: CLIMORA_CORS_ALLOWED_ORIGINS=https://main.dipd0dx7w10zl.amplifyapp.com,...
   ├── Non-root User: climora
   ├── WSGI: Gunicorn 21.2.0 (2 workers, 4 threads)
   └── Dual-Mode Runtime Loader: services/runtime_data.py
       │
       │ IAM Task Role (climora-ecs-task-role)
       │ Least-Privilege Action: s3:GetObject
       ▼
Amazon S3 Scientific Data Lake
   Bucket: climora-scientific-lake-434658845459-pune25
   Working Set: 56 Objects (24.23 MB)
   Integrity: 7/7 Canonical Parquet/JSON/GeoJSON Artifacts SHA-256 Verified
```

---

## 3. Data Lineage: S3 → ECS → API → Amplify Frontend

Scientific data integrity is preserved strictly without client-side calculation or numerical drift:

```text
Amazon S3 Lake (ap-south-1)
  ├── canonical_feature_matrix.parquet (SHA: 76f344b...)
  ├── canonical_hev_components.parquet (SHA: 1970c2d...)
  ├── canonical_risk_surface.parquet (SHA: e2d5df6...)
  ├── canonical_spatial_autocorrelation.parquet (SHA: 47cc702...)
  ├── canonical_optimization_allocation.parquet (SHA: 2519473...)
  └── project_pune_2025_tree_shade_10m.json
       │
       │ IAM Task Role (s3:GetObject)
       ▼
ECS Express Fargate (ZonalQueryEngine Memory Mesh)
  ├── Loads & indexes 5 canonical Parquets at startup
  ├── Indexes 28 priority H3 cells at Resolution 9
  └── Frozen formulations: F-19 through F-26
       │
       │ HTTPS JSON Response
       ▼
React / Vite CLIMORA Frontend (Amplify Hosting)
  ├── Overview Page: Retrieves project proposal & 5-year thermal baseline
  ├── Explore Page: Maps H3 Res 9 cells with live observed/derived/modeled evidence
  ├── Project Page: Displays allocation ledger, CapEx breakdown, and MRV gating
  └── Governance Tab: Dispatches authorized state machine transitions & revisions
```

---

## 4. Frontend Build & Configuration

### 4.1 Build Specification
* **Source Command:** `npm run build`
* **Underlying Toolchain:** `tsc && vite build`
* **Output Directory:** `frontend/dist`
* **Artifact Metrics:**
  * `dist/index.html`: `1.29 kB` (gzip: `0.70 kB`)
  * `dist/assets/index-CUqLmwyN.css`: `2.67 kB` (gzip: `1.13 kB`)
  * `dist/assets/index-Pi41fLnd.js`: `610.43 kB` (gzip: `178.65 kB`)

### 4.2 API Base URL Canonical Boundary
* Configured via Vite environment variable: `VITE_API_BASE_URL`
* Production setting (`frontend/.env.production`):
  ```properties
  VITE_API_BASE_URL=https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws
  ```
* Development boundary preserved: When `VITE_API_BASE_URL` is omitted or empty (as in local `npm run dev`), the frontend continues to default to `''` and relies on Vite's local proxy to `http://127.0.0.1:8000`.
* Zero multiple hardcoded references: All network calls route strictly through `frontend/src/services/api.ts`.

---

## 5. Deployment Engineering: AWS Amplify Hosting

### 5.1 Application Provisioning
* **App Identifier:** `dipd0dx7w10zl`
* **App Name:** `climora-frontend`
* **Platform:** `WEB`
* **Branch:** `main` (Stage: `PRODUCTION`)
* **Default Domain:** `dipd0dx7w10zl.amplifyapp.com`
* **Branch URL:** `https://main.dipd0dx7w10zl.amplifyapp.com`

### 5.2 Archive Packaging & POSIX Separator Discipline
During initial deployment, a critical platform nuance was diagnosed and resolved:
* Standard Windows PowerShell `Compress-Archive` encodes directory paths using Windows backslashes (`assets\index-*.js`). When unpacked by AWS Amplify onto S3, object keys were created with literal backslashes, causing browser requests for `/assets/index-*.js` to return `HTTP 404 Not Found` (resulting in a blank screen).
* A deterministic Python POSIX packaging step was introduced to ensure all ZIP archive entries enforce forward slashes (`/`):
  ```python
  import zipfile, os
  dist_dir = r"frontend/dist"
  with zipfile.ZipFile("scratch/dist_posix.zip", "w", zipfile.ZIP_DEFLATED) as zf:
      for r, d, fs in os.walk(dist_dir):
          for f in fs:
              full = os.path.join(r, f)
              arc = os.path.relpath(full, dist_dir).replace('\\', '/')
              zf.write(full, arcname=arc)
  ```
* Deployed via Amplify manual deployment API (`aws amplify create-deployment` -> S3 Presigned Upload -> `aws amplify start-deployment` -> Job ID 2: `SUCCEED`).
* Assets verified: Both `index-Pi41fLnd.js` and `index-CUqLmwyN.css` load with `HTTP/1.1 200 OK`.

---

## 6. Single Page Application (SPA) Routing & Fallback

Amplify custom rewrite rules were configured on `dipd0dx7w10zl` to ensure nested client-side React Router paths never return `HTTP 404`:

```json
[
  {
    "source": "</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/>",
    "target": "/index.html",
    "status": "200"
  }
]
```

### Verification Matrix for Direct Navigation:
| Route | Direct Browser Curl / Navigation | Result | Status |
| :--- | :--- | :--- | :--- |
| `/` | `curl -i https://main.dipd0dx7w10zl.amplifyapp.com/` | `HTTP/1.1 200 OK` (serves `index.html`) | **PASS** |
| `/explore/pune` | `curl -i https://main.dipd0dx7w10zl.amplifyapp.com/explore/pune` | `HTTP/1.1 200 OK` (serves `index.html`) | **PASS** |
| `/projects/PROJ-PUNE-2025-BA225D6A` | `curl -i https://main.dipd0dx7w10zl.amplifyapp.com/projects/PROJ-PUNE-2025-BA225D6A` | `HTTP/1.1 200 OK` (serves `index.html`) | **PASS** |

Direct browser refresh tests on nested routes load the SPA without 404 errors.

---

## 7. CORS Security Hardening & Explicit Allowlist

Per Phase AWS-4 requirements, wildcard CORS (`Access-Control-Allow-Origin: *`) was strictly prohibited for production.

### 7.1 Backend Configuration
* ECS Task Definition `climora-cluster-climora-api:3` was registered and rolled out to service `climora-api`.
* Environment variable `CLIMORA_CORS_ALLOWED_ORIGINS` was configured with an explicit allowlist:
  ```properties
  CLIMORA_CORS_ALLOWED_ORIGINS=https://main.dipd0dx7w10zl.amplifyapp.com,https://dipd0dx7w10zl.amplifyapp.com,http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
  ```

### 7.2 Preflight & CORS Verification Table
| Scenario | Origin Header | Target Path | Method | Returned `Access-Control-Allow-Origin` | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Amplify GET Preflight** | `https://main.dipd0dx7w10zl.amplifyapp.com` | `/health` | `OPTIONS` | `https://main.dipd0dx7w10zl.amplifyapp.com` | **PASS (204)** |
| **Amplify POST Preflight**| `https://main.dipd0dx7w10zl.amplifyapp.com` | `/projects/{id}/transition` | `OPTIONS` | `https://main.dipd0dx7w10zl.amplifyapp.com` | **PASS (204)** |
| **Amplify Live POST** | `https://main.dipd0dx7w10zl.amplifyapp.com` | `/projects/{id}/transition` | `POST` | `https://main.dipd0dx7w10zl.amplifyapp.com` | **PASS (200)** |
| **Untrusted Origin** | `https://malicious-site.example.com` | `/health` | `OPTIONS` | *None* (Header omitted) | **PASS (Blocked)** |

Allowed Methods: `GET, POST, OPTIONS`  
Allowed Headers: `Content-Type, Authorization, X-Correlation-ID, X-Request-ID`  
Vary Header: `Vary: Origin`

---

## 8. End-to-End Production Browser Verification

Verification was conducted using an autonomous browser agent executing live on `https://main.dipd0dx7w10zl.amplifyapp.com`:

### 8.1 Overview Page (`/`)
* Hero Title: `"Turning planetary observations into fundable urban interventions."` rendered with Newsreader serif typography.
* Navigation: Persistent header rendering `CLIMORA`, `Overview`, `Explore`, `Projects`, and subtitle `Pune · H3 Res-9`.
* Four Key Baseline Metrics:
  * **5-year thermal baseline:** `46.36°C` (`OBSERVED · Landsat 2021-2025`)
  * **Priority footprint:** `28 H3 cells` (`DERIVED · Spatial hotspot cluster`)
  * **Planned intervention:** `2,695 trees` (`MODELED · 15.0m interval`)
  * **Modeled capital:** `₹9.99M` (`MODELED · Under ₹10.0M ceiling`)
* Visual design system: Deep Basalt ground (`#0C0E0D`), Calcified Sandstone ink (`#F2F4EF`), Terracotta/Sage/Derived truth badges.

### 8.2 Explore Page (`/explore/pune`)
* Map Canvas: Renders Leaflet tile canvas centered over Pune.
* H3 Grid: Real-time retrieval of H3 Resolution 9 hexagonal geometry and baseline evidence from `/projects/PROJ-PUNE-2025-BA225D6A/baseline`.
* Accessibility Keyboard Toggle (`Alt+T`): Toggled into view, displaying full semantic table with 28 rows, column headers, H3 cell IDs (`89608850003ffff`... ), LST values, tree counts, and CapEx allocations. Toggled back seamlessly.

### 8.3 Project Page (`/projects/PROJ-PUNE-2025-BA225D6A`)
* Project Title: `"Pune Urban Heat Island Mitigation & Street Canopy Initiative"`
* Identifier: `PROJ-PUNE-2025-BA225D6A`
* Initial Status: `PROPOSED`
* Tab Navigation: All 4 tabs functional (`Baseline Evidence`, `Capital Allocation`, `MRV Readiness`, `Governance & Audit`).
* Mathematical Invariants Verified in Browser:
  * Prioritized Cells: `28`
  * Planned Tree Quantity: `2,695`
  * Modeled CapEx: `₹9,992,500`
  * Scenario Budget Envelope: `₹10,000,000`
  * Unallocated Slack: `₹7,500`
  * Scoped Beneficiary Population: `118,941`
  * Optimization Objective Score: `0.106048`
* MRV Gate: Accurately reflects Difference-in-Differences status `PLANNED / NOT_YET_EXECUTABLE` with null/unobserved empirical cooling.

### 8.4 State POST End-to-End Test (Governance Tab)
* Sanction ID Input: Entered `PMC-SANC-2025-AMPLIFY`.
* Action: Executed `POST /projects/PROJ-PUNE-2025-BA225D6A/transition`.
* Execution Result: Browser preflight `OPTIONS` passed with 204; `POST` request completed with `HTTP 200 OK`.
* State Machine UI: Project status badge immediately transitioned from `PROPOSED` to **`Project Sanctioned (FUNDED)`**.
* Browser Console: Clean, zero errors (`0 errors reported`).
* Visual Artifacts:
  * Verified Screenshot: `project_page_verified_1791219297901.png`
  * WebP Video Recording: `verify_live_amplify_1791219051807.webp`

---

## 9. Architectural Limitation Disclosure

Per Section 13 of the specification:
> **Canonical scientific truth is durable in Amazon S3, while current governance/revision runtime state is process-local and is not yet a durable event store.**

* **Authoritative Truth:** All 7 canonical scientific artifacts (features, HEV components, risk surface, spatial autocorrelation, allocation, project proposal, GeoJSON) are immutable, cryptographically hashed, and stored durably in Amazon S3 (`climora-scientific-lake-434658845459-pune25`).
* **Governance State:** Municipal lifecycle transitions (`PROPOSED` -> `FUNDED`) and proposed allocation revisions execute in ECS task process memory. If the ECS container restarts or scales, state resets to the initial S3 baseline.
* **Resolution Path:** Durable persistence of governance events and audit logs is planned for Phase AWS-5 (e.g. Amazon DynamoDB event sourcing or S3 audit journal). Zero database services were introduced in AWS-4 to strictly respect service boundaries.

---

## 10. Security & Secret Audit

* **Frontend Source & Dist Inspection:**
  * Searched `frontend/src/` and `frontend/dist/` for AWS credentials (`AKIA...`), secret access keys, IAM tokens, private keys, and administrative secrets.
  * Result: **0 credentials found**.
* **Public Environment Variables:**
  * Only `VITE_API_BASE_URL` is exposed in the build.
* **Least Privilege:**
  * Amplify App has zero IAM backend roles attached (pure static hosting).
  * ECS Fargate Task Role possesses strictly scoped `s3:GetObject` on the scientific data lake bucket.
  * Container runs as unprivileged user `climora`.

---

## 11. Cost Safety & Resource Discipline

* **CloudWatch Billing Alarm:** Verified active at `$15.00 USD` threshold in `us-east-1` (`climora-billing-alarm-15usd`).
* **Infrastructure Footprint:**
  * AWS Amplify Hosting: 1 Web App (`dipd0dx7w10zl`), 1 Branch (`main`), ~614 kB storage.
  * Amazon ECS Fargate: 1 running task (`0.25 vCPU`, `512 MiB` RAM).
  * Amazon S3: 56 objects, 24.23 MB.
  * Amazon ECR: 1 image (`climora-api:latest`).
* **AWS Services Intentionally Rejected:**
  * No Amazon RDS / Aurora
  * No Amazon DynamoDB
  * No Amazon OpenSearch
  * No AWS Lambda
  * No Amazon API Gateway
  * No Amazon EKS
  * No NAT Gateway
  * No Amazon Cognito
* **Phase AWS-4 Incurred Cost:** **<$0.15 USD**.

---

## 12. Regression Test Verification Record

| Test Suite | Execution Command | Result | Duration |
| :--- | :--- | :--- | :--- |
| **Backend Test Suite** | `python -m pytest tests/ -q` (Python 3.13) | **160 passed, 1 warning** | 106.42s |
| **Frontend Test Suite** | `npm test -- --run` | **13 passed (100%)** | 1.73s |
| **Frontend Production Build** | `npm run build` (`tsc && vite build`) | **PASS (clean)** | 9.04s |
| **Live Browser E2E Suite** | Autonomous Browser Subagent | **PASS (0 console errors)** | ~90s |

---

## 13. Phase AWS-4 Acceptance Checklist

- [x] Pre-implementation audit completed across 10 boundary criteria.
- [x] Vite frontend configured to point `VITE_API_BASE_URL` to the public ECS endpoint.
- [x] Local development fallback (`http://127.0.0.1:8000`) preserved intact.
- [x] Production build clean (`dist/` generated with zero secrets).
- [x] AWS Amplify Hosting App provisioned in `ap-south-1` (`dipd0dx7w10zl`).
- [x] Branch `main` created and deployed.
- [x] POSIX separator packaging applied to eliminate Windows backslash 404 asset bug.
- [x] SPA rewrite rules active (`/index.html` fallback for direct navigation).
- [x] Direct navigation to `/`, `/explore/pune`, and `/projects/PROJ-PUNE-2025-BA225D6A` verified (no 404s).
- [x] Backend CORS updated from wildcard `*` to explicit Amplify domain allowlist.
- [x] Preflight `OPTIONS` requests verified for both GET and POST endpoints.
- [x] Live browser test confirms Overview, Explore, and Project pages render cleanly with zero white screens.
- [x] Alt+T accessibility table toggle verified in browser.
- [x] All 7 canonical scientific invariants verified in the public frontend.
- [x] POST `/projects/{id}/transition` executed from browser; state transition to `FUNDED` verified.
- [x] 160 backend tests pass (100%).
- [x] 13 frontend tests pass (100%).
- [x] Cost safety preserved under $15 CloudWatch billing alarm.
- [x] Architectural limitation regarding process-local governance state explicitly documented.

---

## 14. Conclusion & Readiness Assessment for AWS-5

**AWS-4 STATUS: PASSED**

The CLIMORA public application is now live and accessible at:
👉 **`https://main.dipd0dx7w10zl.amplifyapp.com`**

The system fulfills all end-to-end integration criteria: Judge Browser → AWS Amplify Hosting → React/Vite SPA → HTTPS → ECS Express Mode API → IAM Task Role → Amazon S3 Scientific Data Lake.

The system is ready for Phase AWS-5 (Durable Governance Persistence & Production Readiness Review).
