"""Unit tests for spatial thinning and correlation helpers."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point

from maxent_insect_dir.utils import remove_highly_correlated, spatial_thinning


def _point_gdf(coords: list[tuple[float, float]]) -> gpd.GeoDataFrame:
    """Build a simple projected point GeoDataFrame.

    Args:
        coords: List of (x, y) coordinates.

    Returns:
        GeoDataFrame in EPSG:5070.
    """
    return gpd.GeoDataFrame(
        geometry=[Point(x, y) for x, y in coords],
        crs="EPSG:5070",
    )


def test_spatial_thinning_removes_close_points() -> None:
    """Points closer than min_distance should be thinned."""
    gdf = _point_gdf([(0, 0), (10, 0), (100000, 0)])
    thinned = spatial_thinning(gdf, min_distance=1000)
    assert len(thinned) == 2


def test_spatial_thinning_noop_when_none() -> None:
    """None distance should keep all points."""
    gdf = _point_gdf([(0, 0), (10, 0), (20, 0)])
    thinned = spatial_thinning(gdf, min_distance=None)
    assert len(thinned) == 3


def test_remove_highly_correlated() -> None:
    """Near-duplicate columns should be dropped above the threshold."""
    rng = np.random.default_rng(1)
    a = rng.normal(size=200)
    df = pd.DataFrame(
        {
            "a": a,
            "b": a + rng.normal(scale=0.01, size=200),
            "c": rng.normal(size=200),
        }
    )
    cleaned = remove_highly_correlated(df, threshold=0.9)
    assert "a" in cleaned.columns
    assert "c" in cleaned.columns
    assert "b" not in cleaned.columns


def test_config_insect_alias() -> None:
    """Historical Spooted_Lanternfly key should alias Spotted_Lanternfly."""
    from maxent_insect_dir import config

    assert config.Insect_list["Spooted_Lanternfly"] == config.Insect_list["Spotted_Lanternfly"]
    assert "SSP_245" in config.VALID_PATHWAYS
