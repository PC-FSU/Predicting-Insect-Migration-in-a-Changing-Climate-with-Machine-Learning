import argparse
import os
import pandas as pd
import elapid as ela
from maxent_insect_dir.config import *
from maxent_insect_dir.utils_common import *
from maxent_insect_dir.utils_process_insect_data import *
from maxent_insect_dir.insect_crop_intersection import *
from maxent_insect_dir.prepare_presence import *
from maxent_insect_dir.prepare_background import *

import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")


def get_presence(insect_source, insect_name, crop_mapping_dict, path_save_fig, path_save_data):

    # Load the presence data
    presence = safe_read_file(config_raw['insect'][insect_source][insect_name])
    
    # Clean and prepare the data
    print(f'Step 1: Cleaning raw insect data...\n\n')
    presence = clean_insect_data(insect_source, presence)
    # Keep only label == 1
    presence = presence[presence['label'] == 1].reset_index(drop=True)

    print(f'Step 2: Perform spatial thinning...\n\n')
    if presence.crs.is_geographic:
        # change the crs to 5070
        presence = presence.to_crs(epsg=5070) 

    original_presence_count = presence.shape[0]
    presence = spatial_thinning(presence, min_distance=spatial_thinning_distance[insect_name])   
    presence['SampleWeight'] = ela.distance_weights(presence, n_neighbors=-1, center=None)
    
    print(f'Original presence count : {original_presence_count} | presence thinned count: {presence.shape[0]}..\n\n')

    print('Step 3: Getting the crop intersection...\n\n')
    # Get the crop-insect intersection
    presence_crop = crops_insect_intersection_presence(
        point_df=presence,
        crop_raster_config=config_raw['crop_data'],
        id_column='objectid',
        crop_mapping_dict=crop_mapping_dict
    )
    
    # Get crop and bioclim intersection
    print(f'Step 4: Getting intersection between insect data, crop data, and BioClim data...\n\n')
    presence_crop_bioclim = get_crop_bioclim_intersection_presence(presence_crop)
    
    
    # Plot and save the data
    print(f'Step 5: Plotting data distributions and saving the results...\n\n')
    if insect_source == 'GBIF':
        plot_presence_data(presence_crop_bioclim, path_save_fig, insect_name, date_column='day')
    else:
        plot_presence_data(presence_crop_bioclim, path_save_fig, insect_name, date_column='ObsDate')
    
    # Save the cleaned and processed data to a GeoPackage file
    presence_crop_bioclim.to_file(path_save_data, driver='GPKG', layer='PointLayer')

    return presence_crop_bioclim


def get_background(presence, count, weight, crop_mapping_dict, path_save_fig, path_save_data):
    print(f'Step 1: Generate the background data...\n\n')
    background = spatial_weighting(presence, weight=weight, count=count)
    # This is required, and will act as id. 
    background.reset_index(inplace=True)

    if background.crs.is_geographic:
        # change the crs to 5070
        background = background.to_crs(epsg=5070) 
    
    print('Step 2: Getting the crop intersection...\n\n')
    # Get the crop-insect intersection
    background_crop,_,_,_ = crops_insect_intersection_background(
        gdf=background,
        crop_raster_config=config_raw['crop_data'],
        id_column='index',
        crop_mapping_dict=crop_mapping_dict
    )
    
    # Get crop and bioclim intersection
    print(f'Step 3: Getting intersection between insect data, crop data, and BioClim data...\n\n')
    background_crop_bioclim = get_crop_bioclim_intersection_background(gdf=background_crop, id_column='index')

    
    background_crop_bioclim.plot(alpha=0.1)
    plt.savefig(os.path.join(path_save_fig, 'background.png'))
    
    # Save the data
    print(f'Step 4: Saving the Data...\n\n')
    # Save the cleaned and processed data to a GeoPackage file
    background_crop_bioclim.to_file(path_save_data,  driver='GPKG',  layer='PointLayer')


if __name__ =='__main__':

    # Argument parser to accept INSECT_NAME, DOWNLOAD_SOURCE, and CLIMATE_SOURCE from command line
    parser = argparse.ArgumentParser(description='Pipeline to prepare presence and background points')
    parser.add_argument('--insect_name', type=str, required=True, help='The name of the insect to process.')
    parser.add_argument('--insect_source', type=str, required=True, choices=['EDD', 'GBIF'], help='The data source to use (either EDD or GBIF).')
    #parser.add_argument('--climate_source', type=str, required=True, choices=['WorldClim', 'CDS'], help='The climate data source to use (either WorldClim or CDS).')
    parser.add_argument('--spatial_weight', type=float, required=True, help='weight 1 means all background point are selected from the bias, 0 mean everything are selected uniformly')
    parser.add_argument('--count', type=int, required=True, help='Total number of background point to generate')


    args = parser.parse_args()

    # Use the command-line arguments for INSECT_NAME, DOWNLOAD_SOURCE, and CLIMATE_SOURCE
    insect_name = args.insect_name
    insect_source = args.insect_source
    #climate_source = args.climate_source
    spatial_weight = args.spatial_weight
    count = args.count


    # Define paths and insect data based on the command-line arguments
    insect_data = config_raw['insect'][insect_source][insect_name]

    # Dynamically set paths based on passed args
    PRESENCE_POINT_PATH = os.path.join(PATH_TO_SAVE_PRESENCE_POINTS, f'spatial_weight_{spatial_weight}')
    PATH_SAVE_PRESENCE = os.path.join(PRESENCE_POINT_PATH, f'{insect_name}_intermediatory.gpkg')
    PATH_PRESENCE_SAVE_FIG = os.path.join(PATH_TO_SAVE_DATA_VISUALIZATION_INSECT, 'presence', f'spatial_weight_{spatial_weight}')
    
    BACKGROUND_POINT_PATH = os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, f'spatial_weight_{spatial_weight}')
    PATH_SAVE_BACKGROUND = os.path.join(BACKGROUND_POINT_PATH, f'{insect_name}_intermediatory.gpkg')
    PATH_BACKGROUND_SAVE_FIG = os.path.join(PATH_TO_SAVE_DATA_VISUALIZATION_INSECT, 'backgroud', f'spatial_weight_{spatial_weight}')
    
    check_dirs = [PRESENCE_POINT_PATH, BACKGROUND_POINT_PATH, PATH_PRESENCE_SAVE_FIG, PATH_BACKGROUND_SAVE_FIG]
    for dir in check_dirs:
        # Check if the directories exist, create them if necessary
        if not os.path.exists(dir):
            os.makedirs(dir)
            print(f"Directory {dir} created.")
        else:
            print(f"Directory {dir} already exists.")


    # Load crop mapping and create a mapping dictionary
    crop_mapping = pd.read_csv(config_raw['crop_mapping_config'])
    crop_mapping_dict = dict(zip(crop_mapping['Code'], crop_mapping['Crop']))

    print(f'Insect : {insect_name} | downloaded source: {insect_source}...\n\n')
    
    print(f'######################### Get Presence point ############################...\n\n')
    presence = get_presence(insect_source, insect_name, crop_mapping_dict, PATH_PRESENCE_SAVE_FIG, PATH_SAVE_PRESENCE)
    
    print(f'######################### Get Background point ############################...\n\n')
    get_background(presence, count, spatial_weight, crop_mapping_dict, PATH_BACKGROUND_SAVE_FIG, PATH_SAVE_BACKGROUND)
    
    