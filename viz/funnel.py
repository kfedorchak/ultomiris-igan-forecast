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
    scenario_label: str = "",
) -> go.Figure:
    """Plotly Funnel — all values at `year`. `scenario_label` renders as a subtitle under the chart title."""
    stages = [
        "Diagnosed IgAN",
        "High-risk",
        "Class adoption ceiling",
        "On targeted IgAN therapy",
        "Ultomiris on therapy",
    ]
    values = [diagnosed_prevalent, high_risk, class_addressable, class_active, ultomiris_treated]
    colors = ["#BDBDBD", "#9E9E9E", "#757575", "#616161", ULTOMIRIS_COLOR]

    title = f"Patient Funnel — all values at {year}"
    if scenario_label:
        title += f"<br><span style='font-size:13px;color:#888'>{scenario_label}</span>"

    fig = go.Figure(
        go.Funnel(
            y=stages,
            x=values,
            texttemplate="%{value:,.0f}  (%{percentPrevious:.1%} of prior)",
            marker=dict(color=colors),
        )
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=360,
        margin=dict(l=240, r=20, t=80, b=20),
    )
    return fig
