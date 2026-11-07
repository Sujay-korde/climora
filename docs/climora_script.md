# CLIMORA Visual Choreography & Video Production Reference
### Master Scene Guide: Camera Paths, UI States, Motion Specs, and On-Screen Telemetry

**Total Duration:** 240 Seconds (04:00 ±2s)  
**Resolution:** 4K UHD (3840×2160) @ 60 FPS  
**Color Profile:** Dark High-Tech Industrial Glass (`#090a0f`, `#12151e`, `#232936`)  
**Typography:** Space Grotesk 700 (Display), Inter (Body), JetBrains Mono Tabular (Data/Metrics)  

---

### SCENE 01: The Unspoken Urban Heat Crisis (00:00 - 00:20)
* **Visual Action:** 3D orthographic descent towards Pune Municipal Corporation (PMC). Thermal radiance shader sweeps across satellite imagery, transitioning from natural RGB into high-contrast Landsat Level-2 Surface Temperature (LST).
* **DOM / UI State:** High-resolution map with glowing boundary overlay (`data/aoi/pune.geojson`).
* **Camera Path:** Orbital push-in (scale `0.88 -> 1.04`), slight pitch angle 12° easing into overhead nadir.
* **Keyframe Easing:** `cubic-bezier(0.16, 1, 0.3, 1)`
* **On-Screen HUD:**
  - `PUNE MUNICIPAL CORPORATION (PMC)` · `312.11 KM² · 5,011,229 RESIDENTS`
  - `PEAK SUMMER SURFACE TEMP: 46.36°C` `[OBSERVED]`
* **SFX:** Sub-bass drone hum (`sfx_sub_boom`), gentle atmospheric wind.

---

### SCENE 02: The Institutional Failure Spiral (00:20 - 00:45)
* **Visual Action:** Visual splits into 3 glass diagnostic cards representing systemic municipal failure modes. Cards animate with staggered spring entrance, then subtly disintegrate under high thermal stress.
* **Visual Layout:**
  - Card 1: `SPATIAL DISCONNECT` — Raw Satellite Pixels vs Heterogeneous Municipal Wards.
  - Card 2: `CAPITAL SCARCITY` — Blind Ward Politics & Unoptimized Quotas.
  - Card 3: `ACCOUNTABILITY VACUUM` — Zero Empirical Post-Deployment Verification.
* **Camera Path:** Slow horizontal tracking shot across the 3 glass cards, snapping to center on "We have a decision problem."
* **SFX:** Dull mechanical tape stop on chasm reveal, subtle heartbeat pulse.

---

### SCENE 03: Introducing Climora & 6-Stage Mesh Lineage (00:45 - 01:10)
* **Visual Action:** Brand reveal: **CLIMORA**. 3,181 Uber H3 Res-9 hexagons cascade onto the Pune terrain in a radial wavefront from the city center outward.
* **Architecture Flowchart (Hero Visual):** 6 Figma-styled glass nodes light up sequentially with traveling luminous energy pulses:
  1. `1. EARTH SENSING` (Landsat 8/9 LST, Sentinel-2 NDVI/NDBI, WorldPop)
  2. `2. SPATIAL MESH` (Uber H3 Res-9, 3,181 Hexagons, ~0.0986 km²)
  3. `3. RISK SYNTHESIS` (IPCC AR6 $H \times E \times V$, Zero-Exposure Axiom)
  4. `4. HiGHS SOLVER` (Mixed-Integer Linear Programming, ₹5L → ₹1 Cr)
  5. `5. CEDAR GOVERNANCE` (5 Personas, ABAC, Negative Anti-Tamper)
  6. `6. EMPIRICAL MRV` (Difference-in-Differences, Matched Controls)
* **Camera Path:** Isometric pan across the flowchart, zooming into the H3 mesh node.
* **SFX:** 110 BPM ambient-electronic bed kicks in (`climora_110bpm_music_bed.wav`), tactile micro-clicks on node connections.

---

### SCENE 04: Mathematical Formulation & Operations Research (01:10 - 01:30)
* **Visual Action:** Mathematical equations emerge with crisp syntax rendering:
  - Zero-Exposure Axiom: $E_i = 0 \implies R_i = 0$
  - Multi-Objective MILP Formulation: $\max \sum (R_i \cdot \Delta T_i) - \text{Mobilization Penalties}$
* **DOM / UI State:** High-speed matrix visualization showing discrete integer lot sizing and road capacity constraints settling into global Pareto optimality.
* **SFX:** Electronic data chitter, resonant riser (`sfx_riser`) building into live demo.

---

### SCENE 05: Live Geospatial Explorer & Truth Lineage (01:30 - 02:00)
* **Visual Action:** Direct screencast of `/explore/pune` on live app. Simulated DOM cursor glides across layers:
  1. Thermal (LST 2025: ≤40°C → 46°C → ≥52°C)
  2. Exposure (WorldPop 2020: 0 → 4,500 people/cell)
  3. Climate Risk ($H \times E \times V$)
* **Target Cell Click:** Cursor hovers and clicks priority hexagon `89608850003ffff`.
* **Sidebar Animation:** `CellInspector` drawer slides open smoothly from right.
* **On-Screen Displayed Values:**
  - `H3 Cell: 89608850003ffff`
  - `Baseline Risk: 0.2222` `[DERIVED]`
  - `LST 2025: 47.06°C` `[OBSERVED]`
  - `Population: 4,757 residents` `[DERIVED]`
  - `Planned Allocation: 76 Shade Trees` `[MODELED]`
* **SFX:** Smooth drawer slide, tactile UI click (`sfx_click`).

---

### SCENE 06: Portfolio Optimizer & Monotonic Capital Presets (02:00 - 02:30)
* **Visual Action:** Screencast of `/optimizer`. Cursor clicks preset button: `₹1 Crore (Benchmark) — Canonical municipal investment`.
* **Interactive Solver Trigger:** Cursor clicks `Execute HiGHS Optimization →`.
* **Dynamic Feedback:**
  - Solver status badge switches to `OPTIMAL` (`HiGHS branch-and-cut`).
  - Exactly 28 priority hexagons illuminate with high-contrast emerald glow across Pune.
  - Multi-objective metric cards update:
    * `Allocated Capital: ₹99,92,500` (Slack: ₹7,500 under ₹10,000,000 ceiling)
    * `Trees Planned: 2,695 shade trees` (15m spacing)
    * `Citizens Protected: 118,941 residents`
    * `Treated Footprint: 28 cells (0.88% of PMC)`
* **SFX:** Numerical count-up ticker sound, solver convergence chime (`sfx_chime`).

---

### SCENE 07: Cedar Policy Engine & Immutable Governance (02:30 - 03:00)
* **Visual Action:** Screencast of `/projects/PROJ-PUNE-2025-BA225D6A`.
* **Workflow:**
  1. Cursor opens `CedarGovernancePanel`.
  2. Active persona selector switches from `urban_planner_lead` (Pooja Deshmukh) to `pmc_commissioner` (Dr. Rajesh Patil).
  3. Cursor clicks `Generate Tender Brief 📄`.
  4. Project Brief Modal appears with SHA-256 cryptographic provenance hash: `BA225D6A...`.
  5. Negative policy test: cursor hovers over immutable baseline; Cedar tooltips indicate `FORBIDDEN: Negative Anti-Tamper Policy active`.
* **SFX:** Official authority stamp effect (`sfx_stamp`), subtle digital echo.

---

### SCENE 08: Tripartite MRV & Honest Empirical Limits (03:00 - 03:25)
* **Visual Action:** Screencast of `/mrv`.
* **Scientific Honesty Walkthrough:**
  - Header displays: `EMPIRICAL EVIDENCE & AUDIT FRAMEWORK · Pending Post-Deployment Observation`.
  - Tripartite status pills: `PREDICTED: 2,695 Trees` | `OBSERVED: Satellite Scheduled` | `VERIFIED: Not Yet Started`.
  - Graphic highlights detectability limits: Single-cell thermal noise floor (6.91°C) vs 2-cell cluster aggregation requirement.
* **Camera Path:** Gentle zoom into the Difference-in-Differences matched control comparison graphic.
* **SFX:** Soft data sweep tone, serene atmospheric pad.

---

### SCENE 09: Scalability Across Global South Metropolises (03:25 - 03:45)
* **Visual Action:** 3D map zooms out from Pune and pans across India and the Global South. Neon H3 hexagonal meshes illuminate over Delhi, Hyderabad, Cairo, and Jakarta.
* **Telemetry Overlay:**
  - `CITY-AGNOSTIC DATA PIPELINE`
  - `48-HOUR ONBOARDING SLA`
  - `OPEN DATA LAKE ARCHITECTURE (LOCAL / AWS S3)`
* **SFX:** Deep stereo panning sweep, energetic rhythm lift.

---

### SCENE 10: The Crescendo & Final Call to Action (03:45 - 04:00)
* **Visual Action:** Rapid 0.5s visual recap montage (Hex mesh, MILP solver, Cedar seal, green street canopies) converging into the Climora brand logo.
* **Final Center Lockup:**
  - **CLIMORA** (Gradient glow: `#06b6d4` → `#f97316` → `#10b981`)
  - *"Turning planetary observations into fundable urban interventions."*
  - `Live Prototype: http://127.0.0.1:3000`
  - `Target: Novex 2026 Climate Tech Evaluation`
  - `VIT Pune · Department of CSE (AIML)`
* **SFX:** Full musical crescendo resolving into a sustained resonant piano chord.

