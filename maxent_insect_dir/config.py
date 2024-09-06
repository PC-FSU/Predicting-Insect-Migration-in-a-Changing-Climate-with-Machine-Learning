import pathlib
import os


# This file contains paths pointing to different assets in the project.


# Path to save initial visualization of insect map and time series
PATH_TO_SAVE_INITIAL_DATA_VIS_INSECT = pathlib.Path("/data/Maxent/data/raw/Species Data/Guna/image/readme")

# Path to save intermediatory processed insect data. 
PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA = pathlib.Path("/home/pc19d/postdoc/MaxEnt_insect_dir/data/interim")

# Paths to data downloaded from the EDD site
EDD_DATA_PATH = "/home/pc19d/postdoc/MaxEnt_insect_dir/data/raw/Species Data/Guna/EDD Maps Site"

# Paths to data downloaded from the GBIF site
GBIF_DATA_PATH = "/home/pc19d/postdoc/MaxEnt_insect_dir/data/raw/Species Data/Guna/GBIF Site"


# Paths to interim dataset for insect
PATH_INTERIM_INSECT = "/home/pc19d/postdoc/MaxEnt_insect_dir/data/interim/insect"


Insect_list = {
    'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(EDD_DATA_PATH, "Brown_Marmorated_Stink_Bug - (Halyomorpha_halys) (1999_2023).gpkg")),
    'Corn_Earworm': pathlib.Path(os.path.join(EDD_DATA_PATH, "Corn_Earworm - (Helicoverpa_Zea) (2004-2023).gpkg")),
    'Large_Lady_Beetle': pathlib.Path(os.path.join(EDD_DATA_PATH, "Large_Lady_Beetle - (Harmonia_Axyridis) (1995-2023).gpkg")),
    'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(GBIF_DATA_PATH, "Brown_Marmorated_Stink_Bug -  (Halyomorpha_halys) (2007-2023).gpkg")),
    'Root_Weevil': pathlib.Path(os.path.join(GBIF_DATA_PATH, "Root_Weevil - (Diaprepes_abbreviatus) (2012-2023).gpkg"))
}


# Dictionaries to store data paths
Data_EDD = {
    "Brown_Marmorated_Stink_bug": Insect_list['Brown_Marmorated_Stink_bug'],
    "Corn_Earworm": Insect_list['Corn_Earworm'],
    "Large_Lady_Beetle": Insect_list['Large_Lady_Beetle']
}


Data_GBIF = {
    "Brown_Marmorated_Stink_bug_2": Insect_list['Brown_Marmorated_Stink_bug_2'],
    "Root_Weevil": Insect_list['Root_Weevil']
}


# Path to climate data
Bioclim_1970_2000 = "/home/pc19d/postdoc/MaxEnt_insect_dir/data/raw/worldclim_monthly/wc2.1_10m_tmin"


# Configuration dictionary to store all paths
config_ = {
    'insect': {
        'EDD': Data_EDD,
        'GBIF': Data_GBIF
    },
    'climate_data': pathlib.Path(Bioclim_1970_2000),
    'crop_data': pathlib.Path("/home/pc19d/postdoc/MaxEnt_insect_dir/data/raw/crop_data/2023_30m_cdls/2023_30m_cdls.tif")
}


# config dictionary for interim data

config_interim = {
    'insect' : {
        'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(PATH_INTERIM_INSECT, "Brown_Marmorated_Stink_bug_EDD_intermediatory.gpkg")),
        'Corn_Earworm': pathlib.Path(os.path.join(PATH_INTERIM_INSECT, "Corn_Earworm_EDD_intermediatory.gpkg")),
        'Large_Lady_Beetle': pathlib.Path(os.path.join(PATH_INTERIM_INSECT, "Large_Lady_Beetle_EDD_intermediatory.gpkg")),
        'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(PATH_INTERIM_INSECT, "Brown_Marmorated_Stink_bug_2_GBIF_intermediatory.gpkg")),
        'Root_Weevil': pathlib.Path(os.path.join(PATH_INTERIM_INSECT, "Root_Weevil_GBIF_intermediatory.gpkg"))
    }
}