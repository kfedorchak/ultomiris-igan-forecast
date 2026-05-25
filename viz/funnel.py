"""Patient funnel: diagnosed IgAN -> high-risk -> class-treated -> Ultomiris on-therapy."""

import plotly.graph_objects as go

from viz.formatting import ULTOMIRIS_COLOR


def build_funnel_figure(
    year: int,
    diagnosed_prevalent: float,
    high_risk: float,
    class_addressable: float,
    class_active: float,
    ultomiris_treated: float,
) -> go.Figure:
    """Plotly Funnel: diagnosed -> high-risk -> class peak (long-run M) -> class active (this year) -> Ultomiris."""
    stages = [
        "Diagnosed IgAN",
        "High-risk",
        "Treated (class peak)",
        f"Treated (class active, {year})",
        "Ultomiris on therapy",
    ]
    values = [diagnosed_prevalent, high_risk, class_addressable, class_active, ultomiris_treated]
    colors = ["#BDBDBD", "#9E9E9E", "#757575", "#616161", ULTOMIRIS_COLOR]

    fig = go.Figure(
        go.Funnel(
            y=stages,
            x=values,
            texttemplate="%{value:,.0f}  (%{percentPrevious:.1%} of prior)",
            marker=dict(color=colors),
        )
    )
    fig.update_layout(
        title=f"Patient Funnel — {year} (modestly-positive scenario)",
        template="plotly_white",
        height=350,
        margin=dict(l=160, r=20, t=60, b=20),
    )
    return fig
