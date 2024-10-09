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

from maxent_insect_dir.config import *
from maxent_insect_dir.utils_common import *

# Suppress pandas chain assignment warning
pd.options.mode.chained_assignment = None  # default='warn'



def load_netcdf_files(climate_data_path: str):
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


# Function: Extract Bioclimatic Values at Point Locations
def extract_bioclim_values_at_points_as_timeseries(
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

        # Process each point in the group
        for idx, row in group.iterrows():
            longitude, latitude = row.geometry.x, row.geometry.y

            for variable_name, bioclim_data in bioclim_data_dict.items():
                # Extract the bioclimatic value using the helper function
                bioclim_value = sample_netcdf_values_at_points(
                    longitude=longitude,
                    latitude=latitude,
                    time_idx=time_idx,
                    variable_name=variable_name,
                    bioclim_data=bioclim_data,
                    bioclim_lats=bioclim_lats,
                    bioclim_lons=bioclim_lons,
                    insect_year=year
                )

                # Update the value in insect_data
                insect_data.at[idx, variable_name] = bioclim_value

    return insect_data
