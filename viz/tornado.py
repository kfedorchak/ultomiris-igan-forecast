"""Tornado sensitivity chart: six key drivers, impact on a target-year EV revenue."""

import copy
import math
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from core.revenue import run_forecast
from viz.formatting import ALEXION_BLUE, GREY_MEDIUM, fmt_currency


@dataclass(frozen=True)
class TornadoDriver:
    """A sensitivity driver: parameter path + low/high bounds + display label."""

    parent: str
    key: str
    label: str
    low: float
    high: float


KEY_DRIVERS: list[TornadoDriver] = [
    TornadoDriver("epi", "high_risk_pct", "% high-risk patients", 0.20, 0.60),
    TornadoDriver("bass", "market_potential_fraction", "Class adoption ceiling", 0.30, 0.85),
    TornadoDriver("bass", "p_ultomiris_adjustment", "IV/REMS friction (1=none)", 0.30, 1.00),
    TornadoDriver("persistence", "year_2plus_persistence", "Annual persistence (y2+)", 0.60, 0.95),
    TornadoDriver("pricing", "net_price_per_patient_year", "Net price ($/yr)", 250_000, 700_000),
    TornadoDriver("diagnostic_expansion", "annual_growth_rate", "Diagnostic expansion (annual)", 0.01, 0.08),
]


def _cumulative_revenue(
    params: dict,
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
    scenario: str,
) -> float:
    """Cumulative revenue across the forecast horizon under the given scenario ('expected_value' = EV-weighted)."""
    fc = run_forecast(params, tarpeyo_df, tarpeyo_market_potential)
    if scenario == "expected_value":
        return sum(yr.expected_value_revenue for yr in fc.values())
    return sum(yr.revenues_by_scenario[scenario] for yr in fc.values())


def _cumulative_at_bound(
    params: dict,
    driver: TornadoDriver,
    value: float,
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
    scenario: str,
) -> float:
    """Re-run forecast with `driver` swapped to `value`, return cumulative revenue under `scenario`."""
    p = copy.deepcopy(params)
    p[driver.parent][driver.key] = value
    return _cumulative_revenue(p, tarpeyo_df, tarpeyo_market_potential, scenario)


_SCENARIO_TITLE = {
    "expected_value": "cumulative EV revenue",
    "strongly_positive": "cumulative revenue (strongly positive)",
    "modestly_positive": "cumulative revenue (modestly positive)",
    "weak_neutral": "cumulative revenue (weak/neutral)",
}


def build_tornado_chart(
    params: dict,
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
    scenario: str = "expected_value",
) -> go.Figure:
    """Horizontal tornado of low/high deltas from base cumulative revenue under the selected scenario."""
    base_ev = _cumulative_revenue(params, tarpeyo_df, tarpeyo_market_potential, scenario)

    impacts = []
    for d in KEY_DRIVERS:
        low_ev = _cumulative_at_bound(params, d, d.low, tarpeyo_df, tarpeyo_market_potential, scenario)
        high_ev = _cumulative_at_bound(params, d, d.high, tarpeyo_df, tarpeyo_market_potential, scenario)
        low_delta = low_ev - base_ev
        high_delta = high_ev - base_ev
        magnitude = abs(low_delta) + abs(high_delta)
        impacts.append((d.label, low_delta, high_delta, magnitude))

    # Sort ascending so largest plots at the top of the y-axis
    impacts.sort(key=lambda x: x[3])

    labels = [i[0] for i in impacts]
    low_deltas = [i[1] for i in impacts]
    high_deltas = [i[2] for i in impacts]
    # Hover labels use fmt_currency with 2 decimals so billions read as
    # "$1.23B" rather than d3's default high-precision raw number.
    low_hover = [fmt_currency(d, scale_precision=2) for d in low_deltas]
    high_hover = [fmt_currency(d, scale_precision=2) for d in high_deltas]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=labels,
            x=low_deltas,
            orientation="h",
            name="Low driver value",
            marker_color=GREY_MEDIUM,
            customdata=low_hover,
            hovertemplate="<b>%{y}</b><br>Low driver value: %{customdata}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=labels,
            x=high_deltas,
            orientation="h",
            name="High driver value",
            marker_color=ALEXION_BLUE,
            customdata=high_hover,
            hovertemplate="<b>%{y}</b><br>High driver value: %{customdata}<extra></extra>",
        )
    )
    # Build explicit tick labels using fmt_currency so billions render as "B"
    # instead of d3-format's SI default "G". Symmetric around zero, step
    # picked from the magnitude of the largest delta in the data.
    all_deltas = [d for i in impacts for d in (i[1], i[2])]
    abs_max = max(abs(v) for v in all_deltas) if all_deltas else 1e9
    if abs_max >= 2e9:
        tick_step = 1e9
    elif abs_max >= 1e9:
        tick_step = 5e8
    elif abs_max >= 4e8:
        tick_step = 2e8
    else:
        tick_step = 1e8
    n_ticks = math.ceil(abs_max / tick_step)
    tickvals = [i * tick_step for i in range(-n_ticks, n_ticks + 1)]
    ticktext = [fmt_currency(v, scale_precision=0) for v in tickvals]

    fig.update_layout(
        title=f"Sensitivity ({_SCENARIO_TITLE[scenario]}) — base ${base_ev / 1e9:.2f}B",
        xaxis=dict(
            title="Δ from base cumulative EV (USD)",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="black",
        ),
        template="plotly_white",
        height=440,
        margin=dict(b=110),
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
    )
    return fig
