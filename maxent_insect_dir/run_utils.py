# packages
import os
import numpy as np
import geopandas as gpd
import rasterio as rio
import matplotlib.pyplot as plt
import elapid as ela
from sklearn import metrics
from maxent_insect_dir import config, utils, plot_functions, continuous_boyce_index


def resolve_save_path(base_path, filename):
    """
    Construct a file path for saving plots or figures.

    Args:
        base_path (str or bool): Base directory where files should be saved.
                                 If False/None, returns False.
        filename (str): Name of the file to be saved.

    Returns:
        str or bool: Full path to save file, or False if saving is disabled.
    """
    return False if isinstance(base_path, (bool, type(None))) else os.path.join(base_path, filename)


def get_presence_background(insect_name, uniform_raster, to_thin=True, bias_uniform_mix_coeff=0.75,
                            background_count=10000, plot=False, save_path=False):
    """
    Load insect presence data, optionally thin it spatially, and generate background points.

    Args:
        insect_name (str): Name of the insect species.
        uniform_raster (str): Path to raster file used for background sampling.
        to_thin (bool): Whether to apply spatial thinning to presence points.
        bias_uniform_mix_coeff (float): Weighting coefficient between biased and uniform background sampling.
        background_count (int): Number of background points to sample.
        plot (bool): Whether to plot presence/background distribution.
        save_path (str or bool): Directory where plot should be saved, or False to skip saving.

    Returns:
        tuple: (presence_thinned, background) as GeoDataFrames.
    """
    insect_source = config.insect_data[insect_name]
    thinning_distance = config.spatial_thinning_distance[insect_name] if to_thin else 0

    # Load presence data and apply thinning
    presence = gpd.read_file(insect_source)[['geometry']]
    presence_thinned = utils.spatial_thinning(presence, thinning_distance)

    # Generate background points
    background = utils.spatial_weighted_background(
        presence=presence_thinned,
        uniform_raster=uniform_raster,
        bias_uniform_mix_coeff=bias_uniform_mix_coeff,
        count=background_count
    )

    print(f'Presence original : {presence.shape} | Presence spatially thinned : {presence_thinned.shape} | '
          f'Background : {background.shape}..\n')

    # Plot and save results
    save_path_ = resolve_save_path(save_path, 'presence_background.png')
    plot_functions.plot_presence_background(presence, presence_thinned, background, plot, save_path_)

    # Ensure same schema for presence and background
    assert np.all(np.sort(presence_thinned.columns.values) == np.sort(background.columns.values)), \
        'Different columns in presence and background'

    return presence_thinned, background


def annotate(points, rasters, labels, drop_na=True):
    """
    Annotate point locations with raster values.

    Args:
        points (GeoDataFrame): Points to annotate.
        rasters (list[str]): Paths to raster layers.
        labels (list[str]): Names of raster layers to assign as columns.
        drop_na (bool): Whether to drop rows with missing raster values.

    Returns:
        GeoDataFrame: Points with raster values appended.
    """
    return ela.annotate(points, rasters, labels=labels, drop_na=drop_na)


def remove_correlated_columns(presence, background, cols_for_uncorrelated_cal,
                              threshold=0.9, plot=False, save_path=False, tag=None):
    """
    Remove highly correlated features from presence/background data.

    Args:
        presence (GeoDataFrame): Presence dataset.
        background (GeoDataFrame): Background dataset.
        cols_for_uncorrelated_cal (list[str]): Feature columns to check for correlation.
        threshold (float): Correlation threshold for removal.
        plot (bool): Whether to plot correlation matrices.
        save_path (str or bool): Directory to save plots.
        tag (str): Tag to add to filenames.

    Returns:
        Index: Remaining uncorrelated feature columns.
    """
    # Merge for correlation analysis
    merged = ela.stack_geodataframes(presence, background, add_class_label=False)
    corr_matrix = merged[cols_for_uncorrelated_cal].corr()

    # Remove correlated features
    df_uncorrelated = utils.remove_highly_correlated(merged[cols_for_uncorrelated_cal], threshold=threshold)
    corr_matrix_uncorrelated = df_uncorrelated.corr()

    # Plot correlation matrices before/after removal
    plot_functions.plot_correlation_matrix(
        corr_matrix,
        "Correlation Matrix Before Removing Highly Correlated Features",
        plot,
        resolve_save_path(save_path, f'corr_matrix_{tag}_before.png')
    )

    plot_functions.plot_correlation_matrix(
        corr_matrix_uncorrelated,
        "Correlation Matrix After Removing Highly Correlated Features",
        plot,
        resolve_save_path(save_path, f'corr_matrix_{tag}_after.png')
    )

    return df_uncorrelated.columns


def get_ks(presence, background, labels, plot=False, save_path=False):
    """
    Compare distributions of features between presence and background (similar to KS test).

    Args:
        presence (GeoDataFrame): Presence dataset.
        background (GeoDataFrame): Background dataset.
        labels (list[str]): Feature labels to compare.
        plot (bool): Whether to plot distributions.
        save_path (str or bool): Directory to save plot.

    Returns:
        dict: Results of KS-style distribution comparison.
    """
    save_path_ = resolve_save_path(save_path, 'presence_background_distribution.png')
    return plot_functions.plot_presence_background_feature_distribution(presence, background, labels, plot, save_path_)


def prepare_test_train(presence, train_background, test_background, plot=False, save_path=False):
    """
    Split presence into train/test sets and merge with background data.

    Args:
        presence (GeoDataFrame): Presence dataset.
        train_background (GeoDataFrame): Background for training.
        test_background (GeoDataFrame): Background for testing.
        plot (bool): Whether to plot train/test split.
        save_path (str or bool): Directory to save plots.

    Returns:
        dict: {x_train, y_train, x_test, y_test}
    """
    # Split presence
    train_presence, test_presence = utils.get_train_test_split(presence)

    # Stack presence + background for training
    df_train = ela.stack_geodataframes(train_presence, train_background, add_class_label=True)
    x_train = df_train.drop(columns=['class', 'geometry'])
    y_train = df_train['class']

    # Stack presence + background for testing
    df_test = ela.stack_geodataframes(test_presence, test_background, add_class_label=True)
    x_test = df_test.drop(columns=['class', 'geometry'])
    y_test = df_test['class']

    print(f'train_presence : {train_presence.shape} | test_presence : {test_presence.shape} | '
          f'train_background : {train_background.shape} | test_background : {test_background.shape}...\n\n')

    # Plot splits
    save_path_ = resolve_save_path(save_path, 'presence_train_test_split.png')
    plot_functions.plot_train_test_split(train_presence, test_presence, plot=plot, title='Presence', save_path=save_path_)

    save_path_ = resolve_save_path(save_path, 'background_train_test_split.png')
    plot_functions.plot_train_test_split(train_background, test_background, plot=plot, title='Background', save_path=save_path_)

    return {"x_train": x_train, "y_train": y_train, "x_test": x_test, "y_test": y_test}


def train_model(x_train, y_train, cat_indices=None, tau=0.5, beta_multiplier=2.0, feature_type='lph'):
    """
    Train a MaxEnt model using cloglog transform.

    Args:
        x_train (DataFrame): Training features.
        y_train (Series): Training labels (presence=1, background=0).
        cat_indices (list[int] or None): Categorical feature indices.
        tau (float): Regularization parameter.
        beta_multiplier (float): Regularization strength multiplier.
        feature_type (str): Types of features ('lph' = linear, product, hinge).

    Returns:
        MaxentModel: Trained model.
    """
    print(f'Training model with tau={tau}, beta_multiplier={beta_multiplier}, feature_type={feature_type}...\n')
    model = ela.MaxentModel(transform='cloglog', tau=tau, beta_multiplier=beta_multiplier, feature_types=feature_type)
    model.fit(x_train, y_train, categorical=cat_indices)
    return model


def evaluate(model, x_test, y_test, x_train, y_train, cat_indices, plot=False, save_path=False):
    """
    Evaluate a trained MaxEnt model with multiple metrics & plots.

    Args:
        model (MaxentModel): Trained model.
        x_test (DataFrame): Test features.
        y_test (Series): Test labels.
        x_train (DataFrame): Training features.
        y_train (Series): Training labels.
        cat_indices (list[int]): Indices of categorical features.
        plot (bool): Whether to plot results.
        save_path (str or bool): Directory to save plots.

    Returns:
        tuple: (feature_importance, auc, cbi_train, cbi_test)
    """
    # Compute feature importance
    feature_importance = utils.get_feature_importance(model, x_test, y_test)
    plot_functions.plot_feature_importance(
        feature_importance,
        plot,
        resolve_save_path(save_path, 'feature_importance.png')
    )

    # AUC
    auc = {'AUC_test': metrics.roc_auc_score(y_test, model.predict(x_test))}

    nbins = 20

    # CBI on training data
    cbi_train = Continuous_boyce_index.continuous_boyce_index(
        yobs=model.predict(x_train[y_train == 1]),
        ypred=model.predict(x_train[y_train == 0]),
        nbins=nbins,
        to_plot=False
    )
    plot_functions.plot_PE_curve(
        x=np.mean(cbi_train['HS'], axis=1),
        y=cbi_train['F.ratio'],
        plot=plot,
        save_path=resolve_save_path(save_path, 'cbi_train.png')
    )

    # CBI on test data
    cbi_test = Continuous_boyce_index.continuous_boyce_index(
        yobs=model.predict(x_test[y_test == 1]),
        ypred=model.predict(x_test[y_test == 0]),
        nbins=nbins,
        to_plot=False
    )
    plot_functions.plot_PE_curve(
        x=np.mean(cbi_test['HS'], axis=1),
        y=cbi_test['F.ratio'],
        plot=plot,
        save_path=resolve_save_path(save_path, 'cbi_test.png')
    )

    # Partial dependency plots
    plot_functions.plot_partial_dependency(
        model,
        x_train,
        cat_indices,
        plot,
        resolve_save_path(save_path, 'partial_dependency_plot.png')
    )

    return feature_importance, auc, cbi_train, cbi_test


def compute_projections(model, rasters, output_raster, tag, plot=False, save_path=False):
    """
    Generate spatial predictions by applying the trained model to raster layers.

    Args:
        model (MaxentModel): Trained model.
        rasters (list[str]): List of raster input layers.
        output_raster (str): Path to save the prediction raster.
        tag (str): Label for output file naming.
        plot (bool): Whether to plot projection.
        save_path (str or bool): Directory to save plot.

    Returns:
        None
    """
    # Apply model to rasters and write to file
    ela.apply_model_to_rasters(model, rasters, output_raster, quiet=True)

    # Read prediction raster
    with rio.open(output_raster, 'r') as src:
        pred = src.read(1, masked=True)

    # Plot projection map
    plot_functions.plot_projection(
        pred,
        tag,
        plot,
        resolve_save_path(save_path, f'projection_{tag}.png')
    )
