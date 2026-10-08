# CLIMORA — Uncertainty Propagation & Sensitivity Analysis Framework

**Document Version:** 1.0.0  
**Phase:** Phase 1B Analytical Execution & Scientific Formulation Gate  
**Reference Register:** [`docs/science/climora-mathematical-formulation-register.md`](file:///c:/Users/lenovo/climora/docs/science/climora-mathematical-formulation-register.md)  
**Machine-Readable Contract:** [`data/manifests/scientific_formulation_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/scientific_formulation_contract.json)  
**Status:** **RATIFIED & CANONICAL**  
**Lead Roles:** Lead Scientific Systems Architect, Mathematical Modeler, Geospatial ML Engineer  

---

## 1. Executive Mandate

A common flaw in geospatial climate risk modeling is collapsing disparate uncertainties into an arbitrary single composite percentage (e.g., "$\pm 10\%$ overall error").

CLIMORA strictly rejects this practice.

In accordance with Section 27 and Section 28 of the Scientific Formulation Gate, this framework establishes:
1. A **7-Category Component-Wise Uncertainty Architecture** that maintains explicit lineage from raw physical measurement to final decision metric.
2. Rigorous mathematical conditions under which uncertainties may or may not be aggregated in quadrature.
3. A **Multi-Dimensional Sensitivity Analysis Protocol** testing the structural stability of CLIMORA's risk rankings, hotspot clusters, and intervention allocations.

---

## 2. Seven-Category Uncertainty Architecture

CLIMORA isolates and tracks seven distinct uncertainty categories:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIMORA UNCERTAINTY PROPAGATION STACK                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. SENSOR MEASUREMENT UNCERTAINTY (σ_sensor)                                │
│    • Landsat 8/9 TIRS Band 10 Radiometric Calibration                       │
│    • Documented USGS Level-2 ST RMSE: ±1.0 K to ±1.5 K                      │
│    • Classification: DOCUMENTED_EXTERNAL                                    │
│                                    ↓                                        │
│ 2. ATMOSPHERIC / PROCESSING UNCERTAINTY (σ_atmos)                           │
│    • ASTER GED Emissivity & MERRA-2 Reanalysis Atmospheric Profile Residuals│
│    • Model Residual: ±0.5 K                                                 │
│    • Classification: CLIMORA_ASSUMPTION                                     │
│                                    ↓                                        │
│ 3. SPATIAL AGGREGATION & SUB-GRID HETEROGENEITY (σ_spatial)                 │
│    • Within-cell sample standard deviation s_{i,t} (range 1.2°C to 2.8°C)   │
│    • Positive Spatial Autocorrelation (Moran's I > 0)                       │
│    • Ban on σ / sqrt(n) independent-pixel standard error                    │
│    • Classification: DERIVED                                                │
│                                    ↓                                        │
│ 4. TEMPORAL SAMPLING & INTERANNUAL VARIABILITY (σ_temporal)                 │
│    • 5-Year Pre-Monsoon Baseline Interannual Standard Deviation σ_base      │
│    • Range: 0.8°C to 2.1°C across valid baseline years (K_valid >= 4)       │
│    • Morning Overpass (~10:30 AM) vs Diurnal Peak Heat (3:00 PM) Offset     │
│    • Classification: DERIVED & DOCUMENTED_EXTERNAL                          │
│                                    ↓                                        │
│ 5. DEMOGRAPHIC DASYMETRIC UNCERTAINTY (σ_pop)                               │
│    • WorldPop 1km Random Forest Disaggregation: ±15% relative uncertainty   │
│    • Residential Nighttime Census Baseline vs Diurnal Commuter Flow Influx   │
│    • Classification: CLIMORA_ASSUMPTION                                     │
│                                    ↓                                        │
│ 6. PROXY / MODEL STRUCTURAL UNCERTAINTY (σ_proxy)                           │
│    • Biophysical Susceptibility (1 - NDVI, NDBI) as physical heat proxy     │
│    • Complete absence of parcel-level socioeconomic vulnerability data      │
│    • Classification: METHODOLOGICAL_BOUNDARY                                │
│                                    ↓                                        │
│ 7. INTERVENTION SCENARIO UNCERTAINTY (σ_scenario)                           │
│    • Expected Cool Roof & Urban Canopy Cooling Effect: ±30% variance        │
│    • Literature-derived estimates; NEVER presented as observed facts        │
│    • Classification: SCENARIO_ASSUMPTION                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mathematical Propagation Rules

### 3.1 Strict Conditions for Quadrature Summation
Uncertainties may be combined using root-sum-of-squares (quadrature) **ONLY** when the constituent components are proven to be mutually uncorrelated, linearly independent, and additive:

$$\sigma_{\text{quad}} = \sqrt{\sum_{k=1}^K \sigma_k^2}$$

* **Valid Application:** Combining instrument sensor noise ($\sigma_{\text{sensor}} \approx 1.0\text{ K}$) with independent atmospheric transmission inversion noise ($\sigma_{\text{atmos}} \approx 0.5\text{ K}$):
  $$\sigma_{\text{physical\_lst}} = \sqrt{1.0^2 + 0.5^2} \approx 1.12\text{ K}$$

### 3.2 Prohibited Aggregations & Component-Wise Rule
* **STRICT PROHIBITION 1 (Spatial Autocorrelation):** Combining spatial sub-grid variance $s_{i, t}$ into measurement uncertainty via $s / \sqrt{N}$ is **MATHEMATICALLY DISQUALIFIED**. Pixels within an H3 hexagon exhibit strong positive spatial autocorrelation ($\text{Moran's } I > 0$).
* **STRICT PROHIBITION 2 (Cross-Domain Collapse):** Collapsing physical temperature uncertainty ($^\circ\text{C}$) and demographic disaggregation uncertainty ($\%$) into a single composite uncertainty index is prohibited.
* **Component-Wise Mandate:** Every H3 cell record in CLIMORA must preserve a structured **Uncertainty Vector**:
  $$\mathbf{U}_i = \begin{bmatrix} \sigma_{\text{sensor}} \\ \sigma_{\text{atmos}} \\ s_{i, t} \\ \sigma_{\text{base}, i} \\ \sigma_{\text{pop}, i} \\ \sigma_{\text{scenario}, i} \end{bmatrix}$$

---

## 4. Multi-Dimensional Sensitivity Analysis Protocol

To ensure that analytical conclusions are robust and not artifacts of arbitrary parameter choices, CLIMORA defines explicit sensitivity sweeps across seven key dimensions:

| Parameter / Assumption | Default Baseline | Sensitivity Test Range | Evaluation Metric | Governance Status |
| :--- | :---: | :---: | :--- | :---: |
| **Risk Exponent $\alpha$ (Hazard)** | $1.0$ | $[0.5, 2.0]$ (step 0.25) | Spearman rank correlation of Risk | `PENDING_CALIBRATION` |
| **Risk Exponent $\beta$ (Exposure)** | $1.0$ | $[0.5, 2.0]$ (step 0.25) | Hotspot spatial overlap (Jaccard index) | `PENDING_CALIBRATION` |
| **Risk Exponent $\gamma$ (Susceptibility)** | $1.0$ | $[0.5, 2.0]$ (step 0.25) | Top-100 high-risk cell turnover rate | `PENDING_CALIBRATION` |
| **Normalization Method** | Linear Min-Max | Min-Max vs Quantile Rank vs Robust Winsorized ($P_2 - P_{98}$) | Outlier suppression & rank stability | `IMPLEMENTED` |
| **Hazard Sub-Weights ($w_H$)** | Equal ($0.25$) | Dirichlet random walk $[0.10, 0.40]$ | Hazard index variance distribution | `PENDING_CALIBRATION` |
| **Valid Pixel Coverage Gate** | $\ge 70\%$ | $60\%, 70\%, 80\%$ | Cell drop-out rate across 3,181 cells | `IMPLEMENTED` |
| **Extreme LST Threshold** | $45.0^\circ\text{C}$ | $43.0^\circ\text{C}, 45.0^\circ\text{C}, 47.0^\circ\text{C}$ | Recurrence distribution skewness | `IMPLEMENTED` |
| **Demographic Disaggregation** | Central Count | $[-15\%, +15\%]$ perturbation | Population-weighted cooling benefit | `ASSUMPTION` |
| **Intervention Cooling Effect** | Literature Mean | $[-30\%, +30\%]$ variance | Multi-objective Pareto frontier shift | `ASSUMPTION` |

---

## 5. Local Elasticity and Global Sobol Decomposition

### 5.1 Local Logarithmic Elasticity
For any individual H3 cell $i$, the local sensitivity of the multiplicative risk score $\text{Risk}_i = \mathcal{H}_i^\alpha \mathcal{E}_i^\beta \mathcal{V}_i^\gamma$ with respect to the exponents is evaluated analytically via logarithmic derivatives:

$$S_\alpha = \frac{\partial \ln \text{Risk}_i}{\partial \ln \alpha} = \alpha \ln \mathcal{H}_i$$
$$S_\beta = \frac{\partial \ln \text{Risk}_i}{\partial \ln \beta} = \beta \ln \mathcal{E}_i$$
$$S_\gamma = \frac{\partial \ln \text{Risk}_i}{\partial \ln \gamma} = \gamma \ln \mathcal{V}_i$$

Because normalized inputs $\mathcal{H}_i, \mathcal{E}_i, \mathcal{V}_i \in (0.0, 1.0]$, their natural logarithms are strictly negative or zero. The component with the lowest normalized score exhibits the steepest relative dampening effect on composite risk.

### 5.2 Global Variance Decomposition (Sobol Indices)
To assess how much parameter uncertainty drives the total spatial variance of risk across the 3,181 hexagons of Pune, CLIMORA formulates the first-order Sobol sensitivity index:

$$S_k = \frac{\text{Var}_{p_k}\left(E_{\mathbf{p}_{\sim k}}[\text{Risk} \mid p_k]\right)}{\text{Var}(\text{Risk})}$$

and total-order index:

$$S_{Tk} = 1 - \frac{\text{Var}_{\mathbf{p}_{\sim k}}\left(E_{p_k}[\text{Risk} \mid \mathbf{p}_{\sim k}]\right)}{\text{Var}(\text{Risk})}$$

where $\mathbf{p} = \{\alpha, \beta, \gamma, w_H, w_E, w_V\}$. If $S_{Tk} - S_k \approx 0$, parameter interactions are negligible, confirming that the multiplicative structure behaves cleanly and transparently across the urban domain.
