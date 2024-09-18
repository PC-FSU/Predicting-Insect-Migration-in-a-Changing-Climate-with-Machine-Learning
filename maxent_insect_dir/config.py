import pathlib
import os


# This file contains paths pointing to different assets in the project.


# Path to save initial visualization of insect map and time series
PATH_TO_SAVE_INITIAL_DATA_VIS_INSECT = pathlib.Path("/home/pc19d/postdoc/MaxEnt_insect_dir/reports/figures")

# Path to save intermediatory processed insect data. 
PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA = pathlib.Path("/data/Maxent/data/interim")

# Paths to data downloaded from the EDD site
EDD_DATA_PATH = pathlib.Path("/data/Maxent/data/raw/Species Data/Guna/EDD Maps Site")

# Paths to data downloaded from the GBIF site
GBIF_DATA_PATH = pathlib.Path("/data/Maxent/data/raw/Species Data/Guna/GBIF Site")

#Path to the folder where all crop data is present.
CROP_DATA = pathlib.Path("/data/Maxent/data/raw/crop_data")


#Path to BioClim Data
BIOCLIM_DATA = pathlib.Path("/data/Maxent/data/raw/BioCLim/data")


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
    'crop_config': Crop_config,
    'BioClim_data' : BIOCLIM_DATA
}


# config dictionary for interim data. the path is same as where the interim data were saved.

config_interim_ERA5 = {
    'insect' : {
        'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "ERA5", "Brown_Marmorated_Stink_bug_EDD_intermediatory.gpkg")),
        'Corn_Earworm': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "ERA5", "Corn_Earworm_EDD_intermediatory.gpkg")),
        'Large_Lady_Beetle': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "ERA5", "Large_Lady_Beetle_EDD_intermediatory.gpkg")),
        'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "ERA5", "Brown_Marmorated_Stink_bug_2_GBIF_intermediatory.gpkg")),
        'Root_Weevil': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "ERA5", "Root_Weevil_GBIF_intermediatory.gpkg"))
    }
}

config_interim_WorldClim = {
    'insect' : {
        'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Brown_Marmorated_Stink_bug_EDD_intermediatory.gpkg")),
        'Corn_Earworm': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Corn_Earworm_EDD_intermediatory.gpkg")),
        'Large_Lady_Beetle': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Large_Lady_Beetle_EDD_intermediatory.gpkg")),
        'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Brown_Marmorated_Stink_bug_2_GBIF_intermediatory.gpkg")),
        'Root_Weevil': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Root_Weevil_GBIF_intermediatory.gpkg"))
    }
}


config_worldclim = {
    'yearly_avg': {
        '1970_2020': pathlib.Path("/data/Maxent/data/raw/wordclim_average_1970_2000/wc2.1_10m_bio")
    },
    'monthly_avg': {
        '1990-1999': {
            'tmax': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/1990-1999/wc2.1_cruts4.06_10m_tmax_1990-1999"),
            'tmin': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/1990-1999/wc2.1_cruts4.06_10m_tmin_1990-1999"),
            'prec': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/1990-1999/wc2.1_cruts4.06_10m_prec_1990-1999")
        },
        '2000-2009': {
            'tmax': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/2000-2009/wc2.1_cruts4.06_10m_tmax_2000-2009"),
            'tmin': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/2000-2009/wc2.1_cruts4.06_10m_tmin_2000-2009"),
            'prec': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/2000-2009/wc2.1_cruts4.06_10m_prec_2000-2009")
        },
        '2010-2019': {
            'tmax': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/2010-2019/wc2.1_cruts4.06_10m_tmax_2010-2019"),
            'tmin': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/2010-2019/wc2.1_cruts4.06_10m_tmin_2010-2019"),
            'prec': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/2010-2019/wc2.1_cruts4.06_10m_prec_2010-2019")
        },
        '2020-2021': {
            'tmax': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/2020-2021/wc2.1_cruts4.06_10m_tmax_2020-2021"),
            'tmin': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/2020-2021/wc2.1_cruts4.06_10m_tmin_2020-2021"),
            'prec': pathlib.Path("/data/Maxent/data/raw/worldclim_monthly/2020-2021/wc2.1_cruts4.06_10m_prec_2020-2021")
        }
    }
}
