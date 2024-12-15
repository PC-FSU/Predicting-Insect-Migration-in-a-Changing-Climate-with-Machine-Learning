# Common Setup
import os

from maxent_insect_dir.config import *
from maxent_insect_dir.utils_common import *
from maxent_insect_dir.utils_process_insect_data import *
from maxent_insect_dir.insect_crop_intersection import *
from maxent_insect_dir.worldclim_processing import *
from maxent_insect_dir.CDS_processing import *

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
def get_crop_bioclim_intersection_presence(gdf):
    """Performs crop and bioclimatic data intersection for insect data."""
    
    print('\n.......Getting the LUH2 avgs for 1970_2000......\n')
    data_ = LUH2_intersection(
        raster_path=config_raw['LUH2']['avgs']['1970_2000'],
        gfd=gdf,
        id_column = 'objectid',
        label_prefix='LUH2_1970_2000_AVG_'    
    )
    
    print('\n.......Getting the LUH2 avgs for 1990_2021......\n')
    data_ = LUH2_intersection(
        raster_path=config_raw['LUH2']['avgs']['1990_2021'],
        gfd=data_,
        id_column = 'objectid',
        label_prefix='LUH2_1990_2021_AVG_'    
    )
    
    
    print('\n.......Getting the Bioclim avgs for 1970_2000 (WorldClim)......\n')
    data_ = bioclim_avg_insect_intersection(
        raster_path=config_raw['climate_data_worldclim']['avgs']['1970_2000'],
        gfd=data_,
        id_column = 'objectid',
        label_prefix='WORLDCLIM_1970_2000_AVG_'
    )
        
    print('\n.......Getting the Bioclim avgs for 1990_2021 (WorldClim)......\n')
    data_ = bioclim_avg_insect_intersection(
        raster_path=config_raw['climate_data_worldclim']['avgs']['1990_2021'],
        gfd=data_,
        id_column = 'objectid',
        label_prefix='WORLDCLIM_1990_2021_AVG_'
    )
        
        
    print('\n.......Getting the monthly avg for Bioclim (WorldClim)......\n')
    data_ =  worldclim_bioclim_monthly_avg_insect_intersection(
        climate_data_path=config_raw['climate_data_worldclim']['monthly_avg'],
        insect_crop_data=data_,
        id_column='objectid'
    )
    

    # CDS: Get bioclim data for CDS dataset
    print('\n.......Getting Bioclim data (CDS)......\n')
    
    print('\n.......Getting the Bioclim avgs for 1970_2000 (CDS)......\n')
    data_ = bioclim_avg_insect_intersection(
        raster_path=config_raw['climate_data_CDS']['avgs']['1970_2000'],
        gfd=data_,
        id_column = 'objectid',
        label_prefix='CDS_1970_2000_AVG_'
    )
        
    print('\n.......Getting the Bioclim avgs for 1990_2021 (CDS)......\n')
    data_ = bioclim_avg_insect_intersection(
        raster_path=config_raw['climate_data_CDS']['avgs']['1990_2021'],
        gfd=data_,
        id_column = 'objectid',
        label_prefix='CDS_1990_2021_AVG_'
    )
    
        
    print('\n.......Getting the Bioclim in timeseries fashion (CDS)......\n')
    # Load CDS bioclimatic data
    data_dict, lats, lons = load_netcdf_files(climate_data_path=config_raw['climate_data_CDS']['yearly'])
    
    # Extract bioclimatic values at insect locations in timeseries fashion.
    data_ = extract_bioclim_values_at_points_as_timeseries(
        insect_data=data_,
        bioclim_data_dict=data_dict,
        bioclim_lats=lats,
        bioclim_lons=lons,
        id_column='objectid'
    )
    
    return data_



# Function to plot and save cleaned bioclimatic data
def plot_presence_data(cleaned_bioclim_data, save_fig_path, insect_name, date_column=None, plot_timeseries=True):
    """
    Plots various visualizations (map, time series, histograms) of the cleaned bioclimatic data 
    and saves them to the specified file paths.

    Args:
        cleaned_bioclim_data (GeoDataFrame or DataFrame): Cleaned insect presence and bioclimatic data to be plotted.
        save_fig_path (str): Path to the directory where the plots will be saved.
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
    save_path = os.path.join(save_fig_path, f'{insect_name}_map.png')  # Save path for the map plot
    plot_data(cleaned_bioclim_data, plot_infos, show_plots=True, save_path=save_path)
    

    plot_infos = {
        'plot_type': 'map',                       # Specifies that this is a map plot
        'title': 'Sample weight',  # Title of the plot
        'xlabel': 'Longitude',                    # Label for the x-axis
        'ylabel': 'Latitude',                     # Label for the y-axis
        'column': 'SampleWeight'                  # Column used for plotting
    }
    save_path = os.path.join(save_fig_path, f'{insect_name}_SampleWeight.png')  # Save path for the map plot
    plot_data(cleaned_bioclim_data, plot_infos, show_plots=True, save_path=save_path)
    
    
    # Plot 2: Time series showing insect observations over time
    if plot_timeseries:
        plot_infos = {
            'plot_type': 'timeseries',                # Specifies that this is a time series plot
            'title': 'Time Series of Observations',   # Title of the plot
            'xlabel': None,                           # X-axis label is not specified
            'ylabel': None,                           # Y-axis label is not specified
            'column': date_column                     # Column containing date information
        }
        save_path = os.path.join(save_fig_path, f'{insect_name}_timeline.png')  # Save path for the time series plot
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
    save_path = os.path.join(save_fig_path, f'{insect_name}_cropDistribution.png')  # Save path for the histogram
    plot_data(cleaned_bioclim_data, plot_infos, show_plots=True, save_path=save_path)

    # Plot 4: Histograms for all columns (especially bioclimatic data)
    plot_infos = {
        'plot_type': 'hist_all',                  # Specifies that histograms should be plotted for all columns
        'title': 'Histogram of All Columns',      # Title of the plot
        'xlabel': None,                           # X-axis label is not specified
        'ylabel': None,                           # Y-axis label is not specified
        'rotation': None                          # No rotation for x-axis labels
    }
    save_path = os.path.join(save_fig_path, f'{insect_name}_BioClimDistribution.png')  # Save path for bioclimatic histograms
    plot_data(cleaned_bioclim_data, plot_infos, show_plots=True, save_path=save_path)





