import math

import elapid as ela
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio as rio
import seaborn as sns
from maxent_insect_dir import config
from maxent_insect_dir.config import MPLSTYLE_PATH

plt.style.use(str(MPLSTYLE_PATH))

from scipy.stats import ks_2samp
from sklearn.inspection import partial_dependence
from matplotlib.colors import ListedColormap


def plot_presence_background(presence, presence_thinned, background, plot=False, save_path=False):
    
    us_boundary = gpd.read_file(config.PATH_TO_US_BOUNDARY).to_crs(presence.crs)
    
    fig, ax = plt.subplots(1,3, figsize=(15,5))
    
    presence.plot(ax=ax[0], color='red', alpha=0.1)
    us_boundary.plot(ax=ax[0], edgecolor='black', facecolor='none', linewidth=1)
    ax[0].set_title('Presence')
    ax[0].set_xticks([])
    ax[0].set_yticks([])

    
    
    presence_thinned.plot(ax=ax[1], color='red', alpha=0.1)
    us_boundary.plot(ax=ax[1], edgecolor='black', facecolor='none', linewidth=1)
    ax[1].set_title('Presence spatially thinned')
    ax[1].set_xticks([])
    ax[1].set_yticks([])

    
    background.plot(ax=ax[2], color='red', alpha=0.1)
    us_boundary.plot(ax=ax[2], edgecolor='black', facecolor='none', linewidth=1)
    ax[2].set_title('Background')
    ax[2].set_xticks([])
    ax[2].set_yticks([])

    
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
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
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)
    

def plot_presence_background_feature_distribution(presence, background, labels, plot=False, save_path=False):
    
    # Check if 'geometry' column exists and drop it
    if 'geometry' in presence.columns:
        presence = presence.drop(columns=['geometry'])
        
    if 'geometry' in background.columns:
        background = background.drop(columns=['geometry'])
    
    # Remove 'geometry' if it exists in the list
    if 'geometry' in labels:
        labels.remove('geometry')
    
    ncols = 4
    nrows = math.ceil(len(labels) / ncols)
    pair_colors = ['blue', 'green']
    
    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(4 * ncols, 3 * nrows))
    axs = axs.ravel()  # Flatten the 2D array of axes for easy iteration

    ks_results = {}  # To store KS test results for each raster

    for idx, ax in enumerate(axs):
        if idx >= len(labels):
            ax.axis('off')  # Turn off any extra subplot
            continue
        
        name = labels[idx]
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
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)
    
    return ks_results


def plot_correlation_matrix(corr_matrix, title, plot=False, save_path=False):
    """Function to plot the correlation matrix using seaborn heatmap"""
    fig = plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, square=True)
    plt.title(title)
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)



def plot_sample_weights(df_presence, df_background,  plot=False, save_path=False):
    
    us_boundary = gpd.read_file(config.PATH_TO_US_BOUNDARY).to_crs(df_presence.crs)

    fig, ax = plt.subplots(1,2,figsize=(15,3))
    
    df_presence.plot(column='SampleWeight', legend=True, cmap='coolwarm', ax=ax[0])
    us_boundary.plot(ax=ax[0], edgecolor='black', facecolor='none', linewidth=1)
    
    df_background.plot(column='SampleWeight', legend=True, cmap='coolwarm', ax=ax[1])
    us_boundary.plot(ax=ax[1], edgecolor='black', facecolor='none', linewidth=1)
    
    ax[0].set_title('presence sampleweight')
    # ax[0].set_xlabel("Longitude")
    # ax[0].set_ylabel("Latitude")
    ax[0].set_xticks([])
    ax[0].set_yticks([])


    # ax[1].set_xlabel("Longitude")
    # ax[1].set_ylabel("Latitude")
    ax[1].set_title('background sampleweight')
    ax[1].set_xticks([])
    ax[1].set_yticks([])
    
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)
    
    


def plot_train_test_split(train, test, plot=False, title='Dataset', save_path=None):
    train = train.copy()
    test = test.copy()
    train['split'] = 'train'
    test['split']  = 'test'

    us_boundary = gpd.read_file(config.PATH_TO_US_BOUNDARY).to_crs(train.crs)
    checker = ela.stack_geodataframes(train, test)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Define color mapping
    split_colors = {'train': 'red', 'test': 'green'}
    categories = ['train', 'test']
    color_list = [split_colors[cat] for cat in categories]
    cmap = ListedColormap(color_list)

    # Plot the data with the custom colormap
    checker.plot(
        column='split',
        categorical=True,
        cmap=cmap,
        markersize=1,
        legend=True,
        legend_kwds={
            'loc': 'lower left',
            'title': 'Dataset',
        },
        ax=ax
    )
    us_boundary.plot(ax=ax, edgecolor='black', facecolor='none', linewidth=1)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')

    # Customize the legend
    legend = ax.get_legend()
    if legend:
        legend.set_frame_on(False)  # Remove legend box
        legend.set_title(title, prop={'size': 20})  # Set title font size
        for text in legend.get_texts():
            text.set_fontsize(20)  # Set label font size

    if save_path:
        fig.savefig(save_path, bbox_inches='tight')
    if plot:
        plt.show()
    plt.close(fig)



def plot_feature_importance(feature_importance, plot=False, save_path=False):
    # Sort and prepare the data
    feature_importance = feature_importance.sort_values(ascending=False)

    fig = plt.figure(figsize=(12, 6))  
    feature_importance.plot(kind='bar', title='Permutation Importance')
    plt.ylabel('Mean Decrease in AUC')
    plt.xticks(rotation=45, ha='right')  
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)    
    
        


def plot_projection(projection, tag, plot=False, save_path=False):
    # Plot the suitability predictions
    fig, ax = plt.subplots(1, 1, figsize=(10, 4), dpi=100)
    vmin = np.min(projection.ravel())
    vmax = np.max(projection.ravel())
    img = ax.imshow(projection, vmin=vmin, vmax=vmax, cmap='coolwarm')
    ax.set_title(tag)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.colorbar(img, ax=ax, label="relative occurrence probability", pad=0.04)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)


def plot_partial_dependency(model, x_train, cat_indices=None, plot=False, save_path=False):
    labels = x_train.columns
    ncols = 4
    nrows = math.ceil((len(labels)-len(cat_indices))/ncols)
    percentiles=(0.025, 0.975)# lower and upper percentiles used to set the range to plot.
    n_bins=100 # the number of bins spanning the lower-upper percentile range.
    
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(4*ncols, 4*nrows), constrained_layout=True)
    axes = axes.flatten()
    
    plot_axes_index = 0
    for idx in range(len(labels)):
        if idx in cat_indices:
            continue
        pd = partial_dependence(
            model,
            x_train,
            [idx],
            percentiles=percentiles,
            grid_resolution=n_bins,
            kind="individual",
        )
        mean = pd["individual"][0].mean(axis=0)
        stdv = pd["individual"][0].std(axis=0)
        bins = pd["grid_values"][0]
        
        axes[plot_axes_index].fill_between(bins, mean - stdv, mean + stdv, alpha=0.25)
        axes[plot_axes_index].plot(bins, mean)
        axes[plot_axes_index].set_title(labels[idx])
        
        plot_axes_index += 1
        
    
    # Hide any unused axes
    for i in range(plot_axes_index, len(axes)):
        axes[i].axis('off')
    
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
        
    plt.close()
    

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
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
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
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    
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
    
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()

    plt.close(fig)
    