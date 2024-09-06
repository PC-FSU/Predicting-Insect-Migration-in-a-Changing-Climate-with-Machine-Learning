# Common Setup
from maxent_insect_dir import config
from data_utils import *

# Define paths and insect name
INSECT_NAME = 'Root_Weevil'  
DOWNLOAD_SOURCE = 'GBIF' # either GBIF or EDD
INSECT_DATA = config.config_['insect'][DOWNLOAD_SOURCE][INSECT_NAME]
INTERIM_PATH = config.PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA
PATH_SAVE_FIG = config.PATH_TO_SAVE_INITIAL_DATA_VIS_INSECT

# Load the presence data
presence = safe_read_file(INSECT_DATA)


# Clean and prepare the data
if DOWNLOAD_SOURCE == 'GBIF':
    # Clean the data
    presence_cleaned = clean_and_prepare_data_for_GBIF(
        presence,
        date_column='day'
    )
    # Plot the data
    plot_data(
        gdf = presence_cleaned,
        save_path=PATH_SAVE_FIG,
        insect_name=INSECT_NAME, 
        date_column='day'
    )
    
    # Save the data
    presence_cleaned.to_file(
        os.path.join(INTERIM_PATH, f'{INSECT_NAME}_{DOWNLOAD_SOURCE}_intermediatory.gpkg'),
        driver='GPKG',
        layer='PointLayer'
    )
    
else:
    # Clean the data
    presence_cleaned = clean_and_prepare_data_for_EDD(
        presence,
        keep_columns=['ObsDate','DateEnt','OccStatus','NumCollect','Latitude','Longitude','geometry'],
        date_column='ObsDate',
        status_column='OccStatus',
        count_column='NumCollect'
    )
    # Plot the data
    plot_data(
        gdf=presence_cleaned,
        save_path=PATH_SAVE_FIG,
        insect_name=INSECT_NAME,
        markersize_col='NumCollect_int', # This should be in returned df from clean_and_prepare_data_for_EDD
        date_column='ObsDate'
    )
    
    # Save the data
    presence_cleaned.to_file(
        os.path.join(INTERIM_PATH, f'{INSECT_NAME}_{DOWNLOAD_SOURCE}_intermediatory.gpkg'),
        driver='GPKG',
        layer='PointLayer'
    )
    
    
