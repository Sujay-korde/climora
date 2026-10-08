# CLIMORA — PHASE 1D: HAZARD–EXPOSURE–SUSCEPTIBILITY CONSTRUCTION GATE REPORT

**Document Version:** 1.0.0  
**Phase:** Phase 1D Scientific Construction & Mathematical Audit Gate  
**Contract Companion:** [`data/manifests/canonical_hev_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/canonical_hev_contract.json)  
**Primary Parquet Asset:** [`data/processed/hev/canonical_hev_components.parquet`](file:///c:/Users/lenovo/climora/data/processed/hev/canonical_hev_components.parquet)  
**Status:** **PHASE 1D — PASSED**  
**Lead Roles:** Senior Scientific Architect, Geospatial ML Engineer, Mathematical Model Auditor, and Forensic Repository Engineer  
**Date:** 2026-10-02  

---

## 1. Executive Decision

```text
================================================================================
FINAL DECISION: PHASE 1D — PASSED
================================================================================
```

The CLIMORA Hazard–Exposure–Susceptibility Construction Gate has **PASSED** all twelve forensic gate criteria.

1. **Independent Dimension Construction:** $H_i$, $E_i$, and $V_i$ were constructed independently across distinct, non-overlapping input feature vectors.
2. **Zero Cross-Contamination:** No demographic features enter Hazard or Susceptibility; no satellite spectral features enter Exposure.
3. **Strict PMC Ward Decoupling:** H/E/V construction operates strictly on the Uber H3 Resolution 9 analytical mesh (3,181 cells). The KMeans `ward_id` column is treated as a deferred downstream administrative placeholder and was **not used** in any analytical computation. Mathematical invariance to ward assignment was empirically proven.
4. **No Socioeconomic Vulnerability Fabrication:** Susceptibility $V_i$ is strictly restricted to **biophysical and structural susceptibility** ($1 - \text{NDVI}'$, $\text{NDBI}'$, $1 - A_{\text{green}}'$). Zero synthetic demographic, poverty, income, or clinical health features were introduced.
5. **Rigorous Missing Data Governance:** The temporal validity rule ($K_{\text{valid}, i} \ge 4$) was strictly maintained. Disqualified cells ($N = 68$) evaluate to `NaN` for $H_i$ and $V_i$, with `overall_hev_eligibility = False`. Zero silent imputation was performed.
6. **Formulation Register Traceability:** All equations adhere verbatim to ratified Formulations F-19, F-20, and F-21 in [`docs/science/climora-mathematical-formulation-register.md`](file:///c:/Users/lenovo/climora/docs/science/climora-mathematical-formulation-register.md).
7. **Explicit Weight Governance:** All component weights are explicitly classified as `CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)` and are not represented as calibrated physical constants.
8. **Monotonic Directionality:** All components were audited and verified to possess correct positive directionality (greater physical stress $\implies$ higher score).
9. **No Fabricated Spatial Statistics:** Only empirical distributions and Pearson/Spearman correlations computed directly from the data are reported. No unsupported spatial autocorrelation claims or fabricated Moran's I statistics are made.
10. **Composite Risk Strictly Deferred:** Final composite risk ($\text{Risk}_i = H_i^\alpha E_i^\beta V_i^\gamma$) was **not** computed, preserving the required scientific staging.
11. **Regression Integrity:** All 62 prior unit tests and 12 new Phase 1D tests pass (74/74 green).
12. **Materialized Lineage:** Parquet and contract artifacts were materialized with complete SHA-256 provenance tracking.

---

## 2. Input Lineage & Integrity

The Phase 1D engine consumed the frozen canonical feature matrix:

* **Source File:** [`data/processed/canonical_feature_matrix.parquet`](file:///c:/Users/lenovo/climora/data/processed/canonical_feature_matrix.parquet)
* **SHA-256 Checksum:** `76f344b147b349f3887259f64c97923414c74fd9a97ec679844fb8d9109f7c01`
* **Mesh Resolution:** Uber H3 Resolution 9
* **Total Rows:** 3,181 cells
* **Total Columns:** 57 columns
* **Associated Contracts:**
  * [`data/manifests/canonical_feature_matrix_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/canonical_feature_matrix_contract.json)
  * [`data/manifests/scientific_formulation_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/scientific_formulation_contract.json)
  * [`docs/science/climora-mathematical-formulation-register.md`](file:///c:/Users/lenovo/climora/docs/science/climora-mathematical-formulation-register.md)

No raw data files were modified, and no prior Phase 1A, 1B, 1C, or 1C.1 assets were regenerated.

---

## 3. Hazard Construction ($\mathcal{H}_i$)

### 3.1 Mathematical Formulation (F-19)

$$\mathcal{H}_i = w_{H, 1} \cdot \text{norm\_lst\_2025}_i + w_{H, 2} \cdot \text{norm\_lst\_anomaly}_i + w_{H, 3} \cdot \text{norm\_persistence}_i + w_{H, 4} \cdot \text{norm\_recurrence\_ge45}_i$$

where:
$$w_{H, 1} = 0.25, \quad w_{H, 2} = 0.25, \quad w_{H, 3} = 0.25, \quad w_{H, 4} = 0.25 \quad \left(\sum_{k=1}^4 w_{H, k} = 1.00\right)$$

### 3.2 Component Semantics & Normalization

| Component | Source Column | Physical Role | Normalization Scheme | Weight | Directionality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $\bar{T}_{2025, i}'$ | `norm_lst_2025` | Current pre-monsoon peak summer thermal skin intensity (Landsat 8, April 19, 2025) | Linear min-max ($[31.76^\circ\text{C}, 55.01^\circ\text{C}]$) | 0.25 | Positive (Hotter $\to$ Higher) |
| $\Delta T_{2025, i}'$ | `norm_lst_anomaly` | Acute departure from 5-year multi-annual baseline mean ($\bar{T}_{2025} - \bar{T}_{\text{base}}$) | Linear min-max ($[-3.68^\circ\text{C}, 5.73^\circ\text{C}]$) | 0.25 | Positive (Greater surge $\to$ Higher) |
| $\text{Persistence}_i'$ | `norm_persistence` | Chronic heat retention (frequency of valid years in citywide top quartile $P_{75, t}$) | Dimensionless fraction $[0.0, 1.0]$ | 0.25 | Positive (More persistent $\to$ Higher) |
| $\text{Recurrence}_{45, i}'$ | `norm_recurrence_ge45` | Extreme acute threshold crossing count ($\sum \mathbb{I}(\bar{T}_{i, t} \ge 45.0^\circ\text{C})$) | Linear min-max ($[0, 5]$ years) | 0.25 | Positive (More frequent $\ge 45^\circ\text{C} \to$ Higher) |

### 3.3 Eligibility & Missingness
* **Eligibility Rule:** $K_{\text{valid}, i} \ge 4$.
* **Eligible Cells:** 3,113 cells ($97.86\%$). All components are strictly non-null and finite.
* **Ineligible Cells:** 68 cells ($2.14\%$). Flagged `hazard_eligibility = False`; $\mathcal{H}_i$ is strictly preserved as `NaN`.

### 3.4 Empirical Statistical Distribution (Eligible Mesh $N = 3,113$)

| Component / Composite | Min | Q05 | Q25 | Median | Mean | Q75 | Q95 | Max | Std | Missing ($N=3181$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `norm_lst_2025` | 0.0000 | 0.4226 | 0.5295 | 0.6047 | 0.6166 | 0.7015 | 0.8405 | 1.0000 | 0.1277 | 68 |
| `norm_lst_anomaly` | 0.0000 | 0.2550 | 0.3528 | 0.4070 | 0.4143 | 0.4729 | 0.5834 | 1.0000 | 0.1011 | 68 |
| `norm_persistence` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.2478 | 0.4000 | 1.0000 | 1.0000 | 0.3821 | 68 |
| `norm_recurrence_ge45` | 0.0000 | 0.0000 | 0.2000 | 0.6000 | 0.5627 | 0.8000 | 1.0000 | 1.0000 | 0.3404 | 68 |
| **Hazard Composite ($\mathcal{H}_i$)** | **0.0813** | **0.2112** | **0.3127** | **0.4386** | **0.4604** | **0.6009** | **0.7854** | **0.8856** | **0.1867** | **68** |

### 3.5 Intra-Hazard Pairwise Correlations (Pearson $r$)

| Variable | `norm_lst_2025` | `norm_lst_anomaly` | `norm_persistence` | `norm_recurrence_ge45` | Correlation with $\mathcal{H}_i$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `norm_lst_2025` | 1.0000 | -0.1063 | 0.7976 | 0.8504 | **+0.8712** |
| `norm_lst_anomaly` | -0.1063 | 1.0000 | -0.3372 | -0.3044 | **+0.0911** |
| `norm_persistence` | 0.7976 | -0.3372 | 1.0000 | 0.6429 | **+0.8267** |
| `norm_recurrence_ge45` | 0.8504 | -0.3044 | 0.6429 | 1.0000 | **+0.8778** |

**Forensic Diagnostic Interpretation:**
1. Strong positive correlations exist between 2025 intensity, chronic persistence, and recurrence $\ge 45^\circ\text{C}$ ($r \in [0.64, 0.85]$). This confirms that physical built-surface heat in Pune exhibits strong structural consistency across time.
2. Anomaly exhibits negative correlation with persistence ($r = -0.3372$) and recurrence ($r = -0.3044$). This occurs because chronically overheated urban cores already operate near physiological/thermodynamic saturation ($48-52^\circ\text{C}$) each year, producing moderate anomalies relative to their elevated baselines. Conversely, developing suburban fringes experienced acute thermal surges in 2025. Combining anomaly with persistence and baseline intensity ensures that both **chronic heat islands** and **acute shock zones** are captured.

---

## 4. Exposure Construction ($\mathcal{E}_i$)

### 4.1 Mathematical Formulation (F-20)

$$\mathcal{E}_i = w_{E, 1} \cdot \text{norm\_population}_i + w_{E, 2} \cdot \text{norm\_population\_density}_i + w_{E, 3} \cdot \text{norm\_civic\_infra}_i + w_{E, 4} \cdot \text{norm\_road\_length}_i$$

where:
$$w_{E, 1} = 0.40, \quad w_{E, 2} = 0.30, \quad w_{E, 3} = 0.20, \quad w_{E, 4} = 0.10 \quad \left(\sum_{k=1}^4 w_{E, k} = 1.00\right)$$

### 4.2 Component Semantics & Normalization

| Component | Source Column | Semantic Role | Normalization Scheme | Weight | Directionality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $C_i'$ | `norm_population` | Absolute human demographic presence (WorldPop 2020 mass-conserved) | Linear min-max ($[25.07, 5180.79]$ persons) | 0.40 | Positive (More people $\to$ Higher) |
| $D_i'$ | `norm_population_density` | Human crowding intensity ($C_i / A_i$, where $A_i$ is geodesic $\text{km}^2$) | Linear min-max ($[254.8, 52478.9]\text{ persons/km}^2$) | 0.30 | Positive (Denser $\to$ Higher) |
| $N_{\text{infra}, i}'$ | `norm_civic_infra` | Critical public assets: sum of hospitals, clinics, schools, universities | Linear min-max ($[0, 11]$ facilities) | 0.20 | Positive (More facilities $\to$ Higher) |
| $L_{\text{road}, i}'$ | `norm_road_length` | Transportation lifelines & pedestrian mobility exposure | Linear min-max ($[0.0, 2040.84]$ meters) | 0.10 | Positive (More roads $\to$ Higher) |

### 4.3 Anti-Double-Counting Audit: Population vs Population Density
A critical mathematical audit was performed on the relationship between `norm_population` ($C_i'$) and `norm_population_density` ($D_i'$):
* Empirical correlation: **$r = 1.0000$** ($0.9999996$).
* **Mathematical Cause:** Across all 3,181 H3 Resolution 9 cells within Pune's latitudinal span ($18.43^\circ\text{N} - 18.62^\circ\text{N}$), geodesic cell area $A_i$ varies by only $\pm 0.25\%$ ($0.098367\text{ km}^2$ to $0.098871\text{ km}^2$, mean $0.098629\text{ km}^2$). Because cell area is essentially constant, density $D_i = C_i / A_i$ is a near-perfect linear transformation of count $C_i$.
* **Governance Stance:** In CLIMORA formulation F-20, $C_i$ represents **Absolute Exposure Mass** (the volume of lives at risk), while $D_i$ represents **Spatial Intensity** (evacuation difficulty and vertical density). In an equal-area hexagonal tessellation, this duality results in a combined effective demographic weight of $0.40 + 0.30 = 0.70$.
* This overlap is **intentional by methodological design** and does not cause numerical instability. Per Section 7 of the governance mandate, the formulation is preserved without modification.

### 4.4 Zero-Exposure Audit & Semantics
* **Cells with $E_i = 0.0$:** Exactly **1 cell** (`89608855343ffff`).
* **Lineage Audit of Cell `89608855343ffff`:**
  * `population_2020` = 25.07 (exactly citywide minimum $\implies \text{norm} = 0.0000$)
  * `population_density_2020` = 254.80 (exactly citywide minimum $\implies \text{norm} = 0.0000$)
  * `civic_infra_sum` = 0 facilities ($\implies \text{norm} = 0.0000$)
  * `road_length_m` = 0.00 meters ($\implies \text{norm} = 0.0000$)
  * `green_space_area_m2` = $98,040.42\text{ m}^2$ (unoccupied forested/conserved parcel)
* **Downstream Interpretation:** Under the CLIMORA zero-exposure axiom (Formulation F-22), $\mathcal{E}_i = 0 \implies \text{Risk}_i = 0$. Human heat risk cannot exist where human presence and critical infrastructure are absent.

### 4.5 Empirical Statistical Distribution

| Component / Composite | Min | Q05 | Q25 | Median | Mean | Q75 | Q95 | Max | Std | Missing ($N=3181$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `norm_population` | 0.0000 | 0.0201 | 0.0780 | 0.1999 | 0.3007 | 0.4963 | 0.8056 | 1.0000 | 0.2595 | 0 |
| `norm_population_density` | 0.0000 | 0.0202 | 0.0782 | 0.2003 | 0.3009 | 0.4965 | 0.8068 | 1.0000 | 0.2596 | 0 |
| `norm_civic_infra` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0289 | 0.0000 | 0.1818 | 1.0000 | 0.0827 | 0 |
| `norm_road_length` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0591 | 0.0000 | 0.3474 | 1.0000 | 0.1362 | 0 |
| **Exposure Composite ($\mathcal{E}_i$, All $N=3181$)** | **0.0000** | **0.0146** | **0.0643** | **0.1551** | **0.2222** | **0.3601** | **0.5937** | **0.8086** | **0.1890** | **0** |
| **Exposure Composite ($\mathcal{E}_i$, Eligible $N=3113$)** | **0.0000** | **0.0155** | **0.0663** | **0.1614** | **0.2257** | **0.3645** | **0.5981** | **0.8086** | **0.1893** | **0** |

---

## 5. Biophysical & Structural Susceptibility Construction ($\mathcal{V}_i$)

### 5.1 Mathematical Formulation (F-21)

$$\mathcal{V}_i = w_{V, 1} \cdot \left(1 - \text{norm\_ndvi}_{2025, i}\right) + w_{V, 2} \cdot \text{norm\_ndbi}_{2025, i} + w_{V, 3} \cdot \left(1 - \text{norm\_green\_space}_i\right)$$

where:
$$w_{V, 1} = 0.45, \quad w_{V, 2} = 0.45, \quad w_{V, 3} = 0.10 \quad \left(\sum_{k=1}^3 w_{V, k} = 1.00\right)$$

### 5.2 Mandatory Semantic Boundary Enforcement
> **MANDATORY SCIENTIFIC QUALIFICATION:** In strict compliance with the CLIMORA formulation governance, $\mathcal{V}_i$ represents **biophysical and structural susceptibility**, NOT socioeconomic vulnerability. It quantifies physical surface properties that amplify localized radiant heating (vegetative canopy deficit, dense masonry/asphalt/tin thermal mass, and lack of designated green spaces). It does NOT measure human poverty, household income, caste, age demographics, or adaptive capacity.

### 5.3 Component Semantics & Normalization

| Component | Source Column | Physical Role | Normalization Scheme | Weight | Directionality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $\text{NDVI Deficit}_i'$ | `norm_ndvi_deficit` | Absence of evaporative cooling and shading canopy ($1 - \text{norm}(\text{NDVI}_{2025})$) | Linear min-max ($[0.1027, 0.7523] \to [0.0, 1.0]$) | 0.45 | Positive (Less vegetation $\to$ Higher) |
| $\text{NDBI}_i'$ | `norm_ndbi` | Impervious built-up thermal mass (concrete, masonry, tin, blacktop) | Linear min-max ($[-0.3917, 0.1299] \to [0.0, 1.0]$) | 0.45 | Positive (More built-up $\to$ Higher) |
| $\text{Green Space Deficit}_i'$ | `norm_green_space_deficit` | Absence of gazetted parks, public gardens, or urban forests ($1 - \text{norm}(A_{\text{green}})$) | Linear min-max ($[0.0, 165882.19]\text{ m}^2 \to [0.0, 1.0]$) | 0.10 | Positive (Less park area $\to$ Higher) |

### 5.4 Empirical Statistical Distribution (Eligible Mesh $N = 3,113$)

| Component / Composite | Min | Q05 | Q25 | Median | Mean | Q75 | Q95 | Max | Std | Missing ($N=3181$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `norm_ndvi_deficit` | 0.0000 | 0.4437 | 0.6025 | 0.7121 | 0.6924 | 0.7974 | 0.8831 | 1.0000 | 0.1386 | 68 |
| `norm_ndbi` | 0.0000 | 0.4720 | 0.6240 | 0.7235 | 0.7071 | 0.8020 | 0.9032 | 1.0000 | 0.1331 | 68 |
| `norm_green_space_deficit` | 0.0000 | 0.7124 | 0.9968 | 1.0000 | 0.9618 | 1.0000 | 1.0000 | 1.0000 | 0.1154 | 0 |
| **Susceptibility Composite ($\mathcal{V}_i$)** | **0.0900** | **0.5091** | **0.6509** | **0.7453** | **0.7260** | **0.8155** | **0.8866** | **0.9760** | **0.1189** | **68** |

### 5.5 Intra-Susceptibility Pairwise Correlations (Pearson $r$)

| Variable | `norm_ndvi_deficit` | `norm_ndbi` | `norm_green_space_deficit` | Correlation with $\mathcal{V}_i$ |
| :--- | :---: | :---: | :---: | :---: |
| `norm_ndvi_deficit` | 1.0000 | 0.8249 | 0.2316 | **+0.9238** |
| `norm_ndbi` | 0.8249 | 1.0000 | 0.0160 | **+0.8710** |
| `norm_green_space_deficit` | 0.2316 | 0.0160 | 1.0000 | **+0.3204** |

**Forensic Diagnostic Interpretation:**
1. High correlation between NDVI deficit and NDBI ($r = 0.8249$) reflects the biophysical reality of urban environments: surfaces with dense impervious materials naturally replace vegetative canopy.
2. Low correlation between designated green spaces and spectral canopy deficit ($r = 0.2316$) confirms that OpenStreetMap vector parks capture statutory municipal park boundaries, whereas Landsat NDVI captures all photosynthetic vegetation (including unmapped private residential trees, agricultural plots, and roadside verges). They represent distinct physical aspects of cooling infrastructure.

---

## 6. Weight Governance

All weights applied in Phase 1D are governed as follows:

```text
================================================================================
CLASSIFICATION: CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)
================================================================================
```

The weights:
* Hazard: $w_H = (0.25, 0.25, 0.25, 0.25)$
* Exposure: $w_E = (0.40, 0.30, 0.20, 0.10)$
* Susceptibility: $w_V = (0.45, 0.45, 0.10)$

are **methodological modeling assumptions**, NOT calibrated empirical parameters, machine-learned coefficients, or physical constants.

```text
      ┌──────────────────────────────────────────────┐
      │       Observed Data (Landsat, WorldPop, OSM)  │
      └──────────────────────┬───────────────────────┘
                             │
                             ▼
      ┌──────────────────────────────────────────────┐
      │  Derived Physical Metrics (LST, NDVI, NDBI)  │
      └──────────────────────┬───────────────────────┘
                             │
                             ▼
      ┌──────────────────────────────────────────────┐
      │    Methodological Normalization (Min-Max)    │
      └──────────────────────┬───────────────────────┘
                             │
                             ▼
      ┌──────────────────────────────────────────────┐
      │ Methodological Weights (PENDING_CALIBRATION) │
      └──────────────────────┬───────────────────────┘
                             │
                             ▼
      ┌──────────────────────────────────────────────┐
      │      H_i, E_i, V_i Dimensional Composites    │
      └──────────────────────────────────────────────┘
```

Sensitivity testing across weight envelopes ($[0.1, 0.5]$) is formally registered under Formulation F-28 for future phases.

---

## 7. Missingness & Disqualification Audit

* **Temporal Governance Rule (F-13):** A cell is valid for baseline central tendencies iff $K_{\text{valid}, i} \ge 4$ years with $f_{\text{valid}} \ge 0.70$.
* **Disqualified Cells ($N = 68$, $2.14\%$):**
  * Cell counts by $K_{\text{valid}}$: $K=0$ (26 cells), $K=1$ (10 cells), $K=2$ (10 cells), $K=3$ (22 cells).
  * These cells fall along steep terrain edges (Sinhagad foothills, Katraj Ghat ridge) or water bodies where cloud masking reduced annual clear coverage below $70\%$.
* **Missing Value Policy:**
  * For all 68 disqualified cells, $\mathcal{H}_i = \text{NaN}$ and $\mathcal{V}_i = \text{NaN}$.
  * `hazard_eligibility = False`, `susceptibility_eligibility = False`, `overall_hev_eligibility = False`.
  * **Strict zero-imputation policy:** Values were NOT replaced with zero, mean, median, spatial interpolation, or nearest-neighbor values.

---

## 8. Spatial Diagnostics & Inter-Dimensional Coupling

### 8.1 Inter-Dimensional Correlation Analysis (Eligible Mesh $N = 3,113$)

```text
Pearson Correlation Matrix:
             H_i          E_i          V_i
  H_i     1.000000    -0.404811    +0.758153
  E_i    -0.404811     1.000000    -0.299164
  V_i    +0.758153    -0.299164     1.000000

Spearman Rank Correlation Matrix:
             H_i          E_i          V_i
  H_i     1.000000    -0.438788    +0.793440
  E_i    -0.438788     1.000000    -0.378681
  V_i    +0.793440    -0.378681     1.000000
```

### 8.2 Forensic Interpretation of Cross-Dimensional Patterns
1. **$H_i$ vs $V_i$ ($r = +0.758$ / $\rho = +0.793$):**
   * There is a strong positive correlation between thermal hazard and biophysical susceptibility.
   * This is physically intuitive: built impervious surfaces lacking tree canopy (high $V_i$) absorb shortwave solar radiation and emit intense sensible heat, driving elevated surface temperatures, chronic persistence, and acute threshold crossings (high $H_i$).
   * However, they remain conceptually and mathematically decoupled: $H_i$ represents the multi-temporal thermal dynamic response, whereas $V_i$ represents the underlying land cover fabric.
2. **$E_i$ vs $H_i$ ($r = -0.405$ / $\rho = -0.439$):**
   * Moderate negative correlation. In Pune, the highest pre-monsoon radiant surface temperatures ($> 50^\circ\text{C}$) occur in unshaded peripheral basalt plateaus, quarry ridges, and industrial tin-roof complexes where resident nighttime population density is low. Conversely, high-density residential cores (Kasba Peth, Shivajinagar) feature older masonry structures, street shading, or moderate vegetation that keep surface skin temperatures slightly below barren rock extremes.
3. **$E_i$ vs $V_i$ ($r = -0.299$ / $\rho = -0.379$):**
   * Weak to moderate negative correlation. Vegetated residential cantonment zones and established wards possess moderate canopy cover compared to peripheral industrial zones.

### 8.3 Governance on Spatial Statistics
In accordance with Section 19.8 of the mandate:
> Only actual computed statistics are reported. No unsupported spatial autocorrelation claims, Moran's I values, LISA hotspot statistics, or clustering significance scores are invented or claimed in this Phase 1D report. Formal spatial autocorrelation and hotspot detection belong strictly to Phase 1E (Formulation F-23).

---

## 9. PMC Ward Decoupling Enforcement

### 9.1 Forensic Decoupling Declaration

> **OFFICIAL STATUS:** Authoritative Pune Municipal Corporation (PMC) statutory ward geometry remains unavailable as established by the Phase 1C.1a audit (`BLOCKED — AUTHORITATIVE PMC WARD GEOMETRY NOT LOCATED`).
>
> The Phase 1D H/E/V construction operates strictly and exclusively at the **Uber H3 Resolution 9 analytical mesh** (3,181 cells).
>
> KMeans `ward_id` values were **completely decoupled** and not used in any calculation of $H_i$, $E_i$, or $V_i$. The canonical HEV artifact contains no `ward_id` column. PMC administrative reporting remains a deferred downstream integration dependency.

### 9.2 Invariance Verification
Unit test `test_ward_decoupling_mathematical_invariance` proved that randomly permuting or completely removing `ward_id` produces 100% byte-for-byte identical $H_i$, $E_i$, and $V_i$ outputs.

---

## 10. Analytical Limitations & Governance Boundaries

1. **Absence of Socioeconomic Vulnerability:** No socioeconomic, demographic age-structure, income, slum tenure, or housing-quality data currently exist in the canonical dataset. $V_i$ represents only biophysical/structural susceptibility.
2. **Absence of Heat-Health Outcomes:** No clinical heat stroke, hospital admission, ambulance dispatch, or mortality ground-truth data exist. H/E/V scores must not be represented as health risk predictions.
3. **Uncalibrated Methodological Weights:** Weights in all three dimensions are methodological assumptions. They are not empirical best-fit estimates.
4. **No Composite Risk in Phase 1D:** Composite risk ($\text{Risk}_i = H_i^\alpha E_i^\beta V_i^\gamma$) was intentionally not constructed in this phase.
5. **No Optimization or Intervention Modeling:** Phase 1D does not allocate cooling interventions, perform MILP optimization, or simulate temperature reduction.

---

## 11. Materialized Artifacts Inventory

| Asset Name | Relative File Path | Format | SHA-256 Checksum | Size |
| :--- | :--- | :---: | :--- | :---: |
| **Canonical HEV Parquet** | [`data/processed/hev/canonical_hev_components.parquet`](file:///c:/Users/lenovo/climora/data/processed/hev/canonical_hev_components.parquet) | Parquet | `1970c2da7863f5771b223c2f265344129ea3f7ed1e5119ece98dc56e37fa2be9` | 179.9 KiB |
| **Canonical HEV Contract** | [`data/manifests/canonical_hev_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/canonical_hev_contract.json) | JSON | `20f6b1fc579cc91c481ab6fcf49ddfd20d693a4b3163f9c08bc1ade4817a5a2f` | 9.8 KiB |
| **HEV Construction Module** | [`processing/hev_construction.py`](file:///c:/Users/lenovo/climora/processing/hev_construction.py) | Python | — | 11.2 KiB |
| **HEV Test Suite** | [`tests/test_phase_1d_hev_construction.py`](file:///c:/Users/lenovo/climora/tests/test_phase_1d_hev_construction.py) | Python | — | 8.9 KiB |
| **Forensic Report** | [`docs/science/phase-1d-hev-construction-gate.md`](file:///c:/Users/lenovo/climora/docs/science/phase-1d-hev-construction-gate.md) | Markdown | — | — |

---

## 12. Forensic Gate Summary

```text
Phase status:           PHASE 1D — PASSED
H construction:         Constructed (Formulation F-19; 4 components, equal weights 0.25)
E construction:         Constructed (Formulation F-20; 4 components, weights 0.40/0.30/0.20/0.10)
V construction:         Constructed (Formulation F-21; 3 components, weights 0.45/0.45/0.10)
Eligible cells:         3,113 cells (K_valid >= 4)
Blocked cells:          68 cells (Strictly NaN for H and V; K_valid < 4)
Weight status:          CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)
Ward dependency:        DECOUPLED (H3 Res9 canonical; KMeans ward_id unused)
Tests:                  74 passed / 0 failed (12 Phase 1D tests + 62 existing tests)
Artifacts created:      data/processed/hev/canonical_hev_components.parquet
                        data/manifests/canonical_hev_contract.json
                        processing/hev_construction.py
                        tests/test_phase_1d_hev_construction.py
                        docs/science/phase-1d-hev-construction-gate.md
Scientific blockers:    None for H/E/V construction; PMC ward geometry remains deferred
Recommended next phase: PHASE 1E: POWER-LAW CLIMATE RISK & SPATIAL AUTOCORRELATION GATE (F-22 & F-23)
```
