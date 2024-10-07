# Common Setup
from maxent_insect_dir import config
from raw_data_utilis_CDS import *
from raw_data_utilis_worldclim import *
import os
import pandas as pd
import elapid




def generate_background_pts(bias_path, count):
    """
    Generates background (pseudoabsence) points based on a bias raster file and calculates sample weights for each point.

    Args:
        bias_path (str): The file path to the bias raster, which defines areas of interest where background points should be sampled.
        count (int): The number of background points to generate.

    Returns:
        GeoDataFrame: A GeoDataFrame containing the generated background points with a calculated 'SampleWeight' column.
        Points with greater proximity to other points will have lower sample weights, while isolated points will
        have higher sample weights.

    Description:
        This function performs the following steps:
        1. **Load Bias File**: It loads a bias raster file that defines areas where background points should be sampled.
        2. **Sample Background Points**: Using the `elapid.sample_bias_file()` method, it generates the desired number of background points (`count`) based on the bias file.
        3. **Create GeoDataFrame**: The sampled points are converted into a GeoDataFrame for easy geographic manipulation and analysis.
        4. **Calculate Sample Weights**: The sample weight for each point is calculated using `elapid.distance_weights()`, which assigns higher weights to points that are farther from others and lower weights to points near clusters.
        5. **Return GeoDataFrame**: The function returns a GeoDataFrame containing the generated points with their calculated sample weights.

    """
    
    # Load the bias file and generate background points based on the given bias
    pseudoabsence_bias_pts = elapid.sample_bias_file(bias_path, count)
    pseudoabsence_bias_pts = gpd.GeoDataFrame(pseudoabsence_bias_pts, columns=['geometry'])  # Convert to GeoDataFrame
    pseudoabsence_bias_pts = pseudoabsence_bias_pts.set_geometry('geometry')  # Set 'geometry' as the geometry column
    
    # Calculate sample weights for each point. Points farther from others get higher weights, nearby points get lower weights.
    pseudoabsence_bias_pts['SampleWeight'] = elapid.distance_weights(pseudoabsence_bias_pts, n_neighbors=-1)
    
    return pseudoabsence_bias_pts





# Function to get crop and bioclim intersection based on the climate source
def get_crop_bioclim_intersection_background(cleaned_data, crop_mapping_dict, climate_source):
    """Performs crop and bioclimatic data intersection for insect data."""
    
    print('\n.......Getting the crop intersection......\n')
    # Get the crop intersection
    cleaned_crop_data = find_crops_for_insect_locations(
        point_df=cleaned_data,
        crop_raster_config=config.config_raw['crop_data'],
        id_column='objectid',
        crop_mapping_dict=crop_mapping_dict
    )
    
    if climate_source == 'WorldClim':
        print('\n.......Getting the yearly avg for Bioclim (WorldClim)......\n')
        # WorldClim: Get yearly and monthly averages
        insect_crop_data_with_yearly_avg = worldclim_bioclim_yearly_avg_insect_intersection(
            climate_data_path=config.config_raw['climate_data_worldclim']['yearly_avg']['1970_2020'],
            insect_crop_data=cleaned_crop_data
        )
        
        print('\n.......Getting the monthly avg for Bioclim (WorldClim)......\n')
        return worldclim_bioclim_monthly_avg_insect_intersection(
            climate_data_path=config.config_raw['climate_data_worldclim']['monthly_avg'],
            insect_crop_data=insect_crop_data_with_yearly_avg,
            id_column='objectid'
        )
    else:
        print('\n.......Getting Bioclim data (CDS)......\n')
        # CDS: Get bioclim data for CDS dataset
        return bioclim_insect_intersection(
            climate_data_path=config.config_raw['climate_data_CDS'],
            insect_crop_data=cleaned_crop_data,
            id_column='objectid'
        )