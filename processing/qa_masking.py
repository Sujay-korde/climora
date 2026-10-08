"""QA_PIXEL & QA_RADSAT deterministic masking engine for Landsat Collection 2 Level-2.

Preserves explicit distinctions between:
- Valid clear observation (land or water)
- Cloud masked pixel
- Cloud shadow masked pixel
- Dilated cloud masked pixel
- Cirrus masked pixel
- Saturated pixel (QA_RADSAT)
- Fill / No-data pixel

Produces:
1. Deterministic uint8 classification raster (0..7)
2. Boolean clean valid pixel mask (True for clean, False for any invalid condition)
3. Machine-readable audit dictionary of pixel counts, percentages, and logic documentation
"""

from __future__ import annotations

from typing import Any, Dict, Tuple
import numpy as np

from processing.config import (
    QA_CLASS_CIRRUS,
    QA_CLASS_CLOUD,
    QA_CLASS_CLOUD_SHADOW,
    QA_CLASS_DILATED_CLOUD,
    QA_CLASS_FILL_NODATA,
    QA_CLASS_NAMES,
    QA_CLASS_SATURATED,
    QA_CLASS_SNOW_ICE,
    QA_CLASS_VALID_CLEAR,
    QA_PIXEL_BITS,
    QA_RADSAT_RELEVANT_MASK,
)


def get_mask_logic_specification() -> Dict[str, Any]:
    """Return machine-readable documentation of the QA masking logic."""
    return {
        "standard": "USGS Landsat Collection 2 Level-2 QA_PIXEL & QA_RADSAT Specifications",
        "qa_pixel_bit_definitions": {
            "bit_0": "Fill (1 = fill / nodata)",
            "bit_1": "Dilated Cloud (1 = dilated cloud)",
            "bit_2": "Cirrus (1 = high confidence cirrus)",
            "bit_3": "Cloud (1 = high confidence cloud)",
            "bit_4": "Cloud Shadow (1 = high confidence cloud shadow)",
            "bit_5": "Snow/Ice (1 = snow/ice)",
            "bit_6": "Clear (1 = clear land or water, no cloud/shadow/cirrus)",
            "bit_7": "Water (1 = water body)",
            "bits_8_9": "Cloud Confidence (00=None, 01=Low, 10=Medium, 11=High)",
            "bits_10_11": "Cloud Shadow Confidence (00=None, 01=Low, 10=Reserved, 11=High)",
            "bits_12_13": "Snow/Ice Confidence (00=None, 01=Low, 10=Reserved, 11=High)",
            "bits_14_15": "Cirrus Confidence (00=None, 01=Low, 10=Reserved, 11=High)",
        },
        "qa_radsat_saturation_mask": {
            "evaluated_bands": ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10"],
            "bit_mask": QA_RADSAT_RELEVANT_MASK,
            "description": "Bitmask selecting saturation in visible, NIR, SWIR, and thermal bands",
        },
        "classification_hierarchy": [
            {"code": QA_CLASS_FILL_NODATA, "name": "FILL_NODATA", "rule": "qa_pixel & 1 != 0 or raw_dn == 0 or nodata"},
            {"code": QA_CLASS_SATURATED, "name": "SATURATED", "rule": "qa_radsat & relevant_mask != 0 (non-fill)"},
            {"code": QA_CLASS_CLOUD, "name": "CLOUD", "rule": "qa_pixel & (1 << 3) != 0 (non-fill)"},
            {"code": QA_CLASS_CLOUD_SHADOW, "name": "CLOUD_SHADOW", "rule": "qa_pixel & (1 << 4) != 0 (non-fill)"},
            {"code": QA_CLASS_DILATED_CLOUD, "name": "DILATED_CLOUD", "rule": "qa_pixel & (1 << 1) != 0 (non-fill)"},
            {"code": QA_CLASS_CIRRUS, "name": "CIRRUS", "rule": "qa_pixel & (1 << 2) != 0 (non-fill)"},
            {"code": QA_CLASS_SNOW_ICE, "name": "SNOW_ICE", "rule": "qa_pixel & (1 << 5) != 0 (non-fill)"},
            {"code": QA_CLASS_VALID_CLEAR, "name": "VALID_CLEAR", "rule": "non-fill, clear, uncorrupted, un-saturated"},
        ],
        "valid_clear_definition": "A pixel is valid clear iff it is non-fill, not cloud, not cloud shadow, not dilated cloud, not cirrus, and not radiometrically saturated.",
    }


def evaluate_landsat_quality_masks(
    qa_pixel: np.ndarray,
    qa_radsat: np.ndarray,
    aoi_boundary_mask: np.ndarray | None = None,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Generate quality classification raster and boolean valid mask from QA_PIXEL and QA_RADSAT.

    Args:
        qa_pixel: 2D uint16 numpy array of QA_PIXEL values
        qa_radsat: 2D uint16 numpy array of QA_RADSAT values
        aoi_boundary_mask: Optional boolean 2D mask (True inside statutory AOI polygon)

    Returns:
        (classification_raster, boolean_valid_clear_mask, metrics_dict)
    """
    if qa_pixel.shape != qa_radsat.shape:
        raise ValueError(
            f"Shape mismatch: QA_PIXEL {qa_pixel.shape} != QA_RADSAT {qa_radsat.shape}"
        )

    # 1. Fill / Nodata condition
    # Bit 0 of QA_PIXEL is Fill; value 1 or 0 is also treated as nodata
    is_fill = (
        (qa_pixel == 0)
        | (qa_pixel == 1)
        | ((qa_pixel & (1 << QA_PIXEL_BITS["fill"])) != 0)
    )
    if aoi_boundary_mask is not None:
        is_fill = is_fill | (~aoi_boundary_mask)

    # 2. Quality flags (evaluated only on non-fill pixels)
    non_fill = ~is_fill

    is_cloud = non_fill & ((qa_pixel & (1 << QA_PIXEL_BITS["cloud"])) != 0)
    is_shadow = non_fill & ((qa_pixel & (1 << QA_PIXEL_BITS["cloud_shadow"])) != 0)
    is_dilated = non_fill & ((qa_pixel & (1 << QA_PIXEL_BITS["dilated_cloud"])) != 0)
    is_cirrus = non_fill & ((qa_pixel & (1 << QA_PIXEL_BITS["cirrus"])) != 0)
    is_snow = non_fill & ((qa_pixel & (1 << QA_PIXEL_BITS["snow"])) != 0)

    # 3. Radiometric Saturation (QA_RADSAT)
    is_saturated = non_fill & ((qa_radsat & QA_RADSAT_RELEVANT_MASK) != 0)

    # 4. Strict Valid Clear Pixels: non-fill AND NOT (cloud or shadow or dilated or cirrus or sat)
    is_valid_clear = (
        non_fill
        & (~is_cloud)
        & (~is_shadow)
        & (~is_dilated)
        & (~is_cirrus)
        & (~is_snow)
        & (~is_saturated)
    )

    # 5. Build deterministic uint8 classification raster
    # Precedence hierarchy:
    # 0 = FILL_NODATA
    # 1 = VALID_CLEAR
    # 2 = CLOUD
    # 3 = CLOUD_SHADOW
    # 4 = DILATED_CLOUD
    # 5 = CIRRUS
    # 6 = SATURATED
    # 7 = SNOW_ICE
    classification = np.full(qa_pixel.shape, QA_CLASS_FILL_NODATA, dtype=np.uint8)

    # Assign in reverse precedence so higher precedence overrides
    classification[is_valid_clear] = QA_CLASS_VALID_CLEAR
    classification[is_snow] = QA_CLASS_SNOW_ICE
    classification[is_cirrus] = QA_CLASS_CIRRUS
    classification[is_dilated] = QA_CLASS_DILATED_CLOUD
    classification[is_shadow] = QA_CLASS_CLOUD_SHADOW
    classification[is_cloud] = QA_CLASS_CLOUD
    classification[is_saturated] = QA_CLASS_SATURATED
    classification[is_fill] = QA_CLASS_FILL_NODATA

    # 6. Calculate comprehensive quality metrics
    total_raster_pixels = int(qa_pixel.size)
    aoi_internal_pixels = int(np.count_nonzero(non_fill))

    def _pct(count: int) -> float:
        return round((count / aoi_internal_pixels) * 100.0, 4) if aoi_internal_pixels > 0 else 0.0

    valid_clear_count = int(np.count_nonzero(is_valid_clear))
    cloud_count = int(np.count_nonzero(is_cloud))
    shadow_count = int(np.count_nonzero(is_shadow))
    dilated_count = int(np.count_nonzero(is_dilated))
    cirrus_count = int(np.count_nonzero(is_cirrus))
    saturated_count = int(np.count_nonzero(is_saturated))
    fill_count = int(np.count_nonzero(is_fill))

    metrics = {
        "raster_dimensions": list(qa_pixel.shape),
        "total_raster_pixels": total_raster_pixels,
        "aoi_internal_pixels": aoi_internal_pixels,
        "valid_clear_pixels": valid_clear_count,
        "valid_clear_pct": _pct(valid_clear_count),
        "cloud_pixels": cloud_count,
        "cloud_pct": _pct(cloud_count),
        "shadow_pixels": shadow_count,
        "shadow_pct": _pct(shadow_count),
        "dilated_cloud_pixels": dilated_count,
        "dilated_cloud_pct": _pct(dilated_count),
        "cirrus_pixels": cirrus_count,
        "cirrus_pct": _pct(cirrus_count),
        "saturated_pixels": saturated_count,
        "saturated_pct": _pct(saturated_count),
        "fill_nodata_pixels": fill_count,
        "qa_logic": get_mask_logic_specification(),
    }

    return classification, is_valid_clear, metrics
