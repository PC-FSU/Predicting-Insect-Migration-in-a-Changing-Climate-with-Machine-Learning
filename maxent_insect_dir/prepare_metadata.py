import os


# Utility Functions
def get_raster_mapping(base_path, raster_names):
    """
    Generate a mapping of raster names to their file paths.

    Args:
        base_path (str): Base directory containing raster files.
        raster_names (list): List of raster file names (without extensions).

    Returns:
        tuple: List of raster file paths and a dictionary mapping raster names to paths.
    """
    rasters = [os.path.join(base_path, f"{name}.tif") for name in raster_names]
    return rasters, dict(zip(raster_names, rasters))


def get_bioclim_rasters_paths(bioclim_paths):
    """
    Retrieve paths and mappings for bioclimatic raster files.

    Args:
        bioclim_paths (str): Base path to bioclimatic raster files.

    Returns:
        tuple: List of raster paths, mapping of raster names to paths, and list of raster names.
    """
    raster_names = [
        "Bio1", "Bio2", "Bio3", "Bio4", "Bio5", "Bio6", "Bio7", "Bio8", "Bio9", "Bio10",
        "Bio11", "Bio12", "Bio13", "Bio14", "Bio15", "Bio16", "Bio17", "Bio18", "Bio19",
    ]
    rasters, raster_mapping = get_raster_mapping(bioclim_paths, raster_names)
    return rasters, raster_mapping, raster_names


# Metadata Preparation Functions
def prepare_bioclim_metadata(data, bioclim_config, avg, data_periods, raster_labels):
    """
    Prepare metadata for bioclimatic data.

    Args:
        data (dict): Data dictionary to populate.
        bioclim_config (dict): Configuration for bioclimatic data paths.
        avg (str): Key for average bioclimatic data in the configuration.
        data_periods (list): List of time periods for the data.
        raster_labels (dict): Dictionary to store raster labels.

    Returns:
        dict: Updated data dictionary.
    """
    for period in data_periods:
        if period == "train":
            data["train"]["bioclim"]["rasters"], data["train"]["bioclim"]["mapping"], raster_labels["bioclim"] = get_bioclim_rasters_paths(bioclim_config[avg])
        else:
            data[period]["bioclim"]["rasters"], data[period]["bioclim"]["mapping"], _ = get_bioclim_rasters_paths(bioclim_config[period])
    return data


def prepare_elevation_metadata(data, elevation_raster_path, data_periods, raster_labels):
    """
    Prepare metadata for elevation data.

    Args:
        data (dict): Data dictionary to populate.
        elevation_raster_path (str): Path to the elevation raster file.
        data_periods (list): List of time periods for the data.
        raster_labels (dict): Dictionary to store raster labels.

    Returns:
        dict: Updated data dictionary.
    """
    raster_labels["elevation"] = ["elevation"]
    elevation_mapping = {"elevation": elevation_raster_path}
    for period in data_periods:
        data[period]["elevation"] = {
            "rasters": elevation_raster_path,
            "mapping": elevation_mapping,
        }
    return data


def prepare_crop_metadata(data, crop_raster_path, data_periods, raster_labels):
    """
    Prepare metadata for crop data.

    Args:
        data (dict): Data dictionary to populate.
        crop_raster_path (str): Path to the crop raster file.
        data_periods (list): List of time periods for the data.
        raster_labels (dict): Dictionary to store raster labels.

    Returns:
        dict: Updated data dictionary.
    """
    raster_labels["crop"] = ["crop"]
    crop_mapping = {"crop": crop_raster_path}
    for period in data_periods:
        data[period]["crop"] = {
            "rasters": crop_raster_path,
            "mapping": crop_mapping,
        }
    return data


def prepare_experiment_metadata(bioclim_config, avg, data_periods, use_elevation=False, elevation_raster_path=None, use_crop=False, crop_raster_path=None):
    """
    Prepare datasets for climatic, elevation, and crop data.

    Args:
        bioclim_config (dict): Configuration for bioclimatic data paths by time period.
        avg (str): Key for average bioclimatic data in the configuration.
        data_periods (str): List of time periods for the projection.
        use_elevation (bool): Whether to include elevation data.
        elevation_raster_path (str): Path to the elevation data.
        use_crop (bool): Whether to include crop data.
        crop_raster_path (str): Path to the crop data.

    Returns:
        tuple: Organized data dictionary and raster labels.
    """
    data_used = ["bioclim"]  # Each experiment will have bioclimatic variables
    raster_labels = {}

    if use_elevation:
        data_used.append("elevation")
    if use_crop:
        data_used.append("crop")

    # Initialize data dictionary
    data = {
        period: {data_type: {"rasters": None, "mapping": None} for data_type in data_used}
        for period in data_periods
    }

    # Prepare metadata for each data type
    data = prepare_bioclim_metadata(data, bioclim_config, avg, data_periods, raster_labels)
    if use_elevation:
        data = prepare_elevation_metadata(data, elevation_raster_path, data_periods, raster_labels)
    if use_crop:
        data = prepare_crop_metadata(data, crop_raster_path, data_periods, raster_labels)

    return data, raster_labels


def prepare_projection_metadata(projection_config, columns):
    """
    Prepare metadata for future projections.

    Args:
        projection_config (dict): Configuration for projection data.
        columns (list): List of column names to maintain order.

    Returns:
        dict: Ordered mapping of column names to raster paths.
    """
    # Flatten the projection configuration
    unrolled_config = {}
    for key in projection_config.keys():
        for mapping_key, mapping_value in projection_config[key]["mapping"].items():
            unrolled_config[mapping_key] = mapping_value

    # Maintain column order as seen during training
    res = {col: unrolled_config[col] for col in columns}
    return res