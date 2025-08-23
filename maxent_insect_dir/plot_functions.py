import seaborn as sns
import elapid as ela
import math
import rasterio as rio
import numpy as np
import config
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
plt.style.use('./my_style.mplstyle')

from scipy.stats import ks_2samp
from sklearn.inspection import partial_dependence
from matplotlib.colors import ListedColormap


def plot_presence_background(presence, presence_thinned, background, plot=False, save_path=False):
    """
    Plot presence points, spatially thinned presence points, and background points 
    on a map with the US boundary for reference.

    Args:
        presence (GeoDataFrame): Original presence points.
        presence_thinned (GeoDataFrame): Presence points after spatial thinning.
        background (GeoDataFrame): Background sampling points.
        plot (bool, optional): If True, displays the figure. Default is False.
        save_path (str or Path, optional): Path to save the figure. Default is False.

    Returns:
        None
    """
    us_boundary = gpd.read_file(config.PATH_TO_US_BOUNDARY).to_crs(presence.crs)
    
    fig, ax = plt.subplots(1,3, figsize=(15,5))
    
    # Plot original presence
    presence.plot(ax=ax[0], color='red', alpha=0.1)
    us_boundary.plot(ax=ax[0], edgecolor='black', facecolor='none', linewidth=1)
    ax[0].set_title('Presence')
    ax[0].set_xticks([])
    ax[0].set_yticks([])

    # Plot thinned presence
    presence_thinned.plot(ax=ax[1], color='red', alpha=0.1)
    us_boundary.plot(ax=ax[1], edgecolor='black', facecolor='none', linewidth=1)
    ax[1].set_title('Presence spatially thinned')
    ax[1].set_xticks([])
    ax[1].set_yticks([])

    # Plot background
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
    """
    Plot histograms comparing environmental features for presence and background points.

    Args:
        presence (DataFrame): Environmental values at presence points.
        background (DataFrame): Environmental values at background points.
        raster_names (list[str]): Names of raster features to plot.
        plot (bool, optional): If True, displays the figure. Default is False.
        save_path (str or Path, optional): Path to save the figure. Default is False.

    Returns:
        None
    """
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
    """
    Plot KDE distributions of environmental features for presence vs background 
    and perform KS test.

    Args:
        presence (DataFrame): Presence feature values (geometry column dropped).
        background (DataFrame): Background feature values (geometry column dropped).
        labels (list[str]): Feature labels to compare.
        plot (bool, optional): If True, displays the figure. Default is False.
        save_path (str or Path, optional): Path to save the figure. Default is False.

    Returns:
        dict: KS results for each feature {feature: {ks_stat, p_value}}.
    """
    # Drop geometry column if exists
    if 'geometry' in presence.columns:
        presence = presence.drop(columns=['geometry'])
    if 'geometry' in background.columns:
        background = background.drop(columns=['geometry'])
    if 'geometry' in labels:
        labels.remove('geometry')
    
    ncols = 4
    nrows = math.ceil(len(labels) / ncols)
    pair_colors = ['blue', 'green']
    
    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(4 * ncols, 3 * nrows))
    axs = axs.ravel()

    ks_results = {}
    for idx, ax in enumerate(axs):
        if idx >= len(labels):
            ax.axis('off')
            continue
        
        name = labels[idx]
        pvar = presence[name]
        bvar = background[name]

        ks_stat, p_value = ks_2samp(pvar, bvar)
        ks_results[name] = {'ks_stat': ks_stat, 'p_value': p_value}

        sns.kdeplot(pvar, ax=ax, label='presence', color=pair_colors[0], fill=True, alpha=0.5)
        sns.kdeplot(bvar, ax=ax, label='background', color=pair_colors[1], fill=True, alpha=0.5)

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
    """
    Plot a correlation matrix as a heatmap using seaborn.

    Args:
        corr_matrix (pd.DataFrame or np.ndarray): Correlation matrix of features 
            (usually from `df.corr()`).
        title (str): Title for the heatmap plot.
        plot (bool, optional): If True, displays the plot interactively. Default is False.
        save_path (str or Path, optional): If provided, saves the plot to the given path. 
            Default is False.

    Returns:
        None
    """
    # Create a new figure with defined size
    fig = plt.figure(figsize=(10, 8))

    # Plot correlation matrix as a heatmap
    sns.heatmap(
        corr_matrix,
        annot=True,        # Display correlation values inside cells
        fmt=".2f",         # Format numbers to 2 decimal places
        cmap="coolwarm",   # Use diverging color map
        cbar=True,         # Show color bar
        square=True        # Force square cells
    )

    # Set the title for the plot
    plt.title(title)

    # Save figure if save_path is provided
    if save_path:
        plt.savefig(save_path)

    # Show the plot interactively if requested
    if plot:
        plt.show()

    # Close figure to free memory (important in batch plotting)
    plt.close(fig)



def plot_sample_weights(weights, plot=False, save_path=False):
    """
    Plot the distribution of sample weights.

    Args:
        weights (array-like): List or array of sample weights.
        plot (bool, optional): If True, displays the figure. Default is False.
        save_path (str or Path, optional): Path to save the figure. Default is False.

    Returns:
        None
    """
    fig, ax = plt.subplots(figsize=(6,4))
    ax.hist(weights, bins=30, color="skyblue", edgecolor="black", alpha=0.7)
    ax.set_title("Distribution of Sample Weights")
    ax.set_xlabel("Weight")
    ax.set_ylabel("Frequency")

    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)


def plot_feature_importance(feature_importance, plot=False, save_path=False):
    """
    Plot feature importance scores as a bar chart.

    Args:
        feature_importance (pd.Series): Feature importance values, with feature names as index.
        plot (bool, optional): If True, displays the plot interactively. Default is False.
        save_path (str or Path, optional): If provided, saves the plot to the given path.
            Default is False (no file saved).

    Returns:
        None
    """
    # Sort features by importance (highest first)
    feature_importance = feature_importance.sort_values(ascending=False)

    # Initialize figure
    fig = plt.figure(figsize=(12, 6))

    # Plot feature importance as a bar chart
    feature_importance.plot(kind='bar', title='Permutation Importance')

    # Label the y-axis
    plt.ylabel('Mean Decrease in AUC')

    # Rotate x-axis labels for readability
    plt.xticks(rotation=45, ha='right')

    # Adjust layout to prevent label overlap
    plt.tight_layout()

    # Save figure if path is provided
    if save_path:
        plt.savefig(save_path)

    # Show plot interactively if requested
    if plot:
        plt.show()

    # Close figure to free memory
    plt.close(fig)



def plot_partial_dependence(model, X, features, feature_names, plot=False, save_path=False):
    """
    Plot partial dependence plots (PDP) for a trained model.

    Args:
        model (fitted estimator): Trained ML model supporting sklearn's partial_dependence.
        X (DataFrame): Input data used for computing PDP.
        features (list[int]): Indices of features to compute PDP for.
        feature_names (list[str]): Names of features corresponding to indices.
        plot (bool, optional): If True, displays the plots. Default is False.
        save_path (str or Path, optional): Path to save the figure. Default is False.

    Returns:
        None
    """
    ncols = 3
    nrows = math.ceil(len(features) / ncols)

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(4*ncols, 3*nrows))
    axs = axs.ravel()

    for i, feat_idx in enumerate(features):
        pdp, axes = partial_dependence(model, X, [feat_idx])
        axs[i].plot(axes[0], pdp[0], color="blue")
        axs[i].set_title(f"PDP: {feature_names[feat_idx]}")
        axs[i].set_xlabel(feature_names[feat_idx])
        axs[i].set_ylabel("Partial Dependence")

    # Turn off unused axes
    for j in range(len(features), len(axs)):
        axs[j].axis("off")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)


def plot_prediction_map(prediction_raster, title="Prediction Map", cmap="viridis", plot=False, save_path=False):
    """
    Plot a prediction raster as a map.

    Args:
        prediction_raster (str or Path): Path to raster file (GeoTIFF).
        title (str, optional): Plot title. Default is "Prediction Map".
        cmap (str, optional): Colormap for raster visualization. Default is 'viridis'.
        plot (bool, optional): If True, displays the plot. Default is False.
        save_path (str or Path, optional): Path to save the plot. Default is False.

    Returns:
        None
    """
    with rio.open(prediction_raster) as src:
        img = src.read(1)  # read first band
        bounds = src.bounds

    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(img, cmap=cmap, extent=[bounds.left, bounds.right, bounds.bottom, bounds.top])
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.colorbar(im, ax=ax, label="Prediction Value")

    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)


def plot_custom_colormap(data, cmap_list, bounds, plot=False, save_path=False):
    """
    Plot raster-like data with a custom colormap.

    Args:
        data (ndarray): 2D numpy array of data values.
        cmap_list (list[str]): List of colors for custom colormap.
        bounds (list[float]): Bin boundaries for coloring values.
        plot (bool, optional): If True, displays the plot. Default is False.
        save_path (str or Path, optional): Path to save the plot. Default is False.

    Returns:
        None
    """
    cmap = ListedColormap(cmap_list)

    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(data, cmap=cmap)
    ax.set_title("Custom Colormap Plot")
    ax.set_xticks([])
    ax.set_yticks([])

    cbar = fig.colorbar(im, ax=ax, boundaries=bounds, ticks=bounds)
    cbar.set_label("Value Bins")

    if save_path:
        plt.savefig(save_path)
    if plot:
        plt.show()
    plt.close(fig)
    
    
def plot_train_test_split(train, test, plot=False, title='Dataset', save_path=None):
    """
    Plot a train/test split of geospatial data on a map, overlaying the US boundary.

    Args:
        train (gpd.GeoDataFrame): Training dataset (must have a valid CRS).
        test (gpd.GeoDataFrame): Test dataset (must have the same CRS as train).
        plot (bool, optional): If True, displays the plot interactively. Default is False.
        title (str, optional): Title for the legend. Default is 'Dataset'.
        save_path (str or Path, optional): If provided, saves the plot to the given path. 
            Default is None.

    Returns:
        None
    """
    # Copy dataframes to avoid modifying originals
    train = train.copy()
    test = test.copy()

    # Add a 'split' column to distinguish between train/test
    train['split'] = 'train'
    test['split'] = 'test'

    # Read US boundary shapefile and match CRS to training data
    us_boundary = gpd.read_file(config.PATH_TO_US_BOUNDARY).to_crs(train.crs)

    # Combine train and test geodataframes into a single dataset
    checker = ela.stack_geodataframes(train, test)

    # Initialize figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Define color mapping for train/test
    split_colors = {'train': 'red', 'test': 'green'}
    categories = ['train', 'test']
    color_list = [split_colors[cat] for cat in categories]
    cmap = ListedColormap(color_list)

    # Plot the train/test points with categorical coloring
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

    # Overlay US boundary on top
    us_boundary.plot(ax=ax, edgecolor='black', facecolor='none', linewidth=1)

    # Remove axis ticks and borders
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')

    # Customize legend appearance
    legend = ax.get_legend()
    if legend:
        legend.set_frame_on(False)  # Remove legend box
        legend.set_title(title, prop={'size': 20})  # Legend title font size
        for text in legend.get_texts():
            text.set_fontsize(20)  # Legend label font size

    # Save figure if a path is provided
    if save_path:
        fig.savefig(save_path, bbox_inches='tight')

    # Show interactively if requested
    if plot:
        plt.show()

    # Close figure to free memory
    plt.close(fig)


def plot_PE_curve(x, y, plot=False, save_path=False):
    """
    Plot the Predicted/Expected (P/E) curve for the Boyce Index.

    The P/E curve compares predicted habitat suitability values to the ratio of
    observed presences (Predicted) against what would be expected under random
    distribution (Expected). It is often used in ecological modeling to evaluate
    species distribution models.

    Args:
        x (array-like): Habitat suitability values (e.g., interval midpoints).
        y (array-like): Predicted/Expected ratios corresponding to the 
            habitat suitability intervals.
        plot (bool, optional): If True, displays the plot interactively. Default is False.
        save_path (str or Path, optional): If provided, saves the plot to the given path.
            Default is False.

    Returns:
        None
    """
    # Create a new figure
    fig = plt.figure()

    # Plot the P/E curve with markers
    plt.plot(x, y, marker="o")

    # Label axes
    plt.xlabel("Habitat suitability")
    plt.ylabel("Predicted/Expected ratio")

    # Add title
    plt.title("Boyce Index")

    # Adjust layout to prevent overlaps
    plt.tight_layout()

    # Save figure if path is provided
    if save_path:
        plt.savefig(save_path)

    # Show plot interactively if requested
    if plot:
        plt.show()

    # Close figure to free memory
    plt.close(fig)


def plot_partial_dependency(model, x_train, cat_indices=None, plot=False, save_path=False):
    """
    Plot partial dependence plots (PDPs) for a trained model.

    Partial dependence plots show how the predicted outcome of a model 
    changes when a feature is varied over its range, while keeping 
    other features constant. This helps interpret the effect of 
    individual features on the model's predictions.

    Args:
        model: Trained model (must support scikit-learn's `partial_dependence`).
        x_train (pd.DataFrame): Training data used for PDP computation.
        cat_indices (list[int], optional): Indices of categorical features 
            to skip when plotting. Default is None.
        plot (bool, optional): If True, display the plots interactively. Default is False.
        save_path (str or Path, optional): If provided, saves the figure at this path. Default is False.

    Returns:
        None
    """
    # Extract feature names
    labels = x_train.columns

    # Arrange plots in a grid layout
    ncols = 4
    nrows = math.ceil((len(labels) - len(cat_indices)) / ncols)

    # Define parameters for PDP computation
    percentiles = (0.025, 0.975)  # Focus on central range of feature values
    n_bins = 100  # Number of points for evaluating partial dependence

    # Create figure and grid of subplots
    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols,
        figsize=(4 * ncols, 4 * nrows),
        constrained_layout=True
    )
    axes = axes.flatten()  # Flatten for easy indexing

    plot_axes_index = 0  # Track which subplot to fill

    # Loop through all features
    for idx in range(len(labels)):
        if idx in cat_indices:  # Skip categorical features
            continue

        # Compute partial dependence for the given feature
        pd = partial_dependence(
            model, x_train, [idx],
            percentiles=percentiles,
            grid_resolution=n_bins,
            kind="individual",  # Compute individual curves
        )

        # Get mean and standard deviation of individual predictions
        mean = pd["individual"][0].mean(axis=0)
        stdv = pd["individual"][0].std(axis=0)
        bins = pd["grid_values"][0]

        # Plot mean PDP with uncertainty band
        axes[plot_axes_index].fill_between(bins, mean - stdv, mean + stdv, alpha=0.25)
        axes[plot_axes_index].plot(bins, mean)

        # Add feature name as subplot title
        axes[plot_axes_index].set_title(labels[idx])

        plot_axes_index += 1

    # Hide any unused axes (if features < grid cells)
    for i in range(plot_axes_index, len(axes)):
        axes[i].axis('off')

    # Save figure if path is provided
    if save_path:
        plt.savefig(save_path)

    # Show interactively if requested
    if plot:
        plt.show()

    # Close figure to free memory
    plt.close()


def plot_projection(projection, tag, plot=False, save_path=None):
    """
    Plot the habitat suitability (projection) map with a colorbar.

    Args:
        projection (np.ndarray): 2D array of suitability predictions.
        tag (str): Title for the plot (e.g., dataset or scenario label).
        plot (bool, optional): If True, display the plot interactively. Default is False.
        save_path (str or Path, optional): If provided, saves the figure at this path. Default is None.

    Returns:
        None
    """
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(10, 4), dpi=100)

    # Determine color scaling
    vmin, vmax = np.min(projection), np.max(projection)

    # Plot the raster data
    img = ax.imshow(projection, vmin=vmin, vmax=vmax, cmap='coolwarm')

    # Add title and remove ticks for cleaner map
    ax.set_title(tag)
    ax.set_xticks([])
    ax.set_yticks([])

    # Add colorbar
    fig.colorbar(img, ax=ax, label="Relative occurrence probability", pad=0.04)

    # Adjust layout
    plt.tight_layout()

    # Save if path provided
    if save_path:
        save_path = Path(save_path)  # ensure pathlib
        fig.savefig(save_path, bbox_inches="tight")

    # Show interactively if requested
    if plot:
        plt.show()

    # Close figure to free memory
    plt.close(fig)