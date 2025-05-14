import pathlib
import os


# This file contains paths pointing to different assets in the project.

#---------------------------------------- Base_paths -----------------------------------------


# Path to save initial visualization of insect map and time series
# PATH_TO_SAVE_DATA_VISUALIZATION_INSECT = pathlib.Path("/home/pc19d/postdoc/MaxEnt_insect_dir/reports/figures") # Not using anymore

# # Path to save processed insect data. 
# PATH_TO_SAVE_PRESENCE_POINTS = pathlib.Path("/data/Maxent/data/interim/presence") # Not using anymore

# Path to clean data -- removed non-us point, and outliers.
PATH_TO_CLEAN_DATA = pathlib.Path("/data/Maxent/data/data/Species_Data/Clean_Data") 

#Path to the folder where all crop data is present.
# CROP_DATA = pathlib.Path("/data/Maxent/data/raw/crop_data") # Not using anymore

# Path where the models is saved
PATH_TO_SAVE_RESULTS = pathlib.Path("/data/Maxent/data/results")

# Path to US boundary shapefile
PATH_TO_US_BOUNDARY = pathlib.Path("/data/Maxent/data/data/US_shapefile/US_shapefile.shp")


# Path to test data
PATH_TO_TEST_DATA = pathlib.Path('/data/Maxent/data/data/Test_data/test.gpkg')


#---------------------------------------- To config insects -----------------------------------------

Insect_list = {
    'Brown_Marmorated_Stink_bug': pathlib.Path(
        os.path.join(PATH_TO_CLEAN_DATA, "Brown_Marmorated_Stink_Bug_Halyomorpha_halys_1999_2023.gpkg")
        ),
    'Corn_Earworm': pathlib.Path(
        os.path.join(PATH_TO_CLEAN_DATA, "Corn_Earworm_Helicoverpa_Zea_2004_2023.gpkg")
        ),
    'Large_Lady_Beetle': pathlib.Path(
        os.path.join(PATH_TO_CLEAN_DATA, "Large_Lady_Beetle_Harmonia_Axyridis_1995_2023.gpkg")
        ),
    'Root_Weevil': pathlib.Path(
        os.path.join(PATH_TO_CLEAN_DATA, "Root_Weevil_Diaprepes_abbreviatus_2012_2023.gpkg")
        ),
    'Spongy_Moth': pathlib.Path(
        os.path.join(PATH_TO_CLEAN_DATA, "spongy_moth_(formerly_gypsy_moth)_(Lymantria_dispar).gpkg")
        ),
    'Spooted_Lanternfly': pathlib.Path(
        os.path.join(PATH_TO_CLEAN_DATA, "spotted_lanternfly_(Lycorma_delicatula).gpkg")
        )
}

#---------------------------------------- To config crop -----------------------------------------

# Dictionary to store all path to the raster file for crop data
PATH_TO_MOST_GROWN_CROP = pathlib.Path("/data/Maxent/data/raw/crop_data/reproject_most_grown_crop_1_min.tif")

# path to csv which contain the code:crop_name entries. 
Crop_mapping_config = pathlib.Path("/data/Maxent/data/raw/crop_data/cdl_codes_names.csv")


# Crop code like by each insect. These code are selected in a way that it represent the 90% of insect observation are associated with these crops.
dominant_crop_by_insect = {
    'Brown_Marmorated_Stink_bug' : [121, 141, 122, 123, 190],
    'Corn_Earworm' : [141, 1, 5, 190, 142, 176, 121, 2],
    'Large_Lady_Beetle' : [123, 141, 122, 121, 176, 124, 142, 190],
    'Root_Weevil' : [122, 123, 121, 190]
}

#---------------------------------------- To config climate -----------------------------------------

config_worldclim = {
    'avgs': {
        '1970_2000': pathlib.Path('/data/Maxent/data/data/Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio/Clipped/In_tiff_format'),
        '1990_2021': pathlib.Path('/data/Maxent/data/data/Bioclim_worldclim_average_1990_2021/Clipped/In_tiff_format'), # not using this time average, as this is computed by me. Only using avg from bioclim.
        '2021_2040': pathlib.Path('/data/Maxent/data/data/Bioclim_worldclim_average_2021_2040/Clipped/In_tiff_format'),
        '2041_2060': pathlib.Path('/data/Maxent/data/data/Bioclim_worldclim_average_2041_2060/Clipped/In_tiff_format'),
        '2061_2080': pathlib.Path('/data/Maxent/data/data/Bioclim_worldclim_average_2061_2080/Clipped/In_tiff_format'),
        '2081_2100': pathlib.Path('/data/Maxent/data/data/Bioclim_worldclim_average_2081_2100/Clipped/In_tiff_format')
    }
}


config_CDS = {
    'avgs': {}
}

# ---------------------------------------- Elevation data -----------------------------------------
PATH_TO_ELEVATION_DATA = pathlib.Path('/data/Maxent/data/data/Elevation/stanford-zz186ss2071-geotiff.tif')


#---------------------------------------- raw data config -----------------------------------------



#-------------------------------------- background points config --------------------------------



#---------------------------------------- test data config -----------------------------------------





# -------------------------------------- experiment config --------------------------------------------
# spatial thinning minium distance
spatial_thinning_distance = {
    'Brown_Marmorated_Stink_bug' : 10000,
    'Corn_Earworm' : 10000,
    'Large_Lady_Beetle' : 10000,
    'Brown_Marmorated_Stink_bug_2' : 10000,
    'Root_Weevil' : 10000,
    'Spongy_Moth': None, # Points are already well dispersed. 
    'Spooted_Lanternfly' : 10000
}

# 'Root_Weevil' : 500


#-------------------------------------- Bioclim Json --------------------------------------------------

Bioclim_mapping = {
  "Bio1": "Annual Mean Temperature",
  "Bio2": "Mean Diurnal Range (Mean of monthly (max temp - min temp))",
  "Bio3": "Isothermality (BIO2/BIO7) (×100)",
  "Bio4": "Temperature Seasonality (standard deviation ×100)",
  "Bio5": "Max Temperature of Warmest Month",
  "Bio6": "Min Temperature of Coldest Month",
  "Bio7": "Temperature Annual Range (BIO5-BIO6)",
  "Bio8": "Mean Temperature of Wettest Quarter",
  "Bio9": "Mean Temperature of Driest Quarter",
  "Bio10": "Mean Temperature of Warmest Quarter",
  "Bio11": "Mean Temperature of Coldest Quarter",
  "Bio12": "Annual Precipitation",
  "Bio13": "Precipitation of Wettest Month",
  "Bio14": "Precipitation of Driest Month",
  "Bio15": "Precipitation Seasonality (Coefficient of Variation)",
  "Bio16": "Precipitation of Wettest Quarter",
  "Bio17": "Precipitation of Driest Quarter",
  "Bio18": "Precipitation of Warmest Quarter",
  "Bio19": "Precipitation of Coldest Quarter"
}


# ---------------------------------- Prevalance ---------------------------------------------------------


tau = {
    'Brown_Marmorated_Stink_bug': 0.5,
    'Corn_Earworm': 0.5,
    'Large_Lady_Beetle': 0.5,
    'Root_Weevil': 0.1,
    'Spongy_Moth': 0.1,
    'Spooted_Lanternfly': 0.5
}


# -------------------------------- Path to save images for paper ----------------------------------------
save_images = pathlib.Path('/data/Maxent/data/paper/images')