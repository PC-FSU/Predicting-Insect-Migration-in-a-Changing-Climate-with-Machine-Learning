from typing import Union

import geopandas as gpd
import numpy as np
import rasterio as rio
from rasterio.warp import transform_geom
import elapid as ela
import pathlib
from scipy.stats import mode
from shapely.geometry import Point
from maxent_insect_dir.config import *
from maxent_insect_dir.utils_common import *
from typing import Dict, List, Union

from elapid.types import CRSType, to_iterable




def xy_to_geodataframe(x: Union[float, list, np.ndarray], y: Union[float, list, np.ndarray], crs: CRSType = "epsg:4326") -> gpd.GeoDataFrame:
    """Converts x/y data into a geopandas GeoDataFrame.

    Args:
        x: 1-D array-like of x location values.
        y: 1-D array-like of y location values.
        crs: Coordinate Reference System.

    Returns:
        gdf: GeoDataFrame with Point geometries.
    """
    # Handle single x/y location values
    x = to_iterable(x)
    y = to_iterable(y)

    points = [Point(coords) for coords in zip(x, y)]
    gdf = gpd.GeoDataFrame({'geometry': points}, crs=crs)

    return gdf


def draw_points(raster_path: str, count: int, nodata: float = None, ignore_mask: bool = False) -> gpd.GeoDataFrame:
    """Create a random geographic sample of points based on a raster's extent.

    Selects from unmasked locations if the raster's nodata value is set.

    Args:
        raster_path: raster file path to sample locations from.
        count: number of samples to generate.
        nodata: add pixels with this value to the nodata mask.
        ignore_mask: sample from the full extent of the raster instead of unmasked areas only.

    Returns:
        points: Point geometry GeoDataFrame.
    """
    with rio.open(raster_path) as src:
        print(f'src.nodata : {src.nodata}')
        
        # Check if CRS is EPSG:4326, if not, set up conversion
        crs_is_4326 = src.crs.to_epsg() == 4326
        
        if not crs_is_4326:
            print(f"Reprojecting raster from {src.crs} to EPSG:4326...")

        if src.nodata is None or ignore_mask:
            if nodata is None:
                xmin, ymin, xmax, ymax = src.bounds
                xy = np.random.uniform((xmin, ymin), (xmax, ymax), (count, 2))
            else:
                data = src.read(1)
                mask = data != nodata
                rows, cols = np.where(mask)
                samples = np.random.choice(len(rows), count, replace=False)
                xy = np.zeros((count, 2))
                for i, sample in enumerate(samples):
                    x_coord, y_coord = src.xy(rows[sample], cols[sample])
                    if not crs_is_4326:
                        # Reproject coordinates to EPSG:4326
                        point_geom = transform_geom(
                            src.crs, 'EPSG:4326',
                            {'type': 'Point', 'coordinates': [x_coord, y_coord]}
                        )['coordinates']
                        x_coord, y_coord = point_geom
                    xy[i] = [x_coord, y_coord]
        else:
            if nodata is None:
                masked = src.read_masks(1)
                rows, cols = np.where(masked == 255)
            else:
                data = src.read(1, masked=True)
                data.mask |= (data.data == nodata)
                rows, cols = np.where(~data.mask)
            samples = np.random.choice(len(rows), count, replace=False)
            xy = np.zeros((count, 2))
            for i, sample in enumerate(samples):
                x_coord, y_coord = src.xy(rows[sample], cols[sample])
                if not crs_is_4326:
                    # Re-project coordinates to EPSG:4326
                    point_geom = transform_geom(
                        src.crs, 'EPSG:4326',
                        {'type': 'Point', 'coordinates': [x_coord, y_coord]}
                    )['coordinates']
                    x_coord, y_coord = point_geom
                xy[i] = [x_coord, y_coord]

        points = xy_to_geodataframe(
            xy[:, 0], xy[:, 1],
            crs='EPSG:4326' if not crs_is_4326 else src.crs
        )
        return points


def draw_background(bias_raster: str = None, count: int = 10000) -> gpd.GeoDataFrame:
    """Draws background sample points for modeling.

    Args:
        bias_raster: Path to a bias raster file to guide sampling. If None, samples uniformly from a predefined raster.
        count: Number of background points to generate.

    Returns:
        GeoDataFrame of background sample points.
    """
    if bias_raster is None:
        raster_uniform = pathlib.Path(
            "/data/Maxent/data/raw/crop_data/2008_30m_cdls/2008_30m_cdls_resampled_0.25.tif"
        )
        print(f'Loading uniformly from the domain defined by raster: {raster_uniform}')
        background_points = draw_points(raster_uniform, count, nodata=0)
    else:
        background_points = ela.sample_bias_file(bias_raster, count)
        # Ensure that the result is a GeoDataFrame
        if isinstance(background_points, gpd.GeoSeries):
            background_points = gpd.GeoDataFrame({'geometry': background_points}, crs=background_points.crs)
            
    return background_points





# Function to get crop and bioclim intersection based on the climate source
def get_crop_bioclim_intersection_background(gdf, id_column, climate_source):
    """Performs crop and bioclimatic data intersection for insect data."""
    
    print('\n.......Getting the LUH2 avgs for 1970_2000......\n')
    data_ = LUH2_intersection(
        raster_path=config_raw['LUH2']['avgs']['1970_2000'],
        gfd=gdf,
        id_column=id_column,
        label_prefix='LUH2_1970_2000_AVG_'    
    )
    
    print('\n.......Getting the LUH2 avgs for 1990_2021......\n')
    data_ = LUH2_intersection(
        raster_path=config_raw['LUH2']['avgs']['1990_2021'],
        gfd=data_,
        id_column=id_column,
        label_prefix='LUH2_1990_2021_AVG_'    
    )
    
    
    # WorldClim: Get yearly and monthly averages
    if climate_source == 'WorldClim':
        print('\n.......Getting the Bioclim avgs for 1970_2000 (WorldClim)......\n')
        data_ = bioclim_avg_insect_intersection(
            raster_path=config_raw['climate_data_worldclim']['avgs']['1970_2000'],
            gfd=data_,
            id_column=id_column,
            label_prefix='WORLDCLIM_1970_2000_AVG_'
        )
        
        print('\n.......Getting the Bioclim avgs for 1990_2021 (WorldClim)......\n')
        data_ = bioclim_avg_insect_intersection(
            raster_path=config_raw['climate_data_worldclim']['avgs']['1990_2021'],
            gfd=data_,
            id_column=id_column,
            label_prefix='WORLDCLIM_1990_2021_AVG_'
        )
        
        return data_
        
    else:
        # CDS: Get bioclim data for CDS dataset
        print('\n.......Getting Bioclim data (CDS)......\n')
        
        print('\n.......Getting the Bioclim avgs for 1970_2000 (CDS)......\n')
        data_ = bioclim_avg_insect_intersection(
            raster_path=config_raw['climate_data_CDS']['avgs']['1970_2000'],
            gfd=data_,
            id_column=id_column,
            label_prefix='CDS_1970_2000_AVG_'
        )
        
        print('\n.......Getting the Bioclim avgs for 1990_2021 (CDS)......\n')
        data_ = bioclim_avg_insect_intersection(
            raster_path=config_raw['climate_data_CDS']['avgs']['1990_2021'],
            gfd=data_,
            id_column=id_column,
            label_prefix='CDS_1990_2021_AVG_'
        )
        
        return data_