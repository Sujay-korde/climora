# CLIMORA — Phase 1B: Risk Target, Label Governance & Modeling Strategy

**Document Version:** 1.0.0  
**Phase:** Phase 1B (Analytical Architecture & Decision Gate)  
**Status:** **RATIFIED & FROZEN**  
**Truth-Layer Classification:** Architecture Specification  

---

## 1. Executive Summary & Core Principle

A central finding of the Phase 1B architectural audit is that **no defensible, geo-located ground-truth labels for heat-related mortality, morbidity, or economic loss exist at parcel, ward, or neighborhood scale for the city of Pune**.

Consequently, in strict compliance with CLIMORA Governance Rules (§2.1, §2.2, §18, §19):
1. **CLIMORA strictly prohibits the fabrication of pseudo-labels** (e.g., thresholding LST and calling it "true heatstroke occurrence").
2. **CLIMORA strictly prohibits claiming supervised machine-learning "accuracy" or "F1 scores"** against ungrounded synthetic targets.
3. **CLIMORA adopts the IPCC AR6 Risk Framework (Hazard × Exposure × Vulnerability)** combined with **Unsupervised Thermal Anomaly Detection, Spatial Persistence Analysis, and Multi-Objective Spatial Optimization**.

---

## 2. Evaluation of Candidate Target Strategies

| Strategy | Methodology | Empirical Feasibility in Pune | Scientific Justification | Architecture Decision |
| :--- | :--- | :--- | :--- | :--- |
| **Strategy A: Observed Heat Proxy** | Single physical proxy (e.g., peak summer LST $> 45^\circ\text{C}$) used directly as risk. | Feasible via calibrated Landsat/Sentinel observations. | Conflates physical *hazard* with *risk*. An uninhabited basalt quarry has extreme LST but zero human risk; a crowded tin-roof informal settlement may have slightly lower LST but acute disaster risk. | **REJECTED AS PRIMARY RISK** (Retained strictly as Hazard Layer) |
| **Strategy B: IPCC AR6 Composite Risk Framework** | Disaggregated multi-dimensional formulation: $\text{Risk} = f(\text{Hazard}, \text{Exposure}, \text{Vulnerability})$. | High. Feasible using validated satellite observations (Hazard), WorldPop & OSM (Exposure), and biophysical/built proxies (Vulnerability). | Internationally recognized gold standard (IPCC Working Group II Sixth Assessment Report). Fully transparent, auditable, and preserves modular component truth. | **ADOPTED AS CANONICAL CLIMATE RISK FRAMEWORK** |
| **Strategy C: Supervised ML Target** | Training a classifier/regressor (Random Forest, XGBoost) to predict historical heat casualties. | **IMPOSSIBLE WITHOUT FABRICATING DATA.** | Indian Integrated Disease Surveillance Programme (IDSP) publishes heat deaths aggregated only to District level (Pune District = 15,643 km², covering 15 administrative tehsils and 10 million people), with severe diagnostic under-reporting and zero spatial coordinates. | **STRICTLY REJECTED & PROHIBITED** |
| **Strategy D: Unsupervised / Anomaly & Optimization Framework** | Microclimatic hotspot clustering, temporal anomaly tracking ($z$-score relative to 2021–2025 baseline), and Pareto spatial optimization for cooling interventions. | High. Completely grounded in validated physical observations and spatial topology. | Eliminates label hallucination. Enables robust, deterministic ranking of priority intervention sites and scenario evaluation without false ML claims. | **ADOPTED FOR DOWNSTREAM ANALYTICAL OPTIMIZATION** |

---

## 3. Label Governance Audit

To ensure complete scientific integrity, an exhaustive empirical audit of potential label sources was conducted:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LABEL GOVERNANCE AUDIT                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Question: Do ground-truth heat disaster labels exist for Pune?           │
│    Answer: NO.                                                              │
│                                                                             │
│ 2. Available Data Sources Audited:                                          │
│    • National Crime Records Bureau (NCRB) "Accidental Deaths & Suicides":    │
│      - Aggregation: State level (Maharashtra) or broad metropolitan city    │
│      - Granularity: Annual tabular counts                                   │
│      - Geospatial coordinates: None                                         │
│      - Causality verification: Coroner heatstroke attribution is notorious   │
│        for severe under-reporting (often coded as cardiovascular collapse). │
│    • Integrated Disease Surveillance Programme (IDSP):                      │
│      - Aggregation: District level (Pune Rural + PMC + PCMC combined)       │
│      - Granularity: Weekly alerts, rarely reporting ward-level incidents    │
│      - Coordinates: None                                                    │
│    • 108 Emergency Ambulance Dispatch (MEMS):                               │
│      - Granularity: Call pick-up points exist, but medical call symptom     │
│        codes ("unconscious", "dizziness", "fever") do not isolate thermal   │
│        stress from underlying infectious or chronic etiologies.             │
│                                                                             │
│ 3. Governance Mandate:                                                      │
│    CLIMORA will NEVER fabricate synthetic 0/1 labels to train a classifier.│
│    Supervised ML accuracy metrics (AUC, ROC, F1) on synthetic labels are a  │
│    scientific malpractice that produces a false sense of certainty.        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Disaggregated Risk Definitions: Hazard, Exposure, Vulnerability

In strict accordance with Section 20 of the Phase 1B mandate, CLIMORA enforces complete separation among **Hazard**, **Exposure**, and **Vulnerability**.

### 4.1 Hazard ($\mathcal{H}$) — Physical Climate Condition
*Hazard* refers exclusively to the physical, thermal, and meteorological stress conditions observed or derived from validated sensor platforms.
- **Primary Metrics:**
  - Absolute Peak Surface Temperature: $\text{LST}_{\text{current}}$ ($^\circ\text{C}$, 2025 observation from 2025-04-19 DOY 109)
  - Historical Baseline Surface Temperature: $\text{LST}_{\text{baseline}}$ ($^\circ\text{C}$, 2021–2025 mean across valid baseline years)
  - Thermal Anomaly: $\Delta \text{LST} = \text{LST}_{2025} - \text{LST}_{\text{baseline}}$ ($^\circ\text{C}$ or $z$-score)
  - Heat Persistence: Fraction of valid baseline years where cell LST exceeded the city-wide 75th percentile ($P_{75}$)
  - Extreme LST Recurrence: Count of valid baseline years where cell zonal mean LST $\ge 45.0^\circ\text{C}$ (**CLIMORA methodological surface temperature threshold**; explicitly not an epidemiological human heat-health threshold)
- **Truth Layer:** Strictly `OBSERVED` or `DERIVED`.

### 4.2 Exposure ($\mathcal{E}$) — Human & Asset Presence
*Exposure* refers strictly to the inventory of human lives, critical municipal assets, and public infrastructure located within the hazard zone. Exposure carries zero assumption of vulnerability.
- **Primary Metrics:**
  - Estimated Human Population Count: $P_{\text{cell}}$ (persons, from WorldPop 2020 UN-adjusted dasymetric sum conservation)
  - Population Density: $D_{\text{pop}}$ (persons / km²)
  - Public Infrastructure Count: Hospitals, clinics, schools, universities (OSM points/polygons from `data/raw/osm/pune/public_infrastructure.geojson`)
  - Road Network Length: Total length of primary, secondary, and residential roads (OSM meters from `data/raw/osm/pune/road_network.geojson`)
- **Truth Layer:** Strictly `OBSERVED` or `DERIVED`.

### 4.3 Biophysical & Structural Susceptibility ($\mathcal{V}$) vs Socioeconomic Vulnerability
*Susceptibility* in CLIMORA represents the physical and biophysical properties of the urban fabric that amplify localized heat accumulation, conditioned by surface properties and lack of natural cooling buffers.
- **Biophysical & Structural Proxies (Observed/Derived):**
  1. **Vegetative Deficit ($1 - \text{NDVI}$):**
     - *Interpretation:* Absence of photosynthesizing canopy cover indicates lack of evapotranspirative cooling capacity.
     - *Limitation:* Does not measure indoor air conditioning, building insulation, or household socioeconomic status.
  2. **Built-Up Density / Thermal Mass ($\text{NDBI}$):**
     - *Interpretation:* High impervious surface fraction indicates heat-trapping structural thermal mass and nocturnal heat retention.
     - *Limitation:* Does not differentiate high-income insulated high-rises from uninsulated metal-roof informal settlements.
  3. **Water Body Buffer Distance / Coverage:**
     - *Interpretation:* Proximity to open water bodies providing local microclimatic buffers.
- **CRITICAL GOVERNANCE MANDATE — Vulnerability vs Susceptibility:**
  - CLIMORA strictly designates this layer as **Biophysical and Structural Susceptibility**.
  - CLIMORA will **NEVER** claim that NDVI or NDBI represent socioeconomic human poverty or demographic vulnerability.
  - True **Socioeconomic Vulnerability** and **Adaptive Capacity** (income, age demographics, comorbidities, housing tenure, access to municipal water) require statutory ward-level household surveys (e.g. Slum Rehabilitation Authority surveys or Census micro-data). Because such parcel-level demographic data is currently unavailable, it is explicitly classified as **UNAVAILABLE / PENDING STATUTORY SURVEYS**.
- **Truth Layer:** Strictly `DERIVED`.

---

## 5. Climate Risk Formulation (IPCC Conceptual Framework vs CLIMORA Implementation)

### 5.1 Attribution Distinction
- **IPCC AR6 Conceptual Framework:** IPCC Working Group II defines Risk as the intersection of physical Hazard, human/asset Exposure, and Vulnerability ($\text{Risk} = f(\text{Hazard}, \text{Exposure}, \text{Vulnerability})$).
- **CLIMORA Methodological Implementation:** CLIMORA implements this conceptual framework through a specific multiplicative power-law aggregation:

$$\text{Risk}_i = \mathcal{H}_i^{\alpha} \times \mathcal{E}_i^{\beta} \times \mathcal{V}_i^{\gamma}$$

This equation is a **CLIMORA methodological implementation**, NOT an IPCC-prescribed formula. It is governed under [`data/manifests/risk_parameter_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/risk_parameter_contract.json).

### 5.2 Exponent Parameters $\alpha, \beta, \gamma$ Governance
- $\mathcal{H}_i \in [0, 1]$: Min-Max normalized Hazard Index across valid cells.
- $\mathcal{E}_i \in [0, 1]$: Min-Max normalized Exposure Index (Population + Infrastructure).
- $\mathcal{V}_i \in [0, 1]$: Min-Max normalized Biophysical & Structural Susceptibility Index ($1 - \text{NDVI}$, $\text{NDBI}$).
- **Parameter Status:** Exponents $\alpha, \beta, \gamma$ have default values of `1.0`, `1.0`, `1.0` (equal geometric weighting) and an allowed range of `[0.0, 3.0]`. They are explicitly classified as **`PENDING_METHODOLOGICAL_CALIBRATION`** and are subject to sensitivity analysis in future modeling phases.

### 5.3 Why Multiplicative Rather Than Additive?
In linear additive formulas ($\text{Risk} = w_1 \mathcal{H} + w_2 \mathcal{E} + w_3 \mathcal{V}$), an unpopulated quarry with extreme hazard ($\mathcal{H} = 1.0$) and zero population ($\mathcal{E} = 0$) receives a misleadingly high risk score ($0.33$). Multiplicative aggregation enforces the fundamental risk axiom:
$$\text{If Exposure } \mathcal{E} = 0 \implies \text{Human Climate Risk } = 0$$

### 5.4 Preserving Component Transparency
To prevent the loss of actionable truth, CLIMORA requires that the analytical database and API **always persist and expose the disaggregated components ($\mathcal{H}_i, \mathcal{E}_i, \mathcal{V}_i$) alongside any composite index**. Municipal planners must be able to filter by "High Hazard + High Population" independently of composite scores.

---

## 6. Downstream Modeling & Optimization Strategy (Phase 2+)

Because supervised classification is scientifically unviable, Phase 2+ modeling will be executed under two rigorous, defensible paradigms:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GOVERNED DOWNSTREAM MODELING PARADIGM                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ PARADIGM 1: MULTI-TEMPORAL ANOMALY & PERSISTENCE RANKING                    │
│ • Unsupervised clustering (e.g., HDBSCAN / Spatial DBSCAN) on H3 mesh to   │
│   isolate contiguous urban heat islands with spatial significance.          │
│ • Local Moran's I (LISA) to classify cells into:                            │
│   - High-High: Acute Hotspots (spatially clustered severe heat)             │
│   - High-Low: Spatial Outliers (isolated thermal anomalies)                 │
│   - Low-High: Cool buffers adjacent to hotspots                             │
│   - Low-Low: Resilient cool zones (forests, water bodies)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ PARADIGM 2: MULTI-OBJECTIVE SPATIAL INTERVENTION OPTIMIZATION (MILP)        │
│ • Given an intervention budget (e.g., 200,000 m² cool roofs, 10,000 trees):│
│ • Objective: Maximize total heat risk reduction weighted by population      │
│   $\max \sum_{i} \Delta \mathcal{H}_i(x_i) \times \mathcal{E}_i$            │
│ • Constraints:                                                              │
│   - Available impervious/roof area per H3 cell (parameterized)              │
│   - Budgetary and municipal ward equity constraints                         │
│   - Physical cooling radius constraints (decay across adjacent H3 rings)    │
└─────────────────────────────────────────────────────────────────────────────┘
```

This strategy provides municipal decision-makers with bankable, evidence-backed intervention guidance without inventing ungrounded ML performance statistics.
