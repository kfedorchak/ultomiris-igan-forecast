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
    TornadoDriver("epi", "high_risk_pct", "% high-risk patients", 0.25, 0.50),
    TornadoDriver("bass", "market_potential_fraction", "Peak treatment penetration", 0.40, 0.80),
    TornadoDriver("bass", "p_ultomiris_adjustment", "IV/REMS friction (1=none)", 0.50, 0.90),
    TornadoDriver("persistence", "year_2plus_persistence", "Annual persistence (y2+)", 0.70, 0.92),
    TornadoDriver("pricing", "net_price_per_patient_year", "Net price ($/yr)", 350_000, 550_000),
    TornadoDriver("diagnostic_expansion", "annual_growth_rate", "Diagnostic expansion (annual)", 0.00, 0.08),
]


def _run_at_bound(
    params: dict,
    driver: TornadoDriver,
    value: float,
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
    target_year: int,
) -> float:
    """Re-run forecast with one parameter swapped to `value`, return target-year EV revenue."""
    p = copy.deepcopy(params)
    p[driver.parent][driver.key] = value
    return run_forecast(p, tarpeyo_df, tarpeyo_market_potential)[target_year].expected_value_revenue


def build_tornado_chart(
    params: dict,
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
    target_year: int = 2032,
) -> go.Figure:
    """Horizontal tornado of low/high deltas from base at `target_year`, sorted by magnitude (largest at top)."""
    base_ev = run_forecast(params, tarpeyo_df, tarpeyo_market_potential)[target_year].expected_value_revenue

    impacts = []
    for d in KEY_DRIVERS:
        low_ev = _run_at_bound(params, d, d.low, tarpeyo_df, tarpeyo_market_potential, target_year)
        high_ev = _run_at_bound(params, d, d.high, tarpeyo_df, tarpeyo_market_potential, target_year)
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
            name="Low bound",
            marker_color="#D9534F",
        )
    )
    fig.add_trace(
        go.Bar(
            y=labels,
            x=[i[2] for i in impacts],
            orientation="h",
            name="High bound",
            marker_color="#5CB85C",
        )
    )
    fig.update_layout(
        title=f"Sensitivity ({target_year} EV revenue) — base case ${base_ev / 1e6:.0f}M",
        xaxis_title="Δ from base case (USD)",
        xaxis=dict(tickformat="$.2s", zeroline=True, zerolinewidth=2, zerolinecolor="black"),
        template="plotly_white",
        height=400,
        barmode="overlay",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return fig
