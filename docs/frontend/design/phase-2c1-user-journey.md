# CLIMORA — CANONICAL USER JOURNEY & HACKATHON DEMO WALKTHROUGH
## Phase 2C.1 Companion Architecture Document

**Document Version:** 1.0.0  
**Phase:** Phase 2C.1 — Information Architecture & User Journey Design  
**Target Document Path:** `docs/frontend/design/phase-2c1-user-journey.md`  
**Parent Document:** [`docs/frontend/design/phase-2c1-information-architecture.md`](file:///c:/Users/lenovo/climora/docs/frontend/design/phase-2c1-information-architecture.md)  
**Governing Roles:** Principal Product Designer, Senior UX Architect, Lead Product Strategist  
**Status:** **RATIFIED CANONICAL USER JOURNEY SPECIFICATION**  
**Demonstration Scenario:** Pune Urban Heat Mitigation & Street Canopy Initiative (`PROJ-PUNE-2025-BA225D6A`)  

---

## 1. PURPOSE & DESIGN INTENT

This document details the complete end-to-end user experience of CLIMORA from initial public discovery to post-implementation satellite verification. It serves two vital functions:
1. **The Comprehensive Persona Narrative:** Explains the psychological, institutional, and spatial progression of the Primary User (Dr. Aris Thorne, Municipal Resilience Director) as they evaluate, prioritize, budget, sanction, and verify urban cooling interventions.
2. **The Canonical 3–5 Minute Hackathon Demonstration Script:** Provides an exact beat-by-beat performance guide for presenting CLIMORA to judges, venture evaluators, and climate scientists, ensuring maximum dramatic impact, intellectual clarity, and technical defensibility.

---

## 2. THE CANONICAL END-TO-END JOURNEY (DR. THORNES'S PATHWAY)

```
       DISCOVER                  EXPLORE & DIAGNOSE             PRIORITIZE & ALLOCATE
  [ The Climate Reality ]    [ 5-Yr Landsat Heat Surface ]    [ H3 Spatial Autocorrelation ]
           │                               │                               │
           ▼                               ▼                               ▼
    Problem Context               Anomalous H3 Cells             28 Priority Hexagons
    (Pune: 46.36°C mean)         (Hadapsar Corridor)           (2,695 Street Trees)
           │                               │                               │
           └───────────────────────────────┴───────────────────────────────┘
                                           │
                                           ▼
                               SANCTION & IMPLEMENT
                         [ Project PROJ-PUNE-2025-BA225D6A ]
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
                ₹10M Municipal Budget                 Contractor Logging
               (₹9.99M CapEx / ₹7.5k Slack)          (Zero Deviation / F-27.2)
                        │                                     │
                        └──────────────────┬──────────────────┘
                                           │
                                           ▼
                                 FUTURE VERIFICATION
                            [ Satellite Difference Gate ]
                            (Quarantined / Non-Synthetic)
```

---

## 3. DETAILED JOURNEY STAGES

### STAGE 1: DISCOVER (The Institutional Dilemma)
- **User Mental State:** Overwhelmed by rising heat wave complaints in eastern Pune; tasked with allocating a ₹10M municipal resilience grant; skeptical of generic GIS portals that offer no actionable investment advice.
- **Entry Point:** Lands on `https://climora.network/` (`/`).
- **Experience:**
  - Reads the calm, editorial headline: *"Turning Planetary Observations into Fundable Urban Interventions."*
  - Observes that CLIMORA is not another academic paper or colorful dashboard, but a decision instrument.
  - Reviews the three-column diagnostic: The Thermal Reality (46.36°C baseline mean), The Human Burden (118,941 exposed citizens), and The Capital Gap (ad-hoc spending vs spatial optimization).
- **Cognitive Shift:** From *"Climate change is an intractable, vague crisis"* to *"Here is a spatial instrument designed to allocate capital to specific street corridors."*
- **Action Trigger:** Clicks `[ Explore Pune Spatial Evidence ]`.

---

### STAGE 2: EXPLORE (Planetary Signal over Pune)
- **User Mental State:** Exploring the city to understand where the heat anomaly is concentrated.
- **Route:** `/explore/pune`.
- **Experience:**
  - The map loads smoothly into the Pune Municipal Corporation boundary (AOI: 4194).
  - Floating status chip confirms: `[ H3 RES-9 MESH | 5-YEAR APRIL PRE-MONSOON COMPOSITE ]`.
  - The base thermal layer renders in a restrained sandstone-to-terracotta palette representing Land Surface Temperature ($LST$).
  - Dr. Thorne instantly identifies that the eastern industrial corridors (Hadapsar, Mundhwa, Kharadi) are blazing hot (> 46.5°C), while western hilly ridges (Vetal Tekdi, Kothrud) are significantly cooler.
- **Cognitive Shift:** The heat island is not uniform; it is concentrated along distinct urban morphology corridors.
- **Action Trigger:** Toggles `[ Human Exposure ]` layer.

---

### STAGE 3: DIAGNOSE (The Collision of Heat and Humans)
- **User Mental State:** Heat alone does not equal risk; where are vulnerable people living without tree shade?
- **Route:** `/explore/pune` (Exposure & Biophysical Mode).
- **Experience:**
  - Overlays WorldPop 2020 dasymetric population density and Sentinel-2 NDVI canopy cover.
  - The visual contrast is striking: High-density residential settlements in Hadapsar coincide with an extreme vegetative canopy deficit ($\text{NDVI} < 0.10$, indicating almost total absence of street trees).
- **Cognitive Shift:** Risk is biophysical and demographic; interventions must be placed where heat and human density collide.
- **Action Trigger:** Toggles `[ Hotspot Clusters (LISA Moran's I) ]`.

---

### STAGE 4: PRIORITIZE (Spatial Autocorrelation Hotspots)
- **User Mental State:** Which specific neighborhoods should receive funding first?
- **Route:** `/explore/pune` (Hotspot Cluster Mode).
- **Experience:**
  - The map renders Anselin Local Moran's $I$ spatial autocorrelation clusters ($F\text{-}23.1$).
  - High-High priority clusters illuminate in deep copper across eastern Pune.
  - Dr. Thorne clicks on an individual H3 hexagon: `89608850003ffff` in the Hadapsar corridor.
  - The **Contextual Cell Inspector Drawer** slides in from the right:
    - Observed 2025 LST: `46.69°C` (`OBSERVED`, Landsat-9 TIRS DOY 105).
    - 5-Year Baseline Mean: `46.36°C` (`DERIVED`).
    - Canopy Deficit: $\text{NDVI} = 0.082$ (Severely Deficient).
    - In-Scope Population: `4,281 residents`.
    - Proposed Allocation: `110 Street Trees` (CapEx: `₹405,000`).
- **Cognitive Shift:** This isn't an arbitrary boundary; this specific hexagon represents an empirical priority backed by spatial statistics.
- **Action Trigger:** Clicks `[ Assemble Fundable Project ]`.

---

### STAGE 5: ALLOCATE (The ₹10M Capital Blueprint)
- **User Mental State:** Ready to see the municipal investment proposal. How many trees? What does it cost? Does it fit our ₹10M grant envelope?
- **Route:** `/projects/PROJ-PUNE-2025-BA225D6A`.
- **Experience:**
  - The camera smoothly frames the **28 Canonical Treated Cells**.
  - The Executive Banner presents the exact financial parameters:
    - **Total Modeled CapEx:** ₹9,992,500
    - **Municipal Budget Ceiling:** ₹10,000,000
    - **Unallocated Budget Slack:** ₹7,500
    - **Beneficiary Population:** 118,941 residents
    - **Physical Deployment:** 2,695 street trees
    - **Objective Reduction Score:** 0.106048 (explicitly tagged as modeled aggregate risk-objective reduction under formulation $F\text{-}24$).
  - Dr. Thorne opens the **Allocation Blueprint** tab. Every single one of the 28 cells is listed with its allocated tree count (ranging from 50 to 110 trees) and transparent unit costs (₹3,500/tree planting + ₹20,000/cell mobilization).
  - Dr. Thorne attempts to edit a row. The system displays a firm governance notice: *"Canonical optimization is immutable. Direct cell mutations are prohibited. To test alternatives, branch an auditable revision."*
- **Cognitive Shift:** This is institutional-grade finance. Every rupee is accounted for, and the baseline cannot be tampered with.
- **Action Trigger:** Clicks `[ Sanction Project & Issue Tenders ]`.

---

### STAGE 6: FUND (Municipal State Transition)
- **User Mental State:** Committing public capital; creating legal accountability.
- **Route:** `/projects/PROJ-PUNE-2025-BA225D6A` (Sanction Dialog).
- **Experience:**
  - Dr. Thorne enters Municipal Sanction Order ID: `PMC-CLIMATE-2025-084` and approved budget: `₹10,000,000`.
  - Submits the transition via `POST /projects/{id}/transition`.
  - The lifecycle state badge transitions from `PROPOSED` to `FUNDED` with a clean amber confirmation pill.
  - An official, timestamped municipal sanction record is appended to the project history.
- **Cognitive Shift:** The project is now an active public works mandate, ready for contractor mobilization.
- **Action Trigger:** Opens `[ Implementation & MRV ]` tab.

---

### STAGE 7: IMPLEMENT (Physical Contractor Deployment)
- **User Mental State:** Tracking contractors in the field during the planting season (Q4 2025–Q2 2026).
- **Route:** `/projects/PROJ-PUNE-2025-BA225D6A` (Implementation Tab).
- **Experience:**
  - The contractor logging interface opens (`POST /projects/{id}/implementation-events`).
  - Forestry contractor logs completion for Cell `89608850003ffff`: 110 indigenous saplings planted with 2m tree guards, completion date: `2026-04-15`, attached signed delivery report URI.
  - The system evaluates operational deviation ($F\text{-}27.2$):
    - Planned: `110` | Implemented: `110` | Deviation: `0.00%`.
- **Cognitive Shift:** Real-world physical progress is synchronized directly with the digital spatial unit.
- **Action Trigger:** Navigates to the Verification Gateway.

---

### STAGE 8: VERIFY (Scientific Integrity & Post-Deployment Gate)
- **User Mental State:** Can we claim carbon credits or cool-city certification right now?
- **Route:** `/projects/PROJ-PUNE-2025-BA225D6A` (Verification Gateway).
- **Experience:**
  - The verification card prominently displays:
    - Status: `UNOBSERVED / NOT YET VERIFIED`
    - Causal Evaluation: `Difference-in-Differences (DID) PLANNED / NOT_YET_EXECUTABLE`
    - Measured Empirical Cooling: `null`
  - Dr. Thorne inspects why verification is blocked:
    1. Trees require a 24-month canopy maturation period.
    2. Empirical overpass must occur during the April peak-summer window (DOY 95–115).
    3. Satellite overpass must pass 100% QA screening with $\le 5\%$ cloud contamination.
  - The platform actively rejects synthetic fixtures and optical sensor mismatch (Sentinel-2 MSI for thermal).
- **Cognitive Shift:** Profound trust. CLIMORA will never allow a city to greenwash or claim unverified success.

---

## 4. CANONICAL HACKATHON DEMO WALKTHROUGH (3–5 MINUTES)

This script is engineered for maximum judge impact, narrative momentum, and scientific authority.

```
+----------------------------------------------------------------------------------------------------+
|                               THE 11-BEAT HACKATHON DEMO ARC                                       |
|                                                                                                    |
|  BEAT 01: The Problem Thesis       BEAT 02: Pune Thermal Signal        BEAT 03: Human Exposure     |
|  (0:00 - 0:30)                     (0:30 - 1:00)                       (1:00 - 1:30)               |
|                                                                                                    |
|  BEAT 04: Spatial Hotspots         BEAT 05: Single-Cell Drill-Down     BEAT 06: Fundable Assembly  |
|  (1:30 - 2:00)                     (2:00 - 2:30)                       (2:30 - 3:00)               |
|                                                                                                    |
|  BEAT 07: Allocation Blueprint     BEAT 08: Municipal Sanction         BEAT 09: Contractor MRV     |
|  (3:00 - 3:30)                     (3:30 - 4:00)                       (4:00 - 4:30)               |
|                                                                                                    |
|  BEAT 10: Cryptographic Provenance BEAT 11: The Closing Stance                                     |
|  (4:30 - 4:50)                     (4:50 - 5:00)                                                   |
+----------------------------------------------------------------------------------------------------+
```

---

### BEAT 1: The Problem Thesis (0:00 – 0:30)
- **Screen:** `/` (Public Monograph Landing)
- **Speaker Action:** Stand tall, speak calmly. Do not rush.
- **Spoken Script:**
  > *"Every year, climate hackathons produce dozens of colorful heat maps. But in the real world, municipal commissioners don't need another heat map—they need a fundable project proposal. Right now, billions of dollars in green bonds and municipal resilience capital sit idle because cities cannot translate satellite rasters into bankable street-level interventions. This is CLIMORA. CLIMORA turns planetary climate observations into fundable, verified urban infrastructure projects."*
- **Visual Action:** Scroll smoothly past the editorial diagnostic. Point to the three pillars: Thermal Reality, Human Exposure, Capital Allocation. Click `[ Explore Pune Spatial Evidence ]`.

---

### BEAT 2: Pune Thermal Signal (0:30 – 1:00)
- **Screen:** `/explore/pune` (Thermal Baseline View)
- **Spoken Script:**
  > *"We start with Pune, Maharashtra—a rapidly urbanizing megacity facing severe pre-monsoon heat stress. What you are seeing is not a simulation. This is the canonical 5-year peak-summer baseline derived from USGS Landsat 8 and 9 thermal infrared observations. The baseline surface temperature across the city peaks at 46.36°C. But notice the spatial variance: the western green ridges are cool, while the eastern industrial and residential belts absorb immense solar radiation."*
- **Visual Action:** Hover over Pune's central and eastern corridors. Show the coordinate HUD updating dynamically.

---

### BEAT 3: Human Exposure & Canopy Deficit (1:00 – 1:30)
- **Screen:** `/explore/pune` (Exposure View)
- **Spoken Script:**
  > *"Heat alone is not a disaster until it strikes human beings. In CLIMORA, we overlay WorldPop dasymetric population density and Sentinel-2 vegetation indices onto an invariant Uber H3 Resolution 9 mesh. Look at the eastern Hadapsar corridor: high population density, high built-up thermal mass, and a severe tree canopy deficit with NDVI below 0.10. These residents have zero natural shade protection."*
- **Visual Action:** Toggle the Exposure overlay. The screen reveals dense residential areas colliding with barren asphalt corridors.

---

### BEAT 4: Spatial Autocorrelation Hotspots (1:30 – 2:00)
- **Screen:** `/explore/pune` (Hotspots LISA View)
- **Spoken Script:**
  > *"Rather than letting politicians pick project sites, CLIMORA applies rigorous spatial statistics. Using Anselin Local Moran's I autocorrelation, the platform identifies statistically significant High-High spatial risk clusters where p is less than 0.01. This is where municipal capital will produce the greatest marginal cooling impact."*
- **Visual Action:** Switch view mode to Hotspots. The map highlights the clustered priority zones in deep copper.

---

### BEAT 5: Single-Cell Drill-Down (2:00 – 2:30)
- **Screen:** `/explore/pune` (Contextual Cell Inspector Open)
- **Spoken Script:**
  > *"Let's inspect a single H3 hexagon in Hadapsar: cell `89608850003ffff`. Notice the progressive disclosure in the side drawer. Level 1: What is the action? Deploy 110 street trees for ₹405,000. Level 2: Observed evidence: 46.69°C surface temperature from Landsat-9 TIRS DOY 105, and an extreme NDVI deficit. Level 3: 4,281 exposed residents. Every single hexagon in the city has this exact forensic profile."*
- **Visual Action:** Click cell `89608850003ffff`. The right drawer slides in smoothly. Highlight the `[ OBSERVED ]` and `[ DERIVED ]` truth badges.

---

### BEAT 6: The Fundable Project Moment (2:30 – 3:00)
- **Screen:** Transition to `/projects/PROJ-PUNE-2025-BA225D6A`
- **Spoken Script:**
  > *"Now comes the core breakthrough: turning this evidence into a bankable municipal project. When we click 'Assemble Fundable Project', CLIMORA runs our Mixed-Integer Linear Programming solver under a strict ₹10,000,000 municipal budget ceiling. The result is Project `PROJ-PUNE-2025-BA225D6A`. Exactly 28 H3 cells selected. Exactly 2,695 roadside canopy trees. Modeled CapEx: ₹9,992,500. Remaining unallocated slack: exactly ₹7,500. Beneficiary population: 118,941 residents."*
- **Visual Action:** Click `[ Assemble Fundable Project ]`. The camera frames the 28 cells. The Executive Proposal View materializes with the ₹10M budget breakdown.

---

### BEAT 7: Allocation Immutability (3:00 – 3:30)
- **Screen:** `/projects/:id` (Allocation Blueprint Tab)
- **Spoken Script:**
  > *"Let's open the Allocation Blueprint. Here is the cell-by-cell planting ledger: 110 trees here, 95 trees there, at ₹3,500 per sapling plus ₹20,000 mobilization per cell. Now watch what happens if I try to tamper with these numbers. The API immediately rejects it with HTTP 405. The canonical optimization is legally immutable. If a municipal planner wants to adjust numbers, they must branch an auditable, transparent revision. No backroom alterations."*
- **Visual Action:** Click on a cell quantity field. Show the immutable tooltip and the `[ Branch Proposed Revision ]` action.

---

### BEAT 8: Municipal Sanction Transition (3:30 – 4:00)
- **Screen:** `/projects/:id` (State Transition Dialog)
- **Spoken Script:**
  > *"With the Standing Committee's approval, the Municipal Commissioner can now sanction the initiative. We enter Sanction Order ID `PMC-CLIMATE-2025-084` with the approved ₹10M budget. The backend state machine executes the transition: `PROPOSED` becomes `FUNDED`. The project is now an official municipal tender."*
- **Visual Action:** Submit the transition. The badge turns from stone to active amber `FUNDED`.

---

### BEAT 9: Contractor Implementation & MRV Gate (4:00 – 4:30)
- **Screen:** `/projects/:id` (MRV & Implementation Tab)
- **Spoken Script:**
  > *"During the planting phase, forestry contractors log physical deployments cell-by-cell. Here, 110 trees are logged in Hadapsar with a signed delivery invoice. But here is CLIMORA's ultimate scientific honesty: notice that 'Verified Impact' remains locked as `UNOBSERVED / NOT YET VERIFIED`. We strictly prohibit claiming simulated cooling as verified empirical impact. Verification requires post-planting Landsat thermal overpasses during the April DOY 95–115 window, passing 100% QA screening with zero synthetic data."*
- **Visual Action:** Show the logged implementation event and the locked `UNOBSERVED` verification badge. Highlight the Difference-in-Differences `PLANNED` state.

---

### BEAT 10: Cryptographic Provenance (4:30 – 4:50)
- **Screen:** Provenance Modal
- **Spoken Script:**
  > *"Every single number in this proposal is traceable to canonical Parquet datasets verified by SHA-256 digests. From Landsat Level-2 radiometry to the HiGHS linear solver runtime of 70.1 seconds, there is zero black-box guessing."*
- **Visual Action:** Open the Lineage Modal. Highlight the SHA-256 checksums and formulation $F\text{-}24$.

---

### BEAT 11: The Closing Stance (4:50 – 5:00)
- **Screen:** Full Overview Stance
- **Spoken Script:**
  > *"This is how we close the climate-capital gap: not with generic dashboards, but with serious, spatial, bankable infrastructure intelligence. That is CLIMORA. Thank you."*
- **Visual Action:** Hold the final screen. Welcome judge questions.

---

## 5. DEMO RISK MITIGATION & CONTINGENCY PLAYBOOK

To guarantee a flawless presentation during live hackathon judging, the following contingencies are designed into the UX:

1. **Network Latency or Slow API:**
   - *Mitigation:* The frontend implements deterministic local caching via `services/cache.py`. All canonical GET queries (`/projects`, `/allocation`, `/baseline`) resolve in under 5ms from local memory.
2. **Judge Questions Formulations:**
   - *Action:* Press `Alt+P` or click `[ View Provenance ]` on any screen to immediately reveal the Mathematical Register ($F\text{-}19$ to $F\text{-}28$) and SHA-256 checksums.
3. **Screen Resolution Variations:**
   - *Action:* The responsive layout seamlessly adapts to 13-inch laptop screens (1280px) and wide projection displays (1920px+) using the fluid 12-column grid.

---

## 6. ARCHITECTURAL RATIFICATION

This document stands ratified alongside [`docs/frontend/design/phase-2c1-information-architecture.md`](file:///c:/Users/lenovo/climora/docs/frontend/design/phase-2c1-information-architecture.md). It completely specifies the human and narrative journey that will govern Phase 2C.2 wireframing.
