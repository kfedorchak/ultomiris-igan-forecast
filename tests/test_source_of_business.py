"""Tests for core.source_of_business."""

import numpy as np
import pytest

from core.source_of_business import (
    EARLY_MIX,
    MATURE_MIX,
    TRANSITION_YEARS,
    source_of_business_by_year,
)


@pytest.mark.parametrize("years_since_launch", list(range(0, 11)))
def test_mix_sums_to_one_at_every_year_offset(years_since_launch):
    """Mix sums to 1.0 (within rtol=1e-3) for years_since_launch in [0, 10]."""
    mix = source_of_business_by_year(years_since_launch)
    assert np.isclose(sum(mix.values()), 1.0, rtol=1e-3)


def test_year_0_matches_early_mix():
    """At years_since_launch=0, output equals (normalized) EARLY_MIX."""
    mix = source_of_business_by_year(0)
    total = sum(EARLY_MIX.values())
    for k, v in EARLY_MIX.items():
        assert mix[k] == pytest.approx(v / total)


def test_year_transition_matches_mature_mix():
    """At years_since_launch=TRANSITION_YEARS, output equals (normalized) MATURE_MIX."""
    mix = source_of_business_by_year(TRANSITION_YEARS)
    total = sum(MATURE_MIX.values())
    for k, v in MATURE_MIX.items():
        assert mix[k] == pytest.approx(v / total)


def test_post_transition_clamps_to_mature():
    """Years beyond TRANSITION_YEARS stay at MATURE_MIX (clamped, not extrapolated)."""
    mix_t = source_of_business_by_year(TRANSITION_YEARS)
    mix_t2 = source_of_business_by_year(TRANSITION_YEARS + 5)
    for k in EARLY_MIX:
        assert mix_t[k] == pytest.approx(mix_t2[k])


def test_smoothness_no_year_over_year_jumps_above_0_05():
    """Year-over-year change in any bucket stays <= 0.05 — eliminates the discrete-regime cliff."""
    prev = None
    for ysl in range(0, 12):
        mix = source_of_business_by_year(ysl)
        if prev is not None:
            for k in mix:
                jump = abs(mix[k] - prev[k])
                assert jump <= 0.05, f"jump in {k} between ysl={ysl - 1} and {ysl}: {jump:.4f}"
        prev = mix


def test_treatment_naive_decreases_monotonically():
    """treatment_naive is non-increasing from year 0 to TRANSITION_YEARS+."""
    vals = [source_of_business_by_year(ysl)["treatment_naive"] for ysl in range(0, 11)]
    assert vals == sorted(vals, reverse=True)


def test_all_five_mechanism_buckets_present():
    """Every output mix has the four mechanism switch buckets + treatment_naive. Addon removed in v2."""
    expected_keys = {
        "treatment_naive",
        "switch_from_corticosteroid",
        "switch_from_endothelin",
        "switch_from_oral_complement",
        "switch_from_april_baff",
    }
    for ysl in (0, 4, 8, 12):
        assert set(source_of_business_by_year(ysl).keys()) == expected_keys


def test_module_constants_sum_to_one():
    """EARLY_MIX and MATURE_MIX each sum to 1.0 as defined."""
    assert sum(EARLY_MIX.values()) == pytest.approx(1.0)
    assert sum(MATURE_MIX.values()) == pytest.approx(1.0)


def test_negative_years_clamped_to_early_mix():
    """Pre-launch (negative) years_since_launch defensively clamp to EARLY_MIX."""
    mix = source_of_business_by_year(-3)
    total = sum(EARLY_MIX.values())
    for k, v in EARLY_MIX.items():
        assert mix[k] == pytest.approx(v / total)
