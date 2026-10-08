"""Landsat Collection 2 Level-2 acquisition module for CLIMORA.

Targets:
- Landsat 8 and Landsat 9 Level-2
- Temporal target: 2025
- AOI: Pune intersection
- Cloud threshold: <= 20%
- Assets required: SR_B2, SR_B3, SR_B4, SR_B5, SR_B6, SR_B7, ST_B10, QA_PIXEL, QA_RADSAT
- S3-compatible provenance & deterministic seasonal selection
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import planetary_computer as pc
import pystac_client

from ingestion.common import (
    build_provenance_record,
    calculate_sha256,
    get_logger,
    safe_download_file,
    select_seasonal_candidates,
    validate_raster,
)
from ingestion.config import IngestionConfig

logger = get_logger()

# Standard asset name to Planetary Computer STAC asset key mapping
LANDSAT_ASSET_MAPPING = {
    "SR_B2": "blue",
    "SR_B3": "green",
    "SR_B4": "red",
    "SR_B5": "nir08",
    "SR_B6": "swir16",
    "SR_B7": "swir22",
    "ST_B10": "lwir11",
    "QA_PIXEL": "qa_pixel",
    "QA_RADSAT": "qa_radsat",
}

# Empirical approximate asset sizes for storage estimation (bytes)
LANDSAT_ESTIMATED_ASSET_SIZES = {
    "SR_B2": 85_650_000,
    "SR_B3": 87_670_000,
    "SR_B4": 91_950_000,
    "SR_B5": 94_550_000,
    "SR_B6": 96_420_000,
    "SR_B7": 94_560_000,
    "ST_B10": 88_880_000,
    "QA_PIXEL": 760_000,
    "QA_RADSAT": 225_000,
}
LANDSAT_ESTIMATED_SCENE_SIZE = sum(LANDSAT_ESTIMATED_ASSET_SIZES.values())  # ~640.7 MB


def search_landsat(
    config: IngestionConfig,
    aoi_bbox: List[float],
) -> Dict[str, Any]:
    """Search Landsat Collection 2 Level-2 catalogue via STAC without downloading.

    Performs:
    1. Candidate Discovery (all STAC items intersecting Pune AOI in target year)
    2. Quality Filtering (cloud cover <= cloud_cover_max, platform validity, required assets present)
    3. Deterministic Seasonal Selection (selecting representative observations across Pune seasons,
       prioritizing existing bootstrap data)
    4. Asset Storage Estimation
    """
    logger.info("Searching Landsat Collection 2 Level-2 catalogue...")
    src_cfg = config.sources.get("landsat", {})
    stac_url = src_cfg.get("stac_api_url", "https://planetarycomputer.microsoft.com/api/stac/v1")
    cloud_max = float(src_cfg.get("cloud_cover_max", 20.0))
    collection = src_cfg.get("collection", "landsat-c2-l2")

    datetime_range = f"{config.start_date}T00:00:00Z/{config.end_date}T23:59:59Z"

    catalog = pystac_client.Client.open(stac_url, modifier=pc.sign_inplace)

    # 1. Candidate Discovery
    search_all = catalog.search(
        collections=[collection],
        bbox=aoi_bbox,
        datetime=datetime_range,
    )
    all_items = list(search_all.items())
    total_candidates = len(all_items)

    candidates_inventory: List[Dict[str, Any]] = []
    filtered_scenes: List[Dict[str, Any]] = []

    # Detect existing local bootstrap scene IDs
    landsat_raw_dir = config.raw_dir / "landsat" / str(config.year)
    existing_scene_ids: Set[str] = set()
    if landsat_raw_dir.exists():
        existing_scene_ids = {p.name for p in landsat_raw_dir.iterdir() if p.is_dir()}

    for item in all_items:
        props = item.properties
        cloud_val = props.get("eo:cloud_cover", 100.0)
        platform = props.get("platform", "").lower()
        acq_datetime = props.get("datetime")

        # Map available required assets
        avail_assets = {}
        for req_name, stac_key in LANDSAT_ASSET_MAPPING.items():
            if stac_key in item.assets:
                asset = item.assets[stac_key]
                avail_assets[req_name] = {
                    "stac_key": stac_key,
                    "href": asset.href,
                    "title": asset.title or req_name,
                    "media_type": asset.media_type,
                    "estimated_size_bytes": LANDSAT_ESTIMATED_ASSET_SIZES.get(req_name, 88_000_000),
                }

        has_all_assets = len(avail_assets) == len(LANDSAT_ASSET_MAPPING)
        is_platform_valid = platform in ("landsat-8", "landsat-9", "landsat 8", "landsat 9")
        passes_cloud = float(cloud_val) <= cloud_max

        item_record = {
            "id": item.id,
            "platform": platform,
            "processing_level": "Collection 2 Level-2",
            "date": acq_datetime,
            "cloud_cover": round(float(cloud_val), 2),
            "bbox": item.bbox,
            "geometry": item.geometry,
            "intersects_aoi": True,
            "available_assets": avail_assets,
            "has_all_required_assets": has_all_assets,
            "is_local_bootstrap": item.id in existing_scene_ids,
            "source_catalogue": "Microsoft Planetary Computer STAC / USGS",
            "estimated_scene_size_bytes": LANDSAT_ESTIMATED_SCENE_SIZE,
        }
        candidates_inventory.append(item_record)

        # 2. Quality Filtering
        if is_platform_valid and passes_cloud and has_all_assets:
            filtered_scenes.append(item_record)

    # Sort filtered scenes for deterministic processing
    filtered_scenes.sort(key=lambda s: (s["cloud_cover"], s["date"], s["id"]))

    # 3. Deterministic Seasonal Selection
    target_per_season = config.target_per_season
    selected_scenes, seasonal_summary = select_seasonal_candidates(
        candidates=filtered_scenes,
        seasons=config.seasons,
        target_per_season=target_per_season,
        existing_ids=existing_scene_ids,
    )

    limit = src_cfg.get("download_limit")
    if limit and limit < len(selected_scenes):
        selected_scenes = selected_scenes[:limit]

    logger.info(
        f"Landsat: Found {total_candidates} candidates; {len(filtered_scenes)} met quality filters; "
        f"{len(selected_scenes)} deterministically selected."
    )

    return {
        "dataset": "landsat-c2-l2",
        "provider": "USGS / Microsoft Planetary Computer",
        "official_source": "USGS Landsat Collection 2 Level-2",
        "stac_endpoint": stac_url,
        "filter_criteria": {
            "period": {"start": config.start_date, "end": config.end_date},
            "cloud_cover_max": cloud_max,
            "bbox": aoi_bbox,
            "platforms": ["landsat-8", "landsat-9"],
            "processing_level": "Collection 2 Level-2",
        },
        "selection_strategy": config.selection_strategy,
        "selection_parameters": {
            "target_per_season": target_per_season,
            "max_cloud_cover": cloud_max,
        },
        "seasonal_selection_summary": seasonal_summary,
        "required_assets": list(LANDSAT_ASSET_MAPPING.keys()),
        "total_candidates": total_candidates,
        "filtered_candidates_count": len(filtered_scenes),
        "selected_candidates_count": len(selected_scenes),
        "estimated_size_per_scene_bytes": LANDSAT_ESTIMATED_SCENE_SIZE,
        "total_estimated_selected_bytes": len(selected_scenes) * LANDSAT_ESTIMATED_SCENE_SIZE,
        "selected_scenes": selected_scenes,
        "scenes": selected_scenes,  # Backward compatibility
        "filtered_scenes": filtered_scenes,
        "candidates_inventory": candidates_inventory,
    }


def download_landsat(
    config: IngestionConfig,
    search_results: Dict[str, Any],
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Download approved Landsat scene assets idempotently with complete provenance.

    Downloads only approved assets to:
    data/raw/landsat/<year>/<scene_id>/<asset_name>.tif
    """
    selected = search_results.get("selected_scenes") or search_results.get("scenes", [])
    max_download = limit or len(selected)
    to_download = selected[:max_download]

    ingested_scenes: List[Dict[str, Any]] = []

    stac_url = config.sources.get("landsat", {}).get("stac_api_url", "https://planetarycomputer.microsoft.com/api/stac/v1")
    collection = config.sources.get("landsat", {}).get("collection", "landsat-c2-l2")
    catalog = pystac_client.Client.open(stac_url, modifier=pc.sign_inplace)

    for sc in to_download:
        scene_id = sc["id"]
        sel_meta = sc.get("selection_metadata", {})
        logger.info(
            f"Ingesting Landsat scene: {scene_id} "
            f"(Season: {sel_meta.get('season_name', 'N/A')}, Cloud: {sc['cloud_cover']}%, Date: {sc['date']})"
        )

        signed_search = catalog.search(collections=[collection], ids=[scene_id])
        signed_items = list(signed_search.items())
        if not signed_items:
            logger.error(f"Could not retrieve fresh signed STAC item for {scene_id}")
            continue
        fresh_item = signed_items[0]

        scene_dir = config.get_source_raw_dir("landsat", f"{config.year}/{scene_id}")
        ingested_assets: Dict[str, Any] = {}

        for req_name, stac_key in LANDSAT_ASSET_MAPPING.items():
            if stac_key not in fresh_item.assets:
                continue
            dest_file = scene_dir / f"{req_name}.tif"
            url = fresh_item.assets[stac_key].href

            try:
                dest_path, sha256_hash, file_size, skipped = safe_download_file(
                    url=url,
                    dest_path=dest_file,
                    chunk_size=config.chunk_size_bytes,
                    retries=config.download_retries,
                    timeout=config.download_timeout,
                )

                val = validate_raster(dest_path)
                rel_path = str(dest_file.relative_to(config.project_root))
                s3_uri = f"s3://climora-lake/raw/landsat/{config.year}/{scene_id}/{dest_file.name}"

                prov_record = build_provenance_record(
                    dataset_id="landsat-c2-l2",
                    provider="USGS / Microsoft Planetary Computer",
                    product=f"Landsat Collection 2 Level-2 ({sc['platform'].upper()})",
                    version="Collection 2",
                    source="Microsoft Planetary Computer STAC API",
                    source_item_id=scene_id,
                    license_name="USGS Public Domain / Open Data",
                    access_method="STAC API SAS URL Chunked Stream",
                    spatial_resolution="30m (Thermal resampled to 30m in Level-2)",
                    temporal_resolution="16-day repeat (8-day constellation)",
                    acquisition_date=sc["date"],
                    observation_period={"start": config.start_date, "end": config.end_date},
                    aoi={"study_area": config.study_area, "bbox": sc["bbox"]},
                    cloud_cover=sc["cloud_cover"],
                    selection_strategy=sel_meta.get("selection_strategy", "seasonal_representative"),
                    selection_parameters=sel_meta.get("selection_parameters", {}),
                    required_assets=list(LANDSAT_ASSET_MAPPING.keys()),
                    local_path=rel_path,
                    file_size_bytes=file_size,
                    sha256=sha256_hash,
                    validation_status="VALID" if val.get("valid") else "INVALID",
                    s3_uri=s3_uri,
                    extra={
                        "asset_name": req_name,
                        "stac_key": stac_key,
                        "filename": dest_file.name,
                        "raster_validation": val,
                        "skipped_idempotent": skipped,
                        "selection_reason": sel_meta.get("selection_reason", ""),
                    },
                )
                ingested_assets[req_name] = prov_record

            except Exception as e:
                logger.error(f"Failed to download Landsat asset {req_name} for {scene_id}: {e}")
                ingested_assets[req_name] = {
                    "asset_name": req_name,
                    "status": "FAILED",
                    "error": str(e),
                }

        ingested_scenes.append({
            "scene_id": scene_id,
            "platform": sc["platform"],
            "observation_date": sc["date"],
            "cloud_cover": sc["cloud_cover"],
            "selection_metadata": sel_meta,
            "assets": ingested_assets,
            "all_valid": all(a.get("validation_status") == "VALID" or a.get("status") == "VALID" for a in ingested_assets.values()),
        })

    return ingested_scenes
