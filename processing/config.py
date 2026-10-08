"""CLIMORA Phase 1A.8 Processing Configuration & Constants.

Defines:
- Directory paths for raw, processed, and derived assets
- Approved canonical temporal baseline targets (2021-2025)
- Official USGS Landsat Collection 2 Level-2 scaling coefficients
- Landsat QA_PIXEL and QA_RADSAT bit definitions
- MODIS MOD11A2 v061 scaling coefficients and QA definitions
- NASA POWER meteorological parameter definitions and units
- GeoTIFF compression profiles
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Base data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DERIVED_DIR = DATA_DIR / "derived"
AOI_PATH = DATA_DIR / "aoi" / "pune.geojson"
MANIFESTS_DIR = DATA_DIR / "manifests"

# Processing Version
PROCESSING_VERSION = "1.0.0"
PROCESSING_PHASE = "1A.8"

# Canonical Temporal Baseline Targets (Phase 1A.7.1 Amendment A1 approved)
CANONICAL_TARGET_DOY = 105
PREFERRED_WINDOW: Tuple[int, int] = (95, 115)
FALLBACK_WINDOW: Tuple[int, int] = (90, 120)
HARD_MAX_OFFSET_DAYS = 15

LANDSAT_TEMPORAL_BASELINE = [
    {
        "year": 2021,
        "scene_id": "LC08_L2SP_147047_20210424_02_T1",
        "platform": "Landsat 8",
        "sensor": "OLI/TIRS",
        "collection": "landsat-c2-l2",
        "processing_level": "Collection 2 Level-2",
        "date": "2021-04-24",
        "doy": 114,
        "offset_days": 9,
        "path_row": "147/047",
        "cloud_pct_stac": 0.88,
        "cloud_pct_aoi": 0.00,
        "shadow_pct_aoi": 0.00,
    },
    {
        "year": 2022,
        "scene_id": "LC08_L2SP_147047_20220411_02_T1",
        "platform": "Landsat 8",
        "sensor": "OLI/TIRS",
        "collection": "landsat-c2-l2",
        "processing_level": "Collection 2 Level-2",
        "date": "2022-04-11",
        "doy": 101,
        "offset_days": 4,
        "path_row": "147/047",
        "cloud_pct_stac": 15.21,
        "cloud_pct_aoi": 1.71,
        "shadow_pct_aoi": 3.22,
    },
    {
        "year": 2023,
        "scene_id": "LC09_L2SP_147047_20230422_02_T1",
        "platform": "Landsat 9",
        "sensor": "OLI-2/TIRS-2",
        "collection": "landsat-c2-l2",
        "processing_level": "Collection 2 Level-2",
        "date": "2023-04-22",
        "doy": 112,
        "offset_days": 7,
        "path_row": "147/047",
        "cloud_pct_stac": 0.09,
        "cloud_pct_aoi": 0.00,
        "shadow_pct_aoi": 0.03,
    },
    {
        "year": 2024,
        "scene_id": "LC08_L2SP_147047_20240416_02_T1",
        "platform": "Landsat 8",
        "sensor": "OLI/TIRS",
        "collection": "landsat-c2-l2",
        "processing_level": "Collection 2 Level-2",
        "date": "2024-04-16",
        "doy": 107,
        "offset_days": 2,
        "path_row": "147/047",
        "cloud_pct_stac": 4.01,
        "cloud_pct_aoi": 0.00,
        "shadow_pct_aoi": 0.00,
    },
    {
        "year": 2025,
        "scene_id": "LC08_L2SP_147047_20250419_02_T1",
        "platform": "Landsat 8",
        "sensor": "OLI/TIRS",
        "collection": "landsat-c2-l2",
        "processing_level": "Collection 2 Level-2",
        "date": "2025-04-19",
        "doy": 109,
        "offset_days": 4,
        "path_row": "147/047",
        "cloud_pct_stac": 0.35,
        "cloud_pct_aoi": 0.00,
        "shadow_pct_aoi": 0.00,
    },
]

# Landsat Collection 2 Level-2 Scaling Parameters (USGS Official)
LANDSAT_SR_SCALE = 0.0000275
LANDSAT_SR_OFFSET = -0.2
LANDSAT_ST_SCALE = 0.00341802
LANDSAT_ST_OFFSET = 149.0  # Kelvin

LANDSAT_REQUIRED_BANDS = [
    "SR_B2",
    "SR_B3",
    "SR_B4",
    "SR_B5",
    "SR_B6",
    "SR_B7",
    "ST_B10",
    "QA_PIXEL",
    "QA_RADSAT",
]

# Landsat QA_PIXEL bit masks
QA_PIXEL_BITS = {
    "fill": 0,           # Bit 0: Fill (1 = fill)
    "dilated_cloud": 1,  # Bit 1: Dilated Cloud
    "cirrus": 2,         # Bit 2: Cirrus
    "cloud": 3,          # Bit 3: Cloud
    "cloud_shadow": 4,   # Bit 4: Cloud Shadow
    "snow": 5,           # Bit 5: Snow
    "clear": 6,          # Bit 6: Clear (1 = clear)
    "water": 7,          # Bit 7: Water (1 = water)
}

# Landsat QA_RADSAT radiometric saturation mask for bands 2-7 and 10
# Bit 1: B2, Bit 2: B3, Bit 3: B4, Bit 4: B5, Bit 5: B6, Bit 6: B7, Bit 9: B10
QA_RADSAT_RELEVANT_MASK = (
    (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5) | (1 << 6) | (1 << 9)
)

# Deterministic Quality Mask Class Values (uint8)
QA_CLASS_FILL_NODATA = 0
QA_CLASS_VALID_CLEAR = 1
QA_CLASS_CLOUD = 2
QA_CLASS_CLOUD_SHADOW = 3
QA_CLASS_DILATED_CLOUD = 4
QA_CLASS_CIRRUS = 5
QA_CLASS_SATURATED = 6
QA_CLASS_SNOW_ICE = 7

QA_CLASS_NAMES = {
    QA_CLASS_FILL_NODATA: "FILL_NODATA",
    QA_CLASS_VALID_CLEAR: "VALID_CLEAR",
    QA_CLASS_CLOUD: "CLOUD",
    QA_CLASS_CLOUD_SHADOW: "CLOUD_SHADOW",
    QA_CLASS_DILATED_CLOUD: "DILATED_CLOUD",
    QA_CLASS_CIRRUS: "CIRRUS",
    QA_CLASS_SATURATED: "SATURATED",
    QA_CLASS_SNOW_ICE: "SNOW_ICE",
}

# MODIS MOD11A2 v061 Scaling (LP DAAC Official)
MODIS_LST_SCALE = 0.02  # Kelvin
MODIS_LST_OFFSET = 0.0
MODIS_REQUIRED_LAYERS = ["LST_Day_1km", "LST_Night_1km", "QC_Day", "QC_Night"]

# NASA POWER Daily Variables
NASA_POWER_VARIABLES = {
    "T2M": {"unit": "°C", "longname": "Temperature at 2 Meters"},
    "T2M_MAX": {"unit": "°C", "longname": "Temperature at 2 Meters Maximum"},
    "T2M_MIN": {"unit": "°C", "longname": "Temperature at 2 Meters Minimum"},
    "RH2M": {"unit": "%", "longname": "Relative Humidity at 2 Meters"},
    "WS10M": {"unit": "m/s", "longname": "Wind Speed at 10 Meters"},
    "PRECTOTCORR": {"unit": "mm/day", "longname": "Precipitation Corrected"},
    "ALLSKY_SFC_SW_DWN": {"unit": "MJ/m^2/day", "longname": "All Sky Surface Downward Irradiance"},
}

# GeoTIFF creation options for compact, high-performance compressed rasters
TIFF_FLOAT_PROFILE = {
    "driver": "GTiff",
    "dtype": "float32",
    "nodata": float("nan"),
    "compress": "deflate",
    "predictor": 3,  # Floating point predictor
    "tiled": True,
    "blockxsize": 256,
    "blockysize": 256,
}

TIFF_UINT8_PROFILE = {
    "driver": "GTiff",
    "dtype": "uint8",
    "nodata": 0,
    "compress": "deflate",
    "predictor": 2,  # Horizontal differencing
    "tiled": True,
    "blockxsize": 256,
    "blockysize": 256,
}

TIFF_UINT16_PROFILE = {
    "driver": "GTiff",
    "dtype": "uint16",
    "nodata": 0,
    "compress": "deflate",
    "predictor": 2,
    "tiled": True,
    "blockxsize": 256,
    "blockysize": 256,
}
