import joblib
import argparse
from datetime import datetime
from sklearn.metrics import make_scorer, roc_auc_score
from sklearn.inspection import permutation_importance
from maxent_insect_dir import config
from maxent_insect_dir.utils_common import *
from maxent_insect_dir.utils_maxent import *
from maxent_insect_dir.Continuous_boyce_index import *

import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")


def main(df_presence, df_background, metadata, threshold=0.9, plot=False, use_sample_weights=True, save=False, use_LUH2=False, use_crop=True):
    """
    Main function to run the Maxent model, compute sample weights, and evaluate model performance.
    Saves metadata, including AUC scores and continuous Boyce index, if specified.
    
    Parameters:
    - df_presence: DataFrame containing presence data
    - df_background: DataFrame containing background data
    - metadata: Dictionary to store model metadata and experiment details
    - threshold: Correlation threshold for filtering covariates
    - plot: Boolean to enable plotting of sample weights and results
    - use_sample_weights: 
    - save: Boolean to save model and metadata
    """
    
    print(f'Number of presence point :{df_presence.shape[0]}, Number of background point :{df_background.shape[0]}....\n\n')
    
    
    df_presence.plot(alpha=0.1)
    plt.savefig(os.path.join(metadata['model_savefig_path'],'presence.png'))
    df_background.plot(alpha=0.1)
    plt.savefig(os.path.join(metadata['model_savefig_path'],'background.png'))
    
    
    if use_sample_weights:
        print("Step 1: Computing sample weights for presence and background data....\n\n")
        df_presence['SampleWeight'] = ela.distance_weights(df_presence, n_neighbors=-1, center=None)
        df_background['SampleWeight'] = ela.distance_weights(df_background, n_neighbors=-1, center=None)

        # Update metadata to include sample weight columns
        metadata['base_cols']['presence'].append('SampleWeight')
        metadata['base_cols']['background'].append('SampleWeight')

    if plot:
        if use_sample_weights:
            print("Step 2a: Plotting sample weights...\n\n")
            plot_sample_weights(
                df_presence,
                df_background,
                save_path=os.path.join(metadata['model_savefig_path'],'sample_weights.png')
            )
        
        print("Step 2b: Plotting distribution of presence data variables...\n\n")
        _ = df_presence.hist(figsize=(30,30), grid=False)
        plt.show()
        plt.savefig(os.path.join(metadata['model_savefig_path'],'presence_feature_dist.png'))
        
        print("Step 2c: Plotting distribution of backgrounnd data variables...\n\n")
        _ = df_background.hist(figsize=(30,30), grid=False)
        plt.show()
        plt.savefig(os.path.join(metadata['model_savefig_path'],'background_feature_dist.png'))

    # Merge datasets
    merged = ela.stack_geodataframes(df_presence, df_background)

    # Separating LUH2 and Bioclim columns to perform dimensionality reduction
    if use_LUH2:
        df_LUH2 = merged[list(metadata['cols']['LUH2_renamed'].values())]
    else: 
        df_LUH2 = pd.DataFrame()
        
    print("Step 3: Removing highly correlated variables....\n\n")
    if not df_LUH2.empty:
        df_LUH2_uncorr = remove_uncorrelated_columns(
            df_LUH2,
            threshold,
            save_path=metadata['model_savefig_path'],
            tag='LUH2',
            plot=plot
        )
    else:
        df_LUH2_uncorr = pd.DataFrame()


    df_Bioclim = merged[list(metadata['cols']['bioclim_renamed'].values())]
    
    df_Bioclim_uncorr = remove_uncorrelated_columns(
        df_Bioclim,
        threshold,
        save_path=metadata['model_savefig_path'],
        tag='Bioclim',
        plot=plot
    )


    print("Step 4: Combining selected variables and updating metadata....\n\n")

    columns_to_keep = ['label', 'geometry']
    if use_crop:
        columns_to_keep.append('crop_code')
    if use_sample_weights:
        columns_to_keep.append('SampleWeight')
    
    df_list = [df_LUH2_uncorr, df_Bioclim_uncorr, merged[columns_to_keep]]
    df_merged_uncorr = pd.concat(df_list, axis=1)
    df_merged_uncorr = gpd.GeoDataFrame(df_merged_uncorr, geometry='geometry')

    
    # final check for CRS
    if df_merged_uncorr.crs.to_epsg() != 5070:
        raise ValueError("df_merged_uncorr must be in CRS EPSG:5070 (USA Contiguous Albers Equal Area Conic projection). Please re-project your GeoDataFrame before proceeding.")
        

    print("Step 4a: Performing train-test split....\n\n")
    # Splitting data into train and test sets.
    if use_sample_weights:
        x_train, y_train, x_test, y_test, sample_weight_train, sample_weight_test, train_gdf, test_gdf = get_train_test_split(
            df_merged_uncorr,
            use_sample_weights,
            save_path=os.path.join(metadata['model_savefig_path'],'train_test_split.png'),
            plot=plot
        )
    else:
        x_train, y_train, x_test, y_test, train_gdf, test_gdf = get_train_test_split(
            df_merged_uncorr,
            save_path=os.path.join(metadata['model_savefig_path'],'train_test_split.png'),
            plot=plot
        )
    
    metadata['col_used_in_train'] = x_train.columns.tolist()
    metadata['train_gdf'] = train_gdf
    metadata['test_gdf'] = test_gdf
    print(f'col used in training : {metadata['col_used_in_train']}...\n\n')
    
    # For categorical columns
    cat_column_names = ['crop_code'] if use_crop else None  # List of column names you want to find indices for
    cat_indices = [x_train.columns.get_loc(col) for col in cat_column_names] if cat_column_names is not None else None   # Use get_loc to find the index of each column
    metadata['categorical_columns'] = list(zip(cat_indices, cat_column_names)) if cat_column_names is not None else None

    print("Step 5: Setting up and fitting the Maxent model....\n\n")
    maxent = ela.MaxentModel()
    metadata['model_params'] = maxent.get_params()
    if use_sample_weights:
        maxent.fit(x_train, y_train, sample_weight=sample_weight_train, categorical=cat_indices)
    else:
        maxent.fit(x_train, y_train, categorical=cat_indices)
    metadata['model'] = maxent
    
    
    # Add feature importance calculation here
    print("Step 6: Calculating feature importance...\n")
    # Define the custom scorer with pos_label=1
    scorer = make_scorer(roc_auc_score, needs_proba=True)

    # Ensure classes_ is a NumPy array
    maxent.classes_ = np.array(maxent.classes_)

    # Calculate permutation importance
    result = permutation_importance(maxent, x_test, y_test, n_repeats=10, random_state=42, scoring=scorer)

    # Store feature importance in metadata
    feature_importance = pd.Series(result.importances_mean, index=x_test.columns)
    metadata['feature_importance'] = feature_importance

    if plot:
        # Optionally, display or plot the feature importance
        print("Feature importance calculated using permutation importance:\n", feature_importance)
        # Sort and prepare the data
        feature_importance = feature_importance.sort_values(ascending=False)
        # Plot with enhancements
        plt.figure(figsize=(12, 6))  # Adjust figure size
        feature_importance.plot(kind='bar', title='Permutation Importance')
        plt.ylabel('Mean Decrease in AUC')
        plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels
        plt.tight_layout()  # Adjust layout
        plt.savefig(os.path.join(metadata['model_savefig_path'], 'feature_importance.png'))
        plt.show()
            

    print("Step 7: Predicting on test set and calculating AUC scores....\n\n")
    y_pred = maxent.predict(x_test)
    y_pred_train = maxent.predict(x_train)
    metadata['y_pred_test'] = y_pred
    metadata['y_pred_train'] = y_pred_train
    
    metadata["Unweighted_checkerboard_AUC_score_on_test"] = metrics.roc_auc_score(y_test, y_pred)
    if use_sample_weights:
        metadata["weighted_checkerboard_AUC_score_on_test"] = metrics.roc_auc_score(y_test, y_pred, sample_weight=sample_weight_test)

    print("Step 8a: Calculating continuous Boyce index for train sets....\n\n")
    CBI_train = continuous_boyce_index(
        yobs=maxent.predict(x_train[y_train == 1]),  # prediction on presence
        ypred=maxent.predict(x_train[y_train == 0]),  # prediction on background
        to_plot=plot
    )
    plt.savefig(os.path.join(metadata['model_savefig_path'],'CBI_train.png'))
    

    print("Step 8b: Calculating continuous Boyce index for test sets....\n\n")
    CBI_test = continuous_boyce_index(
        yobs=maxent.predict(x_test[y_test == 1]),  # prediction on presence
        ypred=maxent.predict(x_test[y_test == 0]),  # prediction on background
        to_plot=plot
    )
    plt.savefig(os.path.join(metadata['model_savefig_path'],'CBI_test.png'))


    metadata['CBI'] = {'train': CBI_train, 'test': CBI_test}

    if save:
        print("Step 9: Saving metadata and model state....\n\n")
        joblib.dump(metadata, os.path.join(metadata['model_metadata_path'], 'experiment_states.pkl'))

    print("Experiment completed successfully.")
    
    return metadata



def future_projection(df, metadata):
    """
    Predicts future distributions using trained model and renames columns based on metadata.
    
    Parameters:
    - df: DataFrame with future climate data
    - metadata: Dictionary containing model and training details
    
    Returns:
    - df_pred: DataFrame with geometry and prediction columns
    - df_test: DataFrame with columns used in training
    """
    column_mapping = rename_cols(df.columns)
    df.rename(columns=column_mapping, inplace=True)
    
    # Select columns for prediction based on training metadata
    columns = list(metadata['col_used_in_train']) + ['geometry']
    df_test = df[columns].copy()
    predictions = metadata['model'].predict(df_test[metadata['col_used_in_train']])

    df_pred = df[['geometry']].copy()
    df_pred['predictions'] = predictions

    return df_pred, df_test



if __name__ == '__main__':
    
    insect_name = 'Brown_Marmorated_Stink_bug'
    climate_source = 'WorldClim'
    avg = '1970_2000'
    spatial_weight = 0.50
    use_sample_weights = False
    use_LUH2 = False
    use_crop = False
    # Avg_periods = ['1970_2000']
    plot, save = True, True


    presence, background, metadata = load_data(insect_name, climate_source, avg, use_LUH2, use_crop, spatial_weight)
    
    
    # print(presence.columns)
    # print(background.columns)
    # import sys; sys.exit()

    print(f'Insect : {insect_name} | source : {climate_source} | avg : {avg} | presence.shape : {presence.shape} | background.shape: {background.shape}.')
    metadata['n_presence_thinned'] = presence.shape[0]
    metadata['min_distance'] = spatial_thinning_distance[insect_name]


    if save:
        # Add timestamp to metadata
        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
        path = os.path.join(PATH_TO_SAVE_RESULTS, f'{insect_name}_{avg}_{climate_source}_spatial_weight_{spatial_weight}_{timestamp}')
        
        # Check if the directories exist, create them if necessary
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Directory {path} created.")
        else:
            print(f"Directory {path} already exists.")
        
        metadata['model_metadata_path'] = path
        metadata['model_savefig_path'] = path
        
        

    experiment_states = main(
        presence,
        background,
        metadata,
        threshold=0.9,
        plot=plot,
        use_sample_weights=use_sample_weights,
        save=save,
        use_LUH2=use_LUH2,
        use_crop=use_crop
    )
    
    # Run future projections
    print('Running future projections over the US...\n\n\n\n\n')
    dirs = ['2021', '2040', '2060', '2080', '2100']
    future_projections = {}
    for dir in dirs:
        file = os.path.join(config.PATH_TO_SAVE_TEST_DATA, dir, f'{dir}_count_10000.gpkg')
        df = safe_read_file(file)
        df_pred, df_test = future_projection(df, metadata=experiment_states)
        
        if plot:
            fig, ax = plt.subplots(figsize=(10, 8))
            df_pred.plot(column='predictions', cmap='viridis', legend=True, ax=ax, alpha=0.1)
            ax.set_title("Prediction Map")
            plt.show()
            plt.savefig(os.path.join(metadata['model_savefig_path'],f'future_projection_{dir}.png'))

        future_projections[dir] = df_pred
    
    # Save future projections if save option is enabled
    if save:
        joblib.dump(future_projections, os.path.join(metadata['model_metadata_path'], 'future_projections.pkl'))