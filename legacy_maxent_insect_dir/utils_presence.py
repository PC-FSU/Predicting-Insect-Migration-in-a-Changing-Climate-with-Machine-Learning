# Common Setup
import os
import pandas as pd
import elapid

from MaxEnt_insect_dir.maxent_insect_dir.config import *
from MaxEnt_insect_dir.maxent_insect_dir.utils_common import *
from MaxEnt_insect_dir.maxent_insect_dir.utils_EDD import *
from MaxEnt_insect_dir.maxent_insect_dir.utils_GBIF import *
from MaxEnt_insect_dir.maxent_insect_dir.utils_CDS import *
from MaxEnt_insect_dir.maxent_insect_dir.utils_worldclim import *

# Function to clean insect data
def clean_insect_data(source, presence):
    """Cleans insect data based on the source (GBIF or EDD)."""
    if source == 'GBIF':
        return clean_and_prepare_data_for_GBIF(presence, date_column='day')
    else:
        return clean_and_prepare_data_for_EDD(
            presence,
            keep_columns=['objectid', 'ObsDate', 'DateEnt', 'OccStatus', 'NumCollect', 'Latitude', 'Longitude', 'geometry', 'Location'],
            date_column='ObsDate',
            status_column='OccStatus',
            count_column='NumCollect'
        )


# Function to get crop and bioclim intersection based on the climate source
def get_crop_bioclim_intersection_presence(cleaned_data, crop_mapping_dict, climate_source):
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



# Function to plot and save cleaned bioclimatic data
def plot_and_save_data(cleaned_bioclim_data, save_fig_path, save_data_path, insect_name, date_column):
    """
    Plots various visualizations (map, time series, histograms) of the cleaned bioclimatic data 
    and saves them to the specified file paths.

    Args:
        cleaned_bioclim_data (GeoDataFrame or DataFrame): Cleaned insect presence and bioclimatic data to be plotted.
        save_fig_path (str): Path to the directory where the plots will be saved.
        save_data_path (str): Path to the directory where the processed data will be saved.
        insect_name (str): The name of the insect being processed, used in the plot filenames.
        date_column (str): The column in `cleaned_bioclim_data` that contains date information (for time series plot).
    
    Returns:
        None
    """
    
    # Plot 1: Map showing the distribution of presence-only data
    plot_infos = {
        'plot_type': 'map',                       # Specifies that this is a map plot
        'title': 'Number of Bugs Observed at Locations',  # Title of the plot
        'xlabel': 'Longitude',                    # Label for the x-axis
        'ylabel': 'Latitude',                     # Label for the y-axis
        'column': 'label'                         # Column used for plotting (marker colors based on 'label')
    }
    save_path = os.path.join(save_fig_path, insect_name + '_map.png')  # Save path for the map plot
    plot_data(cleaned_bioclim_data, plot_infos, show_plots=True, save_path=save_path)

    # Plot 2: Time series showing insect observations over time
    plot_infos = {
        'plot_type': 'timeseries',                # Specifies that this is a time series plot
        'title': 'Time Series of Observations',   # Title of the plot
        'xlabel': None,                           # X-axis label is not specified
        'ylabel': None,                           # Y-axis label is not specified
        'column': date_column                     # Column containing date information
    }
    save_path = os.path.join(save_fig_path, insect_name + '_timeline.png')  # Save path for the time series plot
    plot_data(cleaned_bioclim_data, plot_infos, show_plots=True, save_path=save_path)

    # Plot 3: Histogram showing the crop distribution in the data
    plot_infos = {
        'plot_type': 'hist',                      # Specifies that this is a histogram plot
        'title': 'Histogram of Crop Distribution',  # Title of the histogram
        'xlabel': None,                           # X-axis label is not specified
        'ylabel': None,                           # Y-axis label is not specified
        'column': 'crop',                         # Column containing crop data for the histogram
        'rotation': 90                            # Rotate x-axis labels by 90 degrees for better readability
    }
    save_path = os.path.join(save_fig_path, insect_name + '_cropDistribution.png')  # Save path for the histogram
    plot_data(cleaned_bioclim_data, plot_infos, show_plots=True, save_path=save_path)

    # Plot 4: Histograms for all columns (especially bioclimatic data)
    plot_infos = {
        'plot_type': 'hist_all',                  # Specifies that histograms should be plotted for all columns
        'title': 'Histogram of All Columns',      # Title of the plot
        'xlabel': None,                           # X-axis label is not specified
        'ylabel': None,                           # Y-axis label is not specified
        'rotation': None                          # No rotation for x-axis labels
    }
    save_path = os.path.join(save_fig_path, insect_name + '_BioClimDistribution.png')  # Save path for bioclimatic histograms
    plot_data(cleaned_bioclim_data, plot_infos, show_plots=True, save_path=save_path)

    # Save the cleaned and processed data to a GeoPackage file
    cleaned_bioclim_data.to_file(
        save_data_path,  # File path to save the data
        driver='GPKG',  # Specify the file format (GeoPackage)
        layer='PointLayer'  # Layer name for saving point data
    )



