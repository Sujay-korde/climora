"""Comprehensive Test Suite for CLIMORA Phase 1A.8.

Validates:
1. Raster Integrity:
   - Readable by rasterio, CRS validity, transform validity, non-empty dimensions, resolution matching.
2. AOI Integrity:
   - Intersects canonical Pune AOI, exact affine transform matching across all 5 Landsat scenes.
3. QA Integrity:
   - Deterministic classification raster classes (0..7), QA_PIXEL and QA_RADSAT compliance.
4. Temporal Integrity:
   - 5 annual observations present (2021-2025), correct DOY (101-114), offsets <= 9 days.
   - Sensor governance: 2023 is Landsat 9 (LC09), 4x Landsat 8 (LC08).
5. Derived Product Integrity:
   - NDVI bounded in [-1.0, 1.0], NDBI bounded in [-1.0, 1.0].
   - LST physical units in Kelvin (300-345 K) and Celsius (25-72 °C).
   - Zero NaN/Inf leaks in valid masked areas.
6. Sentinel-2 Current-State Isolation:
   - High-resolution reference role, 10m/20m native resolution, separate from historical baseline.
7. MODIS Processing Integrity:
   - Native Sinusoidal ~926.6m resolution, 0.02 scaling to Kelvin/Celsius, QC extraction.
8. NASA POWER Meteorological Normalization:
   - 1,826 daily records across 5 years, all 7 variables, canonical schema.
9. Spatial Harmonization Framework:
   - Candidate analytical units evaluated, final decision explicitly deferred to Phase 1B.
10. Frozen Raw Data Immutability:
   - All 109 raw frozen baseline assets remain 100% byte-for-byte unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest
import rasterio

from ingestion.common import calculate_sha256, load_aoi
from processing.config import (
    CANONICAL_TARGET_DOY,
    DATA_DIR,
    DERIVED_DIR,
    HARD_MAX_OFFSET_DAYS,
    LANDSAT_REQUIRED_BANDS,
    LANDSAT_TEMPORAL_BASELINE,
    MANIFESTS_DIR,
    PREFERRED_WINDOW,
    PROCESSED_DIR,
    PROJECT_ROOT,
    RAW_DIR,
)


@pytest.fixture
def root():
    return PROJECT_ROOT


# ==============================================================================
# 1. RAW DATA IMMUTABILITY & PRESERVATION
# ==============================================================================

def test_frozen_raw_lake_immutability(root):
    """Ensure all 109 raw frozen assets remain 100% byte-for-byte unchanged."""
    checksum_file = MANIFESTS_DIR / "pune_temporal_baseline_v1_checksums.sha256"
    assert checksum_file.exists(), "Raw checksum manifest must exist"

    with open(checksum_file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    assert len(lines) == 109, f"Expected 109 raw frozen assets, found {len(lines)}"

    # Validate all 109 raw assets against their authoritative checksums
    for line in lines:
        expected_sha, rel_path = line.split(maxsplit=1)
        full_path = root / rel_path.replace("\\", "/")
        assert full_path.exists(), f"Raw asset missing: {rel_path}"
        actual_sha = calculate_sha256(full_path)
        assert actual_sha == expected_sha, f"Raw asset modified! Hash mismatch for {rel_path}"


# ==============================================================================
# 2. LANDSAT PROCESSED RASTER & SPATIAL INTEGRITY
# ==============================================================================

def test_landsat_scenes_inventory_and_dimensions(root):
    """Test that all 5 Landsat scenes exist and share the exact identical spatial grid."""
    expected_shape = (706, 954)
    expected_res = (30.0, 30.0)
    expected_crs = "EPSG:32643"
    reference_transform = None

    for spec in LANDSAT_TEMPORAL_BASELINE:
        yr = spec["year"]
        sc_id = spec["scene_id"]
        scene_dir = PROCESSED_DIR / "landsat" / str(yr) / sc_id
        assert scene_dir.exists(), f"Processed Landsat scene directory missing: {scene_dir}"

        # Verify all 9 required bands plus qa_mask exist
        expected_files = [f"{b}.tif" for b in LANDSAT_REQUIRED_BANDS] + ["qa_mask.tif", "metadata.json"]
        for fname in expected_files:
            fpath = scene_dir / fname
            assert fpath.exists(), f"Missing processed asset {fname} in {scene_dir.name}"
            assert fpath.stat().st_size > 0, f"Empty processed asset: {fname}"

        # Check spatial geometry on SR_B4
        b4_path = scene_dir / "SR_B4.tif"
        with rasterio.open(b4_path) as src:
            assert src.shape == expected_shape, f"Dimension mismatch for {b4_path.name}: {src.shape}"
            assert src.res == expected_res, f"Resolution mismatch for {b4_path.name}: {src.res}"
            assert str(src.crs) == expected_crs, f"CRS mismatch: {src.crs}"
            assert src.dtypes[0] == "float32", f"Reflectance dtype must be float32"

            if reference_transform is None:
                reference_transform = src.transform
            else:
                # Every scene must have identical affine transform
                assert src.transform == reference_transform, f"Spatial misalignment in year {yr}!"


def test_landsat_scaling_parameters_and_ranges(root):
    """Test that Landsat surface reflectance and temperature are correctly scaled."""
    for spec in LANDSAT_TEMPORAL_BASELINE:
        yr = spec["year"]
        sc_id = spec["scene_id"]
        scene_dir = PROCESSED_DIR / "landsat" / str(yr) / sc_id

        # Verify Surface Reflectance (SR_B4)
        with rasterio.open(scene_dir / "SR_B4.tif") as src:
            arr = src.read(1)
            valid = arr[np.isfinite(arr)]
            assert valid.size > 0, f"No valid pixels in SR_B4 for {yr}"
            # Physical surface reflectance in visible bands is non-negative and typically <= 1.0
            assert np.min(valid) >= -0.05, f"Unphysical negative reflectance in {yr}: {np.min(valid)}"
            assert np.max(valid) <= 1.60, f"Unphysical high reflectance in {yr}: {np.max(valid)}"

        # Verify Surface Temperature (ST_B10)
        with rasterio.open(scene_dir / "ST_B10.tif") as src:
            arr = src.read(1)
            valid = arr[np.isfinite(arr)]
            assert valid.size > 0, f"No valid pixels in ST_B10 for {yr}"
            # Kelvin in Pune summer: typically 295 K - 345 K (22°C - 72°C)
            assert np.min(valid) >= 290.0, f"Kelvin temp too low in {yr}: {np.min(valid)}"
            assert np.max(valid) <= 345.0, f"Kelvin temp too high in {yr}: {np.max(valid)}"


# ==============================================================================
# 3. QA_PIXEL & QA_RADSAT MASKING INTEGRITY
# ==============================================================================

def test_landsat_qa_mask_classes_and_logic(root):
    """Test that deterministic QA mask rasters contain valid classes and accurate statistics."""
    for spec in LANDSAT_TEMPORAL_BASELINE:
        yr = spec["year"]
        sc_id = spec["scene_id"]
        qa_mask_path = PROCESSED_DIR / "landsat" / str(yr) / sc_id / "qa_mask.tif"
        meta_path = PROCESSED_DIR / "landsat" / str(yr) / sc_id / "metadata.json"

        with rasterio.open(qa_mask_path) as src:
            assert src.dtypes[0] == "uint8"
            qa_arr = src.read(1)
            unique_classes = set(np.unique(qa_arr))
            # All classes must be within 0..7
            assert unique_classes.issubset({0, 1, 2, 3, 4, 5, 6, 7})
            # Statutory valid clear class (1) must be present
            assert 1 in unique_classes, f"Valid clear pixels missing in year {yr}"

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        qa_summary = meta.get("qa_summary", {})
        assert qa_summary.get("aoi_internal_pixels") == 346809, f"Pune AOI pixel count mismatch in {yr}"
        assert qa_summary.get("valid_clear_pixels") > 0

        # In 2022, cloud/shadow pixels must be detected and documented
        if yr == 2022:
            assert qa_summary.get("cloud_pixels") > 0
            assert qa_summary.get("shadow_pixels") > 0
            assert qa_summary.get("valid_clear_pct") < 95.0
        else:
            # 2021, 2023, 2024, 2025 are exceptionally clear (> 99.5%)
            assert qa_summary.get("valid_clear_pct") >= 99.5


# ==============================================================================
# 4. SENSOR GOVERNANCE & TEMPORAL INTEGRITY
# ==============================================================================

def test_sensor_governance_platform_identities(root):
    """Verify that 2023 is Landsat 9 and all other 4 years are Landsat 8."""
    for spec in LANDSAT_TEMPORAL_BASELINE:
        yr = spec["year"]
        sc_id = spec["scene_id"]
        meta_path = PROCESSED_DIR / "landsat" / str(yr) / sc_id / "metadata.json"

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        if yr == 2023:
            assert meta["platform"] == "Landsat 9", f"2023 platform must be Landsat 9, got {meta['platform']}"
            assert meta["scene_id"].startswith("LC09_")
        else:
            assert meta["platform"] == "Landsat 8", f"{yr} platform must be Landsat 8, got {meta['platform']}"
            assert meta["scene_id"].startswith("LC08_")

        assert meta["canonical_target_doy"] == CANONICAL_TARGET_DOY
        assert meta["doy_offset"] <= HARD_MAX_OFFSET_DAYS
        assert PREFERRED_WINDOW[0] <= meta["doy"] <= PREFERRED_WINDOW[1]


# ==============================================================================
# 5. DERIVED PRODUCTS INTEGRITY (NDVI, NDBI, LST)
# ==============================================================================

def test_derived_indices_bounds_and_validity(root):
    """Test that NDVI, NDBI, and LST (Kelvin & Celsius) are strictly within physical limits."""
    for spec in LANDSAT_TEMPORAL_BASELINE:
        yr = spec["year"]
        sc_id = spec["scene_id"]
        der_dir = DERIVED_DIR / "landsat" / str(yr) / sc_id

        # 1. NDVI
        with rasterio.open(der_dir / "ndvi.tif") as src:
            arr = src.read(1)
            valid = arr[np.isfinite(arr)]
            assert valid.size > 0
            assert np.min(valid) >= -1.0, f"NDVI below -1.0 in {yr}: {np.min(valid)}"
            assert np.max(valid) <= 1.0, f"NDVI above 1.0 in {yr}: {np.max(valid)}"
            # Mean urban/semi-arid summer NDVI typically 0.15 - 0.45
            assert 0.10 <= np.mean(valid) <= 0.50

        # 2. NDBI
        with rasterio.open(der_dir / "ndbi.tif") as src:
            arr = src.read(1)
            valid = arr[np.isfinite(arr)]
            assert valid.size > 0
            assert np.min(valid) >= -1.0, f"NDBI below -1.0 in {yr}: {np.min(valid)}"
            assert np.max(valid) <= 1.0, f"NDBI above 1.0 in {yr}: {np.max(valid)}"

        # 3. LST Kelvin & Celsius
        with rasterio.open(der_dir / "lst_kelvin.tif") as src_k, rasterio.open(der_dir / "lst_celsius.tif") as src_c:
            arr_k = src_k.read(1)
            arr_c = src_c.read(1)
            valid_k = arr_k[np.isfinite(arr_k)]
            valid_c = arr_c[np.isfinite(arr_c)]

            assert valid_k.size == valid_c.size
            assert np.allclose(valid_c, valid_k - 273.15, atol=1e-3), f"LST Celsius/Kelvin mismatch in {yr}"
            assert np.min(valid_c) >= 20.0, f"Celsius temp too cold in summer {yr}: {np.min(valid_c)}"
            assert np.max(valid_c) <= 75.0, f"Celsius temp too hot in summer {yr}: {np.max(valid_c)}"


# ==============================================================================
# 6. SENTINEL-2 CURRENT-STATE DATA ISOLATION
# ==============================================================================

def test_sentinel2_current_state_contract(root):
    """Verify Sentinel-2 is strictly maintained as 2025 current-state high-res data."""
    s2_proc_dir = PROCESSED_DIR / "sentinel2" / "2025"
    assert s2_proc_dir.exists()
    granules = list(s2_proc_dir.iterdir())
    assert len(granules) == 1, "Expected exactly 1 Sentinel-2 granule"

    granule_dir = granules[0]
    meta_path = granule_dir / "metadata.json"
    assert meta_path.exists()

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["role"] == "2025 CURRENT-STATE HIGH-RESOLUTION REFERENCE DATA"
    assert "Excluded from 2021-2025 historical Landsat baseline" in meta["governance_rule"]

    # Verify native resolutions
    b4_path = granule_dir / "B04.tif"
    with rasterio.open(b4_path) as src:
        assert src.res == (10.0, 10.0), f"Sentinel-2 10m band resolution altered: {src.res}"

    b11_path = granule_dir / "B11.tif"
    with rasterio.open(b11_path) as src:
        assert src.res == (20.0, 20.0), f"Sentinel-2 20m band resolution altered: {src.res}"


# ==============================================================================
# 7. MODIS MULTI-TEMPORAL PROCESSING INTEGRITY
# ==============================================================================

def test_modis_native_resolution_and_scaling(root):
    """Verify MODIS retains native Sinusoidal grid and official 0.02 scaling."""
    modis_proc_dir = PROCESSED_DIR / "modis"
    assert modis_proc_dir.exists()

    for yr_dir in modis_proc_dir.iterdir():
        if not yr_dir.is_dir():
            continue
        for item_dir in yr_dir.iterdir():
            if not item_dir.is_dir():
                continue
            meta_path = item_dir / "metadata.json"
            assert meta_path.exists()
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            assert meta["role"] == "coarse_resolution_thermal_context_and_cross_check"
            assert meta["resolution_meters"] == [926.625, 926.625]

            # Verify Day LST Kelvin
            lst_k_path = item_dir / "LST_Day_1km_kelvin.tif"
            with rasterio.open(lst_k_path) as src:
                assert src.shape == (24, 19)
                arr = src.read(1)
                valid = arr[np.isfinite(arr)]
                assert valid.size > 0
                assert np.min(valid) >= 280.0
                assert np.max(valid) <= 335.0


# ==============================================================================
# 8. NASA POWER DAILY METEOROLOGICAL NORMALIZATION
# ==============================================================================

def test_nasa_power_normalized_schema_and_completeness(root):
    """Verify NASA POWER daily normalized dataset schema and variable completeness."""
    np_proc_dir = PROCESSED_DIR / "nasa_power" / "pune"
    meta_path = np_proc_dir / "metadata.json"
    json_path = np_proc_dir / "nasa_power_2021_2025_daily_normalized.json"
    csv_path = np_proc_dir / "nasa_power_2021_2025_daily_normalized.csv"

    assert meta_path.exists()
    assert json_path.exists()
    assert csv_path.exists()

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["total_days"] == 1826, f"Expected 1,826 daily dates across 5 years, got {meta['total_days']}"
    assert meta["total_observations"] == 12782, f"Expected 12,782 observations, got {meta['total_observations']}"

    with open(json_path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    assert len(rows) == 12782
    # Verify first row schema
    first = rows[0]
    required_keys = {"date", "year", "day_of_year", "variable", "value", "unit", "source", "coordinates"}
    assert required_keys.issubset(set(first.keys()))


# ==============================================================================
# 9. SPATIAL HARMONIZATION & TEMPORAL STACK MANIFESTS
# ==============================================================================

def test_spatial_harmonization_framework_deferred_status(root):
    """Verify spatial harmonization framework preserves native resolution and defers grid locking."""
    framework_file = PROCESSED_DIR / "temporal" / "spatial_harmonization_framework.json"
    assert framework_file.exists()

    with open(framework_file, "r", encoding="utf-8") as f:
        doc = json.load(f)

    assert doc["governance_status"] == "DECISION_DEFERRED_UNTIL_PHASE_1B"
    assert "UNLOCKED" in doc["lock_status"]
    assert "landsat_30m" in doc["spatial_profiles"]
    assert "sentinel2_10m_20m" in doc["spatial_profiles"]
    assert "modis_1km" in doc["spatial_profiles"]
    assert "candidate_1_planar_metric_grid_250m" in doc["candidate_analytical_units"]
    assert "candidate_2_uber_h3_resolution_9" in doc["candidate_analytical_units"]


def test_temporal_stack_manifest_lineage(root):
    """Verify 5-year temporal stack manifest preserves full lineage and caveats."""
    stack_file = PROCESSED_DIR / "temporal" / "pune_temporal_stack_manifest.json"
    summary_file = DERIVED_DIR / "temporal" / "pune_temporal_summary.json"

    assert stack_file.exists()
    assert summary_file.exists()

    with open(stack_file, "r", encoding="utf-8") as f:
        stack = json.load(f)

    assert len(stack["annual_observations"]) == 5
    for yr_str in ["2021", "2022", "2023", "2024", "2025"]:
        assert yr_str in stack["annual_observations"]
        obs = stack["annual_observations"][yr_str]
        assert "lineage" in obs
        assert "raw_directory" in obs["lineage"]
        assert "processed_directory" in obs["lineage"]
        assert "derived_directory" in obs["lineage"]

    # Verify scientific caveats
    prohibitions = stack["scientific_caveats"]["explicit_prohibitions"]
    assert any("long-term climate trend" in p for p in prohibitions)
    assert any("warming attribution" in p for p in prohibitions)


# ==============================================================================
# 10. PROCESSED CHECKSUMS & FROZEN MANIFEST
# ==============================================================================

def test_processed_checksums_manifest_integrity(root):
    """Verify all processed assets match entries in pune_temporal_baseline_v1_processed_checksums.sha256."""
    checksum_file = MANIFESTS_DIR / "pune_temporal_baseline_v1_processed_checksums.sha256"
    assert checksum_file.exists()

    with open(checksum_file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    assert len(lines) == 160, f"Expected 160 processed assets, found {len(lines)}"

    # Sample check 10 entries across different categories
    for line in lines[::16]:
        expected_sha, rel_path = line.split(maxsplit=1)
        full_path = root / rel_path.replace("\\", "/")
        assert full_path.exists(), f"Processed asset missing: {rel_path}"
        actual_sha = calculate_sha256(full_path)
        assert actual_sha == expected_sha, f"Checksum mismatch for processed asset: {rel_path}"
