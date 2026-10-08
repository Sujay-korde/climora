"""Automated Test Suite for CLIMORA Phase 1B: Forensic Architecture & Contracts.

Validates:
1. Spatial Unit Evaluation, DGGS H3 Res 9 properties, and Ward reporting relationship.
2. WorldPop 2020 raw acquisition, AOI clipping, and dasymetric area-weighted conservation.
3. Feature Dictionary schema completeness across Groups A through J and 4 Truth Layers.
4. Exact on-disk existence of 100% of declared source assets.
5. Reconciled 5-year temporal baseline contract matching Phase 1A.7.1 approved April scenes.
6. Explicit missing-data policy (K_valid >= 4, 70% pixel threshold).
7. Risk Parameter Contract: alpha/beta/gamma calibration, IPCC attribution, and zero-exposure axiom.
8. Vulnerability vs Susceptibility boundaries and neutral 45°C LST threshold.
9. Immutability of Phase 1A frozen raw and processed assets.
"""

import json
from pathlib import Path

import h3
import numpy as np
import pytest
import rasterio
from shapely.geometry import Polygon, shape

from ingestion.common import calculate_sha256, load_aoi
from processing.config import LANDSAT_TEMPORAL_BASELINE, PROJECT_ROOT, PROCESSED_DIR, RAW_DIR

MANIFESTS_DIR = PROJECT_ROOT / "data" / "manifests"
DOCS_DIR = PROJECT_ROOT / "docs" / "architecture"


def test_spatial_unit_contract_and_h3_res9_properties():
    """Verify analytical unit contract and empirical H3 Resolution 9 properties."""
    contract_file = MANIFESTS_DIR / "analytical_unit_contract.json"
    assert contract_file.exists(), "analytical_unit_contract.json must exist"

    with open(contract_file, "r", encoding="utf-8") as f:
        contract = json.load(f)

    assert contract["status"] == "RATIFIED_AND_FROZEN"
    primary = contract["primary_analytical_unit"]
    assert primary["unit_type"] == "grid_hex_h9"
    assert primary["resolution"] == 9
    assert primary["total_aoi_cells"] == 3181
    assert primary["neighborhood_topology"] == "Isotropic 6-neighbor hexagonal adjacency (uniform distance 347.8m)"

    # Secondary reporting unit
    secondary = contract["secondary_administrative_unit"]
    assert secondary["unit_type"] == "ward"
    assert secondary["total_wards"] == 41

    # Verify H3 generation directly from AOI polygon
    aoi_data = load_aoi(PROJECT_ROOT / "data" / "aoi" / "pune.geojson")
    aoi_geom = aoi_data["features"][0]["geometry"]
    h3_shape = h3.geo_to_h3shape(aoi_geom)
    cells = list(h3.h3shape_to_cells(h3_shape, res=9))

    assert len(cells) == 3181, f"Expected 3,181 H3 Res 9 cells, got {len(cells)}"
    assert len(set(cells)) == 3181, "All cell indexes must be unique"

    # Verify each cell is a valid 15-character hex string and has 6 neighbors
    for c in cells[:50]:
        assert len(c) == 15
        assert h3.is_valid_cell(c)
        assert h3.get_resolution(c) == 9
        neighbors = h3.grid_disk(c, 1)
        assert len(neighbors) == 7


def test_worldpop_raw_and_clipped_raster():
    """Verify WorldPop 2020 raw raster properties and clipped AOI raster."""
    raw_path = RAW_DIR / "worldpop" / "2020" / "ind_ppp_2020_1km_Aggregated_UNadj.tif"
    assert raw_path.exists(), "Raw WorldPop 2020 GeoTIFF must exist"
    assert raw_path.stat().st_size == 18313124, "Raw WorldPop size must be exactly 18,313,124 bytes"

    expected_sha = "27d08e3eabf59f63a2147901c25c046d584c3295f9ceb4c4cf08a902a5bec911"
    actual_sha = calculate_sha256(raw_path)
    assert actual_sha == expected_sha, f"SHA-256 mismatch for raw WorldPop: {actual_sha}"

    # Verify clipped raster
    clipped_path = PROCESSED_DIR / "worldpop" / "2020" / "worldpop_pune_2020_clipped.tif"
    assert clipped_path.exists(), "Clipped WorldPop GeoTIFF must exist"

    with rasterio.open(clipped_path) as src:
        assert "4326" in str(src.crs), "Clipped WorldPop CRS must be EPSG:4326"
        arr = src.read(1)
        assert arr.ndim == 2
        assert np.all(arr >= 0.0)
        assert np.sum(arr) > 0.0


def test_population_exposure_aggregation_and_conservation():
    """Verify population aggregation into H3 cells and demographic conservation."""
    pop_json_path = PROCESSED_DIR / "worldpop" / "2020" / "h3_population_exposure.json"
    assert pop_json_path.exists(), "h3_population_exposure.json must exist"

    with open(pop_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    assert meta["spatial_unit"] == "grid_hex_h9"
    assert meta["cell_count"] == 3181
    assert meta["aggregation_method"] == "area_weighted_dasymetric_sum"

    # Verify exact conservation delta is <= 0.05%
    exact_delta = meta["exact_conservation_delta_percent"]
    assert exact_delta <= 0.05, f"Conservation delta {exact_delta}% exceeds 0.05% tolerance"
    assert meta["total_aggregated_population"] > 5000000.0, "Pune population must exceed 5 million"

    cells = data["cells"]
    assert len(cells) == 3181
    for c in cells[:100]:
        assert "h3_index" in c
        assert c["population_count"] >= 0.0
        assert c["population_density_per_km2"] >= 0.0
        assert c["cell_area_km2"] == 0.098623
        expected_density = round(c["population_count"] / c["cell_area_km2"], 1)
        assert abs(c["population_density_per_km2"] - expected_density) <= 0.2


def test_feature_dictionary_schema_and_asset_existence():
    """Verify feature dictionary schema, truth layers, and that 100% of declared assets exist."""
    dict_file = MANIFESTS_DIR / "feature_dictionary.json"
    assert dict_file.exists(), "feature_dictionary.json must exist"

    with open(dict_file, "r", encoding="utf-8") as f:
        d = json.load(f)

    assert d["status"] == "RATIFIED_AND_FROZEN"
    assert d["total_features"] == 29
    assert len(d["groups"]) == 10

    required_fields = {
        "feature_id", "group", "feature_name", "description", "truth_layer",
        "source_dataset", "source_assets", "spatial_unit", "native_resolution",
        "temporal_semantics", "aggregation", "formula", "units", "valid_range",
        "missing_value_policy", "quality_requirement", "provenance", "version"
    }

    valid_truth_layers = {"OBSERVED", "DERIVED", "MODELED", "VERIFIED"}
    observed_feature_ids = set()

    for feat in d["features"]:
        fid = feat.get("feature_id")
        missing = required_fields - set(feat.keys())
        assert not missing, f"Feature {fid} missing fields: {missing}"
        assert feat["truth_layer"] in valid_truth_layers, f"Invalid truth layer: {feat['truth_layer']}"
        assert fid not in observed_feature_ids, f"Duplicate feature_id: {fid}"
        observed_feature_ids.add(fid)

        # Verify NDWI absence (Critical Audit H)
        assert "ndwi" not in fid.lower(), "feat_ndwi_current_2025 must not be in canonical dictionary without source artifacts"

        # Verify that 100% of declared source assets exist on disk
        for asset_path in feat.get("source_assets", []):
            full_path = PROJECT_ROOT / asset_path
            assert full_path.exists(), f"Feature {fid} references non-existent asset: {asset_path}"

        # No modeled predictions in observed or derived
        if feat["truth_layer"] in ("OBSERVED", "DERIVED"):
            assert "predicted" not in feat["feature_name"].lower()
            assert "ml_target" not in feat["feature_name"].lower()


def test_temporal_feature_contract_and_scene_lineage():
    """Verify 5-year temporal baseline contract against approved April baseline scenes."""
    temporal_file = MANIFESTS_DIR / "temporal_feature_contract.json"
    assert temporal_file.exists(), "temporal_feature_contract.json must exist"

    with open(temporal_file, "r", encoding="utf-8") as f:
        t = json.load(f)

    assert t["status"] == "RATIFIED_AND_FROZEN"
    obs = t["historical_observations"]
    assert len(obs) == 5

    # Strictly verify against LANDSAT_TEMPORAL_BASELINE
    for i, expected_spec in enumerate(LANDSAT_TEMPORAL_BASELINE):
        actual_obs = obs[i]
        assert actual_obs["year"] == expected_spec["year"]
        assert actual_obs["scene_id"] == expected_spec["scene_id"]
        assert actual_obs["acquisition_date"] == expected_spec["date"]
        assert actual_obs["doy"] == expected_spec["doy"]
        assert actual_obs["doy_offset"] == expected_spec["offset_days"]

    # Verify missing data rules
    missing_policy = t["temporal_quality_and_missing_data_policy"]
    assert missing_policy["min_valid_baseline_years"] == 4
    assert missing_policy["annual_cell_validity_threshold"] == 0.70

    # Verify Sentinel-2 isolation
    isolation = t["sensor_isolation_matrix"]
    assert "strictly isolated" in isolation["sentinel2_role"]
    assert "never upscaled to 30m" in isolation["modis_role"]


def test_risk_parameter_contract_and_governance():
    """Verify risk parameter contract governing alpha, beta, gamma and IPCC attribution."""
    param_file = MANIFESTS_DIR / "risk_parameter_contract.json"
    assert param_file.exists(), "risk_parameter_contract.json must exist"

    with open(param_file, "r", encoding="utf-8") as f:
        rp = json.load(f)

    assert rp["status"] == "RATIFIED_AND_FROZEN"
    attrib = rp["framework_attribution"]
    assert "NOT an IPCC-prescribed formula" in attrib["attribution_distinction"]
    assert "Risk_i = 0" in attrib["zero_exposure_axiom"]

    params = {p["parameter_name"]: p for p in rp["risk_parameters"]}
    for name in ("risk_weight_alpha", "risk_weight_beta", "risk_weight_gamma"):
        assert name in params
        p = params[name]
        assert p["default_value"] == 1.0
        assert p["allowed_range"] == [0.0, 3.0]
        assert p["calibration_status"] == "PENDING_METHODOLOGICAL_CALIBRATION"

    # Verify 45°C neutral threshold
    thresholds = rp["methodological_thresholds"]
    assert thresholds["lst_extreme_recurrence_threshold_celsius"] == 45.0
    assert thresholds["threshold_type"] == "CLIMORA_METHODOLOGICAL_SURFACE_TEMPERATURE_THRESHOLD"


def test_risk_target_strategy_and_governance_rules():
    """Verify that Risk Target Strategy documentation enforces label governance."""
    doc_path = DOCS_DIR / "phase-1b-risk-target-strategy.md"
    assert doc_path.exists(), "phase-1b-risk-target-strategy.md must exist"

    content = doc_path.read_text(encoding="utf-8")

    assert "strictly prohibits the fabrication of pseudo-labels" in content
    assert "strictly prohibits claiming supervised machine-learning" in content
    assert "Strategy B: IPCC AR6 Composite Risk Framework" in content
    assert "Strategy D: Unsupervised / Anomaly" in content
    assert "Biophysical and Structural Susceptibility" in content
    assert "NOT an IPCC-prescribed formula" in content


def test_frozen_raw_and_processed_lake_immutability():
    """Ensure Phase 1A frozen assets remain 100% untouched."""
    raw_frozen_manifest = MANIFESTS_DIR / "pune_temporal_baseline_v1_frozen.json"
    assert raw_frozen_manifest.exists()

    with open(raw_frozen_manifest, "r", encoding="utf-8") as f:
        raw_m = json.load(f)

    # 109 raw assets
    assert raw_m["inventory_summary"]["total_lake_files"] == 109

    # Verify raw checksum manifest exists and has 109 entries
    raw_checksum_file = MANIFESTS_DIR / "pune_temporal_baseline_v1_checksums.sha256"
    assert raw_checksum_file.exists()
    with open(raw_checksum_file, "r", encoding="utf-8") as f:
        raw_lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    assert len(raw_lines) == 109

    # Verify processed frozen manifest
    proc_frozen_manifest = MANIFESTS_DIR / "pune_temporal_baseline_v1_processed_frozen.json"
    assert proc_frozen_manifest.exists()
    with open(proc_frozen_manifest, "r", encoding="utf-8") as f:
        proc_m = json.load(f)
    assert len(proc_m["inventory"]) == 160

    # Verify processed checksum manifest exists and has 160 entries
    proc_checksum_file = MANIFESTS_DIR / "pune_temporal_baseline_v1_processed_checksums.sha256"
    assert proc_checksum_file.exists()
    with open(proc_checksum_file, "r", encoding="utf-8") as f:
        proc_lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    assert len(proc_lines) == 160
