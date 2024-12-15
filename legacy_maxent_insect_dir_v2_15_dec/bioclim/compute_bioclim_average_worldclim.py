import numpy as np
import rasterio
import xarray as xr
import os
import matplotlib.pyplot as plt
from maxent_insect_dir.config import *
from maxent_insect_dir.bioclim.bioclim import *
    

def collect_paths(path, var):
    res = []
    for key in path.keys():
        files =  os.listdir(path[key][var])
        res.extend([os.path.join(path[key][var],file) for file in files])
    res = sorted(res)
    return res

def read_raster_files(files):
    # Read the first file to get metadata
    with rasterio.open(files[0]) as src:
        meta = src.meta
        meta.update(count=len(files))
        data_shape = (len(files), meta['height'], meta['width'])
        stack_data = np.empty(data_shape, dtype=meta['dtype'])
        transform = src.transform
    
    # Read each raster and stack it
    for idx, file in enumerate(files):
        with rasterio.open(file) as src:
            stack_data[idx, :, :] = src.read(1)
    
    # Calculate the longitude and latitude values based on the transform
    nrows, ncols = meta['height'], meta['width']
    x_coords = np.arange(ncols)
    y_coords = np.arange(nrows)
    lon = transform * (x_coords, np.zeros_like(x_coords))
    lat = transform * (np.zeros_like(y_coords), y_coords)
    lon_values = lon[0]
    lat_values = lat[1]
    
    coords = {
        "time": np.arange(len(files)),
        "y": lat_values,
        "x": lon_values
    }
    data_array = xr.DataArray(stack_data, dims=["time", "y", "x"], coords=coords)
    
    return data_array


def write_raster(bio_data, bio_name, metadata, save_path):
    """
    Writes a bioclimatic variable to a raster file using provided metadata.

    Parameters:
        bio_data (xarray.DataArray): The bioclimatic data to write.
        bio_name (str): The name of the bioclimatic variable.
        metadata (dict): Dictionary containing raster metadata (crs, transform, nodata, height, width).
        save_path (str): Directory where the output raster will be saved.
    """
    print(f"Writing {bio_name} to raster...")

    # Ensure the data is 2D (squeeze singleton dimensions if necessary)
    bio_data = bio_data.squeeze()

    # Get the data values as a NumPy array
    data_values = bio_data.values

    # Ensure data type is compatible with rasterio
    data_values = data_values.astype('float32')

    # Extract metadata from the provided metadata dictionary
    crs = metadata.get('crs')
    transform = metadata.get('transform')
    nodata = metadata.get('nodata')
    height = metadata.get('height')
    width = metadata.get('width')

    # Ensure the data shape matches the expected dimensions
    if data_values.shape != (height, width):
        raise ValueError(f"Data shape {data_values.shape} does not match expected shape {(height, width)}")

    # Write the data to a raster file
    output_file = os.path.join(save_path, f"{bio_name}.tif")

    # Define the raster profile (metadata)
    profile = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': data_values.dtype,
        'crs': crs,
        'transform': transform,
        'nodata': nodata,
        'compress': 'lzw'  # Optional: to compress the output file
    }

    # Create the output directory if it doesn't exist
    os.makedirs(save_path, exist_ok=True)

    with rasterio.open(output_file, 'w', **profile) as dst:
        dst.write(data_values, 1)

    print(f"{bio_name} written to {output_file}")


if __name__ == '__main__':
    
    paths_tmax = collect_paths(path = config_raw['climate_data_worldclim']['monthly_avg'], var = 'tmax')
    paths_tmin = collect_paths(path = config_raw['climate_data_worldclim']['monthly_avg'], var = 'tmin')
    paths_prec = collect_paths(path = config_raw['climate_data_worldclim']['monthly_avg'], var = 'prec')
        
        
    assert len(paths_tmax) == len(paths_tmin) == len(paths_prec)

    # Read raster stacks
    print('Reading maximum temperatures rasters...\n')
    tmax = read_raster_files(paths_tmax)
    print('Reading minimum temperatures rasters...\n')
    tmin = read_raster_files(paths_tmin)
    print('Reading precipitation temperatures rasters...\n')
    prec = read_raster_files(paths_prec)

    # Get Bioclimatic variables
    bio_climatic = get_avg_bioclims(tmax, tmin, prec)


    ############## Save the computed avg ############
    
    # get the refernce metadata
    metadata = {}
    with rasterio.open(paths_tmax[0]) as src:
        metadata['crs'] = src.crs
        metadata['transform'] = src.transform
        metadata['nodata'] = src.nodata
        metadata['height'] = src.height 
        metadata['width'] = src.width

    save_path = pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_1990_2021')
    for key, val in bio_climatic.items():
        write_raster(
            bio_data=val,
            bio_name=key,
            metadata=metadata,
            save_path=save_path
        )