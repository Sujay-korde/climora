# CLIMORA — PHASE 2C.0 DESIGN FOUNDATION
## Product UX Governance, Visual North Star & Frontend Experience Architecture

**Document Version:** 1.0.0  
**Phase:** Phase 2C.0 — Frontend Design Foundation & Experience Governance  
**Target Document Path:** `docs/frontend/design/phase-2c0-design-foundation.md`  
**Governing Roles:** Principal Product Designer, Senior UI/UX Engineer, Design Systems Architect, Lead Product Strategist  
**Status:** **RATIFIED DESIGN GOVERNANCE SPECIFICATION**  
**Upstream System Frozen Baseline:** Phase 1A through Phase 1H.2, Phase 2A, Phase 2B (160 tests passing, 0 failures, 0 regressions)  
**Scientific Formulations Introduced:** **NONE** (Zero scientific recalculation; F-19 through F-28.1 strictly frozen)  

---

## EXECUTIVE MANDATE & GOVERNANCE SCOPE

This document establishes the binding **Design Foundation and Frontend Experience Architecture** for CLIMORA. 

CLIMORA is not an administrative GIS portal, not an internal enterprise analytics dashboard, not a generic SaaS telemetry console, and not an AI-generated landing page. It is an **Awwwards-level climate intelligence instrument and decision-support product** engineered to transition municipal leadership, climate financiers, and infrastructure planners from raw planetary observation to auditable, bankable urban cooling interventions.

This specification governs all subsequent frontend engineering, design token systems, wireframing, layout composition, and interactive component development. It enforces three inviolable principles:
1. **The UI is a visualization and decision layer over frozen canonical truth:** The frontend consumes precomputed canonical scientific artifacts and Phase 2B API contracts. It never executes scientific calculations, never alters formulations, and never synthesizes analytical truth in client-side code.
2. **Visual excellence and scientific credibility are inseparable:** The aesthetic bar is inspired by the calm, editorial restraint of *Vayu* (Minimal Creative) and the rigorous, verification-first architecture of *Proofmode*. Visual drama derives from typography, spatial hierarchy, generous breathing room, and immaculate data presentation—never from neon gradients, glassmorphism, or decorative clutter.
3. **Decisions precede the analytical pipeline:** The user experience is anchored in **Progressive Disclosure**. Non-technical decision-makers immediately comprehend the *need*, *location*, *action*, and *capital requirement* of an intervention before encountering mathematical formulations, H3 topologies, MILP solvers, or satellite spectral band derivations.

---

## 1. DESIGN MISSION

### 1.1 Purpose
The mission of the CLIMORA frontend is to transform complex, multi-sensor climate science and mathematical spatial optimization into a **calm, authoritative, and fundable narrative**.

Urban heat mitigation in Global South megacities (beginning with Pune, Maharashtra) currently suffers from a fatal disconnect: scientific researchers publish complex raster rasters that municipal commissioners cannot operationalize, while city planners deploy capital ad-hoc without spatial optimization or empirical verification. CLIMORA bridges this chasm by delivering an interface that:
- **Speaks with quiet scientific authority:** Every displayed pixel, polygon, and metric carries provenance and explicit truth attribution.
- **Empowers executive capital allocation:** Translates abstract heat hazards into specific physical units (street trees), exact budgetary envelopes (₹10,000,000 CapEx), and municipal ward contexts.
- **Enforces rigorous verifiability:** Quarantines modeled ex-ante simulations from empirical ex-post verifications, preserving uncompromised integrity for climate finance and municipal bonds.

### 1.2 The Emotional Impact
The CLIMORA interface must evoke:
- **Calm Clarity:** An antidote to chaotic, alarmist climate dashboards. The feeling of stepping into an impeccably curated scientific publication or examining an ultra-high-precision Swiss navigational instrument.
- **Absolute Trust:** Unflinching intellectual honesty. When empirical impact is unverified, the system proudly proclaims `UNOBSERVED / NOT YET VERIFIED` rather than fabricating synthetic cheer.
- **Spatial Wonder:** A deep respect for the geographic reality of Pune—its terrain, arterial corridors, dense settlements, and microclimates.

---

## 2. CORE DESIGN PRINCIPLES

```
+---------------------------------------------------------------------------------------------------+
|                                    CLIMORA UX AXIOMS                                              |
|                                                                                                   |
|  1. DECISION BEFORE PIPELINE      2. TRUTH-LAYER TRANSPARENCY    3. RESTRAINED EDITORIAL GRAVITAS  |
|  Understand *what to do* before   Never confuse observed data    Whitespace and typography create |
|  deciphering how it was modeled.  with simulated outcomes.       authority; zero decorative noise. |
|                                                                                                   |
|  4. INSTRUMENT OVER DASHBOARD     5. SPATIAL REASONING FIRST     6. PROVENANCE AS A FIRST-CLASS UI|
|  An analytical tool for action,   The H3 hexagonal mesh is a     Every metric links back to its   |
|  not a cemetery of widget cards.  canvas for spatial discovery.  sensor, equation, and artifact. |
+---------------------------------------------------------------------------------------------------+
```

### Principle 1: Decision Before Pipeline (Progressive Disclosure)
Executive stakeholders care about the intervention first, the rationale second, and the mathematical mechanics third. The interface surfaces high-level municipal decisions cleanly, providing effortless drill-downs for scientific auditors without frontloading technical jargon.

### Principle 2: Truth-Layer Transparency
Every metric is visually anchored in its epistemological reality: `OBSERVED`, `DERIVED`, `MODELED`, or `VERIFIED`. The UI guarantees that modeled microclimatic cooling can never be mistaken for empirical satellite measurement.

### Principle 3: Restrained Editorial Gravitas
Authority does not scream. CLIMORA avoids bright neon status lights, flashy gradients, and vibrating animations. It employs generous margins, classical proportions, deliberate typography, and high-contrast editorial layouts that convey institutional weight.

### Principle 4: Instrument Over Dashboard
Dashboards are passive aggregations of unrelated charts. CLIMORA is an active instrument: a unified operational surface where map interactions, portfolio summaries, budget constraints, and baseline evidence harmonize around a singular municipal goal.

### Principle 5: Spatial Reasoning as the Primary Interaction
Climate risk is inherently spatial. Rather than burying the map inside a small card widget, the spatial environment serves as the primary contextual anchor. The analytical topology (Uber H3 Resolution 9) is celebrated as a designed geometric mesh.

### Principle 6: Provenance as a First-Class UI Citizen
Scientific trust requires forensic auditability. The frontend provides immediate, non-intrusive access to source sensors (Landsat-8/9 TIRS, Sentinel-2 MSI, WorldPop, OSM), acquisition dates (target DOY 105), equations ($F\text{-}19$ through $F\text{-}28$), and canonical SHA-256 artifact digests.

---

## 3. VISUAL NORTH STAR

The visual north star of CLIMORA is defined by the following synthesis:

$$\mathbf{CLIMORA} = \mathbf{Editorial\ Digital\ Publication} + \mathbf{Spatial\ Intelligence\ Instrument} + \mathbf{Capital\ Decision\ System}$$

```
                           EDITORIAL DIGITAL PUBLICATION
                           (Generous whitespace, classical proportions,
                            refined typography, long-form narrative pacing)
                                        ▲
                                        │
                                        ▼
    SPATIAL INTELLIGENCE INSTRUMENT ◄───┼───► CAPITAL DECISION SUPPORT
    (H3 Resolution 9 geometry,          │     (₹10M budget ceiling, ₹7.5k slack,
     spectral layer overlays,           │      2,695 physical street trees,
     calibrated spatial palettes)       ▼      exact 118,941 protected population)
                              PREMIUM CLIMATE TECH
                              (Quiet, purposeful,
                               calm, institutionally fundable)
```

The product sits at the intersection of:
- An award-winning international climate journalism piece (e.g., *The New York Times* climate interactives, *Reuters Graphics*).
- An ultra-refined spatial intelligence apparatus (e.g., high-end Swiss topographic cartography meets modern geospatial analytics).
- An institutional financial prospectus for municipal green infrastructure bonds.

It deliberately rejects:
- Generic SaaS administrative consoles (sidebar + 12 KPI cards + data table).
- AI startup templates (black background + purple/cyan neon radial gradients + floating 3D spheres).
- Traditional government GIS portals (cluttered toolbars, 40 confusing layer toggles, microscopic serif text).
- PowerBI / Tableau / ArcGIS clones (stiff card borders, default primary colors, disjointed widgets).

---

## 4. VAYU-INSPIRED DESIGN PRINCIPLES TO ABSORB

*Reference: Vayu by Minimal Creative (Case Study & Platform Architecture)*

We extract the following structural and aesthetic principles from Vayu without copying its layout, branding, or specific graphics:

1. **Generous Whitespace as an Active Structural Element:**
   - Whitespace is not empty space; it is an active design element that focuses attention, provides cognitive relief, and signals luxury and confidence.
   - Large sections are allowed to contain a single focal narrative point or key metric without being filled with extraneous charts.
2. **Metadata Pointers and Scale Calibration Bars:**
   - Technical metadata (sensor source, resolution, temporal window, coordinate reference system) is presented in structured pointer blocks using clean, small-scale uppercase typography.
   - Visual scale indicators (tick marks, baseline calibration bars, coordinate ticks) frame spatial and analytical views, establishing an instrument-like aesthetic.
3. **Restrained, Asymmetrical Editorial Composition:**
   - Avoiding monotonous, centered layouts. Pairing a prominent, left-aligned editorial thesis statement with right-aligned, high-density data panels creates visual tension and editorial pacing.
   - Alternating wide-canvas spatial visualizers with narrow, focused analytical columns.
4. **Controlled Information Density & Vertical Rhythm:**
   - Content is spaced according to strict vertical rhythmic increments (8px / 16px / 24px / 48px / 96px / 144px).
   - Complex technical topics are broken into deliberate, paced steps (Problem $\rightarrow$ Spatial Evidence $\rightarrow$ Mathematical Priority $\rightarrow$ Municipal Implementation).
5. **Hairline Precision Borders & Subdued Dividers:**
   - Structural dividers use 1px hairlines with very low contrast against surfaces (e.g., 8–12% opacity neutral ink), avoiding heavy card containers.
   - Borders serve as subtle geometric guides rather than confining boxes.

---

## 5. PROOFMODE-INSPIRED DESIGN PRINCIPLES TO ABSORB

*Reference: Proofmode (Cryptographic Reality & Verification Architecture)*

We extract the following verification and trust-centric principles from Proofmode:

1. **Verification-First Architecture:**
   - Trust is not assumed; it is cryptographically and methodologically demonstrated.
   - The UI distinguishes between *what is claimed* and *what is verified*. Verification is treated as a monumental, auditable state rather than a checkbox.
2. **Restrained Pill & Status System:**
   - Status indicators do not use generic neon badges. They use subdued, bespoke pills with precise geometric framing, clear typography, and unambiguous semantic color.
   - Every status pill explicitly differentiates between `PROPOSED`, `FUNDED`, `IMPLEMENTING`, and `VERIFIED`.
3. **Section-to-Section Editorial Transitions:**
   - Transitions between thematic sections use intentional surface shifts (e.g., transition from warm mineral paper into deep atmospheric charcoal) to delineate cognitive shifts (e.g., from public narrative into operational spatial inspection).
4. **Modular Visual Fields & Card Objecthood:**
   - Data displays are treated as distinct *editorial objects* with bespoke proportions rather than cookie-cutter dashboard cards.
   - Large photographic, topographic, or spatial fields are integrated directly into the narrative stream rather than isolated into thumbnail popups.
5. **Architectural Footer & System Provenance:**
   - The footer and inspection drawers are treated as comprehensive architectural artifacts, providing exhaustive system telemetry, legal attribution, coordinate references, and methodology links.

---

## 6. CLIMORA'S OWN VISUAL IDENTITY & SYNTHESIS

CLIMORA synthesizes these influences into an original, domain-specific visual identity designed specifically for **Urban Climate Intelligence & Municipal Heat Mitigation**.

### 6.1 The Anti-Green Philosophy
Generic climate products rely heavily on saturated greens, falling into the cliché of "it's green, therefore it's environmental." 
CLIMORA rejects this superficial trope:
- **Surface Tone:** Evokes mineral, geological, and planetary foundations (calcified stone, bleached earth, deep basalt).
- **Ink Tone:** Evokes archival printing ink, dark shale, and deep charcoal.
- **Botanical Green:** Reserved strictly for **living biophysical infrastructure** (vegetation canopy, street tree deployments, NDVI biophysical cooling). It is deep, muted, and botanical—not neon lime.
- **Acid Lime:** Used exclusively as an ultra-controlled, microscopic accent (1px focal cursor, selected cell highlight, active timeline pulse) to direct ocular focus.
- **Terracotta & Scorched Earth:** Semantic hue representing radiant urban surface heat (LST), thermal anomalies, and extreme heat recurrence ($\ge 45^\circ\text{C}$).
- **Desaturated Cool Analytical:** Semantic hue representing hydrological features, atmospheric moisture, and baseline reference data.

```
+----------------------------------------------------------------------------------------------------+
|                               CLIMORA COLOR SPECTRUM SEMANTICS                                     |
|                                                                                                    |
|  [ MINERAL SURFACES ]      Warm off-white, bleached bone, pale slate (Day) / Basalt (Dark)       |
|  [ ARCHIVAL INK ]          Deep carbon, oxidized shale, graphite text                             |
|  [ BOTANICAL CANOPY ]      Muted forest pine, deep sage (represents nature-based interventions)    |
|  [ FOCAL ACCENT ]          Controlled acid lime (used sparingly for active selections & cursors)  |
|  [ THERMAL HAZARD ]        Scorched terracotta, clay, muted copper (represents radiant heat/LST)  |
|  [ COOL ANALYTICAL ]       Subdued slate-cyan, desaturated deep water (represents reference data) |
+----------------------------------------------------------------------------------------------------+
```

### 6.2 Semantic Mapping for Truth Layers
The four frozen truth layers of CLIMORA are given strict visual semantics that must remain uniform across the entire frontend:

| Truth Layer | Semantic Meaning | Visual Character | UI Treatment & Metadata Binding |
| :--- | :--- | :--- | :--- |
| **`OBSERVED`** | Direct physical sensor or cadastral measurement (Landsat TIRS, Sentinel-2 MSI, WorldPop) | **Factual, Neutral, Archival** | Monospace neutral tags; subtle stone pill with hairline border; indicates sensor, band, DOY, and spatial resolution. |
| **`DERIVED`** | Multi-year mathematical aggregation or spatial calculation (5-yr baseline mean, anomaly, Moran's $I$) | **Cool Analytical Slate** | Slate-blue tinted badge; explicit formula reference tag (e.g., `F-14`, `F-15`); indicates temporal baseline window (2021–2025). |
| **`MODELED`** | Ex-ante spatial optimization, HEV simulation, and prospective impact (MILP, CapEx, Risk) | **Warm Decision Gold / Amber** | Warm ochre/amber pill; explicit disclaimer: *"Ex-ante optimization projection under F-24 formulation; not verified impact."* |
| **`VERIFIED`** | Empirical, post-deployment, satellite-verified difference-in-differences outcome | **Audited Forest / Diamond Stamp** | High-contrast confirmation emblem; **strictly locked to `UNOBSERVED / NOT YET VERIFIED`** at current proposal phase. |

```
+---------------------------------------------------------------------------------------------------+
|                                  TRUTH LAYER VISUAL BADGES                                        |
|                                                                                                   |
|   [ OBSERVED  | Landsat-9 TIRS DOY 105 ]   --> Archival stone tint, neutral hairline border        |
|   [ DERIVED   | 5-Yr Mean Baseline F-14 ]  --> Cool slate tint, analytical formula badge          |
|   [ MODELED   | F-24 MILP Allocation ]     --> Ochre amber tint, explicit ex-ante warning         |
|   [ VERIFIED  | UNOBSERVED / PENDING ]     --> Quarantined grey-slate pill, locked verification pad|
+---------------------------------------------------------------------------------------------------+
```

---

## 7. TYPOGRAPHY PHILOSOPHY & HIERARCHY

CLIMORA operates with a tripartite typographical system: **Editorial Display**, **Functional UI**, and **Technical Monospace**.

```
+----------------------------------------------------------------------------------------------------+
|                                    TYPOGRAPHIC TRIAD                                               |
|                                                                                                    |
|    1. EDITORIAL DISPLAY             2. FUNCTIONAL UI GROTESK          3. TECHNICAL MONOSPACE       |
|    Classical, confident, literary   Neutral, legible, high-density     Engineered, scientific,     |
|    Used for: Major headlines,       Used for: Body prose, labels,      Used for: Cell IDs, sensor  |
|    thematic section titles,         table contents, interactive        metadata, coordinates,      |
|    key narrative anchors.           controls, buttons, microcopy.      financial figures, sha256.  |
|    (e.g., Newsreader/Instrument)    (e.g., Geist / Inter / Manrope)    (e.g., Geist Mono / Plex)   |
+----------------------------------------------------------------------------------------------------+
```

### 7.1 Typographic Roles & Justification

1. **Why the Editorial Display Face Exists:**
   - Climate change is a human and institutional crisis, not merely a telemetry problem.
   - An editorial serif or high-character display face gives the platform the intellectual gravitas of an authoritative report. It signals to municipal commissioners and institutional investors that this is a considered, strategic document.
   - *Exploration families:* `Newsreader`, `Instrument Serif`, `Montagu Slab`, `Cormorant Garamond`, `Canela-like`.
2. **Why the Functional UI Grotesk Exists:**
   - Complex data interfaces require impeccable optical clarity at sizes between 11px and 16px.
   - The UI face must feature tall x-height, open apertures, and tabular figure support so that metric tables and spatial inspector cards do not jitter.
   - *Exploration families:* `Geist Sans`, `Inter Tight`, `Public Sans`, `Manrope`.
3. **When Technical Monospace is Mandatory:**
   - Every H3 cell index (e.g., `8960145ad4fffff`).
   - Canonical identifiers (e.g., `PROJ-PUNE-2025-BA225D6A`, `OPT-PUNE-2025-SCENARIO-BA225D6A`).
   - Sensor metadata, band designations (`SR_B10`, `B08`), and acquisition dates (`DOY 105`).
   - Exact demographic totals (`118,941.21 exact canonical value`).
   - Budget figures (₹10,000,000, ₹9,992,500, ₹7,500).
   - Mathematical formulation tokens (`F-24.1`, `Moran's I = 0.428`).
   - Canonical SHA-256 artifact digests.
   - *Exploration families:* `Geist Mono`, `IBM Plex Mono`, `Space Mono`, `JetBrains Mono`.

### 7.2 Typographic Hierarchy & Scale Rationale

| Hierarchy Level | Face Category | Relative Scale | Line Height | Letter Spacing | Purpose & Usage Guidelines |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display Hero** | Editorial Serif | 48px – 72px | 1.05 – 1.15 | -0.02em | Hero impact statements on public narrative surfaces. Maximum 1 per major page. |
| **Section Title** | Editorial Serif | 32px – 40px | 1.20 | -0.01em | Thematic narrative shifts (e.g., "The Urban Heat Baseline of Pune"). |
| **UI Header (H3)** | Functional Grotesk | 20px – 24px | 1.30 | -0.01em | Inspector panel headers, modal headers, major view controllers. Semi-bold. |
| **Subhead / Lead** | Functional Grotesk | 16px – 18px | 1.50 | 0.00em | Introductory explanatory paragraphs preceding data views. Regular / Medium. |
| **UI Body** | Functional Grotesk | 13px – 14px | 1.55 | 0.00em | Standard analytical prose, inspector descriptions, metadata explanations. |
| **UI Microcopy** | Functional Grotesk | 11px – 12px | 1.40 | +0.01em | Form field labels, card captions, secondary notes. Uppercase or Sentence Case. |
| **Technical Data** | Technical Mono | 12px – 14px | 1.40 | -0.01em | Tabular numbers, budget breakdowns, cell statistics. Always tabular figures (`tnum`). |
| **System Tag / Pill**| Technical Mono | 10px – 11px | 1.00 | +0.05em | Truth-layer badges (`OBSERVED`), sensor badges, state indicators. Strictly uppercase. |

### 7.3 Typography Rules of Disappearance
- **Typography must dominate** in high-level narrative and problem-framing moments where human understanding is established.
- **Typography must disappear** into clean, unencumbered tabular scaffolding during spatial inspection, allowing the map, the geometry, and the numbers to communicate without visual friction.

---

## 8. COLOR PHILOSOPHY & SEMANTIC MAPPING

### 8.1 Environmental Palette Architecture
CLIMORA does not use a single background color or a generic dark-mode toggle. It utilizes **thematic environmental surfaces** tuned to the cognitive mode of the user.

```
+---------------------------------------------------------------------------------------------------+
|                                 ENVIRONMENTAL SURFACE MODES                                       |
|                                                                                                   |
|  MODE 1: ARCHIVAL MINERAL (Light Theme / Executive Briefing)                                       |
|  - Surface: Pale calcified sandstone, warm parchment, bleached limestone                          |
|  - Text: Deep charcoal ink (#161716), muted graphite (#525451)                                   |
|  - Vibe: Prestigious institutional whitepaper, high-end print publication.                         |
|                                                                                                   |
|  MODE 2: DEEP BASALT / NOCTURNE (Spatial Instrument / Dark Theme)                                  |
|  - Surface: Deep volcanic basalt, obsidian, dark shale (#0D0F0E, #141715)                         |
|  - Text: Crisp off-white (#EDEFEA), muted stone (#8E928C)                                         |
|  - Vibe: High-precision satellite telemetry console, planetary observation terminal.              |
+---------------------------------------------------------------------------------------------------+
```

### 8.2 Semantic Color Mapping by Domain

1. **Thermal Hazard Domain (Scorched Terracotta):**
   - Radiant Land Surface Temperature ($LST_{2025}$), thermal anomalies ($\Delta LST$), and extreme heat recurrence ($\ge 45^\circ\text{C}$).
   - *Tonal Range:* Muted rust $\rightarrow$ burnt terracotta $\rightarrow$ deep ember. Never neon red or cartoonish orange.
2. **Biophysical Infrastructure Domain (Botanical Sage to Forest):**
   - Existing vegetation canopy (NDVI), urban greening opportunities, street tree interventions.
   - *Tonal Range:* Pale lichen $\rightarrow$ muted sage $\rightarrow$ deep botanical evergreen.
3. **Urban Morphology & Built Mass (Mineral Slate):**
   - Built-up index (NDBI), impervious surface coverage, arterial road corridors.
   - *Tonal Range:* Concrete grey $\rightarrow$ oxidized graphite $\rightarrow$ dark slate.
4. **Hydrology & Atmospheric Baseline (Cool Desaturated Water):**
   - Water bodies (Mula-Mutha rivers), atmospheric moisture, baseline reference layers.
   - *Tonal Range:* Desaturated cool blue-grey. Never saturated azure.
5. **The Controlled Focal Cursor (Acid Lime / Electric Spruce):**
   - Used in micro-doses (< 0.5% of total screen pixels):
     - Active H3 hexagon selection border.
     - Pulsing timeline progress marker.
     - Focused data cursor in interactive distribution charts.

---

## 9. GRID, GEOMETRY & SPACING PHILOSOPHY

### 9.1 The Responsive 12-Column Editorial Grid
Layouts are anchored to a mathematical 12-column grid that allows both classical symmetry and dynamic, asymmetric tension:

```
+----+----+----+----+----+----+----+----+----+----+----+----+
| C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10| C11| C12|
+----+----+----+----+----+----+----+----+----+----+----+----+
|<-- 4 Cols: Context / Problem ->|<-- 8 Cols: Spatial Instrument / Topology -->|
|<-- 7 Cols: Narrative Thesis -->|<-- 5 Cols: Exact Budget & Allocations ----->|
|<------------------------ 12 Cols: Full Bleed Map / Horizon ----------------->|
```

- **Desktop Canvas:** Maximum content constraint of 1440px or 1600px with dynamic outer gutters (minimum 48px, expanding on wide screens).
- **Asymmetric Composition:**
  - Executive views: 5 columns for narrative problem framing, 7 columns for interactive spatial evidence.
  - Detail inspection: 8 columns for the interactive H3 map instrument, 4 columns for the sticky, deep-dive analytical inspector drawer.
- **Vertical Spacing Rhythm:**
  - Strict 8pt spatial grid: 8px, 16px, 24px, 32px, 48px, 64px, 96px, 128px.
  - Large section transitions use 96px to 144px of breathing room to enforce cognitive reset between stages of the decision journey.

### 9.2 Geometric Philosophy: Rejection of the Generic Rounded Card
- **No Heavy Card Enclosures:** Information does not need to be barricaded inside round-cornered boxes with heavy drop shadows.
- **Structural Lines Over Containers:** Data modules are separated by razor-sharp 1px hairline dividers with generous padding on either side.
- **Restrained Corner Radii:** Where structural containers are necessary (e.g., active floating toolbars, inspection sheets), corners use subtle, architectonic radii (4px to 8px max). Bulky, bubble-like 24px radii are strictly prohibited.

---

## 10. COMPONENT PHILOSOPHY

CLIMORA treats UI components as **editorial and scientific objects**, not interchangeable dashboard widgets.

```
+---------------------------------------------------------------------------------------------------+
|                               COMPONENT DESIGN ARCHETYPES                                         |
|                                                                                                   |
|  1. THE EDITORIAL NARRATIVE BLOCK    2. THE SPATIAL INSTRUMENT CANVAS    3. THE INSPECTION DRAWER |
|  Typography-led thesis statement     Interactive H3 mesh surface with    Slide-in or sticky deep-  |
|  with embedded inline metrics        minimalist floating calibration     dive panel with forensic  |
|  and direct provenance pills.        controls and viewport telemetry.    provenance and charts.   |
|                                                                                                   |
|  4. THE ARCHITECTURAL STAT BLOCK     5. THE AUDITABLE TIMELINE           6. THE TRUTH BADGE       |
|  Large tabular figures with small    Structured lifecycle tracker with   Standardized capsule with|
|  labels and explicit truth layer.    explicit gating prerequisites.      layer type & sensor tags.|
+---------------------------------------------------------------------------------------------------+
```

### 10.1 Component Archetypes

1. **The Editorial Narrative Block:**
   - Combines a prominent headline, concise explanatory text, and inline live data tokens.
   - Example: *"In Ward 14 (Hadapsar), pre-monsoon surface temperatures exceed **46.7°C** across **28 critical zones**, exposing **118,941 residents** to chronic microclimatic stress."*
2. **The Spatial Instrument Canvas:**
   - Framed with subtle geographic coordinate marks (latitude/longitude hairlines).
   - Floats a minimalist viewport status chip: `[ H3 RES-9 | PUNE URBAN AGGLOMERATION | EPSG:4326 ]`.
   - Free of cluttered GIS zoom buttons; supports fluid, physics-based pan and zoom with high-performance WebGL rendering.
3. **The Deep-Dive Inspection Drawer:**
   - Appears upon cell selection or drill-down request.
   - Structured into four permanent zones:
     - *Zone A (Spatial Identity):* Cell hex ID, statutory ward context, land area.
     - *Zone B (Baseline Evidence):* Observed LST, derived 5-year anomaly, biophysical canopy (NDVI), built-up density (NDBI).
     - *Zone C (Optimization & Action):* Allocated tree count, direct CapEx, mobilization cost.
     - *Zone D (Scientific Audit & Provenance):* Sensor platform, DOY, equations applied, source Parquet SHA-256.
4. **The Architectural Stat Block:**
   - Replaces the generic "KPI card."
   - Features a large-scale number set in tabular monospace or grotesk, an understated uppercase label, and an integrated truth-layer pill.
   - Zero superfluous icons (no cartoon thermomemters or trees).
5. **The Lifecycle State Machine Stepper:**
   - Displays the project's journey: `DISCOVERED` $\rightarrow$ `ASSESSED` $\rightarrow$ `OPTIMIZED` $\rightarrow$ `PROPOSED` $\rightarrow$ `FUNDED` $\rightarrow$ `IMPLEMENTING` $\rightarrow$ `IMPLEMENTED` $\rightarrow$ `MONITORING` $\rightarrow$ `VERIFIED`.
   - Visually indicates gate conditions and locks downstream states until explicit prerequisites are satisfied.

---

## 11. INFORMATION-DENSITY RULES

Climate intelligence contains hundreds of variables across thousands of spatial units. Left unchecked, interfaces become unreadable data cemeteries. CLIMORA governs density through strict rules:

```
+---------------------------------------------------------------------------------------------------+
|                                  DENSITY GOVERNANCE RULES                                         |
|                                                                                                   |
|  EXECUTIVE VIEW (Top-Level)         --> Low Density (1-3 Key Decisions, Generous Margins)          |
|  PORTFOLIO VIEW (Comparative)       --> Moderate Density (Structured Tables, Spatial Corridors)    |
|  CELL INSPECTION VIEW (Forensic)    --> High Density (Deep Provenance, Band Data, Formulations)    |
+---------------------------------------------------------------------------------------------------+
```

1. **The Single Primary Focal Point Rule:**
   - Every view must have exactly one primary visual anchor (e.g., the spatial map or the portfolio decision summary). Secondary modules must defer visually to the primary anchor.
2. **The 3-Second Comprehension Rule:**
   - An executive viewing any screen for 3 seconds must immediately comprehend:
     - *Where are we looking?* (Pune, 28 treated cells).
     - *What is the decision?* (Deploy 2,695 street trees for ₹9,992,500).
     - *What is the status?* (Proposed, awaiting sanction).
3. **No Redundant KPI Echoing:**
   - A metric must not be displayed three times in three different card formats. Display it once with authoritative precision and contextual depth.
4. **Strict Monospace Formatting for All Quantities:**
   - All floating-point and monetary values use tabular figures (`font-variant-numeric: tabular-nums`) to prevent layout shifts during interaction and facilitate vertical scanning.

---

## 12. PROGRESSIVE-DISCLOSURE RULES

Progressive disclosure is the central UX mechanism separating CLIMORA from traditional GIS and dashboard tools.

```
                                  PROGRESSIVE DISCLOSURE FUNNEL
                                  
    LEVEL 1: THE EXECUTIVE DECISION          "Deploy 2,695 street trees across 28 high-heat cells in Pune."
    (Immediately visible; zero jargon)        Budget: ₹9.99M | Protected: 118,941 residents
                   │
                   ▼
    LEVEL 2: THE SPATIAL & PHYSICAL WHY       "Why these 28 cells?"
    (One-click inspection)                    Persistent thermal anomaly > 46°C + high population exposure
                   │                          + low vegetative canopy (< 0.12 NDVI).
                   ▼
    LEVEL 3: THE CAPITAL ALLOCATION           "What is the cost breakdown?"
    (Tabular drill-down)                      ₹3,500/tree planting + ₹20,000/cell mobilization.
                   │                          Remaining slack: ₹7,500 under ₹10M budget ceiling.
                   ▼
    LEVEL 4: THE SCIENTIFIC & LEGAL PROVENANCE "Show me the mathematical and sensor proof."
    (On-demand drawer / modal)                Landsat-9 TIRS DOY 105, F-24 MILP objective formulation,
                                              LISA Moran's I, Parquet SHA-256 digests.
```

### The Explicit Disclosure Contract
- **Never force a non-expert to read the analytical pipeline:** A municipal commissioner must be able to sanction a project without ever knowing what an H3 index or a MILP solver is.
- **Never hide the analytical pipeline from an auditor:** A climate bond verifier or scientific reviewer must be able to inspect every raw sensor band, QA mask, and equation parameter in three clicks or fewer.
- **Disclosure Controls:** Technical depth is accessed via clean, understated action triggers: `[ Inspect Scientific Lineage ]`, `[ View Sensor Provenance ]`, `[ Formulation Details F-24 ]`.

---

## 13. SPATIAL EXPERIENCE & MAP INSTRUMENT ARCHITECTURE

The map is the primary cognitive stage of CLIMORA. It is not an embedded Google Maps iframe or an admin GIS tool.

```
+---------------------------------------------------------------------------------------------------+
|                                 SPATIAL HIERARCHY OF PUNE                                         |
|                                                                                                   |
|  LEVEL 1: CITY SCALE              Overview of Pune Municipal Boundary (AOI: 4194).               |
|  (Zoom 10 - 11)                   Urban thermal morphology, regional heat distribution.           |
|                                                                                                   |
|  LEVEL 2: CORRIDOR / WARD SCALE   Administrative Wards (contextual overlay only).                 |
|  (Zoom 12 - 13)                   Cluster identification, arterial street corridors.              |
|                                                                                                   |
|  LEVEL 3: H3 ANALYTICAL MESH      Resolution 9 Hexagonal Topology (~0.10 km² per cell).           |
|  (Zoom 14 - 15)                   Treated footprint (28 cells) highlighted against city mesh.     |
|                                                                                                   |
|  LEVEL 4: CELL DEEP-DIVE          Individual cell inspection (30m Landsat pixel resolution).      |
|  (Zoom 16+)                       Road network, tree planting capacity, microclimatic baseline.   |
+---------------------------------------------------------------------------------------------------+
```

### 13.1 Spatial Topology vs Administrative Wards
- **H3 Resolution 9 is the Sole Analytical Topology:** The optimization, risk surface, biophysical indices, and tree allocations exist strictly on H3 hexagons.
- **Wards are Contextual Metadata:** Administrative ward boundaries are available as an optional, translucent contextual guide for municipal reporting. The UI will **never** allow administrative wards to be treated as optimization units or constraint boundaries.

### 13.2 Map Aesthetic Guidelines
- **Base Cartography:** Bespoke, high-contrast, minimalist vector tiles (subdued roads, zero distracting commercial POIs, muted water bodies).
- **Hexagon Geometry Styling:**
  - Non-selected city cells: Subtle hairline borders with 5–10% opacity, revealing urban geometry without visual noise.
  - The 28 Selected Canonical Cells: Prominent, high-density botanical sage / deep emerald fill with crisp boundaries, visually isolated as the municipal intervention footprint.
  - Hover / Focus State: Delicate acid lime hairline cursor framing the hovered hexagon, with an instant, lightweight spatial tooltip.

---

## 14. MICROINTERACTION PHILOSOPHY

Motion in CLIMORA is functional, mathematical, and calm. It communicates **causality and spatial continuity**, never decorative spectacle.

```
+----------------------------------------------------------------------------------------------------+
|                                    MOTION TAXONOMY                                                 |
|                                                                                                    |
|  1. SPATIAL CONTINUITY              Smooth camera transitions when moving from citywide view       |
|                                     to the 28-cell project footprint. Easing: cubic-bezier.        |
|                                                                                                    |
|  2. TABULAR NUMBER INTERPOLATION    When toggling scenarios or budgets, metrics interpolate        |
|                                     smoothly over 400ms rather than snapping abruptly.             |
|                                                                                                    |
|  3. CELL SELECTION REVEAL           Selected H3 cells expand their stroke subtly; inspection      |
|                                     drawer slides in with a precise, dampened physical feel.       |
|                                                                                                    |
|  4. REDUCED MOTION MANDATE          Full respect for `prefers-reduced-motion`. When active,       |
|                                     all animations revert to instantaneous state switches.         |
+----------------------------------------------------------------------------------------------------+
```

### Prohibited Motion Anti-Patterns
- Parallax scrolling effects that distort reading position.
- Bouncing buttons, elastic rubber-band easing, or cartoonish UI micro-jiggles.
- Flashing neon alert pulses or simulated "matrix" data streams.
- Page transition loaders that lock user interaction.

---

## 15. ACCESSIBILITY, USABILITY & INCLUSION STANDARDS

Awwwards-level visual design is worthless if it excludes users or fails institutional compliance. CLIMORA commits to **WCAG 2.1 Level AA** compliance (and AAA for textual contrast):

1. **Textual Contrast Ratios:**
   - Body prose and data numbers maintain a minimum contrast ratio of **7:1** against backgrounds in both light and dark modes.
   - Secondary labels and microcopy maintain a minimum contrast ratio of **4.5:1**.
2. **Colorblind-Safe Spatial Palettes:**
   - Thermal hazard scales (terracotta/copper) and biophysical green scales (sage/forest) are tested against Deuteranopia, Protanopia, and Tritanopia.
   - The map never relies on color alone to communicate quantitative differences; spatial metrics are backed by numerical tooltips, patterns, and tabular fallbacks.
3. **Keyboard Navigability of Spatial Data:**
   - The entire 28-cell canonical portfolio is navigable via keyboard (`Tab`, arrow keys, `Enter` to inspect).
   - A dedicated **Tabular Portfolio View** provides a 100% accessible, WCAG-compliant alternative to the WebGL map interface.
4. **Screen Reader Semantic Architecture:**
   - All spatial data is backed by semantic HTML5 tables and ARIA live regions.
   - Screen readers announce cell selections, filter updates, and state transitions clearly (e.g., *"H3 cell 8960145ad4fffff selected. Ward: Hadapsar. Allocated street trees: 110. Baseline temperature: 46.8 degrees Celsius."*).

---

## 16. PUBLIC EXPERIENCE VS. APPLICATION EXPERIENCE

CLIMORA operates as two distinct but harmonious product experiences:

```
+----------------------------------------------------------------------------------------------------+
|                                  THE DUAL EXPERIENCE ARCHITECTURE                                  |
|                                                                                                    |
|  EXPERIENCE A: PUBLIC / PRODUCT NARRATIVE            EXPERIENCE B: APPLICATION / DECISION SUITE     |
|  - Audience: Citizens, climate leaders, journalists  - Audience: Municipal engineers, bond verifiers|
|  - Tone: Immersive, narrative, editorial, inspiring  - Tone: Operational, spatial, analytical, dense|
|  - Density: Low to medium; story-driven              - Density: Medium to high; tool-driven         |
|  - Primary Action: Understand the problem & promise  - Primary Action: Allocate, inspect, certify   |
|  - Map Role: Curated, guided scrollytelling canvas   - Map Role: Full interactive analytical tool   |
+----------------------------------------------------------------------------------------------------+
```

### Shared Visual Heritage
Both experiences share:
- The exact same typographic triad (Display Serif, UI Grotesk, Technical Mono).
- The exact same color spectrum and truth-layer badges.
- Identical canonical data values (₹9,992,500, 2,695 trees, 28 cells, 118,941 population).
- Seamless transition: A button in the public experience (`[ Open Pune Decision Suite ]`) transitions directly into the application experience without a visual shock.

---

## 17. PRELIMINARY INFORMATION ARCHITECTURE & USER DECISION JOURNEY

The user experience follows the canonical **9-Stage Decision Journey**:

$$\mathbf{OBSERVE} \longrightarrow \mathbf{UNDERSTAND} \longrightarrow \mathbf{IDENTIFY} \longrightarrow \mathbf{PRIORITIZE} \longrightarrow \mathbf{INTERVENE} \longrightarrow \mathbf{FUND} \longrightarrow \mathbf{IMPLEMENT} \longrightarrow \mathbf{VERIFY}$$

```
+----------------------------------------------------------------------------------------------------+
|                               PRELIMINARY INFORMATION ARCHITECTURE                                 |
|                                                                                                    |
|  1. / (ROOT) ── PUBLIC NARRATIVE                                                                   |
|     ├── Problem: Urban Heat Crisis in Indian Megacities                                            |
|     ├── Pune Demonstration: The Evidence & The Opportunity                                         |
|     └── Call to Action: Access Analytical Platform                                                 |
|                                                                                                    |
|  2. /explore/pune ── CITY EXPLORER & SPATIAL INSTRUMENT                                            |
|     ├── City Thermal Baseline (Landsat 2021-2025 Multi-Year Heat Surface)                          |
|     ├── Exposure & Vulnerability Overlays (WorldPop + OSM Density)                                 |
|     └── Spatial Autocorrelation & Hotspot Clusters (LISA Moran's I Quadrants)                      |
|                                                                                                    |
|  3. /projects/PROJ-PUNE-2025-BA225D6A ── CANONICAL PROJECT SUITE                                  |
|     ├── Overview Tab: Executive Decision & Proposal Synthesis                                      |
|     ├── Spatial Allocation Tab: Interactive 28-Cell Mesh & Planting Blueprint                      |
|     ├── Baseline Evidence Tab: Cell-by-cell Observed vs Derived Evidence                           |
|     ├── Capital & Budget Tab: Transparent ₹10M Breakdown & Contractor Unit Costs                   |
|     ├── MRV & Implementation Tab: Deployment Tracking & Deviation Audits                           |
|     └── Scientific Provenance Modal: Sensor Lineage, SHA Digests, F-Formulations                   |
+----------------------------------------------------------------------------------------------------+
```

### Structural Screen Classifications
- **Primary Pages:** Full-route destinations (`/`, `/explore/pune`, `/projects/:id`).
- **Interactive Views:** State-driven modes within the spatial explorer (e.g., *Heat View*, *Exposure View*, *Hotspot View*, *Intervention Allocation View*).
- **Contextual Drawers:** Slide-in sheets for single-cell deep dives and contractor deviation audits.
- **Forensic Overlays / Modals:** Full-screen or centered sheets for mathematical formulation inspection and canonical Parquet SHA-256 validation.

---

## 18. DESIGN ANTI-PATTERNS REGISTER

To ensure that future design exploration and engineering never dilute CLIMORA's visual and scientific integrity, the following patterns are **strictly prohibited**:

```
+---------------------------------------------------------------------------------------------------+
|                                STRICTLY PROHIBITED DESIGN ANTI-PATTERNS                           |
|                                                                                                   |
|  [X] Neon Cyberpunk Aesthetic         [X] Generic AI Badges ("Powered by AI", sparkles)           |
|  [X] Saturated Glassmorphism          [X] Fake 3D Climate Graphics (Rotating glowing globes)      |
|  [X] Card Grids Everywhere            [X] Giant Dashboard KPI Wall (20 unranked widget boxes)     |
|  [X] Meaningless Data Animation       [X] Misrepresenting Modeled Scores as Verified Impact       |
|  [X] Masking Administrative Layers    [X] Client-side Scientific Recalculation                    |
+---------------------------------------------------------------------------------------------------+
```

### Prohibited Patterns in Detail:
1. **No Neon Cyberpunk or "Hacker" Visuals:** No glowing green borders, fluorescent purple heat maps, or dark-web matrix aesthetic. CLIMORA is institutional and environmental.
2. **No Generic Glassmorphism:** Heavy blurred backgrounds with frosted glass borders and multi-layered translucent cards dilute legibility and feel dated. Surfaces must be crisp and opaque.
3. **No Fake "AI" Tropes:** No sparkle icons, no "AI Magic" tags, no generative chatbot widgets placed randomly in the corner. CLIMORA uses deterministic Mixed-Integer Linear Programming (MILP) and validated spatial statistics, not probabilistic LLM guessing.
4. **No Misrepresentation of the Optimization Objective:**
   - The value `0.10604830270054796` must **NEVER** be displayed as "10.6% cooling", "10.6% temperature reduction", "10.6% risk reduction", or "10.6% clinical health improvement".
   - It is strictly labeled: *"modeled aggregate risk-objective reduction under the canonical optimization formulation."*
5. **No Synthetic MRV Certification:** Synthetic demonstration fixtures (`DEMO_ONLY_SYNTHETIC_MRV_DATA`) must never be visually styled as official, validated field evidence.
6. **No Sentinel-2 Thermal Misrepresentation:** Sentinel-2 MSI must never be labeled or depicted as a thermal surface temperature sensor.

---

## 19. FRONTEND / BACKEND INTEGRATION & TRUTH-LAYER SYNERGY

The future frontend is bound to the frozen backend services ratified in Phase 2B.

```
+---------------------------------------------------------------------------------------------------+
|                                 FRONTEND-BACKEND CONTRACT BINDING                                 |
|                                                                                                   |
|   FLASK / PYDANTIC BACKEND (Phase 2B Frozen Contract)         FUTURE REACT / VITE FRONTEND        |
|                                                                                                   |
|   GET  /projects                                      ────►   High-Level Project Proposal List    |
|   GET  /projects/{id}                                 ────►   13-Section Canonical Detail View    |
|   GET  /projects/{id}/allocation?page=1&page_size=28  ────►   28-Cell Spatial Map & Table Mesh    |
|   GET  /projects/{id}/baseline?page=1&page_size=28    ────►   Observed & Derived Evidence Grids   |
|   GET  /projects/{id}/mrv                             ────►   MRV Tracking & DID Readiness Drawer |
|   POST /projects/{id}/implementation-events           ────►   Contractor Deployment Logging Form  |
|   POST /projects/{id}/revisions                       ────►   Auditable Allocation Revision Modal |
|   POST /projects/{id}/transition                      ────►   Guarded Lifecycle Transition Stepper|
+---------------------------------------------------------------------------------------------------+
```

### 19.1 Invariant Demonstration Truth
The frontend must accurately render the following canonical demonstration constants without deviation:

| Analytical Parameter | Canonical Value | Frontend Rendering Governance |
| :--- | :--- | :--- |
| **Project Identifier** | `PROJ-PUNE-2025-BA225D6A` | Display in technical monospace; immutable primary key. |
| **Optimization Run ID** | `OPT-PUNE-2025-SCENARIO-BA225D6A` | Linked to solver lineage and formulation $F\text{-}24$. |
| **Analytical Topology** | Uber H3 Resolution 9 | Hexagons rendered at native resolution (~0.10 $\text{km}^2$). |
| **Treated Footprint** | Exactly 28 cells | Displayed as discrete spatial cohort across Pune. |
| **Intervention Scope** | 2,695 street trees | Nature-based roadside canopy deployment. |
| **Modeled Total CapEx** | ₹9,992,500 | Formatted with Indian Rupee symbol and Indian numbering system. |
| **Municipal Budget** | ₹10,000,000 | Baseline municipal allocation envelope. |
| **Budget Slack** | ₹7,500 | Explicit unallocated surplus remaining in envelope. |
| **Protected Population** | `118,941.21` exact canonical | Exact underlying value in tooltips; display rounded to `118,941`. |
| **Modeled Objective** | `0.10604830270054796` | Label strictly as modeled aggregate risk-objective reduction. |
| **Difference-in-Differences**| `PLANNED / NOT_YET_EXECUTABLE` | Quarantined readiness state; execution disabled in UI. |
| **Verified Impact** | `null` / `UNOBSERVED` | Displayed with locked padlock or explicit pending verification badge. |

### 19.2 Zero Scientific Logic in JavaScript
The frontend will **never**:
- Compute spatial autocorrelation or Moran's $I$.
- Compute HEV risk scores or apply exponent weights.
- Solve or approximate MILP optimization algorithms.
- Interpolate or synthesize thermal anomalies from raster bands.
- Recalculate contractor deviations using ad-hoc formulas.

The frontend is an **honest, high-fidelity projection of backend truth**.

---

## 20. DESIGN DECISION REGISTER & OPEN EXPLORATIONS

To prevent premature freezing of elements that require visual prototyping and usability testing, this register formally distinguishes between **Frozen Architectural Truth**, **Frozen Design Principles**, and **Open Design Decisions**:

| Design Dimension | Governance Status | Underlying Rationale | Requires Visual Exploration in Phase 2C.1/2C.2? |
| :--- | :--- | :--- | :---: |
| **Scientific Formulations** | **FROZEN** | Ratified across Phase 1A–1H; zero recalculation in UI. | **NO** |
| **Canonical Demonstration Truth** | **FROZEN** | Pune ₹10M, 28 cells, 2,695 trees, 118,941 pop, 0.106048 objective. | **NO** |
| **API Contract & Schemas** | **FROZEN** | Phase 2B hardened query layer and Pydantic v2 endpoints. | **NO** |
| **Truth-Layer Taxonomy** | **FROZEN** | 4-tier truth classification (`OBSERVED`, `DERIVED`, `MODELED`, `VERIFIED`). | **NO** |
| **Spatial Topology** | **FROZEN** | H3 Resolution 9 analytical topology; wards decoupled as display context. | **NO** |
| **Design Philosophy & North Star** | **PRINCIPLE FROZEN** | Editorial + Spatial Instrument + Capital Decision Support (Vayu/Proofmode). | **NO** |
| **Progressive Disclosure Funnel** | **PRINCIPLE FROZEN** | Decision-first hierarchy (Level 1 Decision $\rightarrow$ Level 4 Provenance). | **NO** |
| **Typography Family Selection** | **NOT FROZEN** | Requires side-by-side legibility comparison between candidate pairings. | **YES** |
| **Exact Color Hex Tokens** | **NOT FROZEN** | Requires optical calibration for map layers and WCAG 2.1 AA/AAA compliance. | **YES** |
| **Information Architecture Routes** | **PROVISIONAL** | Initial proposed 3-route model requires wireframing and user journey testing. | **YES** |
| **Navigation & Layout Model** | **PROVISIONAL** | Split-screen vs sticky drawer vs full-bleed map requires wireframing. | **YES** |
| **H3 Hexagon Visual Styling** | **PROVISIONAL** | Stroke width, fill opacities, and hover shaders require map engine testing. | **YES** |
| **Microinteraction Specifications** | **PROVISIONAL** | Transition curves, hover dampening, and drawer easing require prototyping. | **YES** |
| **Tabular Fallback Component Architecture** | **PROVISIONAL** | Accessible table representation of 28 cells requires usability audit. | **YES** |

---

## CONCLUSION & ARCHITECTURAL READINESS

Phase 2C.0 establishes the unshakeable foundation for the CLIMORA frontend. By marrying the editorial sophistication of international climate publications with the mathematical rigor of a spatial intelligence instrument, CLIMORA ensures that every stakeholder—from municipal leaders to climate bond auditors—experiences clarity, authority, and trust.

Execution must now proceed strictly to **Phase 2C.1: Product Information Architecture & User Journey Design**.
No UI code, React components, Tailwind styling, or visual mockups shall be implemented until Phase 2C.1 is complete.
