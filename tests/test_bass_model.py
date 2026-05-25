"""Tests for core.bass_model."""

import numpy as np
import pandas as pd
import pytest

from core.bass_model import (
    bass_cumulative_adoption,
    fit_bass_to_tarpeyo,
    ultomiris_cumulative_adoption,
)


def test_bass_starts_at_zero():
    """F(t=0) = 0 by construction."""
    assert bass_cumulative_adoption(np.array([0.0]), 0.02, 0.5, 10_000)[0] == pytest.approx(0.0, abs=1e-9)


def test_bass_monotonic_increasing():
    """Cumulative adoption monotonically increases in t."""
    t = np.linspace(0.1, 10, 50)
    cum = bass_cumulative_adoption(t, 0.02, 0.5, 10_000)
    assert np.all(np.diff(cum) > 0)


def test_bass_asymptotes_to_M():
    """Cumulative adoption -> M as t -> infinity."""
    cum_far = bass_cumulative_adoption(np.array([100.0]), 0.02, 0.5, 10_000)[0]
    assert cum_far == pytest.approx(10_000, rel=1e-3)


def test_fit_converges_on_synthetic_data():
    """Synthetic data generated from known (p, q, M) recovers (p, q) within tolerance."""
    p_true, q_true, M = 0.025, 0.6, 27_000
    t = np.arange(14) / 4
    cum_true = bass_cumulative_adoption(t, p_true, q_true, M)
    adds = np.diff(np.concatenate(([0.0], cum_true)))
    df = pd.DataFrame({"quarter_index": np.arange(14), "estimated_patients": adds})
    p_fit, q_fit = fit_bass_to_tarpeyo(df, M)
    assert p_fit == pytest.approx(p_true, abs=0.005)
    assert q_fit == pytest.approx(q_true, abs=0.05)


def test_fit_falls_back_at_bounds():
    """Bound-edge convergence triggers fallback to default (p, q)."""
    # Synthesize data from q=2.5 (above the [0.05, 2.0] q upper bound); fit clamps to edge.
    t = np.arange(14) / 4
    cum = bass_cumulative_adoption(t, 0.04, 2.5, 1_000)
    adds = np.diff(np.concatenate(([0.0], cum)))
    df = pd.DataFrame({"quarter_index": np.arange(14), "estimated_patients": adds})
    p_fit, q_fit = fit_bass_to_tarpeyo(df, 1_000)
    assert (p_fit, q_fit) == (0.012, 0.42)


def test_ultomiris_helper_applies_p_adjustment():
    """ultomiris_cumulative_adoption == Bass with p multiplied by p_adjustment, q unchanged."""
    t = np.array([2.0])
    direct = bass_cumulative_adoption(t, 0.02 * 0.7, 0.5, 10_000)[0]
    via_helper = ultomiris_cumulative_adoption(t, 0.02, 0.5, 10_000, p_adjustment=0.7)[0]
    assert via_helper == pytest.approx(direct, rel=1e-9)
