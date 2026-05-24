"""Bass diffusion model: closed-form cumulative adoption + Tarpeyo calibration."""

import logging

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)


def bass_cumulative_adoption(
    t: np.ndarray,
    p: float,
    q: float,
    M: float,
) -> np.ndarray:
    """Closed-form Bass cumulative adoption at time t (years)."""
    numerator = 1 - np.exp(-(p + q) * t)
    denominator = 1 + (q / p) * np.exp(-(p + q) * t)
    return M * numerator / denominator


def fit_bass_to_tarpeyo(
    tarpeyo_df: pd.DataFrame,
    tarpeyo_market_potential: float,
    fallback_p: float = 0.012,
    fallback_q: float = 0.42,
) -> tuple[float, float]:
    """Fit (p, q) to observed Tarpeyo cumulative patient adoption; fall back to defaults at bounds or on failure."""
    t_data = tarpeyo_df["quarter_index"].values / 4  # quarters -> years
    cumulative_patients = tarpeyo_df["estimated_patients"].cumsum().values

    def wrapped(t, p, q):
        return bass_cumulative_adoption(t, p, q, tarpeyo_market_potential)

    try:
        popt, _ = curve_fit(
            wrapped,
            t_data,
            cumulative_patients,
            p0=[0.01, 0.4],
            bounds=([0.0001, 0.05], [0.05, 1.0]),
            maxfev=5000,
        )
        p_fit, q_fit = popt
        if p_fit <= 0.0005 or p_fit >= 0.045 or q_fit <= 0.08 or q_fit >= 0.95:
            logger.warning(
                "Bass fit hit bounds (p=%.4f, q=%.3f); using fallback defaults (p=%.4f, q=%.3f)",
                p_fit, q_fit, fallback_p, fallback_q,
            )
            return fallback_p, fallback_q
        return float(p_fit), float(q_fit)
    except Exception as e:
        logger.warning("Bass fit failed: %s; using fallback defaults (p=%.4f, q=%.3f)", e, fallback_p, fallback_q)
        return fallback_p, fallback_q


def ultomiris_cumulative_adoption(
    years_since_launch: np.ndarray,
    p_fit: float,
    q_fit: float,
    ultomiris_market_potential: float,
    p_adjustment: float = 0.7,
) -> np.ndarray:
    """Bass cumulative adoption with p multiplied by p_adjustment (IV/REMS friction); q_fit used directly."""
    p_adjusted = p_fit * p_adjustment
    return bass_cumulative_adoption(years_since_launch, p_adjusted, q_fit, ultomiris_market_potential)
