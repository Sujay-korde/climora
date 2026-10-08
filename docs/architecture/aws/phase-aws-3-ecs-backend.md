# CLIMORA — Phase AWS-3 Architecture & Verification Report

## Containerized Backend, S3 Runtime Integration & ECS Express Mode

---

## 1. Executive Summary

Phase AWS-3 successfully transitions the CLIMORA Flask scientific API from developer workstation reliance to a containerized, cloud-native service deployed via **Amazon ECS Express Mode** on **AWS Fargate** in AWS region `ap-south-1`.

The deployed service retrieves its authoritative scientific baseline and optimization artifacts directly from the 56-object S3 scientific data lake (`climora-scientific-lake-434658845459-pune25`) provisioned and cryptographically verified in Phase AWS-2. All data retrieval utilizes an IAM Task Role with strictly scoped, least-privilege `s3:GetObject` permissions. Zero static AWS credentials or workstation-specific paths exist within the container or runtime configuration.

All scientific formulations (HEV, Moran's I, MILP optimization, H3 resolution 9 indexing, difference-in-differences MRV gating) remain 100% unmodified and frozen. Canonical numerical invariants are preserved identically across all live public API responses.

---

## 2. Architectural Blueprint

```text
React / Vite Frontend (Local / Amplify AWS-4)
       │
       │ HTTPS REST (TLS 1.3 / Port 443)
       ▼
AWS ECS Express Mode (Managed Application Load Balancer)
  URL: https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws
       │
       │ HTTP / Port 8000
       ▼
AWS Fargate Task (Container: climora-api:latest)
  ├── Non-root User: climora (UID/GID)
  ├── WSGI Server: Gunicorn 21.2.0 (2 workers, 4 threads)
  ├── Dual-Mode Runtime Loader: services/runtime_data.py
  └── Memory Cache: /tmp/climora_data_cache
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

## 3. Container Engineering & Size Discipline

### 3.1 Dockerfile Specification

The container image is built from `python:3.11-slim`:
- **Security:** Runs as unprivileged system user `climora` (`groupadd -r climora && useradd -r -g climora -d /app climora`).
- **WSGI Engine:** Gunicorn 21.2.0 binding to `0.0.0.0:8000` with 2 workers, 4 threads, and structured stdout/stderr access logging.
- **Port Exposure:** Exposes TCP port 8000.
- **Healthcheck:** Native Docker health check executing `curl -f http://localhost:8000/health || exit 1` every 30 seconds.
- **Size Discipline:** `.dockerignore` strictly excludes `data/raw/` (~4.97 GB raw satellite archive), `frontend/`, `tests/`, `scratch/`, `.git/`, and `node_modules/`.
- **Data Lake Separation:** S3 canonical parquet files are NOT baked into the image. They are retrieved at runtime via IAM Task Role into `/tmp/climora_data_cache` and verified via SHA-256 checksums.

### 3.2 Image Metrics
- **Local Tag:** `climora-api:latest`
- **Compressed Content Size:** 182 MB
- **Disk Usage:** 759 MB
- **Raw Satellite Archive Inclusion:** 0 bytes (100% excluded)

---

## 4. Amazon ECR Registry Configuration

The production container was pushed to a dedicated Amazon ECR repository in `ap-south-1`:

| Attribute | Value |
| :--- | :--- |
| **AWS Account ID** | `434658845459` |
| **AWS Region** | `ap-south-1` |
| **Repository Name** | `climora-api` |
| **Repository ARN** | `arn:aws:ecr:ap-south-1:434658845459:repository/climora-api` |
| **Repository URI** | `434658845459.dkr.ecr.ap-south-1.amazonaws.com/climora-api` |
| **Image Tags** | `latest`, `v1.1.0` |
| **Immutable Image Digest** | `sha256:813faca97b33c4e6d2b91c4eeb2b85c6b6e0aab1b56e9c66f5a0755fba35f1e3` |
| **Encryption** | AES256 (Server-Side) |
| **Image Scanning** | Scan on push enabled |

---

## 5. IAM Roles & Least-Privilege Access

Three dedicated IAM roles govern the execution boundary:

### 5.1 ECS Express Infrastructure Role
- **Role Name:** `climora-ecs-express-infra-role`
- **Role ARN:** `arn:aws:iam::434658845459:role/climora-ecs-express-infra-role`
- **Trust Principal:** `ecs.amazonaws.com`
- **Managed Policy:** `arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices`
- **Inline Policy (`ECSExpressManagedALBPolicy`):** Grants managed ALB provisioning (`elasticloadbalancing:*`), network discovery (`ec2:Describe*`), and auto-scaling pass-role (`iam:PassRole` on `AWSServiceRoleForApplicationAutoScaling_ECSService`).

### 5.2 ECS Task Execution Role
- **Role Name:** `climora-ecs-execution-role`
- **Role ARN:** `arn:aws:iam::434658845459:role/climora-ecs-execution-role`
- **Trust Principal:** `ecs-tasks.amazonaws.com`
- **Managed Policy:** `arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy`
- **Function:** Authorizes AWS Fargate agent to pull images from ECR and stream logs to CloudWatch.

### 5.3 ECS Task Role (S3 Runtime Access)
- **Role Name:** `climora-ecs-task-role`
- **Role ARN:** `arn:aws:iam::434658845459:role/climora-ecs-task-role`
- **Trust Principal:** `ecs-tasks.amazonaws.com`
- **Inline Policy (`ClimoraS3ScientificLakeReadPolicy`):**
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowS3ScientificLakeRead",
        "Effect": "Allow",
        "Action": [
          "s3:GetObject"
        ],
        "Resource": "arn:aws:s3:::climora-scientific-lake-434658845459-pune25/*"
      }
    ]
  }
  ```
- **Security Boundary:** No `s3:*`, no bucket admin permissions, no write permissions on the scientific lake. Zero embedded credentials.

---

## 6. ECS Express Gateway Service Specification

| Specification Parameter | Configured Value |
| :--- | :--- |
| **Deployment Mode** | Amazon ECS Express Mode |
| **ECS Cluster** | `climora-cluster` (`arn:aws:ecs:ap-south-1:434658845459:cluster/climora-cluster`) |
| **Service Name** | `climora-api` |
| **Service ARN** | `arn:aws:ecs:ap-south-1:434658845459:service/climora-cluster/climora-api` |
| **Compute Profile** | AWS Fargate (`0.25 vCPU` / 256 CPU units, `512 MiB` RAM) |
| **CPU Architecture** | `X86_64` |
| **Scaling Target** | Min: 1 task, Max: 2 tasks (70% Average CPU threshold) |
| **Container Port** | 8000 (TCP) |
| **Health Check Path** | `/health` (HTTP 200 required, 30s interval, 5s timeout) |
| **Managed Load Balancer** | `arn:aws:elasticloadbalancing:ap-south-1:434658845459:loadbalancer/app/ecs-express-gateway-alb-b1a1b518/d1b6aa98e4ae623d` |
| **SSL / TLS Certificate** | AWS Certificate Manager managed TLS 1.3 Post-Quantum policy (`ELBSecurityPolicy-TLS13-1-2-Ext1-PQ-2025-09`) |
| **Public HTTPS Endpoint** | `https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws` |
| **CloudWatch Log Group** | `/ecs/climora-api` |

---

## 7. Critical Runtime Data & Dependency Audit

| API Endpoint | Runtime Data Dependency | Local Source (Dev) | Cloud Runtime Source (ECS) | S3 Object Key | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /health` | Engine cache stats & service meta | Memory | Memory | N/A (Zero S3 reads on health) | VERIFIED |
| `GET /projects` | Canonical project document | `data/processed/projects/*.json` | S3 Cached Parquet/JSON | `projects/project_pune_2025_tree_shade_10m.json` | VERIFIED |
| `GET /projects/{id}` | Canonical project document | `data/processed/projects/*.json` | S3 Cached Parquet/JSON | `projects/project_pune_2025_tree_shade_10m.json` | VERIFIED |
| `GET /projects/{id}/baseline` | 5 Canonical Parquets | `data/processed/` Parquets | S3 Cached Parquets | `processed/feature-matrix/canonical_feature_matrix.parquet`<br>`processed/hev/canonical_hev_components.parquet`<br>`processed/risk/canonical_risk_surface.parquet`<br>`processed/spatial-autocorrelation/canonical_spatial_autocorrelation.parquet`<br>`processed/optimization/canonical_optimization_allocation.parquet` | VERIFIED |
| `GET /projects/{id}/allocation` | Canonical allocation Parquet | `data/processed/optimization/*.parquet` | S3 Cached Parquet | `processed/optimization/canonical_optimization_allocation.parquet` | VERIFIED |
| `GET /projects/{id}/mrv` | Canonical allocation + domain events | In-memory + Parquet | In-memory + S3 Parquet | `processed/optimization/canonical_optimization_allocation.parquet` | VERIFIED |
| `POST /projects/{id}/transition` | Project state machine | In-memory domain service | In-memory domain service | Seeded from `projects/project_pune_2025_tree_shade_10m.json` | VERIFIED |
| `POST /projects/{id}/revisions` | Revision tracker & immutable base | In-memory tracker + Parquet | In-memory tracker + S3 Parquet | Seeded from `canonical_optimization_allocation.parquet` | VERIFIED |

**Data Dependency Gap Analysis:** Zero missing artifacts. All 7 required runtime artifacts exist within the 56-object S3 lake and match expected SHA-256 hashes. **NO AWS-3 DATA DEPENDENCY GAP**.

---

## 8. S3 Cloud-Runtime Proof

The deployed container was validated against live HTTPS requests to confirm complete elimination of workstation paths (`C:\Users\...`):

```text
Public Internet (curl.exe)
       │
       │ HTTPS GET /projects/PROJ-PUNE-2025-BA225D6A/allocation
       ▼
ECS Express ALB (Port 443)
       │
       │ HTTP Port 8000
       ▼
Fargate Container (172.31.2.210)
       │
       │ Assumes climora-ecs-task-role via AWS metadata service
       ▼
Amazon S3 API (s3.ap-south-1.amazonaws.com)
       │
       │ GetObject s3://climora-scientific-lake-434658845459-pune25/processed/optimization/canonical_optimization_allocation.parquet
       ▼
Cryptographic Verification (/app/services/runtime_data.py)
  Computed SHA-256: 2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555
  Expected SHA-256: 2519473a32a2b4a3a22bc8beb43525c3f21dc404783168f1edd6de7bc4bb5555
  Integrity Match: 100% IDENTICAL
       │
       ▼
ZonalQueryEngine (Memory Resolution 9 Mesh)
       │
       ▼
JSON API Response (28 Cells, 2695 Trees, ₹9,992,500 Cost)
```

CloudWatch log excerpt from stream `ecs/Main/d71bc8984a9741d4a96a12c20f11879f`:
```text
[INFO] ZonalQueryEngine successfully indexed all 5 canonical Parquet datasets.
[INFO] correlation_id=corr-d3100bd0d728 method=GET path=/health status=200 elapsed_ms=0.337
172.31.32.74 - - [05/Oct/2026:15:18:56 +0000] "GET /health HTTP/1.1" 200 539 "-" "ELB-HealthChecker/2.0"
```

---

## 9. API Functional Verification (Public HTTPS)

All public endpoints were tested over HTTPS against `https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws`:

### 9.1 `GET /health`
```json
{
  "cache": {
    "cached_entries_count": 0,
    "hit_ratio": 0.0,
    "hits": 0,
    "max_entries": 500,
    "misses": 0,
    "total_requests": 0
  },
  "canonical_project_id": "PROJ-PUNE-2025-BA225D6A",
  "data_mode": "S3",
  "h3_resolution": 9,
  "optimization_run_id": "OPT-PUNE-2025-SCENARIO-BA225D6A",
  "phase": "Phase AWS-3 (Containerized & S3-Integrated)",
  "s3_bucket": "climora-scientific-lake-434658845459-pune25",
  "scientific_architecture": "FROZEN",
  "service": "CLIMORA Production API & Service Boundary",
  "status": "HEALTHY",
  "version": "1.1.0"
}
```

### 9.2 Invariant Verification Table

| Metric / Contract Parameter | Canonical Expected Value | Live Public HTTPS Response | Result |
| :--- | :--- | :--- | :--- |
| **Selected Treated Cells** | `28` | `28` | **MATCH** |
| **Planned Tree Quantity** | `2,695.0` | `2,695.0` | **MATCH** |
| **Modeled Optimized CapEx** | `₹9,992,500.0` | `₹9,992,500.0` | **MATCH** |
| **Scenario Budget Envelope**| `₹10,000,000.0` | `₹10,000,000.0` | **MATCH** |
| **Unallocated Budget Slack** | `₹7,500.0` | `₹7,500.0` | **MATCH** |
| **Exact Scoped Population** | `118,941.21` | `118,941.21` | **MATCH** |
| **Optimization Objective** | `0.10604830270054796` | `0.10604830270054796` | **MATCH** |
| **Lifecycle Initial State** | `PROPOSED` | `PROPOSED` | **MATCH** |
| **MRV Verification Gate** | `NOT_STARTED` / `null` cooling | `NOT_STARTED` / `null` cooling | **MATCH** |

### 9.3 State POST Endpoints
- `POST /projects/PROJ-PUNE-2025-BA225D6A/transition`: Transitioned project from `PROPOSED` to `FUNDED` (`sanction_id: PMC-SANC-2025-01`). Returned HTTP 200 with authorized state machine result.
- `POST /projects/PROJ-PUNE-2025-BA225D6A/revisions`: Proposed delta of +24 trees on cell `89608850003ffff`. Returned HTTP 200 with `canonical_file_preserved: true`.

---

## 10. Cost & Billing Safety Controls

- **CloudWatch Billing Alarm:** `climora-billing-alarm-15usd` active at `$15.00 USD` threshold in `us-east-1`.
- **Fargate Compute Footprint:** 1 active task running `0.25 vCPU` and `0.5 GB RAM`. At standard ap-south-1 Fargate rates ($0.04048/vCPU-hr + $0.004445/GB-hr), compute cost is **~$0.0123 / hour** (~$0.30 / day).
- **ALB Ingress:** Managed ALB shared gateway managed by Express Mode.
- **Excluded AWS Services:** Zero RDS, DynamoDB, OpenSearch, NAT Gateways, EKS, Lambda, or API Gateways provisioned.
- **Total Expected AWS-3 Verification Cost:** **<$0.40 USD**.

---

## 11. Regression Test Verification Record

| Test Suite | Execution Command | Result | Duration |
| :--- | :--- | :--- | :--- |
| **Backend Test Suite** | `pytest tests/ -q` | **160 passed**, 1 warning | 71.97s |
| **Frontend Test Suite** | `npm test -- --run` | **13 passed** (100%) | 1.75s |
| **Frontend Production Build** | `npm run build` (`tsc && vite build`) | **PASS** (610 kB JS / 178 kB gzip) | 8.47s |

---

## 12. AWS-3 Acceptance Checklist

- [x] Production container builds cleanly (`climora-api:latest`, 182 MB content size).
- [x] Container executes locally with zero developer path dependencies.
- [x] Container pushed to ECR (`434658845459.dkr.ecr.ap-south-1.amazonaws.com/climora-api:latest`).
- [x] Immutable image digest recorded (`sha256:813faca97b33c4e6d2b91c4eeb2b85c6b6e0aab1b56e9c66f5a0755fba35f1e3`).
- [x] ECS Express Mode service provisioned on AWS Fargate (`climora-api` in `climora-cluster`).
- [x] Public HTTPS endpoint active (`https://cl-c5ee1706dbd84bc3b8a4bb176ff0afba.ecs.ap-south-1.on.aws`).
- [x] ECS task assumes IAM Task Role (`climora-ecs-task-role`) with least-privilege `s3:GetObject`.
- [x] Zero static AWS credentials or secrets embedded in the container.
- [x] S3 canonical artifacts dynamically loaded and cryptographically verified on startup.
- [x] Local developer paths (`C:\Users\...`) completely eliminated from runtime.
- [x] `/health` returns HTTP 200 with service metadata and cache status.
- [x] `/projects/{id}` returns verified project proposal and canonical metrics.
- [x] `/baseline` returns multi-tier analytical indicators across all 28 cells.
- [x] `/allocation` returns read-only optimization allocations.
- [x] All 7 canonical invariants preserved identically without float drift.
- [x] Backend tests: 160 passed.
- [x] Frontend tests: 13 passed.
- [x] Frontend build: PASS.
- [x] Zero scientific files modified; zero equations or weights altered.
- [x] Cost safety preserved within $15 billing boundary.
