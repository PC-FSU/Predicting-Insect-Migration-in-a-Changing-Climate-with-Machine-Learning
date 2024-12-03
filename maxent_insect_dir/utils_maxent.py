import elapid as ela
import os
import warnings
import copy
from pprint import pprint
import numpy as np
import pandas as pd
import itertools
import geopandas as gpd
import rasterio as rio
from rasterio import plot as rioplot
from sklearn import metrics
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns
from maxent_insect_dir import config
from maxent_insect_dir.utils_common import *
from scipy.interpolate import griddata

# def get_experiment_metadata(insect, climate_source, avg_period):
#     """
#     Generates metadata for a given experiment, including insect type, climate source, and averaging period.
    
#     Args:
#         insect (str): The insect species to be modeled.
#         climate_source (str): Source of climate data, e.g., 'WorldClim' or 'CDS'.
#         avg_period (str): The averaging period for the climate data, e.g., '1970_2000' or '1990_2021'.
        
#     Returns:
#         dict: A metadata dictionary containing presence data, background data, and relevant columns for the experiment.
#     """
#     # Initialize the metadata dictionary with insect, climate source, and empty placeholders
#     metadata = {
#         'insect': insect,
#         'climate_source': climate_source,
#         'presence_data': None,
#         'background_data': None,
#         'presence_cols': {
#             'base': config.cols_presence
#         },
#         'background_cols': {
#             'base': config.cols_background
#         },
#         'cols' : {}
#     }
    
#     # Set presence and background data based on climate source
#     if climate_source == 'WorldClim':
#         metadata['presence_data'] = config_interim_WorldClim['presence'][insect]
#         metadata['background_data'] = config_interim_WorldClim['background'][insect]
#     else:
#         metadata['presence_data'] = config_interim_CDS['presence'][insect]
#         metadata['background_data'] = config_interim_CDS['background'][insect]
    
#     # Assign LUH2 columns based on the averaging period
#     if avg_period == '1970_2000':
#         # metadata['presence_original_cols'].append(config.LUH2_cols_1970_2000)
#         # metadata['presence_cols']['LUH2'] = rename_cols(config.LUH2_cols_1970_2000)
#         # metadata['background_original_cols'].append(config.LUH2_cols_1970_2000)
#         # metadata['background_cols']['LUH2'] = rename_cols(config.LUH2_cols_1970_2000)
#         metadata['cols']['LUH2'] = config.LUH2_cols_1970_2000
#     else:
#         # metadata['presence_original_cols'].append(config.LUH2_cols_1990_2021)
#         # metadata['presence_cols']['LUH2'] = rename_cols(config.LUH2_cols_1990_2021)
#         #metadata['background_cols']['LUH2'] = config.LUH2_cols_1990_2021
#         metadata['cols']['LUH2'] = config.LUH2_cols_1990_2021
    
#     # metadata['background_original_cols'] = metadata['presence_original_cols'].copy()
#     # metadata['background_cols']['LUH2'] = metadata['presence_cols']['LUH2'].copy()
    
#     # Assign bioclimatic columns based on climate source and averaging period
#     if avg_period == '1970_2000' and climate_source == 'WorldClim':
#         # metadata['presence_cols']['bioclim'] = config.WorldClim_cols_1970_2000
#         # metadata['background_cols']['bioclim'] = config.WorldClim_cols_1970_2000
#         metadata['cols']['bioclim'] = config.WorldClim_cols_1970_2000
#     elif avg_period == '1970_2000' and climate_source == 'CDS':
#         # metadata['presence_cols']['bioclim'] = config.CDS_cols_1970_2000
#         # metadata['background_cols']['bioclim'] = config.CDS_cols_1970_2000
#         metadata['cols']['bioclim'] = config.CDS_cols_1970_2000
#     elif avg_period == '1990_2021' and climate_source == 'WorldClim':
#         # metadata['presence_cols']['bioclim'] = config.WorldClim_cols_1990_2021
#         # metadata['background_cols']['bioclim'] = config.WorldClim_cols_1990_2021
#         metadata['cols']['bioclim'] = config.WorldClim_cols_1990_2021
#     elif avg_period == '1990_2021' and climate_source == 'CDS':
#         # metadata['presence_cols']['bioclim'] = config.CDS_cols_1990_2021
#         # metadata['background_cols']['bioclim'] = config.CDS_cols_1990_2021
#         metadata['cols']['bioclim'] = config.CDS_cols_1990_2021

#     return metadata





def get_experiment_metadata(insect, climate_source, avg_period):
    """
    Generates metadata for a given experiment, including insect type, climate source, and averaging period.
    
    Args:
        insect (str): The insect species to be modeled.
        climate_source (str): Source of climate data, e.g., 'WorldClim' or 'CDS'.
        avg_period (str): The averaging period for the climate data, e.g., '1970_2000' or '1990_2021'.
        
    Returns:
        dict: A metadata dictionary containing presence data, background data, and relevant columns for the experiment.
    """
    # Initialize the metadata dictionary with insect, climate source, and empty placeholders
    metadata = {
        'insect': insect,
        'climate_source': climate_source,
        'presence_data': None,
        'background_data': None,
        'base_cols': {
            'presence': config.cols_presence,
            'background': config.cols_background
        },
        'cols' : {}
    }
    
    # Set presence and background data based on climate source
    if climate_source == 'WorldClim':
        metadata['presence_data'] = config_interim_WorldClim['presence'][insect]
        metadata['background_data'] = config_interim_WorldClim['background'][insect]
    else:
        metadata['presence_data'] = config_interim_CDS['presence'][insect]
        metadata['background_data'] = config_interim_CDS['background'][insect]
    
    # Assign LUH2 columns based on the averaging period
    if avg_period == '1970_2000':
        metadata['cols']['LUH2'] = config.LUH2_cols_1970_2000
    else:
        metadata['cols']['LUH2'] = config.LUH2_cols_1990_2021
    
    
    # Assign bioclimatic columns based on climate source and averaging period
    if avg_period == '1970_2000' and climate_source == 'WorldClim':
        metadata['cols']['bioclim'] = config.WorldClim_cols_1970_2000
    elif avg_period == '1970_2000' and climate_source == 'CDS':
        metadata['cols']['bioclim'] = config.CDS_cols_1970_2000
    elif avg_period == '1990_2021' and climate_source == 'WorldClim':
        metadata['cols']['bioclim'] = config.WorldClim_cols_1990_2021
    elif avg_period == '1990_2021' and climate_source == 'CDS':
        metadata['cols']['bioclim'] = config.CDS_cols_1990_2021

    metadata['cols']['LUH2_renamed'] = rename_cols(metadata['cols']['LUH2'])
    metadata['cols']['bioclim_renamed'] = rename_cols(metadata['cols']['bioclim'])
    
    return metadata


def spatial_thinning(gdf, min_distance):
    """
    Performs spatial thinning on a GeoDataFrame.

    Parameters:
    - gdf: GeoDataFrame with point geometries
    - min_distance: Minimum distance between points in meters

    Returns:
    - A GeoDataFrame with thinned points
    """
    # Extract coordinates
    coords = np.array([(geom.x, geom.y) for geom in gdf.geometry])

    # Build KDTree for efficient spatial queries
    tree = cKDTree(coords)

    # Initialize list to hold indices of points to keep
    keep_indices = []
    # Initialize a set to hold indices of points already considered
    considered = set()

    for idx in range(len(coords)):
        if idx in considered:
            continue
        # Query points within min_distance
        indices = tree.query_ball_point(coords[idx], r=min_distance)
        # Add current index to keep_indices
        keep_indices.append(idx)
        # Mark all indices within min_distance as considered
        considered.update(indices)

    # Return the thinned GeoDataFrame
    
    gdf = gdf.iloc[keep_indices]
    
    return gdf.reset_index(drop=True)


def load_data(insect, climate_source, avg_period):
    """
    Loads presence and background data for the specified insect, climate source, and averaging period. 
    Additionally, it processes the data and ensures consistency between presence and background columns.
    
    Args:
        insect (str): The insect species to be modeled.
        climate_source (str): Source of climate data, e.g., 'WorldClim' or 'CDS'.
        avg_period (str): The averaging period for the climate data, e.g., '1970_2000' or '1990_2021'.
    
    Returns:
        tuple: Processed presence data, background data, and metadata.
    """
    
    # Get metadata for the experiment and make a deep copy to avoid altering the original structure
    metadata = copy.deepcopy(get_experiment_metadata(insect, climate_source, avg_period))

    
    # Load presence and background data
    presence = safe_read_file(metadata['presence_data'])
    background = safe_read_file(metadata['background_data'])
    
    
    # Flatten and extract relevant columns for presence and background
    presence_cols = metadata['base_cols']['presence'] + metadata['cols']['LUH2'] + metadata['cols']['bioclim']
    background_cols = metadata['base_cols']['background'] + metadata['cols']['LUH2'] + metadata['cols']['bioclim']

    # Subset presence and background data based on selected columns
    presence_ = presence[presence_cols].copy()
    background_ = background[background_cols].copy()

    # Add label column to background data and update metadata
    background_.loc[:, 'label'] = 0
    metadata['base_cols']['background'].append('label')

    # Map crop names to crop codes and update presence data, and metadata
    crop_mapping = pd.read_csv(config_raw['crop_mapping_config'])
    crop_mapping_dict = dict(zip(crop_mapping['Crop'], crop_mapping['Code']))
    presence_.loc[:, 'crop_code'] = presence_['crop'].map(crop_mapping_dict)
    presence_ = presence_.drop('crop', axis=1)
    metadata['base_cols']['presence'].append('crop_code')
    metadata['base_cols']['presence'].remove('crop')
    
    # Reorder columns for consistency
    presence_ = presence_.reindex(sorted(presence_.columns), axis=1)
    background_ = background_.reindex(sorted(background_.columns), axis=1)

    # rename the columns
    presence_.rename(columns=metadata['cols']['LUH2_renamed'], inplace=True)
    presence_.rename(columns=metadata['cols']['bioclim_renamed'], inplace=True)
    background_.rename(columns=metadata['cols']['LUH2_renamed'], inplace=True)
    background_.rename(columns=metadata['cols']['bioclim_renamed'], inplace=True)
    
    # Ensure columns match between presence and background data
    assert set(presence_.columns) == set(background_.columns), 'Columns for presence and background do not match'
    
    presence_=filter_outlier(drop_points_outside_us(presence_))
    background_=filter_outlier(drop_points_outside_us(background_))

    # Return processed data and metadata
    return presence_, background_, metadata


# Function to create a column mapping for prefix and suffix
def rename_cols(col_list):
    col_map = {}
    for col in col_list:
        if '_' in col:
            prefix, suffix = col.split('_')[0], col.split('_')[-1]
            col_map[col] = f"{prefix}_{suffix}"
        else:
            col_map[col] = col  # If no '_', keep the column name as is
    return col_map


def plot_correlation_matrix(corr_matrix, title):
    """Function to plot the correlation matrix using seaborn heatmap"""
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, square=True)
    plt.title(title)
    plt.show()


def remove_highly_correlated(df, threshold=0.9):
    """
    Remove highly correlated features from the dataframe.
    
    :param df: Input DataFrame with continuous variables
    :param threshold: Correlation threshold above which to remove variables
    :return: DataFrame with removed highly correlated features
    """
    corr_matrix = df.corr()  # Compute correlation matrix for continuous variables
    upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))

    # Find features with correlation greater than the threshold
    to_drop = [column for column in upper_triangle.columns if any(upper_triangle[column].abs() > threshold)]
    
    print(f"Columns to drop (correlation > {threshold}): {to_drop}")
    return df.drop(to_drop, axis=1)


def remove_uncorrelated_columns(df, threshold = 0.9, plot=False):
    # Remove highly correlated features
    df_filtered = remove_highly_correlated(df, threshold=threshold)
    
    # Compute and plot correlation matrix
    corr_matrix = df.corr()
    corr_matrix_uncorr = df_filtered.corr()
    if plot:
        plot_correlation_matrix(corr_matrix, "Correlation Matrix Before Removing Highly Correlated Features")
        plot_correlation_matrix(corr_matrix_uncorr, "Correlation Matrix After Removing Highly Correlated Features")    
    
    return df_filtered


def plot_sample_weights(df_presence, df_background):
    
    _, ax = plt.subplots(1,2,figsize=(15,3))
    df_presence.plot(column='SampleWeight', legend=True, cmap='YlOrBr', ax=ax[0])
    df_background.plot(column='SampleWeight', legend=True, cmap='YlOrBr', ax=ax[1])
    
    ax[0].set_title('presence sampleweight')
    ax[0].set_xlabel("Longitude")
    ax[0].set_ylabel("Latitude")

    ax[1].set_xlabel("Longitude")
    ax[1].set_ylabel("Latitude")
    ax[1].set_title('background sampleweight')
    
    plt.show()


def get_train_test_split(df, grid_size=0.05, plot=False):
    
    if not df.crs.is_geographic:
        grid_size = 50000
    
    print(f'Using the grid_size : {grid_size}..\n\n')
    
    train, test = ela.checkerboard_split(df, grid_size=grid_size)
    
    # we'll re-merge them for plotting purposes
    train['split'] = 'train'
    test['split'] = 'test'
    
    # Create GeoDataFrames for train and test
    train_gdf = gpd.GeoDataFrame(train, geometry='geometry', crs=df.crs)
    test_gdf = gpd.GeoDataFrame(test, geometry='geometry', crs=df.crs)
    
    # split train-test
    x_train = train.drop(columns=['label', 'SampleWeight', 'split', 'geometry'])
    y_train = train['label']
    sample_weight_train = train['SampleWeight']

    x_test = test.drop(columns=['label', 'SampleWeight', 'split', 'geometry'])
    y_test = test['label']
    sample_weight_test = test['SampleWeight']
    
    if plot:
        checker = ela.stack_geodataframes(train, test)
        checker.plot(column='split', markersize=0.75, legend=True)
        plt.show()
    
    return x_train, y_train, x_test, y_test, sample_weight_train, sample_weight_test, train_gdf, test_gdf


def plot_prediction_field(x, y, z):
    
    # Define grid for interpolation
    xi = np.linspace(x.min(), x.max(), 500)
    yi = np.linspace(y.min(), y.max(), 500)
    xi, yi = np.meshgrid(xi, yi)

    # Interpolate using griddata
    zi = griddata((x, y), z, (xi, yi), method='cubic')

    # Plot the interpolated field
    plt.figure(figsize=(10, 8))
    plt.contourf(xi, yi, zi, levels=15, cmap="viridis")
    plt.colorbar(label='Prediction')
    plt.title("Interpolated Prediction Field")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()