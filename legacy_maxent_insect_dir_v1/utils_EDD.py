import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from MaxEnt_insect_dir.maxent_insect_dir.config import *
from MaxEnt_insect_dir.maxent_insect_dir.utils_common import *


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

    return drop_points_outside_us(gdf_trimmed)
