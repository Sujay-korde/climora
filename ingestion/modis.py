"""MODIS MOD11A2 Version 6.1 acquisition module for CLIMORA.

Targets:
- MODIS Terra/Aqua Land Surface Temperature and Emissivity 8-Day Global 1km
- Product: MOD11A2 Version 6.1
- Pune sinusoidal tile: h25v07
- Temporal target: 2025
- Required assets: LST_Day_1km, LST_Night_1km, QC_Day, QC_Night
- Native resolution: ~1 km explicitly recorded without resampling
- S3-compatible provenance & temporal sequence preservation
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
    validate_raster,
)
from ingestion.config import IngestionConfig

logger = get_logger()

MODIS_REQUIRED_ASSETS = ["LST_Day_1km", "LST_Night_1km", "QC_Day", "QC_Night"]

# Empirical approximate asset sizes for storage estimation (bytes)
MODIS_ESTIMATED_ASSET_SIZES = {
    "LST_Day_1km": 1_733_000,
    "LST_Night_1km": 1_611_000,
    "QC_Day": 78_000,
    "QC_Night": 81_000,
}
MODIS_ESTIMATED_PERIOD_SIZE = sum(MODIS_ESTIMATED_ASSET_SIZES.values())  # ~3.50 MB


def search_modis(
    config: IngestionConfig,
    aoi_bbox: List[float],
) -> Dict[str, Any]:
    """Search MODIS MOD11A2 v6.1 catalogue for Pune tile (h25v07) for 2025."""
    logger.info("Searching MODIS MOD11A2 v6.1 catalogue for Pune (tile h25v07)...")
    src_cfg = config.sources.get("modis", {})
    stac_url = src_cfg.get("stac_api_url", "https://planetarycomputer.microsoft.com/api/stac/v1")
    collection = src_cfg.get("collection", "modis-11A2-061")
    target_tile = src_cfg.get("tile", "h25v07")

    datetime_range = f"{config.start_date}T00:00:00Z/{config.end_date}T23:59:59Z"

    catalog = pystac_client.Client.open(stac_url, modifier=pc.sign_inplace)

    search = catalog.search(
        collections=[collection],
        bbox=aoi_bbox,
        datetime=datetime_range,
    )
    all_items = list(search.items())

    # Detect existing local bootstrap MODIS periods
    modis_raw_dir = config.raw_dir / "modis" / str(config.year)
    existing_period_ids: Set[str] = set()
    if modis_raw_dir.exists():
        existing_period_ids = {p.name for p in modis_raw_dir.iterdir() if p.is_dir()}

    tile_items: List[Dict[str, Any]] = []
    for item in all_items:
        # Match Pune tile h25v07
        if target_tile in item.id:
            avail_assets = {}
            for req_key in MODIS_REQUIRED_ASSETS:
                if req_key in item.assets:
                    asset = item.assets[req_key]
                    avail_assets[req_key] = {
                        "href": asset.href,
                        "title": asset.title or req_key,
                        "media_type": asset.media_type,
                        "estimated_size_bytes": MODIS_ESTIMATED_ASSET_SIZES.get(req_key, 1_000_000),
                    }

            acq_date = item.properties.get("datetime") or item.properties.get("start_datetime")
            tile_items.append({
                "id": item.id,
                "date": acq_date,
                "tile": target_tile,
                "native_resolution": "1 km (SIN Grid)",
                "temporal_cadence": "8-day composite",
                "available_assets": avail_assets,
                "has_all_required_assets": len(avail_assets) == len(MODIS_REQUIRED_ASSETS),
                "is_local_bootstrap": item.id in existing_period_ids,
                "estimated_period_size_bytes": MODIS_ESTIMATED_PERIOD_SIZE,
            })

    tile_items.sort(key=lambda x: str(x["date"]))

    # Deterministic selection for MODIS:
    # Prioritize existing bootstrap period, then select evenly spaced periods across 2025
    limit = src_cfg.get("download_limit", 4)
    if limit and limit < len(tile_items):
        # Always include existing bootstrap periods
        selected_periods = [p for p in tile_items if p["is_local_bootstrap"]]
        remaining = [p for p in tile_items if not p["is_local_bootstrap"]]
        slots_needed = limit - len(selected_periods)
        if slots_needed > 0 and remaining:
            step = max(1, len(remaining) // slots_needed)
            for i in range(0, len(remaining), step):
                if len(selected_periods) < limit:
                    selected_periods.append(remaining[i])
        selected_periods.sort(key=lambda x: str(x["date"]))
    else:
        selected_periods = list(tile_items)

    logger.info(
        f"MODIS: Found {len(tile_items)} 8-day composite periods for tile {target_tile} in {config.year}; "
        f"Selected {len(selected_periods)} periods across the annual sequence."
    )

    return {
        "dataset": "MOD11A2-061",
        "provider": "NASA LP DAAC / Microsoft Planetary Computer",
        "official_source": "MODIS/Terra Land Surface Temperature/Emissivity 8-Day L3 Global 1km SIN Grid V061",
        "native_resolution": "1 km (SIN Grid)",
        "temporal_cadence": "8-day composite",
        "tile": target_tile,
        "stac_endpoint": stac_url,
        "period": {"start": config.start_date, "end": config.end_date},
        "required_assets": MODIS_REQUIRED_ASSETS,
        "total_periods": len(tile_items),
        "selected_periods_count": len(selected_periods),
        "estimated_size_per_period_bytes": MODIS_ESTIMATED_PERIOD_SIZE,
        "total_estimated_selected_bytes": len(selected_periods) * MODIS_ESTIMATED_PERIOD_SIZE,
        "selected_periods": selected_periods,
        "periods": selected_periods,  # Backward compatibility
        "all_candidate_periods": tile_items,
    }


def download_modis(
    config: IngestionConfig,
    search_results: Dict[str, Any],
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Download approved MODIS 8-day assets idempotently with complete provenance.

    Downloads only required assets to:
    data/raw/modis/<year>/<product_id>/<asset_name>.tif
    """
    periods = search_results.get("selected_periods") or search_results.get("periods", [])
    max_download = limit or len(periods)
    to_download = periods[:max_download]

    ingested_periods: List[Dict[str, Any]] = []

    stac_url = config.sources.get("modis", {}).get("stac_api_url", "https://planetarycomputer.microsoft.com/api/stac/v1")
    collection = config.sources.get("modis", {}).get("collection", "modis-11A2-061")
    catalog = pystac_client.Client.open(stac_url, modifier=pc.sign_inplace)

    for per in to_download:
        item_id = per["id"]
        logger.info(f"Ingesting MODIS 8-day period: {item_id} (Date: {per['date']}, Native Res: 1 km)")

        signed_search = catalog.search(collections=[collection], ids=[item_id])
        signed_items = list(signed_search.items())
        if not signed_items:
            logger.error(f"Could not retrieve fresh signed STAC item for MODIS {item_id}")
            continue
        fresh_item = signed_items[0]

        out_dir = config.get_source_raw_dir("modis", f"{config.year}/{item_id}")
        ingested_assets: Dict[str, Any] = {}

        for asset_name in MODIS_REQUIRED_ASSETS:
            if asset_name not in fresh_item.assets:
                continue
            dest_file = out_dir / f"{asset_name}.tif"
            url = fresh_item.assets[asset_name].href

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
                s3_uri = f"s3://climora-lake/raw/modis/{config.year}/{item_id}/{dest_file.name}"

                prov_record = build_provenance_record(
                    dataset_id="MOD11A2-061",
                    provider="NASA LP DAAC / Microsoft Planetary Computer",
                    product="MODIS/Terra Land Surface Temperature/Emissivity 8-Day L3 Global 1km SIN Grid V061",
                    version="061",
                    source="Microsoft Planetary Computer STAC API",
                    source_item_id=item_id,
                    license_name="NASA Open Data Policy",
                    access_method="STAC API SAS URL Chunked Stream",
                    spatial_resolution="1 km (SIN Grid, native resolution preserved)",
                    temporal_resolution="8-day composite",
                    acquisition_date=str(per["date"]),
                    observation_period={"start": config.start_date, "end": config.end_date},
                    aoi={"study_area": config.study_area, "tile": per["tile"]},
                    cloud_cover=None,  # Composite product
                    selection_strategy="temporal_sequence_8day",
                    selection_parameters={"cadence": "8-day", "tile": per["tile"]},
                    required_assets=MODIS_REQUIRED_ASSETS,
                    local_path=rel_path,
                    file_size_bytes=file_size,
                    sha256=sha256_hash,
                    validation_status="VALID" if val.get("valid") else "INVALID",
                    s3_uri=s3_uri,
                    extra={
                        "asset_name": asset_name,
                        "filename": dest_file.name,
                        "native_resolution": "1 km",
                        "raster_validation": val,
                        "skipped_idempotent": skipped,
                    },
                )
                ingested_assets[asset_name] = prov_record

            except Exception as e:
                logger.error(f"Failed to download MODIS asset {asset_name} for {item_id}: {e}")
                ingested_assets[asset_name] = {
                    "asset_name": asset_name,
                    "status": "FAILED",
                    "error": str(e),
                }

        ingested_periods.append({
            "item_id": item_id,
            "observation_date": per["date"],
            "native_resolution": "1 km",
            "assets": ingested_assets,
            "all_valid": all(a.get("validation_status") == "VALID" or a.get("status") == "VALID" for a in ingested_assets.values()),
        })

    return ingested_periods
