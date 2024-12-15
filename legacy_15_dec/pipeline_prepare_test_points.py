import argparse
import os
import pandas as pd

from maxent_insect_dir.config import *
from maxent_insect_dir.utils_common import *
from maxent_insect_dir.prepare_background import *
from maxent_insect_dir.insect_crop_intersection import *
from maxent_insect_dir.LUH2.LUH2 import get_LUH2_yearly, write_LUH2_to_raster
from maxent_insect_dir.bioclim.compute_bioclim_average_CDS import get_bioclims_cds

# Argument parser to accept  DOWNLOAD_SOURCE, and CLIMATE_SOURCE from command line
parser = argparse.ArgumentParser(description='Pipeline to prepare test points')
parser.add_argument('--year', type=int, required=True, help='The year for which the LHU2 and Bioclim data is calculated')

args = parser.parse_args()


# Use the command-line arguments for INSECT_NAME, DOWNLOAD_SOURCE, and CLIMATE_SOURCE
YEAR = args.year

# Dynamically set data based on the climate data source
PATH_ = os.path.join(PATH_TO_SAVE_TEST_DATA, f'{YEAR}')


# Check if the directories exist, create them if necessary
if not os.path.exists(PATH_):
    os.makedirs(PATH_)
    print(f"Directory {PATH_} created.")
else:
    print(f"Directory {PATH_} already exists.")


# Load crop mapping and create a mapping dictionary
crop_mapping = pd.read_csv(config_raw['crop_mapping_config'])
crop_mapping_dict = dict(zip(crop_mapping['Code'], crop_mapping['Crop']))

print(f'We are creating test-set for year: {YEAR}...\n\n')

available_years = [2021,2040,2060,2080,2100]

if YEAR not in available_years:
    print(f'Worldclim data is available only for year: {available_years}')
    import sys; sys.exit()



# count = 10000
# test_points = draw_background(count=count)
## This is required, and will act as id. 
# test_points.reset_index(inplace=True)

path_to_load_background = pathlib.Path('/data/Maxent/data/processed/Test/Background_count_10000.gpkg')
print(f'Step 1: Load the test data from path {path_to_load_background}...\n\n')
test_points = safe_read_file(path_to_load_background)
test_points.plot()
plt.show()


print('Step 2: Getting the crop intersection...\n\n')
# Get the crop-insect intersection
test_points,_,_,_ = crops_insect_intersection_background(
    gdf=test_points,
    crop_raster_config=config_raw['crop_data'],
    id_column='index',
    crop_mapping_dict=crop_mapping_dict
)


print('Step 3: Getting the LUH data...\n\n')
# read and write the raster layer for a particular year to the folder
temp = get_LUH2_yearly(YEAR)
temp_path= os.path.join(config_LUH2['yearly'],str(YEAR))
write_LUH2_to_raster(dataset=temp, save_path=temp_path)

# Get the intersection
test_points = LUH2_intersection(
    raster_path=temp_path,
    gfd=test_points,
    id_column='index',
    label_prefix=f'LUH2_{YEAR}_AVG_'    
)


print(F'Step 4: Getting the Bioclim for {YEAR} (CDS)...\n\n')
# read and write the raster layer for a particular year to the folder
get_bioclims_cds(year=YEAR, save=True)

# this is the path where file after computing the bioclims is saved
temp_path = os.path.join(pathlib.Path("/data/Maxent/data/raw/Bioclim_CDS_yearly"),str(YEAR))
# get the bioclim intersection for cds
test_points = bioclim_avg_insect_intersection(
        raster_path=temp_path,
        gfd=test_points,
        id_column='index',
        label_prefix=f'CDS_{YEAR}_'
    )


print(f'Step 5: Getting the Bioclim for {YEAR} (Worldclim)....\n\n')

if YEAR==2021:
    temp_path = os.path.join(pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_1990_2021'))
elif YEAR==2040:
    temp_path = os.path.join(pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2021_2040'))
elif YEAR==2060:
    temp_path = os.path.join(pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2041_2060'))
elif YEAR==2080:
    temp_path = os.path.join(pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2061_2080'))
else:
    temp_path = os.path.join(pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2081_2100'))
    
# get the bioclim intersection for worldclim
test_points = bioclim_avg_insect_intersection(
        raster_path=temp_path,
        gfd=test_points,
        id_column='index',
        label_prefix=f'WORLDCLIM_{YEAR}_'
    )

    
# Save the data
print(f'Step 6: Saving the Data...\n\n')
# Save the cleaned and processed data to a GeoPackage file
test_points.to_file(
    os.path.join(PATH_,f'{YEAR}_count_10000.gpkg'),  # File path to save the data
    driver='GPKG',  # Specify the file format (GeoPackage)
    layer='PointLayer'  # Layer name for saving point data
)