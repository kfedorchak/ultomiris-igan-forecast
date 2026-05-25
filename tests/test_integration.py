"""End-to-end integration tests for the forecast."""

import math

import pandas as pd
import pytest

from core.bass_model import fit_bass_to_tarpeyo
from core.revenue import YearlyRevenue, run_forecast
from data.assumptions import DEFAULTS, TARPEYO_MARKET_POTENTIAL_2022


@pytest.fixture
def tarpeyo_df():
    return pd.read_csv("data/tarpeyo_trajectory.csv")


@pytest.fixture
def forecast(tarpeyo_df):
    return run_forecast(DEFAULTS, tarpeyo_df, TARPEYO_MARKET_POTENTIAL_2022)


def test_forecast_covers_full_horizon(forecast):
    """Forecast spans forecast_start_year through forecast_start + horizon - 1."""
    start = DEFAULTS["launch"]["forecast_start_year"]
    horizon = DEFAULTS["launch"]["forecast_horizon_years"]
    assert set(forecast.keys()) == set(range(start, start + horizon))


def test_every_year_is_yearly_revenue_with_all_fields(forecast):
    """Each forecast value is a populated YearlyRevenue with all required fields."""
    scenario_keys = set(DEFAULTS["egfr_readout_scenarios"].keys())
    for year, yr in forecast.items():
        assert isinstance(yr, YearlyRevenue)
        assert yr.year == year
        assert set(yr.treated_patients_by_scenario.keys()) == scenario_keys
        assert set(yr.revenues_by_scenario.keys()) == scenario_keys
        assert isinstance(yr.expected_value_revenue, float)


def test_no_nan_or_negative_outputs(forecast):
    """No NaN, no negative revenues or patient counts in any year/scenario."""
    for yr in forecast.values():
        assert not math.isnan(yr.expected_value_revenue)
        assert yr.expected_value_revenue >= 0
        for rev in yr.revenues_by_scenario.values():
            assert not math.isnan(rev)
            assert rev >= 0
        for treat in yr.treated_patients_by_scenario.values():
            assert not math.isnan(treat)
            assert treat >= 0


def test_ev_between_weak_and_strong_post_readout(forecast):
    """At every post-readout year, weak <= EV <= strong (probability weighting)."""
    readout = DEFAULTS["launch"]["egfr_readout_year"]
    for year, yr in forecast.items():
        if year >= readout:
            weak = yr.revenues_by_scenario["weak_neutral"]
            strong = yr.revenues_by_scenario["strongly_positive"]
            assert weak <= yr.expected_value_revenue <= strong


def test_treated_stock_has_ramp_peak_decline_pattern(forecast):
    """Treated stock ramps from year 1, peaks mid-horizon, declines as persistence haircuts dominate Bass."""
    launch = DEFAULTS["launch"]["us_launch_year"]
    stocks_post = [
        forecast[y].treated_patients_by_scenario["modestly_positive"]
        for y in sorted(forecast.keys())
        if y >= launch
    ]
    peak = max(stocks_post)
    assert stocks_post[0] < peak, "stock should ramp from year 1"
    assert stocks_post[-1] < peak, "stock should decline from peak before horizon end"


def test_lower_price_lowers_peak_revenue(tarpeyo_df, forecast):
    """End-to-end smoke: dropping net_price slider lowers peak revenue."""
    cheaper = {**DEFAULTS, "pricing": {**DEFAULTS["pricing"], "net_price_per_patient_year": 300_000}}
    fc_cheap = run_forecast(cheaper, tarpeyo_df, TARPEYO_MARKET_POTENTIAL_2022)
    peak_base = max(r.expected_value_revenue for r in forecast.values())
    peak_cheap = max(r.expected_value_revenue for r in fc_cheap.values())
    assert peak_cheap < peak_base


def test_default_tarpeyo_data_fits_without_fallback(tarpeyo_df):
    """Placeholder Tarpeyo CSV fits cleanly within Bass bounds (Gate #8: fit tracks data)."""
    p, q = fit_bass_to_tarpeyo(tarpeyo_df, TARPEYO_MARKET_POTENTIAL_2022)
    fallback = (DEFAULTS["bass"]["innovation_p_default"], DEFAULTS["bass"]["imitation_q_default"])
    assert (p, q) != fallback


def test_tarpeyo_share_of_treated_exceeds_share_of_new_starts_at_2032(tarpeyo_df):
    """First-mover advantage: Tarpeyo's accumulated stock gives it more share-of-treated than share-of-new-starts."""
    from core.conjoint import (
        compute_drug_utilities,
        get_active_drugs_for_year,
        get_drug_attributes_for_year,
        utilities_to_shares,
    )
    from core.revenue import compute_per_drug_treated_stocks
    from data.competitive_landscape import COMPETITOR_LAUNCH_YEARS, DRUG_ATTRIBUTES

    p_fit, q_fit = fit_bass_to_tarpeyo(tarpeyo_df, TARPEYO_MARKET_POTENTIAL_2022)
    fs = DEFAULTS["launch"]["forecast_start_year"]
    forecast_years = list(range(fs, fs + DEFAULTS["launch"]["forecast_horizon_years"]))

    drug_stocks = compute_per_drug_treated_stocks(forecast_years, DEFAULTS, p_fit, q_fit)
    total_2032 = sum(drug_stocks[d][2032] for d in drug_stocks)
    tarpeyo_share_of_treated = drug_stocks["tarpeyo"][2032] / total_2032

    year_attrs = get_drug_attributes_for_year(2032, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS)
    utilities = compute_drug_utilities(year_attrs, DEFAULTS["conjoint"]["attribute_weights"])
    active = get_active_drugs_for_year(2032, COMPETITOR_LAUNCH_YEARS)
    shares = utilities_to_shares(utilities, DEFAULTS["conjoint"]["logit_lambda"], active)
    tarpeyo_share_of_new_starts = shares["tarpeyo"]

    assert tarpeyo_share_of_treated > tarpeyo_share_of_new_starts, (
        f"first-mover advantage missing: stock share {tarpeyo_share_of_treated:.3f} "
        f"vs new-starts share {tarpeyo_share_of_new_starts:.3f}"
    )
