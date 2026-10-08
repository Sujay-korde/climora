"""CLIMORA Unified Ingestion Command Line Interface.

Provides CLI subcommands:
- search: Discover candidate scenes and assets across STAC / APIs without downloading.
- estimate: Calculate storage requirements for selected candidates before downloading.
- download: Ingest approved candidate assets idempotently with storage threshold guard.
- validate: Run spatial, raster, vector, and checksum validation on local lake.
- status: Report overall acquisition status, integrity, and local storage usage.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ingestion.common import (
    calculate_sha256,
    get_logger,
    load_aoi,
    load_manifest,
    save_manifest,
    validate_aoi,
    validate_raster,
    validate_vector,
)
from ingestion.config import IngestionConfig, load_config
from ingestion.dem import download_dem, search_dem
from ingestion.landsat import (
    LANDSAT_ASSET_MAPPING,
    LANDSAT_ESTIMATED_ASSET_SIZES,
    LANDSAT_ESTIMATED_SCENE_SIZE,
    download_landsat,
    search_landsat,
)
from ingestion.modis import (
    MODIS_ESTIMATED_ASSET_SIZES,
    MODIS_ESTIMATED_PERIOD_SIZE,
    MODIS_REQUIRED_ASSETS,
    download_modis,
    search_modis,
)
from ingestion.nasa_power import acquire_nasa_power
from ingestion.osm import acquire_osm
from ingestion.sentinel2 import (
    SENTINEL2_BAND_MAPPING,
    SENTINEL2_ESTIMATED_BAND_SIZES,
    SENTINEL2_ESTIMATED_PRODUCT_SIZE,
    download_sentinel2,
    search_sentinel2,
)

logger = get_logger()


def format_bytes(size: int | float) -> str:
    """Format bytes into human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size) < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def get_lake_files(raw_dir: Path) -> List[Path]:
    """Return all non-temporary files in local raw data lake."""
    if not raw_dir.exists():
        return []
    return [f for f in raw_dir.rglob("*") if f.is_file() and not f.name.endswith(".part") and not f.name.endswith(".tmp")]


def cmd_search(config: IngestionConfig, source: Optional[str] = None, year: Optional[int] = None) -> int:
    """Execute search across catalogues without downloading."""
    if year:
        config.year = year
        config.start_date = f"{year}-01-01"
        config.end_date = f"{year}-12-31"

    # Validate AOI first
    aoi_data = load_aoi(config.aoi_path)
    is_valid, crs, geom, bbox, centroid = validate_aoi(aoi_data)
    if not is_valid:
        logger.error(f"Invalid AOI geometry: {crs}")
        return 1

    sources_to_search = [source.lower()] if source else ["landsat", "sentinel2", "modis", "nasa_power", "osm", "dem"]

    # Load existing manifest to preserve historical acquisitions
    manifest_path = config.get_manifest_path()
    existing_manifest = load_manifest(manifest_path)
    existing_acquisitions = existing_manifest.get("acquisitions", {})

    plan: Dict[str, Any] = {
        "title": "CLIMORA Pune Data Acquisition Plan",
        "study_area": "Pune, Maharashtra, India",
        "period": {"start": config.start_date, "end": config.end_date},
        "aoi": {
            "path": str(config.aoi_path.relative_to(config.project_root)),
            "crs": crs,
            "bbox": bbox,
            "centroid": centroid,
        },
        "selection_policy": {
            "strategy": config.selection_strategy,
            "target_per_season": config.target_per_season,
            "storage_threshold_gb": config.storage_warning_threshold_gb,
            "seasons": config.seasons,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": existing_manifest.get("sources", {}),
        "acquisitions": existing_acquisitions,
    }

    print("\n" + "=" * 60)
    print("CLIMORA DATA ACQUISITION CANDIDATE SEARCH & SELECTION")
    print("=" * 60)
    print(f"Study area:\n  Pune, Maharashtra, India")
    print(f"Period:\n  {config.start_date} -> {config.end_date}")
    print(f"AOI Bbox:\n  {bbox}\n")

    # 1. Landsat
    if "landsat" in sources_to_search:
        l_res = search_landsat(config, bbox)
        plan["sources"]["landsat"] = l_res
        print("LANDSAT (Collection 2 Level-2)")
        print(f"  Candidate scenes in {config.year}: {l_res['total_candidates']}")
        print(f"  Passed quality & cloud filter (<= {config.sources['landsat']['cloud_cover_max']}%): {l_res['filtered_candidates_count']}")
        print(f"  Deterministically selected across seasons: {l_res['selected_candidates_count']}")
        for sc in l_res["selected_scenes"]:
            sm = sc.get("selection_metadata", {})
            print(f"    - [{sm.get('season_name', 'Season')}] {sc['id']} (Date: {sc['date'][:10]}, Cloud: {sc['cloud_cover']}%, Bootstrap Preserved: {sm.get('is_existing_bootstrap')})")
        print(f"  Required assets: {', '.join(l_res['required_assets'])}")
        print()

    # 2. Sentinel-2
    if "sentinel2" in sources_to_search:
        s2_res = search_sentinel2(config, bbox)
        plan["sources"]["sentinel2"] = s2_res
        print("SENTINEL-2 (MSI Level-2A)")
        print(f"  Candidate products in {config.year}: {s2_res['total_candidates']}")
        print(f"  Passed quality & cloud filter (<= {config.sources['sentinel2']['cloud_cover_max']}%): {s2_res['filtered_candidates_count']}")
        print(f"  Deterministically selected across seasons: {s2_res['selected_candidates_count']}")
        for pr in s2_res["selected_products"]:
            sm = pr.get("selection_metadata", {})
            print(f"    - [{sm.get('season_name', 'Season')}] {pr['id']} (Date: {pr['date'][:10]}, Cloud: {pr['cloud_cover']}%, Bootstrap Preserved: {sm.get('is_existing_bootstrap')})")
        print(f"  Required bands: {', '.join(s2_res['required_bands'])}")
        print()

    # 3. MODIS
    if "modis" in sources_to_search:
        m_res = search_modis(config, bbox)
        plan["sources"]["modis"] = m_res
        print("MODIS (MOD11A2 Version 6.1)")
        print(f"  Target tile: {m_res['tile']} (~1 km SIN Grid)")
        print(f"  Temporal cadence: 8-day composite")
        print(f"  Candidate 8-day periods in {config.year}: {m_res['total_periods']}")
        print(f"  Selected periods for temporal representation: {m_res['selected_periods_count']}")
        print(f"  Required assets: {', '.join(m_res['required_assets'])}")
        print()

    # 4. NASA POWER
    if "nasa_power" in sources_to_search:
        p_cfg = config.sources.get("nasa_power", {})
        vars_req = p_cfg.get("variables", [])
        plan["sources"]["nasa_power"] = {
            "dataset": "NASA_POWER_DAILY_POINT",
            "provider": "NASA Langley Research Center",
            "api_endpoint": p_cfg.get("api_url"),
            "coordinates": {"latitude": centroid[1], "longitude": centroid[0]},
            "period": {"start": config.start_date, "end": config.end_date},
            "requested_variables": vars_req,
        }
        print("NASA POWER (Daily Surface Meteorology)")
        print(f"  Centroid: lat {round(centroid[1], 4)}, lon {round(centroid[0], 4)}")
        print(f"  Period: {config.start_date} -> {config.end_date}")
        print(f"  Requested variables: {', '.join(vars_req)}")
        print()

    # 5. OpenStreetMap
    if "osm" in sources_to_search:
        o_cfg = config.sources.get("osm", {})
        plan["sources"]["osm"] = {
            "dataset": "OpenStreetMap_Pune_Extracts",
            "provider": "OpenStreetMap Contributors / Overpass API",
            "aoi_bbox": bbox,
            "feature_categories": ["green_spaces", "water_bodies", "public_infrastructure", "road_network"],
        }
        print("OPENSTREETMAP (Pune AOI Extract)")
        print("  Requested feature categories: green_spaces, water_bodies, public_infrastructure, road_network")
        print()

    # 6. DEM
    if "dem" in sources_to_search:
        d_res = search_dem(config, bbox)
        plan["sources"]["dem"] = d_res
        print("DEM (Copernicus DEM GLO-30)")
        print(f"  Required tiles: {', '.join(d_res['required_tiles'])}")
        print(f"  Resolution: 30m Cloud-Optimized GeoTIFF")
        print()

    print("=" * 60)
    print("SEARCH COMPLETED. No files were downloaded during this search.")
    print("=" * 60)

    save_manifest(manifest_path, plan)
    logger.info(f"Saved candidate discovery & selection plan to {manifest_path.name}")
    return 0


def cmd_estimate(config: IngestionConfig, year: Optional[int] = None, source: Optional[str] = None) -> int:
    """Calculate storage requirements for candidate dataset without downloading."""
    if year:
        config.year = year
        config.start_date = f"{year}-01-01"
        config.end_date = f"{year}-12-31"

    manifest_path = config.get_manifest_path()
    plan = load_manifest(manifest_path)
    if not plan or "sources" not in plan:
        logger.info("Acquisition plan not found. Performing candidate discovery first...")
        cmd_search(config, source=source, year=year)
        plan = load_manifest(manifest_path)

    sources_plan = plan.get("sources", {})

    print("\n" + "=" * 60)
    print("CLIMORA STORAGE ESTIMATION REPORT")
    print(f"Study Area: {config.study_area} | Year: {config.year}")
    print("=" * 60)

    # 1. Landsat estimation
    l_plan = sources_plan.get("landsat", {})
    l_selected = l_plan.get("selected_scenes") or l_plan.get("scenes", [])
    l_req_assets = l_plan.get("required_assets", list(LANDSAT_ASSET_MAPPING.keys()))
    l_local_bytes = 0
    l_new_bytes = 0
    l_cand_count = l_plan.get("total_candidates", 0)

    for sc in l_selected:
        sc_id = sc["id"]
        sc_dir = config.raw_dir / "landsat" / str(config.year) / sc_id
        for asset_name in l_req_assets:
            fpath = sc_dir / f"{asset_name}.tif"
            if fpath.exists() and fpath.is_file():
                l_local_bytes += fpath.stat().st_size
            else:
                l_new_bytes += LANDSAT_ESTIMATED_ASSET_SIZES.get(asset_name, 88_000_000)

    l_est_total = l_local_bytes + l_new_bytes
    print("LANDSAT (Collection 2 Level-2)")
    print(f"  Candidates:       {l_cand_count}")
    print(f"  Selected:         {len(l_selected)}")
    print(f"  Required assets:  {len(l_req_assets)} ({', '.join(l_req_assets)})")
    print(f"  Already Local:    {format_bytes(l_local_bytes)}")
    print(f"  New to Download:  {format_bytes(l_new_bytes)}")
    print(f"  Estimated Total:  {format_bytes(l_est_total)}")
    print()

    # 2. Sentinel-2 estimation
    s2_plan = sources_plan.get("sentinel2", {})
    s2_selected = s2_plan.get("selected_products") or s2_plan.get("products", [])
    s2_req_bands = s2_plan.get("required_bands", list(SENTINEL2_BAND_MAPPING.keys()))
    s2_local_bytes = 0
    s2_new_bytes = 0
    s2_cand_count = s2_plan.get("total_candidates", 0)

    for pr in s2_selected:
        pr_id = pr["id"]
        pr_dir = config.raw_dir / "sentinel2" / str(config.year) / pr_id
        for band_name in s2_req_bands:
            fpath = pr_dir / f"{band_name}.tif"
            if fpath.exists() and fpath.is_file():
                s2_local_bytes += fpath.stat().st_size
            else:
                s2_new_bytes += SENTINEL2_ESTIMATED_BAND_SIZES.get(band_name, 50_000_000)

    s2_est_total = s2_local_bytes + s2_new_bytes
    print("SENTINEL-2 (MSI Level-2A)")
    print(f"  Candidates:       {s2_cand_count}")
    print(f"  Selected:         {len(s2_selected)}")
    print(f"  Required bands:   {len(s2_req_bands)} ({', '.join(s2_req_bands)})")
    print(f"  Already Local:    {format_bytes(s2_local_bytes)}")
    print(f"  New to Download:  {format_bytes(s2_new_bytes)}")
    print(f"  Estimated Total:  {format_bytes(s2_est_total)}")
    print()

    # 3. MODIS estimation
    m_plan = sources_plan.get("modis", {})
    m_selected = m_plan.get("selected_periods") or m_plan.get("periods", [])
    m_req_assets = m_plan.get("required_assets", MODIS_REQUIRED_ASSETS)
    m_local_bytes = 0
    m_new_bytes = 0
    m_total_periods = m_plan.get("total_periods", 0)

    for per in m_selected:
        per_id = per["id"]
        per_dir = config.raw_dir / "modis" / str(config.year) / per_id
        for asset_name in m_req_assets:
            fpath = per_dir / f"{asset_name}.tif"
            if fpath.exists() and fpath.is_file():
                m_local_bytes += fpath.stat().st_size
            else:
                m_new_bytes += MODIS_ESTIMATED_ASSET_SIZES.get(asset_name, 1_000_000)

    m_est_total = m_local_bytes + m_new_bytes
    print("MODIS (MOD11A2 Version 6.1)")
    print(f"  Candidate Periods: {m_total_periods}")
    print(f"  Selected Periods:  {len(m_selected)}")
    print(f"  Required assets:   {len(m_req_assets)} ({', '.join(m_req_assets)})")
    print(f"  Already Local:     {format_bytes(m_local_bytes)}")
    print(f"  New to Download:   {format_bytes(m_new_bytes)}")
    print(f"  Estimated Total:   {format_bytes(m_est_total)}")
    print()

    # 4. NASA POWER estimation
    p_dir = config.raw_dir / "nasa_power" / "pune" / str(config.year)
    p_file = p_dir / f"power_{config.year}_daily.json"
    p_local_bytes = p_file.stat().st_size if p_file.exists() else 0
    p_new_bytes = 0 if p_file.exists() else 75_000
    print("NASA POWER (Daily Surface Meteorology)")
    print(f"  Existing Records:  365 daily observations")
    print(f"  Already Local:     {format_bytes(p_local_bytes)}")
    print(f"  New to Download:   {format_bytes(p_new_bytes)}")
    print()

    # 5. OSM estimation
    o_dir = config.raw_dir / "osm" / "pune"
    o_local_bytes = sum(f.stat().st_size for f in o_dir.glob("*.geojson")) if o_dir.exists() else 0
    o_new_bytes = 0 if o_local_bytes > 0 else 6_000_000
    print("OPENSTREETMAP (Pune AOI Vectors)")
    print(f"  Layers:            4 (green_spaces, water_bodies, public_infrastructure, road_network)")
    print(f"  Already Local:     {format_bytes(o_local_bytes)}")
    print(f"  New to Download:   {format_bytes(o_new_bytes)}")
    print()

    # 6. DEM estimation
    d_dir = config.raw_dir / "dem" / "pune"
    d_local_bytes = sum(f.stat().st_size for f in d_dir.glob("*.tif")) if d_dir.exists() else 0
    d_new_bytes = 0 if d_local_bytes > 0 else 46_000_000
    print("DEM (Copernicus DEM GLO-30)")
    print(f"  Selected Tiles:    1 (Copernicus_DSM_COG_10_N18_00_E073_00_DEM)")
    print(f"  Already Local:     {format_bytes(d_local_bytes)}")
    print(f"  New to Download:   {format_bytes(d_new_bytes)}")
    print()

    # Total Storage Metrics
    current_lake_files = get_lake_files(config.raw_dir)
    current_lake_bytes = sum(f.stat().st_size for f in current_lake_files)
    new_data_bytes = l_new_bytes + s2_new_bytes + m_new_bytes + p_new_bytes + o_new_bytes + d_new_bytes
    projected_total_bytes = current_lake_bytes + new_data_bytes
    threshold_bytes = int(config.storage_warning_threshold_gb * 1024 * 1024 * 1024)

    print("-" * 60)
    print(f"TOTAL ESTIMATED DATA (Selected Set):          {format_bytes(l_est_total + s2_est_total + m_est_total + p_local_bytes + o_local_bytes + d_local_bytes)}")
    print(f"CURRENT LOCAL DATA (Bootstrap Lake):          {format_bytes(current_lake_bytes)}")
    print(f"NEW DATA TO ACQUIRE:                          {format_bytes(new_data_bytes)}")
    print(f"PROJECTED LOCAL DATA AFTER ACQUISITION:       {format_bytes(projected_total_bytes)}")
    print(f"CONFIGURED STORAGE THRESHOLD:                 {config.storage_warning_threshold_gb:.1f} GB ({format_bytes(threshold_bytes)})")
    print("-" * 60)

    if projected_total_bytes > threshold_bytes:
        print("\n[WARNING] Estimated acquisition exceeds configured local threshold.")
        print("Recommendation: Review selection before continuing or adjust storage threshold in config.yaml.")
        print("=" * 60)
        return 1
    else:
        print("[OK] Projected acquisition is well within configured storage limits.")
        print("=" * 60)
        return 0


def cmd_download(
    config: IngestionConfig,
    source: Optional[str] = None,
    limit: Optional[int] = None,
    bands: Optional[str] = None,
    force: bool = False,
) -> int:
    """Execute download of approved assets idempotently with threshold guard."""
    aoi_data = load_aoi(config.aoi_path)
    is_valid, crs, geom, bbox, centroid = validate_aoi(aoi_data)
    if not is_valid:
        logger.error("Invalid AOI geometry")
        return 1

    manifest_path = config.get_manifest_path()
    plan = load_manifest(manifest_path)
    if not plan or "sources" not in plan:
        logger.info("Acquisition plan not found. Running search first to discover candidates...")
        cmd_search(config, source=source)
        plan = load_manifest(manifest_path)

    # Storage threshold check before download (Section 18)
    current_lake_files = get_lake_files(config.raw_dir)
    current_lake_bytes = sum(f.stat().st_size for f in current_lake_files)
    threshold_bytes = int(config.storage_warning_threshold_gb * 1024 * 1024 * 1024)

    if current_lake_bytes > threshold_bytes and not force:
        logger.error(
            f"Estimated acquisition exceeds configured local threshold ({config.storage_warning_threshold_gb} GB). "
            f"Current lake is {format_bytes(current_lake_bytes)}. Review selection before continuing."
        )
        return 1

    sources_to_dl = [source.lower()] if source else ["landsat", "sentinel2", "modis", "nasa_power", "osm", "dem"]
    band_list = [b.strip() for b in bands.split(",")] if bands else None

    acquisitions = plan.get("acquisitions", {})

    print("\n" + "=" * 60)
    print("CLIMORA CONTROLLED LOCAL DATA ACQUISITION")
    print(f"Target Year: {config.year} | Storage Threshold: {config.storage_warning_threshold_gb} GB")
    print("=" * 60)

    # 1. Landsat
    if "landsat" in sources_to_dl and "landsat" in plan.get("sources", {}):
        l_res = plan["sources"]["landsat"]
        l_ingested = download_landsat(config, l_res, limit=limit)
        acquisitions["landsat"] = l_ingested

    # 2. Sentinel-2
    if "sentinel2" in sources_to_dl and "sentinel2" in plan.get("sources", {}):
        s2_res = plan["sources"]["sentinel2"]
        s2_ingested = download_sentinel2(config, s2_res, limit=limit, bands=band_list)
        acquisitions["sentinel2"] = s2_ingested

    # 3. MODIS
    if "modis" in sources_to_dl and "modis" in plan.get("sources", {}):
        m_res = plan["sources"]["modis"]
        m_ingested = download_modis(config, m_res, limit=limit)
        acquisitions["modis"] = m_ingested

    # 4. NASA POWER
    if "nasa_power" in sources_to_dl:
        p_ingested = acquire_nasa_power(config, centroid)
        acquisitions["nasa_power"] = p_ingested

    # 5. OpenStreetMap
    if "osm" in sources_to_dl:
        o_ingested = acquire_osm(config, bbox)
        acquisitions["osm"] = o_ingested

    # 6. DEM
    if "dem" in sources_to_dl and "dem" in plan.get("sources", {}):
        d_res = plan["sources"]["dem"]
        d_ingested = download_dem(config, d_res, limit=limit or 1)
        acquisitions["dem"] = d_ingested

    # Update manifest with acquisitions and lake metrics
    all_lake = get_lake_files(config.raw_dir)
    total_bytes = sum(f.stat().st_size for f in all_lake)

    plan["acquisitions"] = acquisitions
    plan["storage_summary"] = {
        "raw_data_lake_bytes": total_bytes,
        "raw_data_lake_human": format_bytes(total_bytes),
        "total_files": len(all_lake),
        "storage_status": "local",
        "s3_status": "disabled_local_only",
    }
    plan["last_updated_at"] = datetime.now(timezone.utc).isoformat()
    save_manifest(manifest_path, plan)
    logger.info("Updated acquisition manifest with ingestion results and provenance.")

    # Validate immediately
    return cmd_validate(config, source=source)


def cmd_validate(config: IngestionConfig, source: Optional[str] = None) -> int:
    """Validate all downloaded files and data lake integrity."""
    print("\n" + "=" * 60)
    print("CLIMORA DATA LAKE INTEGRITY & VALIDATION REPORT")
    print("=" * 60)

    # Validate AOI
    aoi_data = load_aoi(config.aoi_path)
    is_valid, crs, geom, bbox, centroid = validate_aoi(aoi_data)
    print(f"AOI Validation: {'VALID' if is_valid else 'INVALID'}")
    print(f"  Path: {config.aoi_path.name}")
    print(f"  CRS: {crs}")
    print(f"  Bounding Box: {bbox}")
    print(f"  Centroid: {centroid}\n")

    manifest_path = config.get_manifest_path()
    plan = load_manifest(manifest_path)
    acquisitions = plan.get("acquisitions", {})

    total_files = 0
    valid_files = 0
    failed_files = 0
    total_bytes = 0
    checksum_passed = 0
    checksum_failed = 0
    raster_passed = 0
    raster_failed = 0
    vector_passed = 0
    vector_failed = 0

    sources_to_check = [source.lower()] if source else ["landsat", "sentinel2", "modis", "nasa_power", "osm", "dem"]

    # 1. Landsat validation
    if "landsat" in sources_to_check and "landsat" in acquisitions:
        print("LANDSAT VALIDATION:")
        for sc in acquisitions["landsat"]:
            print(f"  Scene: {sc['scene_id']} (Platform: {sc['platform']}, Date: {sc['observation_date'][:10]})")
            for req_name, asset in sc.get("assets", {}).items():
                total_files += 1
                rel_path = asset.get("local_path") or asset.get("rel_path")
                full_path = config.project_root / rel_path if rel_path else None
                if full_path and full_path.exists():
                    val = validate_raster(full_path)
                    f_size = full_path.stat().st_size
                    total_bytes += f_size
                    computed_sha = calculate_sha256(full_path)
                    recorded_sha = asset.get("sha256", "")
                    if computed_sha == recorded_sha:
                        checksum_passed += 1
                    else:
                        checksum_failed += 1

                    if val.get("valid"):
                        raster_passed += 1
                        valid_files += 1
                        print(f"    [OK] {req_name:10} | {format_bytes(f_size):>10} | {val.get('width')}x{val.get('height')} | SHA: {recorded_sha[:8]}... | Local: {rel_path}")
                    else:
                        raster_failed += 1
                        failed_files += 1
                        print(f"    [FAIL] {req_name:10} | Raster error: {val.get('error')}")
                else:
                    failed_files += 1
                    print(f"    [FAIL] {req_name:10} | File missing: {rel_path}")
        print()

    # 2. Sentinel-2 validation
    if "sentinel2" in sources_to_check and "sentinel2" in acquisitions:
        print("SENTINEL-2 VALIDATION:")
        for pr in acquisitions["sentinel2"]:
            print(f"  Product: {pr['product_id']} (Date: {pr['observation_date'][:10]})")
            for band_name, band in pr.get("bands", {}).items():
                total_files += 1
                rel_path = band.get("local_path") or band.get("rel_path")
                full_path = config.project_root / rel_path if rel_path else None
                if full_path and full_path.exists():
                    val = validate_raster(full_path)
                    f_size = full_path.stat().st_size
                    total_bytes += f_size
                    computed_sha = calculate_sha256(full_path)
                    recorded_sha = band.get("sha256", "")
                    if computed_sha == recorded_sha:
                        checksum_passed += 1
                    else:
                        checksum_failed += 1

                    if val.get("valid"):
                        raster_passed += 1
                        valid_files += 1
                        print(f"    [OK] {band_name:10} | {format_bytes(f_size):>10} | {val.get('width')}x{val.get('height')} | SHA: {recorded_sha[:8]}... | Local: {rel_path}")
                    else:
                        raster_failed += 1
                        failed_files += 1
                        print(f"    [FAIL] {band_name:10} | Raster error: {val.get('error')}")
                else:
                    failed_files += 1
                    print(f"    [FAIL] {band_name:10} | File missing: {rel_path}")
        print()

    # 3. MODIS validation
    if "modis" in sources_to_check and "modis" in acquisitions:
        print("MODIS VALIDATION:")
        for per in acquisitions["modis"]:
            print(f"  Period: {per['item_id']} (Date: {str(per['observation_date'])[:10]}, Native Res: 1 km)")
            for asset_name, asset in per.get("assets", {}).items():
                total_files += 1
                rel_path = asset.get("local_path") or asset.get("rel_path")
                full_path = config.project_root / rel_path if rel_path else None
                if full_path and full_path.exists():
                    val = validate_raster(full_path)
                    f_size = full_path.stat().st_size
                    total_bytes += f_size
                    computed_sha = calculate_sha256(full_path)
                    recorded_sha = asset.get("sha256", "")
                    if computed_sha == recorded_sha:
                        checksum_passed += 1
                    else:
                        checksum_failed += 1

                    if val.get("valid"):
                        raster_passed += 1
                        valid_files += 1
                        print(f"    [OK] {asset_name:15} | {format_bytes(f_size):>10} | {val.get('width')}x{val.get('height')} | SHA: {recorded_sha[:8]}...")
                    else:
                        raster_failed += 1
                        failed_files += 1
                        print(f"    [FAIL] {asset_name:15} | Raster error: {val.get('error')}")
                else:
                    failed_files += 1
                    print(f"    [FAIL] {asset_name:15} | File missing: {rel_path}")
        print()

    # 4. NASA POWER validation
    if "nasa_power" in sources_to_check and "nasa_power" in acquisitions:
        print("NASA POWER VALIDATION:")
        p_res = acquisitions["nasa_power"]
        rel_path = p_res.get("local_path") or p_res.get("file")
        full_path = config.project_root / rel_path if rel_path else None
        total_files += 1
        if full_path and full_path.exists():
            f_size = full_path.stat().st_size
            total_bytes += f_size
            computed_sha = calculate_sha256(full_path)
            recorded_sha = p_res.get("sha256", "")
            if computed_sha == recorded_sha:
                checksum_passed += 1
            else:
                checksum_failed += 1
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
                num_days = len(pdata.get("properties", {}).get("parameter", {}).get("T2M", {}))
                valid_files += 1
                print(f"  [OK] power_{config.year}_daily.json | {format_bytes(f_size)} | {num_days} daily records | SHA: {recorded_sha[:8]}...")
            except Exception as e:
                failed_files += 1
                print(f"  [FAIL] JSON parsing error: {e}")
        else:
            failed_files += 1
            print("  [FAIL] NASA POWER data file missing")
        print()

    # 5. OpenStreetMap validation
    if "osm" in sources_to_check and "osm" in acquisitions:
        print("OPENSTREETMAP VALIDATION:")
        layers = acquisitions["osm"].get("layers", {})
        for layer_name, layer_info in layers.items():
            total_files += 1
            rel_path = layer_info.get("local_path") or layer_info.get("file")
            full_path = config.project_root / rel_path if rel_path else None
            if full_path and full_path.exists():
                val = validate_vector(full_path)
                f_size = full_path.stat().st_size
                total_bytes += f_size
                computed_sha = calculate_sha256(full_path)
                recorded_sha = layer_info.get("sha256", "")
                if computed_sha == recorded_sha:
                    checksum_passed += 1
                else:
                    checksum_failed += 1

                if val.get("valid"):
                    vector_passed += 1
                    valid_files += 1
                    print(f"  [OK] {layer_name:22} | {format_bytes(f_size):>10} | {val.get('feature_count')} features | SHA: {recorded_sha[:8]}...")
                else:
                    vector_failed += 1
                    failed_files += 1
                    print(f"  [FAIL] {layer_name:22} | Vector error: {val.get('error')}")
            else:
                failed_files += 1
                print(f"  [FAIL] {layer_name:22} | File missing")
        print()

    # 6. DEM validation
    if "dem" in sources_to_check and "dem" in acquisitions:
        print("DEM VALIDATION:")
        for tile in acquisitions["dem"]:
            total_files += 1
            rel_path = tile.get("local_path") or tile.get("rel_path")
            full_path = config.project_root / rel_path if rel_path else None
            if full_path and full_path.exists():
                val = validate_raster(full_path)
                f_size = full_path.stat().st_size
                total_bytes += f_size
                computed_sha = calculate_sha256(full_path)
                recorded_sha = tile.get("sha256", "")
                if computed_sha == recorded_sha:
                    checksum_passed += 1
                else:
                    checksum_failed += 1

                if val.get("valid"):
                    raster_passed += 1
                    valid_files += 1
                    print(f"  [OK] {tile['tile_id']} | {format_bytes(f_size):>10} | {val.get('width')}x{val.get('height')} | SHA: {recorded_sha[:8]}...")
                else:
                    raster_failed += 1
                    failed_files += 1
                    print(f"  [FAIL] {tile['tile_id']} | Raster error: {val.get('error')}")
            else:
                failed_files += 1
                print(f"  [FAIL] {tile['tile_id']} | File missing")
        print()

    print("=" * 60)
    print("VALIDATION SUMMARY:")
    print(f"  Checksums:         {checksum_passed}/{checksum_passed + checksum_failed} passed")
    print(f"  Raster validation: {raster_passed}/{raster_passed + raster_failed} passed")
    print(f"  Vector validation: {vector_passed}/{vector_passed + vector_failed} passed")
    print(f"  Overall:           {valid_files}/{total_files} files valid ({failed_files} failed)")
    print(f"  Local Data Lake:   {format_bytes(total_bytes)}")
    print("=" * 60)
    return 0 if failed_files == 0 else 1


def cmd_status(config: IngestionConfig) -> int:
    """Produce executive status report of data lake and ingestion state matching Section 30."""
    aoi_data = load_aoi(config.aoi_path)
    is_valid, crs, geom, bbox, centroid = validate_aoi(aoi_data)

    manifest_path = config.get_manifest_path()
    plan = load_manifest(manifest_path)
    sources_plan = plan.get("sources", {})
    acquisitions = plan.get("acquisitions", {})

    print("\n" + "=" * 60)
    print("CLIMORA INGESTION & DATA LAKE STATUS")
    print("=" * 60)

    print("AOI")
    print(f"  Study Area:   {config.study_area}")
    print(f"  Status:       {'VALID' if is_valid else 'INVALID'}")
    print(f"  Geometry:     {geom.geom_type if geom else 'Unknown'}")
    print(f"  CRS:          {crs}")
    print(f"  Bounding Box: {bbox}")
    print(f"  Centroid:     {centroid}")
    print()

    # Landsat status
    l_plan = sources_plan.get("landsat", {})
    l_acq = acquisitions.get("landsat", [])
    l_downloaded = sum(len(s.get("assets", {})) for s in l_acq)
    l_valid = sum(sum(1 for a in s.get("assets", {}).values() if a.get("validation_status") == "VALID" or a.get("status") == "VALID") for s in l_acq)
    print("LANDSAT (Collection 2 Level-2)")
    print(f"  Candidate Scenes:  {l_plan.get('total_candidates', 'N/A')}")
    print(f"  Selected Scenes:   {len(l_acq)}")
    print(f"  Downloaded Assets: {l_downloaded}")
    print(f"  Valid Assets:      {l_valid}")
    print(f"  Failed:            {l_downloaded - l_valid}")
    print()

    # Sentinel-2 status
    s2_plan = sources_plan.get("sentinel2", {})
    s2_acq = acquisitions.get("sentinel2", [])
    s2_downloaded = sum(len(p.get("bands", {})) for p in s2_acq)
    s2_valid = sum(sum(1 for b in p.get("bands", {}).values() if b.get("validation_status") == "VALID" or b.get("status") == "VALID") for p in s2_acq)
    print("SENTINEL-2 (MSI Level-2A)")
    print(f"  Candidate Products: {s2_plan.get('total_candidates', 'N/A')}")
    print(f"  Selected Products:  {len(s2_acq)}")
    print(f"  Downloaded Bands:   {s2_downloaded}")
    print(f"  Valid Bands:        {s2_valid}")
    print(f"  Failed:             {s2_downloaded - s2_valid}")
    print()

    # MODIS status
    m_plan = sources_plan.get("modis", {})
    m_acq = acquisitions.get("modis", [])
    m_downloaded = sum(len(p.get("assets", {})) for p in m_acq)
    m_valid = sum(sum(1 for a in p.get("assets", {}).values() if a.get("validation_status") == "VALID" or a.get("status") == "VALID") for p in m_acq)
    print("MODIS (MOD11A2 Version 6.1)")
    print(f"  Tile:              {m_plan.get('tile', 'h25v07')} (1 km native resolution)")
    print(f"  Candidate Periods: {m_plan.get('total_periods', 'N/A')}")
    print(f"  Selected Periods:  {len(m_acq)}")
    print(f"  Downloaded Assets: {m_downloaded}")
    print(f"  Valid Assets:      {m_valid}")
    print(f"  Failed:            {m_downloaded - m_valid}")
    print()

    # NASA POWER status
    p_acq = acquisitions.get("nasa_power", {})
    p_valid = 1 if p_acq.get("status") == "VALID" or p_acq.get("validation_status") == "VALID" else 0
    vars_list = p_acq.get("variables") or p_acq.get("metadata", {}).get("returned_variables", [])
    print("NASA POWER (Daily Meteorology)")
    print(f"  Status:            {'INGESTED & VALID' if p_valid else 'PENDING'}")
    print(f"  Observations:      365 daily records ({len(vars_list)} variables: {', '.join(vars_list)})")
    print()

    # OSM status
    o_acq = acquisitions.get("osm", {})
    o_layers = o_acq.get("layers", {})
    o_valid = sum(1 for l in o_layers.values() if l.get("status") == "VALID" or l.get("validation_status") == "VALID")
    print("OPENSTREETMAP (Pune AOI Vectors)")
    print(f"  Layers Ingested:   {len(o_layers)}")
    print(f"  Valid Layers:      {o_valid}")
    print()

    # DEM status
    d_plan = sources_plan.get("dem", {})
    d_acq = acquisitions.get("dem", [])
    d_valid = sum(1 for t in d_acq if t.get("status") == "VALID" or t.get("validation_status") == "VALID")
    print("DEM (Copernicus DEM GLO-30)")
    print(f"  Available Tiles:   {len(d_plan.get('required_tiles', []))}")
    print(f"  Downloaded Tiles:  {len(d_acq)}")
    print(f"  Valid Tiles:       {d_valid}")
    print()

    # Raw subfolder breakdown
    raw_lake_files = get_lake_files(config.raw_dir)
    total_lake_bytes = sum(f.stat().st_size for f in raw_lake_files)

    landsat_bytes = sum(f.stat().st_size for f in raw_lake_files if "landsat" in f.parts)
    sentinel_bytes = sum(f.stat().st_size for f in raw_lake_files if "sentinel2" in f.parts)
    modis_bytes = sum(f.stat().st_size for f in raw_lake_files if "modis" in f.parts)
    dem_bytes = sum(f.stat().st_size for f in raw_lake_files if "dem" in f.parts)
    osm_bytes = sum(f.stat().st_size for f in raw_lake_files if "osm" in f.parts)
    nasa_bytes = sum(f.stat().st_size for f in raw_lake_files if "nasa_power" in f.parts)

    print("STORAGE BREAKDOWN")
    print(f"  Landsat:           {format_bytes(landsat_bytes)} ({sum(1 for f in raw_lake_files if 'landsat' in f.parts)} files)")
    print(f"  Sentinel-2:        {format_bytes(sentinel_bytes)} ({sum(1 for f in raw_lake_files if 'sentinel2' in f.parts)} files)")
    print(f"  MODIS:             {format_bytes(modis_bytes)} ({sum(1 for f in raw_lake_files if 'modis' in f.parts)} files)")
    print(f"  DEM:               {format_bytes(dem_bytes)} ({sum(1 for f in raw_lake_files if 'dem' in f.parts)} files)")
    print(f"  OSM:               {format_bytes(osm_bytes)} ({sum(1 for f in raw_lake_files if 'osm' in f.parts)} files)")
    print(f"  NASA POWER:        {format_bytes(nasa_bytes)} ({sum(1 for f in raw_lake_files if 'nasa_power' in f.parts)} files)")
    print(f"  TOTAL RAW LAKE:    {format_bytes(total_lake_bytes)} ({len(raw_lake_files)} total files)")
    print(f"  S3 STATUS:         DISABLED (Local-only mode active)")
    print("=" * 60)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m ingestion",
        description="CLIMORA Phase 0: Pune Data Acquisition & Local Data Lake CLI",
    )
    parser.add_argument("--config", type=str, default=None, help="Path to custom config.yaml")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: search
    p_search = subparsers.add_parser("search", help="Search catalogues and generate acquisition plan without downloading")
    p_search.add_argument("--source", type=str, default=None, help="Specific source (landsat, sentinel2, modis, nasa_power, osm, dem)")
    p_search.add_argument("--year", type=int, default=None, help="Acquisition target year (e.g. 2025)")

    # Subcommand: estimate
    p_est = subparsers.add_parser("estimate", help="Calculate storage requirements for candidate dataset without downloading")
    p_est.add_argument("--year", type=int, default=None, help="Acquisition target year (e.g. 2025)")
    p_est.add_argument("--source", type=str, default=None, help="Specific source to estimate")

    # Subcommand: download
    p_dl = subparsers.add_parser("download", help="Download approved candidate assets idempotently")
    p_dl.add_argument("--source", type=str, default=None, help="Specific source to download")
    p_dl.add_argument("--limit", type=int, default=None, help="Max scenes/products to download")
    p_dl.add_argument("--bands", type=str, default=None, help="Comma-separated band names to download (e.g. SCL,B05,B08)")
    p_dl.add_argument("--force", action="store_true", help="Force download even if storage threshold warning triggers")

    # Subcommand: validate
    p_val = subparsers.add_parser("validate", help="Validate integrity, formats, checksums, and geometries of ingested data")
    p_val.add_argument("--source", type=str, default=None, help="Specific source to validate")

    # Subcommand: status
    subparsers.add_parser("status", help="Print overall acquisition status and data lake storage metrics")

    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    if args.command == "search":
        sys.exit(cmd_search(config, source=args.source, year=args.year))
    elif args.command == "estimate":
        sys.exit(cmd_estimate(config, year=args.year, source=args.source))
    elif args.command == "download":
        sys.exit(cmd_download(config, source=args.source, limit=args.limit, bands=args.bands, force=args.force))
    elif args.command == "validate":
        sys.exit(cmd_validate(config, source=args.source))
    elif args.command == "status":
        sys.exit(cmd_status(config))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
