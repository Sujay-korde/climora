# CLIMORA — Phase 1C.1a: PMC Ward Spatial Assignment Gate Report

**Document ID:** `CLIMORA-REPORT-PHASE-1C1A-WARD-GATE-V1`  
**Phase:** Phase 1C.1a (PMC Ward Spatial Assignment Correction Gate)  
**Status:** **BLOCKED — AUTHORITATIVE PMC WARD GEOMETRY NOT LOCATED**  
**Ratified At:** 2026-10-02T14:35:00Z  
**Primary Roles:** Chief Systems Architect, Scientific Data Engineer, Geospatial Scientist, Mathematical Modeler, Data Lineage Auditor, Statistical Quality Engineer, CLIMORA Hackathon Lead Engineer  
**Machine-Readable Contract Reference:** [`data/manifests/canonical_feature_matrix_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/canonical_feature_matrix_contract.json)  
**Companion Architecture:** [`docs/architecture/phase-1b-spatial-unit-decision.md`](file:///c:/Users/lenovo/climora/docs/architecture/phase-1b-spatial-unit-decision.md)  

---

## 1. Executive Decision

In strict accordance with the Governing Principles of Phase 1C.1a:

> **"If authoritative ward polygons cannot be found, STOP and report: `BLOCKED — AUTHORITATIVE PMC WARD GEOMETRY NOT LOCATED`. Do not fabricate a replacement."**  
> **"Do not invent ward geometries. Do not create synthetic ward polygons. Do not use k-means, clustering, Voronoi partitioning, nearest-centroid clustering, or any statistical clustering as a substitute for administrative boundaries."**

An exhaustive forensic search across all repository directories (`data/`, `docs/`, `processing/`, `ingestion/`, and `data/manifests/`) was conducted. 

### Findings:
1. **Authoritative Ward Polygons Not Found:** The repository does **NOT** contain an authoritative vector polygon dataset representing the 41 administrative Prabhag wards of the Pune Municipal Corporation (PMC).
2. **Current `ward_id` Provenance:** The 41 values currently populated in `ward_id` (`PMC_WARD_01` to `PMC_WARD_41`) were generated in Phase 1C via unsupervised spatial centroid clustering (`sklearn.cluster.KMeans(n_clusters=41, random_state=42)`) applied to H3 cell centroids in [`processing/feature_matrix.py`](file:///c:/Users/lenovo/climora/processing/feature_matrix.py#L57-L75).
3. **Scientific Disqualification:** Statistical clustering of hexagon centroids is **scientifically invalid** as a representation of statutory administrative ward boundaries. It produces geometric Voronoi-like convex partitions that bear no legal or physical correspondence to the actual municipal ward delimitation gazetted by the State Election Commission of Maharashtra or PMC.
4. **Refusal to Fabricate:** Under the absolute stop conditions of Section 2, Section 3, and Section 14 of the Phase 1C.1a charter, the Directorate refuses to fabricate synthetic ward boundaries or maintain statistical clustering under the false guise of administrative truth.

### Official Gate Decision:
> **GATE STATUS: BLOCKED — AUTHORITATIVE PMC WARD GEOMETRY NOT LOCATED**  
> **Action Required:** Ingest the authoritative 41 PMC administrative ward polygon boundary file (GeoJSON/Shapefile) from official municipal/governmental open data sources before ratifying administrative ward spatial membership. The canonical feature matrix is held at Phase 1C.1 with `ward_id` explicitly flagged as `SYNTHETIC_STATISTICAL_CLUSTER_PROXY (PENDING_STATUTORY_WARD_DATA)`.

---

## 2. Authoritative Ward Source Search

A comprehensive audit of every file and directory in the repository was executed:

| Directory Inspected | Asset Types Checked | Findings |
| :--- | :--- | :--- |
| `data/aoi/` | `.geojson` | Only [`data/aoi/pune.geojson`](file:///c:/Users/lenovo/climora/data/aoi/pune.geojson) exists. Contains exactly 1 feature: outer statutory boundary of Pune Municipal Corporation (`osm_relation_id: 10351626`, `admin_level: 6`, area $312.11\text{ km}^2$). **Zero internal ward polygons.** |
| `data/raw/osm/pune/` | `.geojson`, `.json` | Contains extracts for `green_spaces.geojson` (602 features), `water_bodies.geojson` (357 features), `public_infrastructure.geojson` (1,268 features), and `road_network.geojson` (2,138 features). Overpass extraction script [`ingestion/osm.py`](file:///c:/Users/lenovo/climora/ingestion/osm.py) did not query `boundary=administrative` or municipal sub-districts. |
| `data/processed/` | `.tif`, `.json`, `.parquet`, `.csv` | Contains satellite rasters (Landsat, Sentinel-2, DEM, WorldPop) and H3 feature matrices. No administrative polygon assets. |
| `data/manifests/` | `.json` | [`analytical_unit_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/analytical_unit_contract.json) establishes Tier 2 reporting requirement for 41 PMC wards, but references conceptual relational schema rather than an on-disk geometry file path. |
| `docs/` | `.md` | Architectural documents define the H3 $\leftrightarrow$ Ward relationship conceptually, referencing "41 statutory wards / 76 administrative prabhags", but do not bundle raw geometries. |
| `processing/` | `.py` | [`processing/feature_matrix.py`](file:///c:/Users/lenovo/climora/processing/feature_matrix.py) implements `assign_deterministic_wards()` using `sklearn.cluster.KMeans(n_clusters=41)`. |

**Forensic Audit Verdict:** Authoritative administrative ward polygons do not exist on disk.

---

## 3. Ward Geometry Validation

Because no authoritative ward file exists in the repository, the validation criteria evaluate as follows:

```text
Authoritative File Path:       NOT FOUND
Source / Provenance:           NOT ACQUIRED
Ward Count (N_wards):          0 (Expected: 41)
Coordinate Reference System:   N/A
Geometry Types:                N/A
Duplicate Geometry Count:      N/A
Empty Geometry Count:          N/A
Invalid Geometry Count:        N/A
Validation State:              FAIL (Asset Missing)
```

---

## 4. Previous Clustering Implementation Audit

### Implementation Inspection:
In [`processing/feature_matrix.py`](file:///c:/Users/lenovo/climora/processing/feature_matrix.py#L57-L75):

```python
def assign_deterministic_wards(
    coords: np.ndarray,
    n_wards: int = 41,
    random_state: int = 42,
) -> List[str]:
    """Assign deterministic PMC ward IDs (PMC_WARD_01 to PMC_WARD_41) to cells.

    Uses spatial centroid clustering with a fixed random seed, sorted geographically
    (latitude descending, longitude ascending) to ensure 100% reproducible assignments.
    """
    km = KMeans(n_clusters=n_wards, random_state=random_state, n_init=10)
    labels = km.fit_predict(coords)
    centers = km.cluster_centers_

    # Sort cluster centers: north to south, then west to east
    sort_order = np.lexsort((centers[:, 1], -centers[:, 0]))
    rank_map = {old: f"PMC_WARD_{new + 1:02d}" for new, old in enumerate(sort_order)}
    return [rank_map[l] for l in labels]
```

### Forensic Defect Analysis:
1. **MAUP Violations:** $k$-means clusters cells based strictly on spatial Euclidean distance between H3 cell centroids $(\text{lat}, \text{lon})$. This forms a regular Voronoi tessellation of roughly equal-radius spatial clusters.
2. **Ignorance of Statutory Boundaries:** Real municipal ward boundaries in Pune follow major roadways (e.g., Karve Road, Mumbai-Bengaluru Highway), river corridors (Mula-Mutha confluence), historical Peth boundaries, and demographic/electoral quota lines. K-means clusters slice arbitrarily through statutory jurisdictions.
3. **Misleading Nomenclature:** Labeling cluster 1 through 41 as `PMC_WARD_01` through `PMC_WARD_41` creates a false perception that the system is reporting against official administrative wards.

---

## 5. H3 ↔ Ward Intersection Methodology

When authoritative PMC ward polygons are ingested, the spatial relationship between the primary analytical mesh (H3 Resolution 9) and administrative wards must be computed using the **Fractional Area Intersection Formulation**:

$$M_{ij} = \frac{A(H_i \cap W_j)}{A(H_i)}$$

where:
- $H_i$: Geometry of H3 Resolution 9 cell $i$.
- $W_j$: Authoritative geometry of PMC administrative ward $j \in \{1, \dots, 41\}$.
- $A(H_i)$: Exact geodesic area of cell $i$ (computed via `h3.cell_area(c, unit='km^2')`).
- $A(H_i \cap W_j)$: Planar intersection area evaluated in conformal projected coordinate system **UTM Zone 43N (`EPSG:32643`)**.

### Primary Reporting Assignment Rule:
$$\text{ward}_i = \arg\max_j M_{ij}$$

The canonical `ward_id` column represents the **primary reporting ward assignment** (the ward containing the plurality/majority of the cell's area). For cells that intersect ward boundaries, the full relational join table (`h3_ward_membership.json`) records the fractional weights $M_{ij}$ to enable exact area-weighted demographic and hazard rollups.

---

## 6. Fractional Membership Statistics

**Status:** `BLOCKED / DEFERRED`  
Empirical calculation of $M_{ij}$ and verification of $\sum_j M_{ij} \approx 1.0$ cannot proceed without authoritative polygon boundaries. Synthetic or clustered approximations are strictly prohibited.

---

## 7. Old vs. New `ward_id` Comparison

**Status:** `BLOCKED / DEFERRED`  
Because authoritative ward polygons are not yet ingested, no geometry-derived `ward_id` can be calculated without violating the core mandate. The existing feature matrix retains its 3,181 rows $\times$ 57 columns, with the explicit qualification that `ward_id` is an ungrounded cluster proxy.

---

## 8. Feature-Matrix Impact

- **Matrix Dimensions:** 3,181 rows $\times$ 57 columns (100% stable).
- **Physical Feature Integrity:** All non-ward features (LST historical baseline, thermal anomalies, NDVI, NDBI, WorldPop population count and density, OSM infrastructure metrics, and normalized feature vectors) remain **100% byte-identical and mathematically valid**.
- **Isolation of Defect:** The defect is strictly isolated to the spatial lineage of the single metadata column `ward_id`. It does not contaminate satellite processing, demographic mass conservation, or physical environmental features.

---

## 9. 57-Column Contract Arithmetic Correction

Section 9 mandated correcting the feature-group reconciliation arithmetic across all documentation and contracts.

### Canonical 8-Group Reconciliation:
```text
Group 1: Spatial Identity                 =  5 columns
Group 2: Temporal Quality                 =  7 columns
Group 3: Historical Thermal Baseline      =  8 columns
Group 4: Thermal Dynamics                 =  4 columns
Group 5: Biophysical Vegetation Dynamics  =  7 columns
Group 6: Built Environment Dynamics       =  7 columns
Group 7: Demographic & Infrastructure     =  9 columns
Group 8: Normalized Feature Vectors       = 10 columns
------------------------------------------------------
TOTAL CANONICAL SCHEMA                    = 57 columns
```

$$\text{Canonical Sum} = 5 + 7 + 8 + 4 + 7 + 7 + 9 + 10 = 57$$

**Correction Performed:** The erroneous 9-term string ($5 + 7 + 8 + 4 + 7 + 7 + 2 + 7 + 10 = 57$), which improperly split Demographic Exposure (2) and Infrastructure (7) from their canonical Group 7 pairing, was permanently corrected in [`docs/science/phase-1c1-forensic-spatial-feature-gate.md`](file:///c:/Users/lenovo/climora/docs/science/phase-1c1-forensic-spatial-feature-gate.md).

---

## 10. Population Conservation Wording Correction

Section 10 mandated standardizing the scientific qualification of WorldPop demographic conservation.

### Ratified Formulation:
> **"Population aggregation agrees with the reference clipped WorldPop total within the established 0.05% numerical tolerance (observed relative difference $0.0033\% \le 0.05\%$, difference of $167.3$ persons out of $5.01\text{M}$ residents)."**

### Language Rule:
Do **NOT** describe the population conservation as "mathematically exact" ($0.0000\%$). It is a dasymetric area-weighted numerical approximation governed by the $0.05\%$ statutory threshold.

---

## 11. Tests

All 62 existing automated unit tests continue to pass with 0 failures:

```text
tests/test_ingestion.py:                                    13 PASSED
tests/test_phase_1a8_processing.py:                         12 PASSED
tests/test_phase_1b_analytical_contracts.py:                 8 PASSED
tests/test_phase_1c_feature_matrix.py:                      14 PASSED
tests/test_scientific_formulation_contracts.py:              5 PASSED
tests/test_temporal_governance.py:                          10 PASSED

TOTAL: 62 PASSED, 0 FAILED (100% pass rate)
```

---

## 12. Checksums

| Artifact Path | Format | Size (Bytes) | SHA-256 Hash |
| :--- | :---: | :---: | :--- |
| `data/processed/canonical_feature_matrix.parquet` | Parquet | 643,957 | `76f344b147b349f3887259f64c97923414c74fd9a97ec679844fb8d9109f7c01` |
| `data/processed/canonical_feature_matrix.csv` | CSV | 1,397,514 | `c6a8c7b3b167754e629b8d62a7ba20dedda1a809fb15d5f5353356146f5247aa` |
| `data/manifests/canonical_feature_matrix_contract.json` | JSON | 32,860 | `c6037a48f865966064f5f36b3c187fc6d8e234b34ed04f35f53690d3ca1ee6d9` |
| `docs/science/phase-1c1-forensic-spatial-feature-gate.md` | Markdown | 28,292 | `818415082cb3d760079cccbf64674f6f822221bdad9227d42946b5afb3fcdb09` |

---

## 13. Final Gate Decision & Remediation Mandate

### Gate Verdict:
> **STATUS: BLOCKED — AUTHORITATIVE PMC WARD GEOMETRY NOT LOCATED**

### Concrete Technical Remediation Roadmap:
To achieve `PASS` on Phase 1C.1a, the following sequential steps must be executed:
1. **Acquire Statutory PMC Ward Polygons:**
   - Ingest official PMC Prabhag/Ward GeoJSON boundary file (`data/raw/boundaries/pune_wards_41.geojson`) sourced from the PMC Geographic Information System (GIS) portal or Maharashtra State Election Commission delimitation maps.
2. **Execute Geometric Intersection:**
   - Overlay the 3,181 H3 Resolution 9 polygons against the 41 statutory ward polygons in `EPSG:32643`.
   - Calculate intersection fractions $M_{ij} = \frac{A(H_i \cap W_j)}{A(H_i)}$.
3. **Materialize Relational Membership Table:**
   - Write `data/processed/spatial/h3_ward_membership.parquet` recording `h3_cell_id`, `ward_id`, and `intersection_fraction`.
4. **Assign Primary `ward_id`:**
   - Recompute $\text{ward}_i = \arg\max_j M_{ij}$ for each H3 cell.
   - Update `ward_id` in `canonical_feature_matrix.parquet` and `.csv`.
5. **Re-run Automated Test Suite & Unblock:**
   - Verify all tests pass, update contracts and checksums, and issue `PHASE 1C.1a — PASSED`.

Until statutory boundaries are ingested, the downstream risk engine (Phase 1D) must operate strictly on the primary physical mesh (**H3 Resolution 9**) and must not rely on `ward_id` for statutory civic allocation.
