# packages
import os
import numpy as np
import geopandas as gpd
import rasterio as rio
import matplotlib.pyplot as plt

plt.style.use('/home/pc19d/postdoc/MaxEnt_insect_dir/maxent_insect_dir/my_style.mplstyle')

from sklearn import metrics
import elapid as ela

from maxent_insect_dir import config, utils, plot_functions, Continuous_boyce_index


def resolve_save_path(base_path, filename):
    """Resolve file path for saving plot outputs."""
    return False if isinstance(base_path, (bool, type(None))) else os.path.join(base_path, filename)


def get_presence_background(insect_name, uniform_raster, to_thin=True, bias_uniform_mix_coeff=0.75, background_count=10000, plot=False, save_path=False):
    """
    Reads and optionally thins presence data, and samples background points based on spatial bias.
    """
    insect_source = config.Insect_list[insect_name]
    thinning_distance = config.spatial_thinning_distance[insect_name] if to_thin else 0

    presence = gpd.read_file(insect_source)[['geometry']]
    presence_thinned = utils.spatial_thinning(presence, thinning_distance)

    background = utils.spatial_weighted_background(
        presence=presence_thinned,
        uniform_raster=uniform_raster,
        bias_uniform_mix_coeff=bias_uniform_mix_coeff,
        count=background_count
    )

    print(f'Presence original : {presence.shape} | Presence spatially thinned : {presence_thinned.shape} | background : {background.shape}..\n')

    save_path_ = resolve_save_path(save_path, 'presence_background.png')
    plot_functions.plot_presence_background(presence, presence_thinned, background, plot, save_path_)

    assert np.all(np.sort(presence_thinned.columns.values) == np.sort(background.columns.values)), 'Different col in presence and absence'

    return presence_thinned, background


def annotate(points, rasters, labels, drop_na=True):
    """
    Annotates points with raster values using provided labels.
    """
    return ela.annotate(points, rasters, labels=labels, drop_na=drop_na)


def remove_correlated_columns(presence, background, cols_for_uncorrelated_cal, threshold=0.9, plot=False, save_path=False, tag=None):
    """
    Removes highly correlated features from presence/background data.
    """
    merged = ela.stack_geodataframes(presence, background, add_class_label=False)
    corr_matrix = merged[cols_for_uncorrelated_cal].corr()
    df_uncorrelated = utils.remove_highly_correlated(merged[cols_for_uncorrelated_cal], threshold=threshold)
    corr_matrix_uncorrelated = df_uncorrelated.corr()

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
    Computes and optionally plots KS-test-style distributions between presence and background.
    """
    save_path_ = resolve_save_path(save_path, 'presence_background_distribution.png')
    return plot_functions.plot_presence_background_feature_distribution(presence, background, labels, plot, save_path_)


def prepare_test_train(presence, train_background, test_background, plot=False, save_path=False):
    """
    Splits presence into train/test and stacks with background points.
    """
    train_presence, test_presence = utils.get_train_test_split(presence)

    df_train = ela.stack_geodataframes(train_presence, train_background, add_class_label=True)
    x_train = df_train.drop(columns=['class', 'geometry'])
    y_train = df_train['class']

    df_test = ela.stack_geodataframes(test_presence, test_background, add_class_label=True)
    x_test = df_test.drop(columns=['class', 'geometry'])
    y_test = df_test['class']

    print(f'train_presence : {train_presence.shape} | test_presence : {test_presence.shape} | train_background : {train_background.shape} | test_background : {test_background.shape}...\n\n')

    save_path_ = resolve_save_path(save_path, 'presence_train_test_split.png')
    plot_functions.plot_train_test_split(train_presence, test_presence, plot, save_path_)
    
    save_path_ = resolve_save_path(save_path, 'background_train_test_split.png')
    plot_functions.plot_train_test_split(train_background, test_background, plot, save_path_)
    
    return {
        "x_train": x_train,
        "y_train": y_train,
        "x_test": x_test,
        "y_test": y_test
    }


def train_model(x_train, y_train, cat_indices=None, tau=0.5):
    """
    Trains a MaxEnt model using cloglog transform and specified tau.
    """
    model = ela.MaxentModel(transform='cloglog', tau=tau, beta_multiplier=2.0)
    model.fit(x_train, y_train, categorical=cat_indices)
    return model


def evaluate(model, x_test, y_test, x_train, y_train, cat_indices, plot=False, save_path=False):
    """
    Evaluates the trained model using AUC and Continuous Boyce Index (CBI), and plots feature importance & PDP.
    """
    feature_importance = utils.get_feature_importance(model, x_test, y_test)

    plot_functions.plot_feature_importance(
        feature_importance,
        plot,
        resolve_save_path(save_path, 'feature_importance.png')
    )

    auc = {'AUC_test': metrics.roc_auc_score(y_test, model.predict(x_test))}

    # CBI on train
    cbi_train = Continuous_boyce_index.continuous_boyce_index(
        yobs=model.predict(x_train[y_train == 1]),
        ypred=model.predict(x_train[y_train == 0]),
        to_plot=False
    )
    plot_functions.plot_PE_curve(
        x=np.mean(cbi_train['HS'], axis=1),
        y=cbi_train['F.ratio'],
        plot=plot,
        save_path=resolve_save_path(save_path, 'cbi_train.png')
    )

    # CBI on test
    cbi_test = Continuous_boyce_index.continuous_boyce_index(
        yobs=model.predict(x_test[y_test == 1]),
        ypred=model.predict(x_test[y_test == 0]),
        to_plot=False
    )
    plot_functions.plot_PE_curve(
        x=np.mean(cbi_test['HS'], axis=1),
        y=cbi_test['F.ratio'],
        plot=plot,
        save_path=resolve_save_path(save_path, 'cbi_test.png')
    )

    # Partial dependency plot
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
    Applies trained model to raster stack and visualizes spatial predictions.
    """
    ela.apply_model_to_rasters(model, rasters, output_raster, quiet=True)

    with rio.open(output_raster, 'r') as src:
        pred = src.read(1, masked=True)

    plot_functions.plot_projection(
        pred,
        tag,
        plot,
        resolve_save_path(save_path, f'projection_{tag}.png')
    )
