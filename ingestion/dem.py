"""Copernicus DEM acquisition module for CLIMORA.

Targets:
- Copernicus DEM GLO-30 (30m Cloud-Optimized GeoTIFF)
- Pune coverage tile: Copernicus_DSM_COG_10_N18_00_E073_00_DEM
- Documented fallback: GLO-90
- Storage: data/raw/dem/pune/
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import planetary_computer as pc
import pystac_client

from ingestion.common import calculate_sha256, get_logger, safe_download_file, validate_raster
from ingestion.config import IngestionConfig

logger = get_logger()


def search_dem(
    config: IngestionConfig,
    aoi_bbox: List[float],
) -> Dict[str, Any]:
    """Search Copernicus DEM GLO-30 catalogue for Pune coverage tiles."""
    logger.info("Searching Copernicus DEM GLO-30 catalogue for Pune...")
    src_cfg = config.sources.get("dem", {})
    stac_url = src_cfg.get("stac_api_url", "https://planetarycomputer.microsoft.com/api/stac/v1")
    collection = src_cfg.get("collection", "cop-dem-glo-30")

    catalog = pystac_client.Client.open(stac_url, modifier=pc.sign_inplace)

    search = catalog.search(
        collections=[collection],
        bbox=aoi_bbox,
    )
    items = list(search.items())

    dem_tiles: List[Dict[str, Any]] = []
    for item in items:
        data_asset = item.assets.get("data")
        if data_asset:
            dem_tiles.append({
                "id": item.id,
                "title": data_asset.title or item.id,
                "href": data_asset.href,
                "bbox": item.bbox,
                "resolution": "30m",
                "format": "Cloud-Optimized GeoTIFF (COG)",
            })

    # Sort so E073 (covering majority of Pune City) is first
    dem_tiles.sort(key=lambda t: 0 if "E073" in t["id"] else 1)

    logger.info(f"DEM: Found {len(dem_tiles)} Copernicus DEM GLO-30 tile(s) covering Pune")

    return {
        "dataset": "copernicus-dem-glo-30",
        "provider": "Copernicus / European Space Agency / Microsoft Planetary Computer",
        "official_source": "Copernicus DEM GLO-30 (30m)",
        "fallback_option": "copernicus-dem-glo-90 (90m)",
        "stac_endpoint": stac_url,
        "aoi_bbox": aoi_bbox,
        "required_tiles": [t["id"] for t in dem_tiles],
        "tiles": dem_tiles,
    }


def download_dem(
    config: IngestionConfig,
    search_results: Dict[str, Any],
    limit: Optional[int] = 1,
) -> List[Dict[str, Any]]:
    """Download approved Copernicus DEM tile(s) idempotently.

    Downloads COG to:
    data/raw/dem/pune/<tile_id>.tif
    """
    tiles = search_results.get("tiles", [])
    max_download = limit or 1
    to_download = tiles[:max_download]

    out_dir = config.get_source_raw_dir("dem", "pune")
    ingested_tiles: List[Dict[str, Any]] = []

    stac_url = config.sources.get("dem", {}).get("stac_api_url", "https://planetarycomputer.microsoft.com/api/stac/v1")
    collection = config.sources.get("dem", {}).get("collection", "cop-dem-glo-30")
    catalog = pystac_client.Client.open(stac_url, modifier=pc.sign_inplace)

    for tile in to_download:
        tile_id = tile["id"]
        dest_file = out_dir / f"{tile_id}.tif"

        signed_search = catalog.search(collections=[collection], ids=[tile_id])
        signed_items = list(signed_search.items())
        if not signed_items:
            logger.error(f"Could not retrieve fresh signed STAC item for DEM tile {tile_id}")
            continue
        fresh_item = signed_items[0]
        data_asset = fresh_item.assets.get("data")
        if not data_asset:
            continue
        url = data_asset.href

        logger.info(f"Ingesting Copernicus DEM GLO-30 tile: {tile_id}...")

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
            s3_uri = f"s3://climora-lake/raw/dem/pune/{dest_file.name}"

            from ingestion.common import build_provenance_record
            prov = build_provenance_record(
                dataset_id="copernicus-dem-glo-30",
                provider="Copernicus / European Space Agency / Microsoft Planetary Computer",
                product="Copernicus DEM GLO-30 (30m Cloud-Optimized GeoTIFF)",
                version="GLO-30",
                source="Microsoft Planetary Computer STAC API",
                source_item_id=tile_id,
                license_name="Copernicus Open Access",
                access_method="STAC API SAS URL Chunked Stream",
                spatial_resolution="30m",
                temporal_resolution="Static Digital Elevation Model",
                acquisition_date="2021",
                observation_period={"start": "static", "end": "static"},
                aoi={"study_area": config.study_area, "tile": tile_id},
                cloud_cover=None,
                selection_strategy="elevation_baseline",
                selection_parameters={"target_tile": config.sources.get("dem", {}).get("target_tile")},
                required_assets=["data"],
                local_path=rel_path,
                file_size_bytes=file_size,
                sha256=sha256_hash,
                validation_status="VALID" if val.get("valid") else "INVALID",
                s3_uri=s3_uri,
                extra={
                    "tile_id": tile_id,
                    "filename": dest_file.name,
                    "resolution": "30m",
                    "format": "COG",
                    "raster_validation": val,
                    "skipped_idempotent": skipped,
                },
            )
            prov["tile_id"] = tile_id
            prov["status"] = prov["validation_status"]
            ingested_tiles.append(prov)
        except Exception as e:
            logger.error(f"Failed to download DEM tile {tile_id}: {e}")
            ingested_tiles.append({
                "tile_id": tile_id,
                "status": "FAILED",
                "error": str(e),
            })

    return ingested_tiles
