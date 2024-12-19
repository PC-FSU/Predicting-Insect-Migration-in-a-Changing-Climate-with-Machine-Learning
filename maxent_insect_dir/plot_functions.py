import matplotlib.pyplot as plt
import seaborn as sns
import elapid as ela
import math
import rasterio as rio
from scipy.stats import ks_2samp



def plot_presence_background(presence, presence_thinned, background, plot=False, save_path=False):
    fig, ax = plt.subplots(1,3, figsize=(15,5))
    presence.plot(ax=ax[0], alpha=0.1)
    ax[0].set_title('Presence')
    presence_thinned.plot(ax=ax[1], alpha=0.1)
    ax[1].set_title('Presence spatially thinned')
    background.plot(ax=ax[2], alpha=0.1)
    ax[2].set_title('Background')
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)



def plot_presence_background_feature_histogram(presence, background, raster_names, plot=False, save_path=False):
    ncols = 4
    nrows = math.ceil(len(raster_names)/ncols)
    pair_colors = ['blue', 'green']

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(4*ncols,3*nrows))
    for idx, ax in enumerate(axs.ravel()):
        if idx >= len(raster_names):
            continue
        name = raster_names[idx] 
        pvar = presence[name]
        bvar = background[name]
        ax.hist([pvar, bvar], density=True, alpha=0.7, label=['presence', 'background'], color=pair_colors)
        ax.set_title(name)
        
    handles, lbls = ax.get_legend_handles_labels()
    fig.legend(handles, lbls, loc=(0.6, 0.9))
    plt.tight_layout()
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)
    

def plot_presence_background_feature_distribution(presence, background, raster_names, plot=False, save_path=False):
    ncols = 4
    nrows = math.ceil(len(raster_names) / ncols)
    pair_colors = ['blue', 'green']
    
    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(4 * ncols, 3 * nrows))
    axs = axs.ravel()  # Flatten the 2D array of axes for easy iteration

    ks_results = {}  # To store KS test results for each raster

    for idx, ax in enumerate(axs):
        if idx >= len(raster_names):
            ax.axis('off')  # Turn off any extra subplot
            continue
        
        name = raster_names[idx]
        pvar = presence[name]
        bvar = background[name]

        # Perform the Kolmogorov-Smirnov (KS) test
        ks_stat, p_value = ks_2samp(pvar, bvar)
        ks_results[name] = {'ks_stat': ks_stat, 'p_value': p_value}

        # Plot KDE for presence and background data
        sns.kdeplot(pvar, ax=ax, label='presence', color=pair_colors[0], fill=True, alpha=0.5)
        sns.kdeplot(bvar, ax=ax, label='background', color=pair_colors[1], fill=True, alpha=0.5)

        # Set the title with KS statistic and p-value
        ax.set_title(f"{name}\nKS Stat: {ks_stat:.2f}, p-value: {p_value:.2g}")
        ax.legend()

    plt.tight_layout()
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)
    
    return ks_results


def plot_correlation_matrix(corr_matrix, title, plot=False, save_path=False):
    """Function to plot the correlation matrix using seaborn heatmap"""
    fig = plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, square=True)
    plt.title(title)
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)


def plot_sample_weights(df_presence, df_background,  plot=False, save_path=False):
    
    fig, ax = plt.subplots(1,2,figsize=(15,3))
    df_presence.plot(column='SampleWeight', legend=True, cmap='YlOrBr', ax=ax[0])
    df_background.plot(column='SampleWeight', legend=True, cmap='YlOrBr', ax=ax[1])
    
    ax[0].set_title('presence sampleweight')
    ax[0].set_xlabel("Longitude")
    ax[0].set_ylabel("Latitude")

    ax[1].set_xlabel("Longitude")
    ax[1].set_ylabel("Latitude")
    ax[1].set_title('background sampleweight')
    
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)
        
def plot_train_test_split(train, test, plot=False, save_path=False):
    train['split'] = 'train'
    test['split'] = 'test'
    
    # Stack the geodataframes
    checker = ela.stack_geodataframes(train, test)
    
    # Create a new figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size as needed
    
    # Plot the data
    checker.plot(column='split', markersize=0.75, legend=True, ax=ax)
    
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    
    plt.close(fig)  # Close the figure to prevent it from being displayed again

        
        


def plot_feature_importance(feature_importance, plot=False, save_path=False):
    # Sort and prepare the data
    feature_importance = feature_importance.sort_values(ascending=False)

    fig = plt.figure(figsize=(12, 6))  
    feature_importance.plot(kind='bar', title='Permutation Importance')
    plt.ylabel('Mean Decrease in AUC')
    plt.xticks(rotation=45, ha='right')  
    plt.tight_layout()
    
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)    
    
        


def plot_projection(projection, tag, plot=False, save_path=False):
    # Plot the suitability predictions
    fig, ax = plt.subplots(1, 1, figsize=(10, 4), dpi=100)
    img = ax.imshow(projection, vmin=0, vmax=1, cmap='viridis')
    ax.set_title(tag)
    ax.set_xticks([])
    ax.set_yticks([])
    cbar = plt.colorbar(img, ax=ax, label="relative occurrence probability", pad=0.04)
    plt.tight_layout()
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)

        


def plot_partial_dependency(model, x_train, cat_indices=None, plot=False, save_path=False):
    labels = x_train.columns
    ncols = 4
    nrows = math.ceil(len(labels)/ncols)

    fig, ax = model.partial_dependence_plot(x_train, labels=labels, categorical_features = cat_indices,  dpi=100, figsize=(4*ncols,3*nrows))
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)    
    

def plot_current_future_feature_histogram(projections, raster_names, plot=False, save_path=False):
    ncols = 2
    nrows = math.ceil(len(raster_names)/ncols)
    
    temp = list(zip(projections['current']['rasters'], projections['2040']['rasters'], projections['2060']['rasters'], projections['2080']['rasters'], projections['2100']['rasters']))

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(6*ncols,3*nrows))
    for idx, ax in enumerate(axs.ravel()):
        if idx >= len(raster_names):
            continue
        name = raster_names[idx] 
        rasters = temp[idx]
        variables = []

        for raster in rasters:
            with rio.open(raster, 'r') as src:
                data = src.read(1, masked=True).compressed()
                variables.append(data)

        ax.hist(variables, density=True, alpha=0.7, label=projections.keys())    
        ax.set_title(name)
        
    handles, lbls = ax.get_legend_handles_labels()
    fig.legend(handles, lbls, loc=(0.6, 0.9))
    plt.tight_layout()
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)
    

def plot_current_future_feature_distribution(projections, raster_names, plot=False, save_path=False):
    ncols = 2
    nrows = math.ceil(len(raster_names) / ncols)
    
    temp = list(zip(projections['current']['rasters'], 
                    projections['2040']['rasters'], 
                    projections['2060']['rasters'], 
                    projections['2080']['rasters'], 
                    projections['2100']['rasters']))

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(6 * ncols, 3 * nrows))
    axs = axs.ravel()  # Flatten the 2D array of axes for easy iteration

    # Dictionary to store KS results for each raster name
    ks_results = {}

    for idx, ax in enumerate(axs):
        if idx >= len(raster_names):
            ax.axis('off')  # Turn off any extra subplot
            continue
        
        name = raster_names[idx]
        rasters = temp[idx]

        # Load current distribution
        with rio.open(rasters[0], 'r') as src:
            current_data = src.read(1, masked=True).compressed()
        
        # Plot current distribution
        sns.kdeplot(current_data, ax=ax, label='current', fill=True, alpha=0.5)

        # List to store KS stats and p-values
        ks_stats = []

        # Compare current distribution with future distributions and plot them
        for raster, year in zip(rasters[1:], ['2040', '2060', '2080', '2100']):
            with rio.open(raster, 'r') as src:
                future_data = src.read(1, masked=True).compressed()
            
            # Perform KS test
            ks_stat, p_value = ks_2samp(current_data, future_data)
            ks_stats.append(f"{year}: KS={ks_stat:.2f}, p={p_value:.2g}")

            # Plot future distribution
            sns.kdeplot(future_data, ax=ax, label=year, fill=True, alpha=0.5)

        # Update title to include KS stats
        ax.set_title(f"{name}\n" + "\n".join(ks_stats))
        ax.legend()

        # Store KS results
        ks_results[name] = ks_stats

    plt.tight_layout()
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    
    plt.close(fig)
    
    return ks_results


def plot_PE_curve(x, y, plot=False, save_path=False):
    """
    Plots the Predicted/Expected (P/E) curve for the Boyce Index.

    Args:
        x (array-like): Habitat suitability values (e.g., interval midpoints).
        y (array-like): Predicted/Expected ratios corresponding to the habitat suitability intervals.

    Returns:
        None
    """
    fig = plt.figure()
    plt.plot(x, y, marker="o")
    plt.xlabel("Habitat suitability")
    plt.ylabel("Predicted/Expected ratio")
    plt.title("Boyce Index")
    plt.tight_layout()
    if plot:
        plt.show()
    if save_path:
        plt.savefig(save_path)
    plt.close(fig)
    