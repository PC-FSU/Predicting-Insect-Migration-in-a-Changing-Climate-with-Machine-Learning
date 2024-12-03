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

# Path to bias rasters
BIAS_RASTERS_PATH =  pathlib.Path("/data/Maxent/data/raw/bias_file")

# Path where backgrounds point will be saved
PATH_TO_SAVE_BACKGROUND_POINTS  = pathlib.Path("/data/Maxent/data/interim/backgrounds")

# Path where figure to visualize background point will be saved
PATH_TO_SAVE_BACKGROUND_FIGS = pathlib.Path("/home/pc19d/postdoc/MaxEnt_insect_dir/reports/figures/Background")

# Path where the test-dataset will be saved. These dataset will contain the point sample in continental US, with crop data, LUH2 and Bioclim varaible.
PATH_TO_SAVE_TEST_DATA = pathlib.Path("/data/Maxent/data/processed/Test")

# Path where the models is saved
PATH_TO_SAVE_RESULTS = pathlib.Path("/data/Maxent/data/results")


#---------------------------------------- To config insects -----------------------------------------

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

#---------------------------------------- To config crop -----------------------------------------


# Dictionary to store all path to the raster file for crop data
All_crop_data = {year : pathlib.Path(os.path.join(CROP_DATA,f"{year}_30m_cdls",f"{year}_30m_cdls.tif",)) for year in range(2008,2024)}

# path to csv which contain the code:crop_name entries. 
Crop_mapping_config = pathlib.Path("/data/Maxent/data/raw/crop_data/cdl_codes_names.csv")


#---------------------------------------- To config climate -----------------------------------------

# Path to climate data for worldclim
config_worldclim = {
    'avgs': {
        '1970_2000': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio"),
        '1990_2021': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_average_1990_2021")
    },
    'monthly_avg': {
        '1990-1999': {
            'tmax': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/1990-1999/wc2.1_cruts4.06_10m_tmax_1990-1999"),
            'tmin': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/1990-1999/wc2.1_cruts4.06_10m_tmin_1990-1999"),
            'prec': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/1990-1999/wc2.1_cruts4.06_10m_prec_1990-1999")
        },
        '2000-2009': {
            'tmax': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/2000-2009/wc2.1_cruts4.06_10m_tmax_2000-2009"),
            'tmin': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/2000-2009/wc2.1_cruts4.06_10m_tmin_2000-2009"),
            'prec': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/2000-2009/wc2.1_cruts4.06_10m_prec_2000-2009")
        },
        '2010-2019': {
            'tmax': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/2010-2019/wc2.1_cruts4.06_10m_tmax_2010-2019"),
            'tmin': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/2010-2019/wc2.1_cruts4.06_10m_tmin_2010-2019"),
            'prec': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/2010-2019/wc2.1_cruts4.06_10m_prec_2010-2019")
        },
        '2020-2021': {
            'tmax': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/2020-2021/wc2.1_cruts4.06_10m_tmax_2020-2021"),
            'tmin': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/2020-2021/wc2.1_cruts4.06_10m_tmin_2020-2021"),
            'prec': pathlib.Path("/data/Maxent/data/raw/Bioclim_worldclim_monthly/2020-2021/wc2.1_cruts4.06_10m_prec_2020-2021")
        }
    }
}


#Path to BioClim Data downloaded from CDS
config_CDS = {
    'avgs': {
        '1970_2000': pathlib.Path("/data/Maxent/data/raw/Bioclim_CDS_average_1970_2000"),
        '1990_2021': pathlib.Path("/data/Maxent/data/raw/Bioclim_CDS_average_1990_2021")
    },
    'yearly' : pathlib.Path("/data/Maxent/data/raw/Bioclim_CDS/data")
}


config_LUH2 = {
    'avgs': {
        '1970_2000': pathlib.Path("/data/Maxent/data/raw/LUH2_average_1970_2000"),
        '1990_2021': pathlib.Path("/data/Maxent/data/raw/LUH2_average_1990_2021")
    },
    'yearly' : pathlib.Path("/data/Maxent/data/raw/LUH2_yearly")
}

#---------------------------------------- raw data config -----------------------------------------


# Configuration dictionary to store all raw data paths
config_raw = {
    'insect': {
        'EDD': Data_EDD,
        'GBIF': Data_GBIF
    },
    'climate_data_CDS': config_CDS,
    'climate_data_worldclim' : config_worldclim,
    'crop_data': All_crop_data,
    'crop_mapping_config': Crop_mapping_config,
    'LUH2': config_LUH2
}



#-------------------------------------- background points config --------------------------------

config_bias_rasters = {
    'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(BIAS_RASTERS_PATH, "Brown_Marmorated_Stink_bug_EDD_bias_file.tif")),
    'Corn_Earworm': pathlib.Path(os.path.join(BIAS_RASTERS_PATH, "Corn_Earworm_detected_EDD_bias_file.tif")), # THIS BIAS FILE IS GENERATED USING ONLY PRESENCE POINT. We discarded points where point is not present.
    'Large_Lady_Beetle': pathlib.Path(os.path.join(BIAS_RASTERS_PATH, "Large_Lady_bettle_EDD_bias_file.tif")),
    'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(BIAS_RASTERS_PATH, "Brown_Marmorated_Stink_bug_2_GBIF_bias_file.tif")),
    'Root_Weevil': pathlib.Path(os.path.join(BIAS_RASTERS_PATH, "root_weevil_GBIF_bias_file.tif"))
}



#---------------------------------------- interim data config -----------------------------------------


# config dictionary for interim data. the path is same as where the interim data were saved.

config_interim_CDS = {
    'presence' : {
        'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "CDS", "Brown_Marmorated_Stink_bug_EDD_intermediatory.gpkg")),
        'Corn_Earworm': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "CDS", "Corn_Earworm_EDD_intermediatory.gpkg")),
        'Large_Lady_Beetle': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "CDS", "Large_Lady_Beetle_EDD_intermediatory.gpkg")),
        'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "CDS", "Brown_Marmorated_Stink_bug_2_GBIF_intermediatory.gpkg")),
        'Root_Weevil': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "CDS", "Root_Weevil_GBIF_intermediatory.gpkg"))
    },
    'background': {
        'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "CDS", "Brown_Marmorated_Stink_bug_EDD_intermediatory.gpkg")),
        'Corn_Earworm': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "CDS", "Corn_Earworm_EDD_intermediatory.gpkg")),
        'Large_Lady_Beetle': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "CDS", "Large_Lady_Beetle_EDD_intermediatory.gpkg")),
        'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "CDS", "Brown_Marmorated_Stink_bug_2_GBIF_intermediatory.gpkg")),
        'Root_Weevil': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "CDS", "Root_Weevil_GBIF_intermediatory.gpkg"))
    }
}

config_interim_WorldClim = {
    'presence' : {
        'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Brown_Marmorated_Stink_bug_EDD_intermediatory.gpkg")),
        'Corn_Earworm': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Corn_Earworm_EDD_intermediatory.gpkg")),
        'Large_Lady_Beetle': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Large_Lady_Beetle_EDD_intermediatory.gpkg")),
        'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Brown_Marmorated_Stink_bug_2_GBIF_intermediatory.gpkg")),
        'Root_Weevil': pathlib.Path(os.path.join(PATH_TO_SAVE_INTERMEDIATORY_INSECT_DATA, "WorldClim", "Root_Weevil_GBIF_intermediatory.gpkg"))
    },
    'background': {
        'Brown_Marmorated_Stink_bug': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "WorldClim", "Brown_Marmorated_Stink_bug_EDD_intermediatory.gpkg")),
        'Corn_Earworm': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "WorldClim", "Corn_Earworm_EDD_intermediatory.gpkg")),
        'Large_Lady_Beetle': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "WorldClim", "Large_Lady_Beetle_EDD_intermediatory.gpkg")),
        'Brown_Marmorated_Stink_bug_2': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "WorldClim", "Brown_Marmorated_Stink_bug_2_GBIF_intermediatory.gpkg")),
        'Root_Weevil': pathlib.Path(os.path.join(PATH_TO_SAVE_BACKGROUND_POINTS, "WorldClim", "Root_Weevil_GBIF_intermediatory.gpkg"))
    }
}


LUH2_cols_1990_2021 =  [
    'LUH2_1990_2021_AVG_secmb',
    'LUH2_1990_2021_AVG_primf',
    'LUH2_1990_2021_AVG_pastr',
    'LUH2_1990_2021_AVG_c3per',
    'LUH2_1990_2021_AVG_secdf',
    'LUH2_1990_2021_AVG_c4ann',
    'LUH2_1990_2021_AVG_urban',
    'LUH2_1990_2021_AVG_secdn',
    'LUH2_1990_2021_AVG_c4per',
    'LUH2_1990_2021_AVG_primn',
    'LUH2_1990_2021_AVG_range',
    'LUH2_1990_2021_AVG_secma',
    'LUH2_1990_2021_AVG_c3ann',
    'LUH2_1990_2021_AVG_c3nfx'
]

LUH2_cols_1970_2000 = [
    'LUH2_1970_2000_AVG_secmb',
    'LUH2_1970_2000_AVG_primf',
    'LUH2_1970_2000_AVG_pastr',
    'LUH2_1970_2000_AVG_c3per',
    'LUH2_1970_2000_AVG_secdf',
    'LUH2_1970_2000_AVG_c4ann',
    'LUH2_1970_2000_AVG_urban',
    'LUH2_1970_2000_AVG_secdn',
    'LUH2_1970_2000_AVG_c4per',
    'LUH2_1970_2000_AVG_primn',
    'LUH2_1970_2000_AVG_range',
    'LUH2_1970_2000_AVG_secma',
    'LUH2_1970_2000_AVG_c3ann',
    'LUH2_1970_2000_AVG_c3nfx'
]


CDS_cols_1990_2021 = [
    'CDS_1990_2021_AVG_Bio1',
    'CDS_1990_2021_AVG_Bio2',
    'CDS_1990_2021_AVG_Bio3',
    'CDS_1990_2021_AVG_Bio4',
    'CDS_1990_2021_AVG_Bio5',
    'CDS_1990_2021_AVG_Bio6',
    'CDS_1990_2021_AVG_Bio7',
    'CDS_1990_2021_AVG_Bio8',
    'CDS_1990_2021_AVG_Bio9',
    'CDS_1990_2021_AVG_Bio10',
    'CDS_1990_2021_AVG_Bio11',
    'CDS_1990_2021_AVG_Bio12',
    'CDS_1990_2021_AVG_Bio13',
    'CDS_1990_2021_AVG_Bio14',
    'CDS_1990_2021_AVG_Bio15',
    'CDS_1990_2021_AVG_Bio16',
    'CDS_1990_2021_AVG_Bio17',
    'CDS_1990_2021_AVG_Bio18',
    'CDS_1990_2021_AVG_Bio19'
]


CDS_cols_1970_2000 = [
    'CDS_1970_2000_AVG_Bio1',
    'CDS_1970_2000_AVG_Bio2',
    'CDS_1970_2000_AVG_Bio3',
    'CDS_1970_2000_AVG_Bio4',
    'CDS_1970_2000_AVG_Bio5',
    'CDS_1970_2000_AVG_Bio6',
    'CDS_1970_2000_AVG_Bio7',
    'CDS_1970_2000_AVG_Bio8',
    'CDS_1970_2000_AVG_Bio9',
    'CDS_1970_2000_AVG_Bio10',
    'CDS_1970_2000_AVG_Bio11',
    'CDS_1970_2000_AVG_Bio12',
    'CDS_1970_2000_AVG_Bio13',
    'CDS_1970_2000_AVG_Bio14',
    'CDS_1970_2000_AVG_Bio15',
    'CDS_1970_2000_AVG_Bio16',
    'CDS_1970_2000_AVG_Bio17',
    'CDS_1970_2000_AVG_Bio18',
    'CDS_1970_2000_AVG_Bio19',
]


WorldClim_cols_1970_2000 = [
    'WORLDCLIM_1970_2000_AVG_Bio1',
    'WORLDCLIM_1970_2000_AVG_Bio2',
    'WORLDCLIM_1970_2000_AVG_Bio3',
    'WORLDCLIM_1970_2000_AVG_Bio4',
    'WORLDCLIM_1970_2000_AVG_Bio5',
    'WORLDCLIM_1970_2000_AVG_Bio6', 
    'WORLDCLIM_1970_2000_AVG_Bio7',
    'WORLDCLIM_1970_2000_AVG_Bio8',
    'WORLDCLIM_1970_2000_AVG_Bio9',
    'WORLDCLIM_1970_2000_AVG_Bio10', 
    'WORLDCLIM_1970_2000_AVG_Bio11',
    'WORLDCLIM_1970_2000_AVG_Bio12', 
    'WORLDCLIM_1970_2000_AVG_Bio13',
    'WORLDCLIM_1970_2000_AVG_Bio14',
    'WORLDCLIM_1970_2000_AVG_Bio15',
    'WORLDCLIM_1970_2000_AVG_Bio16', 
    'WORLDCLIM_1970_2000_AVG_Bio17',
    'WORLDCLIM_1970_2000_AVG_Bio18', 
    'WORLDCLIM_1970_2000_AVG_Bio19'
]

WorldClim_cols_1990_2021 = [ 
    'WORLDCLIM_1990_2021_AVG_Bio1',
    'WORLDCLIM_1990_2021_AVG_Bio2',
    'WORLDCLIM_1990_2021_AVG_Bio3',
    'WORLDCLIM_1990_2021_AVG_Bio4',
    'WORLDCLIM_1990_2021_AVG_Bio4a',
    'WORLDCLIM_1990_2021_AVG_Bio5',
    'WORLDCLIM_1990_2021_AVG_Bio6',
    'WORLDCLIM_1990_2021_AVG_Bio7',
    'WORLDCLIM_1990_2021_AVG_Bio8',
    'WORLDCLIM_1990_2021_AVG_Bio9',
    'WORLDCLIM_1990_2021_AVG_Bio10',
    'WORLDCLIM_1990_2021_AVG_Bio11',
    'WORLDCLIM_1990_2021_AVG_Bio12',
    'WORLDCLIM_1990_2021_AVG_Bio13',
    'WORLDCLIM_1990_2021_AVG_Bio14',
    'WORLDCLIM_1990_2021_AVG_Bio15',
    'WORLDCLIM_1990_2021_AVG_Bio16',
    'WORLDCLIM_1990_2021_AVG_Bio17',
    'WORLDCLIM_1990_2021_AVG_Bio18',
    'WORLDCLIM_1990_2021_AVG_Bio19'
]

cols_presence = [
    'crop',
    'label',
    'geometry'
]

cols_background = [
    'crop_code',
    'geometry'
]


#---------------------------------------- test data config -----------------------------------------


config_test = {
    'CDS' : pathlib.Path(os.path.join(PATH_TO_SAVE_TEST_DATA, "CDS")),
    'WorldClim' : pathlib.Path(os.path.join(PATH_TO_SAVE_TEST_DATA, "WorldClim"))
}



# -------------------------------------- experiment config --------------------------------------------
# spatial thining minium distance
spatial_thinning_distance = {
    'Brown_Marmorated_Stink_bug' : 15000,
    'Corn_Earworm' : 2000,
    'Large_Lady_Beetle' : 40000,
    'Brown_Marmorated_Stink_bug_2' : 30000,
    'Root_Weevil' : 500
}