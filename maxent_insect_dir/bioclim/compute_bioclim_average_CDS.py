import numpy as np
import rasterio
from rasterio.transform import from_origin
import xarray as xr
import os
import matplotlib.pyplot as plt
from maxent_insect_dir.config import *
from maxent_insect_dir.bioclim.bioclim import *
from maxent_insect_dir.bioclim.compute_bioclim_average_worldclim import write_raster
from maxent_insect_dir.CDS_processing import *

def get_avg_bioclims():
    bioclim_cds, latitudes, longitudes = load_netcdf_files(climate_data_path=config_raw['climate_data_CDS'])
    
    bioclim_cds_1990_2021 = {}
    bioclim_cds_1970_2000 = {}
    
    for i in range(len(bioclim_cds)):
        key = 'BIO0' + str(i+1) if i+1 < 10 else 'BIO' + str(i+1)
        bioclim_cds_1990_2021['Bio'+str(i+1)] = bioclim_cds[key][key].sel(time=slice('1990-01-01', '2021-01-01')).mean(dim='time')
        bioclim_cds_1970_2000['Bio'+str(i+1)] = bioclim_cds[key][key].sel(time=slice('1970-01-01', '2000-01-01')).mean(dim='time')
    
    return bioclim_cds_1990_2021, bioclim_cds_1970_2000, latitudes, longitudes



if __name__ == '__main__':
    bioclim_cds_1990_2021, bioclim_cds_1970_2000, latitudes, longitudes = get_avg_bioclims()
    
    # Calculate resolutions
    lat_res = np.abs(latitudes[1] - latitudes[0])  # Latitude resolution
    lon_res = np.abs(longitudes[1] - longitudes[0])  # Longitude resolution

    # Create the affine transform
    transform = from_origin(
        west=longitudes.min() - lon_res / 2,
        north=latitudes.max() + lat_res / 2,
        xsize=lon_res,
        ysize=lat_res
    )

    # Define the CRS
    crs = 'EPSG:4326'  # WGS84 Latitude/Longitude

    # Set the nodata value
    nodata = np.nan

    
    # Create metadata dictionary
    metadata = {
        'crs': crs,
        'transform': transform,
        'nodata': nodata,
        'height': len(latitudes),
        'width': len(longitudes)
    }
    
    print(f'The metadata used to write the file : \n{metadata} ')



    # save 1990_2021    
    save_path = pathlib.Path('/data/Maxent/data/raw/Bioclim_CDS_average_1990_2021')
    for key, val in bioclim_cds_1990_2021.items():
        write_raster(
            bio_data=val,
            bio_name=key,
            metadata=metadata,
            save_path=save_path
        )
    
    
    # save 1970_2000   
    save_path = pathlib.Path('/data/Maxent/data/raw/Bioclim_CDS_average_1970_2000')
    for key, val in bioclim_cds_1970_2000.items():
        write_raster(
            bio_data=val,
            bio_name=key,
            metadata=metadata,
            save_path=save_path
        )