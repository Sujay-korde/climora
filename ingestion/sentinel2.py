"""Sentinel-2 MSI Level-2A acquisition module for CLIMORA.

Targets:
- Sentinel-2 MSI Level-2A (ESA / Copernicus)
- Temporal target: 2025
- AOI: Pune intersection
- Cloud threshold: <= 20%
- Required bands: B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12, SCL
- S3-compatible provenance & deterministic seasonal selection
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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

# Standard band to STAC asset key mapping
SENTINEL2_BAND_MAPPING = {
    "B02": "blue",
    "B03": "green",
    "B04": "red",
    "B05": "rededge1",
    "B06": "rededge2",
    "B07": "rededge3",
    "B08": "nir",
    "B8A": "nir08",
    "B11": "swir16",
    "B12": "swir22",
    "SCL": "scl",
}

# Empirical approximate band sizes for storage estimation (bytes)
SENTINEL2_ESTIMATED_BAND_SIZES = {
    "B02": 110_000_000,
    "B03": 110_000_000,
    "B04": 110_000_000,
    "B05": 59_400_000,
    "B06": 55_000_000,
    "B07": 55_000_000,
    "B08": 110_000_000,
    "B8A": 55_000_000,
    "B11": 55_000_000,
    "B12": 55_000_000,
    "SCL": 3_500_000,
}
SENTINEL2_ESTIMATED_PRODUCT_SIZE = sum(SENTINEL2_ESTIMATED_BAND_SIZES.values())  # ~777.9 MB


def search_sentinel2(
    config: IngestionConfig,
    aoi_bbox: List[float],
) -> Dict[str, Any]:
    """Search Sentinel-2 MSI Level-2A catalogue via Earth Search STAC without downloading.

    Performs:
    1. Candidate Discovery (all STAC items intersecting Pune AOI in target year)
    2. Quality Filtering (cloud cover <= cloud_cover_max, required bands present)
    3. Deterministic Seasonal Selection (selecting representative observations across Pune seasons,
       prioritizing existing bootstrap data)
    4. Asset Storage Estimation
    """
    logger.info("Searching Sentinel-2 MSI Level-2A catalogue...")
    src_cfg = config.sources.get("sentinel2", {})
    stac_url = src_cfg.get("stac_api_url", "https://earth-search.aws.element84.com/v1")
    cloud_max = float(src_cfg.get("cloud_cover_max", 20.0))
    collection = src_cfg.get("collection", "sentinel-2-c1-l2a")

    datetime_range = f"{config.start_date}T00:00:00Z/{config.end_date}T23:59:59Z"

    catalog = pystac_client.Client.open(stac_url)

    # 1. Candidate Discovery
    search_all = catalog.search(
        collections=[collection],
        bbox=aoi_bbox,
        datetime=datetime_range,
    )
    all_items = list(search_all.items())
    total_candidates = len(all_items)

    candidates_inventory: List[Dict[str, Any]] = []
    filtered_products: List[Dict[str, Any]] = []

    # Detect existing local bootstrap product IDs
    s2_raw_dir = config.raw_dir / "sentinel2" / str(config.year)
    existing_product_ids: Set[str] = set()
    if s2_raw_dir.exists():
        existing_product_ids = {p.name for p in s2_raw_dir.iterdir() if p.is_dir()}

    for item in all_items:
        props = item.properties
        cloud_val = props.get("eo:cloud_cover", 100.0)
        platform = props.get("platform", "sentinel-2")
        acq_datetime = props.get("datetime")

        avail_bands = {}
        for band_name, stac_key in SENTINEL2_BAND_MAPPING.items():
            if stac_key in item.assets:
                asset = item.assets[stac_key]
                avail_bands[band_name] = {
                    "stac_key": stac_key,
                    "href": asset.href,
                    "title": asset.title or band_name,
                    "media_type": asset.media_type,
                    "estimated_size_bytes": SENTINEL2_ESTIMATED_BAND_SIZES.get(band_name, 50_000_000),
                }

        has_all_bands = len(avail_bands) == len(SENTINEL2_BAND_MAPPING)
        passes_cloud = float(cloud_val) <= cloud_max

        item_record = {
            "id": item.id,
            "platform": platform,
            "processing_level": "Level-2A",
            "date": acq_datetime,
            "cloud_cover": round(float(cloud_val), 2),
            "bbox": item.bbox,
            "geometry": item.geometry,
            "intersects_aoi": True,
            "available_bands": avail_bands,
            "has_all_required_bands": has_all_bands,
            "is_local_bootstrap": item.id in existing_product_ids,
            "source_catalogue": "ESA Copernicus / AWS Earth Search STAC",
            "estimated_product_size_bytes": SENTINEL2_ESTIMATED_PRODUCT_SIZE,
        }
        candidates_inventory.append(item_record)

        # 2. Quality Filtering
        if passes_cloud and has_all_bands:
            filtered_products.append(item_record)

    filtered_products.sort(key=lambda p: (p["cloud_cover"], p["date"], p["id"]))

    # 3. Deterministic Seasonal Selection
    target_per_season = config.target_per_season
    selected_products, seasonal_summary = select_seasonal_candidates(
        candidates=filtered_products,
        seasons=config.seasons,
        target_per_season=target_per_season,
        existing_ids=existing_product_ids,
    )

    limit = src_cfg.get("download_limit")
    if limit and limit < len(selected_products):
        selected_products = selected_products[:limit]

    logger.info(
        f"Sentinel-2: Found {total_candidates} candidates; {len(filtered_products)} met quality filters; "
        f"{len(selected_products)} deterministically selected."
    )

    return {
        "dataset": "sentinel-2-l2a",
        "provider": "ESA Copernicus / AWS Earth Search",
        "official_source": "Copernicus Sentinel-2 MSI Level-2A",
        "stac_endpoint": stac_url,
        "filter_criteria": {
            "period": {"start": config.start_date, "end": config.end_date},
            "cloud_cover_max": cloud_max,
            "bbox": aoi_bbox,
            "processing_level": "Level-2A",
        },
        "selection_strategy": config.selection_strategy,
        "selection_parameters": {
            "target_per_season": target_per_season,
            "max_cloud_cover": cloud_max,
        },
        "seasonal_selection_summary": seasonal_summary,
        "required_bands": list(SENTINEL2_BAND_MAPPING.keys()),
        "total_candidates": total_candidates,
        "filtered_candidates_count": len(filtered_products),
        "selected_candidates_count": len(selected_products),
        "estimated_size_per_product_bytes": SENTINEL2_ESTIMATED_PRODUCT_SIZE,
        "total_estimated_selected_bytes": len(selected_products) * SENTINEL2_ESTIMATED_PRODUCT_SIZE,
        "selected_products": selected_products,
        "products": selected_products,  # Backward compatibility
        "filtered_products": filtered_products,
        "candidates_inventory": candidates_inventory,
    }


def download_sentinel2(
    config: IngestionConfig,
    search_results: Dict[str, Any],
    limit: Optional[int] = None,
    bands: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Download approved Sentinel-2 product bands idempotently with complete provenance.

    Downloads bands to:
    data/raw/sentinel2/<year>/<product_id>/<band_name>.tif
    """
    selected = search_results.get("selected_products") or search_results.get("products", [])
    max_download = limit or len(selected)
    to_download = selected[:max_download]

    # Target bands: config download_bands or bands CLI arg or all required bands
    cfg_bands = config.sources.get("sentinel2", {}).get("download_bands")
    target_bands = bands or cfg_bands or list(SENTINEL2_BAND_MAPPING.keys())

    ingested_products: List[Dict[str, Any]] = []

    for pr in to_download:
        prod_id = pr["id"]
        sel_meta = pr.get("selection_metadata", {})
        logger.info(
            f"Ingesting Sentinel-2 product: {prod_id} "
            f"(Season: {sel_meta.get('season_name', 'N/A')}, Cloud: {pr['cloud_cover']}%, Date: {pr['date']})"
        )

        prod_dir = config.get_source_raw_dir("sentinel2", f"{config.year}/{prod_id}")
        ingested_bands: Dict[str, Any] = {}

        for band_name in target_bands:
            if band_name not in SENTINEL2_BAND_MAPPING:
                continue
            if band_name not in pr.get("available_bands", {}):
                continue

            band_info = pr["available_bands"][band_name]
            dest_file = prod_dir / f"{band_name}.tif"
            url = band_info["href"]

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
                s3_uri = f"s3://climora-lake/raw/sentinel2/{config.year}/{prod_id}/{dest_file.name}"

                prov_record = build_provenance_record(
                    dataset_id="sentinel-2-l2a",
                    provider="ESA Copernicus / AWS Earth Search",
                    product="Sentinel-2 MSI Level-2A Bottom-Of-Atmosphere Reflectance",
                    version="Collection 1 (Level-2A)",
                    source="AWS Earth Search STAC API",
                    source_item_id=prod_id,
                    license_name="Copernicus Open Access / CC BY-SA 3.0 IGO",
                    access_method="Direct HTTPS COG Stream",
                    spatial_resolution="10m (B02,B03,B04,B08) / 20m (B05,B06,B07,B8A,B11,B12,SCL)",
                    temporal_resolution="5-day constellation revisit (S2A/S2B/S2C)",
                    acquisition_date=pr["date"],
                    observation_period={"start": config.start_date, "end": config.end_date},
                    aoi={"study_area": config.study_area, "bbox": pr["bbox"]},
                    cloud_cover=pr["cloud_cover"],
                    selection_strategy=sel_meta.get("selection_strategy", "seasonal_representative"),
                    selection_parameters=sel_meta.get("selection_parameters", {}),
                    required_assets=list(SENTINEL2_BAND_MAPPING.keys()),
                    local_path=rel_path,
                    file_size_bytes=file_size,
                    sha256=sha256_hash,
                    validation_status="VALID" if val.get("valid") else "INVALID",
                    s3_uri=s3_uri,
                    extra={
                        "band_name": band_name,
                        "stac_key": band_info["stac_key"],
                        "filename": dest_file.name,
                        "raster_validation": val,
                        "skipped_idempotent": skipped,
                        "selection_reason": sel_meta.get("selection_reason", ""),
                    },
                )
                ingested_bands[band_name] = prov_record

            except Exception as e:
                logger.error(f"Failed to download Sentinel-2 band {band_name} for {prod_id}: {e}")
                ingested_bands[band_name] = {
                    "band_name": band_name,
                    "status": "FAILED",
                    "error": str(e),
                }

        ingested_products.append({
            "product_id": prod_id,
            "observation_date": pr["date"],
            "cloud_cover": pr["cloud_cover"],
            "selection_metadata": sel_meta,
            "bands": ingested_bands,
            "all_valid": all(b.get("validation_status") == "VALID" or b.get("status") == "VALID" for b in ingested_bands.values()),
        })

    return ingested_products
