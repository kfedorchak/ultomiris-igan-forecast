"""Tests for core.revenue."""

import pandas as pd
import pytest

from core.bass_model import fit_bass_to_tarpeyo
from core.revenue import (
    YearlyRevenue,
    compute_new_starts_per_year,
    compute_treated_stock,
    compute_yearly_revenue,
    run_forecast,
)
from data.assumptions import DEFAULTS, TARPEYO_MARKET_POTENTIAL_2022


@pytest.fixture
def tarpeyo_df():
    return pd.read_csv("data/tarpeyo_trajectory.csv")


@pytest.fixture
def bass_fit(tarpeyo_df):
    return fit_bass_to_tarpeyo(tarpeyo_df, TARPEYO_MARKET_POTENTIAL_2022)


@pytest.fixture
def forecast_years():
    start = DEFAULTS["launch"]["forecast_start_year"]
    horizon = DEFAULTS["launch"]["forecast_horizon_years"]
    return list(range(start, start + horizon))


@pytest.fixture
def forecast(tarpeyo_df):
    return run_forecast(DEFAULTS, tarpeyo_df, TARPEYO_MARKET_POTENTIAL_2022)


def test_pre_launch_returns_zero_revenue(forecast):
    """2026 (pre-launch=2027) has $0 revenue across every scenario and EV."""
    yr = forecast[2026]
    assert yr.expected_value_revenue == 0.0
    assert all(v == 0.0 for v in yr.revenues_by_scenario.values())


def test_new_starts_positive_in_every_post_launch_year(bass_fit, forecast_years):
    """Risk #2 regression: class-wide Bass with stable total_M never yields negative Ultomiris new starts."""
    p_fit, q_fit = bass_fit
    drug_new_starts = compute_new_starts_per_year(
        forecast_years, "modestly_positive", DEFAULTS, p_fit, q_fit
    )
    launch_year = DEFAULTS["launch"]["us_launch_year"]
    for year in forecast_years:
        if year >= launch_year:
            ult = drug_new_starts["ultomiris"][year]
            assert ult > 0, f"non-positive ultomiris new_starts in {year}: {ult}"


def test_first_year_cohort_not_aged():
    """A cohort started in year Y is at full count in year Y (aging applies from Y+1)."""
    new_starts = {2027: 100.0, 2028: 0.0}
    stock = compute_treated_stock([2027, 2028], new_starts, 0.75, 0.85)
    assert stock[2027] == 100.0


def test_cohort_ages_with_y1_then_y2plus():
    """Year Y+1 applies persistence_y1; Y+2 and beyond apply persistence_y2plus each year."""
    new_starts = {2027: 100.0, 2028: 0.0, 2029: 0.0, 2030: 0.0}
    stock = compute_treated_stock([2027, 2028, 2029, 2030], new_starts, 0.75, 0.85)
    assert stock[2028] == pytest.approx(75.0)
    assert stock[2029] == pytest.approx(75.0 * 0.85)
    assert stock[2030] == pytest.approx(75.0 * 0.85 * 0.85)


def test_expected_value_is_probability_weighted(forecast):
    """EV = sum(scenario_prob x scenario_revenue) at every post-launch year."""
    yr = forecast[2032]
    expected = sum(
        DEFAULTS["egfr_readout_scenarios"][s]["probability"] * yr.revenues_by_scenario[s]
        for s in DEFAULTS["egfr_readout_scenarios"]
    )
    assert yr.expected_value_revenue == pytest.approx(expected)


def test_pre_signal_year_no_scenario_impact(bass_fit, forecast_years):
    """In 2026 (pre-signal), all eGFR scenarios produce identical Ultomiris new starts (helper returns 1.0)."""
    from core.revenue import get_scenario_multiplier

    p_fit, q_fit = bass_fit
    launch = DEFAULTS["launch"]
    year_pre = launch["egfr_signal_year"] - 1

    for s_name, scenario in DEFAULTS["egfr_readout_scenarios"].items():
        assert get_scenario_multiplier(year_pre, scenario, launch) == 1.0

    ult_new = {
        s: compute_new_starts_per_year(forecast_years, s, DEFAULTS, p_fit, q_fit)["ultomiris"][year_pre]
        for s in DEFAULTS["egfr_readout_scenarios"]
    }
    vals = list(ult_new.values())
    assert all(v == pytest.approx(vals[0]) for v in vals)


def test_signal_year_partial_impact(bass_fit, forecast_years):
    """At signal year (2027), Ultomiris share-of-new-starts diff (strong − weak) ≈ 50% of the readout year diff."""
    from core.revenue import compute_class_new_starts_per_year

    p_fit, q_fit = bass_fit
    class_new = compute_class_new_starts_per_year(forecast_years, DEFAULTS, p_fit, q_fit)
    strong = compute_new_starts_per_year(forecast_years, "strongly_positive", DEFAULTS, p_fit, q_fit)["ultomiris"]
    weak = compute_new_starts_per_year(forecast_years, "weak_neutral", DEFAULTS, p_fit, q_fit)["ultomiris"]

    signal_year = DEFAULTS["launch"]["egfr_signal_year"]
    readout_year = DEFAULTS["launch"]["egfr_readout_year"]

    diff_signal_share = (strong[signal_year] - weak[signal_year]) / class_new[signal_year]
    diff_readout_share = (strong[readout_year] - weak[readout_year]) / class_new[readout_year]

    assert diff_signal_share > 0
    assert diff_readout_share > 0
    ratio = diff_signal_share / diff_readout_share
    assert 0.40 < ratio < 0.60, f"signal/readout share-diff ratio: {ratio:.3f} (expected ~0.5)"


def test_readout_year_full_impact(bass_fit, forecast_years):
    """From readout year (2028) onward, Ultomiris new starts strictly ordered strong > modest > weak."""
    p_fit, q_fit = bass_fit
    strong = compute_new_starts_per_year(forecast_years, "strongly_positive", DEFAULTS, p_fit, q_fit)["ultomiris"]
    modest = compute_new_starts_per_year(forecast_years, "modestly_positive", DEFAULTS, p_fit, q_fit)["ultomiris"]
    weak = compute_new_starts_per_year(forecast_years, "weak_neutral", DEFAULTS, p_fit, q_fit)["ultomiris"]

    readout_year = DEFAULTS["launch"]["egfr_readout_year"]
    for year in [y for y in forecast_years if y >= readout_year]:
        assert strong[year] > modest[year], f"{year}: strong {strong[year]:.1f} <= modest {modest[year]:.1f}"
        assert modest[year] > weak[year], f"{year}: modest {modest[year]:.1f} <= weak {weak[year]:.1f}"


def test_scenarios_diverge_after_readout_year(forecast):
    """At year 2032 (post-readout), strongly_positive > modestly_positive > weak_neutral."""
    yr = forecast[2032]
    assert (
        yr.revenues_by_scenario["strongly_positive"]
        > yr.revenues_by_scenario["modestly_positive"]
        > yr.revenues_by_scenario["weak_neutral"]
    )


def test_peak_revenue_in_sanity_band(forecast):
    """Gate #5: peak EV revenue lands in $400M-$1.0B at default params."""
    peak_ev = max(yr.expected_value_revenue for yr in forecast.values())
    assert 400_000_000 <= peak_ev <= 1_000_000_000, f"peak EV revenue: ${peak_ev/1e6:.0f}M"
