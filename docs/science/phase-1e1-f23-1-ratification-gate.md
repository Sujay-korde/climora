# CLIMORA — PHASE 1E.1: F-23.1 SPATIAL AUTOCORRELATION & LISA SIGNIFICANCE RATIFICATION GATE REPORT

**Document Version:** 1.0.0  
**Phase:** Phase 1E.1 Spatial-Statistical Formulation Ratification Gate  
**Contract Companion:** [`data/manifests/spatial_autocorrelation_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/spatial_autocorrelation_contract.json)  
**Primary Parquet Asset:** [`data/processed/risk/canonical_spatial_autocorrelation.parquet`](file:///c:/Users/lenovo/climora/data/processed/risk/canonical_spatial_autocorrelation.parquet)  
**Input Risk Surface Asset:** [`data/processed/risk/canonical_risk_surface.parquet`](file:///c:/Users/lenovo/climora/data/processed/risk/canonical_risk_surface.parquet) (SHA-256: `e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677`)  
**Status:** **PHASE 1E.1 — PASSED**  
**Lead Roles:** Senior Scientific Architect, Mathematical Statistician, Geospatial Scientist, and Forensic Model Governance Engineer  
**Date:** 2026-10-02  

---

## 24.1 Executive Decision

```text
================================================================================
FINAL DECISION: PHASE 1E.1 — PASSED
================================================================================
```

The CLIMORA Spatial Autocorrelation & LISA Significance Ratification Gate has completed its forensic evaluation under the controlled formulation amendment **F-23.1 (Eligible H3 Spatial Autocorrelation & LISA Significance)**.

All three governance defects that blocked Phase 1E have been comprehensively resolved through formal mathematical formulation, rigorous empirical computation, and automated contract ratification:

1. **Defect 1 (Missingness & Analytical Population) — RESOLVED:** The analytical population for inferential spatial statistics is strictly restricted to the eligible H3 analytical mesh $\mathcal{I} = \{i : K_{\text{valid},i} \ge 4\}$ ($N_e = 3,113$). The 68 disqualified cells remain in the spatial mesh as `NaN` observations and are strictly excluded from the observation vector, spatial graph adjacency summations, and matrix multiplications. No numerical risk values are imputed, zeroed, or interpolated.
2. **Defect 2 (Spatial Weight Normalization) — RESOLVED:** Spatial weights are unambiguously ratified as row-standardized $w_{ij} = 1 / k_i$ across eligible 1-ring neighbors ($w_{ii} = 0$), guaranteeing $\sum_j w_{ij} = 1.0$ for all $N_e$ eligible cells and yielding $S_0 = \sum_i \sum_j w_{ij} = N_e = 3,113.0$. The prior conflicting fixed $w_{ij} = 1/6$ definition has been formally retired from canonical governance.
3. **Defect 3 (Local Significance & Multiple Testing) — RESOLVED:** Raw local Moran $p$-values are generated via a fully ratified, deterministic conditional Monte Carlo permutation procedure ($B = 9,999$, seed = 42) computing two-sided finite-sample pseudo-$p$-values $p_i = \frac{1 + \#\{|I_i^{(b)}| \ge |I_i^{\text{obs}}|\}}{B + 1}$. Benjamini-Hochberg False Discovery Rate (FDR) control at $Q = 0.05$ is applied across the complete family of $N_e = 3,113$ eligible local tests, identifying exactly 339 statistically significant LISA cells (337 High-High hotspots, 2 Low-High spatial outliers, 0 Low-Low coldspots, and 0 High-Low outliers).

Composite Climate Risk construction (Formulation F-22) remains preserved byte-for-byte in [`data/processed/risk/canonical_risk_surface.parquet`](file:///c:/Users/lenovo/climora/data/processed/risk/canonical_risk_surface.parquet) with checksum unmodified. PMC ward boundaries remain strictly decoupled ($0$ dependency). All 94 test suite assertions pass cleanly.

---

## 24.2 Previous F-23 Defects

The Phase 1E forensic audit identified three critical formulation and governance defects in Formulation F-23 that precluded inferential claims of spatial clustering:

### Defect 1 — Missingness & Population Mismatch
* **Defect Description:** F-23 previously hardcoded the analytical population as $N = 3,181$ cells, but 68 cells possessed $K_{\text{valid},i} < 4$ (excessive Landsat/Sentinel cloud masking across the temporal window), resulting in $H_i = \text{NaN}, V_i = \text{NaN}, \text{Risk}_i = \text{NaN}$.
* **Forensic Impact:** F-23 provided no mathematical rule governing the treatment of disqualified cells within the spatial weights matrix $W$ or during vector-matrix products. Incorporating $\text{NaN}$ values into standard Moran matrix summations yields non-finite products, while imputing arbitrary values (such as zero risk) would violate physical reality and corrupt null distributions.

### Defect 2 — Weight Normalization Conflict
* **Defect Description:** F-23 contained mutually contradictory definitions: it specified row-standardized weights ($W = \sum_i \sum_j w_{ij} = N$) while simultaneously specifying fixed weights "$w_{ij} = 1/6$ for $j \in \text{neighbors}(i)$".
* **Forensic Impact:** For an infinite hexagonal lattice, every cell has degree 6, making $1/6$ identical to $1/k_i$. However, on the finite Pune H3 Res9 mesh, 359 eligible cells reside on the boundary and have $k_i < 6$ eligible neighbors. Under fixed $w_{ij} = 1/6$, row sums equal $k_i / 6 < 1.0$, producing $S_0 = 2,991.33 \ne N$, which violates row-standardization and introduces boundary attenuation. Under row-standardization ($w_{ij} = 1/k_i$), each row sums to $1.0$, producing $S_0 = N_e = 3,113.0$. Canonical governance lacked a binding choice between these formulations.

### Defect 3 — Unratified Local Significance & Pseudo-$p$ Formulation
* **Defect Description:** F-23 prescribed Benjamini-Hochberg FDR control at $Q = 0.05$ over $N = 3,181$ tests, but omitted the primary statistical procedure for generating raw local Moran $p$-values ($p_i$).
* **Forensic Impact:** Local Moran's $I_i$ lacks a simple closed-form analytical variance under non-normal spatial data without severe simplifying assumptions. Furthermore, no Monte Carlo permutation parameters (number of permutations $B$, random seed, conditional vs unconditional sampling, one-sided vs two-sided hypothesis, finite-sample pseudo-$p$ formula) were governed. Without ratified raw $p$-values, FDR adjustment could not be mathematically executed, preventing valid claims of statistically significant hotspots.

---

## 24.3 F-23.1 Amendment

To resolve these defects without altering upstream risk construction, Formulation F-23 has been amended to **Formulation F-23.1 (Eligible H3 Spatial Autocorrelation & LISA Significance)** in the scientific formulation register ([`docs/science/climora-mathematical-formulation-register.md`](file:///c:/Users/lenovo/climora/docs/science/climora-mathematical-formulation-register.md)):

1. **Governed Analytical Population:** Bounded strictly to the eligible H3 analytical mesh:
   $$\mathcal{I} = \{i : K_{\text{valid},i} \ge 4\}, \quad N_e = |\mathcal{I}| = 3,113$$
   The 68 ineligible cells remain in the spatial coordinate database with $\text{Risk} = \text{NaN}$ but are strictly omitted from the numerical observation vector $\mathbf{x} \in \mathbb{R}^{N_e}$.
2. **Induced Eligible Graph:** The spatial topology is defined as the induced subgraph of $\mathcal{I}$ under H3 Res9 1-ring contiguity:
   $$a_{ij} = \begin{cases} 1 & \text{if } j \in \text{grid\_ring}(i, 1) \text{ and } j \in \mathcal{I} \\ 0 & \text{otherwise} \end{cases}, \quad a_{ii} = 0$$
   Cross-boundary edges leading to disqualified cells do not contribute adjacency or weight.
3. **Canonical Spatial Weights:** Unambiguously ratified as row-standardized:
   $$w_{ij} = \begin{cases} \frac{1}{k_i} & \text{if } a_{ij} = 1 \\ 0 & \text{otherwise} \end{cases}, \quad w_{ii} = 0$$
   where $k_i = \sum_{j \in \mathcal{I}} a_{ij}$. For all non-isolated cells, $\sum_j w_{ij} = 1.0$, guaranteeing $S_0 = \sum_i \sum_j w_{ij} = N_e = 3,113.0$. Fixed $1/6$ weights are permanently retired from canonical inference.
4. **Governed Global Significance Testing:** Deterministic Monte Carlo permutation procedure:
   * Permutation replicates: $B = 9,999$
   * Random seed: $42$ (Mersenne Twister / NumPy BitGenerator)
   * Permutation unit: Unrestricted shuffling of $\text{Risk}_i$ values across the $N_e$ eligible cells
   * Pseudo-$p$-value formula (two-sided, finite-sample corrected):
     $$p_{\text{pseudo}} = \frac{1 + \#\{b : |I^{(b)}| \ge |I_{\text{obs}}|\}}{B + 1}$$
     guaranteeing $p_{\text{pseudo}} \ge \frac{1}{B + 1} = 0.000100$ and eliminating exact zero $p$-values.
5. **Governed Local Significance Testing:** Deterministic conditional Monte Carlo permutation procedure:
   * For each focal cell $i \in \mathcal{I}$, observed risk $x_i$ is held fixed at location $i$.
   * Risk values of the remaining $N_e - 1$ eligible cells are permuted without replacement across non-focal positions.
   * Permutation replicates: $B = 9,999$; Random seed: $42$.
   * Finite-sample two-sided pseudo-$p$-value:
     $$p_i = \frac{1 + \#\{b : |I_i^{(b)}| \ge |I_i^{\text{obs}}|\}}{B + 1}$$
6. **Multiple-Testing Correction:** Benjamini-Hochberg FDR control at $Q = 0.05$ evaluated across exactly $M = N_e = 3,113$ eligible hypothesis tests.
7. **Inferential LISA Clusters vs Descriptive Quadrants:** Inferential labels (`High-High`, `Low-Low`, `High-Low`, `Low-High`) are assigned exclusively to cells satisfying $q_i \le 0.05$. Cells with $q_i > 0.05$ are strictly classified as `Not significant`.

---

## 24.4 Eligible Mesh

The spatial mesh inventory under Formulation F-23.1 is structured as follows:

| Mesh Metric | Value | Proportion | Mathematical Policy |
| :--- | :---: | :---: | :--- |
| **Total Geographic Mesh ($N$)** | 3,181 | 100.00% | Bounding hexagonal grid covering Pune Municipal Corporation study area. |
| **Eligible Analytical Mesh ($N_e$)** | 3,113 | 97.86% | Cells with $K_{\text{valid},i} \ge 4$ (sufficient valid temporal clearances). Form the inferential population. |
| **Ineligible Cells ($N_{\text{ineligible}}$)** | 68 | 2.14% | Disqualified due to cloud contamination ($K_{\text{valid},i} < 4$). Assigned $\text{Risk} = \text{NaN}$. Excluded from weights matrix. |
| **Missingness Imputation Policy** | None (0) | 0.00% | Strict prohibition of mean, median, zero, or kriging imputation for unobserved risk cells. |

All 68 disqualified cells remain present in the canonical geospatial coordinate system to preserve geographic continuity but are completely absent from numerical matrix summations.

---

## 24.5 Spatial Graph

The induced eligible graph topology $(\mathcal{I}, \mathbf{A})$ was constructed and audited:

### Degree Distribution

$$k_i = \sum_{j \in \mathcal{I}} a_{ij}$$

| Degree ($k_i$) | Cell Count | Percentage | Cumulative | Topological Role |
| :---: | :---: | :---: | :---: | :--- |
| $1$ | 3 | 0.10% | 0.10% | Peninsula boundary nodes |
| $2$ | 14 | 0.45% | 0.55% | Corner boundary nodes |
| $3$ | 86 | 2.76% | 3.31% | Exterior perimeter nodes |
| $4$ | 145 | 4.66% | 7.97% | Truncated boundary nodes |
| $5$ | 111 | 3.57% | 11.53% | Indented boundary nodes |
| $6$ | 2,754 | 88.47% | 100.00% | Fully interior hexagonal nodes |
| **Total** | **3,113** | **100.00%** | — | — |

### Graph Topology Metrics
* **Minimum Degree ($\min k_i$):** $1$
* **Maximum Degree ($\max k_i$):** $6$
* **Mean Degree ($\bar{k}$):** $5.7655$
* **Isolated Cells ($k_i = 0$):** Exactly $0$ (verified: no islands exist; mesh is singly connected).
* **Boundary Truncated Cells ($k_i < 6$):** $359$ cells ($11.53\%$).
* **Full Interior Cells ($k_i = 6$):** $2,754$ cells ($88.47\%$).
* **Total Non-Zero Adjacency Edges:** $17,948$ directed edges.
* **Spatial Weights Sum ($S_0$):**
  $$S_0 = \sum_{i=1}^{N_e} \sum_{j=1}^{N_e} w_{ij} = \sum_{i=1}^{N_e} 1.0 = 3,113.0$$
* **Row Sum Distribution:** $\min \sum_j w_{ij} = 1.000000$, $\max \sum_j w_{ij} = 1.000000$, $\text{mean} = 1.000000$.

---

## 24.6 Global Moran's I

Global spatial autocorrelation was evaluated on the eligible Risk observation vector $\mathbf{x} \in \mathbb{R}^{3113}$:

$$I = \frac{N_e}{S_0} \frac{\sum_{i=1}^{N_e} \sum_{j=1}^{N_e} w_{ij}(x_i - \bar{x})(x_j - \bar{x})}{\sum_{i=1}^{N_e} (x_i - \bar{x})^2}$$

Because $S_0 = N_e = 3,113.0$, the prefactor $\frac{N_e}{S_0} = 1.0$.

### Numerical Estimates

| Metric | Analytical Randomization | Monte Carlo Permutation ($B=9,999$, seed=42) |
| :--- | :---: | :---: |
| **Observed Moran's $I$** | **+0.781355** | **+0.781355** |
| **Expected Value $E[I]$** | $-0.000321$ ($-\frac{1}{N_e-1} = -\frac{1}{3112}$) | $-0.000457$ (Empirical permutation mean) |
| **Standard Error** | $0.010649$ | $0.010656$ |
| **Standardized Score ($z$)** | $+73.4005$ | $+73.3712$ |
| **$p$-value** | $< 10^{-16}$ (Gaussian tail) | **0.000100** ($p_{\text{pseudo}} = \frac{1 + 0}{10000}$, $p < 0.001$) |
| **Permutation Extreme Count** | — | Exactly $0$ replicates with $|I^{(b)}| \ge 0.781355$ |
| **Permutation Bounds** | — | $\min I^{(b)} = -0.042770, \max I^{(b)} = +0.042381$ |

### Interpretation
The observed Global Moran's $I = +0.781355$ establishes strong, positive spatial autocorrelation across the Pune metropolitan area. Under 9,999 random permutations, the maximum observed Moran statistic was $+0.042381$, which is more than 73 standard errors below the empirical statistic. The null hypothesis of spatial randomness is definitively rejected ($p_{\text{pseudo}} = 0.000100$).

---

## 24.7 Local Moran's I & Multiple Testing

Local spatial association was computed for each cell $i \in \mathcal{I}$:

$$I_i = \frac{x_i - \bar{x}}{m_2} \sum_{j=1}^{N_e} w_{ij}(x_j - \bar{x}), \quad m_2 = \frac{1}{N_e} \sum_{i=1}^{N_e} (x_i - \bar{x})^2$$

### Verification of Mean Identity
The theoretical relationship between local and global statistics was audited:
$$\frac{1}{N_e} \sum_{i=1}^{N_e} I_i = \frac{2430.358249}{3113} = 0.781355038$$
$$\left| \frac{1}{N_e} \sum_{i=1}^{N_e} I_i - I \right| = 3.33 \times 10^{-16} < 10^{-12}$$
The identity holds to machine floating-point precision.

### Local Permutation & $p$-Value Distribution
Under conditional local permutation ($B = 9,999$, seed = 42):
* **Raw $p$-value range:** $\min p_i = 0.000100$, $\text{median} = 0.110000$, $\text{mean} = 0.231104$, $\max p_i = 1.000000$.
* **Unadjusted Significant Cells ($p_i < 0.05$):** $1,079$ cells ($34.66\%$ of eligible mesh).

### Benjamini-Hochberg False Discovery Rate Control ($Q = 0.05$)
Applying the Benjamini-Hochberg procedure across all $M = 3,113$ ranked raw $p$-values:
1. Rank $p_{(1)} \le p_{(2)} \le \dots \le p_{(M)}$.
2. Identify largest $k$ such that $p_{(k)} \le \frac{k}{M} Q$.
3. Compute adjusted $q$-values: $q_{(i)} = \min_{j \ge i} \left( \min\left(1, \frac{M \cdot p_{(j)}}{j}\right) \right)$.
4. Reject null hypothesis for all cells with $q_i \le 0.05$.

* **FDR Threshold Index ($k$):** $339$
* **Critical $p$-value at Threshold ($p_{(339)}$):** $0.005400 \le \frac{339}{3113} \times 0.05 = 0.005445$
* **Statistically Significant Cells ($q_i \le 0.05$):** Exactly **339 cells** ($10.89\%$ of eligible mesh).

---

## 24.8 LISA Cluster Classification

Formulation F-23.1 enforces a strict distinction between descriptive Moran quadrants and inferential LISA clusters:

| Category | High-High (HH) | Low-Low (LL) | High-Low (HL) | Low-High (LH) | Not Significant | Total Eligible |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Descriptive Quadrants (Unfiltered)** | 1,069 (34.34%) | 1,746 (56.09%) | 85 (2.73%) | 213 (6.84%) | 0 (0.00%) | 3,113 (100%) |
| **Inferential LISA Clusters ($q_i \le 0.05$)** | **337 (10.83%)** | **0 (0.00%)** | **0 (0.00%)** | **2 (0.06%)** | **2,774 (89.11%)** | 3,113 (100%) |

```text
LISA Cluster Summary (Inferential):
  * Hotspots (High-High): 337 cells (10.83%)
  * Coldspots (Low-Low): 0 cells (0.00%)
  * Spatial Outliers (Low-High): 2 cells (0.06%)
  * Spatial Outliers (High-Low): 0 cells (0.00%)
  * Not Significant: 2,774 cells (89.11%)
```

### Scientific Diagnostic Observations
1. **Hotspot Consolidation:** While 1,069 cells fall descriptively into the upper-right quadrant ($z_i > 0, L_i > 0$), only **337 cells** exhibit spatial association sufficiently extreme to survive multiple-testing correction ($q_i \le 0.05$). These 337 cells represent statistically verified high-risk spatial clusters (climate risk hotspots).
2. **Coldspot Absence under FDR:** Although 1,746 cells descriptively exhibit below-average risk surrounded by below-average neighbors ($z_i < 0, L_i < 0$), zero Low-Low cells achieve statistical significance after FDR adjustment ($q_i \le 0.05$). This occurs because the baseline risk surface in low-exposure suburban/rural peripheries varies smoothly with lower gradient contrast, yielding larger local permutation $p$-values.
3. **Spatial Outliers:** Exactly two cells (`8960885628bffff` and `8960885628fffff`) are confirmed as statistically significant Low-High spatial outliers ($q_i \le 0.05$), representing localized pockets of low risk embedded directly within elevated regional risk zones.

---

## 24.9 Ward Independence Audit

In strict accordance with the spatial governance mandate (Sections 20 and 23):
* Administrative PMC ward geometries remain **BLOCKED** due to lack of authoritative boundary data.
* No administrative boundary, synthetic ward cluster, or `ward_id` attribute enters the spatial graph construction, spatial weights matrix, Global Moran calculation, permutation engine, or LISA classification.
* Topological contiguity derives strictly and exclusively from the discrete global grid system (Uber H3 Resolution 9).
* Mathematical invariance tests confirm that altering, shuffling, or stripping administrative identifiers produces bitwise-identical spatial autocorrelation statistics ($0.0$ variance).

---

## 24.10 Limitations & Governance Boundaries

1. **Methodological Component Weights:** Component exponents ($\alpha = 1.0, \beta = 1.0, \gamma = 1.0$) remain classified as `CLIMORA_INITIAL_METHODOLOGICAL_ASSUMPTION (PENDING_CALIBRATION)`. They represent equal multiplicative weighting prior to empirical epidemiological validation.
2. **Association vs. Causality:** Moran's $I$ and LISA statistics measure spatial autocorrelation (spatial structure and geographic clustering). They do NOT imply physical or socio-ecological causality.
3. **Significance vs. Intervention Efficacy:** A cell's classification as a statistically significant High-High hotspot establishes that its elevated risk is spatially clustered, not that an urban cooling intervention deployed in that cell is guaranteed to produce optimal municipal mitigation.
4. **Socioeconomic Vulnerability Exclusion:** As governed in Phase 1D, the vulnerability component $V_i$ reflects biophysical susceptibility (impervious surface fraction, lack of canopy cover, lack of water). Socioeconomic sensitivity (income, age distribution, housing structure quality) is not currently represented.
5. **PMC Ward Non-Availability:** Ward-level aggregation remains deferred until authoritative PMC boundary polygons are officially integrated.

---

## 26. FINAL GATE OUTPUT

```text
Phase status: PHASE 1E.1 — PASSED
F-22 status: PASSED (PRESERVED, UNMODIFIED)
F-23.1 status: RATIFIED AND IMPLEMENTED
Analytical population: Eligible H3 analytical mesh only (N_e = 3113)
Eligible cells: 3113
Ineligible cells: 68
Spatial neighborhood: H3 Resolution 9 1-ring topological adjacency
Weight formulation: Row-standardized w_ij = 1/k_i over eligible neighbors; w_ii = 0 (Fixed 1/6 retired)
S0: 3113.0
Global Moran's I: +0.781355
Global permutation p-value: 0.000100 (B = 9999, seed = 42, pseudo-p = (1+0)/(9999+1))
Local permutation method: Conditional local permutation (B = 9999, seed = 42, focal fixed, non-focal permuted without replacement)
BH Q: 0.05 (applied across all N_e = 3113 eligible tests)
Significant LISA cells: 339
HH: 337
LL: 0
HL: 0
LH: 2
Not significant: 2774
Deterministic reproducibility: Verified identical (100% bitwise matching across repeat executions, seed = 42)
Ward dependency: None (ward_id completely decoupled; H3 Res9 graph only)
Risk artifact preserved: Yes (SHA-256: e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677)
Tests: 94 passed (9 dedicated Phase 1E.1 tests in tests/test_phase_1e1_spatial_autocorrelation.py; 85 prior tests green)
Artifacts: data/processed/risk/canonical_spatial_autocorrelation.parquet, data/manifests/spatial_autocorrelation_contract.json, docs/science/climora-mathematical-formulation-register.md, docs/science/phase-1e1-f23-1-ratification-gate.md
Scientific blockers: None (F-23 defects resolved; F-23.1 ratified)
Recommended next phase: Phase 1F: Optimization Layer Formulation & MILP Problem Definition Gate
```
