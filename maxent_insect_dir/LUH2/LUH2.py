from maxent_insect_dir import config
import os
import pathlib
import geopandas as gpd
import rasterio
import rasterio.plot as rioplot # To Visualize Raster Data
import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
from rasterio.transform import from_bounds
from maxent_insect_dir.bioclim.compute_bioclim_average_worldclim import write_raster

pd.options.mode.chained_assignment = None  # default='warn'


def get_LUH2_avg():

    # Load yearly raster files
    data_850_2015 =  xr.open_dataset(pathlib.Path("/data/Maxent/data/raw/LUH2/states_850_2015.nc"), decode_times=False )
    data_2015_2100 = xr.open_dataset(pathlib.Path("/data/Maxent/data/raw/LUH2/multiple-states_input4MIPs_landState_ScenarioMIP_UofMD-MESSAGE-ssp245-2-1-f_gn_2015-2100.nc"), decode_times=False )

    ############# for 1970-2000 avg ####################
    # Select the time range 1970 to 2000 (after adjusting for the 850 year offset)
    print('Calculating LUH2 average for 1970_2000....\n')
    LUH2_avg_1970_2000 = data_850_2015.sel(time=slice(1970-850, 2000-850)).mean(dim='time')


    print('Calculating LUH2 average for 1990_2021....\n')
    LUH2_1990_2021 = xr.concat(
        [data_850_2015.sel(time=slice(1990-850, 2014-850)),
        data_2015_2100.sel(time=slice(0, 6))],
        dim='time'
    )    
    LUH2_avg_1990_2021 = LUH2_1990_2021.mean(dim='time')
    
    return LUH2_avg_1970_2000, LUH2_avg_1990_2021


def write_LUH2_to_raster(dataset, save_path):
    """
    Helper function to loop over all variables in an xarray dataset and call write_raster for each.

    Parameters:
        dataset (xarray.Dataset): The dataset containing the variables to write.
        save_path (str): Directory where the output raster files will be saved.
    """
    # Extract latitude and longitude values
    lat = dataset['lat'].values
    lon = dataset['lon'].values
    height = len(lat)
    width = len(lon)
    

    # Define the geospatial transform using the bounds of latitude and longitude
    transform = from_bounds(min(lon), min(lat), max(lon), max(lat), width, height)

    # Create metadata dictionary for the raster files
    metadata = {
        'crs': 'EPSG:4326',  # Assuming WGS84 coordinate system
        'transform': transform,
        'nodata': np.nan,  # Set nodata value 
        'height': height,
        'width': width
    }
    

    # Loop over each variable in the dataset and call write_raster for each
    for var_name in dataset.data_vars:


        bio_data = dataset[var_name]  # Get the data for the current variable
                
        # Skip non-spatial variables like 'lat_bounds', 'lon_bounds', etc.
        if bio_data.shape != (height, width):
            print(f"Skipping {var_name}: shape {bio_data.shape} does not match (height, width) of ({height}, {width})")
            continue


        # Call the write_raster function for each variable
        write_raster(bio_data, var_name, metadata, save_path)

    print("All variables have been written to raster files.")


if __name__ == '__main__':
    
    LUH2_avg_1970_2000, LUH2_avg_1990_2021 = get_LUH2_avg()
    
    write_LUH2_to_raster(
        LUH2_avg_1970_2000,
        save_path=pathlib.Path('/data/Maxent/data/raw/LUH2_average_1970_2000')
        )
    
    write_LUH2_to_raster(
        LUH2_avg_1990_2021,
        save_path=pathlib.Path('/data/Maxent/data/raw/LUH2_average_1990_2021')
        )
    