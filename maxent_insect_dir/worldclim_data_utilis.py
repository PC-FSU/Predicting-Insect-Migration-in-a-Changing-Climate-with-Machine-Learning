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




def worldclimbioclim_yearlyavg_insect_intersection(climate_data_path, insect_crop_data):
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
        var_name = 'WORLDCLIM_YEARLY_AVG_BIO'+str(idx)
        
        # Load the raster file using rasterio
        with rasterio.open(raster_path) as src:
            print(f'insect data crs : {insect_crop_data.crs} | bioclim data crs : {src.crs}')
            assert insect_crop_data.crs == src.crs, 'mismatch in the crs co-ord of two file'
            
            # Sample raster values at point coordinates
            insect_crop_data[var_name] = [
                list(src.sample([(geom.x, geom.y)]))[0][0] if geom.is_valid else None
                for geom in insect_crop_data.geometry
            ]

    return insect_crop_data