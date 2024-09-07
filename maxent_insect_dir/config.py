import pathlib
import os


# This file contains paths pointing to different assets in the project.


# Path to save initial visualization of insect map and time series
PATH_TO_SAVE_INITIAL_DATA_VIS_INSECT = pathlib.Path("/data/Maxent/data/raw/Species Data/Guna/image/readme")

# Path to save intermediatory processed insect data. 
PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA = pathlib.Path("/data/Maxent/data/interim")

# Paths to data downloaded from the EDD site
EDD_DATA_PATH = pathlib.Path("/data/Maxent/data/raw/Species Data/Guna/EDD Maps Site")

# Paths to data downloaded from the GBIF site
GBIF_DATA_PATH = pathlib.Path("/data/Maxent/data/raw/Species Data/Guna/GBIF Site")

#Path to the folder where all crop data is present.
CROP_DATA = pathlib.Path("/data/Maxent/data/raw/crop_data")

Insect_list = {
    'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(EDD_DATA_PATH, "Brown_Marmorated_Stink_Bug - (Halyomorpha_halys) (1999_2023).gpkg")),
    'Corn_Earworm': pathlib.Path(os.path.join(EDD_DATA_PATH, "Corn_Earworm - (Helicoverpa_Zea) (2004-2023).gpkg")),
    'Large_Lady_Beetle': pathlib.Path(os.path.join(EDD_DATA_PATH, "Large_Lady_Beetle - (Harmonia_Axyridis) (1995-2023).gpkg")),
    'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(GBIF_DATA_PATH, "Brown_Marmorated_Stink_Bug -  (Halyomorpha_halys) (2007-2023).gpkg")),
    'Root_Weevil': pathlib.Path(os.path.join(GBIF_DATA_PATH, "Root_Weevil - (Diaprepes_abbreviatus) (2012-2023).gpkg"))
}


# Dictionaries to store insect data paths
Data_EDD = {
    "Brown_Marmorated_Stink_bug": Insect_list['Brown_Marmorated_Stink_bug'],
    "Corn_Earworm": Insect_list['Corn_Earworm'],
    "Large_Lady_Beetle": Insect_list['Large_Lady_Beetle']
}


Data_GBIF = {
    "Brown_Marmorated_Stink_bug_2": Insect_list['Brown_Marmorated_Stink_bug_2'],
    "Root_Weevil": Insect_list['Root_Weevil']
}


# Path to climate data, this need to be more general, but for the time being its left to point to one file.
Bioclim_1970_2000 = "/home/pc19d/postdoc/MaxEnt_insect_dir/data/raw/worldclim_monthly/wc2.1_10m_tmin"




# Dictionary to store all path to the raster file for crop data
All_crop_data = {f'{year}' : pathlib.Path(os.path.join(CROP_DATA,f"{year}_30m_cdls",f"{year}_30m_cdls.tif",)) for year in range(2008,2010)}

# path to csv whic contain the code:crop_name entries. 
Crop_config = pathlib.Path("/data/Maxent/data/raw/crop_data/cdl_codes_names.csv")

# Configuration dictionary to store all raw data paths
config_raw = {
    'insect': {
        'EDD': Data_EDD,
        'GBIF': Data_GBIF
    },
    'climate_data': pathlib.Path(Bioclim_1970_2000),
    'crop_data': All_crop_data,
    'crop_config': Crop_config
}


# config dictionary for interim data. the path is same as where the interim data were saved.

config_interim = {
    'insect' : {
        'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "Brown_Marmorated_Stink_bug_EDD_intermediatory.gpkg")),
        'Corn_Earworm': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "Corn_Earworm_EDD_intermediatory.gpkg")),
        'Large_Lady_Beetle': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "Large_Lady_Beetle_EDD_intermediatory.gpkg")),
        'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "Brown_Marmorated_Stink_bug_2_GBIF_intermediatory.gpkg")),
        'Root_Weevil': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "Root_Weevil_GBIF_intermediatory.gpkg"))
    }
}