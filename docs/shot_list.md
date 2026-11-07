# CLIMORA Master Production Shot List
### Phase 0 Reconnaissance & Recording Blueprint (Exact 240 Seconds / 10 Scenes)

**Target Viewport:** 2560×1440 @ 60 FPS (Browser Zoom: 110%, Dark Theme)  
**Host Application:** `http://127.0.0.1:3000` (Frontend) · `http://127.0.0.1:8000` (Backend API)  

---

| Scene ID | Duration | Route / Target | Key Selectors & DOM Events | Expected On-Screen Values | Discrepancies vs Script / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SCENE 01** | `20s` (0:00-0:20) | `/` (Overview) + 3D Satellite | `.font-tabular`, hero header, Pune boundary layer | `46.36°C` [OBSERVED], `312.11 km²`, `5.01M Residents` | Script matches live app 100%. Camera transitions from orbital globe to hero metric strip. |
| **SCENE 02** | `25s` (0:20-0:45) | Motion Graphics Chasm | Remotion Glass Cards (`SpatialDisconnect`, `CapitalScarcity`, `MRVVacuum`) | `Detection ≠ Capital Allocation`, `Heuristic Allocation`, `Zero Post-Deployment MRV` | Pure motion design scene in Remotion. No live DOM dependency. |
| **SCENE 03** | `25s` (0:45-0:10) | Motion Architecture Flowchart | Remotion 6-Node Flowchart (`Ingestion`, `H3Mesh`, `IPCC`, `HiGHS`, `Cedar`, `DiD`) | `3,181 H3 Res-9 Cells`, `~0.0986 km²`, `R = H × E × V`, `Zero-Exposure Axiom` | Flowchart constructed with traveling light pulses and spring entrance (damping 18, stiffness 120). |
| **SCENE 04** | `20s` (1:10-1:30) | Mathematical Visualizer | Remotion Math Formulas (`eq6_zero_exp.svg`, `eq9_milp.svg`) | $E_i = 0 \implies R_i = 0$, Semi-continuous Lot Sizing, Budget Caps | SVGs pulled directly from `docs/assets/formulas/`. |
| **SCENE 05** | `30s` (1:30-2:00) | `/explore/pune` | `button:has-text("Thermal")`, `button:has-text("Exposure")`, `button:has-text("Risk")`, polygon click `89608850003ffff`, `#cell-inspector` drawer | `89608850003ffff`, `LST: 47.06°C`, `Pop: 4,757`, `Risk: 0.2222`, `76 Trees Planned` | **RECONCILED:** Prompt draft referenced `8960144d...`; live app has canonical cell `89608850003ffff`. |
| **SCENE 06** | `30s` (2:00-2:30) | `/optimizer` | `button:has-text("₹1 Crore (Benchmark)")`, `button:has-text("Execute HiGHS Optimization")`, metric summary cards | `₹99,92,500 Allocated`, `28 Cells Treated (0.88%)`, `2,695 Trees`, `118,941 Citizens Protected`, `Slack: ₹7,500` | Exact live numbers match the HiGHS solver output. |
| **SCENE 07** | `30s` (2:30-3:00) | `/projects/PROJ-PUNE-2025-BA225D6A` | `select#actor-select` (change to `pmc_commissioner`), `button:has-text("Generate Tender Brief")`, `.modal-brief`, `.hash-sha256` | `Dr. Rajesh Patil`, `Municipal Commissioner`, `State: SANCTIONED`, `SHA-256 Provenance` | Client-side navigation via React Router to avoid Vite proxy intercept. |
| **SCENE 08** | `25s` (3:00-3:25) | `/mrv` | `.mrv-tripartite-strip`, `#did-chart-container`, `.detectability-limit-card` | `PREDICTED: 2,695 Trees`, `OBSERVED: Post-Monsoon Scheduled`, `STATUS: PLANNED / NOT_YET_EXECUTABLE` | **RECONCILED:** Accurately states post-deployment DiD is pending; highlights honest 6.91°C single-cell noise floor. |
| **SCENE 09** | `20s` (3:25-3:45) | Motion Graphics Megacities | Remotion 3D Global Mesh (Pune → Delhi, Hyderabad, Cairo, Jakarta) | `City-Agnostic Ingestion`, `48h Deployment SLA`, `Local / S3 Hybrid Data Lake` | Remotion vector animation with glowing hexagonal network. |
| **SCENE 10** | `15s` (3:45-4:00) | Brand Climax & Lockup | Remotion Final Card (`#climora-logo`, QR code, GitHub repo, live URL) | `CLIMORA`, `Turning planetary observations into fundable urban interventions`, `climora.app` | Crescendo resolving into final piano decay at 240.0s. |

---

### Key Recording Execution Parameters
- **Capture Resolution:** 2560×1440 (scaled cleanly to 3840×2160 in Remotion composition)
- **Frame Rate:** Constant 60 FPS
- **Simulated Mouse Cursor:** Custom injected DOM cursor with Bézier arc interpolation, ease-out curve, and 80ms click-ripple expansion.
- **Timing Synchronization:** Each live screencast emits `scene_XX.events.json` recording the exact millisecond of clicks, modal openings, and number settles to drive Remotion camera zooms and Truth Badge entrance animations.

