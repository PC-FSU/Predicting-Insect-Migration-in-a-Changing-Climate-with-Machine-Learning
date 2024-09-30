# Common Imports
from maxent_insect_dir import config
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import pathlib
import os
import rasterio
import numpy as np
import xarray as xr



def worldclim_bioclim_yearly_avg_insect_intersection(climate_data_path, insect_crop_data):
    """
    Extracts bioclimatic values from a set of raster file at the locations 
    specified in the insect_crop_data and adds them as columns in the GeoDataFrame.

    Parameters:
    -----------
    climate_data_path : str
        The path to the directory containing .netcdf files with bioclimatic data.
    insect_crop_data : GeoDataFrame
        A GeoDataFrame containing point geometries (latitude, longitude) and year of observation.

    Returns:
    --------
    GeoDataFrame
        The input GeoDataFrame with additional columns containing the bioclimatic variable values 
        at the coordinates and years corresponding to the insect_crop_data points.
    """
    
    
    files = sorted(os.listdir(climate_data_path), key = lambda x : int(x.split('_')[-1].split('.')[0]))
    
    
    for idx, file in enumerate(files):
        raster_path = os.path.join(climate_data_path, file)
        var_name = 'WORLDCLIM_YEARLY_AVG_BIO' + str(idx+1)
        insect_crop_data[var_name] = 0.0
        
        # Load the raster file using rasterio
        with rasterio.open(raster_path) as src:
            print(f'insect data crs : {insect_crop_data.crs} | bioclim data crs : {src.crs}')
            assert insect_crop_data.crs == src.crs, 'mismatch in the crs co-ord of two file'
            
            #Sample raster values at point coordinates
            insect_crop_data[var_name] = [
                list(src.sample([(geom.x, geom.y)]))[0][0] if geom.is_valid else None
                for geom in insect_crop_data.geometry
            ]
    
    # extra processing step, remove the outlier values
    insect_crop_data = insect_crop_data.drop(insect_crop_data[(insect_crop_data['WORLDCLIM_YEARLY_AVG_BIO2'] < -1e6) | (insect_crop_data['WORLDCLIM_YEARLY_AVG_BIO2'] > 1e6)].index)

    return insect_crop_data


def get_nearest_time_range(year, data):
    """
    Given a year, this function finds the nearest time range in the available climate data.
    
    Args:
        year (int): The year to search for.
        data (dict): Dictionary where keys represent year ranges, and values are paths to climate data.
        
    Returns:
        tuple: The dictionary of paths for the nearest year range, the range as a string, and the closest boundary year.
    """
    nearest_range = None
    smallest_diff = float('inf')
    
    for range_key in data.keys():
        # Extract the start and end years from the range key
        start_year, end_year = map(int, range_key.split('-'))
        
        # If the year is within the range, return it immediately
        if start_year <= year <= end_year:
            return data[range_key], range_key, year
        
        # Calculate the smallest difference between the year and the range boundaries
        diff = min(abs(year - start_year), abs(year - end_year))
        if diff < smallest_diff:
            smallest_diff = diff
            nearest_range = range_key
            
            # Track the closest boundary year (either start or end of the range)
            boundary = start_year if abs(year - start_year) <= abs(year - end_year) else end_year
            
    return data[nearest_range], nearest_range, boundary


def worldclim_bioclim_monthly_avg_insect_intersection(climate_data_path, insect_crop_data, id_column):
    """
    Intersects monthly climate data with insect point data on a per-year basis. 
    For each insect point, it retrieves the average monthly values for temperature maximum (tmax), 
    temperature minimum (tmin), and precipitation (prec).
    
    Args:
        climate_data_path (dict): Dictionary with year ranges as keys and paths to climate data as values.
        insect_crop_data (pd.DataFrame): DataFrame containing insect data (coordinates, month, year).
        id_column (str): Column name for unique identifiers of insect points.
    
    Returns:
        pd.DataFrame: The original insect data merged with the corresponding climate data (tmax, tmin, prec).
    """
    
    results = []

    # Group the insect point data by year for processing efficiency
    grouped = insect_crop_data.groupby('year')
    
    # Process each year group
    for year, group in grouped:
        sample_count = group[id_column].count()
        print(f'Processing {sample_count} samples for the year {year}...\n')

        # Get the nearest available climate data for the year
        year_dict, year_range, boundary = get_nearest_time_range(year, climate_data_path)
        
        # If the current year is out of range, use the boundary year
        if boundary != year:
            print(f'Updating year {year} to nearest available year {boundary}.')
            year = boundary
        
        # Create file paths for the monthly tmax, tmin, and prec data
        month_dict = {
            'tmax': {month: f'wc2.1_10m_tmax_{year}-{month:02d}.tif' for month in range(1, 13)},
            'tmin': {month: f'wc2.1_10m_tmin_{year}-{month:02d}.tif' for month in range(1, 13)},
            'prec': {month: f'wc2.1_10m_prec_{year}-{month:02d}.tif' for month in range(1, 13)}
        }

        # Build the complete file paths using the climate data directories
        final_dict_path = {
            'tmax': {month: os.path.join(year_dict['tmax'], month_dict['tmax'][month]) for month in range(1, 13)},
            'tmin': {month: os.path.join(year_dict['tmin'], month_dict['tmin'][month]) for month in range(1, 13)},
            'prec': {month: os.path.join(year_dict['prec'], month_dict['prec'][month]) for month in range(1, 13)}
        }
        
        # Open the raster files for all months for the year
        data = {
            'tmax': {month: rasterio.open(final_dict_path['tmax'][month]) for month in range(1, 13)},
            'tmin': {month: rasterio.open(final_dict_path['tmin'][month]) for month in range(1, 13)},
            'prec': {month: rasterio.open(final_dict_path['prec'][month]) for month in range(1, 13)}
        }
    
        # Iterate over each insect point in the group
        for idx, row in group.iterrows():
            insect_location = [(row.geometry.x, row.geometry.y)]
            month = row['month']
            
            # Retrieve climate data for the given month
            current_tmax_raster = data['tmax'][month]
            current_tmin_raster = data['tmin'][month]
            current_prec_raster = data['prec'][month]
            
            # Ensure CRS consistency only once (for the first sample)
            if idx == 0:
                assert group.crs == current_tmax_raster.crs == current_tmin_raster.crs == current_prec_raster.crs, 'CRS mismatch detected. Ensure all data uses the same coordinate reference system.'
            
            # Sample the raster data at the insect location
            tmax = list(current_tmax_raster.sample(insect_location))[0][0]
            tmin = list(current_tmin_raster.sample(insect_location))[0][0]
            prec = list(current_prec_raster.sample(insect_location))[0][0]
            
            # Append the results for the current insect point
            results.append({
                'insect_id': row[id_column],
                'WORLDCLIM_MONTHLY_AVG_tmax': tmax,
                'WORLDCLIM_MONTHLY_AVG_tmin': tmin,
                'WORLDCLIM_MONTHLY_AVG_prec': prec
            })
    
    # Convert results into a DataFrame
    result_df = pd.DataFrame(results)
    
    # Merge the result DataFrame with the original insect data
    insect_crop_data = pd.merge(insect_crop_data, result_df, how='left', left_on=id_column, right_on='insect_id')
    
    return insect_crop_data
