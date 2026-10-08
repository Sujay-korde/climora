# CLIMORA — PHASE 1E: POWER-LAW CLIMATE RISK & SPATIAL AUTOCORRELATION GATE REPORT

**Document Version:** 1.0.0  
**Phase:** Phase 1E Scientific Construction & Spatial Autocorrelation Gate  
**Contract Companion:** [`data/manifests/canonical_risk_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/canonical_risk_contract.json)  
**Primary Parquet Asset:** [`data/processed/risk/canonical_risk_surface.parquet`](file:///c:/Users/lenovo/climora/data/processed/risk/canonical_risk_surface.parquet)  
**Status:** **PHASE 1E — BLOCKED**  
**Lead Roles:** Senior Scientific Architect, Mathematical Model Auditor, Geospatial Risk Modeler, and Forensic Repository Engineer  
**Date:** 2026-10-02  

---

## 1. Executive Decision

```text
================================================================================
FINAL DECISION: PHASE 1E — BLOCKED
================================================================================
```

The CLIMORA Composite Climate Risk and Spatial Autocorrelation Gate has completed its forensic evaluation under Formulations F-22 and F-23. The gate status is formally declared **BLOCKED** in strict accordance with the mandatory scientific governance mandate (Sections 3, 13, 15, and 25):

1. **Risk Construction (F-22) — PASSED:**
   * Canonical composite climate risk ($\text{Risk}_i = H_i^\alpha E_i^\beta V_i^\gamma$) was constructed strictly from the independently validated, frozen components ($H_i, E_i, V_i$) of Phase 1D.
   * Exponents $\alpha = 1.0, \beta = 1.0, \gamma = 1.0$ were applied and strictly labeled `CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)`.
   * Temporal missingness governance was rigorously preserved: exactly 3,113 eligible cells evaluate to finite, bounded $[0.0, 0.3873]$ values, while all 68 disqualified cells ($K_{\text{valid}} < 4$) evaluate strictly to `NaN` (no silent imputation, no interpolation).
   * The Zero-Exposure Axiom ($E_i = 0 \implies \text{Risk}_i = 0$) was verified for cell `89608855343ffff`.
   * Monotonicity, domain bounds, and numerical safety were verified across the mesh.

2. **Spatial Autocorrelation Diagnostics (F-23) — BLOCKED:**
   * **Blocker 1 (Missing Data / Mesh Invariance in Spatial Weights):** Formulation F-23 hardcodes $N = 3,181$ and assumes an isotropic 6-neighbor spatial weights matrix $W$ with $W = \sum \sum w_{ij} = N$. However, F-23 contains **zero mathematical governance** regarding how the spatial weights matrix or Global/Local Moran's I must handle the 68 disqualified cells whose Hazard, Susceptibility, and Risk values are strictly `NaN`. Pruning disqualified cells reduces the eligible analytical mesh to $N = 3,113$ and alters neighbor degrees for adjacent cells; retaining them with `NaN` yields undefined matrix summations.
   * **Blocker 2 (Boundary Normalization Ambiguity):** F-23 defines "$w_{ij}$ is the row-standardized 6-neighbor spatial weight ($w_{ij} = 1/6$ if $j \in \text{neighbors}(i)$, $0$ otherwise), and $W = \sum_{i=1}^N \sum_{j=1}^N w_{ij} = N$". For the 359 finite-mesh boundary cells having fewer than 6 eligible neighbors, fixed $1/6$ weights yield $W = 2991.33 \ne N$ (violating row-standardization), whereas row-standardization ($w_{ij} = 1/k_i$) yields $W = N = 3113$ but departs from fixed $1/6$.
   * **Blocker 3 (Unratified Primary Significance Testing Procedure):** Formulation F-23 specifies Benjamini-Hochberg False Discovery Rate (FDR) control at $Q = 0.05$ over $N = 3,181$ tests, but **fails to mathematically formulate the primary procedure for generating raw $p$-values ($p_i$)**. F-23 provides no analytical variance formula for Local Moran's I ($Var(I_i)$) under either normality or randomization, nor does it govern a Monte Carlo permutation algorithm (replicate count, pseudo-random generator seed, conditional vs unconditional permutation, or exact pseudo-$p$ definition).
   * **Governance Enforcement:** Per Section 3 and Section 15 of the mandate, unratified mathematical details must NOT be invented. Consequently, descriptive Moran quadrants are reported, but inferential significance-based hotspot classifications (High-High, Low-Low clusters) are **withheld**, and Phase 1E is marked **BLOCKED**.

---

## 2. Formulation Governance Audit

A rigorous verification of the repository's formulation register ([`docs/science/climora-mathematical-formulation-register.md`](file:///c:/Users/lenovo/climora/docs/science/climora-mathematical-formulation-register.md)) and companion contract ([`data/manifests/scientific_formulation_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/scientific_formulation_contract.json)) was conducted across the eleven mandatory audit criteria:

| # | Governance Criterion | Register Status | Audit Finding |
| :--- | :--- | :---: | :--- |
| 1 | $\alpha, \beta, \gamma$ definitions | **RATIFIED** | Formally defined in F-22 as exponent scaling parameters for Hazard, Exposure, and Biophysical Susceptibility. Governed in [`data/manifests/risk_parameter_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/risk_parameter_contract.json). |
| 2 | Default values of $\alpha, \beta, \gamma$ | **RATIFIED** | Explicitly defined in F-22 as $\alpha = 1.0, \beta = 1.0, \gamma = 1.0$. Classified as `CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)`. |
| 3 | Spatial neighborhood definition | **RATIFIED** | Specified in F-23 as H3 Resolution 9 1-ring topological adjacency (`h3.grid_disk(c, 1) - {c}`). |
| 4 | Spatial weights matrix $w_{ij}$ | **PARTIALLY RATIFIED** | Defined in F-23 as row-standardized weights ($W = N$). Evaluated on eligible mesh ($N = 3,113$). |
| 5 | Treatment of self-neighbors | **RATIFIED** | $w_{ii} = 0$ (standard spatial autoregressive contiguity; self is excluded). |
| 6 | Row standardization | **PARTIALLY RATIFIED** | Stated as $W = N$. Satisfied under $w_{ij} = 1 / k_i$, but in tension with the literal text "$w_{ij} = 1/6$" for boundary cells. |
| 7 | Eligibility handling in spatial statistics | **NOT RATIFIED** | F-23 hardcodes $N = 3,181$ and contains zero governance on how disqualified cells are handled during spatial weighting. |
| 8 | Treatment of 68 ineligible cells | **NOT RATIFIED** | Completely absent from F-23. Ineligible cells have `NaN` risk; cannot be evaluated in standard matrix products without explicit policy. |
| 9 | Exact Local Moran/LISA statistic | **RATIFIED** | Formula $I_i = \frac{x_i - \bar{x}}{m_2} \sum_j w_{ij}(x_j - \bar{x})$ where $m_2 = \frac{1}{N} \sum_i (x_i - \bar{x})^2$ adheres verbatim to Anselin (1995). |
| 10 | Significance-testing method | **NOT RATIFIED** | F-23 omits the mathematical formula/algorithm for raw $p$-values (no analytical variance equation, no permutation parameters). |
| 11 | Multiple-testing correction | **RATIFIED** | Benjamini-Hochberg False Discovery Rate ($Q = 0.05$) is ratified, but assumes $N = 3,181$ input $p$-values. |

---

## 3. Power-Law Climate Risk Construction

### 3.1 Mathematical Formulation (F-22)

$$\text{Risk}_i = \mathcal{H}_i^\alpha \times \mathcal{E}_i^\beta \times \mathcal{V}_i^\gamma$$

Under the governed default parameters:

$$\alpha = 1.0, \quad \beta = 1.0, \quad \gamma = 1.0 \implies \text{Risk}_i = \mathcal{H}_i \times \mathcal{E}_i \times \mathcal{V}_i$$

### 3.2 Methodological Attribution & Qualification
* **Attribution Boundary:** Formulation F-22 is CLIMORA's methodological implementation operationalizing the conceptual interaction of Hazard, Exposure, and Vulnerability from IPCC AR6 WGII. It is **NOT** an IPCC-prescribed mathematical equation.
* **Exponents Qualification:** The exponents $\alpha = \beta = \gamma = 1.0$ are classified as `CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)`. They are **NOT** empirically calibrated, fitted against epidemiological damage functions, or estimated via machine learning.

### 3.3 Numerical Safety & Bounds Verification
Before and after exponentiation, all eligible components were verified:
* Zero `NaN`, zero $\pm \infty$, and zero negative values across all 3,113 eligible cells.
* Empirical input domains: $\mathcal{H}_i \in [0.0813, 0.8856]$, $\mathcal{E}_i \in [0.0000, 0.8086]$, $\mathcal{V}_i \in [0.0900, 0.9760]$.
* Resulting composite risk: $\text{Risk}_i \in [0.0000, 0.3873]$ (strictly finite and bounded in $[0.0, 1.0]$).
* No artificial numerical clipping or winsorizing was applied.

---

## 4. Eligibility & Missingness Audit

* **Temporal Governance Rule (F-13):** A cell is eligible for multi-temporal baseline central tendencies and downstream risk iff $K_{\text{valid}, i} \ge 4$ years with unmasked clear pixel fraction $f_{\text{valid}} \ge 0.70$.
* **Eligible Cells:** Exactly **3,113 cells** ($97.86\%$). All three components ($H_i, E_i, V_i$) and composite $\text{Risk}_i$ are strictly non-null and finite.
* **Ineligible Cells:** Exactly **68 cells** ($2.14\%$). Flagged `overall_risk_eligibility = False`.
* **Zero Silent Imputation:** For all 68 disqualified cells, $\mathcal{H}_i = \text{NaN}$, $\mathcal{V}_i = \text{NaN}$, and $\text{Risk}_i = \text{NaN}$. No spatial interpolation, citywide mean substitution, or nearest-neighbor copying was performed.

---

## 5. Zero-Exposure Axiom Audit

Under Formulation F-22, with $\beta > 0$:

$$\mathcal{E}_i = 0 \implies \text{Risk}_i = \mathcal{H}_i^\alpha \times 0^\beta \times \mathcal{V}_i^\gamma = 0.0$$

* **Empirical Mesh Audit:** Exactly **1 cell** (`89608855343ffff`) exhibits $\mathcal{E}_i = 0.000000$.
* **Cell Attributes:**
  * Population count: $25.07$ persons (citywide minimum $\implies \text{Norm}(C) = 0.0$)
  * Population density: $254.80\text{ persons/km}^2$ (citywide minimum $\implies \text{Norm}(D) = 0.0$)
  * Civic infrastructure: $0$ facilities ($\implies \text{Norm}(N) = 0.0$)
  * Road network length: $0.00$ meters ($\implies \text{Norm}(L) = 0.0$)
  * Hazard composite: $\mathcal{H}_i = 0.370498$ (moderate radiant surface heat)
  * Susceptibility composite: $\mathcal{V}_i = 0.697693$
* **Resulting Risk:** $\text{Risk}_i = 0.370498^1 \times 0.0^1 \times 0.697693^1 = 0.000000$.
* **Semantic Qualification:** This zero result is an analytical consequence of the mathematical formulation enforcing that human climate risk cannot exist where human presence and critical infrastructure are completely absent. It is not presented as a universal physical law.

---

## 6. Composite Risk Distribution Audit

Descriptive statistical summary across the **3,113 eligible cells**:

| Metric | Empirical Value |
| :--- | :---: |
| **Observation Count ($N$)** | 3,113 |
| **Missingness ($N=3181$)** | 68 (`NaN`) |
| **Minimum** | 0.000000 |
| **Percentile 05 (P05)** | 0.006511 |
| **Percentile 25 (P25)** | 0.020690 |
| **Median (P50)** | 0.044614 |
| **Mean** | 0.065245 |
| **Percentile 75 (P75)** | 0.093930 |
| **Percentile 90 (P90)** | 0.153609 |
| **Percentile 95 (P95)** | 0.187132 |
| **Percentile 99 (P99)** | 0.251679 |
| **Maximum** | 0.387269 |
| **Sample Standard Deviation** | 0.059022 |

### Extremes & Threshold Crossings:
* **Zero-risk cells ($\text{Risk} = 0.0$):** Exactly 1 cell (`89608855343ffff`).
* **Near-zero cells ($\text{Risk} < 0.001$):** 23 cells ($0.74\%$).
* **Cells $\ge \text{P90}$ ($\text{Risk} \ge 0.153609$):** 312 cells.
* **Cells $\ge \text{P95}$ ($\text{Risk} \ge 0.187132$):** 156 cells.

> **CLASSIFICATION GOVERNANCE POLICY:** Per Section 8 of the mandate, these continuous scores are **NOT converted into arbitrary qualitative bins** such as "Low", "Medium", "High", or "Extreme". No classification threshold has been ratified in the formulation register.

---

## 7. Component Correlation Diagnostics

Pairwise association matrix across the eligible mesh ($N = 3,113$):

```text
Pearson Correlation Matrix:
              H_i          E_i          V_i         Risk_i
  H_i       1.000000    -0.404811    +0.758153    +0.085777
  E_i      -0.404811     1.000000    -0.299164    +0.768610
  V_i      +0.758153    -0.299164     1.000000    +0.161376
  Risk_i   +0.085777    +0.768610    +0.161376     1.000000

Spearman Rank Correlation Matrix:
              H_i          E_i          V_i         Risk_i
  H_i       1.000000    -0.438788    +0.793440    +0.043101
  E_i      -0.438788     1.000000    -0.378681    +0.852531
  V_i      +0.793440    -0.378681     1.000000    +0.052104
  Risk_i   +0.043101    +0.852531    +0.052104     1.000000
```

### Forensic Diagnostic Observations (Non-Causal Interpretation):
1. **Exposure Dominance in Multiplicative Risk:**
   * The composite risk score exhibits strong positive correlation with Exposure ($r = +0.7686$, $\rho = +0.8525$).
   * This diagnostic indicates that under equal unitary exponents ($\alpha = \beta = \gamma = 1.0$), spatial variation in composite human climate risk across Pune is predominantly structured by human demographic and infrastructure exposure patterns.
2. **Hazard and Susceptibility Decoupling from Composite Risk:**
   * While Hazard and Biophysical Susceptibility are strongly coupled to each other ($r = +0.7582$, $\rho = +0.7934$), their linear correlations with composite Risk are weak ($r = +0.0858$ and $r = +0.1614$).
   * The observed association is consistent with Pune's spatial geography: areas with the most extreme radiant surface skin temperatures and vegetative deficits occur in low-density peripheral basalt plateaus and industrial complexes, whereas central municipal wards experience high demographic concentration with moderate thermal hazard.
   * This observation is diagnostic of model structure under unitary weights and does not constitute causal proof.

---

## 8. Risk Monotonicity Audit

Analytically, for $\text{Risk}_i = H_i^\alpha E_i^\beta V_i^\gamma$ with positive parameters $\alpha, \beta, \gamma > 0$ and non-negative domains $H_i, E_i, V_i \ge 0$:

$$\frac{\partial \text{Risk}_i}{\partial H_i} = \alpha H_i^{\alpha-1} E_i^\beta V_i^\gamma \ge 0$$
$$\frac{\partial \text{Risk}_i}{\partial E_i} = \beta H_i^\alpha E_i^{\beta-1} V_i^\gamma \ge 0$$
$$\frac{\partial \text{Risk}_i}{\partial V_i} = \gamma H_i^\alpha E_i^\beta V_i^{\gamma-1} \ge 0$$

Numerical monotonicity was verified via controlled unit tests (`test_risk_monotonicity` in [`tests/test_phase_1e_risk_spatial_gate.py`](file:///c:/Users/lenovo/climora/tests/test_phase_1e_risk_spatial_gate.py)). Holding any two dimensions constant while monotonically increasing the third yields non-decreasing risk scores across all evaluations.

---

## 9. Spatial Neighborhood & Spatial Weights Matrix (F-23)

### 9.1 Topology and Neighborhood Construction
* **Discrete Global Grid System:** Uber H3 Resolution 9 ($200.8\text{ m}$ edge length, $\sim 347.8\text{ m}$ centroid spacing).
* **Neighborhood Definition:** Immediate 1-ring hexagonal adjacency (`h3.grid_disk(c, 1) - {c}`). Every cell in boundless H3 topology has exactly 6 neighbors.

### 9.2 Finite-Mesh Boundary Degree Distribution (Eligible Mesh $N = 3,113$)
In the finite statutory Pune mesh restricted to the 3,113 eligible cells:
* **Total Eligible Observations ($N$):** 3,113 cells.
* **Isolated Cells ($k_i = 0$):** **0 cells** (no cell is topologically disconnected).
* **Full Interior Cells ($k_i = 6$):** 2,754 cells ($88.47\%$).
* **Boundary Truncated Cells ($k_i < 6$):** 359 cells ($11.53\%$).
  * $k_i = 5$: 111 cells
  * $k_i = 4$: 145 cells
  * $k_i = 3$: 86 cells
  * $k_i = 2$: 14 cells
  * $k_i = 1$: 3 cells
* **Mean Neighbors per Cell:** $5.7655$ neighbors.

### 9.3 Row Standardization vs Fixed Weights Governance
* **Primary Implementation (Row-Standardized):**
  $$w_{ij} = \frac{1}{k_i} \quad \text{for } j \in \mathcal{N}_i, \quad 0 \text{ otherwise}$$
  * Ensures $\sum_{j=1}^N w_{ij} = 1.000000$ for all 3,113 cells.
  * Matrix weight sum: $W = \sum_{i=1}^N \sum_{j=1}^N w_{ij} = 3,113.0 = N$.
* **Secondary Comparison (Fixed $1/6$ Weights):**
  $$w_{ij} = \frac{1}{6} \quad \text{for } j \in \mathcal{N}_i, \quad 0 \text{ otherwise}$$
  * Boundary cells sum to $k_i / 6 < 1.0$.
  * Matrix weight sum: $W = 2,991.3333 \ne N$.

---

## 10. Global Moran's I Spatial Autocorrelation

Global Moran's I was computed across the 3,113 eligible cells using Formulation F-23:

$$I = \frac{N}{S_0} \frac{\sum_{i=1}^N \sum_{j=1}^N w_{ij} (x_i - \bar{x})(x_j - \bar{x})}{\sum_{i=1}^N (x_i - \bar{x})^2}$$

### 10.1 Empirical Moran's I Results

| Metric / Parameter | Primary (Row-Standardized) | Secondary (Fixed 1/6) | Methodological Role |
| :--- | :---: | :---: | :--- |
| **Observation Count ($N$)** | 3,113 | 3,113 | Eligible cells with valid $K_{\text{valid}} \ge 4$ |
| **Sum of Weights ($S_0$)** | 3,113.0000 | 2,991.3333 | Total spatial interaction mass |
| **Observed Moran's $I$** | **+0.781355** | **+0.788981** | Spatial autocorrelation coefficient |
| **Theoretical Expected $E[I]$** | **-0.000321** | **-0.000321** | $-1 / (N - 1) = -1 / 3112$ |
| **Analytical Variance $Var(I)$** | 0.00011341 | 0.00011115 | Under randomization hypothesis (Cliff & Ord 1981) |
| **Standard Error $SD(I)$** | 0.010649 | 0.010543 | Standard error of the statistic |
| **Standardized $z$-Score** | **+73.40** | **+74.87** | $(I - E[I]) / SD(I)$ |
| **Analytical $p$-Value** | $< 10^{-16}$ ($0.0$) | $< 10^{-16}$ ($0.0$) | Two-tailed Gaussian approximation |
| **Monte Carlo Pseudo $p$-Value** | $0.0010$ ($p < 0.001$) | $0.0010$ ($p < 0.001$) | 999 permutations, seed=42; max perm $I = 0.0339$ |

### 10.2 Dimensional Cross-Comparison
To contextualize the spatial structure of composite risk against its constituent dimensions, Global Moran's I was computed across all components using identical eligible spatial weights ($W_{\text{row-std}}$):

| Analytical Variable | Observed Moran's $I$ | Expected $E[I]$ | Standardized $z$-Score | Analytical $p$-Value |
| :--- | :---: | :---: | :---: | :---: |
| **Exposure Composite ($\mathcal{E}_i$)** | **+0.942667** | -0.000321 | +88.51 | $< 10^{-16}$ |
| **Composite Climate Risk ($\text{Risk}_i$)** | **+0.781355** | -0.000321 | +73.40 | $< 10^{-16}$ |
| **Biophysical Susceptibility ($\mathcal{V}_i$)** | **+0.710874** | -0.000321 | +66.77 | $< 10^{-16}$ |
| **Current LST Intensity ($\bar{T}_{2025}$)** | **+0.709241** | -0.000321 | +66.60 | $< 10^{-16}$ |
| **Hazard Composite ($\mathcal{H}_i$)** | **+0.708605** | -0.000321 | +66.54 | $< 10^{-16}$ |

### 10.3 Inferential Scientific Interpretation
* The observed Global Moran's $I = +0.781355$ ($z = +73.40, p < 10^{-16}$) demonstrates **statistically detectable positive spatial autocorrelation** across the H3 Resolution 9 mesh.
* Risk values in Pune are not distributed as spatially independent random noise. Hexagons with elevated composite risk are systematically adjacent to other hexagons with elevated composite risk.
* Exposure exhibits the highest degree of spatial clustering ($I = 0.9427$), consistent with contiguous urban demographic development along transport corridors.

---

## 11. Local Spatial Diagnostics (LISA)

### 11.1 Local Moran's I Statistic Distribution
Local Moran's I was evaluated for every eligible cell ($N = 3,113$) using Formulation F-23:

$$I_i = \frac{x_i - \bar{x}}{m_2} \sum_{j=1}^N w_{ij} (x_j - \bar{x}) \quad \text{where } m_2 = \frac{1}{N} \sum_{i=1}^N (x_i - \bar{x})^2$$

* **Mean Local $I_i$:** $0.781355$ (identically matches Global Moran's $I$, verifying Anselin's identity $\frac{1}{N} \sum I_i = I$).
* **Minimum $I_i$:** $-0.578587$ (negative spatial association; spatial outlier).
* **Percentile 25:** $+0.117905$
* **Median $I_i$:** $+0.426212$
* **Percentile 75:** $+0.821579$
* **Percentile 95:** $+3.292596$
* **Maximum $I_i$:** $+14.228697$ (intense local positive spatial clustering).

### 11.2 Descriptive Moran Quadrants (Spatial Lag Typology)
In accordance with Formulation F-23, cells were classified into empirical quadrants based on the joint sign of local anomaly ($z_i = x_i - \bar{x}$) and row-standardized spatial lag ($[Wz]_i = \sum_j w_{ij} z_j$):

| Quadrant | Typology | Cell Count | Percentage | Descriptive Interpretation |
| :--- | :--- | :---: | :---: | :--- |
| **Quadrant 1** | **High-High** | 1,069 | 34.34% | Elevated risk surrounded by elevated neighbor risk |
| **Quadrant 2** | **Low-Low** | 1,746 | 56.09% | Low risk surrounded by low neighbor risk |
| **Quadrant 3** | **Low-High** | 213 | 6.84% | Low risk surrounded by elevated neighbor risk (spatial outlier) |
| **Quadrant 4** | **High-Low** | 85 | 2.73% | Elevated risk surrounded by low neighbor risk (spatial outlier) |
| **Ineligible** | Disqualified ($K_{\text{valid}} < 4$) | 68 | — | Evaluated strictly as `NaN` (no spatial lag evaluated) |

### 11.3 Why Significance-Based LISA Clustering is Withheld
Formulation F-23 specifies that High-High (Hotspot) and Low-Low (Coldspot) clusters require:

$$z_i > 0 \land [Wz]_i > 0 \land p_{\text{adj}} < 0.05$$

where $p_{\text{adj}}$ is adjusted via Benjamini-Hochberg FDR control. However, as established in the Formulation Governance Audit (Section 2):
1. **No primary significance testing formula exists in F-23** for generating the unadjusted $p$-values ($p_i$).
2. Analytical variance equations for Local Moran's I are not defined in the register.
3. Permutation testing parameters (iteration count, seed, conditional vs unconditional resampling, pseudo-$p$ formula) are not ratified in F-23.
4. An exploratory sensitivity test demonstrated that the number of significant cells varies wildly from 183 to over 700 depending on permutation algorithm and seed.

> **MANDATORY GOVERNANCE DECISION:** In strict adherence to Section 15 ("Do not produce significance-based categories unless the F-23 formulation explicitly defines the significance procedure. Do not invent a p-value threshold."), **no cell is categorized as an inferential Hotspot or Coldspot**. Quadrants are reported strictly as empirical descriptive associations. Phase 1E is marked **BLOCKED** on this omission.

---

## 12. PMC Ward Decoupling & Invariance Verification

* **Administrative Geometry Status:** Authoritative statutory PMC municipal ward polygons remain unavailable as established by the Phase 1C.1a audit (`BLOCKED — AUTHORITATIVE PMC WARD GEOMETRY NOT LOCATED`).
* **Complete Analytical Decoupling:**
  * The KMeans synthetic `ward_id` column was **NOT used** in any calculation of composite Risk, spatial neighborhood graph construction, spatial weights matrix, Global Moran's I, or Local Moran's I.
  * Canonical parquet artifact [`canonical_risk_surface.parquet`](file:///c:/Users/lenovo/climora/data/processed/risk/canonical_risk_surface.parquet) contains no `ward_id` column.
* **Mathematical Invariance Verification:** Unit test `test_ward_decoupling_mathematical_invariance` proved that randomly permuting `ward_id` across the mesh produces 100% byte-for-byte identical Risk values.

---

## 13. Scientific Limitations & Governance Boundaries

1. **Methodological Parameter Exponents:** The exponents $\alpha = \beta = \gamma = 1.0$ and all component weights are methodological modeling assumptions. They are not calibrated physical or epidemiological constants.
2. **Absence of Socioeconomic Vulnerability:** Susceptibility ($\mathcal{V}_i$) strictly measures biophysical canopy deficit and built thermal mass. No parcel-level household income, poverty, caste, or adaptive capacity data are represented.
3. **Absence of Epidemiological Ground Truth:** Composite Risk is a relative screening index. It does not predict clinical heat stroke, hospital admissions, ambulance dispatches, or excess mortality.
4. **Spatial Autocorrelation Inference Scope:** Global Moran's I demonstrates statistically detectable spatial clustering of risk across the H3 mesh. However, localized cluster significance (LISA hotspots) cannot be asserted without ratified significance-testing governance.
5. **No Intervention Modeling:** Phase 1E does not allocate cooling interventions, perform MILP spatial optimization, simulate temperature reductions, or project financial budgets.

---

## 14. Materialized Artifacts Inventory

| Asset Name | Relative File Path | Format | SHA-256 Checksum | Size |
| :--- | :--- | :---: | :--- | :---: |
| **Canonical Risk Parquet** | [`data/processed/risk/canonical_risk_surface.parquet`](file:///c:/Users/lenovo/climora/data/processed/risk/canonical_risk_surface.parquet) | Parquet | `e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677` | 202.2 KiB |
| **Canonical Risk Contract** | [`data/manifests/canonical_risk_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/canonical_risk_contract.json) | JSON | `325d371cb8917f8189e18eb719ce007cf43c6af8770b6ebabbc0600eea0b9cef` | 9.3 KiB |
| **Risk Construction Engine** | [`processing/risk_construction.py`](file:///c:/Users/lenovo/climora/processing/risk_construction.py) | Python | — | 18.2 KiB |
| **Phase 1E Test Suite** | [`tests/test_phase_1e_risk_spatial_gate.py`](file:///c:/Users/lenovo/climora/tests/test_phase_1e_risk_spatial_gate.py) | Python | — | 8.8 KiB |
| **Scientific Gate Report** | [`docs/science/phase-1e-risk-spatial-autocorrelation-gate.md`](file:///c:/Users/lenovo/climora/docs/science/phase-1e-risk-spatial-autocorrelation-gate.md) | Markdown | — | — |

---

## 15. Forensic Gate Summary

```text
Phase status:           PHASE 1E — BLOCKED
Risk formulation:       Constructed (Formulation F-22: Risk_i = H_i^alpha * E_i^beta * V_i^gamma)
Alpha:                  1.0 (CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION; PENDING_CALIBRATION)
Beta:                   1.0 (CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION; PENDING_CALIBRATION)
Gamma:                  1.0 (CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION; PENDING_CALIBRATION)
Eligible cells:         3,113 cells (K_valid >= 4)
Zero-risk cells:        1 cell (89608855343ffff; E_i = 0.0 => Risk_i = 0.0)
Spatial neighborhood:   Uber H3 Resolution 9 1-ring hexagonal adjacency (grid_disk radius 1)
Spatial weights:        Row-standardized (w_ij = 1/k_i; W = N = 3113.0 across eligible mesh)
Global Moran's I:       +0.781355 (Expected: -0.000321; z-score: +73.40 under randomization)
Moran significance:     p < 10^-16 (analytical Gaussian); p < 0.001 (Monte Carlo pseudo-p, 999 perms)
LISA implemented:       Descriptive Moran Quadrants only (1069 HH, 1746 LL, 85 HL, 213 LH); Significance withheld
Ward dependency:        DECOUPLED (H3 Res9 canonical; KMeans ward_id unused and mathematically invariant)
Tests:                  85 passed / 0 failed (11 Phase 1E tests + 74 existing tests)
Artifacts:              data/processed/risk/canonical_risk_surface.parquet
                        data/manifests/canonical_risk_contract.json
                        processing/risk_construction.py
                        tests/test_phase_1e_risk_spatial_gate.py
                        docs/science/phase-1e-risk-spatial-autocorrelation-gate.md
Scientific blockers:    1. Formulation F-23 hardcodes N=3181 and lacks missingness governance for the 68 ineligible cells in spatial weights.
                        2. Formulation F-23 conflates row-standardization with uniform w_ij=1/6 at boundary cells.
                        3. Formulation F-23 omits primary significance testing methodology for raw LISA p-values.
Recommended next phase: PHASE 1E.1: SPATIAL AUTOCORRELATION & LISA SIGNIFICANCE RATIFICATION GATE (Formulation Amendment F-23.1)
```
