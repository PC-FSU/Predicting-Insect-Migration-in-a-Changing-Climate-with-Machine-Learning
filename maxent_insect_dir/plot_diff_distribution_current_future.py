import math
import matplotlib.pyplot as plt
import seaborn as sns
import rasterio as rio
from rasterio.warp import reproject, Resampling
import numpy as np
from pathlib import Path
from scipy.stats import ks_2samp
from config import Bioclim_mapping
plt.style.use('maxent_insect_dir/my_style.mplstyle')


def plot_current_future_feature_distribution(projections, raster_names, plot=False, save_path=False):
    """
    Plot the distribution of current vs. future climate rasters using KDE. Also, perform Kolmogorov-Smirnov (KS) tests.

    Parameters
    ----------
    projections : dict
        Dictionary containing paths to raster files for different years.
        Expected format:
        {
            "current": {"rasters": [list of paths]},
            "2040": {"rasters": [list of paths]},
            "2060": {"rasters": [list of paths]},
            "2080": {"rasters": [list of paths]},
            "2100": {"rasters": [list of paths]}
        }

    raster_names : list of str
        Names of raster variables (e.g., ["bio1", "bio12"]).

    plot : bool, optional (default=False)
        Whether to display the plots interactively.

    save_path : str or Path, optional (default=False)
        File path to save the figure. If False, the figure is not saved.

    Returns
    -------
    ks_results : dict
        Mapping from raster name → list of KS statistics and p-values for each future year.
    """
    ncols = 2
    nrows = math.ceil(len(raster_names) / ncols)

    # Pair current and future rasters together for each variable
    temp = list(zip(projections['current']['rasters'],
                    projections['2040']['rasters'], 
                    projections['2060']['rasters'], 
                    projections['2080']['rasters'], 
                    projections['2100']['rasters']))

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(7 * ncols, 5 * nrows))
    axs = axs.ravel()  # Flatten into 1D array for easy looping

    ks_results = {}  # Store KS results per raster variable

    for idx, ax in enumerate(axs):
        if idx >= len(raster_names):
            ax.axis('off')  # Hide unused subplots
            continue

        name = raster_names[idx]
        rasters = temp[idx]

        # Load current raster distribution
        with rio.open(rasters[0], 'r') as src:
            current_data = src.read(1, masked=True).compressed()

        # Plot current distribution
        sns.kdeplot(current_data, ax=ax, label='current', fill=True, alpha=0.5)

        ks_stats = []  # KS statistics across years

        # Compare current with each future year
        for raster, year in zip(rasters[1:], ['2040', '2060', '2080', '2100']):
            with rio.open(raster, 'r') as src:
                future_data = src.read(1, masked=True).compressed()

            # KS test between current and future
            ks_stat, p_value = ks_2samp(current_data, future_data)
            ks_stats.append(f"{year}: KS={ks_stat:.2f}, p={p_value:.2g}")

            # Plot future distribution
            sns.kdeplot(future_data, ax=ax, label=year, fill=True, alpha=0.5)

        # Title includes KS test results
        ax.set_title(f"{name}\n" + "\n".join(ks_stats))
        ax.legend()

        ks_results[name] = ks_stats

    plt.tight_layout()
    if plot:
        plt.show()
    if save_path:
        plt.savefig(Path(save_path))

    return ks_results


def get_raster_mapping(base_path, raster_names):
    """
    Generate file paths for raster names under a given base directory.

    Parameters
    ----------
    base_path : str or Path
        Base directory containing raster files.

    raster_names : list of str
        List of raster variable names (without extension).

    Returns
    -------
    rasters : list of Path
        List of raster file paths.

    mapping : dict
        Mapping of raster name → raster file path.
    """
    base_path = Path(base_path)
    rasters = [base_path / f"{name}.tif" for name in raster_names]
    return rasters, dict(zip(raster_names, rasters))


def plot_current_future_feature_difference(projections, raster_names, Bioclim_mapping, plot=False, save_path=False):
    """
    Plot pixel-wise differences between current and future climate rasters.

    Parameters
    ----------
    projections : dict
        Dictionary containing paths to raster files for different years.
        Format same as in `plot_current_future_feature_distribution`.

    raster_names : list of str
        Names of raster variables.

    Bioclim_mapping : dict
        Mapping from raster name → descriptive label.

    plot : bool, optional (default=False)
        Whether to display plots interactively.

    save_path : str or Path, optional (default=False)
        Directory path to save the figures. If False, no files are saved.
    """
    ncols = 5
    nrows = len(raster_names)

    temp = list(zip(projections['current']['rasters'],
                    projections['2040']['rasters'], 
                    projections['2060']['rasters'], 
                    projections['2080']['rasters'], 
                    projections['2100']['rasters']))

    for row in range(nrows):
        fig, axs = plt.subplots(nrows=1, ncols=ncols, figsize=(5 * ncols, 3), constrained_layout=True)

        name = raster_names[row]
        rasters = temp[row]
        current_raster = rasters[0]

        # Read current raster
        with rio.open(current_raster, 'r') as current:
            curr_pixel_area = current.res[0] * current.res[1]
            current_data = current.read(1, masked=True)

        # Fix colormap limits for consistency
        vmin_current = np.min(current_data.ravel())
        vmax_current = np.max(current_data.ravel())

        # Plot current climate raster
        im = axs[0].imshow(current_data, cmap='coolwarm', vmin=vmin_current, vmax=vmax_current)
        axs[0].set_title('Current value (Avg. over 1970–2000)')
        axs[0].set_xticks([])
        axs[0].set_yticks([])
        fig.colorbar(im, ax=axs[0], orientation='vertical', fraction=0.020, pad=0.04)

        col_ = 1
        for raster, year in zip(rasters[1:], ['2040', '2060', '2080', '2100']):
            with rio.open(raster, 'r') as future:
                future_pixel_area = future.res[0] * future.res[1]

            # Decide resampling direction based on pixel resolution
            if curr_pixel_area < future_pixel_area:
                high_res_raster, low_res_raster = current_raster, raster
            else:
                high_res_raster, low_res_raster = raster, current_raster

            # Align rasters for subtraction
            with rio.open(high_res_raster) as high_res, rio.open(low_res_raster) as low_res:
                high_res_data = high_res.read(1)
                high_res_transform = high_res.transform

                # Resample low-res raster to match high-res
                resampled_low_res_data = np.empty_like(high_res_data, dtype=np.float32)
                reproject(
                    source=rio.band(low_res, 1),
                    destination=resampled_low_res_data,
                    src_transform=low_res.transform,
                    src_crs=low_res.crs,
                    dst_transform=high_res_transform,
                    dst_crs=high_res.crs,
                    resampling=Resampling.bilinear
                )

                # Compute pixel-wise difference
                difference = resampled_low_res_data - high_res_data
                difference_ = difference[(difference < 1e6) & (difference > -1e6)]
                vmin, vmax = np.min(difference_.ravel()), np.max(difference_.ravel())

                # Plot difference map
                im = axs[col_].imshow(difference, cmap='coolwarm', vmin=vmin, vmax=vmax)
                axs[col_].set_title(f'Difference: {year} vs. current')
                axs[col_].set_xticks([])
                axs[col_].set_yticks([])
                fig.colorbar(im, ax=axs[col_], orientation='vertical', fraction=0.020, pad=0.04)

                col_ += 1

        fig.suptitle(f'{name}: {Bioclim_mapping[name]}')

        if save_path:
            save_path = Path(save_path)
            save_path.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path / f'curr_future_projection_diff_{name}.pdf')

        if plot:
            plt.show()
