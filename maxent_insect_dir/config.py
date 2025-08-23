"""
Configuration file for paths and parameters used in the MaxEnt insect project.

This file centralizes references to data sources, output directories,
and experimental settings (e.g., thinning distance, crop codes).
"""

import os
from pathlib import Path

# ================================================================================================
# Base paths
# ================================================================================================

# Base directory = repository root (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parents[1]
BASE_DIR_STR = str(BASE_DIR)   # used with os.path.join below

# Directory containing cleaned species occurrence data
# (Non-US points and outliers removed)
PATH_TO_CLEAN_DATA = os.path.join(BASE_DIR_STR, "dummy_data", "species_data")

# Directory where model outputs and results are saved
PATH_TO_SAVE_RESULTS = os.path.join(BASE_DIR_STR, "dummy_results")

# US boundary shapefile
PATH_TO_US_BOUNDARY = os.path.join(BASE_DIR_STR, "dummy_data", "us_shapefile", "US_shapefile.shp")

# Test dataset
PATH_TO_TEST_DATA = os.path.join(BASE_DIR_STR, "dummy_data", "test_data", "test.gpkg")


# ================================================================================================
# Insect data configuration
# ================================================================================================

insect_data = {
    "Corn_Earworm": os.path.join(PATH_TO_CLEAN_DATA, "corn_earworm_subset.gpkg"),
    "Large_Lady_Beetle": None,
    "Root_Weevil": None,
    "Spongy_Moth": None,
    "Spooted_Lanternfly": None,
    "Brown_Marmorated_Stink_bug": None,
}


# ================================================================================================
# Crop data configuration
# ================================================================================================

# Most grown crop raster file (reprojected, 1-minute resolution)
PATH_TO_MOST_GROWN_CROP = os.path.join(
    BASE_DIR_STR, "dummy_data", "crop_data", "avg_crop_layer", "reproject_most_grown_crop_1_min.tif"
)

# CSV mapping CDL codes to crop names
CROP_MAPPING_CONFIG = os.path.join(BASE_DIR_STR, "dummy_data", "crop_data", "cdl_codes_names.csv")

# Crop codes (CDL) associated with insects
dominant_crop_by_insect = {
    "Brown_Marmorated_Stink_bug": [121, 141, 122, 123, 190],
    "Corn_Earworm": [141, 1, 5, 190, 142, 176, 121, 2],
    "Large_Lady_Beetle": [123, 141, 122, 121, 176, 124, 142, 190],
    "Root_Weevil": [122, 123, 121, 190],
}


# ================================================================================================
# Climate data configuration
# ================================================================================================

config_worldclim = {
    "SSP_245": {
        "1970_2000": os.path.join(BASE_DIR_STR, "dummy_data", "climate_data", "SSP_245", "1970_2000", "In_tiff_format"),
        "2021_2040": os.path.join(BASE_DIR_STR, "dummy_data", "climate_data", "SSP_245", "2021_2040", "In_tiff_format"),
        "2041_2060": os.path.join(BASE_DIR_STR, "dummy_data", "climate_data", "SSP_245", "2041_2060", "In_tiff_format"),
    }
}


# ================================================================================================
# Elevation data
# ================================================================================================

PATH_TO_ELEVATION_DATA = os.path.join(
    BASE_DIR_STR, "dummy_data", "elevation", "stanford-zz186ss2071-geotiff.tif"
)


# ================================================================================================
# Experiment configuration
# ================================================================================================

# Minimum spatial thinning distance per insect (in meters)
spatial_thinning_distance = {
    "Brown_Marmorated_Stink_bug": 10000,
    "Corn_Earworm": 10000,
    "Large_Lady_Beetle": 10000,
    "Brown_Marmorated_Stink_bug_2": 10000,
    "Root_Weevil": 10000,
    "Spongy_Moth": None,  # Points are already well dispersed
    "Spooted_Lanternfly": 10000,
}


# ================================================================================================
# Bioclimatic variable mapping
# ================================================================================================

bioclim_mapping = {
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


# ================================================================================================
# Prevalence factors (tau)
# ================================================================================================

tau = {
    "Brown_Marmorated_Stink_bug": 0.5,
    "Corn_Earworm": 0.5,
    "Large_Lady_Beetle": 0.5,
    "Root_Weevil": 0.1,
    "Spongy_Moth": 0.1,
    "Spooted_Lanternfly": 0.5,
}


# ================================================================================================
# Paths for saving figures (e.g., for papers)
# ================================================================================================

PATH_TO_SAVE_IMAGES = os.path.join(BASE_DIR_STR, "data", "paper", "images")
