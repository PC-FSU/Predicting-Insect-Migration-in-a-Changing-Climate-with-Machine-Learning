"""Project configuration: data paths, species lists, and climate scenarios.

Paths default to ``/data/Maxent/...`` but can be overridden with environment
variables (see module-level constants). This keeps experiments reproducible
on the lab server while allowing local overrides for testing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

# Package root (maxent_insect_dir/)
PACKAGE_DIR: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = PACKAGE_DIR.parent
MPLSTYLE_PATH: Path = PACKAGE_DIR / "my_style.mplstyle"

# ---------------------------------------------------------------------------
# Base data roots (override with MAXENT_DATA_ROOT / MAXENT_RESULTS_ROOT)
# ---------------------------------------------------------------------------

DATA_ROOT: Path = Path(os.environ.get("MAXENT_DATA_ROOT", "/data/Maxent/data"))
RESULTS_ROOT: Path = Path(os.environ.get("MAXENT_RESULTS_ROOT", "/data/Maxent/data/results"))

PATH_TO_CLEAN_DATA: Path = DATA_ROOT / "data" / "Species_Data" / "Clean_Data"
PATH_TO_SAVE_RESULTS: Path = RESULTS_ROOT
PATH_TO_US_BOUNDARY: Path = DATA_ROOT / "data" / "US_shapefile" / "US_shapefile.shp"
PATH_TO_TEST_DATA: Path = DATA_ROOT / "data" / "Test_data" / "test.gpkg"
PATH_TO_MOST_GROWN_CROP: Path = DATA_ROOT / "data" / "crop_data" / "reproject_most_grown_crop_1_min.tif"
CROP_MAPPING_CONFIG: Path = DATA_ROOT / "data" / "crop_data" / "cdl_codes_names.csv"
# Elevation. The submitted runs used an 8-bit grayscale rendering of the National
# Atlas 100 m elevation (stanford-zz186ss2071, ~1 arc-min, values 1-248; Spearman
# rho 0.996 with WorldClim elevation). Since 13 Oct 2026 the default is the
# WorldClim 2.1 elevation in metres on the 10 arc-min climate grid, clipped and
# masked like the climate layers. MAXENT_ELEVATION=legacy restores the old layer.
_ELEV_LEGACY: Path = DATA_ROOT / "data" / "Elevation" / "stanford-zz186ss2071-geotiff.tif"
_ELEV_WORLDCLIM: Path = DATA_ROOT / "data" / "Elevation" / "wc2.1_10m_elev_clipped.tif"
PATH_TO_ELEVATION_DATA: Path = _ELEV_LEGACY if os.environ.get("MAXENT_ELEVATION", "").lower() == "legacy" else _ELEV_WORLDCLIM
SAVE_IMAGES: Path = Path(os.environ.get("MAXENT_PAPER_IMAGES", "/data/Maxent/data/paper/images"))

# Backwards-compatible aliases used by older notebooks
Crop_mapping_config = CROP_MAPPING_CONFIG
save_images = SAVE_IMAGES


def _bioclim_dir(ssp: str, period: str) -> Path:
    """Return WorldClim bioclim directory for an SSP and time period.

    Args:
        ssp: Pathway key without prefix, e.g. ``"245"`` or special for baseline.
        period: Period folder key such as ``1970_2000`` or ``2021_2040``.

    Returns:
        Absolute path to the clipped TIFF directory.
    """
    if period in {"1970_2000", "1990_2021"}:
        if period == "1970_2000":
            return DATA_ROOT / "data" / "Bioclim_worldclim_average_1970_2000" / "wc2.1_10m_bio" / "Clipped" / "In_tiff_format"
        return DATA_ROOT / "data" / "Bioclim_worldclim_average_1990_2021" / "Clipped" / "In_tiff_format"
    return (
        DATA_ROOT
        / "data"
        / f"SSP_{ssp}"
        / f"Bioclim_worldclim_average_{period}"
        / "Clipped"
        / "In_tiff_format"
    )


def _build_worldclim_config() -> Dict[str, Dict[str, Path]]:
    """Build WorldClim path tables for all SSPs and time windows.

    Returns:
        Nested mapping ``SSP -> period -> Path``.
    """
    periods = ["1970_2000", "1990_2021", "2021_2040", "2041_2060", "2061_2080", "2081_2100"]
    config: Dict[str, Dict[str, Path]] = {}
    for ssp in ("126", "245", "370", "585"):
        key = f"SSP_{ssp}"
        config[key] = {period: _bioclim_dir(ssp, period) for period in periods}
    return config


config_worldclim: Dict[str, Dict[str, Path]] = _build_worldclim_config()
config_CDS: Dict[str, Dict] = {"avgs": {}}

# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------

Insect_list: Dict[str, Path] = {
    "Brown_Marmorated_Stink_bug": PATH_TO_CLEAN_DATA
    / "Brown_Marmorated_Stink_Bug_Halyomorpha_halys_1999_2023.gpkg",
    "Corn_Earworm": PATH_TO_CLEAN_DATA / "Corn_Earworm_Helicoverpa_Zea_2004_2023.gpkg",
    "Large_Lady_Beetle": PATH_TO_CLEAN_DATA / "Large_Lady_Beetle_Harmonia_Axyridis_1995_2023.gpkg",
    # Revision (13 Oct 2026): records outside the established US range are excluded
    # from the default files. Root weevil: states where EPPO lists the species as
    # present (Florida, Texas, California, Louisiana; 1,084 of 1,107 records). Spongy moth: the 71 Washington State trap detections
    # of eradicated introductions are excluded (132 of 203 records). The complete
    # files stay available under the *_all keys for the sensitivity tables.
    "Root_Weevil": PATH_TO_CLEAN_DATA / "Root_Weevil_est_EPPO.gpkg",
    "Root_Weevil_all": PATH_TO_CLEAN_DATA / "Root_Weevil_Diaprepes_abbreviatus_2012_2023.gpkg",
    # sensitivity: the first revision filter (Florida, Texas, California only; 1,046 records)
    "Root_Weevil_FL_TX_CA": PATH_TO_CLEAN_DATA / "Root_Weevil_est_FL_TX_CA.gpkg",
    "Spongy_Moth": PATH_TO_CLEAN_DATA / "spongy_moth_est_noWA.gpkg",
    "Spongy_Moth_all": PATH_TO_CLEAN_DATA / "spongy_moth_(formerly_gypsy_moth)_(Lymantria_dispar).gpkg",
    "Spotted_Lanternfly": PATH_TO_CLEAN_DATA / "spotted_lanternfly_(Lycorma_delicatula).gpkg",
}

# Historical typo kept as an alias for existing result folders / notebooks
Insect_list["Spooted_Lanternfly"] = Insect_list["Spotted_Lanternfly"]

DEFAULT_INSECTS: List[str] = [
    "Brown_Marmorated_Stink_bug",
    "Corn_Earworm",
    "Root_Weevil",
    "Spongy_Moth",
    "Spotted_Lanternfly",
]

VALID_PATHWAYS: List[str] = list(config_worldclim.keys())

# Letters elapid understands: l linear, q quadratic, p product, h hinge, t threshold.
# "lph" is the feature set stored on the May 2025 models as
# ["linear", "hinge", "product"]. Order in the string does not matter.
FEATURE_TYPES: List[str] = ["l", "lq", "lqh", "lph", "lqhp", "lqhpt"]
# CLI defaults follow the later habitat-coverage grid, not the performance table.
DEFAULT_FEATURE_TYPES: List[str] = ["lph"]
DEFAULT_BETA_MULTIPLIERS: List[float] = [1.5]
DEFAULT_BIAS_MIX: List[float] = [0.25]

# Settings read out of the May 2025 experiment_states.pkl files that produced
# the paper's CBI/AUC-versus-m table. Beta here is 2.0. Do not substitute the
# 1.5 default above if the goal is that table.
PAPER_TABLE_FEATURE: str = "lph"
PAPER_TABLE_BETA: float = 2.0
PAPER_TABLE_BIAS_MIX: List[float] = [0.0, 0.25, 0.5, 0.75, 1.0]
PAPER_TABLE_REPEATS: int = 20
PAPER_TABLE_BACKGROUND: int = 10000
PAPER_TABLE_PATHWAY: str = "SSP_245"

dominant_crop_by_insect: Dict[str, List[int]] = {
    "Brown_Marmorated_Stink_bug": [121, 141, 122, 123, 190],
    "Corn_Earworm": [141, 1, 5, 190, 142, 176, 121, 2],
    "Large_Lady_Beetle": [123, 141, 122, 121, 176, 124, 142, 190],
    "Root_Weevil": [122, 123, 121, 190],
}

spatial_thinning_distance: Dict[str, Optional[float]] = {
    "Brown_Marmorated_Stink_bug": 10000,
    "Corn_Earworm": 10000,
    "Large_Lady_Beetle": 10000,
    "Root_Weevil": 10000,
    "Spongy_Moth": None,  # submitted runs: not thinned; the revision passes --thin-distance 10000
    "Spongy_Moth_all": None,
    "Root_Weevil_all": 10000,
    "Root_Weevil_FL_TX_CA": 10000,
    "Spotted_Lanternfly": 10000,
    "Spooted_Lanternfly": 10000,
}

BIOCLIM_MAPPING: Dict[str, str] = {
    "Bio1": "Annual Mean Temperature",
    "Bio2": "Mean Diurnal Range (Mean of monthly (max temp - min temp))",
    "Bio3": "Isothermality (BIO2/BIO7) (×100)",
    "Bio4": "Temperature Seasonality (standard deviation ×100)",
    "Bio5": "Max Temperature of Warmest Month",
    "Bio6": "Min Temperature of Coldest Month",
    "Bio7": "Temperature Annual Range (BIO5-BIO6)",
    "Bio8": "Mean Temperature of Wettest Quarter",
    "Bio9": "Mean Temperature of Driest Quarter",
    "Bio10": "Mean Temperature of Warmest Quarter",
    "Bio11": "Mean Temperature of Coldest Quarter",
    "Bio12": "Annual Precipitation",
    "Bio13": "Precipitation of Wettest Month",
    "Bio14": "Precipitation of Driest Month",
    "Bio15": "Precipitation Seasonality (Coefficient of Variation)",
    "Bio16": "Precipitation of Wettest Quarter",
    "Bio17": "Precipitation of Driest Quarter",
    "Bio18": "Precipitation of Warmest Quarter",
    "Bio19": "Precipitation of Coldest Quarter",
}

# Backwards-compatible alias
Bioclim_mapping = BIOCLIM_MAPPING

# cloglog prevalence prior (elapid's MaxentModel.tau), not the habitat-suitability
# cutoff of 0.5 used when counting "suitable" pixels in the coverage tables.
# Root weevil and spongy moth are intentionally lower. The May 2025 stink-bug
# states stored tau 0.5, which matches this map.
tau: Dict[str, float] = {
    "Brown_Marmorated_Stink_bug": 0.5,
    "Corn_Earworm": 0.5,
    "Large_Lady_Beetle": 0.5,
    "Root_Weevil": 0.1,
    "Root_Weevil_all": 0.1,
    "Root_Weevil_FL_TX_CA": 0.1,
    "Spongy_Moth": 0.1,
    "Spongy_Moth_all": 0.1,
    "Spotted_Lanternfly": 0.5,
    "Spooted_Lanternfly": 0.5,
}
