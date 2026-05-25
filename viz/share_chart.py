"""Share-of-treated stacked area chart (stock-based, not new-starts-based)."""

import plotly.graph_objects as go

from viz.formatting import COMPETITOR_PALETTE


def build_share_chart(
    forecast_years: list[int],
    drug_stocks: dict[str, dict[int, float]],
    launch_years: dict[str, int] | None = None,
) -> go.Figure:
    """Stacked area of per-drug share of active treated stock per year.

    `drug_stocks` is the {drug: {year: active stock}} output of
    core.revenue.compute_per_drug_treated_stocks. `launch_years` orders the
    legend so first-launched drugs sit at the bottom of the stack.
    """
    share_by_year: dict[int, dict[str, float]] = {}
    for year in forecast_years:
        total = sum(drug_stocks[d].get(year, 0.0) for d in drug_stocks)
        if total > 0:
            share_by_year[year] = {
                d: drug_stocks[d].get(year, 0.0) / total for d in drug_stocks
            }
        else:
            share_by_year[year] = {d: 0.0 for d in drug_stocks}

    if launch_years is not None:
        drugs_order = sorted(drug_stocks.keys(), key=lambda d: launch_years.get(d, 9999))
    else:
        drugs_order = sorted(drug_stocks.keys())

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
        title="Share of Treated Patients (Stock-Derived)",
        xaxis=dict(title="Year", tickmode="linear", dtick=1),
        yaxis_title="Share",
        yaxis_tickformat=".0%",
        template="plotly_white",
        height=440,
        margin=dict(b=110),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
    )
    return fig
