"""Derived Landsat Physical Indices Engine for CLIMORA Phase 1A.8.

Calculates:
1. Normalized Difference Vegetation Index (NDVI):
   NDVI = (NIR - RED) / (NIR + RED) = (SR_B5 - SR_B4) / (SR_B5 + SR_B4)
2. Normalized Difference Built-Up Index (NDBI):
   NDBI = (SWIR1 - NIR) / (SWIR1 + NIR) = (SR_B6 - SR_B5) / (SR_B6 + SR_B5)
3. Land Surface Temperature (LST):
   Official Landsat Collection 2 Level-2 Surface Temperature:
   LST_Kelvin = ST_B10 * 0.00341802 + 149.0
   LST_Celsius = LST_Kelvin - 273.15

Features:
- Valid-pixel masking applied before calculation (clouds, shadows, saturated, fill excluded)
- Zero/negative denominator handling with explicit NaN assignment
- Mathematical range bounding [-1.0, 1.0] for normalized indices
- Physical unit tracking and summary statistics
"""

from __future__ import annotations

from typing import Any, Dict, Tuple
import numpy as np

from processing.config import LANDSAT_ST_OFFSET, LANDSAT_ST_SCALE


def compute_ndvi(
    sr_b4: np.ndarray,
    sr_b5: np.ndarray,
    valid_mask: np.ndarray,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Compute NDVI from scaled surface reflectance RED (B4) and NIR (B5).

    Args:
        sr_b4: 2D float32 array of scaled Surface Reflectance Band 4 (RED)
        sr_b5: 2D float32 array of scaled Surface Reflectance Band 5 (NIR)
        valid_mask: 2D boolean mask where True indicates valid clear observation

    Returns:
        (ndvi_array, metrics_dict)
    """
    ndvi = np.full(sr_b4.shape, np.nan, dtype=np.float32)

    # Condition: valid mask AND positive reflectance in denominator
    denom = sr_b5 + sr_b4
    compute_mask = valid_mask & np.isfinite(sr_b4) & np.isfinite(sr_b5) & (denom > 1e-6)

    with np.errstate(divide="ignore", invalid="ignore"):
        raw_ndvi = (sr_b5 - sr_b4) / denom
        # Constrain to physically meaningful mathematical bounds [-1.0, 1.0]
        clipped_ndvi = np.clip(raw_ndvi, -1.0, 1.0)
        ndvi[compute_mask] = clipped_ndvi[compute_mask].astype(np.float32)

    valid_vals = ndvi[np.isfinite(ndvi)]
    metrics = {
        "index": "NDVI",
        "formula": "(SR_B5 - SR_B4) / (SR_B5 + SR_B4)",
        "bands_used": ["SR_B4 (RED)", "SR_B5 (NIR)"],
        "valid_count": int(valid_vals.size),
        "min": float(np.nanmin(valid_vals)) if valid_vals.size > 0 else None,
        "max": float(np.nanmax(valid_vals)) if valid_vals.size > 0 else None,
        "mean": float(np.nanmean(valid_vals)) if valid_vals.size > 0 else None,
        "std": float(np.nanstd(valid_vals)) if valid_vals.size > 0 else None,
        "units": "dimensionless [-1.0, 1.0]",
    }
    return ndvi, metrics


def compute_ndbi(
    sr_b5: np.ndarray,
    sr_b6: np.ndarray,
    valid_mask: np.ndarray,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Compute NDBI from scaled surface reflectance NIR (B5) and SWIR1 (B6).

    Args:
        sr_b5: 2D float32 array of scaled Surface Reflectance Band 5 (NIR)
        sr_b6: 2D float32 array of scaled Surface Reflectance Band 6 (SWIR1)
        valid_mask: 2D boolean mask where True indicates valid clear observation

    Returns:
        (ndbi_array, metrics_dict)
    """
    ndbi = np.full(sr_b5.shape, np.nan, dtype=np.float32)

    denom = sr_b6 + sr_b5
    compute_mask = valid_mask & np.isfinite(sr_b5) & np.isfinite(sr_b6) & (denom > 1e-6)

    with np.errstate(divide="ignore", invalid="ignore"):
        raw_ndbi = (sr_b6 - sr_b5) / denom
        clipped_ndbi = np.clip(raw_ndbi, -1.0, 1.0)
        ndbi[compute_mask] = clipped_ndbi[compute_mask].astype(np.float32)

    valid_vals = ndbi[np.isfinite(ndbi)]
    metrics = {
        "index": "NDBI",
        "formula": "(SR_B6 - SR_B5) / (SR_B6 + SR_B5)",
        "bands_used": ["SR_B5 (NIR)", "SR_B6 (SWIR1)"],
        "valid_count": int(valid_vals.size),
        "min": float(np.nanmin(valid_vals)) if valid_vals.size > 0 else None,
        "max": float(np.nanmax(valid_vals)) if valid_vals.size > 0 else None,
        "mean": float(np.nanmean(valid_vals)) if valid_vals.size > 0 else None,
        "std": float(np.nanstd(valid_vals)) if valid_vals.size > 0 else None,
        "units": "dimensionless [-1.0, 1.0]",
    }
    return ndbi, metrics


def compute_lst(
    st_b10_dn: np.ndarray,
    valid_mask: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Convert Landsat Collection 2 Level-2 ST_B10 raw DN to physical temperature in Kelvin and Celsius.

    Official USGS Collection 2 Level-2 scaling:
    LST_Kelvin = DN * 0.00341802 + 149.0
    LST_Celsius = LST_Kelvin - 273.15

    Args:
        st_b10_dn: 2D array of ST_B10 raw digital numbers (uint16)
        valid_mask: 2D boolean mask of valid clear pixels

    Returns:
        (lst_kelvin_array, lst_celsius_array, metrics_dict)
    """
    lst_k = np.full(st_b10_dn.shape, np.nan, dtype=np.float32)
    lst_c = np.full(st_b10_dn.shape, np.nan, dtype=np.float32)

    # Valid condition: non-zero DN and valid clear mask
    compute_mask = valid_mask & (st_b10_dn > 0)

    # Calculate physical temperatures
    kelvin_vals = (st_b10_dn.astype(np.float32) * LANDSAT_ST_SCALE) + LANDSAT_ST_OFFSET
    celsius_vals = kelvin_vals - 273.15

    lst_k[compute_mask] = kelvin_vals[compute_mask]
    lst_c[compute_mask] = celsius_vals[compute_mask]

    valid_k = lst_k[np.isfinite(lst_k)]
    valid_c = lst_c[np.isfinite(lst_c)]

    metrics = {
        "parameter": "Land Surface Temperature (LST)",
        "source_band": "ST_B10",
        "scale_factor": LANDSAT_ST_SCALE,
        "add_offset": LANDSAT_ST_OFFSET,
        "reference": "USGS Landsat Collection 2 Level-2 Surface Temperature Guide",
        "valid_count": int(valid_k.size),
        "kelvin": {
            "units": "Kelvin (K)",
            "min": float(np.nanmin(valid_k)) if valid_k.size > 0 else None,
            "max": float(np.nanmax(valid_k)) if valid_k.size > 0 else None,
            "mean": float(np.nanmean(valid_k)) if valid_k.size > 0 else None,
            "std": float(np.nanstd(valid_k)) if valid_k.size > 0 else None,
        },
        "celsius": {
            "units": "Degrees Celsius (°C)",
            "min": float(np.nanmin(valid_c)) if valid_c.size > 0 else None,
            "max": float(np.nanmax(valid_c)) if valid_c.size > 0 else None,
            "mean": float(np.nanmean(valid_c)) if valid_c.size > 0 else None,
            "std": float(np.nanstd(valid_c)) if valid_c.size > 0 else None,
        },
    }
    return lst_k, lst_c, metrics
