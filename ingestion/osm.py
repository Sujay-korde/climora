"""OpenStreetMap acquisition module for CLIMORA.

Targets:
- Pune-only geographic extraction via Overpass API
- Feature categories:
  1. Green spaces (parks, gardens, forests, woods, grasslands)
  2. Water bodies (water, waterways)
  3. Public infrastructure (hospitals, clinics, schools, universities)
  4. Road network (arterials, highways, secondary roads)
- Provenance and raw GeoJSON persistence in data/raw/osm/pune/
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from ingestion.common import calculate_sha256, create_retry_session, get_logger, validate_vector
from ingestion.config import IngestionConfig

logger = get_logger()

# Overpass API endpoints (primary and reliable fallbacks)
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Fast, indexed Overpass QL queries
OSM_QUERIES = {
    "green_spaces": """
        [out:json][timeout:90];
        (
          way["leisure"="park"]({south},{west},{north},{east});
          way["leisure"="garden"]({south},{west},{north},{east});
          way["landuse"="forest"]({south},{west},{north},{east});
          way["natural"="wood"]({south},{west},{north},{east});
          way["natural"="grassland"]({south},{west},{north},{east});
        );
        out body geom;
    """,
    "water_bodies": """
        [out:json][timeout:90];
        (
          way["natural"="water"]({south},{west},{north},{east});
          way["waterway"="river"]({south},{west},{north},{east});
          way["waterway"="stream"]({south},{west},{north},{east});
          way["waterway"="canal"]({south},{west},{north},{east});
        );
        out body geom;
    """,
    "public_infrastructure": """
        [out:json][timeout:90];
        (
          node["amenity"="hospital"]({south},{west},{north},{east});
          node["amenity"="clinic"]({south},{west},{north},{east});
          node["amenity"="school"]({south},{west},{north},{east});
          node["amenity"="university"]({south},{west},{north},{east});
          way["amenity"="hospital"]({south},{west},{north},{east});
          way["amenity"="university"]({south},{west},{north},{east});
        );
        out body geom;
    """,
    "road_network": """
        [out:json][timeout:90];
        (
          way["highway"="motorway"]({south},{west},{north},{east});
          way["highway"="trunk"]({south},{west},{north},{east});
          way["highway"="primary"]({south},{west},{north},{east});
        );
        out body geom;
    """,
}


def _osm_elements_to_geojson(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert Overpass JSON elements with geometry into GeoJSON FeatureCollection."""
    features = []
    for el in elements:
        el_type = el.get("type")
        tags = el.get("tags", {})
        el_id = el.get("id")

        geometry = None
        if el_type == "node" and "lat" in el and "lon" in el:
            geometry = {
                "type": "Point",
                "coordinates": [el["lon"], el["lat"]],
            }
        elif el_type == "way" and "geometry" in el:
            coords = [[pt["lon"], pt["lat"]] for pt in el["geometry"]]
            if len(coords) >= 4 and coords[0] == coords[-1]:
                geometry = {
                    "type": "Polygon",
                    "coordinates": [coords],
                }
            elif len(coords) >= 2:
                geometry = {
                    "type": "LineString",
                    "coordinates": coords,
                }

        if geometry:
            features.append({
                "type": "Feature",
                "id": f"{el_type}/{el_id}",
                "properties": {
                    "osm_id": el_id,
                    "osm_type": el_type,
                    **tags,
                },
                "geometry": geometry,
            })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def _execute_overpass_query(query: str, session: requests.Session) -> Optional[Dict[str, Any]]:
    """Try executing Overpass query across endpoints with failover."""
    headers = {"User-Agent": "CLIMORA-Research-Project/1.0 (Pune-Urban-Heat)"}
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            resp = session.post(
                endpoint,
                data={"data": query.strip()},
                headers=headers,
                timeout=120,
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.warning(f"Overpass {endpoint} returned status {resp.status_code}")
        except Exception as exc:
            logger.warning(f"Failed connecting to {endpoint}: {exc}")
    return None


def acquire_osm(
    config: IngestionConfig,
    aoi_bbox: List[float],  # [minx, miny, maxx, maxy] = [west, south, east, north]
    categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Extract Pune OSM feature layers via Overpass API."""
    logger.info("Acquiring OpenStreetMap vector layers for Pune AOI...")
    west_coord = aoi_bbox[0]
    south_coord = aoi_bbox[1]
    east_coord = aoi_bbox[2]
    north_coord = aoi_bbox[3]

    out_dir = config.get_source_raw_dir("osm", "pune")
    target_cats = categories or list(OSM_QUERIES.keys())

    session = create_retry_session(retries=config.download_retries)
    ingested_layers: Dict[str, Any] = {}

    for cat_name in target_cats:
        if cat_name not in OSM_QUERIES:
            continue

        dest_file = out_dir / f"{cat_name}.geojson"

        # Idempotency check: if destination file exists and is valid
        if dest_file.exists() and dest_file.stat().st_size > 0:
            val = validate_vector(dest_file)
            if val.get("valid") and val.get("feature_count", 0) > 0:
                logger.info(
                    f"[SKIP/VERIFY] OSM {cat_name} already exists ({val.get('feature_count')} features, {dest_file.stat().st_size} bytes)"
                )
                checksum = calculate_sha256(dest_file)
                rel_path = str(dest_file.relative_to(config.project_root))
                s3_uri = f"s3://climora-lake/raw/osm/pune/{dest_file.name}"
                ingested_layers[cat_name] = {
                    "dataset_id": f"osm_pune_{cat_name}",
                    "provider": "OpenStreetMap Contributors / Overpass API",
                    "product": f"OpenStreetMap Extract ({cat_name})",
                    "version": "v1.0",
                    "source": "Overpass API",
                    "source_item_id": f"pune_{cat_name}",
                    "license": "Open Data Commons Open Database License (ODbL)",
                    "access_method": "Overpass QL POST Query",
                    "spatial_resolution": "Vector (Points/Lines/Polygons)",
                    "temporal_resolution": "Snapshot",
                    "acquisition_date": "2025",
                    "observation_period": {"start": config.start_date, "end": config.end_date},
                    "AOI": {"study_area": config.study_area, "bbox": aoi_bbox},
                    "cloud_cover": None,
                    "selection_strategy": "category_extraction",
                    "selection_parameters": {"category": cat_name},
                    "required_assets": [cat_name],
                    "local_path": rel_path.replace("\\", "/"),
                    "s3_uri": s3_uri,
                    "storage_status": "local",
                    "file_size_bytes": dest_file.stat().st_size,
                    "sha256": checksum,
                    "validation_status": "VALID",
                    "file": rel_path,
                    "size_bytes": dest_file.stat().st_size,
                    "vector_validation": val,
                    "status": "VALID",
                }
                continue

        raw_query = OSM_QUERIES[cat_name].format(
            south=south_coord,
            west=west_coord,
            north=north_coord,
            east=east_coord,
        )
        logger.info(f"Querying OSM layer: {cat_name}...")

        try:
            osm_json = _execute_overpass_query(raw_query, session)
            if not osm_json:
                raise RuntimeError("All Overpass endpoints failed or timed out")

            elements = osm_json.get("elements", [])
            geojson_data = _osm_elements_to_geojson(elements)

            tmp_file = dest_file.with_suffix(".part")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, indent=2)
            if dest_file.exists():
                dest_file.unlink()
            tmp_file.rename(dest_file)

            checksum = calculate_sha256(dest_file)
            val = validate_vector(dest_file)

            logger.info(
                f"[DOWNLOADED] OSM {cat_name} ({len(geojson_data['features'])} features, {dest_file.stat().st_size} bytes)"
            )

            ingested_layers[cat_name] = {
                "file": str(dest_file.relative_to(config.project_root)),
                "sha256": checksum,
                "size_bytes": dest_file.stat().st_size,
                "vector_validation": val,
                "status": "VALID" if val.get("valid") else "INVALID",
            }

        except Exception as exc:
            logger.error(f"Error acquiring OSM {cat_name}: {exc}")
            ingested_layers[cat_name] = {
                "status": "FAILED",
                "error": str(exc),
            }

    # Write metadata manifest
    metadata_file = out_dir / "metadata.json"
    meta_content = {
        "dataset": "OpenStreetMap_Pune_Extracts",
        "provider": "OpenStreetMap Contributors / Overpass API",
        "license": "Open Data Commons Open Database License (ODbL)",
        "aoi_bbox": aoi_bbox,
        "acquisition_timestamp": datetime.now(timezone.utc).isoformat(),
        "layers": ingested_layers,
    }
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(meta_content, f, indent=2)

    return {
        "dataset": "osm_pune",
        "metadata_file": str(metadata_file.relative_to(config.project_root)),
        "layers": ingested_layers,
    }
