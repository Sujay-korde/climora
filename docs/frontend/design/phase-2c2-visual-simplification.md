# CLIMORA — PHASE 2C.2R VISUAL SIMPLIFICATION & DESIGN REVISION
## Information Density Reduction, Anti-Claudish UX Architecture & Quiet Geospatial Governance

**Document Version:** 1.0.0  
**Phase:** Phase 2C.2R — Visual Simplification & Information Density Revision  
**Target Document Path:** `docs/frontend/design/phase-2c2-visual-simplification.md`  
**Parent Specifications:**
- Design Foundation: [`docs/frontend/design/phase-2c0-design-foundation.md`](file:///c:/Users/lenovo/climora/docs/frontend/design/phase-2c0-design-foundation.md)
- Information Architecture: [`docs/frontend/design/phase-2c1-information-architecture.md`](file:///c:/Users/lenovo/climora/docs/frontend/design/phase-2c1-information-architecture.md)
- Wireframe System: [`docs/frontend/design/phase-2c2-wireframe-visual-system.md`](file:///c:/Users/lenovo/climora/docs/frontend/design/phase-2c2-wireframe-visual-system.md)  
**Governing Roles:** Principal Product Designer, Senior UX Architect, Design Systems Architect, Lead Product Strategist  
**Status:** **RATIFIED DESIGN REVISION SPECIFICATION**  
**Backend & Scientific Freeze:** Phase 1A–1H.2, Phase 2A, Phase 2B (160 tests passing, 0 failures, 0 regressions)  
**Scientific Formulations Introduced:** **NONE** (Zero client-side recalculation; formulations $F\text{-}19$ through $F\text{-}28.1$ frozen)  

---

## 1. REVISED VISUAL PRINCIPLES: THE "QUIET UI" DIRECTIVE

> **"MAKE THE UI QUIET."**

CLIMORA is an instrument for consequential municipal capital allocation. It is neither a promotional showcase for a design system nor an AI-generated SaaS dashboard. It does not need to constantly advertise its mathematical complexity through visual ornamentation.

```
+----------------------------------------------------------------------------------------------------+
|                                    THE QUIET UI DIRECTIVE                                          |
|                                                                                                    |
|    WHAT CLIMORA IS:                      WHAT CLIMORA IS NOT:                                      |
|    • Editorial, calm, confident          • An AI-generated dashboard showcase                      |
|    • Spatial-first and map-dominant      • "Claudish" (over-decorated with labels and badges)      |
|    • Mathematically honest               • A telemetry control room with permanent HUD strips       |
|    • Institutionally bankable            • A presentation deck with numbered headings (01 /, 02 /)  |
|    • Focused on 1 question per screen    • A database dump of hashes, formulas, and raw variables   |
+----------------------------------------------------------------------------------------------------+
```

### The Three Core Revision Axioms:
1. **One View, One Primary Question:** Each screen or state answers exactly one fundamental question. If an element does not advance that question, it is removed from the primary viewport.
2. **Technical Depth on Demand, Not Technical Clutter by Default:** High-order mathematical formulations ($F\text{-}19$ to $F\text{-}28$), Parquet SHA-256 hashes, solver runtimes, and band-level acquisition metadata exist exclusively in on-demand inspection sheets.
3. **Restrained Instrument Aesthetics:** Acid-lime accents are restricted to $< 0.5\%$ of active pixels (active cell outline and focused cursor). No glowing outlines, neon badges, decorative math symbols ($\Sigma$), or artificial telemetry banners.

---

## 2. SIMPLIFIED NAVIGATION

The persistent top navigation is stripped of all diagnostic telemetry, dataset codes, and coordinate strings. Its sole purpose is **wayfinding and orientation**.

### 2.1 The Revised Persistent Navbar:
```text
+----------------------------------------------------------------------------------------------------+
|  CLIMORA                       Overview     Explore     Projects                                   |
+----------------------------------------------------------------------------------------------------+
```

- **Brand Anchor (`CLIMORA`):** Plain typographical wordmark in `Geist Sans Medium`. Returns to `/`.
- **Primary Routes:**
  - `Overview` $\rightarrow$ `/` (Public narrative monograph & problem statement).
  - `Explore` $\rightarrow$ `/explore/pune` (Citywide spatial intelligence instrument).
  - `Projects` $\rightarrow$ `/projects/PROJ-PUNE-2025-BA225D6A` (Canonical municipal decision suite).
- **Deprecated / Removed from Navbar:**
  - `[ 01 / OVERVIEW ]` decorative numbering $\rightarrow$ Removed.
  - `H3 RES-9 | AOI: 4194` system diagnostics $\rightarrow$ Removed to contextual map controls.
  - `[ PUNE: 2025 ]` telemetry badge $\rightarrow$ Removed.

---

## 3. SIMPLIFIED LANDING PAGE (`/`)

The landing page is an **editorial introduction**, not a technical audit console. It introduces the metropolitan dilemma and provides an immediate bridge into the spatial instrument.

```text
+----------------------------------------------------------------------------------------------------+
| CLIMORA                       Overview     Explore     Projects                                   |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|    Turning planetary observations into fundable urban interventions.                               |
|                                                                                                    |
|    A mathematical decision-support instrument for municipal heat resilience in Pune, India.        |
|                                                                                                    |
|    [ Explore Pune ]      [ View project ]                                                          |
|                                                                                                    |
|    ────────────────────────────────────────────────────────────────────────────────────────────    |
|                                                                                                    |
|    5-year thermal baseline       Priority footprint       Planned intervention     Modeled capital |
|    46.36°C                       28 H3 cells              2,695 trees              ₹9.99M          |
|    Observed                      Derived                  Modeled                  Modeled         |
|                                                                                                    |
|    ────────────────────────────────────────────────────────────────────────────────────────────    |
|                                                                                                    |
|    The Decision Process                                                                            |
|                                                                                                    |
|    Satellite Observation ──► Spatial Risk ──► Optimized Intervention ──► Municipal Tender         |
|    Landsat 8/9 TIRS          H3 Hexagons      2,695 Street Trees         ₹10M Budget Envelope      |
|                                                                                                    |
|    ────────────────────────────────────────────────────────────────────────────────────────────    |
|                                                                                                    |
|    Pune Municipal Demonstration                                                                    |
|    PROJ-PUNE-2025-BA225D6A                                                                         |
|                                                                                                    |
|    A targeted ₹10M roadside canopy intervention protecting 118,941 residents                       |
|    across eastern industrial heat corridors.                                                       |
|                                                                                                    |
|    [ View project prospectus → ]                                                                   |
|                                                                                                    |
|    ────────────────────────────────────────────────────────────────────────────────────────────    |
|                                                                                                    |
|    CLIMORA · Planetary climate intelligence for municipal decision-making                          |
|    USGS Landsat · ESA Sentinel-2 · WorldPop · OpenStreetMap · Uber H3 DGGS                         |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

### Deprecated from Landing Page:
- Latitude / Longitude coordinates in hero.
- Raw EPSG projection codes (`EPSG:32643`, `EPSG:4326`).
- Section numbering (`01 /`, `02 /`, `03 /`).
- Long paragraphs explaining every statistical derivation.
- Checksums, solver runtime, and candidate pair statistics.

---

## 4. SIMPLIFIED SPATIAL INSTRUMENT (`/explore/pune`)

The spatial instrument allows the map to dominate the screen without distracting control-room furniture.

### 4.1 Layout Architecture:
```text
+----------------------------------------------------------------------------------------------------+
| CLIMORA                       Overview     Explore     Projects                                   |
+-----------------------------------------------------------------------------------+----------------+
|                                                                                   | [Alt+T: Table] |
|                                                                                   |                |
|                                                                                   | Active metric  |
|                                                                                   | Surface temp   |
|                                                                                   | 46.69°C        |
|                                                                                   |                |
|                        FULL-SCREEN SPATIAL CANVAS                                 | [•] Thermal    |
|                        (Interactive Uber H3 Mesh)                                 | [ ] Exposure   |
|                                                                                   | [ ] Risk       |
|                                                                                   |                |
|                         [ 28 Prioritized Cells ]                                  | [x] Footprint  |
|                                                                                   |                |
|                                                                                   +────────────────+
|                                                                                   | Selected cell  |
|                                                                                   | 89608850003ffff|
|                                                                                   | 46.69°C        |
|                                                                                   | Observed       |
|                                                                                   |                |
|                                                                                   | 110 trees      |
|                                                                                   | ₹405,000       |
|                                                                                   | Modeled        |
|                                                                                   |                |
|                                                                                   | [View details→]|
+-----------------------------------------------------------------------------------+----------------+
| Pune Municipal Area · Landsat 8 TIRS · Apr 19, 2025                                                |
+----------------------------------------------------------------------------------------------------+
```

### 4.2 Key Changes & Reductions:
- **Telemetry Footer Strip Removed:** Banned the heavy bottom bar (`METRIC: LST_2025 | SENSOR: LANDSAT-8 TIRS | DOY: 109 | CLOUD: 0.0% | ALT+T: TABLE`).
- **Clean Map Metadata:** Replaced by a single understated textual line in the lower-left corner: `Pune Municipal Area · Landsat 8 TIRS · Apr 19, 2025`.
- **Integrated Metric Controls:** Layer toggles (`Thermal`, `Exposure`, `Risk`) and the project footprint toggle are grouped into a clean, floating panel on the upper-right.
- **Sparse Selection Card:** When a cell is clicked, a minimalist floating card confirms the selection without immediately occluding the screen. Clicking `View details` opens the deep inspector drawer.

---

## 5. SIMPLIFIED CELL INSPECTOR

The inspector drawer slides in from the right (420px width) only when the user requests deeper inquiry. It answers four progressive questions cleanly:

```text
+---------------------------------------------------------------------------+
| Selected area                                                     [ Close ]|
+---------------------------------------------------------------------------+
| H3 cell                                                                   |
| 89608850003ffff                                                           |
| 9.86 hectares                                                             |
|                                                                           |
| Surface temperature                                                       |
| 46.69°C                                                                   |
| Observed · Landsat 8, Apr 19, 2025                                        |
|                                                                           |
| Climate risk score                                                        |
| 0.2345                                                                    |
| Modeled · Spatial index                                                   |
|                                                                           |
| In-scope population                                                       |
| 4,281                                                                     |
| Observed · WorldPop 2020                                                  |
|                                                                           |
| ───────────────────────────────────────────────────────────────────────── |
|                                                                           |
| Proposed intervention                                                     |
|                                                                           |
| 110 street trees                                                          |
| Modeled · 15.0m roadside interval                                         |
|                                                                           |
| ₹405,000                                                                  |
| Modeled capital requirement                                               |
|                                                                           |
| ───────────────────────────────────────────────────────────────────────── |
|                                                                           |
| Evidence                                                                  |
|                                                                           |
| Baseline mean LST       46.36°C           Derived (5-year pre-monsoon)    |
| Thermal anomaly         +0.33°C           Derived                         |
| Vegetation index        0.082             Observed (Canopy deficit)       |
| Built-up index          0.241             Observed (High thermal mass)    |
| Spatial correlation     High-High         Derived (Hotspot cluster)       |
|                                                                           |
| ───────────────────────────────────────────────────────────────────────── |
|                                                                           |
| View technical provenance →                                               |
|                                                                           |
+---------------------------------------------------------------------------+
```

### Deprecated / Removed from Drawer:
- `ZONE 1`, `ZONE 2`, `ZONE 3`, etc. zone labels.
- `LEVEL 1`, `LEVEL 2` progressive disclosure labels.
- Unratified municipal ward names (e.g. `Ward 14 - Hadapsar Industrial Belt` removed because statutory ward geometry is unratified).
- Raw SHA-256 hashes and solver internal execution parameters (moved behind `View technical provenance →`).
- Formulation identifiers (`F-15`, `F-22`, `F-24`, `F-25.1`) removed from primary lines.

---

## 6. SIMPLIFIED PROJECT OVERVIEW (`/projects/:id`)

The project overview is an **investment decision briefing**. Capital and physical scope dominate; secondary metrics support quietly without creating a wall of cards.

```text
+----------------------------------------------------------------------------------------------------+
| CLIMORA                       Overview     Explore     Projects                                   |
+----------------------------------------------------------------------------------------------------+
| Pune Urban Heat Island Mitigation & Street Canopy Initiative                                       |
| PROJ-PUNE-2025-BA225D6A · Proposed                                                                 |
+----------------------------------------------------------------------------------------------------+
| Overview     Allocation     Baseline     Budget     Verification     Provenance                    |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|    ₹9,992,500                                                                                      |
|    Total modeled capital expenditure                                                               |
|    Modeled · Under ₹10,000,000 municipal budget                                                    |
|                                                                                                    |
|    ────────────────────────────────────────────────────────────────────────────────────────────    |
|                                                                                                    |
|    Physical scope                Prioritized area              Beneficiary population              |
|    2,695 street trees            28 H3 cells                   118,941 residents                   |
|    Modeled                       Derived                       Observed                            |
|                                                                                                    |
|    Municipal budget              Remaining slack               Objective score                     |
|    ₹10,000,000                   ₹7,500                        0.106048                            |
|    Statutory envelope            Retained surplus              Modeled objective reduction         |
|                                                                                                    |
|    ────────────────────────────────────────────────────────────────────────────────────────────    |
|                                                                                                    |
|    Municipal Sanction                                                                              |
|    Standing Committee approval required to transition project from PROPOSED to FUNDED.             |
|                                                                                                    |
|    Sanction order: [ PMC-RESILIENCE-2025-084           ]                                           |
|    Approved budget: ₹10,000,000 INR                                                                |
|                                                                                                    |
|    [ Sanction project & issue tender ]                                                             |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

### Structural Improvements:
- **Capital Dominates:** ₹9,992,500 is rendered in large, quiet typography rather than competing in a 6-card grid.
- **Clean Two-Tier Structure:** Physical scope and geography take precedence; statutory budget and unallocated slack follow.
- **Objective Score Disclaimed Elegantly:** Labeled simply as *"Modeled objective reduction"*; tooltip explains: *"Mathematical objective achieved under the ₹10M formulation; not a percentage cooling claim."*

---

## 7. SIMPLIFIED PROJECT TABS

All numerical prefixes (`01 /`, `02 /`, etc.) are permanently removed.

### Tab Navigation:
`Overview     Allocation     Baseline     Budget     Verification     Provenance`

### 7.1 Allocation View:
- Combines the 28-cell spatial footprint with a clean, uncrowded table.
- Columns: `H3 cell`, `Street trees`, `Direct cost`, `Mobilization`, `Total cost`.
- Governed immutability: Table shows a subtle lock indicator: `Canonical allocation is immutable`. Direct edits are disallowed; users can click `[ Propose revision ]` to branch an auditable proposal.

### 7.2 Baseline View:
- Displays multi-year thermal and biophysical evidence across the 28 prioritized cells.
- Hierarchy: Surface temperature $\rightarrow$ Baseline mean $\rightarrow$ Thermal anomaly $\rightarrow$ Canopy cover (NDVI) $\rightarrow$ Built-up index (NDBI).

### 7.3 Budget View:
- Presented as an institutional memorandum.
- Three primary figures: **Budget Envelope** (₹10,000,000), **Allocated Capital** (₹9,992,500), **Unallocated Slack** (₹7,500).
- Breakdown:
  - Direct tree procurement (2,695 $\times$ ₹3,500 = ₹9,432,500).
  - Cell mobilization (28 $\times$ ₹20,000 = ₹560,000).

### 7.4 Verification View:
- Clear lifecycle state progression: `Proposed` $\rightarrow$ `Funded` $\rightarrow$ `Implementing` $\rightarrow$ `Implemented` $\rightarrow$ `Monitoring` $\rightarrow$ `Verified`.
- **Honest Verification Gate:**
  - Status: `Not yet verified`.
  - Measured empirical cooling: `—` (Awaiting post-implementation Landsat overpasses).
  - Difference-in-Differences status: `Planned`.
  - Zero celebratory green badges; unverified projects do not display artificial success graphics.

---

## 8. TRUTH-LAYER PRESENTATION: SUBTLE & UNMISTAKABLE

Truth layers are communicated via refined typography, muted tints, and clean metadata rather than mechanical badges attached to every metric.

```text
+----------------------------------------------------------------------------------------------------+
|                                REVISED TRUTH-LAYER VOCABULARY                                      |
+------------------+-----------------------+---------------------+-----------------------------------+
| LAYER            | TYPOGRAPHY & CHIP     | TONAL ACCENT        | TYPICAL CONTEXT                   |
+------------------+-----------------------+---------------------+-----------------------------------+
| Observed         | Neutral small chip    | Muted Stone (10%)   | Landsat 8 LST, WorldPop, Sentinel |
| Derived          | Neutral small chip    | Slate Blue (10%)    | 5-Yr mean, anomaly, Moran's I     |
| Modeled          | Italic or dashed chip | Warm Amber (10%)    | MILP allocation, CapEx, Risk      |
| Not yet verified | Quarantined chip      | Neutral Grey (10%)  | Empirical cooling, causal impact  |
+------------------+-----------------------+---------------------+-----------------------------------+
```

### Examples of Quiet In-Situ Application:
- **Observed Metric:**
  `46.69°C`  
  `Observed · Landsat 8, Apr 19, 2025`
- **Modeled Metric:**
  `₹9,992,500`  
  `Modeled · Canonical optimization allocation`
- **Unverified Metric:**
  `Measured cooling: —`  
  `Not yet verified · Requires post-deployment satellite overpass`

> [!IMPORTANT]
> **MODELED $\neq$ VERIFIED:** Modeled projections always carry the amber qualifier *"Modeled"* or *"Scenario estimate"*. The word *"Verified"* is never applied to prospective simulations.

---

## 9. TECHNICAL DISCLOSURE & PROVENANCE STRATEGY

Technical metadata is organized into a four-tier disclosure hierarchy:

```
    LEVEL A: DECISION          Immediately visible (e.g. ₹9.99M CapEx, 2,695 trees, 28 cells)
           │
           ▼  [ Click "View details" ]
    LEVEL B: EVIDENCE          Visible in drawer/view (e.g. 46.69°C LST, 0.082 NDVI, 4,281 pop)
           │
           ▼  [ Click "Expand methodology" ]
    LEVEL C: TECHNICAL DETAIL  Expanded in drawer (e.g. 5-yr baseline window, tree spacing: 15.0m)
           │
           ▼  [ Click "View technical provenance →" ]
    LEVEL D: FORENSIC AUDIT    Dedicated Provenance View / Modal:
                               - Full SHA-256 Parquet digests
                               - HiGHS MILP runtime (70.13s) & candidate pairs (7,115)
                               - Formulation references (F-19 to F-28)
                               - QA_PIXEL bit masks & radiometric calibration constants
```

---

## 10. RESPONSIVE BEHAVIOR

- **Desktop (1440 $\times$ 900 & wider):** Clean split layout. Map dominates 70% of the canvas; the right inspector drawer is 420px fixed width.
- **Laptop (1366 $\times$ 768):** Map is 100% width. Inspector drawer slides in as an overlay, with a 15% map dimming shader.
- **Tablet (1024 $\times$ 768):** Minimal navigation. Contextual inspector opens as a 50% split pane.
- **Mobile (390 $\times$ 844):** Full-screen map with floating metric selector. When a cell is tapped, a **Draggable Bottom Sheet** slides up:
  - *Collapsed (84px):* Shows Cell ID, Surface Temp (46.69°C), and Proposed Trees (110).
  - *Expanded (80% height):* Full scrollable evidence and intervention breakdown.

---

## 11. ACCESSIBILITY & USABILITY

- **Keyboard Navigation:** Full tab order through navigation, map view controls, and data tables.
- **Accessible Data Table Alternative (`Alt+T`):** On `/explore/pune`, pressing `Alt+T` immediately replaces the WebGL spatial mesh with a semantic, screen-reader-friendly HTML5 data table of the 28 prioritized cells.
- **Color Independence:** No quantitative status relies solely on color. Every metric includes explicit textual classification (`Observed`, `Modeled`, `Not yet verified`).
- **Contrast Ratios:** All text achieves minimum 4.5:1 contrast against light and dark surfaces (7:1 for primary headings and values).
- **Reduced Motion:** When `prefers-reduced-motion: reduce` is enabled, all drawer slides and camera pans become instantaneous cuts.

---

## 12. ANTI-CLAUDISH DESIGN COMPLIANCE

To guarantee that the product feels like a real, institutional tool rather than a generic design-system template, every screen must satisfy the **Seven Quality Tests**:

```
+----------------------------------------------------------------------------------------------------+
|                                    ANTI-CLAUDISH AUDIT CHECKLIST                                   |
+------------------------------------------------------------------------------------+---------------+
| TEST QUESTION                                                                      | STATUS        |
+------------------------------------------------------------------------------------+---------------+
| 1. If all badges were removed, would the screen still communicate the decision?    | YES (PASS)    |
| 2. Are any numbers present simply because they look technical?                     | NO  (PASS)    |
| 3. Are any badges repeating information already obvious from typography/layout?    | NO  (PASS)    |
| 4. Does the screen resemble a real product rather than a design-system showcase?   | YES (PASS)    |
| 5. Is the map visually dominant when spatial analysis is the purpose?              | YES (PASS)    |
| 6. Can an executive understand the primary message within 5 seconds?               | YES (PASS)    |
| 7. Could removing 20% of the visible UI improve the screen?                        | DONE (PASS)   |
+------------------------------------------------------------------------------------+---------------+
```

---

## 13. DEPRECATED & REMOVED VISUAL ELEMENTS LEDGER

The following visual elements from earlier drafts are **permanently removed**:

1. **All Numbered Section Headings:** Banned `01 /`, `02 /`, `03 /`, `04 /`, `05 /`, `06 /` across navbar, tabs, cards, and sections.
2. **Persistent Bottom Telemetry HUD:** Banned the noisy footer strip (`METRIC | SENSOR | DOY | CLOUD | ALT+T`).
3. **Navbar Diagnostic Badges:** Banned `H3 RES-9 | AOI: 4194` and `PUNE: 2025` from persistent navigation.
4. **Mechanical Badge Overload:** Banned appending `[ OBSERVED | Landsat 8 TIRS DOY 109 ]` to every single metric line.
5. **Prominent Formulation Numbering:** Banned displaying `F-19`, `F-22`, `F-24` in primary UI views.
6. **Decorative Mathematical Symbols:** Banned `Σ` and Greek glyphs from normal cards and buttons.
7. **Unratified Ward Labels:** Banned displaying `Ward 14 - Hadapsar Industrial Belt` as authoritative.
8. **Equal 6-Card Metric Walls:** Banned identical card grids in favor of strong typographical hierarchy.
9. **Celebratory Green Success Badges on Unverified Projects:** Banned fake verification UI.

---

## 14. UPSTREAM CONTRACT CORRECTIONS

The wireframes strictly incorporate the following factual corrections:

1. **Current-State Satellite Platform:** Authoritative 2025 observation is **Landsat 8 OLI/TIRS-1** (`LC08_L2SP_147047_20250419_02_T1`) on **DOY 109** (April 19, 2025). Day of Year 105 is the target center of the window.
2. **Roadside Tree Spacing:** The canonical engineering assumption is **15.0m interval** along rights-of-way (not 10m).
3. **Statutory Ward Geometry:** Municipal ward boundaries remain unratified display context; H3 Resolution 9 is the sole optimization topology.
4. **Synthetic Data Quarantine:** Payloads bearing `DEMO_ONLY_SYNTHETIC_MRV_DATA` are rejected by verification gates with HTTP 422.
5. **Verification State:** Remains strictly `null` / `Not yet verified` at the proposal stage.

---

## 15. FINAL DESIGN DECISION REGISTER

| Decision Area | Status | Governance Rationale |
| :--- | :--- | :--- |
| **Primary Navigation** | **FROZEN** | `CLIMORA     Overview     Explore     Projects` (Minimalist, zero telemetry). |
| **Numbering Pattern** | **DEPRECATED** | Removed all `01 /`, `02 /`, etc. from tabs, cards, and headings. |
| **Telemetry HUD** | **DEPRECATED** | Persistent bottom footer strip eliminated; replaced by quiet map metadata. |
| **Typography System** | **RATIFIED** | Newsreader (Display Serif) + Geist Sans (UI Grotesk) + Geist Mono (Tabular Numbers). |
| **Color System** | **RATIFIED** | Deep Basalt, Calcified Sandstone, Mineral Paper, Terracotta, Botanical Sage, Acid Lime (<0.5%). |
| **Truth-Layer UI** | **RATIFIED** | Subdued in-situ labels: Observed, Derived, Modeled, Not yet verified. Modeled $\neq$ Verified. |
| **Provenance Strategy**| **RATIFIED** | Forensic depth on demand via dedicated tab/drawer; zero hash clutter by default. |
| **Tree Spacing** | **RECTIFIED** | Corrected to 15.0m canonical interval. |
| **2025 Sensor Attribution**| **RECTIFIED** | Corrected to Landsat 8 TIRS DOY 109. |
| **Canonical Constants**| **FROZEN** | Pune ₹10M budget, ₹9,992,500 CapEx, ₹7,500 slack, 28 cells, 2,695 trees, 118,941 pop. |

---

## CONCLUSION

Phase 2C.2R successfully strips away visual noise and artificial technical decoration, leaving an **authoritative, quiet, and consequential climate decision instrument**.

The system is ready for **Phase 2C.3 (Visual Prototype & Interaction Validation)**.
No frontend code, React components, Tailwind styling, or visual code shall be written until Phase 2C.3 signoff.
