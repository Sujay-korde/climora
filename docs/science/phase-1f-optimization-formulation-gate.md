# CLIMORA — PHASE 1F: OPTIMIZATION LAYER FORMULATION & MILP PROBLEM DEFINITION GATE REPORT

**Document Version:** 1.0.0  
**Phase:** Phase 1F Optimization Formulation Gate  
**Contract Companion:** [`data/manifests/optimization_formulation_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/optimization_formulation_contract.json)  
**Mathematical Register:** [`docs/science/climora-mathematical-formulation-register.md`](file:///c:/Users/lenovo/climora/docs/science/climora-mathematical-formulation-register.md)  
**Status:** **PHASE 1F — PASSED**  
**Lead Roles:** Senior Scientific Architect, Operations Research Scientist, Geospatial Optimization Engineer, and Forensic Model Governance Engineer  
**Date:** 2026-10-02  

---

## 1. Executive Summary

```text
================================================================================
FINAL DECISION: PHASE 1F — PASSED
================================================================================
```

The CLIMORA Optimization Layer Formulation & MILP Problem Definition Gate has completed its forensic evaluation. This phase establishes and ratifies the exact mathematical contract governing the transformation:

$$\text{Risk Surface} \longrightarrow \text{Candidate Interventions} \longrightarrow \text{Feasible Portfolio} \longrightarrow \text{Modeled Impact} \longrightarrow \text{Cost} \longrightarrow \text{Budget-Constrained Optimization} \longrightarrow \text{Explainable Allocation}$$

In strict accordance with the Phase 1F mandate, this is a **formulation gate**. The full production optimizer has not been prematurely implemented; instead, the mathematical foundations, decision variables, physical constraints, microclimatic impact transfer equations, and solver-independent MILP matrix specifications have been formally derived, codified in the mathematical formulation register (Formulations F-24.1 through F-24.6 and F-25.1), locked in a canonical JSON contract, and empirically verified via a deterministic synthetic MILP solver test suite.

Upstream foundations remain preserved byte-for-byte:
* **F-22 Canonical Risk Surface:** [`data/processed/risk/canonical_risk_surface.parquet`](file:///c:/Users/lenovo/climora/data/processed/risk/canonical_risk_surface.parquet) checksum verified unchanged (SHA-256: `e2d5df6c7a0a9584367a623b0722e87f3f4340ea5ebf297cb5aaed6533da5677`).
* **F-23.1 Spatial Autocorrelation & LISA Significance:** [`data/processed/risk/canonical_spatial_autocorrelation.parquet`](file:///c:/Users/lenovo/climora/data/processed/risk/canonical_spatial_autocorrelation.parquet) verified unmodified.
* **PMC Ward Geometry:** Remains completely decoupled ($0$ dependency; no administrative polygons or synthetic cluster approximations entered the optimization formulation).
* **Automated Verification:** All 102 unit tests in the repository pass green.

---

## 2. Existing Architecture Audit

A thorough audit of the repository's formulation register, analytical contracts, data parquets, and processing code was conducted prior to formulation design:

1. **Prior Formulation Register State:** Group 10 previously contained a single draft placeholder (`F-24`) specifying:
   $$\max \Phi = \lambda_1 \sum C_i \sum \Delta T_j x_{j,i} + \lambda_2 \sum \text{Infra}_i \sum \Delta T_j x_{j,i} - \lambda_3 \text{Gini}(\text{Benefit})$$
   *Forensic Findings:* The legacy draft suffered from severe dimensional inconsistency (summing person-degrees, infrastructure-degrees, and unitless Gini coefficients with arbitrary $\lambda$ multipliers), lacked connection to CLIMORA's canonical Risk model ($\text{Risk}_i = H_i E_i V_i$), lacked semi-continuous minimum batch linking, and lacked physical mutual compatibility constraints.
2. **Prior Codebase Audit:** Confirmed that **zero optimization code** previously existed in `processing/`, eliminating any risk of duplicate or competing optimization engines.
3. **Input Data Inventory:** Confirmed that the 57-column [`data/processed/canonical_feature_matrix.parquet`](file:///c:/Users/lenovo/climora/data/processed/canonical_feature_matrix.parquet) contains all required morphology and biophysical attributes (`cell_area_km2`, `norm_ndbi`, `road_length_m`, `green_space_area_m2`, `water_body_area_m2`, `norm_ndvi_deficit`) to support rigorous candidate eligibility and capacity bounding without fabricating unavailable engineering datasets.

---

## 3. Intervention Ontology

CLIMORA ratifies a generic, plugin-like catalog $\mathcal{A}$ containing five core physical heat-adaptation interventions:

| Intervention Code ($a$) | Name | Category | Physical Unit | Unit Cost ($c_a$) | Mobilization ($F_a$) | Min Lot ($q^{\min}_a$) | Cooling Rate ($e_a$) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `cool_roofs` | Solar Reflective Roof Coating | Albedo Modification | $\text{m}^2\text{ roof}$ | ₹250.0 / $\text{m}^2$ | ₹25,000 | $500\text{ m}^2$ | $2.381 \times 10^{-5}\,^\circ\text{C / m}^2$ |
| `street_trees` | Street Tree Canopy Planting | Nature-Based | tree count | ₹3,500.0 / tree | ₹20,000 | 25 trees | $7.143 \times 10^{-4}\,^\circ\text{C / tree}$ |
| `green_corridor` | Green Corridor & Pocket Park | Nature-Based | $\text{m}^2\text{ ground}$ | ₹800.0 / $\text{m}^2$ | ₹50,000 | $200\text{ m}^2$ | $3.048 \times 10^{-5}\,^\circ\text{C / m}^2$ |
| `permeable_surfaces` | Permeable Pavement / Pavers | Water / Structural | $\text{m}^2\text{ ground}$ | ₹1,800.0 / $\text{m}^2$ | ₹40,000 | $200\text{ m}^2$ | $1.429 \times 10^{-5}\,^\circ\text{C / m}^2$ |
| `bioswales` | Vegetated Bioretention Swale | Water Infrastructure | $\text{m}^2\text{ ground}$ | ₹2,200.0 / $\text{m}^2$ | ₹40,000 | $100\text{ m}^2$ | $1.905 \times 10^{-5}\,^\circ\text{C / m}^2$ |

*Currency & Price Basis:* Indian Rupees (INR, ₹), constant 2025 price basis.

---

## 4. Decision-Variable Formulation (F-24.1)

To reconcile real-world contractor logistics with mathematical tractability, CLIMORA ratifies a **Mixed-Integer Linear Programming (MILP) semi-continuous formulation**:

For each eligible cell $i \in \mathcal{I}$ ($N_e = 3,113$) and intervention $a \in \mathcal{A}$:
* **Binary Activation Variable:** $x_{i, a} \in \{0, 1\}$ (indicates whether intervention $a$ is deployed in cell $i$).
* **Continuous Allocation Quantity:** $q_{i, a} \ge 0$ (physical quantity deployed in units of intervention $a$).
* **Semi-Continuous Operational Linking:**
  $$q^{\min}_a \cdot x_{i, a} \le q_{i, a} \le Q^{\max}_{i, a} \cdot x_{i, a} \quad \forall i \in \mathcal{I}, a \in \mathcal{A}$$

*Rationale:* In municipal capital deployment, contractor mobilization requires a non-trivial minimum project scale ($q^{\min}_a$). Allowing purely continuous variables without activation thresholds produces economically absurd allocations (e.g. allocating $1.2\text{ m}^2$ of cool roof or $0.3$ trees to a cell). The semi-continuous MILP structure enforces that if a cell is activated ($x_{i, a} = 1$), it receives at least the minimum viable lot size ($q_{i, a} \ge q^{\min}_a$).

---

## 5. Candidate Eligibility Formulation (F-24.2)

Candidate eligibility is governed by binary feasibility indicators $C_{i, a} \in \{0, 1\}$:

$$x_{i, a} \le C_{i, a} \quad \forall i \in \mathcal{I}, a \in \mathcal{A}$$

Eligibility is evaluated strictly using observable satellite and spatial features from [`data/processed/canonical_feature_matrix.parquet`](file:///c:/Users/lenovo/climora/data/processed/canonical_feature_matrix.parquet):

1. **Analytical Mesh Boundary Rule:** For all 68 disqualified cells ($K_{\text{valid}, i} < 4$), $C_{i, a} = 0$ for all $a$. Disqualified cells are strictly excluded from allocation.
2. **Cool Roofs:** $C_{i, \text{roof}} = \mathbb{I}(\text{overall\_risk\_eligibility}_i \land \text{norm\_ndbi}_i > 0.05)$ (requires confirmed built-up footprint).
3. **Street Trees:** $C_{i, \text{trees}} = \mathbb{I}(\text{overall\_risk\_eligibility}_i \land \text{road\_length\_m}_i > 0)$ (requires public right-of-way).
4. **Green Corridors:** $C_{i, \text{corridor}} = \mathbb{I}(\text{overall\_risk\_eligibility}_i \land \text{norm\_ndvi\_deficit}_i > 0.15)$ (requires vegetation deficit and open space).
5. **Permeable Surfaces:** $C_{i, \text{perm}} = \mathbb{I}(\text{overall\_risk\_eligibility}_i \land \text{norm\_ndbi}_i > 0.10 \land \text{road\_length\_m}_i > 0)$ (requires paved impervious non-roof corridors).
6. **Bioswales:** $C_{i, \text{bioswale}} = \mathbb{I}(\text{overall\_risk\_eligibility}_i \land \text{road\_length\_m}_i \ge 100.0\text{ m})$ (requires sufficient linear roadside drainage context).

---

## 6. Capacity Formulation (F-24.2)

Physical capacity upper bounds $Q^{\max}_{i, a}$ prevent physically impossible over-allocation:

* **Cool Roofs:** $Q^{\max}_{i, \text{roof}} = f_{\text{roof}} \cdot \text{norm\_ndbi}_i \cdot A_{\text{cell}, i}$, where $f_{\text{roof}} = 0.40$ (planning heuristic: up to 40% of built-up footprint represents treatable horizontal rooftop).
* **Street Trees:** $Q^{\max}_{i, \text{trees}} = \min\left(N^{\max}_{\text{trees}}, \lfloor \frac{2 \cdot \text{road\_length\_m}_i}{d_{\text{tree\_spacing}}} \rfloor\right)$, with $d_{\text{tree\_spacing}} = 15.0\text{ m}$, $N^{\max}_{\text{trees}} = 800$.
* **Green Corridors:** $Q^{\max}_{i, \text{corridor}} = f_{\text{corridor}} \cdot A_{\text{open}, i}$, where $A_{\text{open}, i} = \max(0, A_{\text{cell}, i} - \text{green\_space\_area\_m2}_i - \text{water\_body\_area\_m2}_i - \text{norm\_ndbi}_i A_{\text{cell}, i})$ and $f_{\text{corridor}} = 0.10$.
* **Permeable Surfaces:** $Q^{\max}_{i, \text{perm}} = f_{\text{pave}} \cdot \text{road\_length\_m}_i \cdot w_{\text{pavement}}$, with $w_{\text{pavement}} = 3.0\text{ m}$, $f_{\text{pave}} = 0.20$.
* **Bioswales:** $Q^{\max}_{i, \text{bioswale}} = f_{\text{swale}} \cdot \text{road\_length\_m}_i \cdot w_{\text{swale}}$, with $w_{\text{swale}} = 2.0\text{ m}$, $f_{\text{swale}} = 0.05$.

---

## 7. Cost Formulation (F-24.3)

Cost consists of fixed cell contractor mobilization overhead ($F_a$) and variable implementation expenditure ($c_a$):

$$\text{Cost}_{i, a}(x_{i, a}, q_{i, a}) = F_a \cdot x_{i, a} + c_a \cdot q_{i, a}$$

Total portfolio expenditure must satisfy the municipal scenario budget constraint:

$$\text{TotalCost} = \sum_{i \in \mathcal{I}} \sum_{a \in \mathcal{A}} \left( F_a \cdot x_{i, a} + c_a \cdot q_{i, a} \right) \le B$$

*Note on Budget Envelope:* The ₹10,000,000 (₹10M) budget specified in hackathon documentation is classified as a **scenario demonstration envelope**, not a fixed statutory municipal ceiling. The solver supports any positive scenario budget $B > 0$.

---

## 8. Impact Formulation (F-24.4)

### Critical Distinction: Modeled Impact ≠ Observed Impact
All projected cooling effects are strictly classified under the truth layer as **`MODELED` SCENARIO ASSUMPTIONS**. They must **NEVER** be described as measured, observed, or verified satellite cooling.

Local surface temperature reduction is modeled via literature-derived microclimatic transfer coefficients:

$$\Delta T_i^{\text{model}} = \sum_{a \in \mathcal{A}} e_a \cdot q_{i, a}$$

Subject to thermodynamic saturation capping:

$$\Delta T_i^{\text{model}} \le \Delta T^{\max}_{\text{cap}} = 4.0^\circ\text{C}$$

*Additivity Policy:* Microclimatic impacts within a cell are modeled as additive scenario assumptions up to the saturation cap. Complex non-linear microclimatic interactions are not empirically calibrated and are deliberately omitted to preserve exact MILP convexity.

---

## 9. Risk-Reduction Formulation (F-24.5)

CLIMORA rejects arbitrary "magic score" objectives. Risk reduction is derived mathematically from canonical Formulation F-22:

$$\text{Risk}_i = H_i E_i V_i$$

Holding human exposure $E_i$ fixed, the marginal response of cell risk to an intervention $a$ is:

$$r_{i, a} = E_i \left( V_i \frac{0.25 \cdot e_a}{\Delta T_{\text{scale}}} + H_i \frac{v_a}{A_{\text{cell}, i}} \right)$$

where:
* $\Delta T_{\text{scale}} = 15.0^\circ\text{C}$ (Phase 1C normalization span);
* $w_{\text{LST}} = 0.25$ (F-19 Hazard component weight);
* $v_a$ is the biophysical susceptibility reduction factor ($v_{\text{corridor}} = 0.315$, $v_{\text{trees}} = 11.25\text{ m}^2/\text{tree}$, $v_{\text{perm}} = 0.225$, $v_{\text{bioswale}} = 0.270$, $v_{\text{roof}} = 0.0$).

Total modeled cell risk reduction is linear in allocated quantities:

$$\Delta \text{Risk}_i = \sum_{a \in \mathcal{A}} r_{i, a} \cdot q_{i, a}$$

*Zero-Exposure Axiom:* If $E_i = 0$, then $r_{i, a} = 0 \implies \Delta \text{Risk}_i = 0$. Interventions deployed in uninhabited cells with zero civic infrastructure yield zero human climate risk reduction.

---

## 10. Objective Formulation (F-24.6)

The primary canonical optimization objective maximizes total aggregate climate risk reduction across the eligible municipal analytical mesh:

$$\max_{\{x_{i, a}, q_{i, a}\}} \quad \Phi = \sum_{i \in \mathcal{I}} \sum_{a \in \mathcal{A}} r_{i, a} \cdot q_{i, a}$$

*Dimensional Coherence:* $\Phi$ is dimensionless, matching canonical $\text{Risk}_i \in [0.0, 1.0]$. Because $r_{i, a} \propto E_i$, maximizing $\Phi$ naturally directs capital to highly exposed, high-hazard, high-susceptibility communities without requiring arbitrary policy weighting multipliers.

---

## 11. Constraint Formulation

Every optimization rule is strictly classified as a **Hard Constraint**:

| Constraint | Mathematical Form | Classification | Provenance | Rationale |
| :--- | :--- | :---: | :--- | :--- |
| **Total Budget** | $\sum_i \sum_a (F_a x_{i,a} + c_a q_{i,a}) \le B$ | **HARD** | Scenario Envelope | Financial capital cannot exceed available budget. |
| **Semi-Continuous Lot** | $q^{\min}_a x_{i,a} \le q_{i,a}$ | **HARD** | Contractor Logistics | Prevents economically non-viable micro-allocations. |
| **Cell Capacity** | $q_{i,a} \le Q^{\max}_{i,a} x_{i,a}$ | **HARD** | Satellite Morphology | Physical land area cannot be over-allocated. |
| **Candidate Eligibility**| $x_{i,a} \le C_{i,a}$ | **HARD** | Missingness & Physics | Ineligible and cloud-masked cells cannot be treated. |
| **Ground Compatibility**| $q_{\text{corridor}} + q_{\text{perm}} + q_{\text{swale}} \le A_{\text{ground}}$ | **HARD** | Spatial Geometry | Ground interventions compete for open surface area. |
| **Roof Compatibility** | $q_{\text{roof}} \le A_{\text{roof}}$ | **HARD** | Structural Geometry | Cool roofs cannot exceed building roof footprint. |
| **Integrality** | $x_{i,a} \in \{0, 1\}$ | **HARD** | MILP Formulation | Activation is discrete. |
| **Non-Negativity** | $q_{i,a} \ge 0$ | **HARD** | Physical Axiom | Negative intervention quantities are impossible. |

---

## 12. Solver-Independent MILP Specification

The canonical CLIMORA optimization problem is expressed in standard matrix form:

$$\min_{\mathbf{y}} \quad \mathbf{c}^T \mathbf{y} \quad \text{s.t.} \quad \mathbf{A} \mathbf{y} \le \mathbf{b}, \quad \mathbf{y}_L \le \mathbf{y} \le \mathbf{y}_U, \quad y_j \in \mathbb{Z} \text{ for } j \in J$$

where $\mathbf{y} = [\mathbf{x}^T, \mathbf{q}^T]^T \in \mathbb{R}^{2 \cdot N_e \cdot |\mathcal{A}|}$, with objective vector $\mathbf{c} = [\mathbf{0}^T, -\mathbf{r}^T]^T$.

*Solver Independence:* This standard representation is solvable by any certified MILP solver (HiGHS, CBC, Google OR-Tools, Gurobi). For Python 3.13, the reference open-source engine is **SciPy's `scipy.optimize.milp`** (backed by the HiGHS branch-and-cut solver), which requires zero commercial licenses.

---

## 13. Explainability Contract

Every optimized allocation output $\mathbf{y}^*$ must support end-to-end explainability:
1. **Selection Provenance:** Record baseline $H_i, E_i, V_i, \text{Risk}_i$, and LISA cluster classification for each treated cell.
2. **Marginal ROI:** Compute marginal risk reduction per rupee spent: $\text{ROI}_{i, a} = \frac{r_{i, a}}{c_a}$.
3. **Binding Constraints:** Identify whether allocation was constrained by budget, cell capacity ($Q^{\max}_{i, a}$), or minimum lot size ($q^{\min}_a$).
4. **Beneficiaries:** Calculate human population residing within treated cells: $\text{Pop}_{\text{treated}} = \sum_{i : \sum_a x_{i,a} \ge 1} \text{population\_2020}_i$.

---

## 14. Edge Cases

The mathematical contract explicitly defines behavior under edge cases:
* **Zero Budget ($B = 0$):** Returns feasible all-zero vector ($x = 0, q = 0, \text{TotalCost} = 0, \Phi = 0$).
* **Insufficient Budget ($B < \min_a (F_a + c_a q^{\min}_a)$):** Returns feasible all-zero vector without crashing.
* **No Eligible Candidates ($C_{i, a} = 0 \, \forall i, a$):** Returns empty portfolio.
* **Zero Modeled Impact ($r_{i, a} = 0$):** Never allocated by the solver because objective coefficient is zero.

---

## 15. Scientific Assumption Register

| Assumption | Value | Unit | Classification | Evidence / Source | Sensitivity Required |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **Roof Treatable Ratio ($f_{\text{roof}}$)** | 0.40 | fraction | `METHODOLOGICAL_ASSUMPTION` | NRDC / Mahila Housing Trust India | Yes ($\pm 25\%$) |
| **Tree Spacing ($d_{\text{tree\_spacing}}$)** | 15.0 | meters | `ENGINEERING_ASSUMPTION` | Urban Forestry Guidelines | Yes ($\pm 20\%$) |
| **Cool Roof Unit CapEx** | 250.0 | INR / $\text{m}^2$ | `SCENARIO_INPUT` | Pune Municipal Benchmark 2025 | Yes ($\pm 20\%$) |
| **Street Tree Unit CapEx** | 3,500.0 | INR / tree | `SCENARIO_INPUT` | PMC Tree Authority Schedule | Yes ($\pm 20\%$) |
| **Cool Roof Cooling Rate ($e_{\text{roof}}$)** | $2.381 \times 10^{-5}$ | $^\circ\text{C / m}^2$ | `MODELED` | Akbari et al. / Santamouris | Yes ($\pm 30\%$) |
| **Tree Cooling Rate ($e_{\text{trees}}$)** | $7.143 \times 10^{-4}$ | $^\circ\text{C / tree}$ | `MODELED` | Bowler et al. / Urban Tree Canopy | Yes ($\pm 30\%$) |
| **Additive Impact Assumption** | Additive | — | `METHODOLOGICAL_ASSUMPTION` | Linearized microclimate model | Yes |

---

## 16. Known Limitations

The Phase 1F optimization formulation adheres to strict scientific boundaries:
1. **No Heat-Health Outcome Claims:** Optimization maximizes modeled physical risk reduction; it does not claim to predict reductions in clinical mortality or hospital admissions.
2. **No Socioeconomic Vulnerability Fabrication:** Susceptibility remains strictly biophysical ($1 - \text{NDVI}$ and $\text{NDBI}$).
3. **Modeled vs. Observed:** Modeled cooling effects are scenario projections, not observed satellite measurements.
4. **No Causal Attribution:** Physical cooling efficacy requires post-deployment MRV (Formulation F-26).
5. **No PMC Ward Dependency:** Optimization operates strictly on H3 cells; ward-level optimization is prohibited until authoritative PMC boundary polygons are officially acquired.
6. **No "Universal Optimality" Claims:** Solutions are optimal **only relative to the specified linear mathematical objective and constraints**.

---

## 17. Formulation Register Amendments

The CLIMORA Mathematical Formulation Register ([`docs/science/climora-mathematical-formulation-register.md`](file:///c:/Users/lenovo/climora/docs/science/climora-mathematical-formulation-register.md)) has been formally updated with seven ratified formulation entries:
* **F-24.1:** Semi-Continuous Intervention Decision Variables & Minimum Lot-Size Linking.
* **F-24.2:** Candidate-Site Spatial Eligibility & Physical Capacity Bounds.
* **F-24.3:** Intervention Cost Model (CapEx & Mobilization Overhead).
* **F-24.4:** Linearized Modeled Microclimate & Biophysical Impact.
* **F-24.5:** Marginal Climate Risk Reduction Response.
* **F-24.6:** Canonical Budget-Constrained Risk Reduction MILP Optimization Problem.
* **F-25.1:** Modeled Post-Intervention State & Thermodynamic Safety Boundaries.

---

## 18. Test Plan & Synthetic MILP Validation

The formulation test suite ([`tests/test_phase_1f_optimization_formulation.py`](file:///c:/Users/lenovo/climora/tests/test_phase_1f_optimization_formulation.py)) implements eight focused tests:
1. `test_contract_manifest_integrity`: Validates JSON contract schema and 5-intervention catalog.
2. `test_dimensional_coherence_and_zero_exposure_axiom`: Validates mathematical units and verifies $E_i = 0 \implies r_{i, a} = 0$.
3. `test_synthetic_milp_solver_optimality`: Solves a synthetic 3-cell, 2-intervention MILP problem to proven HiGHS optimality; verifies budget, lot size, capacity, integrality, and eligibility constraints.
4. `test_synthetic_milp_deterministic_reproducibility`: Proves 100% bitwise reproducibility across repeat solver runs.
5. `test_edge_case_zero_budget`: Verifies $B = 0 \implies x = 0, q = 0$.
6. `test_edge_case_insufficient_budget`: Verifies insufficient budget returns feasible all-zero vector.
7. `test_edge_case_no_eligible_candidates`: Verifies $C = 0$ returns feasible all-zero vector.
8. `test_ward_independence_decoupling`: Verifies complete decoupling from administrative ward geometries.

---

## 19. Final Gate Decision

```text
PHASE 1F STATUS: PASSED

Optimization formulation: RATIFIED
Decision variables: RATIFIED (Semi-continuous MILP: F-24.1)
Candidate eligibility: RATIFIED (Spatial predicates on eligible mesh: F-24.2)
Capacity model: RATIFIED (Physical morphology bounds: F-24.2)
Cost model: RATIFIED (CapEx + fixed mobilization: F-24.3)
Impact model: RATIFIED (Modeled scenario transfer rates: F-24.4)
Risk-reduction formulation: RATIFIED (Linear response of Risk = H*E*V: F-24.5)
Objective: RATIFIED (Maximize aggregate risk reduction: F-24.6)
Constraints: RATIFIED (Hard budget, capacity, compatibility, lot size: F-24.6)
Dimensional analysis: VERIFIED (Dimensionless objective; consistent units)
Synthetic MILP validation: PASSED (SciPy / HiGHS deterministic solve)
Scientific formulation register: AMENDED & RATIFIED (F-24.1 to F-24.6, F-25.1)
Optimization contract: RATIFIED (data/manifests/optimization_formulation_contract.json)
Previous formulations preserved: YES (F-22 and F-23.1 unchanged)
Ward dependency: NONE (H3 Res9 mesh only)
Production optimizer implemented: NO (Formulation Gate only)
```
