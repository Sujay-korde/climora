import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/lenovo/climora")
ASSETS_DIR = (PROJECT_ROOT / "docs" / "assets").as_posix()
FORMULAS_DIR = (PROJECT_ROOT / "docs" / "assets" / "formulas").as_posix()
HTML_OUTPUT = PROJECT_ROOT / "CLIMORA_PROJECT_REPORT.html"
PDF_OUTPUT = PROJECT_ROOT / "CLIMORA_PROJECT_REPORT.pdf"

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CLIMORA — Project Report & Technical Whitepaper</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  @page {
    size: A4;
    margin: 14mm 14mm 14mm 14mm;
  }

  * {
    box-sizing: border-box;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #0F172A;
    background: #FFFFFF;
    line-height: 1.5;
    font-size: 9.2pt;
    margin: 0;
    padding: 0;
  }

  /* Typography */
  h1, h2, h3, h4 {
    color: #0B192C;
    font-weight: 700;
    letter-spacing: -0.025em;
    margin-top: 1.1em;
    margin-bottom: 0.35em;
    break-after: avoid;
  }

  h1 { font-size: 22pt; line-height: 1.15; }
  h2 { 
    font-size: 13pt; 
    border-bottom: 2px solid #0EA5E9; 
    padding-bottom: 3px; 
    margin-top: 1.4em;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  h3 { font-size: 10.5pt; color: #1E3A8A; margin-top: 0.9em; }
  h4 { font-size: 9.5pt; color: #334155; }

  p {
    margin: 0.45em 0;
    text-align: justify;
    text-justify: inter-word;
  }

  a {
    color: #0284C7;
    text-decoration: none;
    font-weight: 500;
  }

  code {
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 8pt;
    background: #F1F5F9;
    color: #0F172A;
    padding: 1.5px 4px;
    border-radius: 4px;
    border: 1px solid #E2E8F0;
  }

  /* Badges & Pills */
  .badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 6.8pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 2px 6px;
    border-radius: 4px;
    margin-right: 4px;
  }
  .badge-observed { background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }
  .badge-derived { background: #E0F2FE; color: #0369A1; border: 1px solid #7DD3FC; }
  .badge-modeled { background: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; }
  .badge-built { background: #EDE9FE; color: #6D28D9; border: 1px solid #C4B5FD; }
  .badge-planned { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }
  .badge-danger { background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }

  /* Cover & Headers */
  .cover-header {
    border-bottom: 3px solid #0B192C;
    padding-bottom: 12px;
    margin-bottom: 16px;
  }

  .doc-tagline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 7.8pt;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #0284C7;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .authors-block {
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    color: #475569;
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px solid #E2E8F0;
  }

  /* Metric KPI Grid */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 14px 0;
  }
  .kpi-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #0EA5E9;
    padding: 8px 10px;
    border-radius: 6px;
  }
  .kpi-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 6.8pt;
    text-transform: uppercase;
    color: #64748B;
    font-weight: 600;
  }
  .kpi-value {
    font-size: 13pt;
    font-weight: 800;
    color: #0B192C;
    margin: 2px 0;
    letter-spacing: -0.02em;
  }
  .kpi-sub {
    font-size: 7.2pt;
    color: #475569;
  }

  /* Callout Boxes */
  .callout {
    margin: 10px 0;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 8.5pt;
    break-inside: avoid;
  }
  .callout-blue {
    background: #F0F9FF;
    border: 1px solid #BAE6FD;
    border-left: 4px solid #0284C7;
  }
  .callout-red {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-left: 4px solid #DC2626;
  }
  .callout-green {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-left: 4px solid #16A34A;
  }

  /* Equations */
  .equation-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 8px 14px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    break-inside: avoid;
  }
  .equation-box img {
    max-height: 36px;
    width: auto;
  }
  .equation-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    color: #64748B;
    font-weight: 600;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 7.8pt;
    break-inside: avoid;
  }
  th, td {
    padding: 5px 7px;
    text-align: left;
    border-bottom: 1px solid #E2E8F0;
  }
  th {
    background: #0F172A;
    color: #FFFFFF;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 6.8pt;
    letter-spacing: 0.05em;
  }
  tr:nth-child(even) td {
    background: #F8FAFC;
  }

  /* Visual Figures */
  .figure-container {
    margin: 12px 0;
    break-inside: avoid;
    text-align: center;
  }
  .figure-img {
    width: 100%;
    max-height: 270px;
    object-fit: contain;
    border-radius: 6px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  .figure-caption {
    font-size: 7.8pt;
    color: #475569;
    margin-top: 5px;
    font-weight: 500;
  }

  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
  }

  .slide-thumbnail {
    width: 100%;
    border-radius: 4px;
    border: 1px solid #CBD5E1;
  }

  .page-break {
    page-break-before: always;
  }

  /* Diagram Box */
  .architecture-diagram {
    background: #0A192F;
    color: #E2E8F0;
    border-radius: 6px;
    padding: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 7pt;
    line-height: 1.35;
    white-space: pre;
    overflow-x: auto;
    margin: 8px 0;
    border: 1px solid #1E293B;
  }
</style>
</head>
<body>

  <!-- COVER / HEADER -->
  <div class="cover-header">
    <div class="doc-tagline">NOVEX 2026 OFFICIAL SUBMISSION &bull; ROUND 2 WHITE PAPER &bull; CLIMATE TECH & URBAN AI</div>
    <h1 style="margin: 4px 0 6px 0;">CLIMORA: A Decision Layer for Urban Heat Risk</h1>
    <div style="font-size: 10.5pt; color: #334155; font-weight: 500; margin-bottom: 10px;">
      Spatial Optimization, Cryptographic Governance & Empirical MRV for Municipal Climate Adaptation
    </div>
    
    <div class="authors-block">
      <div><strong>Authors:</strong> Sujay Korde &amp; Kimaya Kolhe &bull; <em>Department of CSE (AIML), Vishwakarma Institute of Technology (VIT Pune)</em></div>
      <div><strong>Target Area:</strong> Pune Municipal Corporation (PMC), India &bull; <strong>Status:</strong> Validated Prototype</div>
    </div>
  </div>

  <!-- KPI SUMMARY STRIP -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Spatial Analysis Mesh</div>
      <div class="kpi-value">3,181 Hex</div>
      <div class="kpi-sub">Uber H3 Res-9 (~0.0986 km²/cell)</div>
    </div>
    <div class="kpi-card" style="border-left-color: #10B981;">
      <div class="kpi-label">Statutory Domain</div>
      <div class="kpi-value">312.11 km²</div>
      <div class="kpi-sub">Pune Municipal Corporation</div>
    </div>
    <div class="kpi-card" style="border-left-color: #8B5CF6;">
      <div class="kpi-label">Human Population Baseline</div>
      <div class="kpi-value">5,011,229</div>
      <div class="kpi-sub">WorldPop Dasymetric Grid</div>
    </div>
    <div class="kpi-card" style="border-left-color: #F59E0B;">
      <div class="kpi-label">Priority Capital Project</div>
      <div class="kpi-value">₹1.00 Crore</div>
      <div class="kpi-sub">28 Cells &bull; 118,941 Residents Protected</div>
    </div>
  </div>

  <!-- 1. ABSTRACT -->
  <h2>1. Abstract</h2>
  <p>
    Urban Heat Islands (UHIs) represent one of the deadliest and most accelerating consequences of global climate change, disproportionately threatening densifying global South metropolises. While modern satellite Earth Observation (EO) produces petabytes of thermal surface data, municipal authorities encounter an insurmountable operational chasm between <strong>detection</strong> and <strong>capital allocation</strong>. Urban planners lack mathematically grounded spatial optimization models, municipal finance officers face unquantified capital risk without auditable cost-benefit trade-offs, and civic interventions suffer from zero empirical post-deployment verification.
  </p>
  <p>
    <strong>CLIMORA</strong> is an open, deterministic, enterprise-grade Decision Layer and Climate Action Operating System designed to convert satellite microclimate analytics into fundable, mathematically optimized, and cryptographically governed urban intervention projects. Validated across the statutory boundary of <strong>Pune Municipal Corporation (PMC)</strong>—spanning <strong>312.11 km²</strong> and <strong>5,011,229 residents</strong>—CLIMORA discretizes the urban surface into <strong>3,181 Uber H3 Resolution-9 hexagons</strong> (~0.0986 km² each). Integrating a 5-year pre-monsoon peak-summer thermal composite (Landsat 8/9 Collection 2 Level-2, 2021–2025), high-resolution Sentinel-2 multispectral vegetation/built-up indices, and WorldPop dasymetric population counts, CLIMORA operationalizes the <strong>IPCC AR6 Hazard–Exposure–Vulnerability (HEV)</strong> risk framework under an unyielding <strong>Zero-Exposure Axiom</strong>.
  </p>
  <p>
    To resolve capital scarcity, CLIMORA couples spatial econometrics (Local Moran's I) with a <strong>HiGHS Mixed-Integer Linear Programming (MILP)</strong> optimization engine. Under a canonical <strong>₹1 Crore (₹10,000,000)</strong> municipal budget preset, CLIMORA isolates the top <strong>28 priority hex cells</strong> (just <strong>0.88%</strong> of the city's landmass), allocating <strong>2,695 shade trees</strong> to shelter <strong>118,941 vulnerable citizens</strong> (mean 4,248 residents/cell vs. citywide mean 1,575) at an average modeled cooling reduction of <strong>~0.07 °C</strong> to <strong>0.17 °C</strong>. CLIMORA completes the project lifecycle by implementing <strong>Amazon Cedar</strong> attribute-based access control (ABAC) with seven ratified governance policies, guaranteeing complete immutability of scientific truth layers while enforcing strict statutory separation between planners, municipal treasurers, field contractors, and ISO 14064-2 accredited MRV auditors.
  </p>

  <div class="callout callout-blue">
    <strong>Governing Principle &mdash; Evidence Truth Badges:</strong> Every numerical metric within CLIMORA adheres strictly to a classified truth tier: 
    <span class="badge badge-observed">OBSERVED</span> Satellite sensors &bull; 
    <span class="badge badge-derived">DERIVED</span> Deterministic math &bull; 
    <span class="badge badge-modeled">MODELED</span> HiGHS MILP simulation &bull; 
    <span class="badge badge-built">BUILT</span> Production codebase &bull; 
    <span class="badge badge-planned">PLANNED</span> Future post-deployment protocol.
  </div>

  <!-- 2. PROBLEM STATEMENT -->
  <h2>2. Problem Statement</h2>
  <p>
    Rapid urbanization in Pune has substituted vegetative cover with dense asphalt and concrete. In peak summer months (April–May), radiant surface temperatures regularly exceed <strong>45.0 °C</strong>. However, public response remains paralyzed by three fundamental institutional failures:
  </p>
  <div class="grid-3" style="margin: 8px 0;">
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px;">
      <h4 style="margin-top:0; color:#B91C1C;">1. Spatial Disconnect</h4>
      <p style="font-size: 7.8pt; margin: 0; color: #475569;">
        Satellites see raw pixels; mayors see political wards. Administrative boundaries obscure microclimatic pockets, preventing targeted localized action.
      </p>
    </div>
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px;">
      <h4 style="margin-top:0; color:#B45309;">2. Capital Rationing Dilemma</h4>
      <p style="font-size: 7.8pt; margin: 0; color: #475569;">
        Municipal budgets are capped. Cities cannot afford blanket greening and lack mathematical models to prove where each rupee yields maximum thermal protection.
      </p>
    </div>
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px;">
      <h4 style="margin-top:0; color:#475569;">3. The MRV Vacuum</h4>
      <p style="font-size: 7.8pt; margin: 0; color: #475569;">
        Civic tree-planting projects have zero empirical verification. Without counterfactual baseline audits, claims of "cooling" remain unscientific marketing.
      </p>
    </div>
  </div>

  <!-- 3. PROPOSED SOLUTION -->
  <h2>3. Proposed Solution: The CLIMORA Platform</h2>
  <p>
    CLIMORA converts planetary observations into statutory civic capital deployments through a closed-loop six-stage pipeline:
  </p>
  <div class="architecture-diagram">
+--------------------+      +--------------------+      +--------------------+
| 1. SATELLITE INPUT | ---> | 2. SPATIAL MESHING | ---> | 3. RISK SYNTHESIS  |
| Landsat 8/9 C2 L2  |      | Uber H3 Res-9 DGGS |      | IPCC AR6 H x E x V |
| Sentinel-2 MSI     |      | 3,181 Hexagons     |      | Zero-Exposure Rule |
+--------------------+      +--------------------+      +--------------------+
                                                                  |
                                                                  v
+--------------------+      +--------------------+      +--------------------+
| 6. EMPIRICAL MRV   | <--- | 5. CEDAR GOVERN    | <--- | 4. HiGHS OPTIMIZER |
| Diff-in-Diff DiD   |      | 5 Personas / ABAC  |      | Semi-Continuous    |
| Matched Controls   |      | Immutable Truth    |      | 5 Nested Presets   |
+--------------------+      +--------------------+      +--------------------+
  </div>

  <!-- 4. OBJECTIVES -->
  <h2>4. Core Objectives</h2>
  <ul style="margin: 4px 0; padding-left: 18px; font-size: 8.8pt;">
    <li><strong>Equi-Area Discretization:</strong> Partition PMC's 312.11 km² territory into 3,181 uniform Uber H3 Res-9 hexagons (~0.0986 km² each) to guarantee spatial invariance.</li>
    <li><strong>Thermal Baseline Freezing:</strong> Build an empirical 5-year pre-monsoon baseline (April 2021–2025) using cloud-free USGS Landsat 8/9 thermal radiance.</li>
    <li><strong>Zero-Exposure Risk Modeling:</strong> Codify the IPCC AR6 framework ensuring uninhabited hot spots yield zero human risk.</li>
    <li><strong>Mathematical Capital Allocation:</strong> Solve a mixed-integer linear programming (MILP) optimization model under 5 budget presets within a 5% optimality gap.</li>
    <li><strong>Cryptographic Governance:</strong> Implement Amazon Cedar ABAC with 7 ratified policies and strict negative anti-tampering guards.</li>
  </ul>

  <div class="page-break"></div>

  <!-- 5. KEY FEATURES -->
  <h2>5. Key Platform Features</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 28%;">Subsystem Feature</th>
        <th style="width: 44%;">Technical Specification &amp; Implementation</th>
        <th style="width: 28%;">Truth Tier / Lineage</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Hexagonal Global Mesh</strong></td>
        <td>Uber H3 Res-9 (~105m edge, 0.0986 km² area), eliminating boundary gerrymandering</td>
        <td><span class="badge badge-derived">DERIVED</span> Deterministic grid</td>
      </tr>
      <tr>
        <td><strong>Multi-Temporal Baseline</strong></td>
        <td>5-Year April stack (2021–2025), cloud-masked at &le;20%, pixel clear threshold &ge;70%</td>
        <td><span class="badge badge-observed">OBSERVED</span> Landsat 8/9 C2 L2</td>
      </tr>
      <tr>
        <td><strong>IPCC AR6 Risk Matrix</strong></td>
        <td>Multiplicative synthesis: H x E x V with strict zero-exposure enforcement</td>
        <td><span class="badge badge-derived">DERIVED</span> WorldPop + Spectral</td>
      </tr>
      <tr>
        <td><strong>Spatial Hotspot Filter</strong></td>
        <td>Local Moran's I Queen-contiguity spatial weights (p &le; 0.05 pseudo-significance)</td>
        <td><span class="badge badge-derived">DERIVED</span> Econometric LISA</td>
      </tr>
      <tr>
        <td><strong>HiGHS MILP Optimizer</strong></td>
        <td>Branch-and-cut solver with mobilization lot sizes and 4.0 °C thermodynamic safety cap</td>
        <td><span class="badge badge-modeled">MODELED</span> SciPy HiGHS C++</td>
      </tr>
      <tr>
        <td><strong>Nested Monotonic Presets</strong></td>
        <td>5 capital tranches: C(5L) &sub; C(25L) &sub; C(50L) &sub; C(75L) &sub; C(1Cr)</td>
        <td><span class="badge badge-modeled">MODELED</span> Linear Programming</td>
      </tr>
      <tr>
        <td><strong>Amazon Cedar ABAC</strong></td>
        <td>7 ratified policies across 5 institutional roles with negative anti-tamper shields</td>
        <td><span class="badge badge-built">BUILT</span> Cedarpy Rust FFI</td>
      </tr>
      <tr>
        <td><strong>Difference-in-Differences MRV</strong></td>
        <td>Counterfactual baseline analysis against spatial matched control cells</td>
        <td><span class="badge badge-planned">PLANNED</span> ISO 14064-2 Protocol</td>
      </tr>
    </tbody>
  </table>

  <!-- 6. TECH STACK -->
  <h2>6. Technology Stack</h2>
  <div class="grid-2">
    <div>
      <h3 style="margin-top: 2px;">Analytical &amp; Backend Infrastructure</h3>
      <ul style="font-size: 8.2pt; padding-left: 16px; margin: 3px 0;">
        <li><strong>Language:</strong> Python 3.11+, Rust FFI (via cedarpy)</li>
        <li><strong>Solver Engine:</strong> HiGHS (scipy.optimize.milp) branch-and-cut</li>
        <li><strong>Geospatial Processing:</strong> Rasterio, GeoPandas, PyArrow, Libpysal</li>
        <li><strong>API Service Boundary:</strong> Flask 2.3.2, Gunicorn, Pydantic schemas</li>
        <li><strong>Security &amp; Authorization:</strong> Amazon Cedar Policy Engine</li>
        <li><strong>Storage &amp; Data Lake:</strong> Apache Parquet (Snappy), Cloud-Optimized GeoTIFF</li>
      </ul>
    </div>
    <div>
      <h3 style="margin-top: 2px;">Presentation &amp; Cloud Deployment</h3>
      <ul style="font-size: 8.2pt; padding-left: 16px; margin: 3px 0;">
        <li><strong>Frontend Framework:</strong> React 18, Vite, TypeScript, Tailwind CSS</li>
        <li><strong>Mapping Engine:</strong> MapLibre GL, Leaflet, H3-JS vector renderer</li>
        <li><strong>Icons &amp; Design:</strong> Lucide Icons, Headless UI, Custom Dark Navy Palette</li>
        <li><strong>Cloud Infrastructure:</strong> AWS S3 (Data Lake), ECS Fargate, AWS Amplify</li>
        <li><strong>Verification Test Suite:</strong> Pytest (188 backend tests), Vitest (25 UI tests)</li>
      </ul>
    </div>
  </div>

  <!-- 7. SYSTEM ARCHITECTURE -->
  <h2>7. System Architecture &amp; Governance Flow</h2>
  <p>
    CLIMORA enforces a strict separation between <strong>Infrastructure IAM</strong>, <strong>Application Authorization (Amazon Cedar)</strong>, <strong>Domain State Machine</strong>, and <strong>Scientific Truth</strong>:
  </p>
  <div class="architecture-diagram">
API Client Request [X-Climora-Actor / Bearer Token]
   │
   ▼
[ Flask Observability Middleware & Correlation ID ]
   │
   ▼
[ Cedar Policy Evaluation: cedarpy.is_authorized() ]
   │
   ├──> DENY  ──► Return HTTP 403 Forbidden [Structured Explainable Reason] (Zero Mutation)
   │
   └──> ALLOW ──► [ Finite State Machine (FSM) Domain Guard ]
                     │
                     ├──> INVALID STATE ──► Return HTTP 400 (FSM Transition Conflict)
                     │
                     └──> VALID ─────────► [ Execute Service & Commit Immutable Ledger ]
  </div>

  <!-- 8. IMPLEMENTATION & MATHEMATICAL LINEAGE -->
  <h2>8. Implementation &amp; Mathematical Formulations</h2>
  <p>
    Every calculation in CLIMORA traces to codified, ratified formulations in the project register:
  </p>

  <!-- Formula 1 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-01: USGS Landsat 8/9 Surface Reflectance (SR)</div>
      <img src="FORMULAS_PLACEHOLDER/eq1_sr.svg" alt="Eq 1: Surface Reflectance">
    </div>
    <div class="equation-num">(1)</div>
  </div>

  <!-- Formula 2 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-02: Landsat TIRS Land Surface Temperature Conversion</div>
      <img src="FORMULAS_PLACEHOLDER/eq2_lst.svg" alt="Eq 2: LST Conversion">
    </div>
    <div class="equation-num">(2)</div>
  </div>

  <!-- Formula 3 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-04 &amp; F-05: Biophysical Vegetation (NDVI) &amp; Built-Up (NDBI) Indices</div>
      <img src="FORMULAS_PLACEHOLDER/eq3_indices.svg" alt="Eq 3: NDVI and NDBI">
    </div>
    <div class="equation-num">(3)</div>
  </div>

  <!-- Formula 4 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-14 &amp; F-15: 5-Year Pre-Monsoon Baseline &amp; Thermal Anomaly</div>
      <img src="FORMULAS_PLACEHOLDER/eq4_baseline.svg" alt="Eq 4: Baseline and Anomaly">
    </div>
    <div class="equation-num">(4)</div>
  </div>

  <!-- Formula 5 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-22: IPCC AR6 Power-Law Climate Risk Formulation</div>
      <img src="FORMULAS_PLACEHOLDER/eq5_risk.svg" alt="Eq 5: IPCC AR6 Risk">
    </div>
    <div class="equation-num">(5)</div>
  </div>

  <!-- Formula 6 -->
  <div class="callout callout-red" style="margin: 6px 0;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <strong style="color: #B91C1C;">Axiom 1.1: The Zero-Exposure Axiom</strong> &mdash; Human risk collapses to zero where population is zero:
        <br><img src="FORMULAS_PLACEHOLDER/eq6_zero_exp.svg" style="max-height: 26px; margin-top: 3px;" alt="Eq 6: Zero Exposure">
      </div>
      <span class="equation-num">(6)</span>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- Formula 7 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-19 to F-21: Normalized Hazard, Exposure, and Susceptibility Components</div>
      <img src="FORMULAS_PLACEHOLDER/eq7_hev.svg" alt="Eq 7: HEV Synthesis">
    </div>
    <div class="equation-num">(7)</div>
  </div>

  <!-- Formula 8 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-23.1: Anselin Local Moran's I Spatial Autocorrelation &amp; Hotspots</div>
      <img src="FORMULAS_PLACEHOLDER/eq8_moran.svg" alt="Eq 8: Local Moran">
    </div>
    <div class="equation-num">(8)</div>
  </div>

  <!-- Formula 9 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-24.6: Canonical Budget-Constrained HiGHS MILP Formulation</div>
      <img src="FORMULAS_PLACEHOLDER/eq9_milp.svg" alt="Eq 9: HiGHS MILP">
    </div>
    <div class="equation-num">(9)</div>
  </div>

  <!-- Formula 10 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-24.1 &amp; F-24.4: Semi-Continuous Activation, Lot-Size Linking &amp; Saturation Cap</div>
      <img src="FORMULAS_PLACEHOLDER/eq10_constraints.svg" alt="Eq 10: Constraints">
    </div>
    <div class="equation-num">(10)</div>
  </div>

  <!-- Formula 11 -->
  <div class="equation-box">
    <div>
      <div style="font-size: 7.2pt; color: #0284C7; font-weight: 700; text-transform: uppercase;">F-26: Difference-in-Differences (DiD) Empirical MRV Estimator</div>
      <img src="FORMULAS_PLACEHOLDER/eq11_did.svg" alt="Eq 11: Diff in Diff">
    </div>
    <div class="equation-num">(11)</div>
  </div>

  <!-- 9. RESULTS & KEY VISUAL EVIDENCE -->
  <h2>9. Results &amp; Key Visual Evidence</h2>

  <div class="figure-container">
    <img src="ASSETS_PLACEHOLDER/hero_a_citywide_risk_map.png" class="figure-img" alt="Citywide Risk Map and 28 Priority Cells">
    <div class="figure-caption">
      <strong>Figure 1 &bull; Citywide Risk Surface &amp; The 28-Cell Priority Allocation:</strong> 3,181 Uber H3 Res-9 hexagons across Pune Municipal Corporation (312.11 km²). The HiGHS MILP solver isolates the optimal 28 cells (highlighted in cyan/red) under the canonical ₹1 Crore budget envelope.
    </div>
  </div>

  <div class="grid-2">
    <div class="figure-container">
      <img src="ASSETS_PLACEHOLDER/hero_b_rollout_map.png" class="figure-img" style="max-height: 210px;" alt="Rollout Map Across Budget Tiers">
      <div class="figure-caption">
        <strong>Figure 2 &bull; Monotonic Rollout Across 5 Tiers:</strong> Capital expansion scales cleanly: Tier 1 (2 cells) &sub; Tier 2 (8 cells) &sub; Tier 3 (16 cells) &sub; Tier 4 (22 cells) &sub; Tier 5 (28 cells).
      </div>
    </div>
    <div class="figure-container">
      <img src="ASSETS_PLACEHOLDER/hero_c_budget_chart.png" class="figure-img" style="max-height: 210px;" alt="Budget Scaling Analytics">
      <div class="figure-caption">
        <strong>Figure 3 &bull; Budget Scaling &amp; Population Protected:</strong> Dual-axis analytical curve illustrating citizens protected vs. capital expenditure.
      </div>
    </div>
  </div>

  <!-- TABLE OF BUDGET PRESETS -->
  <h3 style="margin-top: 10px;">Canonical Budget Preset Optimization Summary</h3>
  <table>
    <thead>
      <tr>
        <th>Preset Tier</th>
        <th>Budget Envelop</th>
        <th>Capital Allocated</th>
        <th>Budget Slack</th>
        <th>Treated Cells</th>
        <th>Trees Planted</th>
        <th>Population In Scope</th>
        <th>Objective (&Delta;R)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Tier 1 (₹5L)</strong></td>
        <td>₹5,00,000</td>
        <td>₹5,00,000</td>
        <td>₹0</td>
        <td>2 cells</td>
        <td>131 trees</td>
        <td>7,754 residents</td>
        <td>0.006417</td>
      </tr>
      <tr>
        <td><strong>Tier 2 (₹25L)</strong></td>
        <td>₹25,00,000</td>
        <td>₹25,00,000</td>
        <td>₹0</td>
        <td>8 cells</td>
        <td>669 trees</td>
        <td>35,205 residents</td>
        <td>0.029666</td>
      </tr>
      <tr>
        <td><strong>Tier 3 (₹50L)</strong></td>
        <td>₹50,00,000</td>
        <td>₹49,50,500</td>
        <td>₹49,500</td>
        <td>16 cells</td>
        <td>1,323 trees</td>
        <td>67,854 residents</td>
        <td>0.055865</td>
      </tr>
      <tr>
        <td><strong>Tier 4 (₹75L)</strong></td>
        <td>₹75,00,000</td>
        <td>₹72,54,500</td>
        <td>₹2,45,500</td>
        <td>22 cells</td>
        <td>1,947 trees</td>
        <td>92,188 residents</td>
        <td>0.079183</td>
      </tr>
      <tr>
        <td><strong>Tier 5 (₹1 Cr)</strong></td>
        <td>₹1,00,00,000</td>
        <td>₹99,92,500</td>
        <td>₹7,500</td>
        <td>28 cells</td>
        <td>2,695 trees</td>
        <td>118,941 residents</td>
        <td>0.106048</td>
      </tr>
    </tbody>
  </table>

  <div class="page-break"></div>

  <!-- MICRO-CELL CASE STUDY -->
  <h3>Representative Cell Case Study: Cell `89608850003ffff`</h3>
  <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 12px; margin: 6px 0; font-size: 8pt;">
    <div class="grid-2">
      <div>
        <strong>Cell Identifier:</strong> <code>89608850003ffff</code> (H3 Res-9)<br>
        <strong>Baseline Land Surface Temp:</strong> 46.82 °C (Anomaly: +0.46 °C)<br>
        <strong>Local Human Population:</strong> 4,757 residents (High Density)<br>
        <strong>Composite Risk Index:</strong> 0.2222 (Hazard: 0.81, Exposure: 0.92, Vulnerability: 0.30)
      </div>
      <div>
        <strong>Allocated Intervention:</strong> 76 Street-Shade Trees<br>
        <strong>Capital Expenditure:</strong> ₹2,86,000 (Direct ₹2,66,000 + Mobilization ₹20,000)<br>
        <strong>Modeled Cooling Outcome:</strong> 0.0543 °C intra-cell surface relief<br>
        <strong>Statutory Status:</strong> Assigned to Tender <code>PROJ-PUNE-2025-BA225D6A</code>
      </div>
    </div>
  </div>

  <!-- SLIDE GALLERY MOSAIC -->
  <h3 style="margin-top: 12px;">Complete Pitch Presentation Deck Lineage (Novex 2026)</h3>
  <div class="grid-3" style="gap: 8px;">
    <div><img src="ASSETS_PLACEHOLDER/slide_01.png" class="slide-thumbnail" alt="Slide 1"><div style="font-size:6.8pt; color:#64748B; text-align:center;">1. Title &amp; Fact Sheet</div></div>
    <div><img src="ASSETS_PLACEHOLDER/slide_02.png" class="slide-thumbnail" alt="Slide 2"><div style="font-size:6.8pt; color:#64748B; text-align:center;">2. Fragmented Risk</div></div>
    <div><img src="ASSETS_PLACEHOLDER/slide_03.png" class="slide-thumbnail" alt="Slide 3"><div style="font-size:6.8pt; color:#64748B; text-align:center;">3. Detection to Allocation</div></div>
    <div><img src="ASSETS_PLACEHOLDER/slide_04.png" class="slide-thumbnail" alt="Slide 4"><div style="font-size:6.8pt; color:#64748B; text-align:center;">4. What CLIMORA Is</div></div>
    <div><img src="ASSETS_PLACEHOLDER/slide_05.png" class="slide-thumbnail" alt="Slide 5"><div style="font-size:6.8pt; color:#64748B; text-align:center;">5. Pipeline &amp; AI</div></div>
    <div><img src="ASSETS_PLACEHOLDER/slide_06.png" class="slide-thumbnail" alt="Slide 6"><div style="font-size:6.8pt; color:#64748B; text-align:center;">6. Pune Prototype</div></div>
    <div><img src="ASSETS_PLACEHOLDER/slide_07.png" class="slide-thumbnail" alt="Slide 7"><div style="font-size:6.8pt; color:#64748B; text-align:center;">7. Decision Engine</div></div>
    <div><img src="ASSETS_PLACEHOLDER/slide_08.png" class="slide-thumbnail" alt="Slide 8"><div style="font-size:6.8pt; color:#64748B; text-align:center;">8. Cedar Governance</div></div>
    <div><img src="ASSETS_PLACEHOLDER/slide_09.png" class="slide-thumbnail" alt="Slide 9"><div style="font-size:6.8pt; color:#64748B; text-align:center;">9. Empirical MRV</div></div>
  </div>

  <!-- 10. INNOVATION -->
  <h2>10. Innovation &amp; Competitive Differentiation</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 25%;">Dimension</th>
        <th style="width: 35%;">Status Quo / Conventional Portals</th>
        <th style="width: 40%;">CLIMORA Decision Operating System</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Spatial Primitive</strong></td>
        <td>Coarse administrative wards or raster pixels</td>
        <td><strong>Uber H3 Res-9 DGGS:</strong> 3,181 uniform, equidistant equal-area hexagons</td>
      </tr>
      <tr>
        <td><strong>Intelligence Mode</strong></td>
        <td>Passive diagnostic heat maps</td>
        <td><strong>Active Prescriptive Optimization:</strong> HiGHS MILP solving global Pareto front</td>
      </tr>
      <tr>
        <td><strong>Capital Deployment</strong></td>
        <td>Political division or ad-hoc grants</td>
        <td><strong>Monotonic Budget Presets:</strong> Phased, nested mathematical rollouts</td>
      </tr>
      <tr>
        <td><strong>Security Architecture</strong></td>
        <td>Monolithic admin logins</td>
        <td><strong>Amazon Cedar ABAC:</strong> 7 ratified policies separating 5 civic personas</td>
      </tr>
      <tr>
        <td><strong>Data Integrity</strong></td>
        <td>Overwritable databases</td>
        <td><strong>Cryptographic Negative Policy:</strong> Hard forbidden modification of scientific truth</td>
      </tr>
      <tr>
        <td><strong>Accountability</strong></td>
        <td>Unverified claims</td>
        <td><strong>Difference-in-Differences MRV:</strong> ISO 14064-2 matched-control verification</td>
      </tr>
    </tbody>
  </table>

  <!-- 11. IMPACT -->
  <h2>11. Real-World Impact</h2>
  <ul style="font-size: 8.2pt; padding-left: 18px; margin: 3px 0;">
    <li><strong>2.7&times; Density Super-Concentration:</strong> The ₹1 Cr portfolio concentrates capital on just 0.88% of PMC's landmass while directly sheltering 118,941 residents (averaging 4,248 residents/cell vs. citywide mean 1,575).</li>
    <li><strong>Zero Rupee Wastage on Uninhabited Zones:</strong> The Zero-Exposure Axiom guarantees public funds are never wasted on high-heat uninhabited areas (e.g. airport tarmac, quarries).</li>
    <li><strong>Tender-Ready Municipal Dossiers:</strong> Automated generation of municipal procurement briefs with complete bills of quantities (BoQ) and coordinates.</li>
    <li><strong>Bankable Adaptation Assets:</strong> Bridges the climate finance divide, qualifying municipal green bonds for verified ESG performance yields.</li>
  </ul>

  <!-- 12. FUTURE SCOPE -->
  <h2>12. Future Scope &amp; Strategic Roadmap</h2>
  <div style="background: #0F172A; color: #E2E8F0; padding: 8px 12px; border-radius: 6px; font-size: 7.8pt; margin: 6px 0;">
    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 4px; margin-bottom: 6px;">
      <span style="color: #38BDF8; font-weight: 700;">Q4 2026: PMC Field Deployment</span>
      <span style="color: #34D399; font-weight: 700;">Q2 2027: Multi-City Expansion</span>
      <span style="color: #FBBF24; font-weight: 700;">Q1 2028: Sensor Mesh &amp; IoT</span>
    </div>
    <div class="grid-3" style="gap: 10px;">
      <div>Planting across 28 selected cells in Pune &bull; Contractor tracking mobile app &bull; Baseline calibration</div>
      <div>Horizontal scaling across Mumbai, Ahmedabad, and Delhi &bull; State climate portal integration</div>
      <div>Solar LoRaWAN ambient micro-loggers &bull; Drone thermal FLIR audits &bull; On-chain adaptation certificates</div>
    </div>
  </div>

  <!-- 13. REFERENCES -->
  <h2>13. References &amp; Academic Citations</h2>
  <ol style="font-size: 7.2pt; color: #475569; padding-left: 16px; margin: 4px 0;">
    <li><strong>IPCC (2022):</strong> <em>Climate Change 2022: Impacts, Adaptation and Vulnerability.</em> WGII Contribution to AR6. Cambridge University Press.</li>
    <li><strong>USGS (2024):</strong> <em>Landsat 8-9 Collection 2 Level 2 Science Product Guide.</em> U.S. Geological Survey, Version 2.0.</li>
    <li><strong>Anselin, L. (1995):</strong> <em>Local Indicators of Spatial Association—LISA.</em> Geographical Analysis, 27(2), 93–115.</li>
    <li><strong>Huangfu, Q., &amp; Hall, J. A. J. (2018):</strong> <em>Parallelizing the dual revised simplex method.</em> Mathematical Programming Computation, 10(1), 119–142. (HiGHS Optimizer).</li>
    <li><strong>Amazon Web Services (2023):</strong> <em>Cedar Policy Language Specification: Attribute-Based Access Control and Verification.</em></li>
    <li><strong>ISO (2019):</strong> <em>ISO 14064-2: Greenhouse gases — Part 2: Project-level GHG and Climate Impact Verification.</em></li>
    <li><strong>WorldPop (2020):</strong> <em>Global High Resolution Population Denominators Project.</em> University of Southampton.</li>
  </ol>

  <!-- REPOSITORY FOOTER -->
  <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
    <div style="font-size: 7.8pt; color: #475569;">
      <strong>CLIMORA Engineering &amp; Research Lineage:</strong> Department of CSE (AIML), Vishwakarma Institute of Technology (VIT Pune)<br>
      Repository Path: <code>c:/Users/lenovo/climora</code> &bull; All 188 Backend and 25 Frontend Tests Passing.
    </div>
    <div>
      <img src="ASSETS_PLACEHOLDER/qr_github.png" style="width: 44px; height: 44px;" alt="Repository QR">
    </div>
  </div>

</body>
</html>
"""

# Replace placeholders safely
final_html = html_template.replace("FORMULAS_PLACEHOLDER", FORMULAS_DIR).replace("ASSETS_PLACEHOLDER", ASSETS_DIR)

with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"HTML written to {HTML_OUTPUT}")

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_path,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={PDF_OUTPUT}",
    str(HTML_OUTPUT)
]

print("Executing Microsoft Edge headless print-to-pdf...")
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
if PDF_OUTPUT.exists():
    print(f"SUCCESS: Generated PDF at {PDF_OUTPUT} with size {PDF_OUTPUT.stat().st_size} bytes")
else:
    print("FAILED to generate PDF:", res.stderr)
