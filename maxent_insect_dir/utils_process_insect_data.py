import geopandas as gpd
import pandas as pd

from maxent_insect_dir.utils_common import *


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
    
    # Trim the GeoDataFrame to keep only the specified columns
    gdf_trimmed = gdf.loc[:, keep_columns].copy()

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

    return drop_points_outside_us(gdf_trimmed)
