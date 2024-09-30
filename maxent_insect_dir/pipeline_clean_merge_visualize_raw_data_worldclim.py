# Common Setup
from maxent_insect_dir import config
from raw_data_utilis import *
from worldclim_data_utilis import *

# Define paths and insect name
INSECT_NAME = 'Brown_Marmorated_Stink_bug'
DOWNLOAD_SOURCE = 'EDD'  # either GBIF or EDD
INSECT_DATA = config.config_raw['insect'][DOWNLOAD_SOURCE][INSECT_NAME]
INTERIM_PATH = os.path.join(config.PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, 'WorldClim') #updating the interim path
PATH_SAVE_FIG = os.path.join(config.PATH_TO_SAVE_INITIAL_DATA_VIS_INSECT, 'WorldClim')   #updating the savefig path

# Check if the directory exists
if not os.path.exists(INTERIM_PATH):
    # If it doesn't exist, create the directory
    os.makedirs(INTERIM_PATH)
    print(f"Directory {INTERIM_PATH} created.")
else:
    print(f"Directory {INTERIM_PATH} already exists.")


if not os.path.exists(PATH_SAVE_FIG):
    # If it doesn't exist, create the directory
    os.makedirs(PATH_SAVE_FIG)
    print(f"Directory {PATH_SAVE_FIG} created.")
else:
    print(f"Directory {PATH_SAVE_FIG} already exists.")
    

# Load the presence data
presence = safe_read_file(INSECT_DATA)

# Load crop mapping and create a mapping dictionary
crop_mapping = pd.read_csv(config.config_raw['crop_config'])
crop_mapping_dict = dict(zip(crop_mapping['Code'], crop_mapping['Crop']))

print(f'We are looking at insect: {INSECT_NAME}, downloaded from the source: {DOWNLOAD_SOURCE}...\n\n')

def clean_insect_data(source, presence):
    """Cleans insect data based on the source (GBIF or EDD)."""
    if source == 'GBIF':
        return clean_and_prepare_data_for_GBIF(presence, date_column='day')
    else:
        return clean_and_prepare_data_for_EDD(
            presence,
            keep_columns=['objectid', 'ObsDate', 'DateEnt', 'OccStatus', 'NumCollect', 'Latitude', 'Longitude', 'geometry'],
            date_column='ObsDate',
            status_column='OccStatus',
            count_column='NumCollect'
        )

def get_crop_bioclim_intersection(cleaned_data, crop_mapping_dict):
    """Performs crop and bioclimatic data intersection for insect data."""
    
    print('\n.......Getting the crop intersection......\n')
    # Get the crop intersection
    cleaned_crop_data = find_crops_for_insect_locations(
        point_df=cleaned_data,
        crop_raster_folder=config.CROP_DATA,
        id_column='objectid',
        crop_mapping_dict=crop_mapping_dict
    )

    print('\n.......Getting the yearly avg for Bioclim......\n')
    # Get the Bioclim intersection using worldclim dataset -- the yearly averages
    insect_crop_data_with_yearly_avg =  worldclimbioclim_yearlyavg_insect_intersection(
        climate_data_path=config.config_worldclim['yearly_avg']['1970_2020'],
        insect_crop_data=cleaned_crop_data
    )
    
    print('\n.......Getting the monthly avg for Bioclim......\n')
    # Get the Bioclim intersection using worldclim dataset -- the monthly averages
    return worldclimbioclim_monthlyyavg_insect_intersection(
        climate_data_path=config.config_worldclim['monthly_avg'],
        insect_crop_data=insect_crop_data_with_yearly_avg,
        id_column='objectid'
    )

def plot_and_save_data(cleaned_bioclim_data, save_fig_path, insect_name, source, date_column, marker_size_col=None):
    """Plots and saves cleaned bioclimatic data."""
    # Plot the data
    plot_data(
        gdf=cleaned_bioclim_data,
        save_path=save_fig_path,
        insect_name=insect_name,
        date_column=date_column,
        markersize_col=marker_size_col
    )

    # Save the cleaned and processed data
    cleaned_bioclim_data.to_file(
        os.path.join(INTERIM_PATH, f'{insect_name}_{source}_intermediatory.gpkg'),
        driver='GPKG',
        layer='PointLayer'
    )

# Clean and prepare the data
print(f'Step 1: Cleaning raw insect data...\n\n')
presence_cleaned = clean_insect_data(DOWNLOAD_SOURCE, presence)

# Get crop and bioclim intersection
print(f'Step 2: Getting intersection between insect data, crop data, and BioClim data...\n\n')
presence_cleaned_crop_bioclim = get_crop_bioclim_intersection(presence_cleaned, crop_mapping_dict)

# Plot and save the data
print(f'Step 3: Plotting data distributions and saving the results...\n\n')
if DOWNLOAD_SOURCE == 'GBIF':
    plot_and_save_data(presence_cleaned_crop_bioclim, PATH_SAVE_FIG, INSECT_NAME, DOWNLOAD_SOURCE, date_column='day')
else:
    plot_and_save_data(presence_cleaned_crop_bioclim, PATH_SAVE_FIG, INSECT_NAME, DOWNLOAD_SOURCE, date_column='ObsDate', marker_size_col='NumCollect_int')

