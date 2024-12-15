from utils_presence import *
import argparse



# Argument parser to accept INSECT_NAME, DOWNLOAD_SOURCE, and CLIMATE_SOURCE from command line
parser = argparse.ArgumentParser(description='Pipeline to prepare presence points')
parser.add_argument('--insect_name', type=str, required=True, help='The name of the insect to process.')
parser.add_argument('--download_source', type=str, required=True, choices=['EDD', 'GBIF'], help='The data source to use (either EDD or GBIF).')
parser.add_argument('--climate_source', type=str, required=True, choices=['WorldClim', 'CDS'], help='The climate data source to use (either WorldClim or CDS).')

args = parser.parse_args()

# Use the command-line arguments for INSECT_NAME, DOWNLOAD_SOURCE, and CLIMATE_SOURCE
INSECT_NAME = args.insect_name
DOWNLOAD_SOURCE = args.download_source
CLIMATE_SOURCE = args.climate_source

# Define paths and insect data based on the command-line arguments
INSECT_DATA = config.config_raw['insect'][DOWNLOAD_SOURCE][INSECT_NAME]

# Dynamically set interim and save paths based on the climate data source
INTERIM_PATH = os.path.join(config.PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, CLIMATE_SOURCE)
PATH_SAVE_DATA = os.path.join(INTERIM_PATH, f'{INSECT_NAME}_{DOWNLOAD_SOURCE}_intermediatory.gpkg')
PATH_SAVE_FIG = os.path.join(config.PATH_TO_SAVE_INITIAL_DATA_VIS_INSECT, CLIMATE_SOURCE)


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

# Load the presence data
presence = safe_read_file(INSECT_DATA)

# Load crop mapping and create a mapping dictionary
crop_mapping = pd.read_csv(config.config_raw['crop_mapping_config'])
crop_mapping_dict = dict(zip(crop_mapping['Code'], crop_mapping['Crop']))

print(f'We are looking at insect: {INSECT_NAME}, downloaded from the source: {DOWNLOAD_SOURCE}, and working with the climate date: {CLIMATE_SOURCE}...\n\n')



if __name__ == "__main__":
    # Clean and prepare the data
    print(f'Step 1: Cleaning raw insect data...\n\n')
    presence_cleaned = clean_insect_data(DOWNLOAD_SOURCE, presence)

    # Get crop and bioclim intersection
    print(f'Step 2: Getting intersection between insect data, crop data, and BioClim data...\n\n')
    presence_cleaned_crop_bioclim = get_crop_bioclim_intersection(presence_cleaned, crop_mapping_dict, CLIMATE_SOURCE)

    # Plot and save the data
    print(f'Step 3: Plotting data distributions and saving the results...\n\n')
    if DOWNLOAD_SOURCE == 'GBIF':
        plot_and_save_data(presence_cleaned_crop_bioclim, PATH_SAVE_FIG, PATH_SAVE_DATA, INSECT_NAME, date_column='day')
    else:
        plot_and_save_data(presence_cleaned_crop_bioclim, PATH_SAVE_FIG, PATH_SAVE_DATA, INSECT_NAME, date_column='ObsDate')
