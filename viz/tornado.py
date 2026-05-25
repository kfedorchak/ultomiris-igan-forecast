"""Tornado sensitivity chart: six key drivers, impact on a target-year EV revenue."""

import copy
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from core.revenue import run_forecast


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
    TornadoDriver("bass", "market_potential_fraction", "Peak treatment penetration", 0.30, 0.85),
    TornadoDriver("bass", "p_ultomiris_adjustment", "IV/REMS friction (1=none)", 0.30, 1.00),
    TornadoDriver("persistence", "year_2plus_persistence", "Annual persistence (y2+)", 0.60, 0.95),
    TornadoDriver("pricing", "net_price_per_patient_year", "Net price ($/yr)", 250_000, 700_000),
    TornadoDriver("diagnostic_expansion", "annual_growth_rate", "Diagnostic expansion (annual)", -0.02, 0.12),
]


def _cumulative_ev(
    params: dict,
    driver: TornadoDriver,
    value: float,
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
) -> float:
    """Re-run forecast with one parameter swapped to `value`, return cumulative EV revenue across the horizon."""
    p = copy.deepcopy(params)
    p[driver.parent][driver.key] = value
    fc = run_forecast(p, tarpeyo_df, tarpeyo_market_potential)
    return sum(yr.expected_value_revenue for yr in fc.values())


def build_tornado_chart(
    params: dict,
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
) -> go.Figure:
    """Horizontal tornado of low/high deltas from base cumulative EV revenue across the forecast horizon."""
    base_fc = run_forecast(params, tarpeyo_df, tarpeyo_market_potential)
    base_ev = sum(yr.expected_value_revenue for yr in base_fc.values())

    impacts = []
    for d in KEY_DRIVERS:
        low_ev = _cumulative_ev(params, d, d.low, tarpeyo_df, tarpeyo_market_potential)
        high_ev = _cumulative_ev(params, d, d.high, tarpeyo_df, tarpeyo_market_potential)
        low_delta = low_ev - base_ev
        high_delta = high_ev - base_ev
        magnitude = abs(low_delta) + abs(high_delta)
        impacts.append((d.label, low_delta, high_delta, magnitude))

    # Sort ascending so largest plots at the top of the y-axis
    impacts.sort(key=lambda x: x[3])

    labels = [i[0] for i in impacts]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=labels,
            x=[i[1] for i in impacts],
            orientation="h",
            name="Low driver value",
            marker_color="#D9534F",
        )
    )
    fig.add_trace(
        go.Bar(
            y=labels,
            x=[i[2] for i in impacts],
            orientation="h",
            name="High driver value",
            marker_color="#5CB85C",
        )
    )
    fig.update_layout(
        title=f"Sensitivity (cumulative EV revenue) — base ${base_ev / 1e9:.2f}B",
        xaxis_title="Δ from base cumulative EV (USD)",
        xaxis=dict(tickformat="$.2s", zeroline=True, zerolinewidth=2, zerolinecolor="black"),
        template="plotly_white",
        height=400,
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return fig
