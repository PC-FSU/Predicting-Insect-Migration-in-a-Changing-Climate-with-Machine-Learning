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

from maxent_insect_dir.config import *
from maxent_insect_dir.utils_common import *

# Suppress pandas chain assignment warning
pd.options.mode.chained_assignment = None  # default='warn'



def load_yearly_raster_files(climate_data_path: str) -> List[str]:
    """
    Loads and returns a sorted list of yearly raster file paths from the given directory.
    """
    files = sorted(
        [f for f in os.listdir(climate_data_path) if f.endswith('.tif')],
        key=lambda x: int(x.split('_')[-1].split('.')[0])
    )
    raster_paths = [os.path.join(climate_data_path, f) for f in files]
    return raster_paths


def load_monthly_raster_files(
    year: int,
    year_dict: Dict[str, str]
) -> Dict[str, Dict[int, str]]:
    """
    Builds and returns a dictionary of file paths for monthly tmax, tmin, and prec data.
    """
    final_dict_path = {}
    for var in ['tmax', 'tmin', 'prec']:
        final_dict_path[var] = {
            month: os.path.join(
                year_dict[var],
                f'wc2.1_10m_{var}_{year}-{month:02d}.tif'
            ) for month in range(1, 13)
        }
    return final_dict_path


def remove_outliers(
    df: gpd.GeoDataFrame,
    column: str,
    lower_bound: float,
    upper_bound: float
) -> gpd.GeoDataFrame:
    """
    Removes rows where the values in the specified column are outside the given bounds.
    """
    return df[(df[column] > lower_bound) & (df[column] < upper_bound)]



def get_nearest_time_range(year: int, data: Dict[str, Dict[str, str]]) -> tuple[Dict[str, str], str, int]:
    """
    Given a year, find the nearest time range in the available climate data.

    Args:
        year (int): The year to search for.
        data (dict): Dictionary where keys represent year ranges, and values are paths to climate data.

    Returns:
        tuple: (Dictionary of paths for the nearest year range, the range as a string, the closest boundary year)
    """
    nearest_range = None
    smallest_diff = float('inf')
    boundary = None

    for range_key in data.keys():
        # Extract the start and end years from the range key
        start_year, end_year = map(int, range_key.split('-'))

        # If the year is within the range, return it immediately
        if start_year <= year <= end_year:
            return data[range_key], range_key, year

        # Calculate the smallest difference between the year and the range boundaries
        diff_start = abs(year - start_year)
        diff_end = abs(year - end_year)
        diff = min(diff_start, diff_end)

        if diff < smallest_diff:
            smallest_diff = diff
            nearest_range = range_key
            boundary = start_year if diff_start <= diff_end else end_year

    return data[nearest_range], nearest_range, boundary



def process_yearly_raster_file(
    insect_crop_data: gpd.GeoDataFrame,
    raster_path: str,
    id_column: str,
    var_name: str
) -> gpd.GeoDataFrame:
    """
    Samples raster values from a yearly raster file and merges them into the GeoDataFrame.

    Parameters:
    -----------
    insect_crop_data : GeoDataFrame
        GeoDataFrame containing insect data.
    raster_path : str
        Path to the raster file.
    id_column : str
        Column name in insect_crop_data that uniquely identifies each point.
    var_name : str
        Name of the variable to be added to the GeoDataFrame.

    Returns:
    --------
    GeoDataFrame
        Updated GeoDataFrame with the new variable column added.
    """
    # Sample raster values at insect locations
    sampled_values_df = sample_raster_values_at_points(
        insect_crop_data,
        raster_path,
        id_column,
        var_name
    )

    # Merge the sampled values back into the insect_crop_data
    insect_crop_data = insect_crop_data.merge(
        sampled_values_df,
        on=id_column,
        how='left'
    )

    return insect_crop_data


def process_year_group(
    year: int,
    group: gpd.GeoDataFrame,
    climate_data_path: Dict[str, Dict[str, str]],
    id_column: str
) -> pd.DataFrame:
    """
    Processes a group of insect data for a specific year.

    Parameters:
    -----------
    year : int
        Year of the insect data.
    group : GeoDataFrame
        Grouped GeoDataFrame for the specific year.
    climate_data_path : dict
        Dictionary containing paths to climate data.
    id_column : str
        Column name that uniquely identifies each point.

    Returns:
    --------
    DataFrame
        DataFrame containing the sampled climate data for the group.
    """
    sample_count = group[id_column].count()
    print(f'Processing {sample_count} samples for the year {year}...\n')

    # Get the nearest available climate data for the year
    year_dict, _, boundary = get_nearest_time_range(year, climate_data_path)

    # If the current year is out of range, use the boundary year
    if boundary != year:
        print(f'Updating year {year} to nearest available year {boundary}.')
        year = boundary

    # Load monthly raster files for the year
    final_dict_path = load_monthly_raster_files(year, year_dict)

    # Validate CRS consistency
    sample_raster_files = [
        final_dict_path['tmax'][1],
        final_dict_path['tmin'][1],
        final_dict_path['prec'][1]
    ]
    validate_crs_consistency(group, sample_raster_files)

    # Initialize a DataFrame to collect results
    results_df = group[[id_column]].copy()

    # Process each variable
    for var in ['tmax', 'tmin', 'prec']:
        # Iterate over months
        for month in range(1, 13):
            # Get the subset of group for the specific month
            month_group = group[group['month'] == month]

            if not month_group.empty:
                # Sample raster values for the month
                raster_file = final_dict_path[var][month]
                sampled_df = sample_raster_values_at_points(
                    point_gdf=month_group,
                    raster_file=raster_file,
                    id_column=id_column,
                    value_column_name=f'{var}_{month}'
                )
                # Merge the sampled values
                results_df = results_df.merge(
                    sampled_df,
                    on=id_column,
                    how='left'
                )
            else:
                # If no data for the month, add NaNs
                results_df[f'{var}_{month}'] = np.nan

        # Compute average across months for the variable
        month_columns = [f'{var}_{m}' for m in range(1, 13)]
        results_df[f'WORLDCLIM_MONTHLY_AVG_{var}'] = results_df[month_columns].mean(axis=1)

        # Optionally, drop the monthly columns if not needed
        results_df.drop(columns=month_columns, inplace=True)

    return results_df




def worldclim_bioclim_yearly_avg_insect_intersection(
    climate_data_path: str,
    insect_crop_data: gpd.GeoDataFrame,
    id_column: str
) -> gpd.GeoDataFrame:
    """
    Extracts bioclimatic values from yearly raster files at the insect locations.

    Parameters:
    -----------
    climate_data_path : str
        Path to the directory containing raster files with bioclimatic data.
    insect_crop_data : GeoDataFrame
        GeoDataFrame containing insect data.
    id_column : str
        Column name in insect_crop_data that uniquely identifies each point.

    Returns:
    --------
    GeoDataFrame
        Updated GeoDataFrame with additional columns for each bioclimatic variable.
    """
    # Load yearly raster files
    raster_files = load_yearly_raster_files(climate_data_path)

    for idx, raster_path in enumerate(raster_files):
        var_name = f'WORLDCLIM_YEARLY_AVG_BIO{idx + 1}'

        # Process the raster file
        insect_crop_data = process_yearly_raster_file(
            insect_crop_data,
            raster_path,
            id_column,
            var_name
        )

    # Remove outliers
    insect_crop_data = remove_outliers(
        insect_crop_data,
        column='WORLDCLIM_YEARLY_AVG_BIO2',
        lower_bound=-1e6,
        upper_bound=1e6
    )

    return insect_crop_data




def worldclim_bioclim_monthly_avg_insect_intersection(
    climate_data_path: Dict[str, Dict[str, str]],
    insect_crop_data: gpd.GeoDataFrame,
    id_column: str
) -> gpd.GeoDataFrame:
    """
    Intersects monthly climate data with insect point data on a per-year basis.

    Parameters:
    -----------
    climate_data_path : dict
        Dictionary with year ranges as keys and paths to climate data as values.
    insect_crop_data : GeoDataFrame
        GeoDataFrame containing insect data (coordinates, month, year).
    id_column : str
        Column name for unique identifiers of insect points.

    Returns:
    --------
    GeoDataFrame
        The original insect data merged with the corresponding climate data.
    """
    all_results = []

    # Group the insect point data by year for processing efficiency
    grouped = insect_crop_data.groupby('year')

    # Process each year group
    for year, group in grouped:
        results_df = process_year_group(
            year=year,
            group=group,
            climate_data_path=climate_data_path,
            id_column=id_column
        )
        all_results.append(results_df)

    # Concatenate all results
    all_results_df = pd.concat(all_results, ignore_index=True)

    # Merge the result DataFrame with the original insect data
    insect_crop_data = insect_crop_data.merge(
        all_results_df,
        on=id_column,
        how='left'
    )

    return insect_crop_data
