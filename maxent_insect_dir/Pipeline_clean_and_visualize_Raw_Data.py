# Common Setup
from maxent_insect_dir import config
from data_utils import *


# Define paths and insect name
INSECT_NAME = 'Brown_Marmorated_Stink_bug'  
DOWNLOAD_SOURCE = 'EDD' # either GBIF or EDD
INSECT_DATA = config.config_raw['insect'][DOWNLOAD_SOURCE][INSECT_NAME]
INTERIM_PATH = config.PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA
PATH_SAVE_FIG = config.PATH_TO_SAVE_INITIAL_DATA_VIS_INSECT

# Load the presence data
presence = safe_read_file(INSECT_DATA)

#load crop mapping
crop_mapping = pd.read_csv(config.config_raw['crop_config'])
# Create a mapping dictionary
crop_mapping_dict = dict(zip(crop_mapping['Code'], crop_mapping['Crop']))



# Clean and prepare the data
if DOWNLOAD_SOURCE == 'GBIF':
    # Clean the data
    presence_cleaned = clean_and_prepare_data_for_GBIF(
        presence,
        date_column='day'
    )
        
    # Get the crop intersection
    presence_cleaned_crop = find_crops_for_insect_locations(
        point_df=presence_cleaned,
        crop_raster_folder=config.CROP_DATA,
        id_column = 'objectid',
        crop_mapping_dict=crop_mapping_dict
    )
    
    # Get the Bioclim intersection
    presence_cleaned_crop_bioclim = bioclim_insect_intersection(
        climate_data_path=config.config_raw['BioClim_data'],
        insect_crop_data=presence_cleaned_crop,
        id_column='objectid'
    )
    
    # Plot the data
    plot_data(
        gdf = presence_cleaned_crop_bioclim,
        save_path=PATH_SAVE_FIG,
        insect_name=INSECT_NAME, 
        date_column='day'
    )
    
    # Save the data
    presence_cleaned_crop_bioclim.to_file(
        os.path.join(INTERIM_PATH, f'{INSECT_NAME}_{DOWNLOAD_SOURCE}_intermediatory.gpkg'),
        driver='GPKG',
        layer='PointLayer'
    )
    
else:
    # Clean the data
    presence_cleaned = clean_and_prepare_data_for_EDD(
        presence,
        keep_columns=['objectid','ObsDate','DateEnt','OccStatus','NumCollect','Latitude','Longitude','geometry'],
        date_column='ObsDate',
        status_column='OccStatus',
        count_column='NumCollect'
    )
    
    
    # Get the crop intersection
    presence_cleaned_crop = find_crops_for_insect_locations(
        point_df=presence_cleaned,
        crop_raster_folder=config.CROP_DATA,
        id_column = 'objectid',
        crop_mapping_dict=crop_mapping_dict
    )
    
    # Get the Bioclim intersection
    presence_cleaned_crop_bioclim = bioclim_insect_intersection(
        climate_data_path=config.config_raw['BioClim_data'],
        insect_crop_data=presence_cleaned_crop,
        id_column='objectid'
    )
    
    # Plot the data
    plot_data(
        gdf=presence_cleaned_crop_bioclim,
        save_path=PATH_SAVE_FIG,
        insect_name=INSECT_NAME,
        markersize_col='NumCollect_int', # This should be in returned df from clean_and_prepare_data_for_EDD
        date_column='ObsDate'
    )
    
    # Save the data
    presence_cleaned_crop_bioclim.to_file(
        os.path.join(INTERIM_PATH, f'{INSECT_NAME}_{DOWNLOAD_SOURCE}_intermediatory.gpkg'),
        driver='GPKG',
        layer='PointLayer'
    )
    
    
