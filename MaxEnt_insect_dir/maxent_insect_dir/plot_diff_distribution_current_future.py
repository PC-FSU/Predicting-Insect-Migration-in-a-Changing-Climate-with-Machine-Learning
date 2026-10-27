import math
import matplotlib.pyplot as plt
import seaborn as sns
import rasterio as rio
from rasterio.warp import reproject, Resampling
import numpy as np
import pathlib
import os
from scipy.stats import ks_2samp
from maxent_insect_dir.config import BIOCLIM_MAPPING, MPLSTYLE_PATH

Bioclim_mapping = BIOCLIM_MAPPING
plt.style.use(str(MPLSTYLE_PATH))

def plot_current_future_feature_distribution(projections, raster_names, plot=False, save_path=False):
    ncols = 2
    nrows = math.ceil(len(raster_names) / ncols)
    
    temp = list(zip(projections['current']['rasters'],
                    projections['2040']['rasters'], 
                    projections['2060']['rasters'], 
                    projections['2080']['rasters'], 
                    projections['2100']['rasters']))

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(7 * ncols, 5 * nrows))
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
        
        print(name)

        # Compare current distribution with future distributions and plot them
        for raster, year in zip(rasters[1:], ['2040', '2060', '2080', '2100']):
            with rio.open(raster, 'r') as src:
                future_data = src.read(1, masked=True).compressed()
            
            print(current_data.shape, future_data.shape)
            
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
    
    return ks_results


def get_raster_mapping(Base_path, raster_names):
    rasters = [os.path.join(Base_path, f'{i}.tif') for i in raster_names]
    return rasters, dict(zip(raster_names, rasters))



def plot_current_future_feature_difference(projections, raster_names, Bioclim_mapping, plot=False, save_path=False):
    
    ncols = 5
    nrows = len(raster_names)
    print(ncols, nrows)
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

        # Load current distribution
        with rio.open(current_raster, 'r') as current:
            curr_pixel_area = current.res[0] * current.res[1]  # Area of a pixel
            current_data = current.read(1, masked=True)

        # Define colormap limits for the first subplot
        vmin_current = np.min(current_data.ravel())
        vmax_current = np.max(current_data.ravel())

        # Plot the first subplot (Current climate)
        im = axs[0].imshow(current_data, cmap='coolwarm', vmin=vmin_current, vmax=vmax_current)
        axs[0].set_title(f'Current value (Avg. over 1970-2000)\n')
        axs[0].set_xticks([])
        axs[0].set_yticks([])

        # Add colorbar for the first subplot
        fig.colorbar(im, ax=axs[0], orientation='vertical', fraction=0.020, pad=0.04)

        col_ = 1
        # Compare current distribution with future distributions and plot them
        for raster, year in zip(rasters[1:], ['2040', '2060', '2080', '2100']):
            with rio.open(raster, 'r') as future:
                future_pixel_area = future.res[0] * future.res[1]
                
            # Determine which raster has higher resolution (smaller pixel area)
            if curr_pixel_area < future_pixel_area:
                high_res_raster, low_res_raster = current_raster, raster
            else:
                high_res_raster, low_res_raster = raster, current_raster
            

            with rio.open(high_res_raster) as high_res, rio.open(low_res_raster) as low_res:
        
                # Read high-res raster data
                high_res_data = high_res.read(1)
                high_res_transform = high_res.transform

                # Prepare an empty array for the resampled data
                resampled_low_res_data = np.empty_like(high_res_data, dtype=np.float32)

                # Reproject low-res raster to match high-res raster
                reproject(
                    source=rio.band(low_res, 1),
                    destination=resampled_low_res_data,
                    src_transform=low_res.transform,
                    src_crs=low_res.crs,
                    dst_transform=high_res_transform,
                    dst_crs=high_res.crs,
                    resampling=Resampling.bilinear  # Can change to nearest, cubic, etc.
                )
                
                # Generally high res data is one which is current, and low res raster is future projection.
                
                # Compute the difference
                difference = resampled_low_res_data - high_res_data
                difference_ = difference[(difference < 1e6) & (difference > -1e6)]
                vmin = np.min(difference_.ravel())
                vmax = np.max(difference_.ravel())

                # Plot the difference
                im = axs[col_].imshow(difference, cmap='coolwarm', vmin=vmin, vmax=vmax)
                axs[col_].set_title(f'Difference between {year} projection \n and current value')
                axs[col_].set_xticks([])
                axs[col_].set_yticks([])
                
                # Add colorbar for the first subplot
                fig.colorbar(im, ax=axs[col_], orientation='vertical', fraction=0.020, pad=0.04)
                col_ += 1

        
        fig.suptitle(f'{name}: {Bioclim_mapping[name]}')
        #plt.tight_layout()
        if save_path:
            plt.savefig(os.path.join(save_path,f'curr_future_projection_diff_{name}.pdf'))        
        if plot:
            plt.show()


if __name__ == '__main__':
    bioclim_path = pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_1970_2000/wc2.1_5m_bio/Clipped/In_tiff_format')
    raster_names = [
        'Bio1', 'Bio2', 'Bio3', 'Bio4', 'Bio5', 'Bio6', 'Bio7', 'Bio8', 'Bio9', 'Bio10',
        'Bio11', 'Bio12', 'Bio13', 'Bio14', 'Bio15', 'Bio16', 'Bio17', 'Bio18', 'Bio19',
    ]

    current_raster, current_raster_mapping = get_raster_mapping(bioclim_path, raster_names)
    
    
    # Projection_2021 = pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_1990_2021/Clipped/In_tiff_format')
    # rasters_2021, mapping_2021 = get_raster_mapping(Projection_2021, raster_names)

    Projection_2040 = pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2021_2040/Clipped/In_tiff_format')
    rasters_2040, mapping_2040 = get_raster_mapping(Projection_2040, raster_names)

    Projection_2060 = pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2041_2060/Clipped/In_tiff_format')
    rasters_2060, mapping_2060 = get_raster_mapping(Projection_2060, raster_names)

    Projection_2080 = pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2061_2080/Clipped/In_tiff_format')
    rasters_2080, mapping_2080 = get_raster_mapping(Projection_2080, raster_names)

    Projection_2100 = pathlib.Path('/data/Maxent/data/raw/Bioclim_worldclim_average_2081_2100/Clipped/In_tiff_format')
    rasters_2100, mapping_2100 = get_raster_mapping(Projection_2100, raster_names)
    
    
    projections = {
        'current' : {'rasters' : current_raster},
        '2040' : {'rasters' : rasters_2040},
        '2060' : {'rasters' : rasters_2060},
        '2080' : {'rasters' : rasters_2080},
        '2100' : {'rasters' : rasters_2100}
    }
    
    
    #plot_current_future_feature_distribution(projections, raster_names, plot=True)
    plot_current_future_feature_difference(projections, raster_names, Bioclim_mapping, plot=True, save_path='/data/Maxent/data/results/curr_future_projection_diff')
    
    