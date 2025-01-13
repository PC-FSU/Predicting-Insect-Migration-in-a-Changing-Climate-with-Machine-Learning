import pathlib
import os


# This file contains paths pointing to different assets in the project.

#---------------------------------------- Base_paths -----------------------------------------


# Path to save initial visualization of insect map and time series
PATH_TO_SAVE_DATA_VISUALIZATION_INSECT = pathlib.Path("/home/pc19d/postdoc/MaxEnt_insect_dir/reports/figures")

# Path to save processed insect data. 
PATH_TO_SAVE_PRESENCE_POINTS = pathlib.Path("/data/Maxent/data/interim/presence")

# Path to clean data -- removed non-us point, and outliers.
PATH_TO_CLEAN_DATA = pathlib.Path("/data/Maxent/data/raw/Species Data/Guna/Clean_Data")

#Path to the folder where all crop data is present.
CROP_DATA = pathlib.Path("/data/Maxent/data/raw/crop_data")

# Path where the models is saved
PATH_TO_SAVE_RESULTS = pathlib.Path("/data/Maxent/data/results")

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
    'Brown_Marmorated_Stink_bug_2': pathlib.Path(
        os.path.join(PATH_TO_CLEAN_DATA, "Brown_Marmorated_Stink_Bug_Halyomorpha_halys_2007_2023.gpkg")
        ),
    'Root_Weevil': pathlib.Path(
        os.path.join(PATH_TO_CLEAN_DATA, "Root_Weevil_Diaprepes_abbreviatus_2012_2023.gpkg")
        )
}

#---------------------------------------- To config crop -----------------------------------------


# Dictionary to store all path to the raster file for crop data
All_crop_data = {year : pathlib.Path(os.path.join(CROP_DATA,f"{year}_30m_cdls",f"{year}_30m_cdls.tif",)) for year in range(2008,2024)}

# path to csv which contain the code:crop_name entries. 
Crop_mapping_config = pathlib.Path("/data/Maxent/data/raw/crop_data/cdl_codes_names.csv")


#---------------------------------------- To config climate -----------------------------------------

config_worldclim = {
    'avgs': {
        '1970_2000': pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio/Clipped/In_tiff_format'),
        '1990_2021': pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_1990_2021/Clipped/In_tiff_format'),
        '2021_2040': pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2021_2040/Clipped/In_tiff_format'),
        '2041_2060': pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2041_2060/Clipped/In_tiff_format'),
        '2061_2080': pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2061_2080/Clipped/In_tiff_format'),
        '2081_2100': pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2081_2100/Clipped/In_tiff_format')
    }
}


config_CDS = {
    'avgs': {}
}

# ---------------------------------------- Elevation data -----------------------------------------
PATH_TO_ELEVATION_DATA = pathlib.Path('/data/Maxent/data/raw/Elevation/stanford-zz186ss2071-geotiff.tif')


#---------------------------------------- raw data config -----------------------------------------



#-------------------------------------- background points config --------------------------------



#---------------------------------------- test data config -----------------------------------------





# -------------------------------------- experiment config --------------------------------------------
# spatial thinning minium distance
spatial_thinning_distance = {
    'Brown_Marmorated_Stink_bug' : 15000,
    'Corn_Earworm' : 2000,
    'Large_Lady_Beetle' : 40000,
    'Brown_Marmorated_Stink_bug_2' : 30000,
    'Root_Weevil' : 5000
}

# 'Root_Weevil' : 500