"""Tests for core.conjoint."""

import pytest

from core.conjoint import (
    compute_drug_utilities,
    get_active_drugs_for_year,
    utilities_to_shares,
)
from data.assumptions import DEFAULTS
from data.competitive_landscape import COMPETITOR_LAUNCH_YEARS, DRUG_ATTRIBUTES


def test_utilities_are_weighted_sums():
    """utility(d) = sum of (weight x score) over attributes."""
    weights = DEFAULTS["conjoint"]["attribute_weights"]
    utils = compute_drug_utilities(DRUG_ATTRIBUTES, weights)
    expected = sum(weights[a] * s for a, s in DRUG_ATTRIBUTES["ultomiris"].items())
    assert utils["ultomiris"] == pytest.approx(expected)


def test_bad_weights_raise():
    """compute_drug_utilities raises when weights don't sum to 1.0."""
    bad_weights = {"proteinuria_efficacy": 0.5, "egfr_preservation": 0.4}  # sums to 0.9
    drugs = {"x": {"proteinuria_efficacy": 5, "egfr_preservation": 6}}
    with pytest.raises(ValueError):
        compute_drug_utilities(drugs, bad_weights)


def test_shares_sum_to_one_for_active_drugs():
    """Softmax over active drugs sums to 1.0."""
    utils = {"a": 5.0, "b": 6.0, "c": 7.0}
    shares = utilities_to_shares(utils, logit_lambda=0.5, active_drugs=["a", "b"])
    assert shares["a"] + shares["b"] == pytest.approx(1.0)


def test_inactive_drugs_get_zero_share():
    """Drugs not in active_drugs have share 0."""
    utils = {"a": 5.0, "b": 6.0, "c": 7.0}
    shares = utilities_to_shares(utils, logit_lambda=0.5, active_drugs=["a", "b"])
    assert shares["c"] == 0.0


def test_shares_sum_to_one_when_active_drugs_omitted():
    """When active_drugs is None, all drugs included; shares sum to 1.0."""
    utils = {"a": 5.0, "b": 6.0, "c": 7.0}
    shares = utilities_to_shares(utils, logit_lambda=0.5)
    assert sum(shares.values()) == pytest.approx(1.0)


def test_higher_utility_gets_higher_share():
    """Softmax is monotonic: higher utility -> higher share at same lambda."""
    utils = {"low": 4.0, "high": 7.0}
    shares = utilities_to_shares(utils, logit_lambda=0.5)
    assert shares["high"] > shares["low"]


def test_get_active_drugs_filters_by_launch_year():
    """get_active_drugs_for_year includes only drugs launched as of `year`."""
    active_2026 = set(get_active_drugs_for_year(2026, COMPETITOR_LAUNCH_YEARS))
    expected = {d for d, ly in COMPETITOR_LAUNCH_YEARS.items() if ly <= 2026}
    assert active_2026 == expected
    assert "ultomiris" not in active_2026  # ultomiris launches 2027
