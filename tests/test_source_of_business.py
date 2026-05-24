"""Tests for core.source_of_business."""

import numpy as np
import pytest

from core.source_of_business import (
    YEAR_1_2_MIX,
    YEAR_6PLUS_MIX,
    source_of_business_by_year,
)
from data.assumptions import DEFAULTS


@pytest.mark.parametrize("years_since_launch", list(range(0, 11)))
def test_mix_sums_to_one_at_every_year_offset(years_since_launch):
    """Mix sums to 1.0 (within rtol=1e-3) for years_since_launch in [0, 10]."""
    mix = source_of_business_by_year(years_since_launch, DEFAULTS["source_of_business"])
    assert np.isclose(sum(mix.values()), 1.0, rtol=1e-3)


def test_year_1_2_is_naive_heavy():
    """At years_since_launch=0, treatment_naive is the largest bucket."""
    mix = source_of_business_by_year(0, DEFAULTS["source_of_business"])
    assert mix["treatment_naive"] == max(mix.values())


def test_year_3_5_uses_base_mix():
    """At years_since_launch=4, output equals (normalized) base_mix."""
    base = DEFAULTS["source_of_business"]
    mix = source_of_business_by_year(4, base)
    total = sum(base.values())
    for k in base:
        assert mix[k] == pytest.approx(base[k] / total)


def test_year_6plus_shifts_toward_switching():
    """At years_since_launch=6, naive share drops and total switching share rises."""
    base = DEFAULTS["source_of_business"]
    mix_y4 = source_of_business_by_year(4, base)
    mix_y6 = source_of_business_by_year(6, base)
    assert mix_y6["treatment_naive"] < mix_y4["treatment_naive"]
    switch_y4 = sum(v for k, v in mix_y4.items() if k.startswith("switch_from_"))
    switch_y6 = sum(v for k, v in mix_y6.items() if k.startswith("switch_from_"))
    assert switch_y6 > switch_y4


def test_all_six_mechanism_buckets_present():
    """Every output mix has the four mechanism switch buckets + naive + addon."""
    expected_keys = {
        "treatment_naive",
        "switch_from_corticosteroid",
        "switch_from_endothelin",
        "switch_from_oral_complement",
        "switch_from_april_baff",
        "addon_to_existing",
    }
    for ysl in (0, 4, 10):
        mix = source_of_business_by_year(ysl, DEFAULTS["source_of_business"])
        assert set(mix.keys()) == expected_keys


def test_defensive_normalization_corrects_drift():
    """A base_mix that sums to 0.99 still produces a normalized output."""
    drift_mix = {
        "treatment_naive": 0.54,
        "switch_from_corticosteroid": 0.08,
        "switch_from_endothelin": 0.07,
        "switch_from_oral_complement": 0.03,
        "switch_from_april_baff": 0.10,
        "addon_to_existing": 0.17,
    }
    # drift_mix sums to 0.99
    mix = source_of_business_by_year(4, drift_mix)
    assert sum(mix.values()) == pytest.approx(1.0)


def test_module_constants_internally_consistent():
    """YEAR_1_2_MIX and YEAR_6PLUS_MIX both sum to 1.0 as defined."""
    assert sum(YEAR_1_2_MIX.values()) == pytest.approx(1.0)
    assert sum(YEAR_6PLUS_MIX.values()) == pytest.approx(1.0)
