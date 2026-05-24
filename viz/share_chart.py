"""Competitive share-of-treated stacked area over the active drug set each year."""

import plotly.graph_objects as go

from core.conjoint import (
    compute_drug_utilities,
    get_active_drugs_for_year,
    utilities_to_shares,
)
from viz.formatting import COMPETITOR_PALETTE


def build_share_chart(
    forecast_years: list[int],
    params: dict,
    competitor_launch_years: dict[str, int],
    drug_attributes: dict[str, dict[str, float]],
) -> go.Figure:
    """Stacked area of softmax share per year. Drugs not yet launched contribute 0."""
    utilities = compute_drug_utilities(
        drug_attributes, params["conjoint"]["attribute_weights"]
    )

    share_by_year = {
        year: utilities_to_shares(
            utilities,
            params["conjoint"]["logit_lambda"],
            get_active_drugs_for_year(year, competitor_launch_years),
        )
        for year in forecast_years
    }

    drugs_order = sorted(
        competitor_launch_years.keys(), key=lambda d: competitor_launch_years[d]
    )

    fig = go.Figure()
    for drug in drugs_order:
        ys = [share_by_year[y].get(drug, 0.0) for y in forecast_years]
        fig.add_trace(
            go.Scatter(
                x=forecast_years,
                y=ys,
                mode="lines",
                stackgroup="one",
                name=drug.capitalize(),
                line=dict(color=COMPETITOR_PALETTE.get(drug)),
            )
        )

    fig.update_layout(
        title="Competitive Share of Treated",
        xaxis_title="Year",
        yaxis_title="Share",
        yaxis_tickformat=".0%",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
    )
    return fig
