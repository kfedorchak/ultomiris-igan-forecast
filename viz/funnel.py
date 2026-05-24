"""Patient funnel: diagnosed IgAN -> high-risk -> class-treated -> Ultomiris on-therapy."""

import plotly.graph_objects as go

from viz.formatting import ULTOMIRIS_COLOR


def build_funnel_figure(
    year: int,
    diagnosed_prevalent: float,
    high_risk: float,
    class_addressable: float,
    ultomiris_treated: float,
) -> go.Figure:
    """Plotly Funnel from diagnosed IgAN through to Ultomiris on-therapy at `year`."""
    stages = ["Diagnosed IgAN", "High-risk", "Treated (class peak)", "Ultomiris on therapy"]
    values = [diagnosed_prevalent, high_risk, class_addressable, ultomiris_treated]
    colors = ["#BDBDBD", "#9E9E9E", "#757575", ULTOMIRIS_COLOR]

    fig = go.Figure(
        go.Funnel(
            y=stages,
            x=values,
            textinfo="value+percent previous",
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
