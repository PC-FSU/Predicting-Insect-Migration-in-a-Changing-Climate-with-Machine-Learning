"""Unit tests for the Continuous Boyce Index implementation."""

from __future__ import annotations

import numpy as np
import pytest

from maxent_insect_dir.Continuous_boyce_index import (
    boyce_index,
    continuous_boyce_index,
    get_intervals,
)


def test_get_intervals_default_nbins() -> None:
    """Default settings should create 10 equal-width bins on [0, 1]."""
    intervals = get_intervals(nbins=0, bin_size="default", range=(0.0, 1.0))
    assert intervals.shape == (10, 2)
    assert intervals[0, 0] == pytest.approx(0.0)
    assert intervals[-1, 1] == pytest.approx(1.0)


def test_boyce_index_perfect_separation() -> None:
    """Presences in high suitability should yield F > 1 in the top bin."""
    yobs = np.array([0.9, 0.95, 0.85, 0.8])
    ypred = np.linspace(0.0, 1.0, 50)
    fi = boyce_index(yobs, ypred, (0.8, 1.0))
    assert fi > 1.0


def test_continuous_boyce_index_positive_correlation() -> None:
    """Well-calibrated suitability should produce a positive Spearman CBI."""
    rng = np.random.default_rng(0)
    ypred = rng.uniform(0.0, 1.0, size=2000)
    # Presence points preferentially sample high suitability
    yobs = rng.beta(5, 2, size=200)
    result = continuous_boyce_index(yobs=yobs, ypred=ypred, nbins=10, to_plot=False)
    assert "Spearman.cor" in result
    assert result["Spearman.cor"] > 0.3
    assert len(result["F.ratio"]) == 10


def test_continuous_boyce_index_rejects_empty() -> None:
    """Empty arrays should raise ValueError."""
    with pytest.raises(ValueError):
        continuous_boyce_index(yobs=np.array([]), ypred=np.array([0.1, 0.2]))
