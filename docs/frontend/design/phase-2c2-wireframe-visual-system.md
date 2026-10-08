# CLIMORA — PHASE 2C.2 WIREFRAME & VISUAL SYSTEM EXPLORATION
## Spatial Decision Engine Wireframes, Visual Architecture & Interaction Prototypes

**Document Version:** 1.0.0  
**Phase:** Phase 2C.2 — Wireframe & Visual System Exploration  
**Target Document Path:** `docs/frontend/design/phase-2c2-wireframe-visual-system.md`  
**Parent Specifications:**
- Design Foundation: [`docs/frontend/design/phase-2c0-design-foundation.md`](file:///c:/Users/lenovo/climora/docs/frontend/design/phase-2c0-design-foundation.md)
- Information Architecture: [`docs/frontend/design/phase-2c1-information-architecture.md`](file:///c:/Users/lenovo/climora/docs/frontend/design/phase-2c1-information-architecture.md)
- User Journey: [`docs/frontend/design/phase-2c1-user-journey.md`](file:///c:/Users/lenovo/climora/docs/frontend/design/phase-2c1-user-journey.md)  
**Governing Roles:** Principal Product Designer, Senior UX Architect, Senior UI/UX Engineer, Design Systems Architect, Lead Product Strategist  
**Status:** **RATIFIED WIREFRAME & VISUAL SYSTEM SPECIFICATION**  
**Backend & Scientific Freeze:** Phase 1A–1H.2, Phase 2A, Phase 2B (160 tests passing, 0 failures, 0 regressions)  
**Scientific Formulations Introduced:** **NONE** (Zero client-side recalculation; formulations $F\text{-}19$ through $F\text{-}28.1$ frozen)  

---

## 1. PHASE OBJECTIVE

The primary objective of **Phase 2C.2** is to translate the Information Architecture ratified in Phase 2C.1 into **rigorous visual wireframes, layout geometries, typography systems, color tokens, and UI state models**.

This document ensures that before a single line of React, CSS, or WebGL is implemented:
1. Every screen, view, and interaction drawer is mapped to authoritative backend contracts.
2. The user experience embodies the visual restraint of an **editorial scientific monograph** and the operational precision of a **spatial decision instrument**, deliberately rejecting generic SaaS and dashboard aesthetics.
3. The visual divergence between `MODELED` ex-ante projections and `VERIFIED` empirical observations is mathematically and visually impossible to conflate.
4. The 3–5 minute hackathon demonstration sequence is structurally validated across laptop and projection viewports.

---

## 2. UPSTREAM CONTRACT AUDIT & CONSISTENCY REVIEW

Before authoring layout wireframes, a forensic audit was executed comparing Phase 2C.1 design claims against the frozen backend codebase, Parquet assets, and scientific registers.

```
+----------------------------------------------------------------------------------------------------+
|                         PHASE 2C.1 -> UPSTREAM CONTRACT AUDIT MATRIX                               |
+------------------------------------+---------------+-----------------------------------------------+
| AUDITED PARAMETER / CLAIM          | STATUS        | FORENSIC AUDIT DETERMINATION                  |
+------------------------------------+---------------+-----------------------------------------------+
| 5-Year Pre-Monsoon Baseline        | CONFIRMED     | Landsat 8/9 scenes (2021-2025), DOY 101-114.   |
| Multi-Year Anomaly Formulation     | CONFIRMED     | Absolute & z-score anomaly under F-15.        |
| 2025 Sensor Platform Identity      | CONTRADICTION | Phase 2C.1 stated "Landsat-9 TIRS DOY 105".   |
|                                    |               | CONTRACT CONFLICT -> Actual 2025 scene is     |
|                                    |               | Landsat 8 (LC08, DOY 109, April 19 2025).     |
|                                    |               | Landsat 9 was acquired in 2023 (DOY 112).     |
| Target Temporal Window (DOY 105)   | CONFIRMED     | Canonical target DOY 105; window DOY 95-115.  |
| In-Scope Beneficiary Population    | CONFIRMED     | Exact 118,941.21 persons; rounded: 118,941.   |
| WorldPop Dataset Baseline          | CONFIRMED     | WorldPop 2020 UN-adjusted dasymetric sum.     |
| H3 DGGS Analytical Topology        | CONFIRMED     | Uber H3 Resolution 9 (~0.0986 km² / 9.86 ha). |
| Total Pune AOI Cell Count          | CONFIRMED     | Exactly 3,181 hexagons over 312.11 km² AOI.   |
| Canonical Treated Cell Footprint   | CONFIRMED     | Exactly 28 selected cells in allocation Parquet|
| Physical Tree Deployment Scope     | CONFIRMED     | Exactly 2,695 street trees (street_tree_shade)|
| Direct Unit Planting Cost          | CONFIRMED     | ₹3,500 / tree (direct planting + 2m guard).    |
| Cell Mobilization Cost             | CONFIRMED     | ₹20,000 / cell (recon, utility, logistics).   |
| Total Modeled Project CapEx        | CONFIRMED     | ₹9,992,500 (2,695*3,500 + 28*20,000).         |
| Municipal Scenario Budget Envelope | CONFIRMED     | ₹10,000,000 scenario ceiling.                 |
| Unallocated Budget Slack           | CONFIRMED     | ₹7,500 remaining municipal surplus.           |
| Modeled Risk-Objective Reduction   | CONFIRMED     | 0.10604830270054796 (F-24.4 MILP objective).  |
| Sentinel-2 Thermal Sensor Claim    | CONFIRMED     | S2 is optical (NDVI/NDBI); rejected for LST.  |
| Synthetic MRV Data Quarantine      | CONFIRMED     | Rejects DEMO_ONLY_SYNTHETIC_MRV_DATA (422).   |
| Verification Readiness State       | CONFIRMED     | VERIFIED is null; DID is PLANNED / NOT_YET... |
| Allocation Immutability Guard      | CONFIRMED     | Direct PUT/PATCH/DELETE rejected with 405.    |
+------------------------------------+---------------+-----------------------------------------------+
```

### Forensic Rectification:
> [!IMPORTANT]
> **Contract Correction Applied to Wireframes:** Phase 2C.1 text loosely referred to the current-state 2025 satellite observation as *"Landsat-9 TIRS DOY 105"*. The authoritative acquisition manifest ([`processing/config.py`](file:///c:/Users/lenovo/climora/processing/config.py#L101-L115)) and feature contract confirm that the actual 2025 satellite asset in the data lake is **Landsat 8 OLI/TIRS-1** (`LC08_L2SP_147047_20250419_02_T1`) acquired on **2025-04-19 (DOY 109)**. Day of Year 105 represents the canonical *target* center of the pre-monsoon window (DOY 95–115). All wireframes and technical annotations in Phase 2C.2 reflect the true empirical metadata.

---

## 3. DESIGN PRINCIPLES & GOVERNANCE AXIOMS

The wireframes strictly enforce six non-negotiable axioms:
1. **The Spatial Instrument Canvas is Paramount:** The map occupies 60–70% of the active viewport. It is not an illustrative background or a card thumbnail; it is an active computational stage.
2. **Decisions Precede Formulations:** Non-technical commissioners see the intervention (2,695 trees), the cost (₹9.99M), and the target zones (28 cells) immediately. Mathematical formulas ($F\text{-}19$ to $F\text{-}28$) and raw band values reside in Level 4 disclosure drawers.
3. **Institutional Editorial Gravitas:** Zero cartoonish widgets, zero bouncing buttons, zero 3D glowing globes, zero neon gradients. Layouts utilize classical editorial rhythm, generous negative space, and hairline borders.
4. **Epistemological Honesty:** `MODELED` ex-ante projections and `VERIFIED` empirical observations use distinct structural treatments, contrasting typography, and unambiguous labels.
5. **No Client-Side Recalculation:** The UI displays precomputed canonical query projections from the Phase 2B API. It never executes linear solvers or spatial convolutions in JavaScript.
6. **Accessible Tabular Equivalence:** Pressing `Alt+T` instantly replaces the WebGL spatial canvas with a semantic, WCAG 2.1 AA/AAA compliant tabular ledger.

---

## 4. VISUAL DIRECTION

CLIMORA synthesizes the calm editorial restraint of **Vayu** (Minimal Creative) with the cryptographic rigor of **Proofmode**:

```
+----------------------------------------------------------------------------------------------------+
|                                    THE CLIMORA AESTHETIC SPECTRUM                                  |
|                                                                                                    |
|    ENVIRONMENTAL SURFACES               ARCHIVAL INK                   CLIMATE DOMAINS             |
|    • Deep Basalt (#0C0E0D)             • Stark Charcoal (#141715)      • Terracotta (Thermal LST)  |
|    • Calcified Sandstone (#F4F4F0)      • Muted Slate (#71756F)         • Botanical Sage (Canopy)   |
|    • Paper Mineral (#EBECE7)            • Pure White (#FDFDFD)          • Slate Cyan (Hydrology)    |
|                                                                        • Acid Lime (0.5% Accent)   |
+----------------------------------------------------------------------------------------------------+
```

- **Surfaces:** Tactile, mineral, and calm. Evoking archival printing paper and deep basalt volcanic bedrock.
- **Borders:** Ultra-fine 1px hairlines with 8–12% opacity. Containers do not use heavy shadows.
- **Rhythm:** Strict 8pt vertical grid increments (8px, 16px, 24px, 32px, 48px, 64px, 96px).

---

## 5. TYPOGRAPHY EXPLORATION & RATIFICATION

CLIMORA operates on a **tripartite typographical system**:

```
+----------------------------------------------------------------------------------------------------+
|                                    TYPOGRAPHY DIRECTION COMPARISON                                 |
+------------------------------------+---------------------------------------------------------------+
| EVALUATION CRITERION               | DIRECTION A: Newsreader + Geist  | DIRECTION B: Instrument + Inter|
+------------------------------------+----------------------------------+----------------------------+
| Editorial Authority & Seriousness  | VERY HIGH (Classical, literary)  | HIGH (High-fashion, sharp) |
| UI Optical Clarity (11px - 14px)   | EXCEPTIONAL (Geist open counter) | HIGH (Inter Tight compact) |
| Monospace Tabular Figure Alignment | PERFECT (Geist Mono tnum)        | EXCELLENT (JetBrains Mono) |
| Map Instrument Coexistence         | EXCELLENT (Calm, non-distracting)| GOOD (Slightly stylistic)  |
| Executive Briefing Legibility      | OUTSTANDING (Institutional paper)| STRONG                     |
+------------------------------------+----------------------------------+----------------------------+
```

### Typographic Decision:
> **RATIFIED DIRECTION A:**  
> - **Editorial Display:** `Newsreader` (Variable serif, optical sizes 16pt–72pt). Used for hero headlines, thematic section titles, and narrative thesis statements.  
> - **Functional UI Grotesk:** `Geist Sans` (High x-height, neutral geometric grotesque). Used for navigation, body text, form controls, and labels.  
> - **Technical Monospace:** `Geist Mono` with tabular figure enablement (`font-variant-numeric: tabular-nums`). Used for all currency values, coordinates, H3 indices, temperatures, dates, and SHA-256 digests.

### Typographic Scale Tokens:
| Level | Font Family | Size | Weight | Line Height | Tracking |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `display-hero` | Newsreader | 56px | Regular | 1.05 | -0.02em |
| `display-section` | Newsreader | 36px | Regular | 1.15 | -0.01em |
| `ui-h1` | Geist Sans | 22px | SemiBold | 1.25 | -0.01em |
| `ui-h2` | Geist Sans | 16px | Medium | 1.35 | 0.00em |
| `ui-body` | Geist Sans | 13px | Regular | 1.55 | 0.00em |
| `ui-micro` | Geist Sans | 11px | Medium | 1.40 | +0.02em |
| `mono-data` | Geist Mono | 13px | Regular | 1.40 | -0.01em (tnum) |
| `mono-tag` | Geist Mono | 10px | Medium | 1.00 | +0.06em (tnum, uppercase) |

---

## 6. COLOR SYSTEM & SEMANTIC TOKENS

### 6.1 Surface & Ink Tokens
```css
/* Surface Tokens */
--surface-ground-dark:    #0C0E0D; /* Deep Basalt (Default Spatial Canvas) */
--surface-panel-dark:     #141715; /* Dark Volcanic Shale (Drawers / Overlays) */
--surface-ground-light:   #F5F5F1; /* Calcified Sandstone (Public Monograph) */
--surface-panel-light:    #EBECE7; /* Bleached Mineral Paper */

/* Ink Tokens */
--ink-primary-dark:       #F2F4EF; /* Crisp Off-White */
--ink-secondary-dark:     #8E928A; /* Muted Basalt Stone */
--ink-tertiary-dark:      #52564F; /* Deep Charcoal Shadow */
--ink-primary-light:      #121413; /* Archival Carbon Ink */
--ink-secondary-light:    #5B5E57; /* Muted Graphite */
--ink-tertiary-light:     #989C93; /* Pale Slate */

/* Structural Borders */
--border-hairline-dark:   rgba(242, 244, 239, 0.10);
--border-hairline-light:  rgba(18, 20, 19, 0.10);
```

### 6.2 Truth-Layer Semantic Tokens
```css
/* OBSERVED: Archival Neutral Stone */
--truth-observed-bg:      rgba(142, 146, 138, 0.12);
--truth-observed-border:  rgba(142, 146, 138, 0.30);
--truth-observed-ink:     #D8DCD3;

/* DERIVED: Cool Analytical Slate */
--truth-derived-bg:       rgba(94, 129, 153, 0.12);
--truth-derived-border:   rgba(94, 129, 153, 0.35);
--truth-derived-ink:      #A3C6DC;

/* MODELED: Warm Prospective Amber / Ochre */
--truth-modeled-bg:       rgba(217, 155, 38, 0.12);
--truth-modeled-border:   rgba(217, 155, 38, 0.40);
--truth-modeled-ink:      #F5C563;

/* VERIFIED: Audited High-Contrast Emerald */
--truth-verified-bg:      rgba(38, 166, 91, 0.15);
--truth-verified-border:  rgba(38, 166, 91, 0.50);
--truth-verified-ink:     #52D68A;

/* FOCAL ACCENT: Controlled Acid Lime (< 0.5% screen area) */
--accent-focal-cursor:    #C8FF3B;
```

---

## 7. ROUTE 1 WIREFRAMES — EDITORIAL PUBLIC MONOGRAPH (`/`)

The public landing page is an **editorial scientific monograph**. It frames the urban climate crisis and presents the Pune demonstration as a bankable municipal opportunity.

```
+----------------------------------------------------------------------------------------------------+
| TOP PERSISTENT NAV:                                                                                |
| CLIMORA                       [ OVERVIEW ]   [ EXPLORE ]   [ PROJECT ]   [ PUNE: 2025 ] |
+----------------------------------------------------------------------------------------------------+
| SECTION 1: EDITORIAL HERO                                                                          |
|                                                                                                    |
|    TURNING PLANETARY OBSERVATIONS INTO                                                             |
|    FUNDABLE URBAN INTERVENTIONS.                                                                   |
|                                                                                                    |
|    A mathematical decision-support instrument for municipal heat resilience in Pune, India.        |
|                                                                                                    |
|    [ EXPLORE PUNE SPATIAL EVIDENCE  -> ]               [ VIEW CANONICAL PROJECT PROPOSAL ]         |
|                                                                                                    |
|    --------------------------------------------------------------------------------------------    |
|    LAT: 18.5204° N  |  LON: 73.8567° E  |  H3 RESOLUTION: 9  |  BASE SENSOR: LANDSAT-8/9 TIRS       |
+----------------------------------------------------------------------------------------------------+
| SECTION 2: THE METROPOLITAN CRISIS (3-Column Asymmetric Grid)                                      |
|                                                                                                    |
|   01 / THE THERMAL REALITY         02 / THE HUMAN EXPOSURE          03 / THE CAPITAL IMPASSE       |
|   ─────────────────────────        ─────────────────────────        ─────────────────────────      |
|   46.36°C                          118,941                          ₹10,000,000                    |
|   5-Yr Peak-Summer LST Baseline    Citizens in Critical Corridors   Municipal Resilience Envelope  |
|                                                                                                    |
|   Multi-year satellite thermal     High population density in       Municipal adaptation budgets   |
|   observations confirm severe,     eastern industrial settlements   are frequently misallocated    |
|   persistent surface overheating   collides with an acute street    due to lack of spatial         |
|   across asphalt corridors.        canopy deficit (NDVI < 0.10).    optimization and MRV audits.   |
|                                                                                                    |
|   [OBSERVED | Landsat 2021-2025]   [OBSERVED | WorldPop 2020]       [GOVERNED | Municipal Grant]   |
+----------------------------------------------------------------------------------------------------+
| SECTION 3: THE DECISION PROCESS (Mathematical Lineage Diagram)                                     |
|                                                                                                    |
|   [ SATELLITE TIRS ] ──► [ H3 RES-9 MESH ] ──► [ RISK SURFACE ] ──► [ MILP SOLVER ] ──► [ TENDER ]|
|   Landsat 8/9 C2 L2      3,181 Hexagons        F-22 Power-Law       HiGHS Algorithm     2,695 Trees|
|   30m Thermal Radiance   9.86 Hectares/Cell    H · E · V Axiom      ₹10M Budget Ceiling ₹9.99M CapEx|
+----------------------------------------------------------------------------------------------------+
| SECTION 4: THE CANONICAL PUNE DEMONSTRATION BRIEFING                                               |
|                                                                                                    |
|   PROJECT: PROJ-PUNE-2025-BA225D6A                                                                 |
|   Pune Urban Heat Island Mitigation & Roadside Canopy Initiative                                   |
|                                                                                                    |
|   • TARGET GEOGRAPHY:     28 Prioritized H3 Cells (Hadapsar Corridor)                              |
|   • PHYSICAL SCOPE:       2,695 Street Canopy Trees (10m spacing)                                  |
|   • MODELED CAPEX:        ₹9,992,500 INR                                                           |
|   • TREASURY SLACK:       ₹7,500 INR (Retained in Municipal Fund)                                  |
|   • LIFECYCLE STATUS:     PROPOSED (Awaiting Municipal Sanction)                                   |
|                                                                                                    |
|   [ OPEN COMPLETE PROJECT SUITE  -> ]                                                              |
+----------------------------------------------------------------------------------------------------+
| SECTION 5: INSTITUTIONAL FOOTER & TELEMETRY                                                        |
|                                                                                                    |
|   CLIMORA SPATIAL INTELLIGENCE PLATFORM                                                            |
|   Source Data: USGS Landsat Collection 2 Level-2 | ESA Sentinel-2 MSI | WorldPop 2020 | OSM        |
|   Analytical Topology: Uber H3 DGGS (EPSG:4326) | CRS: UTM Zone 43N (EPSG:32643)                   |
|   Parquet Lake Integrity: 5 of 5 SHA-256 Hashes Verified | API Version: 1.1.0 (Phase 2B Hardened) |
|   Legal Disclaimer: Modeled microclimatic scores represent optimization objectives under F-24.     |
+----------------------------------------------------------------------------------------------------+
```

---

## 8. ROUTE 2 WIREFRAMES — PUNE SPATIAL INSTRUMENT (`/explore/pune`)

The spatial instrument is the primary analytical environment. The map canvas dominates the viewport, supported by floating telemetry chips and a 420px contextual inspection drawer.

### 8.1 Viewport Ratio Comparison: 70/30 vs 60/40
- **Variant A (60% Map / 40% Drawer):** Tested on standard laptop screens (1366 $\times$ 768). Provides superior reading comfort for 5 levels of disclosure, but compresses the spatial periphery.
- **Variant B (70% Map / 30% Drawer):** Tested on standard 1080p and 1440p displays (1920 $\times$ 1080 / 1440 $\times$ 900). Delivers an exceptional, immersive spatial instrument feel.
- **Ratified Layout Model:** **Responsive Hybrid.** Defaults to 70% Map / 30% Drawer (fixed 420px width drawer on wide displays). On narrower viewports ($\le 1366\text{px}$), the drawer overlays the right rail with an understated 15% map dimming shader, retaining maximum spatial orientation.

### 8.2 Spatial Instrument Desktop Wireframe (Full Viewport)
```
+----------------------------------------------------------------------------------------------------+
| TOP HUD: CLIMORA   [ OVERVIEW ]   [ EXPLORE: PUNE ]   [ PROJECT ]             [ H3 RES-9 | AOI: 4194 ]|
+-------------------------------------------------------------------------------+--------------------+
|                                                                               | VIEW SELECTOR:     |
|                                                                               | [•] THERMAL LST    |
|                                                                               | [ ] EXPOSURE       |
|                                                                               | [ ] RISK SURFACE   |
|                                                                               | [ ] LISA HOTSPOTS  |
|                                                                               +--------------------+
|                                                                               | ACTIVE CLUSTER:    |
|                      FULL-SCREEN SPATIAL CANVAS                               | Hadapsar Corridor  |
|                      (Interactive Uber H3 Res 9 Mesh)                         | 28 Treated Cells   |
|                                                                               | Mean LST: 46.69°C  |
|                                                                               | [View Project ->]  |
|                                                                               +--------------------+
|                                                                               | CELL INSPECTOR     |
|                       [ 28 CANONICAL CELLS HIGHLIGHTED ]                      | DRAWER             |
|                                                                               | (Slides out from   |
|                                                                               |  right on click)   |
|                                                                               |                    |
|                                                                               |                    |
|                                                                               | Width: 420px       |
|                                                                               |                    |
+-------------------------------------------------------------------------------+--------------------+
| FOOTER TELEMETRY HUD:                                                                              |
| [ METRIC: LST_2025 ]  [ SENSOR: LANDSAT-8 TIRS ]  [ DOY: 109 ]  [ CLOUD: 0.0% ]  [ ALT+T: TABLE ]  |
+----------------------------------------------------------------------------------------------------+
```

### 8.3 Contextual Cell Inspector Drawer (420px Width)
The drawer slides in when a hexagon is selected. It enforces a strict **eye-movement hierarchy**:
$$\text{WHAT IS THIS?} \longrightarrow \text{WHY DOES IT MATTER?} \longrightarrow \text{SUPPORTING EVIDENCE} \longrightarrow \text{PROPOSED ACTION} \longrightarrow \text{HOW DO WE KNOW?}$$

```
+---------------------------------------------------------------------------+
| CONTEXTUAL CELL INSPECTOR DRAWER                          [ ESC / CLOSE ] |
+---------------------------------------------------------------------------+
| ZONE 1: CELL IDENTITY & MUNICIPAL CONTEXT                                 |
| H3 CELL ID: 89608850003ffff                                               |
| Primary Ward: 14 - Hadapsar Industrial Belt (Contextual Metadata Only)    |
| Surface Area: 0.0986 km² (9.86 Hectares) | Valid Pixel Fraction: 100%     |
+---------------------------------------------------------------------------+
| ZONE 2: EXECUTIVE DECISION (Level 1 Disclosure)                           |
| PRIORITY STATUS: CANONICAL TREATED FOOTPRINT (Cell 1 of 28)               |
| Proposed Action: Deploy 110 Street Shade Trees along public right-of-way  |
| Modeled Cost:    ₹405,000 INR (Direct: ₹385,000 | Mobilization: ₹20,000)  |
| Truth Layer:     [ MODELED | F-24 Canonical Optimization Allocation ]     |
+---------------------------------------------------------------------------+
| ZONE 3: OBSERVED & DERIVED EVIDENCE (Level 2 Disclosure)                  |
|                                                                           |
| • Observed Surface Temp: 46.69°C     [ OBSERVED | Landsat 8 DOY 109 ]     |
| • 5-Yr Baseline Mean:    46.36°C     [ DERIVED  | 5-Yr Pre-Monsoon Mean ] |
| • Current-State Anomaly: +0.33°C     [ DERIVED  | F-15 Thermal Anomaly ]  |
| • Canopy Cover (NDVI):   0.082       [ OBSERVED | Sentinel-2 MSI (Deficit)|
| • Built-Up Index (NDBI): 0.241       [ OBSERVED | Sentinel-2 MSI (Dense) ]|
+---------------------------------------------------------------------------+
| ZONE 4: RISK & POPULATION EXPOSURE (Level 3 Disclosure)                   |
|                                                                           |
| • In-Scope Population:   4,281 residents   [ OBSERVED | WorldPop 2020 ]   |
| • Road Network Length:   1,840 meters      [ OBSERVED | OpenStreetMap ]   |
| • Spatial Cluster:       HIGH-HIGH HOTSPOT [ DERIVED  | LISA Moran's I ]  |
| • Climate Risk Score:    0.2345            [ MODELED  | F-22 Formulation ]|
+---------------------------------------------------------------------------+
| ZONE 5: INTERVENTION BLUEPRINT (Level 4 Disclosure)                       |
|                                                                           |
| • Intervention Code:     street_tree_shade                                |
| • Recommended Species:   Azadirachta indica (Neem), Pongamia pinnata      |
| • Planned Spacing:       15.0m interval roadside rights-of-way            |
| • Modeled Cell Cooling:  0.078°C           [ MODELED  | F-25.1 Scenario ] |
+---------------------------------------------------------------------------+
| ZONE 6: SCIENTIFIC LINEAGE & PROVENANCE (Level 5 Disclosure)              |
|                                                                           |
| • Source Parquet:  canonical_feature_matrix.parquet                       |
| • Digest SHA-256:  76f344b147b349f3887259f64c97923414c74fd9...           |
| • Solver Lineage:  OPT-PUNE-2025-SCENARIO-BA225D6A (HiGHS MILP, F-24)     |
|                                                                           |
| [ VIEW DETAILED CELL MATHEMATICAL PROVENANCE -> ]                         |
+---------------------------------------------------------------------------+
```

---

## 9. ROUTE 3 WIREFRAMES — CANONICAL PROJECT DECISION SUITE (`/projects/:id`)

The demonstration project representation ([`PROJ-PUNE-2025-BA225D6A`](file:///c:/Users/lenovo/climora/data/processed/projects/project_pune_2025_tree_shade_10m.json)) organizes the 13 canonical backend sections into six editorial tabs.

```
+----------------------------------------------------------------------------------------------------+
| PROJECT BANNER: PROJ-PUNE-2025-BA225D6A                                                            |
| Pune Urban Heat Island Mitigation & Street Canopy Initiative                                       |
| Beneficiary: Pune Municipal Corporation (Tree Authority) | Price Basis: 2025 INR                   |
| Lifecycle State: [ PROPOSED | Awaiting Standing Committee Sanction ]                               |
+----------------------------------------------------------------------------------------------------+
| TAB CONTROLLER:                                                                                    |
| [•] 01 OVERVIEW  [ ] 02 ALLOCATION  [ ] 03 BASELINE  [ ] 04 BUDGET  [ ] 05 MRV  [ ] 06 PROVENANCE     |
+----------------------------------------------------------------------------------------------------+
```

### 9.1 View 01: Executive Overview (The Decision Briefing)
Max six primary metrics. **Capital Required dominates** with large-scale typography.

```
+----------------------------------------------------------------------------------------------------+
| 01 / EXECUTIVE DECISION BRIEFING                                                                   |
|                                                                                                    |
|   PRIMARY FINANCIAL COMMITMENT                                                                     |
|   ₹9,992,500 INR                                                                                   |
|   Total Modeled Capital Expenditure under Municipal Optimization                                   |
|   [ MODELED | F-24 Mixed-Integer Linear Program Allocation ]                                       |
|                                                                                                    |
|   ----------------------------------------------------------------------------------------------   |
|   SECONDARY EXECUTIVE METRICS (Structured Hierarchy)                                               |
|                                                                                                    |
|   MUNICIPAL BUDGET CEILING     UNALLOCATED BUDGET SLACK     TARGET PHYSICAL SCOPE                  |
|   ₹10,000,000 INR              ₹7,500 INR                   2,695 Street Trees                     |
|   Special Resilience Grant     Retained in Municipal Fund   Across 28 Prioritized Cells            |
|   [ GOVERNED | Statutory Cap ] [ GOVERNED | Treasury Slack] [ MODELED | F-24 Allocation ]          |
|                                                                                                    |
|   PROTECTED POPULATION         CANONICAL OBJECTIVE SCORE    PROJECT BENEFICIARY                    |
|   118,941 residents            0.106048                     Pune Municipal Corporation             |
|   Exact: 118,941.21            Risk-Objective Reduction     Tree Authority & Road Dept             |
|   [ OBSERVED | WorldPop 2020 ] [ MODELED | F-24 Formulation][ GOVERNED | Statutory Agency ]         |
|                                                                                                    |
|   ----------------------------------------------------------------------------------------------   |
|   DECISION ACTION MODULE:                                                                          |
|   Municipal Standing Committee Administrative Sanction:                                            |
|   Sanction ID: [ PMC-RESILIENCE-2025-084           ] Approved Budget: [ ₹10,000,000              ] |
|   Notes:       [ Approved under FY25-26 Special Urban Cooling Grant Envelope                    ] |
|                                                                                                    |
|   [ SANCTION PROJECT & ISSUE TENDER -> (POST /projects/{id}/transition) ]                          |
+----------------------------------------------------------------------------------------------------+
```

### 9.2 View 02: Allocation Blueprint (Interactive 28-Cell Mesh)
Combines the map and the paginated allocation ledger. Enforces **Allocation Immutability**.

```
+----------------------------------------------------------------------------------------------------+
| 02 / SPATIAL ALLOCATION BLUEPRINT                                                                  |
| Total Footprint: 28 Cells | Planned Trees: 2,695 | Direct Unit Cost: ₹3,500 | Mobilization: ₹20k   |
+--------------------------------------------------+-------------------------------------------------+
| MAP VIEWPORT (45% Width):                        | ALLOCATION LEDGER TABLE (55% Width):            |
|                                                  |                                                 |
|                                                  | CELL ID         WARD    TREES   CAPEX     STATUS|
|                                                  | ----------------------------------------------- |
|   [ 28 TREATED CELLS RENDERED IN GREEN ]         | 89608850003ffff Ward 14 110     ₹405,000  LOCKED|
|                                                  | 89608850007ffff Ward 14 105     ₹387,500  LOCKED|
|   • Selected row highlights hexagon on map       | 89608850017ffff Ward 14 95      ₹352,500  LOCKED|
|   • Hovering hexagon highlights table row        | 896088500b3ffff Ward 22 100     ₹370,000  LOCKED|
|                                                  | ... [Showing 1-10 of 28 rows | Page 1 of 3]     |
|                                                  | ----------------------------------------------- |
|                                                  | IMMUTABILITY GOVERNANCE NOTICE:                 |
|                                                  | [LOCKED] Canonical optimization is immutable.   |
|                                                  | Direct edits rejected with HTTP 405.            |
|                                                  |                                                 |
|                                                  | [ PROPOSE AUDITABLE REVISION (POST /revisions) ]|
+--------------------------------------------------+-------------------------------------------------+
```

### 9.3 View 03: Baseline Evidence View
Displays observed thermal, biophysical, and exposure metrics across the 28 cells.

```
+----------------------------------------------------------------------------------------------------+
| 03 / MULTI-YEAR BASELINE EVIDENCE                                                                  |
| Evidence Source: Landsat 8/9 C2 L2 (2021-2025) & Sentinel-2 MSI (2025) | 100% Valid QA Pixels     |
+----------------------------------------------------------------------------------------------------+
| CELL INDEX       OBSERVED LST    BASELINE MEAN   THERMAL ANOMALY   NDVI CANOPY   NDBI BUILT-UP     |
+----------------------------------------------------------------------------------------------------+
| 89608850003ffff  46.69°C         46.36°C         +0.33°C           0.082         0.241             |
| 89608850007ffff  46.82°C         46.41°C         +0.41°C           0.076         0.258             |
| 89608850017ffff  46.51°C         46.20°C         +0.31°C           0.091         0.230             |
| 896088500b3ffff  46.74°C         46.39°C         +0.35°C           0.084         0.247             |
| ...              ...             ...             ...               ...           ...               |
+----------------------------------------------------------------------------------------------------+
| TRUTH METADATA:                                                                                    |
| [ OBSERVED: Landsat-8 TIRS DOY 109 ]  [ DERIVED: 5-Yr Pre-Monsoon Mean ]  [ OBSERVED: Sentinel-2 ]|
+----------------------------------------------------------------------------------------------------+
```

### 9.4 View 04: Transparent Capital & Budget View
Institutional investment memorandum layout. Compares optimized allocation against ad-hoc spending.

```
+----------------------------------------------------------------------------------------------------+
| 04 / CAPITAL BREAKDOWN & BUDGET TRANSPARENCY                                                       |
+----------------------------------------------------------------------------------------------------+
| BUDGET ENVELOPE (STATUTORY CEILING)                                                                |
| ₹10,000,000.00 INR                                                                                 |
|                                                                                                    |
| ALLOCATED CAPITAL (TOTAL MODELED CAPEX)          UNALLOCATED BUDGET SLACK (TREASURY SURPLUS)       |
| ₹9,992,500.00 INR (99.93% Capital Efficiency)    ₹7,500.00 INR (0.07% Retained Surplus)           |
+----------------------------------------------------------------------------------------------------+
| TRANSPARENT COST COMPONENTS:                                                                       |
| 1. DIRECT PHYSICAL INTERVENTION PROCUREMENT                                                        |
|    • Unit Description: Indigenous 2m sapling + galvanized tree guard + soil conditioning          |
|    • Quantity: 2,695 units  |  Unit Rate: ₹3,500 / tree                                            |
|    • Subtotal: ₹9,432,500.00 INR (94.4% of total CapEx)                                            |
|                                                                                                    |
| 2. LOCAL CELL MOBILIZATION & UTILITY CLEARANCE                                                     |
|    • Unit Description: Underground utility clearance, nursery transit, staging per H3 hexagon     |
|    • Quantity: 28 cells  |  Unit Rate: ₹20,000 / cell                                              |
|    • Subtotal: ₹560,000.00 INR (5.6% of total CapEx)                                               |
|                                                                                                    |
| TOTAL MODELED PROJECT COMMITMENT: ₹9,992,500.00 INR                                                |
+----------------------------------------------------------------------------------------------------+
```

### 9.5 View 05: Physical Implementation & MRV Verification Gateway
The post-funding operational lifecycle. Shows physical deployment tracking while keeping verified impact locked.

```
+----------------------------------------------------------------------------------------------------+
| 05 / PHYSICAL IMPLEMENTATION & MRV VERIFICATION                                                    |
+----------------------------------------------------------------------------------------------------+
| LIFECYCLE STATE PROGRESSION:                                                                       |
| [✓] PROPOSED ──► [✓] FUNDED ──► [•] IMPLEMENTING ──► [ ] IMPLEMENTED ──► [ ] MONITORING ──► [🔒] VERIFIED|
+----------------------------------------------------------------------------------------------------+
| CONTRACTOR DEPLOYMENT LEDGER:                                                                      |
|                                                                                                    |
| EVENT ID       CELL ID         PLANNED   IMPLEMENTED   DEVIATION (F-27.2)   DATE        STATUS     |
| -------------------------------------------------------------------------------------------------- |
| EVT-IMPL-01    89608850003ffff 110       110           0.00% (On-Track)     2026-04-15  SIGNED-OFF |
| EVT-IMPL-02    89608850007ffff 105       105           0.00% (On-Track)     2026-04-18  SIGNED-OFF |
|                                                                                                    |
| [ LOG CONTRACTOR DEPLOYMENT EVENT -> (POST /projects/{id}/implementation-events) ]                 |
+----------------------------------------------------------------------------------------------------+
| THIRD-PARTY MRV VERIFICATION GATEWAY (ISO 14064-2 & F-26 ALIGNED):                                 |
|                                                                                                    |
| VERIFICATION STATUS: [ LOCKED | UNOBSERVED / NOT YET VERIFIED ]                                    |
| Difference-in-Differences (DID) Execution Status: [ PLANNED / NOT_YET_EXECUTABLE ]                 |
| Empirical Cooling Measured: [ null / Awaiting post-implementation Landsat overpass ]               |
|                                                                                                    |
| GATE CONDITIONS REQUIRED FOR VERIFICATION:                                                         |
| [✓] Gate 1: 100% of 2,695 physical trees planted with contractor evidence URIs                     |
| [ ] Gate 2: Minimum 24-month sapling canopy establishment period elapsed                          |
| [ ] Gate 3: Valid Landsat-8/9 thermal overpass acquired during target DOY 95-115 window            |
| [ ] Gate 4: Zero cloud/shadow contamination over AOI (QA_PIXEL passed = 100%)                      |
| [ ] Gate 5: Non-synthetic data audit certified by accredited independent third-party auditor       |
|                                                                                                    |
| [ CERTIFY VERIFICATION EVENT (Disabled - Gate Conditions Pending) ]                                |
+----------------------------------------------------------------------------------------------------+
```

### 9.6 View 06: Scientific Provenance & Cryptographic Traceability
Forensic audit trail providing complete reproducibility.

```
+----------------------------------------------------------------------------------------------------+
| 06 / SCIENTIFIC LINEAGE & CRYPTOGRAPHIC AUDIT TRAIL                                                |
+----------------------------------------------------------------------------------------------------+
| OPTIMIZATION RUN TRACEABILITY:                                                                     |
| • Run Identifier:        OPT-PUNE-2025-SCENARIO-BA225D6A                                           |
| • Mathematical Engine:   HiGHS Mixed-Integer Linear Programming (scipy.optimize.milp)               |
| • Optimization Status:   OPTIMAL (Global optimum satisfied under constraints)                     |
| • Solver Runtime:        70.13 seconds                                                             |
| • Candidate Evaluated:   7,115 cell-intervention candidate pairs                                   |
| • Formulation Reference: F-24.1 through F-24.6 (CLIMORA Mathematical Register v1.0.0)             |
+----------------------------------------------------------------------------------------------------+
| CANONICAL PARQUET ARTIFACT INTEGRITY (SHA-256):                                                    |
|                                                                                                    |
| ARTIFACT NAME              PATH                                         SHA-256 CHECKSUM    STATUS |
| -------------------------------------------------------------------------------------------------- |
| Feature Matrix             data/processed/canonical_feature_matrix.pq   76f344b147b349f...  VERIFIED|
| HEV Components             data/processed/hev/canonical_hev_comp.pq     1970c2da7863f57...  VERIFIED|
| Risk Surface               data/processed/risk/canonical_risk_surf.pq   e2d5df6c7a0a958...  VERIFIED|
| Spatial Autocorrelation    data/processed/risk/canonical_spatial_ac.pq  47cc7025ef150ae...  VERIFIED|
| Optimization Allocation    data/processed/opt/canonical_opt_alloc.pq    2519473a32a2b4a...  VERIFIED|
+----------------------------------------------------------------------------------------------------+
```

---

## 10. TRUTH-LAYER VISUAL SYSTEM & SPECIFICATION

A central failure mode of environmental software is conflating simulations with reality. CLIMORA solves this by establishing **unmistakable visual divergence**:

```
+----------------------------------------------------------------------------------------------------+
|                                  TRUTH-LAYER COMPONENT SPECIFICATION                               |
+---------------+---------------------+--------------------+--------------------+--------------------+
| DIMENSION     | OBSERVED            | DERIVED            | MODELED            | VERIFIED           |
+---------------+---------------------+--------------------+--------------------+--------------------+
| Definition    | Empirical satellite | Multi-year or      | Ex-ante mathematical| Post-deployment    |
|               | or sensor measurement| spatial aggregation| simulation/scenario| certified audit    |
| Surface Tint  | Stone Neutral (10%) | Slate Blue (12%)   | Ochre Amber (12%)  | Deep Emerald (15%) |
| Border Stroke | 1px solid stone     | 1px solid slate    | 1px dashed ochre   | 1px solid emerald  |
| Text Glyphs   | Monospace uppercase | Formula code token | Math sigma glyph Σ | Shield/Check emblem|
| Disclaimers   | Sensor platform &   | Formula & temporal | "Scenario model;   | "Certified empirical|
|               | acquisition DOY     | window specified   | not verified."     | overpass audit."   |
| Current State | ACTIVE & VALID      | ACTIVE & VALID     | ACTIVE & RATIFIED  | LOCKED / NULL      |
+---------------+---------------------+--------------------+--------------------+--------------------+
```

### Visual Rendering of Truth Badges:
```text
[ OBSERVED | Landsat 8 TIRS DOY 109 ]     ──► Stone pill with sensor telemetry
[ DERIVED  | 5-Yr Mean Baseline F-14 ]    ──► Slate pill with formula token
[ MODELED  | F-24 MILP Allocation ]       ──► Dashed amber pill with sigma prefix Σ
[ VERIFIED | LOCKED: UNOBSERVED ]         ──► Quarantined slate pill with padlock 🔒
```

---

## 11. UI STATE SYSTEM (12 WIREFRAME STATES)

```
+----------------------------------------------------------------------------------------------------+
| 1. DEFAULT STATE: Clean, high-contrast presentation of calibrated baseline data and canonical H3.  |
| 2. LOADING STATE: 1px hairline shimmer skeleton blocks; map displays pulsing coordinate crosshair. |
| 3. EMPTY STATE: Explanatory card: "No contractor events logged yet. Groundbreaking scheduled Q4."  |
| 4. ERROR STATE: Standardized error banner parsing error.code, message, and correlation_id.         |
| 5. PARTIAL DATA: Hatched pattern over hexagons with < 70% clear pixels (INSUFFICIENT_COVERAGE).   |
| 6. NO SELECTION: Camera frames 28 cells; right drawer shows portfolio-level municipal totals.     |
| 7. CELL SELECTED: Active hexagon receives 1.5px acid lime stroke; drawer opens Zone 1-6 metrics.  |
| 8. DRAWER OPEN: Spatial canvas shifts or dims 10%, keeping urban landmark orientation intact.      |
| 9. MODAL OPEN: Centered dialog with backdrop-blur for cryptographic provenance inspection.         |
| 10. IMMUTABLE GUARD: Hovering locked fields reveals padlock icon: "Canonical allocation immutable."|
| 11. VERIFICATION BLOCKED: Grayed button with amber safety pill: "Requires 100% planting & overpass.|
| 12. SYNTHETIC QUARANTINED: Watermarked diagonal banner: "DEMO FIXTURE — NOT PRODUCTION VERIFIED".  |
+----------------------------------------------------------------------------------------------------+
```

---

## 12. RESPONSIVE BEHAVIOR (DESKTOP, LAPTOP, TABLET, MOBILE)

1. **Desktop Large (1440 $\times$ 900 & 1920 $\times$ 1080):** Full 12-column grid. Map occupies 70% canvas width; contextual cell drawer occupies 30% (fixed 420px).
2. **Laptop Standard (1366 $\times$ 768):** Map occupies 100% width; inspector drawer slides in as an overlay from the right, dimming the map by 15%.
3. **Tablet Landscape (1024 $\times$ 768):** Top nav collapses to brand + status chip. Inspector drawer becomes a half-screen sheet (50% split).
4. **Mobile (390 $\times$ 844):** The map remains full-screen. Upon cell selection, the inspector drawer becomes a **Draggable Bottom Sheet**:
   - *Collapsed Position (96px height):* Shows Level 1 summary (Cell ID, Ward, Tree Count, CapEx).
   - *Expanded Position (85% height):* Full scrollable disclosure of Level 2–5 evidence and provenance.

---

## 13. ACCESSIBILITY & USABLE INCLUSION SPECIFICATION

- **Keyboard Navigation:** Full tab order through navigation, map view switches, and allocation table rows.
- **Accessible Table Alternative (`Alt+T`):** Pressing `Alt+T` on `/explore/pune` immediately swaps the map canvas with a semantic HTML5 data table sorting all 3,181 cells (or the 28 treated cells) by temperature, exposure, and cost.
- **Colorblind-Safe Palettes:** The terracotta heat ramp and forest canopy ramp have been tested under Deuteranopia and Protanopia simulations. Quantitative values are always backed by tabular text.
- **Screen Reader Live Regions:** Dynamic cell selection triggers an `aria-live="polite"` announcement: *"Hexagon 89608850003ffff selected. In Hadapsar corridor. 110 street trees allocated. Modeled cost ₹405,000 INR."*

---

## 14. MICROINTERACTION INTENT SPECIFICATIONS

```
+----------------------------------------------------------------------------------------------------+
| INTERACTION        | TRIGGER            | BEFORE -> TRANSITION -> AFTER        | CAUSAL INTENT     |
+--------------------+--------------------+--------------------------------------+-------------------+
| 1. Map Camera Move | Click treated cell | City view -> 900ms cubic-bezier ->   | Contextual focus  |
|                    | or project CTA     | Smoothly frames 28-cell boundary     | without spatial   |
|                    |                    |                                      | disorientation.   |
| 2. Cell Inspection | Click H3 hexagon   | Default stroke -> 1.5px acid lime -> | Connects spatial  |
|                    | on map mesh        | Right drawer slides in over 350ms    | click to evidence.|
| 3. Project Assembly| Click "Assemble    | Exploratory heatmap -> 700ms fade -> | Transforms raw    |
|                    | Fundable Project"  | Canonical proposal prospectus        | evidence into a   |
|                    |                    | materializes with ₹10M budget card   | bankable project. |
| 4. State Sanction  | Submit sanction ID | PROPOSED (Stone pill) -> 300ms ->    | Confirms legal    |
|                    | & budget form      | FUNDED (Amber active state pill)     | municipal action. |
| 5. Reduced Motion  | prefers-reduced-   | All transitions switch from smooth   | Full WCAG 2.1 AA  |
|                    | motion: reduce     | bezier curves to instantaneous cuts. | motion compliance.|
+----------------------------------------------------------------------------------------------------+
```

---

## 15. HACKATHON DEMONSTRATION FLOW (3–5 MINUTES)

The wireframes are optimized to guide judges through the canonical 11-beat narrative:
1. **0:00 – 0:30 (Beat 1 - Landing):** Monograph headline: *"Turning Planetary Observations into Fundable Urban Interventions."* Establish the ₹10M municipal dilemma.
2. **0:30 – 1:00 (Beat 2 - Thermal Baseline):** Enter `/explore/pune`. Show 5-year Landsat baseline surface (46.36°C mean).
3. **1:00 – 1:30 (Beat 3 - Human Exposure):** Toggle Exposure overlay. Show where extreme heat strikes dense settlements without tree shade.
4. **1:30 – 2:00 (Beat 4 - Hotspots):** Toggle LISA spatial autocorrelation. Reveal Hadapsar High-High risk cluster ($p < 0.01$).
5. **2:00 – 2:30 (Beat 5 - Cell Inspector):** Click cell `89608850003ffff`. Drawer reveals 46.69°C LST, NDVI 0.082, 4,281 residents, 110 trees proposed.
6. **2:30 – 3:00 (Beat 6 - Fundable Assembly):** Click `[ Assemble Fundable Project ]`. Camera frames 28 cells. Reveal ₹9.99M CapEx and ₹7,500 slack under ₹10M budget.
7. **3:00 – 3:30 (Beat 7 - Allocation Blueprint):** Open Allocation tab. Show 2,695 trees. Click row to demonstrate **Allocation Immutability**.
8. **3:30 – 4:00 (Beat 8 - Municipal Sanction):** Execute state transition: input Sanction Order `PMC-CLIMATE-2025-084`. Badge transitions `PROPOSED -> FUNDED`.
9. **4:00 – 4:30 (Beat 9 - Contractor MRV):** Show logged 110 planted trees. Highlight locked verification gate (`UNOBSERVED / NOT YET VERIFIED`).
10. **4:30 – 4:50 (Beat 10 - Provenance):** Open Lineage Modal. Show SHA-256 digests and HiGHS linear solver runtime of 70.13 seconds.
11. **4:50 – 5:00 (Beat 11 - Conclusion):** Deliver final thesis: *"From planetary observation to municipal ground reality."*

---

## 16. DESIGN DECISION REGISTER

| Decision Item | Classification | Rationale & Governance Status |
| :--- | :--- | :--- |
| **3-Route Navigation Model** | **FROZEN FROM 2C.1** | Minimalist route architecture (`/`, `/explore/pune`, `/projects/:id`). |
| **Contextual 420px Side Drawer** | **FROZEN FROM 2C.1** | Preserves spatial context while enabling 5 disclosure levels. |
| **Primary User Persona** | **FROZEN FROM 2C.1** | Focused on Municipal Resilience Director; avoids feature creep. |
| **28-Cell Demonstration Constants**| **FROZEN** | Pune ₹10M, 28 cells, 2,695 trees, 118,941 pop, 0.106048 objective. |
| **Typography Direction A (Newsreader + Geist)** | **RECOMMENDED** | Combines classical institutional gravitas with optical UI precision. |
| **Basalt / Terracotta / Mineral Palette** | **RECOMMENDED** | Restrained climate-tech palette; zero neon/cyberpunk aesthetics. |
| **70/30 Desktop Layout Ratio** | **RECOMMENDED** | Optimal balance between spatial immersion and data legibility. |
| **Mobile Bottom Sheet Inspector** | **PROVISIONAL** | Adapts 420px drawer to mobile displays without route change. |
| **2025 Sensor Rectification** | **RECTIFIED (CONTRACT)**| Corrected to Landsat 8 TIRS DOY 109 (April 19 2025). |

---

## 17. OPEN QUESTIONS & PHASE 2C.3 HANDOFF

1. **WebGL Hexagon Rendering Performance:** Validate whether rendering 3,181 H3 Resolution 9 hexagons on integrated laptop GPUs achieves steady 60 FPS using Mapbox GL / Deck.gl.
2. **Visual Prototype Polish:** In **Phase 2C.3**, evaluate typography font-weight rendering on Windows ClearType vs macOS Retina displays.
3. **Phase 2C.3 Scope:** Proceed to interactive visual prototyping and interaction validation. Zero production code will be generated until Phase 2C.3 signoff.
