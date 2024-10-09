import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import warnings
from typing import Dict, List, Union

from maxent_insect_dir.config import *
from maxent_insect_dir.utils_common import *


# ============================================================
# Function: Find intersection between crop and location
# ============================================================

def crops_insect_intersection_presence(
    point_df: gpd.GeoDataFrame,
    crop_raster_config: Dict[int, str],
    id_column: str,
    crop_mapping_dict: Dict[int, str]
) -> gpd.GeoDataFrame:
    """
    Identifies the crop type at specific insect locations for given years by matching
    insect point data with corresponding crop raster data.

    Parameters:
    -----------
    point_df : GeoDataFrame
        GeoDataFrame containing insect point data with 'geometry' and 'year' columns.
    crop_raster_config : dict
        Dictionary mapping years to raster file paths.
    id_column : str
        Column name in point_df that uniquely identifies each insect point.
    crop_mapping_dict : dict
        Dictionary mapping crop codes to crop names.

    Returns:
    --------
    GeoDataFrame
        Updated GeoDataFrame with a new 'crop' column indicating the crop type at each location.
    """
    results = []
    total_sample_processed = 0

    # Group the insect point data by 'year'
    grouped = point_df.groupby('year')

    for year, group in grouped:
        sample_count = group[id_column].count()
        print(f'Processing {sample_count} samples for the year {year}...\n')

        # Skip years not in crop_raster_config
        if year not in crop_raster_config:
            warnings.warn(f"No raster file available for year {year}. Skipping this year.", UserWarning)
            continue

        raster_file = crop_raster_config[year]

        # Sample raster values at insect locations
        sampled_values_df = sample_raster_values_at_points(
            point_gdf=group,
            raster_file=raster_file,
            id_column=id_column,
            value_column_name='crop_code'
        )

        # Append the results
        results.append(sampled_values_df)
        total_sample_processed += sample_count

    # Concatenate results from all years
    if results:
        result_df = pd.concat(results, ignore_index=True)
    else:
        result_df = pd.DataFrame(columns=[id_column, 'crop_code'])

    # Map crop codes to crop names
    result_df = map_codes_to_names(
        df=result_df,
        code_column='crop_code',
        mapping_dict=crop_mapping_dict,
        name_column='crop'
    )

    # Merge the crop data back into the original point DataFrame
    point_df = pd.merge(point_df, result_df[[id_column, 'crop']], how='left', on=id_column)

    # Impute missing crop values with the mode
    if point_df['crop'].isna().any():
        most_common_crop = point_df['crop'].mode()[0]
        point_df['crop'] = point_df['crop'].fillna(most_common_crop)

    print(f'Processed_samples/total_samples: {total_sample_processed}/{point_df.shape[0]}')

    return point_df
