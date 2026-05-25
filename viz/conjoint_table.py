"""Conjoint transparency panel — attribute weights bar + drug × attribute heatmap table."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from matplotlib.colors import LinearSegmentedColormap

from core.conjoint import (
    compute_drug_utilities,
    get_active_drugs_for_year,
    get_drug_attributes_for_year,
    utilities_to_shares,
)
from viz.formatting import ULTOMIRIS_COLOR


# Sequential grey -> Alexion-blue colormap for the drug × attribute heatmap.
# Capped at a mid-blue tone so a single dark text color stays readable
# across the full range (no per-cell black/white text auto-switching).
_BLUE_GREY_CMAP = LinearSegmentedColormap.from_list(
    "alexion_blue_grey",
    ["#F5F5F5", "#9FAFD0", "#5066A0"],
)


_ATTR_DISPLAY: dict[str, str] = {
    "proteinuria_efficacy": "Proteinuria efficacy",
    "egfr_preservation": "eGFR preservation",
    "route_of_admin": "Route of admin",
    "dosing_frequency": "Dosing frequency",
    "safety_burden": "Safety profile",
    "mechanism_familiarity": "Mechanism familiarity",
    "payer_access": "Payer access",
}


def build_weights_chart(weights: dict[str, float]) -> go.Figure:
    """Horizontal bar chart of attribute weights, sorted descending (largest at top)."""
    items_asc = sorted(weights.items(), key=lambda x: x[1])
    labels = [_ATTR_DISPLAY.get(a, a.replace("_", " ").title()) for a, _ in items_asc]
    values = [w for _, w in items_asc]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker_color=ULTOMIRIS_COLOR,
            text=[f"{w * 100:.0f}%" for w in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Attribute importance weights",
        xaxis=dict(title="Weight", tickformat=".0%", range=[0, 0.30]),
        template="plotly_white",
        height=440,
        margin=dict(l=180, r=60, t=60, b=110),
        showlegend=False,
    )
    return fig


def compute_conjoint_table_data(
    year: int,
    params: dict,
    base_attributes: dict[str, dict[str, float]],
    launch_years: dict[str, int],
) -> tuple[pd.DataFrame, dict[str, float], list[str]]:
    """Build the drug × attribute dataframe at `year`, filtered to active drugs.

    Returns (df, weights, attribute_key_order). df has one row per active drug
    (capitalized index) with attribute-score columns plus Utility and Share.
    Share is stored as a float (0..1); the caller formats for display.
    """
    weights = params["conjoint"]["attribute_weights"]
    logit_lambda = params["conjoint"]["logit_lambda"]

    year_attrs = get_drug_attributes_for_year(year, base_attributes, launch_years)
    utilities = compute_drug_utilities(year_attrs, weights)
    active = get_active_drugs_for_year(year, launch_years)
    shares = utilities_to_shares(utilities, logit_lambda, active)

    rows = {drug: year_attrs[drug] for drug in active}
    df = pd.DataFrame(rows).T
    df["Utility"] = pd.Series({drug: utilities[drug] for drug in active})
    df["Share"] = pd.Series({drug: shares[drug] for drug in active})

    attr_keys = list(weights.keys())
    df = df[attr_keys + ["Utility", "Share"]]
    df.index = df.index.str.capitalize()
    return df, weights, attr_keys


def render_conjoint_table(
    year: int,
    params: dict,
    base_attributes: dict[str, dict[str, float]],
    launch_years: dict[str, int],
) -> None:
    """Render the year-selector + drug × attribute heatmap table via Streamlit primitives."""
    forecast_start = params["launch"]["forecast_start_year"]
    horizon = params["launch"]["forecast_horizon_years"]
    yr_min = forecast_start
    yr_max = forecast_start + horizon - 1
    default_year = year if yr_min <= year <= yr_max else (yr_min + yr_max) // 2

    st.markdown("**Drug × attribute scores at the selected year**")
    selected_year = st.slider(
        "Year",
        min_value=yr_min,
        max_value=yr_max,
        value=default_year,
        step=1,
        key="conjoint_panel_year",
    )

    df, _, attr_keys = compute_conjoint_table_data(
        selected_year, params, base_attributes, launch_years
    )
    display_df = df.rename(columns=_ATTR_DISPLAY)
    attr_display_cols = [_ATTR_DISPLAY[k] for k in attr_keys]

    fmt_map = {col: "{:.2f}" for col in attr_display_cols + ["Utility"]}
    fmt_map["Share"] = "{:.1%}"
    styled = (
        display_df.style.background_gradient(
            cmap=_BLUE_GREY_CMAP,
            subset=attr_display_cols,
            vmin=1,
            vmax=10,
            text_color_threshold=0,        # disable per-cell black/white text auto-switch
        )
        .format(fmt_map)
        .set_properties(color="#1F1F1F")   # single consistent text color across the whole table
    )
    # Height tuned to fit N drug rows + header (35px/row, 38px header) with
    # no trailing blank row. Streamlit's dataframe widget reserves trailing
    # space proportional to the difference between height and content.
    n_rows = len(display_df)
    st.dataframe(styled, width="stretch", height=35 * n_rows + 38)
