import os
import io
import base64
import subprocess
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("c:/Users/lenovo/climora")
ASSETS_DIR = PROJECT_ROOT / "docs" / "assets"
HTML_OUTPUT = PROJECT_ROOT / "CLIMORA_PROJECT_REPORT.html"
PDF_OUTPUT = PROJECT_ROOT / "CLIMORA_PROJECT_REPORT.pdf"

print("Step 1: Rendering high-DPI mathematical formulas (300 DPI transparent PNGs)...")
formulas = {
    'eq1_sr': r'$\rho_\lambda = \mathrm{DN}_\lambda \times 0.0000275 - 0.2$',
    'eq2_lst': r'$T_s (^\circ\mathrm{C}) = (\mathrm{DN}_{\mathrm{ST\_B10}} \times 0.00341802 + 149.0) - 273.15$',
    'eq3_indices': r'$\mathrm{NDVI} = \frac{\rho_{\mathrm{NIR}} - \rho_{\mathrm{Red}}}{\rho_{\mathrm{NIR}} + \rho_{\mathrm{Red}}}, \quad \mathrm{NDBI} = \frac{\rho_{\mathrm{SWIR1}} - \rho_{\mathrm{NIR}}}{\rho_{\mathrm{SWIR1}} + \rho_{\mathrm{NIR}}}$',
    'eq4_baseline': r'$\overline{T}_{s,i} = \frac{1}{K_i} \sum_{k=1}^{K_i} T_{s,i,k}, \quad \Delta T_{s,i} = T_{s,i,2025} - \overline{T}_{s,i}$',
    'eq5_risk': r'$\mathrm{Risk}_i = \mathcal{H}_i^\alpha \times \mathcal{E}_i^\beta \times \mathcal{V}_i^\gamma \quad (\alpha = \beta = \gamma = 1.0)$',
    'eq6_zero_exp': r'$\mathcal{E}_i = 0 \Rightarrow \mathrm{Risk}_i = 0 \quad (\mathrm{Zero-Exposure\ Axiom})$',
    'eq7_hev': r'$\mathcal{H}_i = w_1 \widetilde{T}_{s,i} + w_2 \widetilde{\Delta T}_{s,i} + w_3 P_{75,i} + w_4 F_{45,i}, \quad \mathcal{E}_i = \widetilde{\mathrm{Pop}}_i, \quad \mathcal{V}_i = 0.5(1 - \widetilde{\mathrm{NDVI}}_i) + 0.5\widetilde{\mathrm{NDBI}}_i$',
    'eq8_moran': r'$I_i = \frac{z_i - \bar{z}}{s^2} \sum_{j \in N(i)} w_{ij} (z_j - \bar{z})$',
    'eq9_milp': r'$\max_{x, y} \sum_{i=1}^N \sum_{j=1}^M \Delta \mathcal{R}_{i,j} \cdot x_{i,j} \quad \mathrm{s.t.} \quad \sum_{i=1}^N \sum_{j=1}^M \left(c_j^{\mathrm{unit}} x_{i,j} + c_j^{\mathrm{mob}} y_{i,j}\right) \leq B_{\mathrm{total}}$',
    'eq10_constraints': r'$L_{i,j} \cdot y_{i,j} \leq x_{i,j} \leq C_{i,j} \cdot y_{i,j}, \quad y_{i,j} \in \{0, 1\}, \quad \sum_{j=1}^M \kappa_j x_{i,j} \leq 4.0^\circ\mathrm{C}$',
    'eq11_did': r'$\hat{\delta}_{\mathrm{DiD}} = \left(\overline{T}_{\mathrm{treat}}^{\mathrm{post}} - \overline{T}_{\mathrm{treat}}^{\mathrm{pre}}\right) - \left(\overline{T}_{\mathrm{ctrl}}^{\mathrm{post}} - \overline{T}_{\mathrm{ctrl}}^{\mathrm{pre}}\right)$'
}

formula_b64 = {}
for name, tex in formulas.items():
    fig = plt.figure(figsize=(9.5, 0.95), dpi=300)
    fig.text(0.5, 0.5, tex, fontsize=17, ha='center', va='center', color='#0B192C')
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.04, transparent=True)
    plt.close(fig)
    buf.seek(0)
    formula_b64[name] = base64.b64encode(buf.read()).decode('ascii')

print("Step 2: Base64 encoding hero graphics and architecture diagram...")
images = {
    'hero_a': (ASSETS_DIR / "hero_a_citywide_risk_map.png"),
    'hero_b': (ASSETS_DIR / "hero_b_rollout_map.png"),
    'hero_c': (ASSETS_DIR / "hero_c_budget_chart.png"),
    'qr': (ASSETS_DIR / "qr_github.png"),
    'arch': (ASSETS_DIR / "climora_system_architecture.jpg")
}

image_b64 = {}
for key, path in images.items():
    if path.exists():
        image_b64[key] = base64.b64encode(path.read_bytes()).decode('ascii')
    else:
        print(f"Warning: {path} not found!")

print("Step 3: Constructing fluid, publication-grade HTML...")
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CLIMORA — Technical Report & Research Whitepaper</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  @page {{
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
    @bottom-right {{
      content: "Page " counter(page);
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 8pt;
      color: #64748B;
    }}
  }}

  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  body {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #0F172A;
    background: #FFFFFF;
    line-height: 1.62;
    font-size: 9.3pt;
    margin: 0;
    padding: 0;
  }}

  /* Typography */
  h1, h2, h3, h4 {{
    color: #0B192C;
    font-weight: 700;
    letter-spacing: -0.025em;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
    break-after: avoid;
    page-break-after: avoid;
  }}

  h1 {{ font-size: 22pt; line-height: 1.2; font-weight: 800; }}
  h2 {{ 
    font-size: 13pt; 
    border-bottom: 2px solid #0284C7; 
    padding-bottom: 3px; 
    margin-top: 1.4em;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #0B192C;
  }}
  h3 {{ font-size: 10.5pt; color: #1E3A8A; margin-top: 1em; }}
  h4 {{ font-size: 9.5pt; color: #334155; }}

  p {{
    margin: 0.55em 0;
    text-align: justify;
    text-justify: inter-word;
  }}

  code {{
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 8.2pt;
    background: #F1F5F9;
    color: #0F172A;
    padding: 1.5px 4px;
    border-radius: 4px;
    border: 1px solid #E2E8F0;
  }}

  /* Badges & Pills */
  .badge {{
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 6.8pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 2px 5.5px;
    border-radius: 3px;
    margin-right: 3px;
  }}
  .badge-observed {{ background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }}
  .badge-derived {{ background: #E0F2FE; color: #0369A1; border: 1px solid #7DD3FC; }}
  .badge-modeled {{ background: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; }}
  .badge-built {{ background: #EDE9FE; color: #6D28D9; border: 1px solid #C4B5FD; }}
  .badge-planned {{ background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }}

  /* Cover & Headers */
  .cover-header {{
    border-bottom: 2.5px solid #0B192C;
    padding-bottom: 12px;
    margin-bottom: 16px;
  }}

  .doc-tagline {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #0284C7;
    font-weight: 700;
    margin-bottom: 5px;
  }}

  .authors-block {{
    display: flex;
    justify-content: space-between;
    font-size: 8.5pt;
    color: #475569;
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px solid #E2E8F0;
  }}

  /* Metric KPI Grid */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 14px 0;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .kpi-card {{
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-left: 3.5px solid #0284C7;
    padding: 8px 12px;
    border-radius: 5px;
  }}
  .kpi-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 6.8pt;
    text-transform: uppercase;
    color: #64748B;
    font-weight: 600;
  }}
  .kpi-value {{
    font-size: 13.5pt;
    font-weight: 800;
    color: #0B192C;
    margin: 2px 0;
    letter-spacing: -0.02em;
  }}
  .kpi-sub {{
    font-size: 7.2pt;
    color: #475569;
  }}

  /* Callout Boxes */
  .callout {{
    margin: 12px 0;
    padding: 9px 13px;
    border-radius: 5px;
    font-size: 8.8pt;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .callout-blue {{
    background: #F0F9FF;
    border: 1px solid #BAE6FD;
    border-left: 3.5px solid #0284C7;
  }}
  .callout-red {{
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-left: 3.5px solid #DC2626;
  }}

  /* Equations */
  .equation-box {{
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 5px;
    padding: 6px 12px;
    margin: 6px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  .equation-content {{
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}
  .equation-title {{
    font-size: 7.2pt;
    color: #0284C7;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }}
  .equation-img {{
    height: 27px;
    width: auto;
    object-fit: contain;
  }}
  .equation-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.2pt;
    color: #64748B;
    font-weight: 600;
  }}

  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 8pt;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  th, td {{
    padding: 6px 8px;
    text-align: left;
    border-bottom: 1px solid #E2E8F0;
  }}
  th {{
    background: #0F172A;
    color: #FFFFFF;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 6.8pt;
    letter-spacing: 0.04em;
  }}
  tr:nth-child(even) td {{
    background: #F8FAFC;
  }}

  /* Visual Figures */
  .figure-container {{
    margin: 12px 0;
    break-inside: avoid;
    page-break-inside: avoid;
    text-align: center;
  }}
  .figure-img {{
    width: 100%;
    max-height: 270px;
    object-fit: contain;
    border-radius: 5px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}
  .figure-caption {{
    font-size: 8pt;
    color: #475569;
    margin-top: 5px;
    font-weight: 500;
    text-align: center;
  }}

  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    break-inside: avoid;
    page-break-inside: avoid;
  }}

  .grid-3 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    break-inside: avoid;
    page-break-inside: avoid;
  }}

  /* Diagram Box */
  .architecture-diagram {{
    background: #0A192F;
    color: #E2E8F0;
    border-radius: 5px;
    padding: 10px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 7.2pt;
    line-height: 1.4;
    white-space: pre;
    overflow-x: auto;
    margin: 8px 0;
    border: 1px solid #1E293B;
    break-inside: avoid;
    page-break-inside: avoid;
  }}
</style>
</head>
<body>

  <!-- COVER / HEADER -->
  <div class="cover-header">
    <div class="doc-tagline">CLIMORA TECHNICAL REPORT &bull; RESEARCH WHITEPAPER &bull; URBAN CLIMATE INTELLIGENCE</div>
    <h1 style="margin: 3px 0 5px 0;">CLIMORA: A Decision Layer for Urban Heat Risk</h1>
    <div style="font-size: 11pt; color: #334155; font-weight: 500; margin-bottom: 8px;">
      Spatial Optimization, Cryptographic Governance &amp; Empirical MRV for Municipal Climate Adaptation
    </div>
    
    <div class="authors-block">
      <div><strong>Authors:</strong> Sujay Korde &amp; Kimaya Kolhe &bull; <em>Department of CSE (AIML), Vishwakarma Institute of Technology (VIT Pune)</em></div>
      <div><strong>Study Area:</strong> Pune Municipal Corporation (PMC), India &bull; <strong>Lineage:</strong> Fully Validated</div>
    </div>
  </div>

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
    <strong>Governing Axiom &mdash; Evidence Truth Badges:</strong> Every metric in CLIMORA carries a classified truth badge: 
    <span class="badge badge-observed">OBSERVED</span> Satellite sensor radiances &bull; 
    <span class="badge badge-derived">DERIVED</span> Deterministic mathematical synthesis &bull; 
    <span class="badge badge-modeled">MODELED</span> HiGHS optimization outputs &bull; 
    <span class="badge badge-built">BUILT</span> Production codebase &bull; 
    <span class="badge badge-planned">PLANNED</span> Empirical field MRV protocol.
  </div>

  <!-- 2. PROBLEM STATEMENT -->
  <h2>2. Problem Statement</h2>
  <p>
    Rapid urbanization across Indian metropolises has replaced vegetative canopy with dense, heat-absorbing concrete and asphalt. In Pune, peak-summer surface temperatures regularly exceed <strong>45.0 °C</strong>. However, public mitigation remains paralyzed by three fundamental institutional failures:
  </p>
  <div class="grid-3" style="margin: 8px 0;">
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px; border-radius: 5px;">
      <h4 style="margin-top:0; color:#B91C1C;">1. Spatial Disconnect</h4>
      <p style="font-size: 7.8pt; margin: 0; color: #475569;">
        Satellites observe continuous pixels; municipal commissioners manage political wards. Coarse administrative boundaries obscure micro-heat pockets.
      </p>
    </div>
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px; border-radius: 5px;">
      <h4 style="margin-top:0; color:#B45309;">2. Capital Allocation Vacuum</h4>
      <p style="font-size: 7.8pt; margin: 0; color: #475569;">
        Climate capital is finite. Municipalities lack mathematical optimization tools to determine where each rupee yields maximum citizen protection.
      </p>
    </div>
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px; border-radius: 5px;">
      <h4 style="margin-top:0; color:#475569;">3. Zero Empirical Verification</h4>
      <p style="font-size: 7.8pt; margin: 0; color: #475569;">
        Civic greening initiatives operate with zero post-deployment auditing. Without counterfactual baseline audits, cooling claims remain unverified.
      </p>
    </div>
  </div>

  <!-- 3. PROPOSED SOLUTION -->
  <h2>3. Proposed Solution: The CLIMORA Platform</h2>
  <p>
    CLIMORA bridges detection and execution through an integrated, closed-loop six-stage pipeline:
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

  <!-- 4. CORE OBJECTIVES -->
  <h2>4. Core Objectives</h2>
  <ul style="margin: 6px 0; padding-left: 20px; font-size: 8.8pt;">
    <li><strong>Equi-Area Discretization:</strong> Partition PMC's 312.11 km² statutory territory into 3,181 uniform Uber H3 Res-9 hexagons (~0.0986 km² each) to guarantee spatial invariance.</li>
    <li><strong>Thermal Baseline Freezing:</strong> Build an empirical 5-year pre-monsoon baseline (April 2021–2025) using cloud-free USGS Landsat 8/9 thermal radiance.</li>
    <li><strong>Zero-Exposure Risk Modeling:</strong> Codify the IPCC AR6 framework ensuring uninhabited hot spots yield zero human risk.</li>
    <li><strong>Mathematical Capital Allocation:</strong> Solve a mixed-integer linear programming (MILP) optimization model under 5 budget presets within a 5% optimality gap.</li>
    <li><strong>Cryptographic Governance:</strong> Implement Amazon Cedar ABAC with 7 ratified policies and strict negative anti-tampering guards.</li>
  </ul>

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
        <td>Multiplicative synthesis: Hazard &times; Exposure &times; Vulnerability with zero-exposure rule</td>
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
        <td>5 capital tranches: Tier 1 (₹5L) &sub; Tier 2 (₹25L) &sub; Tier 3 (₹50L) &sub; Tier 4 (₹75L) &sub; Tier 5 (₹1Cr)</td>
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
      <ul style="font-size: 8.4pt; padding-left: 18px; margin: 4px 0;">
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
      <ul style="font-size: 8.4pt; padding-left: 18px; margin: 4px 0;">
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

  <!-- Embed 3D Isometric Architecture Diagram -->
  <div class="figure-container">
    <img src="data:image/jpeg;base64,{image_b64.get('arch', '')}" class="figure-img" style="max-height: 280px;" alt="CLIMORA 3D Isometric System Architecture">
    <div class="figure-caption">
      <strong>Figure: CLIMORA 3D System Architecture &amp; Governance Stack:</strong> 5-Tier decoupled topology bridging planetary satellite sensing, Uber H3 hexagonal meshing, HiGHS MILP spatial optimization, Amazon Cedar ABAC cryptographic policy governance, and MapLibre GL executive civic decision layer.
    </div>
  </div>

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

  <div class="grid-2">
    <!-- Formula 1 -->
    <div class="equation-box">
      <div class="equation-content">
        <div class="equation-title">F-01: USGS Landsat 8/9 Surface Reflectance</div>
        <img src="data:image/png;base64,{formula_b64['eq1_sr']}" class="equation-img" alt="Eq 1: Surface Reflectance">
      </div>
      <div class="equation-num">(1)</div>
    </div>

    <!-- Formula 2 -->
    <div class="equation-box">
      <div class="equation-content">
        <div class="equation-title">F-02: Landsat TIRS Land Surface Temp</div>
        <img src="data:image/png;base64,{formula_b64['eq2_lst']}" class="equation-img" alt="Eq 2: LST Conversion">
      </div>
      <div class="equation-num">(2)</div>
    </div>
  </div>

  <!-- Formula 3 -->
  <div class="equation-box">
    <div class="equation-content">
      <div class="equation-title">F-04 &amp; F-05: Biophysical Vegetation (NDVI) &amp; Built-Up (NDBI) Indices</div>
      <img src="data:image/png;base64,{formula_b64['eq3_indices']}" class="equation-img" alt="Eq 3: NDVI and NDBI">
    </div>
    <div class="equation-num">(3)</div>
  </div>

  <!-- Formula 4 -->
  <div class="equation-box">
    <div class="equation-content">
      <div class="equation-title">F-14 &amp; F-15: 5-Year Pre-Monsoon Baseline &amp; Thermal Anomaly</div>
      <img src="data:image/png;base64,{formula_b64['eq4_baseline']}" class="equation-img" alt="Eq 4: Baseline and Anomaly">
    </div>
    <div class="equation-num">(4)</div>
  </div>

  <div class="grid-2">
    <!-- Formula 5 -->
    <div class="equation-box">
      <div class="equation-content">
        <div class="equation-title">F-22: IPCC AR6 Power-Law Risk</div>
        <img src="data:image/png;base64,{formula_b64['eq5_risk']}" class="equation-img" alt="Eq 5: IPCC AR6 Risk">
      </div>
      <div class="equation-num">(5)</div>
    </div>

    <!-- Formula 6 -->
    <div class="equation-box" style="border-left: 3.5px solid #DC2626; background: #FEF2F2;">
      <div class="equation-content">
        <div class="equation-title" style="color: #DC2626;">Axiom 1.1: Zero-Exposure Axiom</div>
        <img src="data:image/png;base64,{formula_b64['eq6_zero_exp']}" class="equation-img" alt="Eq 6: Zero Exposure">
      </div>
      <div class="equation-num">(6)</div>
    </div>
  </div>

  <!-- Formula 7 -->
  <div class="equation-box">
    <div class="equation-content">
      <div class="equation-title">F-19 to F-21: Normalized Hazard, Exposure, and Susceptibility Components</div>
      <img src="data:image/png;base64,{formula_b64['eq7_hev']}" class="equation-img" alt="Eq 7: HEV Synthesis">
    </div>
    <div class="equation-num">(7)</div>
  </div>

  <!-- Formula 8 -->
  <div class="equation-box">
    <div class="equation-content">
      <div class="equation-title">F-23.1: Anselin Local Moran's I Spatial Autocorrelation &amp; Hotspots</div>
      <img src="data:image/png;base64,{formula_b64['eq8_moran']}" class="equation-img" alt="Eq 8: Local Moran">
    </div>
    <div class="equation-num">(8)</div>
  </div>

  <!-- Formula 9 -->
  <div class="equation-box">
    <div class="equation-content">
      <div class="equation-title">F-24.6: Canonical Budget-Constrained HiGHS MILP Formulation</div>
      <img src="data:image/png;base64,{formula_b64['eq9_milp']}" class="equation-img" alt="Eq 9: HiGHS MILP">
    </div>
    <div class="equation-num">(9)</div>
  </div>

  <!-- Formula 10 -->
  <div class="equation-box">
    <div class="equation-content">
      <div class="equation-title">F-24.1 &amp; F-24.4: Semi-Continuous Activation, Lot-Size Linking &amp; Saturation Cap</div>
      <img src="data:image/png;base64,{formula_b64['eq10_constraints']}" class="equation-img" alt="Eq 10: Constraints">
    </div>
    <div class="equation-num">(10)</div>
  </div>

  <!-- Formula 11 -->
  <div class="equation-box">
    <div class="equation-content">
      <div class="equation-title">F-26: Difference-in-Differences (DiD) Empirical MRV Estimator</div>
      <img src="data:image/png;base64,{formula_b64['eq11_did']}" class="equation-img" alt="Eq 11: Diff in Diff">
    </div>
    <div class="equation-num">(11)</div>
  </div>

  <!-- 9. RESULTS & KEY VISUAL EVIDENCE -->
  <h2>9. Results &amp; Key Visual Evidence</h2>

  <div class="figure-container">
    <img src="data:image/png;base64,{image_b64['hero_a']}" class="figure-img" style="max-height: 250px;" alt="Citywide Risk Map and 28 Priority Cells">
    <div class="figure-caption">
      <strong>Figure 1 &bull; Citywide Risk Surface &amp; Canonical ₹1 Cr Footprint:</strong> 3,181 Uber H3 Res-9 hexagons across Pune Municipal Corporation (312.11 km²). The HiGHS MILP solver isolates the optimal 28 cells (highlighted in cyan/red) under the ₹10,000,000 budget envelope.
    </div>
  </div>

  <h3>Canonical Budget Preset Optimization Summary</h3>
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

  <h3>Representative Cell Case Study: Cell `89608850003ffff`</h3>
  <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 5px; padding: 8px 12px; margin: 8px 0; font-size: 8.2pt;">
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

  <div class="grid-2" style="margin-top: 14px;">
    <div class="figure-container">
      <img src="data:image/png;base64,{image_b64['hero_b']}" class="figure-img" style="max-height: 240px;" alt="Rollout Map Across Budget Tiers">
      <div class="figure-caption">
        <strong>Figure 2 &bull; Monotonic Multi-Tier Rollout Map:</strong> Capital expansion scales cleanly across the 5 presets: Tier 1 (2 cells) &sub; Tier 2 (8 cells) &sub; Tier 3 (16 cells) &sub; Tier 4 (22 cells) &sub; Tier 5 (28 cells).
      </div>
    </div>
    <div class="figure-container">
      <img src="data:image/png;base64,{image_b64['hero_c']}" class="figure-img" style="max-height: 240px;" alt="Budget Scaling Analytics">
      <div class="figure-caption">
        <strong>Figure 3 &bull; Budget Scaling &amp; Population Protected:</strong> Dual-axis analytical curve illustrating citizens protected vs. capital expenditure, demonstrating diminishing marginal costs per protected resident.
      </div>
    </div>
  </div>

  <h3>Analytical Findings on Spatial Stability &amp; Efficiency</h3>
  <p>
    The empirical results confirm three critical operational properties of the CLIMORA optimization engine:
  </p>
  <ul style="font-size: 8.5pt; padding-left: 18px; margin: 4px 0;">
    <li><strong>Monotonic Investment Inclusion:</strong> As municipal capital increases from ₹5 Lakh to ₹1 Crore, previously selected cells remain funded, preventing fragmented multi-year municipal planning.</li>
    <li><strong>Extreme Population Concentration:</strong> Under the ₹1 Crore portfolio, CLIMORA concentrates capital on just 0.88% of PMC's landmass (2.76 km²) while directly sheltering 118,941 residents (averaging 4,248 residents/cell vs. citywide mean 1,575), achieving a <strong>2.7&times; density super-concentration factor</strong>.</li>
    <li><strong>Thermodynamic Safety Boundaries:</strong> All allocated interventions remain well within the 4.0 °C intra-cell cooling saturation cap, guaranteeing realistic biophysical performance without mathematical artifacts.</li>
  </ul>

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
  <ul style="font-size: 8.6pt; padding-left: 18px; margin: 4px 0;">
    <li><strong>2.7&times; Density Super-Concentration:</strong> The ₹1 Cr portfolio concentrates capital on just 0.88% of PMC's landmass while directly sheltering 118,941 residents (averaging 4,248 residents/cell vs. citywide mean 1,575).</li>
    <li><strong>Zero Rupee Wastage on Uninhabited Zones:</strong> The Zero-Exposure Axiom guarantees public funds are never wasted on high-heat uninhabited areas (e.g. airport tarmac, bare quarries).</li>
    <li><strong>Tender-Ready Municipal Dossiers:</strong> Automated generation of municipal procurement briefs with complete bills of quantities (BoQ) and coordinates.</li>
    <li><strong>Bankable Adaptation Assets:</strong> Bridges the climate finance divide, qualifying municipal green bonds for verified ESG performance yields.</li>
  </ul>

  <!-- 12. FUTURE SCOPE -->
  <h2>12. Future Scope &amp; Strategic Roadmap</h2>
  <div style="background: #0F172A; color: #E2E8F0; padding: 10px 14px; border-radius: 5px; font-size: 8pt; margin: 8px 0;">
    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 5px; margin-bottom: 6px;">
      <span style="color: #38BDF8; font-weight: 700;">Phase I (Q4 2026): PMC Field Deployment</span>
      <span style="color: #34D399; font-weight: 700;">Phase II (Q2 2027): Multi-City Expansion</span>
      <span style="color: #FBBF24; font-weight: 700;">Phase III (Q1 2028): Sensor Mesh &amp; IoT</span>
    </div>
    <div class="grid-3" style="gap: 10px;">
      <div>Planting across 28 selected cells in Pune &bull; Contractor tracking mobile app &bull; Baseline calibration</div>
      <div>Horizontal scaling across Mumbai, Ahmedabad, and Delhi &bull; State climate portal integration</div>
      <div>Solar LoRaWAN ambient micro-loggers &bull; Drone thermal FLIR audits &bull; On-chain adaptation certificates</div>
    </div>
  </div>

  <!-- 13. REFERENCES -->
  <h2>13. References &amp; Academic Citations</h2>
  <ol style="font-size: 7.6pt; color: #475569; padding-left: 16px; margin: 6px 0;">
    <li><strong>IPCC (2022):</strong> <em>Climate Change 2022: Impacts, Adaptation and Vulnerability.</em> WGII Contribution to AR6. Cambridge University Press.</li>
    <li><strong>USGS (2024):</strong> <em>Landsat 8-9 Collection 2 Level 2 Science Product Guide.</em> U.S. Geological Survey, Version 2.0.</li>
    <li><strong>Anselin, L. (1995):</strong> <em>Local Indicators of Spatial Association—LISA.</em> Geographical Analysis, 27(2), 93–115.</li>
    <li><strong>Huangfu, Q., &amp; Hall, J. A. J. (2018):</strong> <em>Parallelizing the dual revised simplex method.</em> Mathematical Programming Computation, 10(1), 119–142. (HiGHS Optimizer).</li>
    <li><strong>Amazon Web Services (2023):</strong> <em>Cedar Policy Language Specification: Attribute-Based Access Control and Verification.</em></li>
    <li><strong>ISO (2019):</strong> <em>ISO 14064-2: Greenhouse gases — Part 2: Project-level GHG and Climate Impact Verification.</em></li>
    <li><strong>WorldPop (2020):</strong> <em>Global High Resolution Population Denominators Project.</em> University of Southampton.</li>
  </ol>

  <!-- REPOSITORY FOOTER -->
  <div style="margin-top: 14px; padding-top: 8px; border-top: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center;">
    <div style="font-size: 7.8pt; color: #475569;">
      <strong>CLIMORA Engineering &amp; Research Lineage:</strong> Department of CSE (AIML), Vishwakarma Institute of Technology (VIT Pune)<br>
      Repository Path: <code>c:/Users/lenovo/climora</code> &bull; All 188 Backend and 25 Frontend Tests Passing.
    </div>
    <div>
      <img src="data:image/png;base64,{image_b64['qr']}" style="width: 44px; height: 44px;" alt="Repository QR">
    </div>
  </div>

</body>
</html>
"""

with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Step 4: HTML successfully written to {HTML_OUTPUT} ({HTML_OUTPUT.stat().st_size} bytes)")

print("Step 5: Invoking Microsoft Edge headless renderer...")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_path,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={PDF_OUTPUT}",
    str(HTML_OUTPUT)
]

res = subprocess.run(cmd, capture_output=True, text=True)
if PDF_OUTPUT.exists():
    print(f"SUCCESS: Generated PDF at {PDF_OUTPUT} ({PDF_OUTPUT.stat().st_size} bytes)")
else:
    print("FAILED to generate PDF:", res.stderr)
