import geopandas as gpd
import matplotlib.pyplot as plt
import pathlib
import pandas as pd
import rasterio
import warnings
import numpy as np
import xarray as xr
import re
from typing import Dict, List, Union

from maxent_insect_dir.config import *


################### General Utils ################################################

# Function to safely read GeoDataFrame with exception handling
def safe_read_file(file_path, layer_name=None):
    """
    Safely reads a GeoDataFrame from a file, with exception handling for encoding issues.

    Args:
        file_path (str or Path): The path to the file to be read.
        layer_name (str, optional): The name of the specific layer to read from the file. Default is None.

    Returns:
        GeoDataFrame: The read GeoDataFrame, or None if an error occurred.
    """
    try:
        if layer_name:
            return gpd.read_file(file_path, layer=layer_name)
        else:
            return gpd.read_file(file_path)
    except UnicodeDecodeError:
        print(f"Unicode decoding error occurred while reading layer '{layer_name}' from {file_path}. Attempting with ISO-8859-1 encoding.")
        try:
            if layer_name:
                return gpd.read_file(file_path, layer=layer_name, encoding='ISO-8859-1')
            else:
                return gpd.read_file(file_path, encoding='ISO-8859-1')
        except Exception as e:
            print(f"Failed to read layer '{layer_name}' from {file_path}: {e}")
            return None
    except Exception as e:
        print(f"An error occurred while reading layer '{layer_name}' from {file_path}: {e}")
        return None
    
    

def drop_points_outside_us(gdf):
    """
    Drops points outside the continental US bounding box from a GeoDataFrame.
    
    Parameters:
    gdf (GeoDataFrame): A GeoDataFrame containing point geometries.
    
    Returns:
    GeoDataFrame: A GeoDataFrame with points only within the US bounding box.
    """
    # Define the bounding box with margin of error
    lat_min = 23.896308
    lat_max = 49.884358
    lon_min = -125.500000
    lon_max = -66.434570
    
    # Extract latitude and longitude from GeoDataFrame geometry
    gdf['longitude'] = gdf.geometry.x
    gdf['latitude'] = gdf.geometry.y
    
    # Filter points that are within the bounding box
    gdf_filtered = gdf[
        (gdf['longitude'] >= lon_min) &
        (gdf['longitude'] <= lon_max) &
        (gdf['latitude'] >= lat_min) &
        (gdf['latitude'] <= lat_max)
    ]
    
    # Drop temporary longitude and latitude columns
    gdf_filtered = gdf_filtered.drop(columns=['longitude', 'latitude'])
    
    return gdf_filtered



# Function to plot the data based on provided parameters
def plot_data(gdf, plot_info, save_path, show_plots=True):
    """
    Plots data (spatial, temporal, or histogram) based on the given parameters.

    Args:
        gdf (GeoDataFrame or DataFrame): The data to be plotted.
        plot_info (dict): A dictionary containing plot details:
            - 'plot_type' (str): The type of plot to create ('map', 'timeseries', or 'hist').
            - 'title' (str): The title of the plot.
            - 'xlabel' (str, optional): The label for the x-axis.
            - 'ylabel' (str, optional): The label for the y-axis.
            - 'column' (str, optional): The column from `gdf` to use for plotting.
            - 'rotation' (int, optional): The rotation angle for the x-axis ticks (useful for time-series plots).
        save_path (str or Path): The path where the plot image will be saved.
        show_plots (bool, optional): Whether to display the plot. Defaults to True.

    Returns:
        None
    """
    
    # Retrieve plot information from the plot_info dictionary
    plot_type = plot_info.get('plot_type')  # The type of plot ('map', 'timeseries', or 'hist')
    title = plot_info.get('title')          # The title of the plot
    xlabel = plot_info.get('xlabel', None)  # X-axis label (optional)
    ylabel = plot_info.get('ylabel', None)  # Y-axis label (optional)
    column = plot_info.get('column', None)  # Column in DataFrame to be used for plotting (optional)
    rotation = plot_info.get('rotation', None)  # Rotation for x-axis ticks (optional)

    # Handle different plot types
    if plot_type == 'map':
        # Plot geographic points (such as locations on a map) using the specified column for color coding
        gdf.plot(marker='o', column=column, cmap='viridis', legend=True)
    
    elif plot_type == 'timeseries':
        # Plot a time series showing how a value (such as insect count) changes over time
        plt.figure(figsize=(15, 4))
        # Group the data by the date column and plot the number of occurrences over time
        gdf.groupby(column).size().sort_index().plot(kind='line', marker='o')
        
    elif plot_type == 'hist':
        # Plot a histogram for a specific column to show the distribution of data (e.g., crop distribution)
        plt.figure(figsize=(20, 5))
        gdf[column].hist(grid=False)
    
    elif plot_type == 'hist_all':
        # Plot histograms for all columns (especially bioclim data)
        gdf.hist(figsize=(30, 20), grid=False)

    # Common plot settings
    plt.title(title)  # Set the plot title
    if xlabel:
        plt.xlabel(xlabel)  # Set x-axis label if provided
    if ylabel:
        plt.ylabel(ylabel)  # Set y-axis label if provided
    
    # Handle x-axis tick rotation if specified (for time-series or other plots where it's useful)
    plt.xticks() if rotation is None else plt.xticks(rotation=rotation)
    
    # Adjust layout to ensure no overlap between plot elements
    plt.tight_layout()

    # Save the plot to the specified save_path if it's a valid path
    if isinstance(save_path, (str, pathlib.PosixPath)):  
        plt.savefig(save_path)
    
    # Show or close the plot based on the `show_plots` flag
    if show_plots:
        plt.show()  # Display the plot
    else:
        plt.close()  # Close the plot if not showing (for batch processing)
        
        
        

    
    

def map_codes_to_names(
    df: pd.DataFrame,
    code_column: str,
    mapping_dict: Dict[int, str],
    name_column: str = 'mapped_value'
) -> pd.DataFrame:
    """
    Maps codes in code_column to names using mapping_dict and adds a new column name_column.

    Parameters:
    -----------
    df : DataFrame
        DataFrame containing code_column.
    code_column : str
        Name of the column containing codes.
    mapping_dict : dict
        Dictionary mapping codes to names.
    name_column : str
        Name of the new column to store mapped names.

    Returns:
    --------
    DataFrame
        DataFrame with the new name_column added.
    """
    df[name_column] = df[code_column].map(mapping_dict)
    return df



def validate_crs_consistency(point_gdf: gpd.GeoDataFrame, raster_files: List[str]):
    """
    Validates that the CRS of the point GeoDataFrame matches that of the raster files.

    Parameters:
    -----------
    point_gdf : GeoDataFrame
        GeoDataFrame containing point geometries.
    raster_files : List[str]
        List of paths to raster files.
    """
    for raster_file in raster_files:
        with rasterio.open(raster_file) as src:
            if point_gdf.crs != src.crs:
                warnings.warn(
                    f"CRS mismatch detected between point data and raster file {raster_file}.",
                    UserWarning
                )
                
                
def sample_raster_values_at_points(
    point_gdf: gpd.GeoDataFrame,
    raster_file: str,
    id_column: str,
    var_name: str = 'raster_value'
) -> pd.DataFrame:
    """
    Samples raster values at the locations specified in point_gdf.

    Parameters:
    -----------
    point_gdf : GeoDataFrame
        GeoDataFrame containing point geometries.
    raster_file : str
        Path to the raster file.
    id_column : str
        Column name in point_gdf that uniquely identifies each point.
    value_column_name : str
        Name of the column to store the sampled raster values.

    Returns:
    --------
    DataFrame
        DataFrame with id_column and value_column_name.
    """
    with rasterio.open(raster_file) as src:
        # Reproject points to match raster CRS if needed
        if point_gdf.crs != src.crs:
            point_gdf = point_gdf.to_crs(src.crs)

        coords = [(x, y) for x, y in zip(point_gdf.geometry.x, point_gdf.geometry.y)]
        values = [val[0] for val in src.sample(coords)]

        result_df = pd.DataFrame({
            id_column: point_gdf[id_column],
            var_name: values
        })

        return result_df
                
                
def sample_netcdf_values_at_points(
    longitude: float,
    latitude: float,
    time_idx: int,
    variable_name: str,
    bioclim_data: xr.Dataset,
    bioclim_lats: np.ndarray,
    bioclim_lons: np.ndarray,
    insect_year: int
) -> float:
    """
    Extracts a bioclimatic value from a dataset at a specific location and time index.

    Parameters:
    -----------
    longitude : float
        Longitude of the point.
    latitude : float
        Latitude of the point.
    time_idx : int
        Time index corresponding to the year.
    variable_name : str
        Name of the bioclimatic variable.
    bioclim_data : xr.Dataset
        Xarray Dataset containing the bioclimatic data.
    bioclim_lats : np.ndarray
        Array of latitude values from the dataset.
    bioclim_lons : np.ndarray
        Array of longitude values from the dataset.
    insect_year : int
        Year of the insect data point.

    Returns:
    --------
    float
        The extracted bioclimatic value.

    Raises:
    -------
    ValueError
        If there is a mismatch between insect_year and dataset_year.
    """
    # Validate the year
    dataset_year = bioclim_data['time'].dt.year[time_idx].item()
    if insect_year != dataset_year:
        raise ValueError(f"Year mismatch: insect data year {insect_year}, bioclim data year {dataset_year}")

    # Find nearest indices
    lat_idx = np.abs(bioclim_lats - latitude).argmin()
    lon_idx = np.abs(bioclim_lons - longitude).argmin()

    # Extract the value
    bioclim_value = bioclim_data.isel(
        time=time_idx, latitude=lat_idx, longitude=lon_idx
    )[variable_name].values.item()

    return bioclim_value


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



def load_raster_files(climate_data_path: str):
    """
    Loads and returns a sorted list of yearly raster file paths from the given directory.
    """
    try:
        files = sorted(os.listdir(climate_data_path), key = lambda x: int(re.search(r'\d+', x).group()))
    except:
        files = os.listdir(climate_data_path)
    raster_paths = [os.path.join(climate_data_path, f) for f in files]
    return raster_paths



def bioclim_avg_insect_intersection(
    raster_path: str,
    gfd: gpd.GeoDataFrame,
    id_column: str,
    label_prefix: str
) -> gpd.GeoDataFrame:
    """
    Extracts values from yearly raster files at the locations in the gfd frame.

    Parameters:
    -----------
    raster_path : str
        Path to the directory containing raster files.
    gfd : GeoDataFrame
        GeoDataFrame.
    id_column : str
        Column name in gfd that uniquely identifies each point.

    Returns:
    --------
    GeoDataFrame
        Updated GeoDataFrame with additional columns.
    """
    # Load yearly raster files
    raster_files = load_raster_files(raster_path)

    for idx, path in enumerate(raster_files):
        var_name = label_prefix + path.split('/')[-1].split('.')[0]

        # Sample raster values at insect locations
        sampled_values_df = sample_raster_values_at_points(
            gfd,
            path,
            id_column,
            var_name
        )

        # Merge the sampled values back into the insect_crop_data
        gfd = gfd.merge(
            sampled_values_df,
            on=id_column,
            how='left'
        )
        
    return gfd


# alias for LUH2
LUH2_intersection = bioclim_avg_insect_intersection