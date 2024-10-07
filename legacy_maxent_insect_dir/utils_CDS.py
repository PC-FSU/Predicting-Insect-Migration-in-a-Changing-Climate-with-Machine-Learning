# Common Imports
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import pathlib
import os
import rasterio
import numpy as np
import xarray as xr
import warnings
from typing import Dict, List, Union

from MaxEnt_insect_dir.maxent_insect_dir.config import *
from MaxEnt_insect_dir.maxent_insect_dir.utils_common import *

# Suppress pandas chain assignment warning
pd.options.mode.chained_assignment = None  # default='warn'


# ============================================================
# Function 3: Load Bioclimatic Data from NetCDF Files
# ============================================================

def load_bioclim_data(climate_data_path: str) -> List[Dict[str, xr.Dataset], np.ndarray, np.ndarray]:
    """
    Loads bioclimatic data from .nc files in the specified directory.

    Parameters:
    -----------
    climate_data_path : str
        Path to directory containing .nc files.

    Returns:
    --------
    bioclim_data_dict : dict
        Dictionary of xarray Datasets, keyed by variable name.
    bioclim_lats : np.ndarray
        Array of latitude values from the datasets.
    bioclim_lons : np.ndarray
        Array of longitude values from the datasets.
    """
    netcdf_files = sorted([f for f in os.listdir(climate_data_path) if f.endswith('.nc')])
    bioclim_data_dict = {}
    bioclim_lats = None
    bioclim_lons = None

    for idx, nc_file in enumerate(netcdf_files):
        file_path = os.path.join(climate_data_path, nc_file)
        dataset = xr.open_dataset(file_path)
        variable_name = list(dataset.data_vars)[0]  # Assuming each file has one variable
        bioclim_data_dict[variable_name] = dataset

        if idx == 0:
            # Get latitude and longitude arrays
            bioclim_lats = dataset['latitude'].values
            bioclim_lons = dataset['longitude'].values

        print(f"Loaded {variable_name} from {file_path}")

    return bioclim_data_dict, bioclim_lats, bioclim_lons

# ============================================================
# Function 4: Extract Bioclimatic Values at Point Locations
# ============================================================

def extract_bioclim_values_at_points(
    insect_data: gpd.GeoDataFrame,
    bioclim_data_dict: Dict[str, xr.Dataset],
    bioclim_lats: np.ndarray,
    bioclim_lons: np.ndarray,
    id_column: str
) -> gpd.GeoDataFrame:
    """
    Extracts bioclimatic values from datasets at the locations and years specified
    in the insect_data and adds them as columns.

    Parameters:
    -----------
    insect_data : GeoDataFrame
        GeoDataFrame containing point geometries and 'year' column.
    bioclim_data_dict : dict
        Dictionary of xarray Datasets keyed by variable name.
    bioclim_lats : np.ndarray
        Array of latitude values from the datasets.
    bioclim_lons : np.ndarray
        Array of longitude values from the datasets.
    id_column : str
        Column name in insect_data that uniquely identifies each point.

    Returns:
    --------
    GeoDataFrame
        Updated GeoDataFrame with bioclimatic variable columns added.
    """
    # Initialize bioclimatic variables in insect_data
    for variable_name in bioclim_data_dict.keys():
        insect_data[variable_name] = np.nan  # Initialize with NaNs

    # Group the insect data by 'year'
    grouped = insect_data.groupby('year')

    for year, group in grouped:
        sample_count = group[id_column].count()
        time_idx = year - 1950  # Adjust based on the time dimension in datasets

        print(f'Processing {sample_count} samples for the year {year}...')

        for idx, row in group.iterrows():
            longitude, latitude = row.geometry.x, row.geometry.y

            for variable_name, bioclim_data in bioclim_data_dict.items():
                # Validate the year
                dataset_year = bioclim_data['time'].dt.year[time_idx].item()
                if year != dataset_year:
                    raise ValueError(f"Year mismatch: insect data year {year}, bioclim data year {dataset_year}")

                # Find nearest indices
                lat_idx = np.abs(bioclim_lats - latitude).argmin()
                lon_idx = np.abs(bioclim_lons - longitude).argmin()

                # Extract the value
                bioclim_value = bioclim_data.isel(
                    time=time_idx, latitude=lat_idx, longitude=lon_idx
                )[variable_name].values.item()

                # Update the value in insect_data
                insect_data.at[idx, variable_name] = bioclim_value

    return insect_data

# ============================================================
# Main Function: Merge Insect Data with Bioclimatic Variables
# ============================================================

def bioclim_insect_intersection(
    climate_data_path: str,
    insect_crop_data: gpd.GeoDataFrame,
    id_column: str
) -> gpd.GeoDataFrame:
    """
    Merges insect_crop_data with bioclimatic variables extracted from NetCDF files.

    Parameters:
    -----------
    climate_data_path : str
        Path to directory containing .nc files with bioclimatic data.
    insect_crop_data : GeoDataFrame
        GeoDataFrame containing insect data with 'geometry' and 'year' columns.
    id_column : str
        Column name in insect_crop_data that uniquely identifies each point.

    Returns:
    --------
    GeoDataFrame
        Updated GeoDataFrame with bioclimatic variable columns added.
    """
    # Load bioclimatic data
    bioclim_data_dict, bioclim_lats, bioclim_lons = load_bioclim_data(climate_data_path)

    # Extract bioclimatic values at insect locations
    insect_crop_data = extract_bioclim_values_at_points(
        insect_data=insect_crop_data,
        bioclim_data_dict=bioclim_data_dict,
        bioclim_lats=bioclim_lats,
        bioclim_lons=bioclim_lons,
        id_column=id_column
    )

    return insect_crop_data
