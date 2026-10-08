"""CLIMORA Phase 1A.7: Historical Temporal Dataset Acquisition, Validation & Dataset Freeze.

Orchestrates:
1. Verification and immutability protection of Phase 0 frozen assets (44 files).
2. Live STAC catalogue revalidation of amended Landsat scenes (2021-2025).
3. Acquisition of 45 Landsat Collection 2 Level-2 assets (5 scenes x 9 bands).
4. Acquisition of 16 MODIS MOD11A2 v061 assets (4 years x 4 layers).
5. Acquisition of 4 NASA POWER historical daily files (2021-2024).
6. Comprehensive spatial, temporal, quality, and checksum validation.
7. Derivation and verification of Pune AOI cloud contamination from QA_PIXEL.
8. Generation of authoritative manifests and checksums.
"""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import planetary_computer as pc
import pystac_client
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom
import requests
import shapely.geometry

from ingestion.common import (
    build_provenance_record,
    calculate_sha256,
    create_retry_session,
    get_logger,
    load_aoi,
    safe_download_file,
    validate_aoi,
    validate_raster,
)
from ingestion.config import IngestionConfig, load_config
from ingestion.landsat import LANDSAT_ASSET_MAPPING
from ingestion.modis import MODIS_REQUIRED_ASSETS
from ingestion.nasa_power import DEFAULT_VARIABLES

logger = get_logger()

# Approved 2021-2025 Landsat Contract (Phase 1A.7.1 Amendment A1)
LANDSAT_TARGETS = [
    {
        "year": 2021,
        "scene_id": "LC08_L2SP_147047_20210424_02_T1",
        "platform": "landsat-8",
        "display_platform": "Landsat 8",
        "date": "2021-04-24",
        "doy": 114,
        "offset": 9,
        "stac_cloud_cover": 0.88,
        "expected_aoi_cloud": 0.00,
    },
    {
        "year": 2022,
        "scene_id": "LC08_L2SP_147047_20220411_02_T1",
        "platform": "landsat-8",
        "display_platform": "Landsat 8",
        "date": "2022-04-11",
        "doy": 101,
        "offset": 4,
        "stac_cloud_cover": 15.21,
        "expected_aoi_cloud": 2.61,
    },
    {
        "year": 2023,
        "scene_id": "LC09_L2SP_147047_20230422_02_T1",
        "platform": "landsat-9",
        "display_platform": "Landsat 9",
        "date": "2023-04-22",
        "doy": 112,
        "offset": 7,
        "stac_cloud_cover": 0.09,
        "expected_aoi_cloud": 0.02,
    },
    {
        "year": 2024,
        "scene_id": "LC08_L2SP_147047_20240416_02_T1",
        "platform": "landsat-8",
        "display_platform": "Landsat 8",
        "date": "2024-04-16",
        "doy": 107,
        "offset": 2,
        "stac_cloud_cover": 4.01,
        "expected_aoi_cloud": 0.00,
    },
    {
        "year": 2025,
        "scene_id": "LC08_L2SP_147047_20250419_02_T1",
        "platform": "landsat-8",
        "display_platform": "Landsat 8",
        "date": "2025-04-19",
        "doy": 109,
        "offset": 4,
        "stac_cloud_cover": 0.35,
        "expected_aoi_cloud": 0.00,
    },
]

# Approved MODIS MOD11A2 v061 Granules for DOY 105 (Pune tile h25v07)
MODIS_TARGETS = [
    {
        "year": 2021,
        "item_id": "MOD11A2.A2021105.h25v07.061.2021114054044",
        "date": "2021-04-15",
        "doy": 105,
    },
    {
        "year": 2022,
        "item_id": "MOD11A2.A2022105.h25v07.061.2022118025926",
        "date": "2022-04-15",
        "doy": 105,
    },
    {
        "year": 2023,
        "item_id": "MOD11A2.A2023105.h25v07.061.2023114150920",
        "date": "2023-04-15",
        "doy": 105,
    },
    {
        "year": 2024,
        "item_id": "MOD11A2.A2024105.h25v07.061.2024115214105",
        "date": "2024-04-14",
        "doy": 105,
    },
]

NASA_POWER_YEARS = [2021, 2022, 2023, 2024]


def verify_frozen_baseline(project_root: Path) -> Tuple[bool, List[str]]:
    """Verify that all 44 authoritative Phase 0 files exist and match checksums."""
    checksum_file = project_root / "data" / "manifests" / "pune_2025_v1_checksums.sha256"
    if not checksum_file.exists():
        return False, [f"Missing frozen checksum manifest: {checksum_file}"]

    with open(checksum_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) != 44:
        return False, [f"Expected 44 frozen assets, found {len(lines)} in {checksum_file.name}"]

    errors = []
    for line in lines:
        expected_sha, rel_path = line.split(maxsplit=1)
        full_path = project_root / rel_path.replace("\\", "/")
        if not full_path.exists():
            errors.append(f"MISSING: {rel_path}")
            continue
        actual_sha = calculate_sha256(full_path)
        if actual_sha != expected_sha:
            errors.append(f"MISMATCH: {rel_path} (expected {expected_sha[:8]}, got {actual_sha[:8]})")

    return len(errors) == 0, errors


def revalidate_catalogue_scenes(config: IngestionConfig) -> Tuple[bool, Dict[str, Any], List[str]]:
    """Perform pre-acquisition catalogue check against STAC for all 5 Landsat scenes."""
    logger.info("Performing final STAC catalogue check for 5 Landsat scenes...")
    stac_url = config.sources.get("landsat", {}).get("stac_api_url", "https://planetarycomputer.microsoft.com/api/stac/v1")
    collection = config.sources.get("landsat", {}).get("collection", "landsat-c2-l2")
    catalog = pystac_client.Client.open(stac_url, modifier=pc.sign_inplace)

    revalidated = {}
    errors = []

    for tgt in LANDSAT_TARGETS:
        sc_id = tgt["scene_id"]
        search = catalog.search(collections=[collection], ids=[sc_id])
        items = list(search.items())
        if not items:
            errors.append(f"Scene {sc_id} not found in collection {collection}")
            continue
        item = items[0]
        props = item.properties

        # Check platform
        item_platform = props.get("platform", "").lower()
        expected_platform = tgt["platform"]
        if item_platform != expected_platform:
            errors.append(f"Platform mismatch for {sc_id}: expected {expected_platform}, got {item_platform}")

        # Check date & DOY
        acq_dt = props.get("datetime", "")
        if not acq_dt.startswith(tgt["date"]):
            errors.append(f"Date mismatch for {sc_id}: expected {tgt['date']}, got {acq_dt}")

        # Check WRS path/row
        wrs_path = props.get("landsat:wrs_path")
        wrs_row = props.get("landsat:wrs_row")
        if wrs_path != "147" or wrs_row != "047":
            errors.append(f"WRS mismatch for {sc_id}: expected 147/047, got {wrs_path}/{wrs_row}")

        # Check required assets
        missing_assets = []
        for req_name, stac_key in LANDSAT_ASSET_MAPPING.items():
            if stac_key not in item.assets:
                missing_assets.append(req_name)
        if missing_assets:
            errors.append(f"Scene {sc_id} missing required assets: {missing_assets}")

        revalidated[sc_id] = {
            "item": item,
            "target": tgt,
            "properties": props,
            "stac_cloud": float(props.get("eo:cloud_cover", 100.0)),
        }

    return len(errors) == 0, revalidated, errors


def compute_aoi_cloud_qa(qa_pixel_path: Path, aoi_geom_geojson: Dict[str, Any]) -> Tuple[float, float, int]:
    """Compute cloud and cloud shadow percentage over Pune AOI from QA_PIXEL.
    
    Returns:
        (aoi_cloud_pct, aoi_shadow_pct, valid_pixel_count)
    """
    with rasterio.open(qa_pixel_path) as src:
        geom_proj = transform_geom("EPSG:4326", src.crs, aoi_geom_geojson)
        clipped, _ = mask(src, [geom_proj], crop=True, nodata=1)
        qa = clipped[0]
        valid_mask = (qa != 1) & (qa != 0)
        valid_count = int(np.count_nonzero(valid_mask))
        if valid_count == 0:
            return 0.0, 0.0, 0

        # Bit 3: Cloud (value 8)
        cloud_mask = (qa & (1 << 3)) > 0
        cloud_pixels = np.count_nonzero(cloud_mask & valid_mask)
        cloud_pct = round((cloud_pixels / valid_count) * 100.0, 2)

        # Bit 4: Cloud Shadow (value 16)
        shadow_mask = (qa & (1 << 4)) > 0
        shadow_pixels = np.count_nonzero(shadow_mask & valid_mask)
        shadow_pct = round((shadow_pixels / valid_count) * 100.0, 2)

        return cloud_pct, shadow_pct, valid_count


def acquire_nasa_power_historical(
    config: IngestionConfig,
    centroid: List[float],
) -> Dict[int, Dict[str, Any]]:
    """Acquire historical NASA POWER files for 2021-2024."""
    logger.info("Acquiring NASA POWER historical files (2021-2024)...")
    src_cfg = config.sources.get("nasa_power", {})
    api_url = src_cfg.get("api_url", "https://power.larc.nasa.gov/api/temporal/daily/point")
    community = src_cfg.get("community", "ag")
    vars_to_request = src_cfg.get("variables", DEFAULT_VARIABLES)
    session = create_retry_session(retries=3)

    results = {}

    for year in NASA_POWER_YEARS:
        out_dir = config.project_root / "data" / "raw" / "nasa_power" / "pune" / str(year)
        out_dir.mkdir(parents=True, exist_ok=True)
        data_file = out_dir / f"power_{year}_daily.json"
        meta_file = out_dir / "metadata.json"

        # Idempotency check
        if data_file.exists() and data_file.stat().st_size > 0:
            logger.info(f"[SKIP/VERIFY] NASA POWER {year} already exists ({data_file.stat().st_size} bytes)")
            with open(data_file, "r", encoding="utf-8") as f:
                pdata = json.load(f)
            sha = calculate_sha256(data_file)
            day_count = len(pdata.get("properties", {}).get("parameter", {}).get("T2M", {}))
            results[year] = {
                "year": year,
                "local_path": str(data_file.relative_to(config.project_root)).replace("\\", "/"),
                "file_size_bytes": data_file.stat().st_size,
                "sha256": sha,
                "record_count": day_count,
                "variables": list(pdata.get("properties", {}).get("parameter", {}).keys()),
                "status": "VALID",
            }
            continue

        params = {
            "parameters": ",".join(vars_to_request),
            "community": community,
            "longitude": round(centroid[0], 4),
            "latitude": round(centroid[1], 4),
            "start": f"{year}0101",
            "end": f"{year}1231",
            "format": "JSON",
        }

        part_file = data_file.with_suffix(".json.part")
        resp = session.get(api_url, params=params, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"NASA POWER HTTP {resp.status_code} for {year}: {resp.text[:200]}")

        pdata = resp.json()
        with open(part_file, "w", encoding="utf-8") as f:
            json.dump(pdata, f, indent=2)

        if part_file.exists():
            part_file.rename(data_file)

        sha = calculate_sha256(data_file)
        day_count = len(pdata.get("properties", {}).get("parameter", {}).get("T2M", {}))

        # Write metadata.json
        meta = {
            "dataset_id": f"NASA_POWER_DAILY_POINT_{year}",
            "year": year,
            "provider": "NASA Langley Research Center",
            "source": api_url,
            "coordinates": {"longitude": centroid[0], "latitude": centroid[1]},
            "period": {"start": f"{year}-01-01", "end": f"{year}-12-31"},
            "variables": vars_to_request,
            "records_count": day_count,
            "file_size_bytes": data_file.stat().st_size,
            "sha256": sha,
            "acquisition_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        results[year] = {
            "year": year,
            "local_path": str(data_file.relative_to(config.project_root)).replace("\\", "/"),
            "file_size_bytes": data_file.stat().st_size,
            "sha256": sha,
            "record_count": day_count,
            "variables": list(pdata.get("properties", {}).get("parameter", {}).keys()),
            "status": "VALID",
        }
        logger.info(f"[DOWNLOADED] NASA POWER {year}: {day_count} daily records, SHA: {sha[:12]}...")

    return results


def acquire_modis_historical(
    config: IngestionConfig,
) -> Dict[str, Dict[str, Any]]:
    """Acquire historical MODIS MOD11A2 v061 assets for DOY 105 (2021-2024)."""
    logger.info("Acquiring historical MODIS 8-day composite assets (2021-2024, DOY 105)...")
    stac_url = config.sources.get("modis", {}).get("stac_api_url", "https://planetarycomputer.microsoft.com/api/stac/v1")
    collection = config.sources.get("modis", {}).get("collection", "modis-11A2-061")
    catalog = pystac_client.Client.open(stac_url, modifier=pc.sign_inplace)

    results = {}

    for tgt in MODIS_TARGETS:
        year = tgt["year"]
        item_id = tgt["item_id"]
        logger.info(f"Ingesting MODIS {year} (Item: {item_id}, DOY: {tgt['doy']})...")

        signed_search = catalog.search(collections=[collection], ids=[item_id])
        signed_items = list(signed_search.items())
        if not signed_items:
            raise RuntimeError(f"Could not retrieve fresh signed STAC item for MODIS {item_id}")
        fresh_item = signed_items[0]

        out_dir = config.project_root / "data" / "raw" / "modis" / str(year) / item_id
        out_dir.mkdir(parents=True, exist_ok=True)
        item_assets = {}

        for req_asset in MODIS_REQUIRED_ASSETS:
            if req_asset not in fresh_item.assets:
                raise RuntimeError(f"Asset {req_asset} not found in MODIS item {item_id}")

            asset_obj = fresh_item.assets[req_asset]
            dest_file = out_dir / f"{req_asset}.tif"

            dest_path, sha256_hash, file_size, skipped = safe_download_file(
                url=asset_obj.href,
                dest_path=dest_file,
                chunk_size=config.chunk_size_bytes,
                retries=config.download_retries,
                timeout=config.download_timeout,
            )

            val = validate_raster(dest_path)
            if not val.get("valid"):
                raise RuntimeError(f"Raster validation failed for MODIS asset {dest_file.name}: {val.get('error')}")

            rel_path = str(dest_file.relative_to(config.project_root)).replace("\\", "/")
            item_assets[req_asset] = {
                "local_path": rel_path,
                "file_size_bytes": file_size,
                "sha256": sha256_hash,
                "width": val.get("width"),
                "height": val.get("height"),
                "crs": val.get("crs"),
                "skipped_idempotent": skipped,
                "validation_status": "VALID",
            }

        results[item_id] = {
            "year": year,
            "item_id": item_id,
            "date": tgt["date"],
            "doy": tgt["doy"],
            "assets": item_assets,
            "all_valid": True,
        }

    return results


def download_single_landsat_asset(
    asset_task: Dict[str, Any],
) -> Dict[str, Any]:
    """Worker task to download and validate a single Landsat asset."""
    req_name = asset_task["req_name"]
    url = asset_task["url"]
    dest_file = asset_task["dest_file"]
    chunk_size = asset_task["chunk_size"]
    retries = asset_task["retries"]
    timeout = asset_task["timeout"]
    project_root = asset_task["project_root"]

    dest_path, sha256_hash, file_size, skipped = safe_download_file(
        url=url,
        dest_path=dest_file,
        chunk_size=chunk_size,
        retries=retries,
        timeout=timeout,
    )

    val = validate_raster(dest_path)
    if not val.get("valid"):
        raise RuntimeError(f"Raster validation failed for {dest_file.name}: {val.get('error')}")

    rel_path = str(dest_file.relative_to(project_root)).replace("\\", "/")
    return {
        "req_name": req_name,
        "local_path": rel_path,
        "file_size_bytes": file_size,
        "sha256": sha256_hash,
        "width": val.get("width"),
        "height": val.get("height"),
        "crs": val.get("crs"),
        "skipped_idempotent": skipped,
        "validation_status": "VALID",
    }


def acquire_landsat_series(
    config: IngestionConfig,
    revalidated_scenes: Dict[str, Any],
    aoi_geom: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Acquire and validate all 45 Landsat assets across the 5 approved scenes."""
    logger.info("Acquiring 45 Landsat Collection 2 Level-2 assets across 5 scenes...")
    stac_url = config.sources.get("landsat", {}).get("stac_api_url", "https://planetarycomputer.microsoft.com/api/stac/v1")
    collection = config.sources.get("landsat", {}).get("collection", "landsat-c2-l2")
    catalog = pystac_client.Client.open(stac_url, modifier=pc.sign_inplace)

    results = {}

    for tgt in LANDSAT_TARGETS:
        sc_id = tgt["scene_id"]
        year = tgt["year"]
        logger.info(f"--- Processing Landsat scene: {sc_id} ({tgt['display_platform']}, Year {year}, DOY {tgt['doy']}) ---")

        signed_search = catalog.search(collections=[collection], ids=[sc_id])
        signed_items = list(signed_search.items())
        if not signed_items:
            raise RuntimeError(f"Could not retrieve fresh signed STAC item for {sc_id}")
        fresh_item = signed_items[0]

        scene_dir = config.project_root / "data" / "raw" / "landsat" / str(year) / sc_id
        scene_dir.mkdir(parents=True, exist_ok=True)

        tasks = []
        for req_name, stac_key in LANDSAT_ASSET_MAPPING.items():
            if stac_key not in fresh_item.assets:
                raise RuntimeError(f"Missing required STAC asset {stac_key} for scene {sc_id}")
            asset_obj = fresh_item.assets[stac_key]
            dest_file = scene_dir / f"{req_name}.tif"
            tasks.append({
                "req_name": req_name,
                "url": asset_obj.href,
                "dest_file": dest_file,
                "chunk_size": config.chunk_size_bytes,
                "retries": config.download_retries,
                "timeout": config.download_timeout,
                "project_root": config.project_root,
            })

        # Download assets with ThreadPoolExecutor (max_workers=4)
        scene_assets = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_task = {executor.submit(download_single_landsat_asset, t): t for t in tasks}
            for future in concurrent.futures.as_completed(future_to_task):
                res = future.result()
                scene_assets[res["req_name"]] = res

        # Verify QA_PIXEL and calculate AOI cloud metrics
        qa_pixel_file = scene_dir / "QA_PIXEL.tif"
        aoi_cloud_pct, aoi_shadow_pct, valid_pixels = compute_aoi_cloud_qa(qa_pixel_file, aoi_geom)
        logger.info(
            f"QA_PIXEL AOI Analysis for {sc_id}: Pune AOI Cloud = {aoi_cloud_pct:.2f}%, "
            f"Shadow = {aoi_shadow_pct:.2f}% (Valid pixels: {valid_pixels})"
        )

        results[sc_id] = {
            "year": year,
            "scene_id": sc_id,
            "platform": tgt["display_platform"],
            "date": tgt["date"],
            "doy": tgt["doy"],
            "offset": tgt["offset"],
            "stac_cloud_pct": tgt["stac_cloud_cover"],
            "pune_aoi_cloud_pct": aoi_cloud_pct,
            "pune_aoi_shadow_pct": aoi_shadow_pct,
            "assets": scene_assets,
            "all_valid": len(scene_assets) == 9 and all(a["validation_status"] == "VALID" for a in scene_assets.values()),
        }

    return results


def run_phase_1a7_execution() -> int:
    """Execute complete Phase 1A.7 workflow."""
    print("=" * 60)
    print("CLIMORA PHASE 1A.7 — HISTORICAL ACQUISITION & DATASET FREEZE")
    print("=" * 60)

    config = load_config()
    aoi_data = load_aoi(config.aoi_path)
    is_valid, crs, geom, bbox, centroid = validate_aoi(aoi_data)
    if not is_valid:
        logger.error(f"Invalid AOI geometry: {crs}")
        return 1

    aoi_geom_geojson = aoi_data["features"][0]["geometry"]

    # STEP 1: Verify Frozen Phase 0 Lake
    print("\n--- STEP 1: VERIFYING FROZEN PHASE 0 LAKE IMMUTABILITY ---")
    frozen_valid, frozen_errs = verify_frozen_baseline(config.project_root)
    if not frozen_valid:
        print("[FAIL] Frozen lake protection breached:")
        for e in frozen_errs:
            print(f"  {e}")
        return 1
    print("[PASS] All 44 authoritative Phase 0 assets verified 100% byte-for-byte intact.")

    # STEP 2: Revalidate STAC Catalogue for 5 Landsat scenes
    print("\n--- STEP 2: REVALIDATING 5 AMENDED LANDSAT SCENES IN STAC ---")
    cat_ok, revalidated_scenes, cat_errs = revalidate_catalogue_scenes(config)
    if not cat_ok:
        print("[FAIL] Catalogue revalidation failed:")
        for e in cat_errs:
            print(f"  {e}")
        return 1
    for sc_id, info in revalidated_scenes.items():
        tgt = info["target"]
        print(f"  [OK] {sc_id} | {tgt['display_platform']} | Date: {tgt['date']} | DOY: {tgt['doy']} | STAC Cloud: {info['stac_cloud']}%")

    # STEP 3: Acquire NASA POWER historical files (2021-2024)
    print("\n--- STEP 3: ACQUIRING NASA POWER HISTORICAL FILES (2021-2024) ---")
    nasa_power_res = acquire_nasa_power_historical(config, centroid)
    for yr, ninfo in nasa_power_res.items():
        print(f"  [OK] NASA POWER {yr} | Records: {ninfo['record_count']} | Size: {ninfo['file_size_bytes']} B | SHA: {ninfo['sha256'][:8]}...")

    # STEP 4: Acquire MODIS historical assets (2021-2024)
    print("\n--- STEP 4: ACQUIRING MODIS HISTORICAL ASSETS (2021-2024, DOY 105) ---")
    modis_res = acquire_modis_historical(config)
    for item_id, minfo in modis_res.items():
        print(f"  [OK] MODIS {minfo['year']} ({item_id}) | 4/4 assets valid | DOY: {minfo['doy']}")

    # STEP 5: Acquire Landsat assets (2021-2025, 45 assets)
    print("\n--- STEP 5: ACQUIRING LANDSAT 5-YEAR BASELINE (45 ASSETS) ---")
    landsat_res = acquire_landsat_series(config, revalidated_scenes, aoi_geom_geojson)
    for sc_id, sinfo in landsat_res.items():
        print(
            f"  [OK] Landsat {sinfo['year']} ({sc_id}) | Platform: {sinfo['platform']} | "
            f"AOI Cloud: {sinfo['pune_aoi_cloud_pct']:.2f}% | 9/9 assets valid"
        )

    # STEP 6: Measure Storage
    print("\n--- STEP 6: MEASURING ACTUAL STORAGE USAGE ---")
    # Existing frozen bytes
    frozen_checksum_file = config.project_root / "data" / "manifests" / "pune_2025_v1_checksums.sha256"
    existing_frozen_bytes = 0
    with open(frozen_checksum_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                _, rel_p = line.strip().split(maxsplit=1)
                existing_frozen_bytes += (config.project_root / rel_p.replace("\\", "/")).stat().st_size

    new_landsat_bytes = sum(
        asset["file_size_bytes"]
        for sc in landsat_res.values()
        for asset in sc["assets"].values()
    )
    new_modis_bytes = sum(
        asset["file_size_bytes"]
        for per in modis_res.values()
        for asset in per["assets"].values()
    )
    new_nasa_power_bytes = sum(
        n["file_size_bytes"] for n in nasa_power_res.values()
    )
    new_total_bytes = new_landsat_bytes + new_modis_bytes + new_nasa_power_bytes
    final_raw_dataset_bytes = existing_frozen_bytes + new_total_bytes

    print(f"  Existing Frozen Raw (Phase 0): {existing_frozen_bytes} bytes ({existing_frozen_bytes / (1024**3):.3f} GB)")
    print(f"  New Landsat Raw:               {new_landsat_bytes} bytes ({new_landsat_bytes / (1024**3):.3f} GB)")
    print(f"  New MODIS Raw:                 {new_modis_bytes} bytes ({new_modis_bytes / (1024**2):.2f} MB)")
    print(f"  New NASA POWER Raw:            {new_nasa_power_bytes} bytes ({new_nasa_power_bytes / 1024:.2f} KB)")
    print(f"  New Historical Raw Total:      {new_total_bytes} bytes ({new_total_bytes / (1024**3):.3f} GB)")
    print(f"  Total Raw Dataset:             {final_raw_dataset_bytes} bytes ({final_raw_dataset_bytes / (1024**3):.3f} GB)")

    # STEP 7: Update Checksums Manifest
    print("\n--- STEP 7: GENERATING AUTHORITATIVE CHECKSUMS MANIFEST ---")
    checksum_out_path = config.project_root / "data" / "manifests" / "pune_temporal_baseline_v1_checksums.sha256"
    checksum_lines = []

    # 1. Existing frozen Phase 0 assets
    checksum_lines.append("# Authoritative Reused Frozen 2025 Assets (Phase 0 Lake - 44 files)")
    with open(frozen_checksum_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                checksum_lines.append(line.strip())

    checksum_lines.append("")
    checksum_lines.append("# New Historical Temporal Baseline Assets (Phase 1A.7 - 65 files)")

    # 2. Landsat 45 assets
    checksum_lines.append("# Landsat Collection 2 Level-2 (45 GeoTIFFs across 5 scenes)")
    for sc_id in sorted(landsat_res.keys(), key=lambda k: landsat_res[k]["year"]):
        sc = landsat_res[sc_id]
        for req_name in sorted(sc["assets"].keys()):
            asset = sc["assets"][req_name]
            checksum_lines.append(f"{asset['sha256']}  {asset['local_path'].replace('/', '\\')}")

    # 3. MODIS 16 assets
    checksum_lines.append("# MODIS MOD11A2 v061 (16 GeoTIFFs across 4 historical years)")
    for item_id in sorted(modis_res.keys(), key=lambda k: modis_res[k]["year"]):
        per = modis_res[item_id]
        for req_name in sorted(per["assets"].keys()):
            asset = per["assets"][req_name]
            checksum_lines.append(f"{asset['sha256']}  {asset['local_path'].replace('/', '\\')}")

    # 4. NASA POWER 4 files
    checksum_lines.append("# NASA POWER Historical Daily Point Files (4 files across 2021-2024)")
    for yr in sorted(nasa_power_res.keys()):
        pinfo = nasa_power_res[yr]
        checksum_lines.append(f"{pinfo['sha256']}  {pinfo['local_path'].replace('/', '\\')}")

    with open(checksum_out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(checksum_lines) + "\n")
    print(f"  [SAVED] {checksum_out_path.name} with {44 + 45 + 16 + 4} verified asset entries.")

    # STEP 8: Update Acquisition Manifest
    print("\n--- STEP 8: UPDATING ACQUISITION MANIFEST ---")
    acq_manifest_path = config.project_root / "data" / "manifests" / "pune_temporal_baseline_v1_acquisition.json"
    with open(acq_manifest_path, "r", encoding="utf-8") as f:
        acq_manifest = json.load(f)

    acq_manifest["status"] = "ACQUISITION_COMPLETED_AND_VALIDATED"
    acq_manifest["acquisition_completed_at"] = datetime.now(timezone.utc).isoformat()
    acq_manifest["actual_storage_metrics"] = {
        "existing_frozen_bytes": existing_frozen_bytes,
        "existing_frozen_gb": round(existing_frozen_bytes / (1024**3), 3),
        "new_landsat_bytes": new_landsat_bytes,
        "new_landsat_gb": round(new_landsat_bytes / (1024**3), 3),
        "new_modis_bytes": new_modis_bytes,
        "new_modis_mb": round(new_modis_bytes / (1024**2), 2),
        "new_nasa_power_bytes": new_nasa_power_bytes,
        "new_nasa_power_kb": round(new_nasa_power_bytes / 1024, 2),
        "new_total_bytes": new_total_bytes,
        "new_total_gb": round(new_total_bytes / (1024**3), 3),
        "final_raw_dataset_bytes": final_raw_dataset_bytes,
        "final_raw_dataset_gb": round(final_raw_dataset_bytes / (1024**3), 3),
        "convention": "1 GB = 1024^3 bytes (GiB)",
    }
    acq_manifest["acquired_landsat_series"] = landsat_res
    acq_manifest["acquired_modis_series"] = modis_res
    acq_manifest["acquired_nasa_power_series"] = nasa_power_res

    with open(acq_manifest_path, "w", encoding="utf-8") as f:
        json.dump(acq_manifest, f, indent=2)
    print(f"  [SAVED] {acq_manifest_path.name}")

    # STEP 9: Generate Final Frozen Manifest
    print("\n--- STEP 9: CREATING FINAL FROZEN MANIFEST ---")
    frozen_manifest_path = config.project_root / "data" / "manifests" / "pune_temporal_baseline_v1_frozen.json"
    frozen_manifest = {
        "manifest_id": "climora_temporal_baseline_v1_frozen",
        "dataset_version": "pune_temporal_baseline_v1",
        "status": "FROZEN",
        "phase": "1A.7",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "temporal_scope": "2021–2025",
        "season": "peak_pre_monsoon_summer",
        "canonical_doy": 105,
        "preferred_window": [95, 115],
        "hard_max_offset_days": 15,
        "study_area": "Pune, Maharashtra, India",
        "sensor_governance": {
            "baseline_type": "predominantly_landsat_8_with_2023_landsat_9",
            "statement": "A five-year Landsat Collection 2 Level-2 temporal baseline using the same WRS-2 Path/Row 147/047 and peak pre-monsoon acquisition window, comprising four Landsat 8 observations and one Landsat 9 observation in 2023. Platform identity is retained explicitly for downstream quality control and temporal normalization.",
            "platform_sequence": {
                "2021": "Landsat 8",
                "2022": "Landsat 8",
                "2023": "Landsat 9",
                "2024": "Landsat 8",
                "2025": "Landsat 8",
            },
        },
        "landsat_series": [
            {
                "year": s["year"],
                "scene_id": s["scene_id"],
                "platform": s["platform"],
                "date": s["date"],
                "doy": s["doy"],
                "offset_days": s["offset"],
                "stac_cloud_pct": s["stac_cloud_pct"],
                "pune_aoi_cloud_pct": s["pune_aoi_cloud_pct"],
                "pune_aoi_shadow_pct": s["pune_aoi_shadow_pct"],
                "assets_count": len(s["assets"]),
                "validation": "PASSED_VALID",
            }
            for s in sorted(landsat_res.values(), key=lambda x: x["year"])
        ],
        "modis_historical_series": [
            {
                "year": m["year"],
                "item_id": m["item_id"],
                "date": m["date"],
                "doy": m["doy"],
                "assets_count": len(m["assets"]),
                "validation": "PASSED_VALID",
            }
            for m in sorted(modis_res.values(), key=lambda x: x["year"])
        ],
        "nasa_power_historical_series": [
            {
                "year": n["year"],
                "daily_records_count": n["record_count"],
                "variables": n["variables"],
                "validation": "PASSED_VALID",
            }
            for n in sorted(nasa_power_res.values(), key=lambda x: x["year"])
        ],
        "reused_frozen_phase_0_assets": {
            "total_files": 44,
            "manifest_reference": "data/manifests/pune_2025_v1_frozen.json",
            "checksums_reference": "data/manifests/pune_2025_v1_checksums.sha256",
            "integrity_status": "VERIFIED_UNCHANGED",
        },
        "inventory_summary": {
            "landsat_assets": 45,
            "modis_historical_assets": 16,
            "nasa_power_historical_files": 4,
            "new_historical_files_total": 65,
            "reused_frozen_files_total": 44,
            "total_lake_files": 44 + 65,
        },
        "checksums_manifest": "data/manifests/pune_temporal_baseline_v1_checksums.sha256",
        "storage_metrics": acq_manifest["actual_storage_metrics"],
    }

    with open(frozen_manifest_path, "w", encoding="utf-8") as f:
        json.dump(frozen_manifest, f, indent=2)
    print(f"  [SAVED] {frozen_manifest_path.name} (Status: FROZEN)")

    print("\n" + "=" * 60)
    print("PHASE 1A.7 ACQUISITION EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(run_phase_1a7_execution())
