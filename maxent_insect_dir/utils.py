# packages
import elapid as ela
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import shutil
from maxent_insect_dir.spatial_kde import spatial_kernel_density
from sklearn import metrics
from sklearn.metrics import make_scorer, roc_auc_score
from sklearn.inspection import permutation_importance
from datetime import datetime
from scipy.spatial import cKDTree
from maxent_insect_dir.plot_functions import *


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



def spatial_weighted_background(presence, uniform_raster, bias_uniform_mix_coeff=0, count=1e3):
    # bias_uniform_mix_coeff 1 means everything from the bias, 0 mean everything is uniform
    n_point_biased =  int(count*bias_uniform_mix_coeff) 
    n_point_uniform = int(count - n_point_biased)
    
    print(f'Number of point selected | uniformly: {n_point_uniform}  | with bias: {n_point_biased}\n\n')
    
    dir_path = 'temp_' + str(hash(datetime.now().strftime('%Y_%m_%d_%H_%M')))
    
    bias_raster = os.path.join(dir_path, 'bias.tif')
    if not os.path.exists(dir_path):
        # Create the directory
        os.makedirs(dir_path)
        print(f"Directory '{dir_path}' created for bias file.")
        
    # create the bias using presence point
    spatial_kernel_density(
        points=presence,
        radius=160000,
        output_path=bias_raster,
        output_pixel_size = 16000,
        output_driver='GTiff',
        scaled=True
    )


    point_sampled_uniformly = gpd.GeoDataFrame(geometry=[], crs="EPSG:5070")   
    point_sampled_with_bias = gpd.GeoDataFrame(geometry=[], crs="EPSG:5070")
    
    if bias_uniform_mix_coeff == 0:
        point_sampled_uniformly = ela.sample_raster(uniform_raster, n_point_uniform).to_crs(epsg=5070) 
    elif bias_uniform_mix_coeff == 1:
        point_sampled_with_bias =  ela.sample_bias_file(bias_raster, n_point_biased).to_crs(epsg=5070) 
    else:
        point_sampled_uniformly = ela.sample_raster(uniform_raster, n_point_uniform).to_crs(epsg=5070) 
        point_sampled_with_bias = ela.sample_bias_file(bias_raster, n_point_biased).to_crs(epsg=5070) 
    
    shutil.rmtree(dir_path)
    print(f"Directory '{dir_path}' removed.")
    
    merged = pd.concat(
        [point_sampled_uniformly.geometry, point_sampled_with_bias.geometry], 
        ignore_index=True
    )
    
    merged = gpd.GeoSeries(merged, crs="EPSG:5070")
    
    return gpd.GeoDataFrame(geometry=merged, crs="EPSG:5070")



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



def get_train_test_split(df, grid_size=0.05):
    
    if not df.crs.is_geographic:
        grid_size = 50000
    
    print(f'Using the grid_size : {grid_size}..\n\n')
    
    train, test = ela.checkerboard_split(df, grid_size=grid_size)
    
    return train, test
    


def get_feature_importance(model, x_test, y_test):
    # Define the custom scorer with pos_label=1
    scorer = make_scorer(roc_auc_score, needs_proba=True)
    # Ensure classes_ is a NumPy array
    model.classes_ = np.array(model.classes_)
    # Calculate permutation importance
    result = permutation_importance(model, x_test, y_test, n_repeats=10, random_state=42, scoring=scorer)
    return pd.Series(result.importances_mean, index=x_test.columns)



def get_auc_score(model, x_test, y_test, sample_weight_test):
    auc = {
        'Unweighted_checkerboard_AUC_score_on_test' : 'n/a',
        'Weighted_checkerboard_AUC_score_on_test' : 'n/a'
    }
    
    y_pred = model.predict(x_test)
    auc['Unweighted_checkerboard_AUC_score_on_test'] = round(metrics.roc_auc_score(y_test, y_pred),4)


    if sample_weight_test is not None:
        auc['Weighted_checkerboard_AUC_score_on_test'] = round(metrics.roc_auc_score(y_test, y_pred, sample_weight=sample_weight_test),4)
        
    print(auc)
    
    return auc


def get_raster_mapping(Base_path, raster_names):
    rasters = [os.path.join(Base_path, f'{i}.tif') for i in raster_names]
    return rasters, dict(zip(raster_names, rasters))