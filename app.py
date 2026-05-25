"""Streamlit entry point for the Ultomiris IgAN forecast prototype."""

import copy
import hashlib
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.bass_model import fit_bass_to_tarpeyo
from core.patient_flow import compute_patient_pool
from core.revenue import (
    compute_class_new_starts_per_year,
    compute_per_drug_treated_stocks,
    compute_treated_stock,
    run_forecast,
)
from core.source_of_business import source_of_business_by_year
from data.assumptions import CLASS_TREATED_AT_ULTOMIRIS_LAUNCH, DEFAULTS, TARPEYO_MARKET_POTENTIAL_2022
from data.competitive_landscape import COMPETITOR_LAUNCH_YEARS, DRUG_ATTRIBUTES
from viz.analog_overlay import build_analog_overlay
from viz.conjoint_table import build_weights_chart, render_conjoint_table
from viz.formatting import fmt_currency, fmt_patients
from viz.funnel import build_funnel_figure
from viz.revenue_chart import build_revenue_chart
from viz.share_chart import build_share_chart
from viz.tornado import build_tornado_chart

st.set_page_config(
    page_title="Ultomiris IgAN Forecast Prototype",
    layout="wide",
)

# Override Streamlit's default green inline-code styling with Alexion blue,
# and force code to inherit the parent font-size so it doesn't render smaller
# inside a caption or other body text.
st.markdown(
    """
    <style>
    code {
        color: #273386 !important;
        background-color: rgba(39, 51, 134, 0.08) !important;
        font-size: 1em !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ──────────────────────────── cached helpers ────────────────────────────

@st.cache_data
def load_tarpeyo() -> pd.DataFrame:
    return pd.read_csv("data/tarpeyo_trajectory.csv")


def _params_hash(params: dict) -> str:
    return hashlib.md5(
        json.dumps(params, sort_keys=True, default=str).encode()
    ).hexdigest()


@st.cache_data
def cached_forecast(params_hash: str, _params: dict, market_potential: float):
    return run_forecast(_params, load_tarpeyo(), market_potential)


@st.cache_data
def cached_tornado(params_hash: str, _params: dict, market_potential: float, scenario: str):
    return build_tornado_chart(_params, load_tarpeyo(), market_potential, scenario=scenario)


@st.cache_data
def cached_per_drug_stocks(params_hash: str, _params: dict, market_potential: float, scenario: str) -> dict[str, dict[int, float]]:
    """Per-drug active treated stocks per year under `scenario`.

    'expected_value' returns probability-weighted stocks across the three eGFR
    scenarios; otherwise returns the per-drug stocks for the named scenario.
    """
    p_fit, q_fit = fit_bass_to_tarpeyo(
        load_tarpeyo(),
        market_potential,
        fallback_p=_params["bass"]["innovation_p_default"],
        fallback_q=_params["bass"]["imitation_q_default"],
    )
    fs = _params["launch"]["forecast_start_year"]
    horizon = _params["launch"]["forecast_horizon_years"]
    years = list(range(fs, fs + horizon))

    if scenario == "expected_value":
        scenarios = _params["egfr_readout_scenarios"]
        per_scenario = {
            s: compute_per_drug_treated_stocks(years, s, _params, p_fit, q_fit)
            for s in scenarios
        }
        any_s = next(iter(scenarios))
        drugs = list(per_scenario[any_s].keys())
        ev: dict[str, dict[int, float]] = {d: {} for d in drugs}
        for d in drugs:
            for y in years:
                ev[d][y] = sum(
                    scenarios[s]["probability"] * per_scenario[s][d][y]
                    for s in scenarios
                )
        return ev

    return compute_per_drug_treated_stocks(years, scenario, _params, p_fit, q_fit)


@st.cache_data
def cached_class_active(params_hash: str, _params: dict, market_potential: float) -> dict[int, float]:
    """Class-wide active treated patients per year (Bass over total_M + persistence cohorts, no share)."""
    p_fit, q_fit = fit_bass_to_tarpeyo(
        load_tarpeyo(),
        market_potential,
        fallback_p=_params["bass"]["innovation_p_default"],
        fallback_q=_params["bass"]["imitation_q_default"],
    )
    fs = _params["launch"]["forecast_start_year"]
    horizon = _params["launch"]["forecast_horizon_years"]
    years = list(range(fs, fs + horizon))
    class_new = compute_class_new_starts_per_year(years, _params, p_fit, q_fit)
    return compute_treated_stock(
        years,
        class_new,
        _params["persistence"]["year_1_persistence"],
        _params["persistence"]["year_2plus_persistence"],
        veteran_cohort=(fs, CLASS_TREATED_AT_ULTOMIRIS_LAUNCH),
    )


def scenario_revenue(yearly, scenario: str) -> float:
    """Per-year revenue under `scenario` ('expected_value' returns EV-weighted)."""
    if scenario == "expected_value":
        return yearly.expected_value_revenue
    return yearly.revenues_by_scenario[scenario]


def scenario_treated(yearly, scenario: str, scenario_probs: dict) -> float:
    """Per-year treated patients under `scenario` (EV = probability-weighted across scenarios)."""
    if scenario == "expected_value":
        return sum(
            sp["probability"] * yearly.treated_patients_by_scenario[s]
            for s, sp in scenario_probs.items()
        )
    return yearly.treated_patients_by_scenario[scenario]


# ──────────────────────────── source-of-business chart (inline) ────────

from viz.formatting import ALEXION_BLUE as _ALEXION_BLUE

# Treatment-naive (most strategically important — net-new class entrants)
# gets brand blue; switch buckets are sequential greys from light to dark.
_SOB_COLORS = {
    "treatment_naive":            _ALEXION_BLUE,
    "switch_from_corticosteroid": "#BFBFBF",
    "switch_from_endothelin":     "#9E9E9E",
    "switch_from_oral_complement": "#7D7D7D",
    "switch_from_april_baff":     "#5C5C5C",
}


def _build_source_of_business_chart(
    forecast_years: list[int],
    params: dict,
    highlighted_bucket: str | None = None,
) -> go.Figure:
    """Stacked bar of Ultomiris new-start sources (descriptive attribution).

    `highlighted_bucket`: when set to one of the SoB keys, the corresponding
    bar segment renders in Alexion blue and every other segment fades to
    light grey. When None, the default palette (treatment_naive in blue,
    switch buckets in sequential greys) is used.
    """
    launch_year = params["launch"]["us_launch_year"]
    post_launch = [y for y in forecast_years if y >= launch_year]
    mixes = {
        y: source_of_business_by_year(y - launch_year)
        for y in post_launch
    }
    fig = go.Figure()
    for source, default_color in _SOB_COLORS.items():
        if highlighted_bucket is None:
            color = default_color
        elif source == highlighted_bucket:
            color = _ALEXION_BLUE
        else:
            color = "#E0E0E0"
        fig.add_trace(
            go.Bar(
                x=post_launch,
                y=[mixes[y].get(source, 0.0) for y in post_launch],
                name=source.replace("_", " ").title(),
                marker_color=color,
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>Year: %{x}<br>"
                    "Share: %{y:.1%}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        barmode="stack",
        title="Sources of New Ultomiris Patients (Descriptive Attribution)",
        xaxis=dict(title="Year", tickmode="linear", dtick=1),
        yaxis=dict(title="Share of new starts", tickformat=".0%", range=[0, 1]),
        template="plotly_white",
        height=440,
        margin=dict(b=110),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            itemclick="toggleothers",     # click a bucket to isolate it
            itemdoubleclick="toggle",     # double-click to restore all
        ),
    )
    return fig


# ──────────────────────────── slider defaults + reset callback ─────────

SLIDER_DEFAULTS: dict[str, float | int] = {
    "high_risk_pct": DEFAULTS["epi"]["high_risk_pct"],
    "market_potential_fraction": DEFAULTS["bass"]["market_potential_fraction"],
    "p_ultomiris_adjustment": DEFAULTS["bass"]["p_ultomiris_adjustment"],
    "year_2plus_persistence": DEFAULTS["persistence"]["year_2plus_persistence"],
    "net_price_k": DEFAULTS["pricing"]["net_price_per_patient_year"] // 1000,
    "diagnostic_expansion": DEFAULTS["diagnostic_expansion"]["annual_growth_rate"],
}


def reset_to_defaults() -> None:
    """Reset every slider's session_state entry back to DEFAULTS."""
    for k, v in SLIDER_DEFAULTS.items():
        st.session_state[k] = v


# Initialize session_state once on first render. Avoids the "value + key" warning
# that fires when Streamlit sees both a value= and a pre-existing session_state entry.
for _k, _v in SLIDER_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ──────────────────────────── header ────────────────────────────────────

st.title("Ultomiris in IgAN — US Patient-Based Revenue Forecast")
st.caption("Prototype for Alexion / AstraZeneca · Director, Commercial Insights & Analytics")


# ──────────────────────────── sidebar ───────────────────────────────────

with st.sidebar:
    st.header("Scenario")
    scenario_options = {
        "expected_value": "Risk-adjusted (default)",
        "strongly_positive": "Strongly positive eGFR (p=40%)",
        "modestly_positive": "Modestly positive eGFR (p=40%)",
        "weak_neutral": "Weak / neutral eGFR (p=20%)",
    }
    selected_scenario = st.radio(
        "Display scenario",
        options=list(scenario_options.keys()),
        format_func=lambda k: scenario_options[k],
        index=0,
    )

    st.divider()
    st.header("Key drivers")

    high_risk_pct = st.slider(
        "% high-risk patients",
        min_value=0.20, max_value=0.60,
        step=0.01, format="%.2f",
        key="high_risk_pct",
    )
    market_potential_fraction = st.slider(
        "Class adoption ceiling",
        min_value=0.30, max_value=0.85,
        step=0.01, format="%.2f",
        key="market_potential_fraction",
    )
    p_ultomiris_adjustment = st.slider(
        "IV/REMS friction (1 = none)",
        min_value=0.30, max_value=1.00,
        step=0.05, format="%.2f",
        key="p_ultomiris_adjustment",
    )
    year_2plus_persistence = st.slider(
        "Annual persistence (Y2+)",
        min_value=0.60, max_value=0.95,
        step=0.01, format="%.2f",
        key="year_2plus_persistence",
    )
    net_price_k = st.slider(
        "Net price ($K / patient-year)",
        min_value=250, max_value=700,
        step=10,
        key="net_price_k",
    )
    diagnostic_expansion = st.slider(
        "Diagnostic expansion (annual)",
        min_value=-0.02, max_value=0.12,
        step=0.01, format="%.2f",
        key="diagnostic_expansion",
    )

    st.button("↺ Reset drivers to defaults", on_click=reset_to_defaults)

    st.divider()
    with st.expander("Methodology"):
        st.markdown(
            """
**Bass diffusion** is calibrated to Tarpeyo's 2022-2025 trajectory; Ultomiris
adoption uses the fitted `(p, q)` with `p × IV/REMS friction` applied to model
slower class-wide ramp.

**Conjoint share** is a softmax over 7 weighted attributes across 8 active
competitors. eGFR readout scenarios phase in: partial impact from **2027**
(signal year — first-cohort wk 106, prescriber anticipation builds) and full
impact from **2028** (LPLV-based topline analysis) onward.

**Stock-and-flow** with cohort persistence: each year's new-starts cohort
ages by `Y1` then `Y2+` retention every year thereafter. Revenue =
treated stock × net price × probability of approval (**0.88**).

See `docs/methodology.md` for the full write-up and `data/sources.py` for
per-assumption citations.
            """
        )


# ──────────────────────────── compose params + run forecast ────────────

params = copy.deepcopy(DEFAULTS)
params["epi"]["high_risk_pct"] = high_risk_pct
params["bass"]["market_potential_fraction"] = market_potential_fraction
params["bass"]["p_ultomiris_adjustment"] = p_ultomiris_adjustment
params["persistence"]["year_2plus_persistence"] = year_2plus_persistence
params["pricing"]["net_price_per_patient_year"] = net_price_k * 1000
params["diagnostic_expansion"]["annual_growth_rate"] = diagnostic_expansion

phash = _params_hash(params)
forecast = cached_forecast(phash, params, TARPEYO_MARKET_POTENTIAL_2022)
forecast_years = sorted(forecast.keys())


# ──────────────────────────── KPI strip ────────────────────────────────

scenarios_meta = params["egfr_readout_scenarios"]
revs_by_year = {y: scenario_revenue(forecast[y], selected_scenario) for y in forecast_years}
treats_by_year = {y: scenario_treated(forecast[y], selected_scenario, scenarios_meta) for y in forecast_years}

peak_year = max(revs_by_year, key=revs_by_year.get)
peak_rev = revs_by_year[peak_year]
peak_treated = max(treats_by_year.values())
cumulative_rev = sum(revs_by_year.values())
launch_year = params["launch"]["us_launch_year"]

scenario_help = f"Scenario: {scenario_options[selected_scenario]}"

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Launch year", str(launch_year))
k2.metric("Peak year", str(peak_year), help=scenario_help)
k3.metric("Years to peak", str(peak_year - launch_year), help=scenario_help)
k4.metric("Peak treated", fmt_patients(peak_treated), help=scenario_help)
k5.metric("Peak revenue", fmt_currency(peak_rev), help=scenario_help)
k6.metric(f"Cumulative revenue (through {max(forecast_years)})", fmt_currency(cumulative_rev), help=scenario_help)


# ──────────────────────────── funnel ───────────────────────────────────

funnel_year = 2032 if 2032 in forecast else peak_year
_scenario_subtitle = {
    "expected_value": "Risk-adjusted",
    "strongly_positive": "Strongly positive eGFR",
    "modestly_positive": "Modestly positive eGFR",
    "weak_neutral": "Weak/neutral eGFR",
}[selected_scenario]
pool = compute_patient_pool(
    funnel_year,
    params["launch"]["forecast_start_year"],
    params["epi"],
    params["diagnostic_expansion"]["annual_growth_rate"],
)
class_addressable = pool.high_risk * params["bass"]["market_potential_fraction"]
class_active_stocks = cached_class_active(phash, params, TARPEYO_MARKET_POTENTIAL_2022)
class_active_funnel = class_active_stocks[funnel_year]
ultomiris_treated = scenario_treated(forecast[funnel_year], selected_scenario, scenarios_meta)
st.plotly_chart(
    build_funnel_figure(
        funnel_year,
        pool.diagnosed_prevalent,
        pool.high_risk,
        class_addressable,
        class_active_funnel,
        ultomiris_treated,
        scenario_label=_scenario_subtitle,
    ),
    width="stretch",
)


# ──────────────────────────── revenue | tornado ────────────────────────

st.divider()
col_rev, col_tor = st.columns(2)
with col_rev:
    st.plotly_chart(
        build_revenue_chart(forecast, selected_scenario=selected_scenario),
        width="stretch",
    )
with col_tor:
    st.plotly_chart(
        cached_tornado(phash, params, TARPEYO_MARKET_POTENTIAL_2022, selected_scenario),
        width="stretch",
    )

st.divider()


# ──────────────────────────── SoB | Share of Treated ──────────────────

_SOB_PILL_TO_KEY = {
    "All": None,
    "Treatment naive": "treatment_naive",
    "Corticosteroid": "switch_from_corticosteroid",
    "Endothelin": "switch_from_endothelin",
    "Oral complement": "switch_from_oral_complement",
    "APRIL/BAFF": "switch_from_april_baff",
}

drug_stocks = cached_per_drug_stocks(phash, params, TARPEYO_MARKET_POTENTIAL_2022, selected_scenario)

col_sob, col_share = st.columns(2)
with col_sob:
    _selected_pill = st.pills(
        "Highlight a source",
        options=list(_SOB_PILL_TO_KEY.keys()),
        default="All",
        key="sob_highlight",
    )
    _highlighted_bucket = _SOB_PILL_TO_KEY.get(_selected_pill or "All")
    st.plotly_chart(
        _build_source_of_business_chart(forecast_years, params, _highlighted_bucket),
        width="stretch",
    )
with col_share:
    _share_pill_options = ["All"] + [d.capitalize() for d in COMPETITOR_LAUNCH_YEARS]
    _selected_drug_pill = st.pills(
        "Highlight a drug",
        options=_share_pill_options,
        default="All",
        key="share_highlight",
    )
    _highlighted_drug = (
        None
        if _selected_drug_pill in (None, "All")
        else _selected_drug_pill.lower()
    )
    st.plotly_chart(
        build_share_chart(
            forecast_years,
            drug_stocks,
            launch_years=COMPETITOR_LAUNCH_YEARS,
            highlighted_drug=_highlighted_drug,
        ),
        width="stretch",
    )

st.divider()


# ──────────────────────────── Analog overlay | Weights bar ────────────

col_ana, col_weights = st.columns(2)
with col_ana:
    st.plotly_chart(
        build_analog_overlay(load_tarpeyo(), TARPEYO_MARKET_POTENTIAL_2022, params),
        width="stretch",
    )
with col_weights:
    st.plotly_chart(
        build_weights_chart(params["conjoint"]["attribute_weights"]),
        width="stretch",
    )

st.divider()

render_conjoint_table(2032, params, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS)
st.caption(
    "**How the conjoint drives Share of Treated Patients:** conjoint scores reflect prescriber "
    "preferences across drug attributes — they govern *share allocation* (which drug a new patient "
    "receives) via utility-weighted softmax. Mechanically: "
    "`attribute scores × weights → utility → softmax → share of new starts → accumulating stock → "
    "share of treated patients`. Scores in the table above (1-10, higher = better) evolve "
    "year-over-year via asymptotic maturation on mechanism familiarity, safety, and payer access; "
    "inactive drugs are hidden. Conjoint and the sidebar drivers are intentionally independent "
    "dimensions of the model — the sidebar sliders govern *volume* (how many new patients are "
    "allocated) while the conjoint governs *share* (which drug each one receives). The table above "
    "responds only to the year selector, not to the sidebar sliders."
)
