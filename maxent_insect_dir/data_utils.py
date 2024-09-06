# Common Imports
from maxent_insect_dir import config
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import pathlib
import os

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
    gdf_trimmed['Year'] = gdf_trimmed[date_column].dt.year
    gdf_trimmed['month'] = gdf_trimmed[date_column].dt.month
    gdf_trimmed['day_number'] = gdf_trimmed[date_column].dt.day
    
    return gdf_trimmed





# Function to plot the data
def plot_data(gdf, save_path, insect_name, markersize_col=None, date_column='day'):
    """
    Plots spatial and temporal data of insect observations.

    Args:
        gdf (GeoDataFrame): The GeoDataFrame containing the data to be plotted.
        save_path (str or Path): The directory path where the plots will be saved.
        insect_name (str): The name of the insect being observed, used in the plot filenames.
        markersize_col (str, optional): The column name to be used for determining the size of the markers in the geographic plot. Default is None.
        date_column (str, optional): The name of the date column. Default is 'day'.

    Returns:
        None
    """
    # Plot the points, with size corresponding to the number of bugs observed
    if isinstance(markersize_col, str):
        gdf.plot(marker='o', column='label', markersize=gdf[markersize_col], cmap='viridis', legend=True)  
    else:
        gdf.plot(marker='o', column='label', cmap='viridis', legend=True)
        
    plt.title("Number of Bugs Observed at Locations")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    
    if isinstance(save_path, (str, pathlib.PosixPath)):  
        plt.savefig(os.path.join(save_path, insect_name + '_map.png'))
    plt.show()
    
    # Plotting a time series plot
    plt.figure(figsize=(15, 4))
    gdf.groupby(date_column).size().sort_index().plot(kind='line', marker='o')
    plt.title('Time Series of Observations')
    plt.xlabel('Date')
    plt.ylabel('Number of Observations')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if isinstance(save_path, (str, pathlib.PosixPath)):
        plt.savefig(os.path.join(save_path, insect_name + '_timeline.png'))
    plt.show()
