# packages
import elapid as ela
import os
import numpy as np
import geopandas as gpd
import rasterio as rio

import matplotlib.pyplot as plt
plt.style.use('/home/pc19d/postdoc/MaxEnt_insect_dir/maxent_insect_dir/my_style.mplstyle')

import pathlib
import joblib
import itertools
from datetime import datetime
from maxent_insect_dir import config
from maxent_insect_dir import utils
from maxent_insect_dir import plot_functions
from maxent_insect_dir import Continuous_boyce_index


def get_presence_background(insect_name, uniform_raster, to_thin=True, bias_uniform_mix_coeff=0.75, background_count=10000, plot=False, save_path=False):

    insect_source = config.Insect_list[insect_name]
    thinning_distance = config.spatial_thinning_distance[insect_name] if to_thin else 0
    
    # read the presence data. 
    presence = gpd.read_file(insect_source)[['geometry']]
    presence_thinned = utils.spatial_thinning(presence, thinning_distance)
    presence_thinned['SampleWeight'] = ela.distance_weights(presence_thinned, n_neighbors=-1, center=None)

    # draw background point samples
    background = utils.spatial_weighted_background(presence=presence_thinned, uniform_raster=uniform_raster, bias_uniform_mix_coeff=bias_uniform_mix_coeff, count=background_count)
    background['SampleWeight'] = ela.distance_weights(background, n_neighbors=-1, center=None)
    
    print(f'Presence original : {presence.shape} | Presence spatially thinned : {presence_thinned.shape} | background : {background.shape}..\n' )
    
    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, 'presence_background.png')
    plot_functions.plot_presence_background(presence, presence_thinned, background, plot, save_path_)

    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, 'sample_weight.png')
    plot_functions.plot_sample_weights(presence_thinned, background, plot, save_path_)

    assert np.all(np.sort(presence_thinned.columns.values) == np.sort(background.columns.values)), 'Different col in presence and absence'
    
    return presence_thinned, background


def annotate_bioclim(presence, background, rasters, raster_names):
    presence = ela.annotate(presence, rasters, labels=raster_names, drop_na=True)
    background = ela.annotate(background, rasters, labels=raster_names, drop_na=True)    
    return presence, background


def annotate_elevation(presence, background, raster, raster_name='elevation'):
    presence = ela.annotate(presence, raster, labels=raster_name, drop_na=True)
    background = ela.annotate(background, raster, labels=raster_name, drop_na=True)
    return presence, background

def annotate_crop(presence, background, raster, raster_name='crop'):
    presence = ela.annotate(presence, raster, labels=raster_name, drop_na=True)
    background = ela.annotate(background, raster, labels=raster_name, drop_na=True)
    return presence, background


def annotate(presence, background, rasters, rasters_name):
    presence = ela.annotate(presence, rasters, labels=rasters_name, drop_na=True)
    background = ela.annotate(background, rasters, labels=rasters_name, drop_na=True)
    return presence, background


def remove_correlated_columns(presence, background, cols_for_uncorrelated_cal, threshold=0.9, plot=False, save_path=False, tag=None):
    # merge datasets
    merged = ela.stack_geodataframes(presence, background, add_class_label=False)
    # compute uncorrelated column corelation matrix
    corr_matrix = merged[cols_for_uncorrelated_cal].corr()
    # uncorrelated feature evaluation
    df_uncorrelated = utils.remove_highly_correlated(merged[cols_for_uncorrelated_cal], threshold=threshold)
    corr_matrix_uncorrelated = df_uncorrelated.corr()
    
    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, f'corr_matrix_{tag}_before.png')
    plot_functions.plot_correlation_matrix(corr_matrix, "Correlation Matrix Before Removing Highly Correlated Features", plot, save_path_)
    
    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, f'corr_matrix_{tag}_after.png')
    plot_functions.plot_correlation_matrix(corr_matrix_uncorrelated, "Correlation Matrix After Removing Highly Correlated Features", plot, save_path_)    
    
    cols_to_keep = df_uncorrelated.columns
    
    return cols_to_keep

def get_ks(presence, background, labels, plot=False, save_path=False):
    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, 'presence_background_distribution.png')
    ks_results = plot_functions.plot_presence_background_feature_distribution(presence, background, labels, plot, save_path_)
    return ks_results

def prepare_test_train(presence, background, use_sample_weights=True, plot=False, save_path=False):
    # merge datasets    
    df = ela.stack_geodataframes(presence, background, add_class_label=True) # this will add column class to data
    # split datasets
    train, test = utils.get_train_test_split(df)
    columns = ['class', 'geometry', 'SampleWeight'] # The sample-weight will always be there, but depending on the flag we will drop it later.
    x_train = train.drop(columns=columns)
    y_train = train['class']
    x_test = test.drop(columns=columns)
    y_test = test['class']

    print(f'n_train : {x_train.shape} | n_test : {x_test.shape}...\n\n')
    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, 'train_test_split.png')
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


def train_model(x_train, y_train, cat_indices=None, tau=0.5, sample_weight_train=None):  
    # train the model
    model = ela.MaxentModel(transform='cloglog', tau=tau, beta_multiplier=2.0)
    if sample_weight_train is not None:
        model.fit(x_train, y_train, sample_weight=sample_weight_train, categorical=cat_indices)
    else:
        model.fit(x_train, y_train, categorical=cat_indices)
    return model



def evaluate(model, x_test, y_test, x_train, y_train, cat_indices, sample_weight_test=None, plot=False, save_path=False):
    # get feature importance
    feature_importance = utils.get_feature_importance(model, x_test, y_test)
    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, 'feature_importance.png')
    plot_functions.plot_feature_importance(feature_importance,  plot, save_path_)
    
    # get auc score
    auc = utils.get_auc_score(model, x_test, y_test, sample_weight_test)
    
    # get CBI
    cbi_train = Continuous_boyce_index.continuous_boyce_index(
        yobs=model.predict(x_train[y_train == 1]),  # prediction on presence
        ypred=model.predict(x_train[y_train == 0]),  # prediction on background
        to_plot=False
    )
    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, 'cbi_train.png')
    plot_functions.plot_PE_curve(x=np.mean(cbi_train['HS'], axis=1), y=cbi_train['F.ratio'], plot=plot, save_path=save_path_)

    cbi_test = Continuous_boyce_index.continuous_boyce_index(
        yobs=model.predict(x_test[y_test == 1]),  # prediction on presence
        ypred=model.predict(x_test[y_test == 0]),  # prediction on background
        to_plot=False
    )
    
    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, 'cbi_test.png')
    plot_functions.plot_PE_curve(x=np.mean(cbi_test['HS'], axis=1), y=cbi_test['F.ratio'], plot=plot, save_path=save_path_)
    
    # get partial dependency plot
    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, 'partial_dependency_plot.png')
    plot_functions.plot_partial_dependency(model, x_train, cat_indices, plot, save_path_)

    return feature_importance, auc, cbi_train, cbi_test


def compute_projections(model, rasters, output_raster, tag, plot=False, save_path=False):
    # write the model predictions to disk
    ela.apply_model_to_rasters(model, rasters, output_raster, quiet=True)
    
    # and read into memory
    with rio.open(output_raster, 'r') as src:
        pred = src.read(1, masked=True)

    save_path_ = save_path if isinstance(save_path, (bool, type(None))) else os.path.join(save_path, f'projection_{tag}.png')
    plot_functions.plot_projection(pred, tag, plot, save_path_)


def get_bioclim_rasters_paths(bioclim_paths):
    
    raster_names = [
        'Bio1', 'Bio2', 'Bio3', 'Bio4', 'Bio5', 'Bio6', 'Bio7', 'Bio8', 'Bio9', 'Bio10',
        'Bio11', 'Bio12', 'Bio13', 'Bio14', 'Bio15', 'Bio16', 'Bio17', 'Bio18', 'Bio19'
    ]
    rasters, raster_mapping = utils.get_raster_mapping(bioclim_paths, raster_names)
    return rasters, raster_mapping, raster_names
    

def prepare_experiment_metadata(bioclim_config, avg, use_elevation=False, elevation_raster_path=None, use_crop=False, crop_raster_path=None):
    """
    Prepare datasets for climatic and elevation data.

    Args:
        bioclim_config (dict): Configuration for bioclimatic data paths by time period.
        avg (str): Key for average bioclimatic data in the configuration.
        use_elevation (bool): Whether to include elevation data.
        elevation_raster_path (str): Path to the elevation data.
        use_crop (bool): Whether to include crop data.
        crop_raster_path (str): Path to the crop data.

    Returns:
        dict: Organized data dictionary with climatic and elevation information.
    """
    # Define periods and data types
    data_periods = ["train" ,"2021_2040", "2041_2060", "2061_2080", "2081_2100"]
    data_types = ["bioclim"] # each experiment will have the bioclimatic variables. Will add to this container if other data_types are required
    raster_labels = {} #empty container which will save the label that will be used to assign label to value in df.
    
    if use_elevation == True:
        data_types.append('elevation')
    
    if use_crop==True:
        data_types.append("crop")
        
    data = {period: {data_type: {"rasters":None, "mapping":None} for data_type in data_types} for period in data_periods} # the mapping map raster_label:raster_path. This will be useful when evaluating future projections.
    
    # Get bio-climatic data
    for period in data_periods:
        if period == "train":
            data["train"]["bioclim"]["rasters"], data["train"]["bioclim"]["mapping"], raster_labels['bioclim'] = get_bioclim_rasters_paths(bioclim_config[avg])
        else:
            data[period]["bioclim"]["rasters"], data[period]["bioclim"]["mapping"], _ = get_bioclim_rasters_paths(bioclim_config[period])

    # Add elevation data if required
    if use_elevation == True:
        raster_labels['elevation'] = ['elevation']
        elevation_mapping = {"elevation": elevation_raster_path}
        for period in data_periods:
            data[period]["elevation"] = {
                "rasters": elevation_raster_path,
                "mapping": elevation_mapping,
            }
    
    # Add crop data if required
    if use_crop == True:
        raster_labels['crop'] = ['crop']
        crop_mapping = {'crop': crop_raster_path}
        for period in data_periods:
            data[period]["crop"] = {
                "rasters": crop_raster_path,
                "mapping": crop_mapping,
            }
    
    return data, raster_labels


def prepare_projection_metadata(projection_config, columns):
    # make sure the column are in right order as seen by model while training. 
    unrolled_config = {}  # Keep this as a dictionary to uroll mappings
    for key in projection_config.keys():
        for mapping_key, mapping_value in projection_config[key]['mapping'].items():
                unrolled_config[mapping_key] = mapping_value
    # To keep the column same order as seen by training data.
    res = {}
    for col in columns:
        res[col] = unrolled_config[col]
    return res
                    

if __name__ == '__main__':
    
    # Define the experiment main params
    insect_name='Spooted_Lanternfly'
    tau=config.tau[insect_name]
    avg='1970_2000'
    climate_source='WorldClim'
    bioclim_config=config.config_worldclim['avgs'] if climate_source == 'WorldClim' else config.config_CDS['avgs']
    to_thin=True
    use_sample_weights=False
    background_count=10000
    plot=False
    threshold=0.9
    use_elevation=True
    use_crop=False
    save_experiment_metadata=True
    
    data, raster_labels = prepare_experiment_metadata(
        bioclim_config,
        avg,
        use_elevation=use_elevation,
        elevation_raster_path=config.PATH_TO_ELEVATION_DATA if use_elevation else None,
        use_crop=use_crop,
        crop_raster_path=config.PATH_TO_MOST_GROWN_CROP if use_crop else None
    )
    
    # bias_uniform_mix_coeff_list = [0.0, 0.25, 0.5, 0.75, 1.0]
    bias_uniform_mix_coeff_list = [0, 0.25, 0.5, 0.75, 1.0] #[0.25, 0.75]
    
    for bias_uniform_mix_coeff in bias_uniform_mix_coeff_list:
    
        # create a metadata container to save everything
        metadata = {}

        # define experiment params
        metadata = {
            'insect_name':insect_name,
            'avg':avg,
            'tau':tau,
            'climate_source':climate_source,
            'bioclim_paths':bioclim_config[avg],
            'bias_uniform_mix_coeff':bias_uniform_mix_coeff,
            'background_count':background_count,
            'plot':plot, # If this is false, nothing will be plotted.
            'use_sample_weights':use_sample_weights,
            'base_cols':['geometry', 'SampleWeight'],
            'threshold':threshold,
            'cols_group_for_uncorrelated_calculations':[raster_labels['bioclim']],  # Modify this in separate group and wrap them in list, modify the code too. 
            'save_experiment_metadata':save_experiment_metadata,
            'to_thin':to_thin,
            'use_elevation':use_elevation,
            'use_crop':use_crop,
            'model_savefig_path':None,
            'model_metadata_path':None
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
            
            metadata['model_metadata_path']=path
            metadata['model_savefig_path']=path # just keeping that so its easy to understand.

        
        print('Step: get presence-background data...\n\n')
        presence, background = get_presence_background(
            insect_name=metadata['insect_name'],
            uniform_raster=data['train']['bioclim']['rasters'][0],    # uniform raster provide a reference geographic location over which background points are sampled uniformly.
            to_thin=metadata['to_thin'],
            bias_uniform_mix_coeff=metadata['bias_uniform_mix_coeff'],
            background_count=metadata['background_count'],
            plot=metadata['plot'],
            save_path=metadata['model_savefig_path']
        )

        print('Step: Annotate bioclim variable...\n\n')
        presence, background = annotate(
            presence=presence,
            background=background,
            rasters=data['train']['bioclim']['rasters'],
            rasters_name=raster_labels['bioclim']
        )

        if use_elevation:
            print('Step: Annotate elevation variable...\n\n')
            presence, background = annotate(
                presence=presence,
                background=background,
                rasters=data['train']['elevation']['rasters'],
                rasters_name=raster_labels['elevation']
            )
        
        if use_crop:
            print('Step: Annotate crop information...\n\n')
            presence, background = annotate(
                presence=presence,
                background=background,
                rasters=data['train']['crop']['rasters'],
                rasters_name=raster_labels['crop']
            )

        metadata['presence'] = presence
        metadata['background'] = background
        
        
        cols_to_keep = [metadata['base_cols']] 
        if use_elevation:
            cols_to_keep.append(raster_labels['elevation'])
        if use_crop:
            cols_to_keep.append(raster_labels['crop'])
            
        tags = ['bioclim']  # Update this if more data is added. Note crop and elevation won't be used here. Something like LUH2/biolcim will be added here for correlation calculations.
        assert len(tags) == len(metadata['cols_group_for_uncorrelated_calculations']), 'you might be missing some col group'
        for tag, cols_group in zip(tags, metadata['cols_group_for_uncorrelated_calculations']):
            cols_to_keep.append(remove_correlated_columns(
                presence=presence,
                background=background,
                cols_for_uncorrelated_cal=cols_group,
                threshold=0.9,
                plot=metadata['plot'],
                save_path=metadata['model_savefig_path'],
                tag=tag 
            ))
        
        
        cols_to_keep = list(itertools.chain.from_iterable(cols_to_keep))
        presence = presence[cols_to_keep]
        background = background[cols_to_keep]

        assert list(presence.columns) == list(background.columns) == list(cols_to_keep), 'Check the sequence of columns in presence, background, and cols_to_keep'        
        # With the updated col, we will calculate the ks_results
        metadata['ks_results'] = get_ks(
            presence=presence,
            background=background,
            labels=cols_to_keep,
            plot=metadata['plot'],
            save_path=metadata['model_savefig_path'],
        )
        
        print('Step: prepare test-train data...\n\n')
        result = prepare_test_train(
            presence=presence,
            background=background,
            use_sample_weights=metadata['use_sample_weights'],
            plot=metadata['plot'],
            save_path=metadata['model_savefig_path']
        )
        
        x_train, y_train, x_test, y_test = result["x_train"], result["y_train"], result["x_test"], result["y_test"]

        metadata['x_train']=x_train
        metadata['y_train']=y_train
        metadata['x_test']=x_test
        metadata['y_test']=y_test

        if metadata['use_sample_weights']:  # Check for sample weights if they exist
            sample_weight_train, sample_weight_test = result["sample_weight_train"], result["sample_weight_test"]
            metadata['sample_weight_train'] = sample_weight_train
            metadata['sample_weight_test'] = sample_weight_test
        
        print(x_train)
        print(raster_labels)
        
        print('Step: Run the experiment...\n\n')
        cat_indices = []

        if use_elevation:
            col_ = raster_labels['elevation'][0]
            cat_indices.append(x_train.columns.get_loc(col_))

        if use_crop:
            col_ = raster_labels['crop'][0]
            cat_indices.append(x_train.columns.get_loc(col_))

        
        print(cat_indices)
        model = train_model(
            x_train,
            y_train,
            cat_indices=cat_indices,
            tau=tau,
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
            cat_indices=cat_indices,
            sample_weight_test=metadata['sample_weight_test'] if metadata['use_sample_weights'] else None,
            plot=metadata['plot'],
            save_path=metadata['model_savefig_path']
        )

        metadata['feature_importance']=feature_importance
        metadata['auc']=auc
        metadata['cbi_train']=cbi_train
        metadata['cbi_test']=cbi_test

        
        print('Step: evaluate the future projection...\n\n')        
        # Define time ranges and corresponding output raster names
        time_ranges = {
            'current': 'train',
            '2040': '2021_2040',
            '2060': '2041_2060',
            '2080': '2061_2080',
            '2100': '2081_2100',
        }

        # Generate projections dynamically
        projections = {
            time: {
                'rasters': prepare_projection_metadata(data[time_range], metadata['x_train'].columns),
                'output_raster': os.path.join(metadata['model_metadata_path'], f'{time}.tif') if isinstance(metadata['model_metadata_path'], pathlib.Path) else pathlib.Path(f'{time}.tif')
            }
            for time, time_range in time_ranges.items()
        }
        
        for key, val in projections.items():
            compute_projections(
                model=metadata['model'],
                rasters=list(val['rasters'].values()),
                output_raster=val['output_raster'],
                tag=key,
                plot=metadata['plot'],
                save_path=metadata['model_savefig_path']
            )
        
        print('Step: store metadata now...\n\n')
        if metadata['save_experiment_metadata']:
            joblib.dump(metadata, os.path.join(metadata['model_metadata_path'], 'experiment_states.pkl'))
            