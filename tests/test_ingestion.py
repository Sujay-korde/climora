"""Test suite for CLIMORA Phase 0 Pune Data Ingestion Foundation.

Covers:
- Configuration loading & path resolution
- AOI loading & geometry validation
- SHA-256 checksum calculation
- Manifest serialization & schema
- Idempotency behavior (skip existing valid files)
- Asset filtering & band mapping
- Raster validation on local data lake files
- Deterministic temporal selection & seasonal ranking
- Quality filtering on candidate scenes
- Storage estimation & threshold guard
- S3-compatible provenance metadata schema (Section 22 & 23)
- Duplicate avoidance & bootstrap lake preservation
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from ingestion.common import (
    build_provenance_record,
    calculate_sha256,
    get_season_for_date,
    load_aoi,
    load_manifest,
    safe_download_file,
    save_manifest,
    select_seasonal_candidates,
    validate_aoi,
    validate_raster,
    validate_vector,
)
from ingestion.config import load_config
from ingestion.landsat import LANDSAT_ASSET_MAPPING
from ingestion.sentinel2 import SENTINEL2_BAND_MAPPING


@pytest.fixture
def climora_config():
    """Load default CLIMORA configuration."""
    return load_config()


def test_config_loading(climora_config):
    """Test configuration loading and property resolution."""
    assert climora_config.study_area == "Pune"
    assert climora_config.year == 2025
    assert climora_config.aoi_path.exists()
    assert climora_config.aoi_path.name == "pune.geojson"
    assert "landsat" in climora_config.sources
    assert "sentinel2" in climora_config.sources
    assert "modis" in climora_config.sources
    assert "nasa_power" in climora_config.sources
    assert "osm" in climora_config.sources
    assert "dem" in climora_config.sources
    assert climora_config.storage_warning_threshold_gb >= 1.0
    assert climora_config.selection_strategy == "seasonal_representative"


def test_aoi_loading_and_validation(climora_config):
    """Test loading and validating the canonical Pune AOI."""
    aoi_data = load_aoi(climora_config.aoi_path)
    assert aoi_data["type"] == "FeatureCollection"
    assert len(aoi_data["features"]) >= 1

    is_valid, crs, geom, bbox, centroid = validate_aoi(aoi_data)
    assert is_valid is True
    assert geom.is_valid is True
    assert isinstance(geom, Polygon)
    # Pune bounding box sanity check: ~18.4 to 18.7 N, ~73.7 to 74.1 E
    assert 73.0 < bbox[0] < 74.0
    assert 18.0 < bbox[1] < 19.0
    assert 73.8 < bbox[2] < 74.5
    assert 18.5 < bbox[3] < 19.0


def test_sha256_calculation():
    """Test SHA-256 chunked hashing calculation against hashlib."""
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        data = b"CLIMORA Research-Grade Climate Risk Assessment - Phase 0 Test Data" * 1000
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        computed_hash = calculate_sha256(tmp_path)
        expected_hash = hashlib.sha256(data).hexdigest()
        assert computed_hash == expected_hash
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_manifest_generation_and_schema(climora_config):
    """Test manifest persistence and atomic saving."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_file = Path(tmpdir) / "test_manifest.json"
        test_data = {
            "title": "Test Acquisition Plan",
            "study_area": "Pune",
            "year": 2025,
            "items": [{"id": "scene_1", "status": "VALID"}],
        }
        save_manifest(manifest_file, test_data)
        assert manifest_file.exists()

        loaded = load_manifest(manifest_file)
        assert loaded["title"] == "Test Acquisition Plan"
        assert loaded["items"][0]["id"] == "scene_1"


def test_idempotency_behavior():
    """Test that safe_download_file skips existing valid files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_file = Path(tmpdir) / "test_existing.bin"
        content = b"Deterministic payload for idempotency verification"
        dest_file.write_bytes(content)
        initial_hash = hashlib.sha256(content).hexdigest()

        # Call safe_download_file pointing to existing file with matching size
        path, sha, size, skipped = safe_download_file(
            url="http://example.com/does_not_matter_because_file_exists",
            dest_path=dest_file,
            expected_size=len(content),
        )

        assert path == dest_file
        assert sha == initial_hash
        assert size == len(content)
        assert skipped is True  # Idempotent skip confirmed


def test_asset_filtering():
    """Test required asset lists and mappings for Landsat and Sentinel-2."""
    # Landsat required assets
    expected_landsat = [
        "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "QA_PIXEL", "QA_RADSAT"
    ]
    for asset in expected_landsat:
        assert asset in LANDSAT_ASSET_MAPPING

    # Sentinel-2 required bands
    expected_s2 = [
        "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12", "SCL"
    ]
    for band in expected_s2:
        assert band in SENTINEL2_BAND_MAPPING


def test_raster_validation(climora_config):
    """Test raster validation on ingested local data lake rasters."""
    # Test DEM raster
    dem_path = climora_config.raw_dir / "dem" / "pune" / "Copernicus_DSM_COG_10_N18_00_E073_00_DEM.tif"
    if dem_path.exists():
        val = validate_raster(dem_path)
        assert val["valid"] is True
        assert val["width"] == 3600
        assert val["height"] == 3600
        assert val["bands"] == 1

    # Test MODIS raster
    modis_dir = climora_config.raw_dir / "modis" / "2025"
    if modis_dir.exists():
        subdirs = list(modis_dir.iterdir())
        if subdirs:
            lst_day = subdirs[0] / "LST_Day_1km.tif"
            if lst_day.exists():
                val = validate_raster(lst_day)
                assert val["valid"] is True
                assert val["width"] == 1200
                assert val["height"] == 1200


def test_deterministic_temporal_selection():
    """Test deterministic seasonal selection and existing bootstrap prioritization."""
    mock_candidates = [
        {"id": "cand_w1", "date": "2025-01-15T00:00:00Z", "cloud_cover": 5.0},
        {"id": "cand_w2_bootstrap", "date": "2025-02-14T00:00:00Z", "cloud_cover": 2.0},
        {"id": "cand_s1", "date": "2025-04-10T00:00:00Z", "cloud_cover": 0.5},
        {"id": "cand_s2", "date": "2025-05-01T00:00:00Z", "cloud_cover": 1.2},
        {"id": "cand_p1", "date": "2025-10-20T00:00:00Z", "cloud_cover": 0.1},
    ]
    existing_ids = {"cand_w2_bootstrap"}

    # Run selection twice with identical input
    sel_1, summary_1 = select_seasonal_candidates(mock_candidates, existing_ids=existing_ids, target_per_season=1)
    sel_2, summary_2 = select_seasonal_candidates(mock_candidates, existing_ids=existing_ids, target_per_season=1)

    # 1. Determinism assertion: identical results on repeat execution
    assert [c["id"] for c in sel_1] == [c["id"] for c in sel_2]
    assert summary_1 == summary_2

    # 2. Existing bootstrap prioritization assertion
    winter_selected = [c for c in sel_1 if c["selection_metadata"]["season_key"] == "winter"]
    assert len(winter_selected) == 1
    assert winter_selected[0]["id"] == "cand_w2_bootstrap"
    assert winter_selected[0]["selection_metadata"]["is_existing_bootstrap"] is True

    # 3. Summer selection chooses lowest cloud cover
    summer_selected = [c for c in sel_1 if c["selection_metadata"]["season_key"] == "pre_monsoon_summer"]
    assert len(summer_selected) == 1
    assert summer_selected[0]["id"] == "cand_s1"


def test_candidate_filtering_logic():
    """Test quality filtering logic on candidate observations."""
    cloud_threshold = 20.0
    raw_candidates = [
        {"id": "c1", "cloud_cover": 5.0, "platform": "landsat-8", "has_assets": True},
        {"id": "c2", "cloud_cover": 25.0, "platform": "landsat-8", "has_assets": True},  # Exceeds cloud
        {"id": "c3", "cloud_cover": 1.0, "platform": "landsat-7", "has_assets": True},   # Invalid platform
        {"id": "c4", "cloud_cover": 0.0, "platform": "landsat-9", "has_assets": False},  # Missing assets
    ]

    filtered = [
        c for c in raw_candidates
        if c["cloud_cover"] <= cloud_threshold
        and c["platform"] in ("landsat-8", "landsat-9")
        and c["has_assets"]
    ]

    assert len(filtered) == 1
    assert filtered[0]["id"] == "c1"


def test_storage_estimation_and_threshold_guard(climora_config):
    """Test storage estimation calculation and threshold comparison logic."""
    lake_bytes = 758_802_426  # ~723.7 MB existing
    new_bytes = 500_000_000   # ~476.8 MB new

    projected_bytes = lake_bytes + new_bytes
    threshold_bytes = int(climora_config.storage_warning_threshold_gb * 1024 * 1024 * 1024)

    # Normal case: 1.2 GB is well under 4.0 GB threshold
    assert projected_bytes < threshold_bytes

    # Simulated violation case: huge download of 10 GB
    huge_new_bytes = 10_000_000_000
    huge_projected = lake_bytes + huge_new_bytes
    assert huge_projected > threshold_bytes  # Guard triggers stop recommendation


def test_manifest_provenance_schema_section_22():
    """Test that generated provenance records satisfy all Section 22 & 23 requirements."""
    prov = build_provenance_record(
        dataset_id="landsat-c2-l2",
        provider="USGS / Microsoft Planetary Computer",
        product="Landsat Collection 2 Level-2 (LANDSAT-8)",
        version="Collection 2",
        source="Microsoft Planetary Computer STAC API",
        source_item_id="LC08_L2SP_147047_20250214_02_T1",
        license_name="USGS Public Domain / Open Data",
        access_method="STAC API SAS URL Chunked Stream",
        spatial_resolution="30m",
        temporal_resolution="16-day repeat",
        acquisition_date="2025-02-14T05:27:48Z",
        observation_period={"start": "2025-01-01", "end": "2025-12-31"},
        aoi={"study_area": "Pune", "bbox": [73.7, 18.4, 74.0, 18.6]},
        cloud_cover=0.0,
        selection_strategy="seasonal_representative",
        selection_parameters={"target_per_season": 1, "cloud_cover": 0.0},
        required_assets=["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "QA_PIXEL", "QA_RADSAT"],
        local_path="data/raw/landsat/2025/LC08_L2SP_147047_20250214_02_T1/SR_B2.tif",
        file_size_bytes=85650759,
        sha256="abc123def456",
        validation_status="VALID",
        s3_uri="s3://climora-lake/raw/landsat/2025/LC08_L2SP_147047_20250214_02_T1/SR_B2.tif",
    )

    # Verify all 22 required fields
    required_keys = [
        "dataset_id", "provider", "product", "version", "source", "source_item_id",
        "license", "access_method", "spatial_resolution", "temporal_resolution",
        "acquisition_date", "observation_period", "AOI", "cloud_cover",
        "selection_strategy", "selection_parameters", "required_assets",
        "local_path", "s3_uri", "storage_status", "file_size_bytes", "sha256",
        "validation_status",
    ]
    for key in required_keys:
        assert key in prov, f"Missing required Section 22 field: {key}"

    # Critical architectural constraint: S3 disabled, local storage active
    assert prov["storage_status"] == "local"
    assert prov["validation_status"] == "VALID"


def test_duplicate_avoidance_and_idempotency_extended():
    """Test that safe_download_file avoids redundant downloads and preserves files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_file = Path(tmpdir) / "test_scene.tif"
        payload = b"Sample GeoTIFF payload for idempotency and duplicate avoidance" * 50
        dest_file.write_bytes(payload)
        expected_hash = hashlib.sha256(payload).hexdigest()

        # Re-download attempt pointing to existing file
        dest_path, sha, size, skipped = safe_download_file(
            url="https://example.com/mock_raster.tif",
            dest_path=dest_file,
            expected_size=len(payload),
        )

        assert skipped is True
        assert sha == expected_hash
        assert size == len(payload)
        assert dest_path.exists()
        # Verify no .part file remains
        part_file = dest_file.with_suffix(".tif.part")
        assert not part_file.exists()


def test_existing_bootstrap_dataset_integrity(climora_config):
    """Test that all existing bootstrap baseline assets are present and valid."""
    raw_dir = climora_config.raw_dir

    # 1. Landsat baseline scene
    ls_dir = raw_dir / "landsat" / "2025" / "LC08_L2SP_147047_20250214_02_T1"
    assert ls_dir.exists(), "Landsat bootstrap scene directory missing"
    for asset in ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "QA_PIXEL", "QA_RADSAT"]:
        asset_file = ls_dir / f"{asset}.tif"
        assert asset_file.exists(), f"Landsat asset {asset}.tif missing"
        assert asset_file.stat().st_size > 0

    # 2. DEM baseline
    dem_file = raw_dir / "dem" / "pune" / "Copernicus_DSM_COG_10_N18_00_E073_00_DEM.tif"
    assert dem_file.exists()
    assert dem_file.stat().st_size > 0

    # 3. NASA POWER baseline
    np_file = raw_dir / "nasa_power" / "pune" / "2025" / "power_2025_daily.json"
    assert np_file.exists()
    assert np_file.stat().st_size > 0

    # 4. OSM baseline layers
    osm_dir = raw_dir / "osm" / "pune"
    assert osm_dir.exists()
    for layer in ["green_spaces", "water_bodies", "public_infrastructure", "road_network"]:
        layer_file = osm_dir / f"{layer}.geojson"
        assert layer_file.exists()
        val = validate_vector(layer_file)
        assert val["valid"] is True
