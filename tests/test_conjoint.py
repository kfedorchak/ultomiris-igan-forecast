"""Tests for core.conjoint."""

import pytest

from core.conjoint import (
    compute_drug_utilities,
    get_active_drugs_for_year,
    get_drug_attributes_for_year,
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


def test_attribute_maturation_lifts_ultomiris_mechanism_familiarity():
    """Ultomiris mechanism_familiarity is materially higher in 2034 (ysl=7) than 2027 (ysl=0)."""
    attrs_2027 = get_drug_attributes_for_year(2027, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS)
    attrs_2034 = get_drug_attributes_for_year(2034, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS)
    mf_2027 = attrs_2027["ultomiris"]["mechanism_familiarity"]
    mf_2034 = attrs_2034["ultomiris"]["mechanism_familiarity"]
    assert mf_2027 == DRUG_ATTRIBUTES["ultomiris"]["mechanism_familiarity"]  # ysl=0, no boost
    assert mf_2034 - mf_2027 >= 1.0, f"expected >=1.0 boost by 2034; got {mf_2034 - mf_2027:.2f}"


def test_attribute_maturation_caps_at_10():
    """Score saturation: a drug already near 10 doesn't exceed 10 with maturation."""
    base = {"x": {"mechanism_familiarity": 9.5, "safety_burden": 9.0, "payer_access": 9.5}}
    launches = {"x": 2020}
    matured = get_drug_attributes_for_year(2030, base, launches)
    for v in matured["x"].values():
        assert v <= 10.0


def test_non_maturing_attributes_unchanged():
    """Efficacy / route / dosing are fixed by molecular properties — no maturation applied."""
    attrs_2034 = get_drug_attributes_for_year(2034, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS)
    for fixed_attr in ("proteinuria_efficacy", "egfr_preservation", "route_of_admin", "dosing_frequency"):
        assert attrs_2034["ultomiris"][fixed_attr] == DRUG_ATTRIBUTES["ultomiris"][fixed_attr]
