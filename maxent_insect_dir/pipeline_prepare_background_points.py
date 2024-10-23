import argparse
import os
import pandas as pd

from maxent_insect_dir.config import *
from maxent_insect_dir.utils_common import *
from maxent_insect_dir.prepare_background import *
from maxent_insect_dir.insect_crop_intersection import *
from maxent_insect_dir.prepare_presence import plot_and_save_data

# Argument parser to accept INSECT_NAME, DOWNLOAD_SOURCE, and CLIMATE_SOURCE from command line
parser = argparse.ArgumentParser(description='Pipeline to prepare background points')
parser.add_argument('--insect_name', type=str, required=True, help='The name of the insect to process.')
parser.add_argument('--download_source', type=str, required=True, choices=['EDD', 'GBIF'], help='The data source to use (either EDD or GBIF).')
parser.add_argument('--climate_source', type=str, required=True, choices=['WorldClim', 'CDS'], help='The climate data source to use (either WorldClim or CDS).')
parser.add_argument('--use_Bias_raster', type=bool, required=True, help='If True, bias_raster will be used. If False, points will be drawn uniformly.')

args = parser.parse_args()


# Use the command-line arguments for INSECT_NAME, DOWNLOAD_SOURCE, and CLIMATE_SOURCE
INSECT_NAME = args.insect_name
DOWNLOAD_SOURCE = args.download_source
CLIMATE_SOURCE = args.climate_source
USE_BIAS_RASTER = args.use_Bias_raster

# Define paths and insect data based on the command-line arguments
INSECT_DATA = config_raw['insect'][DOWNLOAD_SOURCE][INSECT_NAME]

# Dynamically set interim and save paths based on the climate data source
INTERIM_PATH = os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, CLIMATE_SOURCE)
PATH_SAVE_DATA = os.path.join(INTERIM_PATH, f'{INSECT_NAME}_{DOWNLOAD_SOURCE}_intermediatory.gpkg')
PATH_SAVE_FIG = os.path.join(PATH_TO_SAVE_INITIAL_DATA_VIS_INSECT, CLIMATE_SOURCE)


# Check if the directories exist, create them if necessary
if not os.path.exists(INTERIM_PATH):
    os.makedirs(INTERIM_PATH)
    print(f"Directory {INTERIM_PATH} created.")
else:
    print(f"Directory {INTERIM_PATH} already exists.")

if not os.path.exists(PATH_SAVE_FIG):
    os.makedirs(PATH_SAVE_FIG)
    print(f"Directory {PATH_SAVE_FIG} created.")
else:
    print(f"Directory {PATH_SAVE_FIG} already exists.")
    





# Load crop mapping and create a mapping dictionary
crop_mapping = pd.read_csv(config_raw['crop_mapping_config'])
crop_mapping_dict = dict(zip(crop_mapping['Code'], crop_mapping['Crop']))

print(f'We are looking at insect: {INSECT_NAME}, downloaded from the source: {DOWNLOAD_SOURCE}, and working with the climate date: {CLIMATE_SOURCE}...\n\n')



if __name__ == "__main__":
    
    print(f'Step 1: Generate the backgropund data...\n\n')
    count = 10000
    if USE_BIAS_RASTER:
        bias_raster = config_bias_rasters[INSECT_NAME]
        background = draw_background(bias_raster, count=count)
    else:
        background = draw_background(count=count)
    background.plot()
    plt.show()
    # This is required, and will act as id. 
    background.reset_index(inplace=True)
    
    
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
    background_crop_bioclim = get_crop_bioclim_intersection_background(
        gdf=background_crop,
        id_column='index',
        climate_source=CLIMATE_SOURCE
    )
    
    
    # Save the data
    print(f'Step 4: Saving the Data...\n\n')
    # Save the cleaned and processed data to a GeoPackage file
    background_crop_bioclim.to_file(
        PATH_SAVE_DATA,  # File path to save the data
        driver='GPKG',  # Specify the file format (GeoPackage)
        layer='PointLayer'  # Layer name for saving point data
    )
