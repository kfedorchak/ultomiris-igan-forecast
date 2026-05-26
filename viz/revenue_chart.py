"""Multi-scenario revenue forecast chart with selectable scenario highlighting."""

import math

import plotly.graph_objects as go

from core.revenue import YearlyRevenue
from viz.formatting import SCENARIO_COLORS, TITLE_COLOR, ULTOMIRIS_COLOR, fmt_currency


SCENARIO_LABELS = {
    "strongly_positive": "Strongly positive eGFR",
    "modestly_positive": "Modestly positive eGFR",
    "weak_neutral": "Weak/neutral eGFR",
}


def build_revenue_chart(
    forecast: dict[int, YearlyRevenue],
    selected_scenario: str = "expected_value",
) -> go.Figure:
    """Line chart of scenario revenues over time. Selected scenario is bold; others are faded."""
    years = sorted(forecast.keys())
    fig = go.Figure()

    for scenario_key, label in SCENARIO_LABELS.items():
        is_selected = scenario_key == selected_scenario
        ys = [forecast[y].revenues_by_scenario[scenario_key] for y in years]
        fig.add_trace(
            go.Scatter(
                x=years,
                y=ys,
                mode="lines+markers",
                name=label,
                line=dict(color=SCENARIO_COLORS[scenario_key], width=3 if is_selected else 1.5),
                opacity=1.0 if is_selected else 0.35,
            )
        )

    is_ev_selected = selected_scenario == "expected_value"
    ys_ev = [forecast[y].expected_value_revenue for y in years]
    fig.add_trace(
        go.Scatter(
            x=years,
            y=ys_ev,
            mode="lines+markers",
            name="Risk-adjusted (EV)",
            line=dict(color=ULTOMIRIS_COLOR, width=3 if is_ev_selected else 1.5),
            opacity=1.0 if is_ev_selected else 0.5,
        )
    )

    # Explicit y-axis ticks using fmt_currency so billions render as "B"
    # (Plotly's "$.2s" SI format uses "G" for giga). Step picked from peak
    # value in the chart's data.
    all_revs = []
    for y in years:
        all_revs.extend(forecast[y].revenues_by_scenario.values())
        all_revs.append(forecast[y].expected_value_revenue)
    max_rev = max(all_revs) if all_revs else 1e9
    if max_rev >= 2e9:
        step = 5e8
    elif max_rev >= 1e9:
        step = 2.5e8
    elif max_rev >= 4e8:
        step = 1e8
    elif max_rev >= 1e8:
        step = 5e7
    else:
        step = 2.5e7
    n_ticks = math.ceil(max_rev / step) + 1
    tickvals = [i * step for i in range(n_ticks + 1)]
    ticktext = [fmt_currency(v) for v in tickvals]

    fig.update_layout(
        title=dict(text="US Net Revenue Forecast", font=dict(color=TITLE_COLOR)),
        xaxis=dict(title="Year", tickmode="linear", dtick=1),
        yaxis=dict(
            title="Net revenue (USD)",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
        ),
        template="plotly_white",
        height=440,
        margin=dict(b=110),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
    )
    return fig
