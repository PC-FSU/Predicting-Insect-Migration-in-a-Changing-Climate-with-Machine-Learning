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


pd.options.mode.chained_assignment = None  # default='warn'

################### Raw data Utils ################################################

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




# Function to clean and prepare data downloaded from EDD website.
def clean_and_prepare_data_for_EDD(gdf, keep_columns, date_column='ObsDate', status_column='OccStatus', count_column='NumCollect'):
    """
    Cleans and prepares data downloaded from the EDD website.

    Args:
        gdf (GeoDataFrame): The GeoDataFrame to be cleaned and prepared.
        keep_columns (list): A list of columns to keep in the trimmed GeoDataFrame.
        date_column (str, optional): The name of the date column. Default is 'ObsDate'.
        status_column (str, optional): The name of the status column. Default is 'OccStatus'.
        count_column (str, optional): The name of the count column. Default is 'NumCollect'.

    Returns:
        GeoDataFrame: The cleaned and prepared GeoDataFrame.
    """
    if keep_columns is None:
        raise ValueError('Please specify the column that you would like to keep in the trimmed df.')
    
    print(f'Keep columns : {keep_columns}\n')
    
    # Let keep the data that we are interested in.
    gdf_trimmed =  gdf[keep_columns]

    # Add explicit label to the data
    label = gdf_trimmed[status_column].apply(lambda x: 1 if x.lower() == "detected" else 0)
    gdf_trimmed['label'] = label
    
    # Clean the NumCollect data, adding 1 to each entry -- There's an entry 'many' here, replacing it by 1, because 'many' is ambiguous. 
    NumCollect_int  = gdf_trimmed[count_column].apply(lambda x: x + 1 if isinstance(x, int) else 1)
    gdf_trimmed['NumCollect_int'] = NumCollect_int

    # Convert date_column to datetime format
    gdf_trimmed[date_column] = pd.to_datetime(gdf_trimmed[date_column], format='%m-%d-%y')
    
    # Extract day, month, and year into separate columns
    gdf_trimmed['year'] = gdf_trimmed[date_column].dt.year
    gdf_trimmed['month'] = gdf_trimmed[date_column].dt.month
    gdf_trimmed['day_number'] = gdf_trimmed[date_column].dt.day
    
    # add column for state and country, and drop the location column
    if 'Location' in gdf_trimmed.columns:
        split_location = gdf_trimmed['Location'].str.split(',', expand=True)
        # Select the second and third columns (state and country)
        gdf_trimmed['state'] = split_location[1].str.strip().str.lower().str.replace('"','')
        gdf_trimmed['country'] = split_location[2].str.strip().str.lower().str.replace('"','')
        gdf_trimmed = gdf_trimmed.drop(['Location'], axis=1)
        
    # drop all point where country is not united states
    allowed_countries = ['united states', 'us', 'unitedstates', 'unitedstate'] # assuming data can take this value
    # Filter the DataFrame to keep only the rows where 'country' is in the allowed list
    gdf_trimmed = gdf_trimmed[gdf_trimmed['country'].str.lower().isin(allowed_countries)]

    return gdf_trimmed




# Function to clean and prepare data downloaded from GBIF website.
def clean_and_prepare_data_for_GBIF(gdf, date_column='day'):
    """
    Cleans and prepares data downloaded from the GBIF website.

    Args:
        gdf (GeoDataFrame): The GeoDataFrame to be cleaned and prepared.
        date_column (str, optional): The name of the date column. Default is 'day'.

    Returns:
        GeoDataFrame: The cleaned and prepared GeoDataFrame.
    """
    if 'Unnamed_ 0' in gdf.columns:
        gdf_trimmed = gdf.drop(['Unnamed_ 0'], axis=1)
    else:
        gdf_trimmed = gdf
    
    if isinstance(date_column, list):
        raise ValueError('Please provide a valid day column as a string.')

    # Create the label column
    gdf_trimmed['label'] = 1
    
    # Convert the 'day' column to datetime format
    gdf_trimmed[date_column] = pd.to_datetime(gdf_trimmed[date_column])
    
    # Extract day, month, and year into separate columns
    gdf_trimmed['Year'] = gdf_trimmed['Year'].astype(int)
    # Rename the column 'Year' to 'year', so we are consistent with EDD data
    gdf_trimmed.rename(columns={'Year': 'year'}, inplace=True)
    gdf_trimmed['month'] = gdf_trimmed[date_column].dt.month
    gdf_trimmed['day_number'] = gdf_trimmed[date_column].dt.day
    
    # Drop all the point where locality != 'US' if locality exist in dataframe columns
    if 'locality' in gdf_trimmed.columns:
        print('\nRemoved non-us samples.....\n\n')
        gdf_trimmed = gdf_trimmed[gdf_trimmed['locality'] == 'US']
        
    # rename 'occurrence' to 'state', and lowercase each entry.
    gdf_trimmed.rename(columns={'occurrence': 'state'}, inplace=True)
    gdf_trimmed['state'] = gdf_trimmed['state'].str.lower()
    
    
    # assign a unique value for each row
    # Set the index as a unique row identifier (use the current index)
    gdf_trimmed = gdf_trimmed.reset_index(drop=True)

    # Rename the index to 'objectid', this is done so EDD and GBIF has same column name for unique key.
    gdf_trimmed = gdf_trimmed.rename_axis('objectid').reset_index()
        
    return gdf_trimmed



# Function to merge crop data with insect location data
def find_crops_for_insect_locations(point_df, crop_raster_folder, id_column, crop_mapping_dict):
    """
    Identifies the crop type at specific insect locations for a given year by matching 
    insect point data with corresponding crop raster data.

    This function processes insect point data and determines which crop is planted at each 
    insect location for the specified year. The crop data is provided in the form of raster 
    files, where each raster file represents a crop coverage map for a particular year. 
    The function groups insect data by year, retrieves the corresponding crop raster for 
    that year, and samples the raster to determine the crop type at each insect location.

    Parameters:
    -----------
    point_df : GeoDataFrame
        A GeoDataFrame containing the insect point data with required columns including 'geometry' 
        (for location) and 'year' (to specify which year's crop data to reference).
    
    crop_raster_folder : str
        The file path to the folder containing the crop raster files for the years 2008-2023. 
        Each year's crop raster is assumed to follow a naming convention such as '{year}_30m_cdls.tif'.
    
    id_column : str
        The column name in point_df that uniquely identifies each insect point.
    
    crop_mapping_dict : dict
        A dictionary mapping crop codes from the raster files to crop names/types. 
        The crop codes are integers from the raster, and the dictionary translates them 
        into human-readable crop names.
    
    Returns:
    --------
    GeoDataFrame
        A new GeoDataFrame which includes the original insect point data along with a new column 
        indicating the crop type (mapped from the raster data) at each insect location.
        
    Process:
    --------
    1. Groups the insect point data by the 'year' column.
    2. For each year, opens the corresponding crop raster file.
    3. Reprojects the insect locations to match the coordinate reference system (CRS) of the raster file.
    4. Samples the raster at each insect location to extract the crop code from the raster.
    5. Maps the crop code to a human-readable crop type using the provided `crop_mapping_dict`.
    6. Merges the crop type information back into the original point GeoDataFrame.
    7. Returns the updated GeoDataFrame with crop types.

    Example Usage:
    --------------
    point_df = gpd.read_file('insect_locations.shp')  # GeoDataFrame with insect data
    crop_raster_folder = 'path/to/crop_raster_folder'
    crop_mapping_dict = {1: 'Corn', 2: 'Wheat', 3: 'Soybeans', ...}  # Example mapping

    # Finding crop types at insect locations
    updated_point_df = find_crops_for_insect_locations(point_df, crop_raster_folder, 'objectid', crop_mapping_dict)

    Notes:
    ------
    - The crop raster files should be organized in subfolders named by year (e.g., '2008_30m_cdls', '2009_30m_cdls').
    - The function assumes that the CRS of the insect point data will be reprojected to match the crop raster files.
    """
    
    results = []
    total_sample_processed = 0

    # Group the insect point data by year
    grouped = point_df.groupby('year')

    for year, group in grouped:
        # Count the number of samples for this year
        sample_count = group[id_column].count()
        print(f'Processing {sample_count} samples for the year {year}...\n')

        # Skip years outside the available crop raster range (2008-2023)
        if year not in range(2008, 2024):
            continue

        # Construct the raster file path for the specific year
        raster_file = f'{crop_raster_folder}/{year}_30m_cdls/{year}_30m_cdls.tif'
        
        # Open the raster file and extract crop values at insect locations
        with rasterio.open(raster_file) as src:
            # Reproject the insect points to match the raster's CRS
            group = group.to_crs(src.crs)
            
            # Iterate over each insect point in the group
            for idx, row in group.iterrows():
                insect_location = [(row.geometry.x, row.geometry.y)]
                
                # Sample the raster to find the crop code at the insect location
                crop_code = list(src.sample(insect_location))[0][0]
                
                # Append the result to the results list
                results.append({
                    'insect_id': row[id_column],
                    'crop_code': crop_code
                })
        
        total_sample_processed += sample_count
    
    # Print total processed samples
    print(f'Processed_samples/total_samples: {total_sample_processed}/{point_df.shape[0]}')

    # Convert results into a DataFrame
    result_df = pd.DataFrame(results)
    result_df['crop'] = result_df['crop_code'].map(crop_mapping_dict)

    # Merge the crop data back into the original point DataFrame
    point_df = pd.merge(point_df, result_df, how='left', left_on=id_column, right_on='insect_id')
    
    # perform data imputation. Replace none/nodata value with mode of crop column
    point_df.loc[(point_df['crop'].isna()) | (point_df['crop'] == 'NoData'), 'crop'] = point_df['crop'].mode()[0]
    
    return point_df


# Function to merge insect_crop data with bioclim variable
def bioclim_insect_intersection(climate_data_path, insect_crop_data, id_column):
    """
    Extracts bioclimatic values from a set of .netcdf files at the locations and years 
    specified in the insect_crop_data and adds them as columns in the GeoDataFrame.

    Parameters:
    -----------
    climate_data_path : str
        The path to the directory containing .netcdf files with bioclimatic data.
    insect_crop_data : GeoDataFrame
        A GeoDataFrame containing point geometries (latitude, longitude) and year of observation.
    id_column : str
        The name of the column in insect_crop_data that contains unique identifiers for the data points.

    Returns:
    --------
    GeoDataFrame
        The input GeoDataFrame with additional columns containing the bioclimatic variable values 
        at the coordinates and years corresponding to the insect_crop_data points.
    """
    
    # Step 1: Load and sort all .netcdf files from the given path
    netcdf_files = sorted([f for f in os.listdir(climate_data_path) if f.endswith('.nc')])
    
    # Step 2: Read all the netcdf files into a dictionary where the key is the variable name
    bioclim_data_dict = {}
    for idx, nc_file in enumerate(netcdf_files):
        file_path = os.path.join(climate_data_path, nc_file)
        dataset = xr.open_dataset(file_path)
        variable_name = list(dataset.data_vars)[0]  # Assuming each file has a unique variable
        bioclim_data_dict[variable_name] = dataset
        
        if idx == 0:    
            # Get latitude and longitude from the bioclim data. All files has same latitude and longitude grid.
            bioclim_lats = dataset['latitude'].values
            bioclim_lons = dataset['longitude'].values
        
        print(f"{file_path.split('_')[0]} | the latitude shape : {dataset['latitude'].values.shape} | the longitude shape : {dataset['longitude'].values.shape} | the time slices : {dataset['time'].values.shape}")
    
    
    # Step 3: Add bioclimatic variables as columns to the insect_crop_data, initialized to zero
    for variable_name in bioclim_data_dict.keys():
        insect_crop_data[variable_name] = 0.0  # Initialize with zeros
    
    # Step 4: Group the insect point data by year
    grouped = insect_crop_data.groupby('year')

    # Step 5: Iterate over each year and group of insect points, then extract bioclimatic values
    for year, group in grouped:
        
        # Count the number of samples for this year
        sample_count = group[id_column].count()
        
        # Bioclim data starts at year 1950 (adjust as needed)
        time_idx = year - 1950
        
        
        print(f'Processing {sample_count} samples for the year {year}, and time_idx in netcdf file {time_idx}...')
        
        # Iterate over each insect point in the group
        for idx, row in group.iterrows():
            longitude, latitude = row.geometry.x, row.geometry.y
            
            # Iterate over each bioclimatic dataset (each variable) in the dictionary
            for variable_name, bioclim_data in bioclim_data_dict.items():
                
                assert year == bioclim_data['time'].dt.year[time_idx].item(), f'Something wrong with the year. The insect_data year is {year}, the bioclim data year is {bioclim_data['time'].dt.year[time_idx].item()}'
                
                # Find the nearest indices in the bioclimatic data
                lat_idx = np.abs(bioclim_lats - latitude).argmin()
                lon_idx = np.abs(bioclim_lons - longitude).argmin()
                
                # Extract the value for the current variable, year, and point location
                bioclim_value = bioclim_data.isel(time=time_idx, latitude=lat_idx, longitude=lon_idx)[variable_name].values.item()
                
                # Update the corresponding row and column in insect_crop_data with the extracted value
                insect_crop_data.at[idx, variable_name] = bioclim_value
    
    return insect_crop_data


# Function to plot the data
def plot_data(gdf, save_path, insect_name, markersize_col=None, date_column='day', show_plots=True):
    """
    Plots spatial and temporal data of insect observations.

    Args:
        gdf (GeoDataFrame): The GeoDataFrame containing the data to be plotted.
        save_path (str or Path): The directory path where the plots will be saved.
        insect_name (str): The name of the insect being observed, used in the plot filenames.
        markersize_col (str, optional): The column name to be used for determining the size of the markers in the geographic plot. Default is None.
        date_column (str, optional): The name of the date column. Default is 'day'.
        show_plots (bool, optional): Whether to display the plots. Default is True.

    Returns:
        None
    """
    
    # Plot the points inside a US map, with size of point corresponding to the number of bugs observed
    if isinstance(markersize_col, str):
        gdf.plot(marker='o', column='label', markersize=gdf[markersize_col], cmap='viridis', legend=True)  
    else:
        gdf.plot(marker='o', column='label', cmap='viridis', legend=True)
        
    plt.title("Number of Bugs Observed at Locations")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()  # Ensures layout is nice
    
    if isinstance(save_path, (str, pathlib.PosixPath)):  
        plt.savefig(os.path.join(save_path, insect_name + '_map.png'))
    if show_plots:
        plt.show()
    else:
        plt.close()

    # Plotting a time series plot, which shows how many bugs have been observed over different years
    plt.figure(figsize=(15, 4))
    gdf.groupby(date_column).size().sort_index().plot(kind='line', marker='o')
    plt.title('Time Series of Observations')
    plt.xlabel('Date')
    plt.ylabel('Number of Observations')
    plt.xticks(rotation=45)
    plt.tight_layout()  # Ensures layout is nice
    
    if isinstance(save_path, (str, pathlib.PosixPath)):
        plt.savefig(os.path.join(save_path, insect_name + '_timeline.png'))
    if show_plots:
        plt.show()
    else:
        plt.close()
        
    print(gdf.head(2))

    # Plot a histogram showing the crop distribution in the data
    gdf['crop'].hist(figsize=(20, 5), grid=False)
    plt.xticks(rotation=90)
    plt.tight_layout()  # Ensures layout is nice
    
    if isinstance(save_path, (str, pathlib.PosixPath)):
        plt.savefig(os.path.join(save_path, insect_name + '_cropDistribution.png'))
    if show_plots:
        plt.show()
    else:
        plt.close()

    # Plot histograms for all columns (especially bioclim data)
    gdf.hist(figsize=(30, 20), grid=False)
    plt.tight_layout()  # Ensures layout is nice
    
    if isinstance(save_path, (str, pathlib.PosixPath)):
        plt.savefig(os.path.join(save_path, insect_name + '_BioClimDistribution.png'))
    if show_plots:
        plt.show()
    else:
        plt.close()
