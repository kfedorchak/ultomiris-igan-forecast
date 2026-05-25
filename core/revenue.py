"""Stock-and-flow revenue: Bass over class-wide market, share allocation, persistence cohorts, multi-scenario composition."""

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.bass_model import bass_cumulative_adoption, fit_bass_to_tarpeyo
from core.conjoint import (
    compute_drug_utilities,
    get_active_drugs_for_year,
    get_drug_attributes_for_year,
    utilities_to_shares,
)
from core.patient_flow import compute_patient_pool
from data.assumptions import DRUG_VETERAN_COHORTS_2027
from data.competitive_landscape import COMPETITOR_LAUNCH_YEARS, DRUG_ATTRIBUTES

logger = logging.getLogger(__name__)


@dataclass
class YearlyRevenue:
    """Revenue snapshot for a single forecast year across all eGFR scenarios."""

    year: int
    treated_patients_by_scenario: dict[str, float]
    revenues_by_scenario: dict[str, float]
    expected_value_revenue: float


def compute_class_new_starts_per_year(
    forecast_years: list[int],
    params: dict,
    p_fit: float,
    q_fit: float,
) -> dict[int, float]:
    """Annual class-wide new starts (sum across all targeted IgAN therapies), no share allocation.

    Bass models class-wide adoption against stable total_M = pool.high_risk x
    market_potential_fraction. Pre-launch years return 0. Logs a warning if
    year-over-year delta turns negative (would imply M(t) decreased).
    """
    launch_year = params["launch"]["us_launch_year"]
    forecast_start_year = params["launch"]["forecast_start_year"]
    p_adjusted = p_fit * params["bass"]["p_ultomiris_adjustment"]

    new_starts: dict[int, float] = {}
    prior_cumulative_total: float = 0.0

    for year in forecast_years:
        if year < launch_year:
            new_starts[year] = 0.0
            continue

        years_since_launch = year - launch_year
        pool = compute_patient_pool(
            year,
            forecast_start_year,
            params["epi"],
            params["diagnostic_expansion"]["annual_growth_rate"],
        )
        total_M = pool.high_risk * params["bass"]["market_potential_fraction"]

        cumulative_total = float(
            bass_cumulative_adoption(
                np.array([years_since_launch + 1.0]),
                p_adjusted,
                q_fit,
                total_M,
            )[0]
        )

        total_new = cumulative_total - prior_cumulative_total
        if total_new < 0:
            logger.warning(
                "Year %d: class-wide new starts negative (%.1f); "
                "pool may be shrinking or M(t) decreased. Investigate if persistent.",
                year,
                total_new,
            )

        new_starts[year] = total_new
        prior_cumulative_total = cumulative_total

    return new_starts


def compute_new_starts_per_year(
    forecast_years: list[int],
    scenario_name: str,
    params: dict,
    p_fit: float,
    q_fit: float,
    competitor_launch_years: dict[str, int] | None = None,
    drug_attributes: dict[str, dict[str, float]] | None = None,
) -> dict[str, dict[int, float]]:
    """Annual per-drug new starts under one eGFR scenario.

    Class-wide new starts (from compute_class_new_starts_per_year) are allocated
    to drugs via time-varying conjoint shares. From egfr_readout_year onward,
    Ultomiris's share is multiplied by the scenario's share_multiplier and ALL
    active drug shares are renormalized to sum to 1.0 (zero-sum: competitor
    shares decrease when Ultomiris boosted, increase when suppressed).
    Returns {drug: {year: new starts}}.
    """
    if competitor_launch_years is None:
        competitor_launch_years = COMPETITOR_LAUNCH_YEARS
    if drug_attributes is None:
        drug_attributes = DRUG_ATTRIBUTES

    launch_year = params["launch"]["us_launch_year"]
    egfr_readout_year = params["launch"]["egfr_readout_year"]
    scenario = params["egfr_readout_scenarios"][scenario_name]
    multiplier = scenario["share_multiplier"]
    weights = params["conjoint"]["attribute_weights"]
    logit = params["conjoint"]["logit_lambda"]

    class_new = compute_class_new_starts_per_year(forecast_years, params, p_fit, q_fit)

    drug_new_starts: dict[str, dict[int, float]] = {d: {} for d in competitor_launch_years}
    for year in forecast_years:
        if year < launch_year:
            for d in competitor_launch_years:
                drug_new_starts[d][year] = 0.0
            continue

        year_attrs = get_drug_attributes_for_year(year, drug_attributes, competitor_launch_years)
        utilities = compute_drug_utilities(year_attrs, weights)
        active = get_active_drugs_for_year(year, competitor_launch_years)
        shares = utilities_to_shares(utilities, logit, active)

        if year >= egfr_readout_year and "ultomiris" in active and multiplier != 1.0:
            ultomiris_raw = shares["ultomiris"]
            renorm = 1.0 + ultomiris_raw * (multiplier - 1.0)
            shares = {
                d: (s * multiplier if d == "ultomiris" else s) / renorm
                for d, s in shares.items()
            }

        for drug in competitor_launch_years:
            drug_new_starts[drug][year] = class_new.get(year, 0.0) * shares.get(drug, 0.0)

    return drug_new_starts


def compute_per_drug_treated_stocks(
    forecast_years: list[int],
    scenario_name: str,
    params: dict,
    p_fit: float,
    q_fit: float,
    competitor_launch_years: dict[str, int] | None = None,
    drug_attributes: dict[str, dict[str, float]] | None = None,
    drug_veteran_cohorts: dict[str, float] | None = None,
) -> dict[str, dict[int, float]]:
    """Per-drug active treated stock per year under one eGFR scenario.

    Builds on compute_new_starts_per_year, applying persistence cohorts and
    seeding veterans from DRUG_VETERAN_COHORTS_2027 at forecast_start_year so
    the pre-launch (e.g. 2026) column reflects the actual end-of-2026
    / start-of-Ultomiris-launch snapshot.
    Returns {drug: {year: active stock}}.
    """
    if competitor_launch_years is None:
        competitor_launch_years = COMPETITOR_LAUNCH_YEARS
    if drug_attributes is None:
        drug_attributes = DRUG_ATTRIBUTES
    if drug_veteran_cohorts is None:
        drug_veteran_cohorts = DRUG_VETERAN_COHORTS_2027

    drug_new_starts = compute_new_starts_per_year(
        forecast_years,
        scenario_name,
        params,
        p_fit,
        q_fit,
        competitor_launch_years,
        drug_attributes,
    )
    forecast_start = params["launch"]["forecast_start_year"]
    persistence_y1 = params["persistence"]["year_1_persistence"]
    persistence_y2plus = params["persistence"]["year_2plus_persistence"]

    drug_stocks: dict[str, dict[int, float]] = {}
    for drug, starts in drug_new_starts.items():
        veteran = drug_veteran_cohorts.get(drug, 0.0)
        veteran_arg = (forecast_start, veteran) if veteran > 0 else None
        drug_stocks[drug] = compute_treated_stock(
            forecast_years, starts, persistence_y1, persistence_y2plus, veteran_arg
        )
    return drug_stocks


def compute_treated_stock(
    forecast_years: list[int],
    new_starts: dict[int, float],
    persistence_y1: float,
    persistence_y2plus: float,
    veteran_cohort: tuple[int, float] | None = None,
) -> dict[int, float]:
    """Discrete cohort-based stock. Year Y cohort: full count at Y, x persistence_y1 at Y+1, x persistence_y2plus thereafter.

    `veteran_cohort = (year, value)` optionally seeds a single cohort of patients
    already on therapy at `year` (e.g. pre-launch carryover stock). They decay at
    persistence_y2plus every year after `year` — they're already past Y1.
    """
    cohorts: dict[int, float] = {}
    annual_stock: dict[int, float] = {}
    veteran_year, veteran_value = (None, 0.0)
    if veteran_cohort is not None:
        veteran_year, veteran_value = veteran_cohort

    for year in forecast_years:
        for start_year in list(cohorts.keys()):
            years_since_start = year - start_year
            if years_since_start == 1:
                cohorts[start_year] *= persistence_y1
            elif years_since_start >= 2:
                cohorts[start_year] *= persistence_y2plus

        if veteran_year is not None and year > veteran_year:
            veteran_value *= persistence_y2plus

        cohorts[year] = new_starts.get(year, 0.0)
        veteran_contrib = veteran_value if (veteran_year is not None and year >= veteran_year) else 0.0
        annual_stock[year] = sum(cohorts.values()) + veteran_contrib

    return annual_stock


def compute_yearly_revenue(
    year: int,
    treated_stock_by_scenario: dict[str, dict[int, float]],
    params: dict,
) -> YearlyRevenue:
    """Compose YearlyRevenue from per-scenario stock streams; applies pricing growth and uniform PoA."""
    launch_year = params["launch"]["us_launch_year"]
    scenarios = params["egfr_readout_scenarios"]

    if year < launch_year:
        return YearlyRevenue(
            year=year,
            treated_patients_by_scenario={s: 0.0 for s in scenarios},
            revenues_by_scenario={s: 0.0 for s in scenarios},
            expected_value_revenue=0.0,
        )

    years_since_launch = year - launch_year
    price = (
        params["pricing"]["net_price_per_patient_year"]
        * (1 + params["pricing"]["annual_price_growth"]) ** years_since_launch
    )
    poa = params["probability_of_approval"]

    treated: dict[str, float] = {}
    revenues: dict[str, float] = {}
    expected_value = 0.0
    for scenario_name, scenario in scenarios.items():
        stock = treated_stock_by_scenario[scenario_name].get(year, 0.0)
        rev = stock * price * poa
        treated[scenario_name] = stock
        revenues[scenario_name] = rev
        expected_value += scenario["probability"] * rev

    return YearlyRevenue(
        year=year,
        treated_patients_by_scenario=treated,
        revenues_by_scenario=revenues,
        expected_value_revenue=expected_value,
    )


def run_forecast(
    params: dict,
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
    competitor_launch_years: dict[str, int] | None = None,
    drug_attributes: dict[str, dict[str, float]] | None = None,
) -> dict[int, YearlyRevenue]:
    """End-to-end forecast orchestrator: Bass fit -> per-scenario new starts -> treated stocks -> yearly revenue."""
    if competitor_launch_years is None:
        competitor_launch_years = COMPETITOR_LAUNCH_YEARS
    if drug_attributes is None:
        drug_attributes = DRUG_ATTRIBUTES

    p_fit, q_fit = fit_bass_to_tarpeyo(
        tarpeyo_df,
        tarpeyo_market_potential,
        fallback_p=params["bass"]["innovation_p_default"],
        fallback_q=params["bass"]["imitation_q_default"],
    )

    forecast_start = params["launch"]["forecast_start_year"]
    horizon = params["launch"]["forecast_horizon_years"]
    forecast_years = list(range(forecast_start, forecast_start + horizon))

    persistence_y1 = params["persistence"]["year_1_persistence"]
    persistence_y2plus = params["persistence"]["year_2plus_persistence"]

    treated_stock_by_scenario: dict[str, dict[int, float]] = {}
    for scenario_name in params["egfr_readout_scenarios"]:
        drug_stocks = compute_per_drug_treated_stocks(
            forecast_years,
            scenario_name,
            params,
            p_fit,
            q_fit,
            competitor_launch_years,
            drug_attributes,
        )
        treated_stock_by_scenario[scenario_name] = drug_stocks["ultomiris"]

    return {
        year: compute_yearly_revenue(year, treated_stock_by_scenario, params)
        for year in forecast_years
    }
