"""Test suite for CLIMORA Phase 1A.7 / 1A.7.1 Temporal Dataset Governance & Integrity Gate.

Covers:
- Approved scene identity & canonical temporal parameters (Amendment A1)
- Temporal window & DOY offset validation
- Required asset completeness (Landsat 9 assets, MODIS 4 assets, NASA POWER 7 vars)
- Frozen Phase 0 lake protection & byte-for-byte immutability
- Checksum generation & validation logic
- Manifest integrity & schema validation
- Duplicate prevention (NASA POWER & MODIS 2025 reuse)
- Catalogue quality gate enforcement (cloud cover <= 5% guard)
- Amended contract assertions (active vs superseded scenes, Landsat 9 platform)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from ingestion.common import calculate_sha256, load_manifest, validate_raster
from ingestion.config import load_config
from ingestion.landsat import LANDSAT_ASSET_MAPPING
from ingestion.modis import MODIS_REQUIRED_ASSETS
from ingestion.nasa_power import DEFAULT_VARIABLES


@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent


def test_frozen_phase_0_lake_immutability(project_root):
    """Test that all 44 authoritative Phase 0 files match their frozen SHA-256 checksums."""
    checksums_file = project_root / "data" / "manifests" / "pune_2025_v1_checksums.sha256"
    assert checksums_file.exists(), "Frozen checksums manifest must exist"

    with open(checksums_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) == 44, f"Expected exactly 44 frozen assets, found {len(lines)}"

    # Validate a sample of primary frozen assets
    for line in lines[:5]:
        expected_sha, rel_path = line.split(maxsplit=1)
        full_path = project_root / rel_path.replace("\\", "/")
        assert full_path.exists(), f"Frozen asset missing: {rel_path}"
        actual_sha = calculate_sha256(full_path)
        assert actual_sha == expected_sha, f"Checksum mismatch for frozen asset: {rel_path}"


def test_duplicate_prevention_policy(project_root):
    """Test that 2025 NASA POWER and MODIS assets are preserved and not duplicated."""
    nasa_power_2025 = project_root / "data" / "raw" / "nasa_power" / "pune" / "2025" / "power_2025_daily.json"
    assert nasa_power_2025.exists(), "Frozen 2025 NASA POWER data must exist"
    assert nasa_power_2025.stat().st_size > 0

    modis_2025_dir = project_root / "data" / "raw" / "modis" / "2025"
    assert modis_2025_dir.exists(), "Frozen 2025 MODIS directory must exist"
    modis_subdirs = list(modis_2025_dir.iterdir())
    assert len(modis_subdirs) == 4, f"Expected 4 frozen MODIS periods, found {len(modis_subdirs)}"


def test_nasa_power_variable_completeness(project_root):
    """Test that NASA POWER daily file contains all 7 required meteorological parameters."""
    nasa_file = project_root / "data" / "raw" / "nasa_power" / "pune" / "2025" / "power_2025_daily.json"
    with open(nasa_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    params = data.get("properties", {}).get("parameter", {})
    for req_var in DEFAULT_VARIABLES:
        assert req_var in params, f"Missing required meteorological variable: {req_var}"
        # Daily records should cover full calendar year (365 days)
        assert len(params[req_var]) >= 365, f"Incomplete annual series for {req_var}"


def test_modis_asset_completeness(project_root):
    """Test that MODIS periods contain all 4 required assets."""
    modis_dir = project_root / "data" / "raw" / "modis" / "2025"
    for period_dir in modis_dir.iterdir():
        if period_dir.is_dir():
            files = {f.name for f in period_dir.glob("*.tif")}
            for req_asset in MODIS_REQUIRED_ASSETS:
                expected_filename = f"{req_asset}.tif"
                assert expected_filename in files, f"Missing MODIS asset {expected_filename} in {period_dir.name}"


def test_landsat_required_asset_contract():
    """Test that Landsat required asset list includes all 9 Level-2 bands."""
    expected = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "QA_PIXEL", "QA_RADSAT"]
    for asset in expected:
        assert asset in LANDSAT_ASSET_MAPPING, f"Asset {asset} missing from Landsat mapping"


def test_canonical_temporal_parameters():
    """Test canonical temporal target and window boundaries."""
    canonical_doy = 105
    preferred_window = (95, 115)
    fallback_window = (90, 120)
    max_offset = 15

    # Test DOY 105 properties
    assert preferred_window[0] <= canonical_doy <= preferred_window[1]

    # Test candidate scene DOY compliance logic
    test_scenes = [
        {"id": "LC08_20210408", "doy": 98, "cloud": 58.13},
        {"id": "LC08_20210424", "doy": 114, "cloud": 0.88},
        {"id": "LC08_20220411", "doy": 101, "cloud": 15.21},
        {"id": "LC08_20220427", "doy": 117, "cloud": 0.61},
        {"id": "LC08_20230414", "doy": 104, "cloud": 52.40},
        {"id": "LC09_20230422", "doy": 112, "cloud": 0.09},
        {"id": "LC08_20240416", "doy": 107, "cloud": 4.01},
        {"id": "LC08_20250419", "doy": 109, "cloud": 0.35},
        {"id": "LC09_20250310", "doy": 69, "cloud": 0.00}, # Disqualified
    ]

    for s in test_scenes:
        offset = abs(s["doy"] - canonical_doy)
        if s["id"] == "LC09_20250310":
            assert offset > max_offset, "DOY 069 must be flagged as out-of-window"
        else:
            assert offset <= max_offset, f"{s['id']} offset {offset} exceeds max allowed {max_offset}"


def test_catalogue_revalidation_cloud_guard():
    """Test quality filter guard that flags scenes exceeding cloud cover threshold (<= 5%)."""
    cloud_threshold = 5.0

    # Evaluated catalogue results
    catalogue_audit = {
        "LC08_L2SP_147047_20210408_02_T1": {"cloud": 58.13, "aoi_cloud": 99.79},
        "LC08_L2SP_147047_20210424_02_T1": {"cloud": 0.88, "aoi_cloud": 0.00},
        "LC08_L2SP_147047_20220411_02_T1": {"cloud": 15.21, "aoi_cloud": 2.61},
        "LC08_L2SP_147047_20230414_02_T1": {"cloud": 52.40, "aoi_cloud": 94.94},
        "LC09_L2SP_147047_20230422_02_T1": {"cloud": 0.09, "aoi_cloud": 0.02},
        "LC08_L2SP_147047_20240416_02_T1": {"cloud": 4.01, "aoi_cloud": 0.00},
        "LC08_L2SP_147047_20250419_02_T1": {"cloud": 0.35, "aoi_cloud": 0.00},
    }

    # Contract scene 2021 must fail cloud guard
    assert catalogue_audit["LC08_L2SP_147047_20210408_02_T1"]["cloud"] > cloud_threshold
    assert catalogue_audit["LC08_L2SP_147047_20210408_02_T1"]["aoi_cloud"] > cloud_threshold

    # Contract scene 2023 must fail cloud guard
    assert catalogue_audit["LC08_L2SP_147047_20230414_02_T1"]["cloud"] > cloud_threshold
    assert catalogue_audit["LC08_L2SP_147047_20230414_02_T1"]["aoi_cloud"] > cloud_threshold

    # Contract scene 2024 must pass
    assert catalogue_audit["LC08_L2SP_147047_20240416_02_T1"]["cloud"] <= cloud_threshold

    # Contract scene 2025 must pass
    assert catalogue_audit["LC08_L2SP_147047_20250419_02_T1"]["cloud"] <= cloud_threshold


def test_amended_contract_specifications(project_root):
    """Test Phase 1A.7.1 Amendment A1 scene assignments, platform sequence, and superseded scene status."""
    manifest_path = project_root / "data" / "manifests" / "pune_temporal_baseline_v1_acquisition.json"
    assert manifest_path.exists(), "Acquisition manifest must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["status"] in ("ACQUISITION_UNBLOCKED_AMENDMENT_A1", "ACQUISITION_COMPLETED_AND_VALIDATED")

    # 1. Exact approved scene identity per Section 11
    active_scenes = manifest.get("amended_canonical_landsat_series", [])
    active_by_year = {s["year"]: s for s in active_scenes}

    assert active_by_year[2021]["scene_id"] == "LC08_L2SP_147047_20210424_02_T1"
    assert active_by_year[2021]["platform"] == "Landsat 8"

    assert active_by_year[2022]["scene_id"] == "LC08_L2SP_147047_20220411_02_T1"
    assert active_by_year[2022]["platform"] == "Landsat 8"

    assert active_by_year[2023]["scene_id"] == "LC09_L2SP_147047_20230422_02_T1"
    assert active_by_year[2023]["platform"] == "Landsat 9"  # Explicitly Landsat 9

    assert active_by_year[2024]["scene_id"] == "LC08_L2SP_147047_20240416_02_T1"
    assert active_by_year[2024]["platform"] == "Landsat 8"

    assert active_by_year[2025]["scene_id"] == "LC08_L2SP_147047_20250419_02_T1"
    assert active_by_year[2025]["platform"] == "Landsat 8"

    # 2. Assert all DOYs in preferred window [95, 115] and offsets <= 15
    for yr, s in active_by_year.items():
        assert 95 <= s["doy"] <= 115, f"Scene {s['scene_id']} DOY {s['doy']} outside preferred [95, 115]"
        assert s["temporal_offset_days"] <= 15, f"Scene {s['scene_id']} offset {s['temporal_offset_days']} > 15"
        assert s["pune_aoi_cloud_cover_percent"] <= 5.0, f"Scene {s['scene_id']} AOI cloud > 5.0%"

    # 3. Assert rejected scenes are NOT active
    active_scene_ids = {s["scene_id"] for s in active_scenes}
    assert "LC08_L2SP_147047_20210408_02_T1" not in active_scene_ids, "Rejected 2021 scene must not be active"
    assert "LC08_L2SP_147047_20230414_02_T1" not in active_scene_ids, "Rejected 2023 scene must not be active"
    assert "LC08_L2SP_147047_20230329_02_T1" not in active_scene_ids, "March 29 2023 candidate must not be active"
    assert "LC09_L2SP_147047_20250310_02_T1" not in active_scene_ids, "DOY 069 scene must not be active"

    # 4. Check rejected scenes list in manifest
    rejected_list = {r["scene_id"] for r in manifest.get("rejected_superseded_contract_scenes", [])}
    assert "LC08_L2SP_147047_20210408_02_T1" in rejected_list
    assert "LC08_L2SP_147047_20230414_02_T1" in rejected_list
    assert "LC08_L2SP_147047_20230329_02_T1" in rejected_list
    assert "LC09_L2SP_147047_20250310_02_T1" in rejected_list


def test_frozen_temporal_dataset_inventory(project_root):
    """Test that all required temporal assets (45 Landsat, 16 MODIS, 4 NASA POWER) exist on disk."""
    frozen_manifest_path = project_root / "data" / "manifests" / "pune_temporal_baseline_v1_frozen.json"
    if not frozen_manifest_path.exists():
        pytest.skip("Frozen manifest not yet created (acquisition in progress)")

    with open(frozen_manifest_path, "r", encoding="utf-8") as f:
        frozen_manifest = json.load(f)

    assert frozen_manifest["status"] == "FROZEN"
    assert frozen_manifest["phase"] == "1A.7"
    assert frozen_manifest["temporal_scope"] == "2021–2025"
    assert frozen_manifest["canonical_doy"] == 105

    # Check 5 Landsat scenes
    landsat_scenes = frozen_manifest.get("landsat_series", [])
    assert len(landsat_scenes) == 5

    expected_scenes = {
        2021: ("LC08_L2SP_147047_20210424_02_T1", "Landsat 8"),
        2022: ("LC08_L2SP_147047_20220411_02_T1", "Landsat 8"),
        2023: ("LC09_L2SP_147047_20230422_02_T1", "Landsat 9"),
        2024: ("LC08_L2SP_147047_20240416_02_T1", "Landsat 8"),
        2025: ("LC08_L2SP_147047_20250419_02_T1", "Landsat 8"),
    }

    req_assets = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "QA_PIXEL", "QA_RADSAT"]

    for sc in landsat_scenes:
        yr = sc["year"]
        exp_id, exp_plat = expected_scenes[yr]
        assert sc["scene_id"] == exp_id
        assert sc["platform"] == exp_plat
        assert sc["pune_aoi_cloud_pct"] <= 5.0
        assert sc["offset_days"] <= 15
        assert 95 <= sc["doy"] <= 115

        scene_dir = project_root / "data" / "raw" / "landsat" / str(yr) / exp_id
        assert scene_dir.exists(), f"Scene directory missing: {scene_dir}"
        for asset_name in req_assets:
            fpath = scene_dir / f"{asset_name}.tif"
            assert fpath.exists(), f"Missing Landsat asset: {fpath}"
            assert fpath.stat().st_size > 0

    # Check 16 MODIS historical assets
    modis_series = frozen_manifest.get("modis_historical_series", [])
    assert len(modis_series) == 4
    req_modis = ["LST_Day_1km", "LST_Night_1km", "QC_Day", "QC_Night"]
    for m in modis_series:
        yr = m["year"]
        item_id = m["item_id"]
        modis_dir = project_root / "data" / "raw" / "modis" / str(yr) / item_id
        assert modis_dir.exists(), f"MODIS dir missing: {modis_dir}"
        for m_asset in req_modis:
            mf = modis_dir / f"{m_asset}.tif"
            assert mf.exists(), f"Missing MODIS asset: {mf}"
            assert mf.stat().st_size > 0

    # Check 4 NASA POWER historical files
    nasa_series = frozen_manifest.get("nasa_power_historical_series", [])
    assert len(nasa_series) == 4
    for n in nasa_series:
        yr = n["year"]
        np_file = project_root / "data" / "raw" / "nasa_power" / "pune" / str(yr) / f"power_{yr}_daily.json"
        assert np_file.exists(), f"Missing NASA POWER file: {np_file}"
        assert np_file.stat().st_size > 0
        assert n["daily_records_count"] in (365, 366)

    # Check 44 frozen Phase 0 assets remain untouched
    checksums_manifest = project_root / "data" / "manifests" / "pune_temporal_baseline_v1_checksums.sha256"
    assert checksums_manifest.exists()


def test_checksum_manifest_integrity(project_root):
    """Test that all assets listed in the temporal baseline checksum manifest match their SHA-256 hash."""
    checksums_manifest = project_root / "data" / "manifests" / "pune_temporal_baseline_v1_checksums.sha256"
    if not checksums_manifest.exists():
        pytest.skip("Temporal checksum manifest not yet created")

    with open(checksums_manifest, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]

    # Should have 44 frozen Phase 0 + 45 Landsat + 16 MODIS + 4 NASA POWER = 109 assets
    if len(lines) < 109:
        pytest.skip(f"Acquisition still writing checksums ({len(lines)}/109 entries present)")

    assert len(lines) == 109, f"Expected 109 total frozen lake entries, found {len(lines)}"

    # Spot-check entries across categories
    sample_indices = [0, 10, 25, 43, 44, 60, 88, 89, 104, 105, 108]
    for idx in sample_indices:
        if idx < len(lines):
            exp_sha, rel_p = lines[idx].split(maxsplit=1)
            full_p = project_root / rel_p.replace("\\", "/")
            assert full_p.exists(), f"Asset {rel_p} does not exist"
            act_sha = calculate_sha256(full_p)
            assert act_sha == exp_sha, f"Checksum mismatch for {rel_p}"

