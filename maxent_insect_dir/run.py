# Import necessary packages
import os
import pathlib
import argparse
import itertools
import joblib
import geopandas as gpd
import elapid as ela
from datetime import datetime
from maxent_insect_dir import config, prepare_metadata, run_utils
from maxent_insect_dir.utils import remove_highly_correlated
from sklearn import metrics


# -------------------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------------------

def create_output_directory(metadata):
    """
    Create an output directory for saving experiment results.  
    Directory structure depends on metadata and includes timestamp.

    Args:
        metadata (dict): Dictionary containing experiment metadata with keys:
            - 'pathway' (str): Climate pathway (e.g., "SSP_245").
            - 'insect_name' (str): Insect species name.
            - 'bias_uniform_mix_coeff' (float): Mixing coefficient for bias vs uniform.
            - 'feature_type' (str): Feature types string (e.g., "lqhpt").
            - 'beta_multiplier' (float): Regularization multiplier.
            - 'avg' (str): Climate baseline (e.g., "1970_2000").
            - 'climate_source' (str): Data source name.

    Returns:
        pathlib.Path: Path to the created (or existing) directory.
    """
    timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    path = pathlib.Path(
        os.path.join(
            config.PATH_TO_SAVE_RESULTS,
            metadata['pathway'],
            metadata['insect_name'],
            str(metadata['bias_uniform_mix_coeff']),
            metadata['feature_type'],
            str(metadata['beta_multiplier']),
            f"{metadata['insect_name']}_{metadata['avg']}_{metadata['climate_source']}_bias_uniform_max_coeff_{metadata['bias_uniform_mix_coeff']}_{timestamp}"
        )
    )
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory {path} created.")
    else:
        print(f"Directory {path} already exists.")
    return path


def process_presence_background(metadata, data):
    """
    Process and generate presence and background data.

    Args:
        metadata (dict): Experiment metadata containing:
            - 'insect_name' (str): Insect species.
            - 'to_thin' (bool): Whether to thin presence data.
            - 'bias_uniform_mix_coeff' (float): Bias-uniform mixing coefficient.
            - 'background_count' (int): Number of background samples.
            - 'plot' (bool): Whether to generate plots.
            - 'model_savefig_path' (str): Path to save plots.
        data (dict): Dictionary of training rasters.

    Returns:
        tuple:
            - presence (GeoDataFrame): Annotated presence points.
            - background (GeoDataFrame): Annotated background points.
    """
    print('Step: get presence-background data...\n\n')
    presence, background = run_utils.get_presence_background(
        insect_name=metadata['insect_name'],
        uniform_raster=data['train']['bioclim']['rasters'][0],
        to_thin=metadata['to_thin'],
        bias_uniform_mix_coeff=metadata['bias_uniform_mix_coeff'],
        background_count=metadata['background_count'],
        plot=metadata['plot'],
        save_path=metadata['model_savefig_path']
    )
    return presence, background


def annotate_data(metadata, presence, background, data, raster_labels):
    """
    Annotate presence and background data with raster values.

    Args:
        metadata (dict): Experiment metadata with flags for elevation/crop usage.
        presence (GeoDataFrame): Presence points.
        background (GeoDataFrame): Background points.
        data (dict): Dictionary of raster datasets for training.
        raster_labels (dict): Labels for each raster type:
            - 'bioclim' (list[str])
            - 'elevation' (list[str])
            - 'crop' (list[str])

    Returns:
        tuple:
            - presence (GeoDataFrame): Annotated presence data.
            - background (GeoDataFrame): Annotated background data.
    """
    print('Step: Annotate bioclim variable...\n\n')
    presence = run_utils.annotate(
        points=presence,
        rasters=data['train']['bioclim']['rasters'],
        labels=raster_labels['bioclim']
    )
    background = run_utils.annotate(
        points=background,
        rasters=data['train']['bioclim']['rasters'],
        labels=raster_labels['bioclim']
    )

    if metadata['use_elevation']:
        print('Step: Annotate elevation variable...\n\n')
        presence = run_utils.annotate(
            points=presence,
            rasters=data['train']['elevation']['rasters'],
            labels=raster_labels['elevation']
        )
        background = run_utils.annotate(
            points=background,
            rasters=data['train']['elevation']['rasters'],
            labels=raster_labels['elevation']
        )

    if metadata['use_crop']:
        print('Step: Annotate crop information...\n\n')
        presence = run_utils.annotate(
            points=presence,
            rasters=data['train']['crop']['rasters'],
            labels=raster_labels['crop']
        )
        background = run_utils.annotate(
            points=background,
            rasters=data['train']['crop']['rasters'],
            labels=raster_labels['crop']
        )
    return presence, background


def prepare_test_data(metadata, data, raster_labels):
    """
    Prepare and annotate test dataset.

    Args:
        metadata (dict): Experiment metadata with elevation/crop flags.
        data (dict): Training and test raster datasets.
        raster_labels (dict): Raster variable labels.

    Returns:
        GeoDataFrame: Annotated test dataset.
    """
    test = gpd.read_file(config.PATH_TO_TEST_DATA)[['geometry']]
    test = run_utils.annotate(test, data['train']['bioclim']['rasters'], labels=raster_labels['bioclim'], drop_na=True)
    if metadata['use_elevation']:
        test = run_utils.annotate(test, data['train']['elevation']['rasters'], labels=['elevation'], drop_na=True)
    if metadata['use_crop']:
        test = run_utils.annotate(test, data['train']['crop']['rasters'], labels=['crop'], drop_na=True)
    return test


def remove_correlated_features(metadata, presence, background, raster_labels):
    """
    Remove highly correlated features from presence/background datasets.

    Args:
        metadata (dict): Experiment metadata containing threshold, plot, etc.
        presence (GeoDataFrame): Annotated presence dataset.
        background (GeoDataFrame): Annotated background dataset.
        raster_labels (dict): Labels for raster features.

    Returns:
        tuple:
            - metadata (dict): Updated metadata with KS results.
            - presence (GeoDataFrame): Filtered presence dataset.
            - background (GeoDataFrame): Filtered background dataset.
            - cols_to_keep (list[str]): Final kept feature columns.
    """
    cols_to_keep = [metadata['base_cols']]
    if metadata['use_elevation']:
        cols_to_keep.append(raster_labels['elevation'])
    if metadata['use_crop']:
        cols_to_keep.append(raster_labels['crop'])

    tags = ['bioclim']
    for tag, cols_group in zip(tags, metadata['cols_group_for_uncorrelated_calculations']):
        cols_to_keep.append(run_utils.remove_correlated_columns(
            presence=presence,
            background=background,
            cols_for_uncorrelated_cal=cols_group,
            threshold=metadata['threshold'],
            plot=metadata['plot'],
            save_path=metadata['model_savefig_path'],
            tag=tag
        ))

    cols_to_keep = list(itertools.chain.from_iterable(cols_to_keep))
    presence = presence[cols_to_keep]
    background = background[cols_to_keep]

    assert list(presence.columns) == list(background.columns) == list(cols_to_keep), \
        'Check the sequence of columns in presence, background, and cols_to_keep'
    
    metadata['ks_results'] = run_utils.get_ks(
        presence=presence,
        background=background,
        labels=cols_to_keep,
        plot=metadata['plot'],
        save_path=metadata['model_savefig_path']
    )

    return metadata, presence, background, cols_to_keep


def prepare_train_test_split(metadata, presence, background, test):
    """
    Prepare train-test data split for model training and evaluation.

    Args:
        metadata (dict): Experiment metadata with plotting and path info.
        presence (GeoDataFrame): Presence dataset.
        background (GeoDataFrame): Background dataset.
        test (GeoDataFrame): Test dataset.

    Returns:
        dict: Updated metadata with train/test splits (x_train, y_train, x_test, y_test).
    """
    print('Step: prepare test-train data...\n\n')
    result = run_utils.prepare_test_train(
        presence=presence,
        train_background=background,
        test_background=test,
        plot=metadata['plot'],
        save_path=metadata['model_savefig_path']
    )
    metadata['x_train'], metadata['y_train'], metadata['x_test'], metadata['y_test'] = \
        result["x_train"], result["y_train"], result["x_test"], result["y_test"]
    return metadata


def train_and_evaluate_model(metadata, raster_labels):
    """
    Train model and evaluate its performance.

    Args:
        metadata (dict): Experiment metadata with x_train, y_train, etc.
        raster_labels (dict): Raster labels for categorical variables.

    Returns:
        dict: Updated metadata with trained model, feature importance, and metrics.
    """
    print('Step: Run the experiment...\n\n')
    cat_indices = []
    if metadata['use_elevation']:
        col_ = raster_labels['elevation'][0]
        cat_indices.append(metadata['x_train'].columns.get_loc(col_))

    if metadata['use_crop']:
        col_ = raster_labels['crop'][0]
        cat_indices.append(metadata['x_train'].columns.get_loc(col_))

    print(cat_indices)
    model = run_utils.train_model(
        metadata['x_train'],
        metadata['y_train'],
        cat_indices=cat_indices,
        tau=metadata['tau'],
        beta_multiplier=metadata['beta_multiplier'],
        feature_type=metadata['feature_type'],
    )
    metadata['model'] = model
    
    print('Step: evaluate the performance metrics...\n\n')
    feature_importance, auc, cbi_train, cbi_test = run_utils.evaluate(
        model=metadata['model'],
        x_test=metadata['x_test'],
        y_test=metadata['y_test'],
        x_train=metadata['x_train'],
        y_train=metadata['y_train'],
        cat_indices=cat_indices,
        plot=metadata['plot'],
        save_path=metadata['model_savefig_path']
    )

    metadata['feature_importance'] = feature_importance
    metadata['auc'] = auc
    metadata['cbi_train'] = cbi_train
    metadata['cbi_test'] = cbi_test
    return metadata


def generate_projections(metadata, data, raster_labels):
    """
    Generate species distribution projections for future climate scenarios.

    Args:
        metadata (dict): Experiment metadata containing model info.
        data (dict): Raster datasets for different time periods.
        raster_labels (dict): Raster variable labels.

    Returns:
        None
    """
    print('Step: evaluate the future projection...\n\n')
    time_ranges = {
        'current': 'train',
        '2040': '2021_2040',
        '2060': '2041_2060'
    }

    projections = {
        time: {
            'rasters': prepare_metadata.prepare_projection_metadata(data[time_range], metadata['x_train'].columns),
            'output_raster': os.path.join(metadata['model_metadata_path'], f'{time}.tif')
        }
        for time, time_range in time_ranges.items()
    }

    for key, val in projections.items():
        run_utils.compute_projections(
            model=metadata['model'],
            rasters=list(val['rasters'].values()),
            output_raster=val['output_raster'],
            tag=key,
            plot=metadata['plot'],
            save_path=metadata['model_savefig_path']
        )


def save_metadata(metadata):
    """
    Save experiment metadata to disk.

    Args:
        metadata (dict): Experiment metadata containing:
            - 'save_experiment_metadata' (bool)
            - 'model_metadata_path' (str)

    Returns:
        None
    """
    print('Step: store metadata now...\n\n')
    if metadata['save_experiment_metadata']:
        joblib.dump(metadata, os.path.join(metadata['model_metadata_path'], 'experiment_states.pkl'))



# Main Workflow
if __name__ == '__main__':
    
    pathways = ['SSP_245']  # this will be a list
    insect_names =  ['Corn_Earworm'] # One of this or other: ['Brown_Marmorated_Stink_bug', 'Corn_Earworm', 'Root_Weevil', 'Spongy_Moth', 'Spooted_Lanternfly']
    feature_types = ['l']  # must be in string "lqphta", like "l", "lq", "lqh", "lph", "lqhp", "lqhpt" or othe combinations
    beta_multipliers = [0.5] # for regularization multiplier [0.5, 1, 1.5, 2.0, 2.5]
    num_experiments = 1  # Number of experiments per configuration
    background_count = 100
    
    # Loop through different experiments. Or just pick one for experiment purpose.
    for pathway in pathways:
        for feature_type in feature_types:
            for beta_multiplier in beta_multipliers:
                for _ in range(num_experiments):
                    for name in insect_names:
                        # Define experiment parameters
                        metadata = {
                                'insect_name': name,
                                'feature_type': feature_type,
                                'beta_multiplier': beta_multiplier,
                                'avg': '1970_2000',
                                'projection_period' : ["2021_2040", "2041_2060"],
                                'pathway': pathway,
                                'climate_source': 'WorldClim',
                                'background_count': background_count,
                                'plot': False,
                                'base_cols': ['geometry'],
                                'threshold': 0.9,
                                'save_experiment_metadata': True,
                                'to_thin': True,
                                'use_elevation': True,
                                'use_crop': False,
                                'model_savefig_path': None,
                                'model_metadata_path': None
                            }
                        
                        
                        data, raster_labels = prepare_metadata.prepare_experiment_metadata(
                            config.config_worldclim[metadata['pathway']] if metadata['climate_source'] == 'WorldClim' else config.config_CDS['avgs'],
                            metadata['avg'],
                            data_periods=['train'] + metadata['projection_period'],
                            use_elevation=metadata['use_elevation'],
                            elevation_raster_path=config.PATH_TO_ELEVATION_DATA if metadata['use_elevation'] else None,
                            use_crop=metadata['use_crop'],
                            crop_raster_path=config.PATH_TO_MOST_GROWN_CROP if metadata['use_crop'] else None
                        )
                        
                        
                        bias_uniform_mix_coeff_list = [0.25]  # using optimized value. Can be of anything: [0, 0.25, 0.5, 0.75, 1.0]              


                        for bias_uniform_mix_coeff in bias_uniform_mix_coeff_list:
                            metadata['tau'] = config.tau[metadata['insect_name']]
                            metadata['bias_uniform_mix_coeff'] = bias_uniform_mix_coeff
                            metadata['cols_group_for_uncorrelated_calculations'] = [raster_labels['bioclim']]
                            metadata['model_metadata_path'] = create_output_directory(metadata)
                            metadata['model_savefig_path'] = metadata['model_metadata_path']

                            presence, background = process_presence_background(metadata, data)
                            presence, background = annotate_data(metadata, presence, background, data, raster_labels)
                            metadata['presence'] = presence
                            metadata['background'] = background
                            test = prepare_test_data(metadata, data, raster_labels)
                            metadata['test'] = test
                            metadata, presence, background, cols_to_keep = remove_correlated_features(metadata, presence, background, raster_labels)
                            metadata['cols_to_keep'] = cols_to_keep
                            metadata = prepare_train_test_split(metadata, presence, background, test)
                            metadata = train_and_evaluate_model(metadata, raster_labels)
                            generate_projections(metadata, data, raster_labels)
                            save_metadata(metadata)

                        
                        # import sys; sys.exit(0)  # Exit after one iteration for testing purposes