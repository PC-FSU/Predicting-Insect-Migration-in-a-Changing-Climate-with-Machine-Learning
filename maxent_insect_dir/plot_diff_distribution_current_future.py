import math
import matplotlib.pyplot as plt
import seaborn as sns
import rasterio as rio
import pathlib
import os
from scipy.stats import ks_2samp



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
    
    return ks_results


def get_raster_mapping(Base_path, raster_names):
    rasters = [os.path.join(Base_path, f'{i}.tif') for i in raster_names]
    return rasters, dict(zip(raster_names, rasters))



if __name__ == '__main__':
    insect_name = 'Brown_Marmorated_Stink_bug'
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
    
    plot_current_future_feature_distribution(projections, raster_names, save_path='Worldclim_current_future_distribution_difference.pdf')
