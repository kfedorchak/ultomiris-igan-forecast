"""Multi-scenario revenue forecast chart with selectable scenario highlighting."""

import plotly.graph_objects as go

from core.revenue import YearlyRevenue
from viz.formatting import SCENARIO_COLORS, ULTOMIRIS_COLOR


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

    fig.update_layout(
        title="US Net Revenue Forecast",
        xaxis_title="Year",
        yaxis_title="Net revenue (USD)",
        template="plotly_white",
        height=400,
        yaxis=dict(tickformat="$.2s"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return fig
