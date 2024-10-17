
# def function to load monthly and yearly data

# def worldclim_bioclim_yearly_avg_insect_intersection(
#     climate_data_path: str,
#     insect_crop_data: gpd.GeoDataFrame
# ) -> gpd.GeoDataFrame:
#     """
#     Extracts bioclimatic values from a set of raster files at the locations
#     specified in the insect_crop_data and adds them as columns in the GeoDataFrame.

#     Parameters:
#     -----------
#     climate_data_path : str
#         Path to the directory containing raster files with bioclimatic data.
#     insect_crop_data : GeoDataFrame
#         GeoDataFrame containing point geometries.

#     Returns:
#     --------
#     GeoDataFrame
#         Updated GeoDataFrame with additional columns for each bioclimatic variable.
#     """

#     # Get list of raster files sorted by bioclim variable index
#     files = sorted(
#         [f for f in os.listdir(climate_data_path) if f.endswith('.tif')],
#         key=lambda x: int(x.split('_')[-1].split('.')[0])
#     )

#     for idx, file in enumerate(files):
#         raster_path = os.path.join(climate_data_path, file)
#         var_name = f'WORLDCLIM_YEARLY_AVG_BIO{idx + 1}'

#         # Sample raster values at insect locations
#         insect_crop_data[var_name] = sample_raster_values_at_points(
#             point_gdf=insect_crop_data,
#             raster_file=raster_path,
#             value_column_name=var_name
#         )

#     # Extra processing step: remove outlier values
#     bio2_col = 'WORLDCLIM_YEARLY_AVG_BIO2'
#     if bio2_col in insect_crop_data.columns:
#         insect_crop_data = insect_crop_data[
#             (insect_crop_data[bio2_col] > -1e6) & (insect_crop_data[bio2_col] < 1e6)
#         ]

#     return insect_crop_data


# def worldclim_bioclim_monthly_avg_insect_intersection(
#     climate_data_path: Dict[str, Dict[str, str]],
#     insect_crop_data: gpd.GeoDataFrame,
#     id_column: str
# ) -> gpd.GeoDataFrame:
#     """
#     Intersects monthly climate data with insect point data on a per-year basis.

#     Args:
#         climate_data_path (dict): Dictionary with year ranges as keys and paths to climate data as values.
#         insect_crop_data (GeoDataFrame): GeoDataFrame containing insect data (coordinates, month, year).
#         id_column (str): Column name for unique identifiers of insect points.

#     Returns:
#         GeoDataFrame: The original insect data merged with the corresponding climate data (tmax, tmin, prec).
#     """

#     results = []

#     # Group the insect point data by year for processing efficiency
#     grouped = insect_crop_data.groupby('year')

#     # Process each year group
#     for year, group in grouped:
#         sample_count = group[id_column].count()
#         print(f'Processing {sample_count} samples for the year {year}...\n')

#         # Get the nearest available climate data for the year
#         year_dict, year_range, boundary = get_nearest_time_range(year, climate_data_path)

#         # If the current year is out of range, use the boundary year
#         if boundary != year:
#             print(f'Updating year {year} to nearest available year {boundary}.')
#             year = boundary

#         # Build the file paths for the monthly tmax, tmin, and prec data
#         final_dict_path = {}
#         for var in ['tmax', 'tmin', 'prec']:
#             final_dict_path[var] = {
#                 month: os.path.join(
#                     year_dict[var],
#                     f'wc2.1_10m_{var}_{year}-{month:02d}.tif'
#                 ) for month in range(1, 13)
#             }

#         # Validate CRS consistency
#         sample_raster_files = [
#             final_dict_path['tmax'][1],
#             final_dict_path['tmin'][1],
#             final_dict_path['prec'][1]
#         ]
#         validate_crs_consistency(group, sample_raster_files)

#         # Iterate over each insect point in the group
#         for idx, row in group.iterrows():
#             insect_location = [(row.geometry.x, row.geometry.y)]
#             month = row['month']

#             data_values = {}
#             for var in ['tmax', 'tmin', 'prec']:
#                 raster_file = final_dict_path[var][month]
#                 value = sample_raster_values_at_points(
#                     point_gdf=gpd.GeoDataFrame(geometry=[row.geometry], crs=group.crs),
#                     raster_file=raster_file,
#                     value_column_name=var
#                 )[0]
#                 data_values[f'WORLDCLIM_MONTHLY_AVG_{var}'] = value

#             # Append the results for the current insect point
#             data_values['insect_id'] = row[id_column]
#             results.append(data_values)

#     # Convert results into a DataFrame
#     result_df = pd.DataFrame(results)

#     # Merge the result DataFrame with the original insect data
#     insect_crop_data = pd.merge(
#         insect_crop_data,
#         result_df,
#         how='left',
#         left_on=id_column,
#         right_on='insect_id'
#     )

#     return insect_crop_data