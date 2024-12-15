import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from MaxEnt_insect_dir.maxent_insect_dir.config import *
from MaxEnt_insect_dir.maxent_insect_dir.utils_common import *


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
        
    return drop_points_outside_us(gdf_trimmed)