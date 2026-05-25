"""Tarpeyo observed adoption vs. fitted Bass + Ultomiris-friction-adjusted projection."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.bass_model import bass_cumulative_adoption, fit_bass_to_tarpeyo
from viz.formatting import ULTOMIRIS_COLOR


def build_analog_overlay(
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
    params: dict,
) -> go.Figure:
    """Cumulative adoption: Tarpeyo observed + Bass fit + Ultomiris friction-adjusted projection (same M)."""
    p_fit, q_fit = fit_bass_to_tarpeyo(
        tarpeyo_df,
        tarpeyo_market_potential,
        fallback_p=params["bass"]["innovation_p_default"],
        fallback_q=params["bass"]["imitation_q_default"],
    )

    t_obs = tarpeyo_df["quarter_index"].values / 4
    cum_obs = tarpeyo_df["estimated_patients"].cumsum().values

    t_curve = np.linspace(0, 10, 100)
    cum_tarpeyo = bass_cumulative_adoption(t_curve, p_fit, q_fit, tarpeyo_market_potential)
    p_adj = p_fit * params["bass"]["p_ultomiris_adjustment"]
    cum_ultomiris = bass_cumulative_adoption(t_curve, p_adj, q_fit, tarpeyo_market_potential)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=t_obs,
            y=cum_obs,
            mode="markers",
            name="Tarpeyo (observed)",
            marker=dict(color="#8C564B", size=8),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=t_curve,
            y=cum_tarpeyo,
            mode="lines",
            name=f"Tarpeyo Bass fit (p={p_fit:.3f}, q={q_fit:.3f})",
            line=dict(color="#8C564B", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=t_curve,
            y=cum_ultomiris,
            mode="lines",
            name=f"Ultomiris projection (p x {params['bass']['p_ultomiris_adjustment']})",
            line=dict(color=ULTOMIRIS_COLOR, width=2, dash="dash"),
        )
    )
    fig.update_layout(
        title="Tarpeyo Analog — Bass Diffusion Calibration",
        xaxis_title="Years since launch",
        yaxis_title="Cumulative patients (same market potential)",
        template="plotly_white",
        height=440,
        margin=dict(b=110),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
    )
    return fig
