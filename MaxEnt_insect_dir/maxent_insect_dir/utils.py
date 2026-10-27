"""Shared geometric and statistical helpers for the MaxEnt pipeline."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple, Union

import elapid as ela
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn import metrics
from sklearn.inspection import permutation_importance
from sklearn.metrics import make_scorer, roc_auc_score

from maxent_insect_dir.spatial_kde import spatial_kernel_density


def inside_mask(points: gpd.GeoDataFrame, mask_raster: Union[str, os.PathLike]) -> np.ndarray:
    """Boolean array: True where a point falls on a cell with value 1 of ``mask_raster``.

    The mask is an accessible-area raster on the climate grid (scripts/accessible_area.py).
    Points outside the raster extent are outside the mask.
    """
    import rasterio
    with rasterio.open(mask_raster) as src:
        m = src.read(1)
        pts = points.to_crs(src.crs)
        rows, cols = rasterio.transform.rowcol(src.transform, pts.geometry.x.values, pts.geometry.y.values)
    rows, cols = np.asarray(rows), np.asarray(cols)
    ok = (rows >= 0) & (rows < m.shape[0]) & (cols >= 0) & (cols < m.shape[1])
    out = np.zeros(len(points), dtype=bool)
    out[ok] = m[rows[ok], cols[ok]] == 1
    return out


def _mask_uniform_raster(uniform_raster, mask_raster, out_path) -> None:
    """Copy of ``uniform_raster`` with every cell outside the accessible area set to nodata."""
    import rasterio
    with rasterio.open(uniform_raster) as src, rasterio.open(mask_raster) as msk:
        assert src.shape == msk.shape and src.transform == msk.transform, 'mask must be on the climate grid'
        arr = src.read(1, masked=True)
        nod = src.nodata if src.nodata is not None else -9999.0
        data = np.where((msk.read(1) == 1) & ~np.ma.getmaskarray(arr), arr.filled(nod), nod).astype(src.dtypes[0])
        prof = src.profile.copy(); prof.update(nodata=nod)
    with rasterio.open(out_path, 'w', **prof) as dst:
        dst.write(data, 1)


def _mask_bias_raster(bias_raster, mask_raster) -> None:
    """Set the kernel-density cells whose centre lies outside the accessible area to nodata."""
    import rasterio
    with rasterio.open(bias_raster) as src:
        z = src.read(1); prof = src.profile.copy(); tr, crs, nod = src.transform, src.crs, src.nodata
    rows, cols = np.indices(z.shape)
    xs, ys = rasterio.transform.xy(tr, rows.ravel(), cols.ravel(), offset='center')
    centres = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xs, ys), crs=crs)
    keep = inside_mask(centres, mask_raster).reshape(z.shape)
    if nod is None:
        nod = -9999.0; prof.update(nodata=nod)
    z = np.where(keep, z, nod).astype(prof['dtype'])
    with rasterio.open(bias_raster, 'w', **prof) as dst:
        dst.write(z, 1)


def spatial_thinning(gdf: gpd.GeoDataFrame, min_distance: Optional[float]) -> gpd.GeoDataFrame:
    """Thin presence points so retained points are at least ``min_distance`` apart.

    Args:
        gdf: Point GeoDataFrame.
        min_distance: Minimum separation in CRS units (meters for projected CRS).
            If ``None`` or ``<= 0``, returns a copy without thinning.

    Returns:
        Thinned GeoDataFrame with a reset index.
    """
    if min_distance is None or min_distance <= 0:
        return gdf.copy().reset_index(drop=True)

    coords = np.array([(geom.x, geom.y) for geom in gdf.geometry])
    tree = cKDTree(coords)
    keep_indices: List[int] = []
    considered: set = set()

    for idx in range(len(coords)):
        if idx in considered:
            continue
        indices = tree.query_ball_point(coords[idx], r=min_distance)
        keep_indices.append(idx)
        considered.update(indices)

    return gdf.iloc[keep_indices].reset_index(drop=True)


DEFAULT_KERNEL_RADIUS: float = 160000.0  # metres, EPSG:5070


def spatial_weighted_background(
    presence: gpd.GeoDataFrame,
    uniform_raster: Union[str, os.PathLike],
    bias_uniform_mix_coeff: float = 0.0,
    count: int = 1000,
    kernel_radius: float = DEFAULT_KERNEL_RADIUS,
    mask_raster: Optional[Union[str, os.PathLike]] = None,
) -> gpd.GeoDataFrame:
    """Sample background points as a mix of uniform and presence-biased draws.

    The "buffer" of the manuscript is a quartic (biweight) kernel density surface
    built from the thinned presences with search radius ``kernel_radius``
    (160 km by default) on a ``kernel_radius / 10`` grid in EPSG:5070. The biased
    share of the background is drawn from that surface with probability
    proportional to the kernel density (``elapid.sample_bias_file``); the
    uniform share is drawn from the valid cells of ``uniform_raster``
    (``elapid.sample_raster``). Both draws are with replacement. Points that
    later fall on a no-data climate cell (sea, outside the US raster) are
    discarded when the predictors are annotated.

    Args:
        presence: Presence points used to build the KDE bias surface.
        uniform_raster: Raster used for uniform sampling (typically a bioclim layer).
        bias_uniform_mix_coeff: Fraction of points drawn from the bias surface
            (``0`` = fully uniform, ``1`` = fully biased).
        count: Total number of background points.
        kernel_radius: Kernel search radius (bandwidth) in metres.
        mask_raster: Optional accessible-area raster on the climate grid (1 = inside).
            When given, both the uniform and the kernel draws are limited to it.

    Returns:
        Background GeoDataFrame in EPSG:5070.
    """
    # m = 0 keeps every background point uniform. m = 1 keeps every point inside
    # the presence kernel. Seed numpy (run.py --seed) for a repeatable draw.
    n_point_biased = int(count * bias_uniform_mix_coeff)
    n_point_uniform = int(count - n_point_biased)
    print(
        f"Number of points selected | uniformly: {n_point_uniform} | with bias: {n_point_biased}\n"
    )

    dir_path = f"temp_{hash(datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f'))}"
    bias_raster = os.path.join(dir_path, "bias.tif")
    os.makedirs(dir_path, exist_ok=True)

    try:
        spatial_kernel_density(
            points=presence,
            radius=float(kernel_radius),
            output_path=bias_raster,
            output_pixel_size=float(kernel_radius) / 10.0,
            output_driver="GTiff",
            scaled=True,
        )
        if mask_raster is not None:
            _mask_bias_raster(bias_raster, mask_raster)
            masked_uniform = os.path.join(dir_path, "uniform_in_M.tif")
            _mask_uniform_raster(uniform_raster, mask_raster, masked_uniform)
            uniform_raster = masked_uniform

        point_sampled_uniformly = gpd.GeoDataFrame(geometry=[], crs="EPSG:5070")
        point_sampled_with_bias = gpd.GeoDataFrame(geometry=[], crs="EPSG:5070")

        if bias_uniform_mix_coeff == 0:
            point_sampled_uniformly = ela.sample_raster(uniform_raster, n_point_uniform).to_crs(
                epsg=5070
            )
        elif bias_uniform_mix_coeff == 1:
            point_sampled_with_bias = ela.sample_bias_file(bias_raster, n_point_biased).to_crs(
                epsg=5070
            )
        else:
            point_sampled_uniformly = ela.sample_raster(uniform_raster, n_point_uniform).to_crs(
                epsg=5070
            )
            point_sampled_with_bias = ela.sample_bias_file(bias_raster, n_point_biased).to_crs(
                epsg=5070
            )
    finally:
        shutil.rmtree(dir_path, ignore_errors=True)

    merged = pd.concat(
        [point_sampled_uniformly.geometry, point_sampled_with_bias.geometry],
        ignore_index=True,
    )
    merged = gpd.GeoSeries(merged, crs="EPSG:5070")
    return gpd.GeoDataFrame(geometry=merged, crs="EPSG:5070")


def remove_highly_correlated(df: pd.DataFrame, threshold: float = 0.9) -> pd.DataFrame:
    """Drop features whose absolute Pearson correlation exceeds ``threshold``.

    Args:
        df: DataFrame of continuous predictors.
        threshold: Absolute correlation cutoff.

    Returns:
        DataFrame with highly correlated columns removed.
    """
    corr_matrix = df.corr()
    upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [
        column for column in upper_triangle.columns if any(upper_triangle[column].abs() > threshold)
    ]
    print(f"Columns to drop (correlation > {threshold}): {to_drop}")
    return df.drop(columns=to_drop)


def get_train_test_split(
    df: gpd.GeoDataFrame, grid_size: float = 0.05, swap: bool = False
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Split points with a spatial checkerboard.

    The grid origin is the lower-left corner of the presence bounding box and
    the cell size is 50 km in EPSG:5070, so the split is deterministic for a
    given presence set (the same cells are train or test in every repeat).

    Args:
        df: Input GeoDataFrame.
        grid_size: Checkerboard cell size (degrees if geographic; meters if projected).
        swap: If True, exchange the two colours of the checkerboard, i.e. train
            on the cells that are normally test cells and vice versa.

    Returns:
        Tuple of ``(train, test)`` GeoDataFrames.
    """
    if not df.crs.is_geographic:
        grid_size = 50000
    print(f"Using the grid_size : {grid_size}..\n")
    train, test = ela.checkerboard_split(df, grid_size=grid_size)
    if swap:
        print("Swapping checkerboard colours (train <-> test)..\n")
        train, test = test, train
    return train, test


def get_feature_importance(
    model: object, x_test: pd.DataFrame, y_test: pd.Series
) -> pd.Series:
    """Compute permutation importance (ROC-AUC) for a fitted classifier.

    Args:
        model: Fitted estimator with ``predict_proba``.
        x_test: Test feature matrix.
        y_test: Test labels.

    Returns:
        Series of mean importance scores indexed by column name.
    """
    try:
        scorer = make_scorer(roc_auc_score, response_method="predict_proba")
    except TypeError:
        scorer = make_scorer(roc_auc_score, needs_proba=True)
    model.classes_ = np.array(model.classes_)
    result = permutation_importance(
        model, x_test, y_test, n_repeats=10, random_state=42, scoring=scorer
    )
    return pd.Series(result.importances_mean, index=x_test.columns)


def get_auc_score(
    model: object,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    sample_weight_test: Optional[np.ndarray] = None,
) -> Dict[str, Union[float, str]]:
    """Compute weighted and unweighted ROC-AUC on the test set.

    Args:
        model: Fitted classifier.
        x_test: Test features.
        y_test: Test labels.
        sample_weight_test: Optional sample weights.

    Returns:
        Dictionary of AUC metrics.
    """
    auc: Dict[str, Union[float, str]] = {
        "Unweighted_checkerboard_AUC_score_on_test": "n/a",
        "Weighted_checkerboard_AUC_score_on_test": "n/a",
    }
    y_pred = model.predict(x_test)
    auc["Unweighted_checkerboard_AUC_score_on_test"] = round(
        metrics.roc_auc_score(y_test, y_pred), 4
    )
    if sample_weight_test is not None:
        auc["Weighted_checkerboard_AUC_score_on_test"] = round(
            metrics.roc_auc_score(y_test, y_pred, sample_weight=sample_weight_test), 4
        )
    print(auc)
    return auc


def get_raster_mapping(
    base_path: Union[str, os.PathLike], raster_names: Sequence[str]
) -> Tuple[List[str], Dict[str, str]]:
    """Map raster variable names to ``.tif`` paths under ``base_path``.

    Args:
        base_path: Directory containing TIFF rasters.
        raster_names: Variable names without extensions.

    Returns:
        Ordered path list and name-to-path mapping.
    """
    rasters = [os.path.join(str(base_path), f"{name}.tif") for name in raster_names]
    return rasters, dict(zip(raster_names, rasters))
