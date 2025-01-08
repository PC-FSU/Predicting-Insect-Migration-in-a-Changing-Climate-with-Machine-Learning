# packages
import elapid as ela
import os
import numpy as np
import geopandas as gpd
import rasterio as rio
import matplotlib.pyplot as plt
import pathlib
import joblib

from datetime import datetime
from maxent_insect_dir import config
from maxent_insect_dir import utils
from maxent_insect_dir import plot_functions
from maxent_insect_dir import Continuous_boyce_index


def get_presence_background(insect_name, rasters, raster_names, to_thin=True, bias_uniform_mix_coeff=0.75, background_count=10000, plot=False, save_path=False):

    insect_source = config.Insect_list[insect_name]
    thinning_distance = config.spatial_thinning_distance[insect_name] if to_thin else 0
    
    # read the presence data. 
    presence = gpd.read_file(insect_source)[['geometry']]
    presence_thinned = utils.spatial_thinning(presence, thinning_distance)
    presence_thinned = ela.annotate(presence_thinned, rasters, labels = raster_names, drop_na=True)
    presence_thinned['SampleWeight'] = ela.distance_weights(presence_thinned, n_neighbors=-1, center=None)

    # draw background point samples
    background = utils.spatial_weighted_background(presence=presence_thinned, uniform_raster=rasters[0], bias_uniform_mix_coeff=bias_uniform_mix_coeff, count=background_count)
    background = ela.annotate(background, rasters, labels=raster_names, drop_na=True)
    background['SampleWeight'] = ela.distance_weights(background, n_neighbors=-1, center=None)
    
    print(f'Presence original : {presence.shape} | Presence spatially thinned : {presence_thinned.shape} | background : {background.shape}..\n' )
    
    
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'presence_background.png')
    plot_functions.plot_presence_background(presence, presence_thinned, background, plot, save_path_)
    
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'presence_background_distribution.png')
    ks_results = plot_functions.plot_presence_background_feature_distribution(presence_thinned, background, raster_names, plot, save_path_)
    
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'sample_weight.png')
    plot_functions.plot_sample_weights(presence_thinned, background, plot, save_path_)

    assert np.all(np.sort(presence_thinned.columns.values) == np.sort(background.columns.values)), 'Different col in presence and absence'
    
    return presence_thinned, background, ks_results


def prepare_test_train(presence, background, base_cols, cols_for_uncorrelated_cal, use_sample_weights=True, threshold=0.9, plot=False, save_path=False):
    # merge datasets
    merged = ela.stack_geodataframes(presence, background, add_class_label=True)
    corr_matrix = merged[cols_for_uncorrelated_cal].corr()
    
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'corr_matrix_before.png')
    plot_functions.plot_correlation_matrix(corr_matrix, "Correlation Matrix Before Removing Highly Correlated Features", plot, save_path_)

    # uncorrelated feature evaluation
    df_uncorrelated = utils.remove_highly_correlated(merged[cols_for_uncorrelated_cal], threshold=threshold)
    corr_matrix_uncorrelated = df_uncorrelated.corr()
    
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'corr_matrix_after.png')
    plot_functions.plot_correlation_matrix(corr_matrix_uncorrelated, "Correlation Matrix After Removing Highly Correlated Features", plot, save_path_)    
    cols_to_keep = df_uncorrelated.columns
    
    
    # get train - test split
    df = merged[base_cols + list(cols_to_keep)]
    train, test = utils.get_train_test_split(df)
    columns = ['class', 'geometry', 'SampleWeight'] # The sample-weight will always be there, but depending on the flag we will drop it later.
    x_train = train.drop(columns=columns)
    y_train = train['class']
    x_test = test.drop(columns=columns)
    y_test = test['class']

    print(f'n_train : {x_train.shape} | n_test : {x_test.shape}...\n\n')
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'train_test_split.png')
    plot_functions.plot_train_test_split(train, test, plot, save_path_)
    
    result = {
        "x_train": x_train,
        "y_train": y_train,
        "x_test": x_test,
        "y_test": y_test
    }
    
    if use_sample_weights:
        result['sample_weight_train'] = train['SampleWeight']
        result['sample_weight_test'] = test['SampleWeight']    
        
    return result


def train_model(x_train, y_train, cat_indices=None, sample_weight_train=None):  
    # train the model
    model = ela.MaxentModel(transform='cloglog', beta_multiplier=2.0)
    if sample_weight_train is not None:
        model.fit(x_train, y_train, sample_weight=sample_weight_train, categorical=cat_indices)
    else:
        model.fit(x_train, y_train, categorical=cat_indices)
    return model



def evaluate(model, x_test, y_test, x_train, y_train, cat_indices, sample_weight_test=None, plot=False, save_path=False):
    # get feature importance
    feature_importance = utils.get_feature_importance(model, x_test, y_test)
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'feature_importance.png')
    plot_functions.plot_feature_importance(feature_importance,  plot, save_path_)
    
    # get auc score
    auc = utils.get_auc_score(model, x_test, y_test, sample_weight_test)
    
    # get CBI
    cbi_train = Continuous_boyce_index.continuous_boyce_index(
        yobs=model.predict(x_train[y_train == 1]),  # prediction on presence
        ypred=model.predict(x_train[y_train == 0]),  # prediction on background
        to_plot=False
    )
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'cbi_train.png')
    plot_functions.plot_PE_curve(x=np.mean(cbi_train['HS'], axis=1), y=cbi_train['F.ratio'], plot=plot, save_path=save_path_)


    cbi_test = Continuous_boyce_index.continuous_boyce_index(
        yobs=model.predict(x_test[y_test == 1]),  # prediction on presence
        ypred=model.predict(x_test[y_test == 0]),  # prediction on background
        to_plot=False
    )
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'cbi_test.png')
    plot_functions.plot_PE_curve(x=np.mean(cbi_test['HS'], axis=1), y=cbi_test['F.ratio'], plot=plot, save_path=save_path_)
    
    # get partial dependency plot
    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, 'partial_dependency_plot.png')
    plot_functions.plot_partial_dependency(model, x_train, cat_indices, plot, save_path_)

    return feature_importance, auc, cbi_train, cbi_test


def compute_projections(model, rasters, output_raster, tag, plot=False, save_path=False):
    # write the model predictions to disk
    ela.apply_model_to_rasters(model, rasters, output_raster, quiet=True)
    
    # and read into memory
    with rio.open(output_raster, 'r') as src:
        pred = src.read(1, masked=True)

    save_path_ = save_path if isinstance(save_path, bool) else os.path.join(save_path, f'projection_{tag}.png')
    plot_functions.plot_projection(pred, tag, plot, save_path_)




if __name__ == '__main__':
    
    # Define the experiment main params
    insect_name = 'Large_Lady_Beetle'
    avg = '1970_2000'
    climate_source = 'WorldClim'
    Base_config = config.config_worldclim['avgs'] if climate_source == 'WorldClim' else config.config_CDS['avgs']
    to_thin = True
    use_sample_weights = False
    
    raster_names = [
        'Bio1', 'Bio2', 'Bio3', 'Bio4', 'Bio5', 'Bio6', 'Bio7', 'Bio8', 'Bio9', 'Bio10',
        'Bio11', 'Bio12', 'Bio13', 'Bio14', 'Bio15', 'Bio16', 'Bio17', 'Bio18', 'Bio19'
    ]

    # laod raster for current, and future projection
    bioclim_paths = Base_config[avg]
    train_data_rasters, train_raster_mapping = utils.get_raster_mapping(bioclim_paths, raster_names)

    Projection_2040 = Base_config['2021_2040']
    rasters_2040, mapping_2040 = utils.get_raster_mapping(Projection_2040, raster_names)

    Projection_2060 = Base_config['2041_2060']
    rasters_2060, mapping_2060 = utils.get_raster_mapping(Projection_2060, raster_names)

    Projection_2080 = Base_config['2061_2080']
    rasters_2080, mapping_2080 = utils.get_raster_mapping(Projection_2080, raster_names)

    Projection_2100 = Base_config['2081_2100']
    rasters_2100, mapping_2100 = utils.get_raster_mapping(Projection_2100, raster_names)

    
    bias_uniform_mix_coeff_list = [0.0, 0.25, 0.5, 0.75, 1.0]
    
    for bias_uniform_mix_coeff in bias_uniform_mix_coeff_list:
    
        # create a metadata container to save everything
        metadata = {}

        # define experiment params
        metadata = {
            'insect_name' : insect_name,
            'avg' : avg,
            'climate_source' : climate_source,
            'bioclim_paths' : bioclim_paths,
            'bias_uniform_mix_coeff': bias_uniform_mix_coeff,
            'background_count': 10000,
            'plot': False, # If this is false, nothing will be plotted.
            'use_sample_weights': use_sample_weights,
            'base_cols': ['geometry', 'class', 'SampleWeight'],
            'threshold': 0.9,
            'cols_for_uncorrelated_cal': raster_names,  # Modify this in separate group and wrap them in list, modify the code too. 
            'save_experiment_metadata': True,
            'to_thin': to_thin
        }

        if metadata['use_sample_weights'] == True:
            metadata['base_cols'].append('SampleWeight')


        if metadata['save_experiment_metadata']:
            # Add timestamp to metadata
            timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
            path = pathlib.Path(
                os.path.join(
                    config.PATH_TO_SAVE_RESULTS, 
                    f'{insect_name}_{avg}_{climate_source}_bias_uniform_max_coeff_{metadata['bias_uniform_mix_coeff']}_{timestamp}')
            ) 
            
            # Check if the directories exist, create them if necessary
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"Directory {path} created.")
            else:
                print(f"Directory {path} already exists.")
            
            metadata['model_metadata_path'] = path
            metadata['model_savefig_path'] = path # just keeping that so its easy to understand.

        
        print('Step: get presence-background data...\n\n')
        presence, background, ks_results = get_presence_background(
            insect_name = metadata['insect_name'],
            rasters=train_data_rasters,
            raster_names=raster_names,
            to_thin=metadata['to_thin'],
            bias_uniform_mix_coeff=metadata['bias_uniform_mix_coeff'],
            background_count=metadata['background_count'],
            plot=metadata['plot'],
            save_path=metadata['model_savefig_path']
        )

        metadata['presence'] = presence
        metadata['background'] = background
        metadata['ks_results'] = ks_results
        
        
        print('Step: prepare test-train data...\n\n')
        result = prepare_test_train(
            presence=presence,
            background=background,
            base_cols=metadata['base_cols'],
            cols_for_uncorrelated_cal=metadata['cols_for_uncorrelated_cal'],
            use_sample_weights=metadata['use_sample_weights'],
            threshold=metadata['threshold'],
            plot=metadata['plot'],
            save_path=metadata['model_savefig_path']
        )

        x_train, y_train, x_test, y_test = result["x_train"], result["y_train"], result["x_test"], result["y_test"]

        metadata['x_train'] = x_train
        metadata['y_train'] = y_train
        metadata['x_test'] = x_test
        metadata['y_test'] = y_test

        if metadata['use_sample_weights']:  # Check for sample weights if they exist
            sample_weight_train, sample_weight_test = result["sample_weight_train"], result["sample_weight_test"]
            metadata['sample_weight_train'] = sample_weight_train
            metadata['sample_weight_test'] = sample_weight_test
            
        
        print('Step: Run the experiment...\n\n')
        cat_indices = None
        model = train_model(
            x_train,
            y_train,
            cat_indices=cat_indices,
            sample_weight_train=metadata['sample_weight_train'] if metadata['use_sample_weights'] else None
        )

        metadata['model'] = model
        
        
        
        print('Step: evaluate the performance metrics...\n\n')
        feature_importance, auc, cbi_train, cbi_test = evaluate(
            model=metadata['model'],
            x_test=metadata['x_test'],
            y_test=metadata['y_test'],
            x_train=metadata['x_train'],
            y_train=metadata['y_train'],
            cat_indices=None,
            sample_weight_test=metadata['sample_weight_test'] if metadata['use_sample_weights'] else None,
            plot=metadata['plot'],
            save_path=metadata['model_savefig_path']
        )

        metadata['feature_importancec'] = feature_importance
        metadata['auc'] = auc
        metadata['cbi_train'] = cbi_train
        metadata['cbi_test'] = cbi_test
        
        
        print('Step: evaluate the future projection...\n\n')
        projections = {
            'current' : {
                'rasters':[train_raster_mapping[i] for i in metadata['x_train'].columns],
                'output_raster':os.path.join(metadata['model_metadata_path'], 'current.tif') 
            },
            '2040' : {
                'rasters':[mapping_2040[i] for i in metadata['x_train'].columns],
                'output_raster':os.path.join(metadata['model_metadata_path'], '2040.tif') 
            },
            '2060' : {
                'rasters':[mapping_2060[i] for i in metadata['x_train'].columns],
                'output_raster':os.path.join(metadata['model_metadata_path'], '2060.tif') 
            },
            '2080' : {
                'rasters':[mapping_2080[i] for i in metadata['x_train'].columns],
                'output_raster':os.path.join(metadata['model_metadata_path'], '2080.tif')
            },
            '2100' : {
                'rasters':[mapping_2100[i] for i in metadata['x_train'].columns],
                'output_raster':os.path.join(metadata['model_metadata_path'], '2100.tif') 
            }
        }

        for key, val in projections.items():
            compute_projections(
                model=metadata['model'],
                rasters=val['rasters'],
                output_raster=val['output_raster'],
                tag=key,
                plot=metadata['plot'],
                save_path=metadata['model_savefig_path']
            )
        
        
        print('Step: store metadata now...\n\n')
        if metadata['save_experiment_metadata']:
            joblib.dump(metadata, os.path.join(metadata['model_metadata_path'], 'experiment_states.pkl'))