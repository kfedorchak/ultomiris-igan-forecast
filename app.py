"""Streamlit entry point for the Ultomiris IgAN forecast prototype."""

import copy
import hashlib
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.patient_flow import compute_patient_pool
from core.revenue import run_forecast
from core.source_of_business import source_of_business_by_year
from data.assumptions import DEFAULTS, TARPEYO_MARKET_POTENTIAL_2022
from data.competitive_landscape import COMPETITOR_LAUNCH_YEARS, DRUG_ATTRIBUTES
from viz.analog_overlay import build_analog_overlay
from viz.formatting import fmt_currency, fmt_patients
from viz.funnel import build_funnel_figure
from viz.revenue_chart import build_revenue_chart
from viz.share_chart import build_share_chart
from viz.tornado import build_tornado_chart

st.set_page_config(
    page_title="Ultomiris IgAN Forecast Prototype",
    layout="wide",
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

_SOB_COLORS = {
    "treatment_naive": "#1F77B4",
    "switch_from_corticosteroid": "#8C564B",
    "switch_from_endothelin": "#E377C2",
    "switch_from_oral_complement": "#9467BD",
    "switch_from_april_baff": "#FF7F0E",
    "addon_to_existing": "#7F7F7F",
}


def _build_source_of_business_chart(forecast_years: list[int], params: dict) -> go.Figure:
    """Stacked bar of source-of-business mix across post-launch forecast years."""
    launch_year = params["launch"]["us_launch_year"]
    post_launch = [y for y in forecast_years if y >= launch_year]
    mixes = {
        y: source_of_business_by_year(y - launch_year, params["source_of_business"])
        for y in post_launch
    }
    fig = go.Figure()
    for source, color in _SOB_COLORS.items():
        fig.add_trace(
            go.Bar(
                x=post_launch,
                y=[mixes[y].get(source, 0.0) for y in post_launch],
                name=source.replace("_", " ").title(),
                marker_color=color,
            )
        )
    fig.update_layout(
        barmode="stack",
        title="Source of New Patient Starts",
        xaxis=dict(title="Year", tickmode="linear", dtick=1),
        yaxis_title="Share of starts",
        yaxis_tickformat=".0%",
        template="plotly_white",
        height=440,
        margin=dict(b=110),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
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
    st.header("📊 Scenario")
    scenario_options = {
        "expected_value": "⭐ Risk-adjusted (default)",
        "strongly_positive": "🟢 Strongly positive eGFR (40%)",
        "modestly_positive": "🟡 Modestly positive eGFR (40%)",
        "weak_neutral": "🟠 Weak / neutral eGFR (20%)",
    }
    selected_scenario = st.radio(
        "Display scenario",
        options=list(scenario_options.keys()),
        format_func=lambda k: scenario_options[k],
        index=0,
    )

    st.divider()
    st.header("🔧 Key drivers")

    high_risk_pct = st.slider(
        "% high-risk patients",
        min_value=0.20, max_value=0.60,
        step=0.01, format="%.2f",
        key="high_risk_pct",
    )
    market_potential_fraction = st.slider(
        "Peak treatment penetration",
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
    with st.expander("📚 Methodology"):
        st.markdown(
            """
**Bass diffusion** is calibrated to Tarpeyo's 2022-2025 trajectory; Ultomiris
adoption uses the fitted `(p, q)` with `p × IV/REMS friction` applied to model
slower class-wide ramp.

**Conjoint share** is a softmax over 7 weighted attributes across 8 active
competitors. eGFR readout scenario multipliers scale Ultomiris share from
**2029** (readout year) onward.

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
k6.metric("Cumulative revenue", fmt_currency(cumulative_rev), help=scenario_help)


# ──────────────────────────── funnel ───────────────────────────────────

st.subheader("Patient funnel")
funnel_year = 2032 if 2032 in forecast else peak_year
st.caption(f"Year {funnel_year}, {scenario_options[selected_scenario]}")
pool = compute_patient_pool(
    funnel_year,
    params["launch"]["forecast_start_year"],
    params["epi"],
    params["diagnostic_expansion"]["annual_growth_rate"],
)
class_addressable = pool.high_risk * params["bass"]["market_potential_fraction"]
ultomiris_treated = scenario_treated(forecast[funnel_year], selected_scenario, scenarios_meta)
st.plotly_chart(
    build_funnel_figure(
        funnel_year,
        pool.diagnosed_prevalent,
        pool.high_risk,
        class_addressable,
        ultomiris_treated,
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


# ──────────────────────────── SoB | analog overlay ─────────────────────

col_sob, col_ana = st.columns(2)
with col_sob:
    st.plotly_chart(
        _build_source_of_business_chart(forecast_years, params),
        width="stretch",
    )
with col_ana:
    st.plotly_chart(
        build_analog_overlay(load_tarpeyo(), TARPEYO_MARKET_POTENTIAL_2022, params),
        width="stretch",
    )


# ──────────────────────────── competitive share ────────────────────────

st.plotly_chart(
    build_share_chart(
        forecast_years, params, COMPETITOR_LAUNCH_YEARS, DRUG_ATTRIBUTES
    ),
    width="stretch",
)

st.caption(
    "Prototype model. Default attribute scores, eGFR readout probabilities, and the "
    "Tarpeyo trajectory placeholder require Kyle's review before final use — see README."
)
