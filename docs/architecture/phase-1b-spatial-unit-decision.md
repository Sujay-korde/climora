# CLIMORA — Phase 1B: Spatial Unit Evaluation & Canonical Analytical Architecture Decision

**Document Version:** 1.0.0  
**Phase:** Phase 1B (Analytical Architecture, Spatial Unit Evaluation & Feature Contract Decision Gate)  
**Status:** **RATIFIED & FROZEN**  
**Applies To:** Spatial Discretization, Analytical Grid Mesh, Administrative Wards, Multi-Sensor Zonal Aggregation, Neighborhood Modeling, Intervention Allocation  
**Machine-Readable Contract:** [`data/manifests/analytical_unit_contract.json`](file:///c:/Users/lenovo/climora/data/manifests/analytical_unit_contract.json)  

---

## 1. Executive Summary & Canonical Decision

Following empirical benchmarking against the frozen Pune pre-monsoon dataset (312.11 km² statutory AOI, 346,809 valid Landsat pixels), CLIMORA establishes a **Dual-Tier Spatial Architecture**:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLIMORA DUAL-TIER SPATIAL ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 1: PRIMARY ANALYTICAL MODELING MESH                                    │
│ • Geometry: Uber H3 Discrete Global Grid System — Resolution 9 (grid_hex_h9)│
│ • Spatial Scale: ~0.0986 km² (9.86 hectares, ~201m edge, ~348m spacing)    │
│ • Total Pune Cells: 3,181 regular hexagons                                  │
│ • Purpose: Zonal feature aggregation, microclimatic hotspot detection,      │
│   heat diffusion modeling, intervention parcel targeting, optimization.    │
├─────────────────────────────────────────────────────────────────────────────┤
│ TIER 2: STATUTORY ADMINISTRATIVE REPORTING SCOPE                            │
│ • Geometry: Pune Municipal Corporation (PMC) Administrative Wards (ward)   │
│ • Spatial Scale: 41 Administrative Wards (or 76 Prabhag Electoral Divisions)│
│ • Purpose: Civic budgeting, ward councillor reporting, political signoff,   │
│   bankable project tender packaging, municipal accountability.              │
│ • Relationship: Every H3 cell records its primary parent ward and           │
│   area-intersection fractions. All H3 risk and impact metrics roll up       │
│   dynamically to wards via area-weighted spatial joins.                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ UNDERLYING DATA LAKE: UNCOMPROMISED NATIVE RESOLUTION                       │
│ • Native 30m Landsat (706 × 954), 10m/20m Sentinel-2, 1km MODIS, and DEM   │
│   remain immutable raster rasters in data/processed/ and data/derived/.     │
│ • The analytical unit extracts features from native data via zonal queries; │
│   it NEVER replaces or destructively resamples the raw satellite lake.      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Empirical Candidate Evaluation

The evaluation was conducted directly on the statutory Pune Municipal Corporation boundary ([`data/aoi/pune.geojson`](file:///c:/Users/lenovo/climora/data/aoi/pune.geojson)), measuring exact spatial properties across the four candidate architectures:

### 2.1 Candidate Summary Matrix

| Metric / Property | Candidate 1: Planar Metric Grid (250m) | Candidate 2: Uber H3 DGGS (Resolution 9) | Candidate 3: Uber H3 DGGS (Resolution 8) | Candidate 4: PMC Administrative Wards |
| :--- | :---: | :---: | :---: | :---: |
| **Geometry** | Regular Cartesian Square | Regular Geodesic Hexagon | Regular Geodesic Hexagon | Irregular Vector Polygon |
| **Native Coordinate System** | `EPSG:32643` (UTM Zone 43N) | `EPSG:4326` (DGGS Indexed) | `EPSG:4326` (DGGS Indexed) | `EPSG:4326` (Statutory) |
| **Total Units over Pune AOI** | 5,284 intersecting (4,694 full) | **3,181 hexagons** | 450 hexagons | 41 statutory wards |
| **Nominal Unit Area** | $0.0625\text{ km}^2$ ($62,500\text{ m}^2$) | $0.0986\text{ km}^2$ ($98,623\text{ m}^2$) | $0.6904\text{ km}^2$ ($690,389\text{ m}^2$) | Mean $\sim 7.61\text{ km}^2$ (Var: $0.8$ to $>35\text{ km}^2$) |
| **Characteristic Dimension** | $250.0\text{ m} \times 250.0\text{ m}$ | Edge: $200.8\text{ m}$, Spacing: $347.8\text{ m}$ | Edge: $531.4\text{ m}$, Spacing: $920.4\text{ m}$ | Irregular diameter ($1\text{ km}$ to $8\text{ km}$) |
| **Landsat 30m Pixels / Unit** | $\sim 69.4$ pixels | $\sim 109.6$ pixels | $\sim 767.1$ pixels | $\sim 8,458$ pixels (extreme variance) |
| **Sentinel-2 10m Pixels / Unit** | $625$ pixels | $\sim 986.2$ pixels | $\sim 6,904$ pixels | $\sim 76,100$ pixels |
| **Neighborhood Topology** | Anisotropic 8-neighbor (Moore) | **Isotropic 6-neighbor (Identical)** | Isotropic 6-neighbor (Identical) | Irregular (3 to 9 neighbors) |
| **Boundary Perimeter-to-Area** | $0.0160\text{ m}^{-1}$ ($1,000\text{ m} / 62,500\text{ m}^2$) | **$0.0122\text{ m}^{-1}$ ($\sim 24\%$ lower than square)** | $0.0046\text{ m}^{-1}$ | Highly variable, convoluted |
| **Boundary Truncated Units** | 590 cells ($11.2\%$ of cells) | 234 boundary-intersecting cells | 46 boundary cells | 0 (boundary defines AOI) |
| **Primary Indexing Type** | 2D $(i, j)$ integer / string code | **64-bit unsigned integer (`uint64`)** | 64-bit unsigned integer (`uint64`) | String Ward Code (e.g. `'WARD_01'`) |

---

## 3. Technical Evaluation Across Required Criteria

### 3.1 Spatial Compatibility with Multi-Sensor Lake
- **Candidate 1 (250m Grid):** High compatibility with planar rasters. $250\text{ m} / 30\text{ m} \approx 8.33$ Landsat pixels; $250\text{ m} / 10\text{ m} = 25$ integer Sentinel-2 pixels. However, fractional Landsat overlap across cell borders creates sub-pixel sampling artifacts.
- **Candidate 2 (H3 Res 9):** Exceptional zonal stability. At $\sim 109.6$ Landsat 30m pixels per cell, zonal aggregation significantly dampens uncorrelated high-frequency sensor noise and georeferencing jitter. Note that positive spatial autocorrelation among adjacent pixels prevents treating $\sigma / \sqrt{N}$ as an independent statistical error estimate; the effective degrees of freedom are smaller than the nominal pixel count, but the multi-pixel sample provides robust micro-neighborhood central tendency estimates.
- **Candidate 3 (H3 Res 8):** Coarse aggregation ($\sim 767$ Landsat pixels) over-smooths localized urban microclimates. An acute 100m informal settlement thermal hotspot is diluted across 69 hectares.
- **Candidate 4 (Wards):** Aggregates thousands of pixels per ward, destroying spatial microclimate heterogeneity. Kasba Peth (dense heritage core) and Katraj (peri-urban hills) are treated as single averages.

### 3.2 Geographic Properties & Spatial Distortion
- **Candidate 1 (250m Grid):** Restricted to planar Cartesian projections (`EPSG:32643`). If CLIMORA expands to multi-city or national scales, regional UTM zone boundary transitions introduce angular shearing and area distortion.
- **Candidate 2 (H3 Res 9):** Built on an icosahedron Discrete Global Grid System (DGGS) defined in WGS84 (`EPSG:4326`). Area variation across Pune's $0.2^\circ$ latitudinal span is less than $0.05\%$. Hexagonal geometry minimizes the distance between the cell center and any point within its boundary.
- **Candidate 4 (Wards):** Suffers from extreme area variance ($> 40:1$ ratio between largest and smallest wards), violating spatial stationarity assumptions in ML and statistical modeling.

### 3.3 Analytical Properties: Neighborhood & Adjacency Support
- **Candidate 1 (250m Grid):** Moore neighborhood has 8 neighbors with two distinct distance classes: 4 orthogonal neighbors at $250\text{ m}$ and 4 diagonal neighbors at $353.55\text{ m}$ ($\sqrt{2} \times 250\text{ m}$, $41.4\%$ further). Simulating thermal diffusion or urban heat island spillover introduces an artificial Cartesian axis bias.
- **Candidate 2 (H3 Res 9):** **Perfect mathematical isotropy.** Every non-boundary hexagon shares an identical edge length ($200.8\text{ m}$) and identical centroid-to-centroid distance ($347.8\text{ m}$) with all 6 neighbors. Spatial autoregressive modeling ($W$ matrix), kernel smoothing, and spatial autocorrelation (Moran's $I$) are uniform in all directions.
- **Candidate 4 (Wards):** Irregular adjacency graph with variable neighbor counts (3 to 9), rendering spatial diffusion algorithms mathematically ill-posed without arbitrary weighting schemes.

### 3.4 Exposure Integration (Population & Infrastructure)
- **Candidate 1 (250m Grid):** Easily integrates with gridded population through raster resample/sum, but square boundaries slice arbitrarily through road networks and building footprints.
- **Candidate 2 (H3 Res 9):** Ideal matching scale for WorldPop ($~1\text{ km}$ downscaling or $100\text{ m}$ aggregation: $\sim 9.8$ ha corresponds to approximately 10 WorldPop 100m cells). Direct compatibility with Kontur 400m H3 population layers. OSM hospital and clinic catchment zones map naturally to hexagonal $k$-ring buffers (`h3.grid_disk`).
- **Candidate 4 (Wards):** Coincides with census enumeration districts, but masks within-ward demographic segregation (slum clusters vs. affluent gated societies).

### 3.5 Intervention Integration & Spatial Optimization
- **Candidate 1 (250m Grid):** A 6.25 ha square cell is reasonable for macro-budgeting, but intervention sites (cool roofs on municipal schools, bus depot painting, street tree corridors) follow linear rights-of-way and parcel parcels, not squares.
- **Candidate 2 (H3 Res 9):** At 9.86 ha, an H3 cell represents a cohesive urban micro-neighborhood. Mixed-integer linear programming (MILP) solvers assign intervention parcels (e.g., $15,000\text{ m}^2$ cool roofs + $400$ street trees) to specific hexagons while cleanly bounding spatial spillover cooling effects into the 6 adjacent cells.
- **Candidate 4 (Wards):** Too coarse for direct intervention siting. An optimization algorithm cannot simply allocate "5,000 cool roofs to Ward 12" without specifying where in Ward 12 they should be painted.

### 3.6 Engineering, Indexing & Queryability
- **Candidate 1 (250m Grid):** Requires custom $(X, Y)$ string identifiers or composite PostGIS integer indexes. Querying neighbor cells requires spatial intersection queries (`ST_DWithin` / `ST_Touches`).
- **Candidate 2 (H3 Res 9):** **Unmatched engineering performance.** Every cell is natively identified by a 64-bit integer (`uint64` / 15-character hex string, e.g., `'8960145b23fffff'`). Topological queries (`h3.grid_disk`, `h3.cell_to_parent`, `h3.grid_distance`) execute in nanoseconds using pure bitwise arithmetic without invoking heavy PostGIS spatial geometry operations.
- **Candidate 4 (Wards):** Low volume (41 records), but spatial joins require heavy vector polygon overlay computations (`ST_Intersection`).

### 3.7 Visualization & Public Interaction
- **Candidate 1 (250m Grid):** Standard grid view; looks like a raster pixel map.
- **Candidate 2 (H3 Res 9):** Modern, visually compelling hexagonal choropleth heatmaps. Smooth, aesthetic color blending in Mapbox GL / Deck.gl / Leaflet. Hexagonal cells feel analytical, scientific, and modern.
- **Candidate 4 (Wards):** Essential for civic presentations. Ward councillors and municipal commissioners think in terms of administrative wards, not hexagon IDs.

---

## 4. Evidence-Based Decision Rationale

| Candidate | Strengths | Limitations | Observed Compatibility | CLIMORA-Specific Consequence | Decision Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Candidate 1: 250m Planar Grid** | Fixed area ($0.0625\text{ km}^2$); direct 2D matrix slicing; simple tensor formatting. | Anisotropic 8-neighbor Moore neighborhood ($\sqrt{2}$ diagonal bias); 590 boundary-truncated cells; restricted to local UTM. | Excellent with 10m/20m/30m rasters; poor for radial heat dispersion. | Good secondary raster modeling mesh, but directional bias compromises heat diffusion and intervention contagion models. | **REJECTED AS PRIMARY UNIT** (Maintained as raster derivation capability) |
| **Candidate 2: Uber H3 Res 9** | **Isotropic 6-neighbor connectivity; 64-bit integer indexing; ~109 Landsat pixels per cell; minimal perimeter-to-area ratio; native DGGS WGS84.** | Non-congruent hierarchical nesting (aperture 7); requires vector zonal extraction. | **100% statutory AOI coverage (3,181 cells); stable zonal statistics; matches micro-neighborhood scale.** | **Optimal balance of microclimatic precision, isotropic spatial diffusion, and ultra-fast database operations.** | **SELECTED AS PRIMARY ANALYTICAL UNIT (`grid_hex_h9`)** |
| **Candidate 3: Uber H3 Res 8** | Compact cell count (450 cells); fast high-level visual summaries. | Coarse resolution ($\sim 69\text{ ha}$, $\sim 920\text{ m}$ spacing); severe spatial dilution of acute hotspots. | High stability, but averages away urban slum heat microclimates. | Unacceptable spatial aggregation error for cool roof and urban greening targeting. | **REJECTED FOR PRIMARY MODELING** (Reserved for regional zoom-out views) |
| **Candidate 4: PMC Wards** | Direct statutory alignment with municipal budgeting, tenders, and political leadership. | Extreme area variance ($> 40:1$); severe Modifiable Areal Unit Problem (MAUP); non-stationary statistical distributions. | Coarse polygon overlay; masks internal demographic and environmental disparity. | Essential for reporting and tender execution, but scientifically invalid as a primary modeling mesh. | **SELECTED AS SECONDARY ADMINISTRATIVE REPORTING UNIT (`ward`)** |

---

## 5. Formal Specification of Canonical Analytical Unit

```json
{
  "unit_id_type": "VARCHAR(15) / uint64",
  "unit_id_example": "8960145b23fffff",
  "unit_type": "grid_hex_h9",
  "system": "Uber H3 Discrete Global Grid System",
  "resolution": 9,
  "nominal_area_m2": 98623.1,
  "nominal_area_km2": 0.09862,
  "nominal_edge_m": 200.79,
  "centroid_spacing_m": 347.77,
  "coordinate_reference_system": "EPSG:4326 (WGS 84)",
  "total_units_pune_aoi": 3181,
  "boundary_behavior": {
    "core_units": "Fully contained within statutory PMC boundary (area_intersection_fraction = 1.0)",
    "boundary_units": "Intersecting PMC boundary with area_intersection_fraction recorded in spatial_unit_ward_membership",
    "clipping_policy": "Full hexagonal geometry is preserved for DGGS topological indexing; statutory polygon intersection fraction is retained as analytical weight."
  },
  "neighborhood_topology": {
    "neighbor_count": 6,
    "relationship_type": "Isotropic edge-sharing adjacency",
    "lookup_method": "Pure bitwise h3.grid_disk(unit_id, k=1)"
  },
  "parent_administrative_relationship": {
    "parent_entity": "administrative_ward",
    "mapping": "spatial_unit_ward_membership join table recording primary_parent_ward_id and intersection_fraction"
  }
}
```

---

## 6. Preservation of Native Data

In strict compliance with project data governance:
- **No Native Data Destruction:** Landsat Collection 2 Level-2 ($30.0\text{ m}$), Sentinel-2 Level-2A ($10.0\text{ m}$ and $20.0\text{ m}$), MODIS MOD11A2 ($926.625\text{ m}$), and Copernicus DEM ($30\text{ m}$) remain completely untouched in their native resolutions.
- **Aggregation Pipeline:** Analytical features are extracted via zonal queries from native rasters into H3 Res 9 cells. The native rasters remain the permanent, immutable ground truth for all spatial audits.
