"""Conjoint-based market share: weighted utility scoring + softmax allocation."""

import math

import numpy as np


# Asymptotic-maturation parameters: each (max_boost, tau_years). Drugs gain
# score on these attributes over time post-launch via boost = max_boost ×
# (1 − exp(−ysl/tau)), capped at 10. Other attributes are fixed by molecular
# properties and do not mature. See data/sources.py for the rationale.
_MATURATION_PARAMS: dict[str, tuple[float, float]] = {
    "mechanism_familiarity": (2.0, 3.0),
    "safety_burden": (1.5, 4.0),
    "payer_access": (1.0, 5.0),
}


def get_drug_attributes_for_year(
    year: int,
    base_attributes: dict[str, dict[str, float]],
    launch_years: dict[str, int],
) -> dict[str, dict[str, float]]:
    """Return per-drug attribute scores at `year` with asymptotic post-launch maturation applied."""
    result: dict[str, dict[str, float]] = {}
    for drug, attrs in base_attributes.items():
        new_attrs = dict(attrs)
        ysl = year - launch_years.get(drug, year)
        if ysl > 0:
            for attr, (max_boost, tau) in _MATURATION_PARAMS.items():
                if attr in new_attrs:
                    boost = max_boost * (1.0 - math.exp(-ysl / tau))
                    new_attrs[attr] = min(10.0, new_attrs[attr] + boost)
        result[drug] = new_attrs
    return result


def compute_drug_utilities(
    drug_attributes: dict[str, dict[str, float]],
    attribute_weights: dict[str, float],
) -> dict[str, float]:
    """Weighted sum of attribute scores per drug. Raises ValueError if weights don't sum to 1.0."""
    weight_sum = sum(attribute_weights.values())
    if abs(weight_sum - 1.0) > 1e-6:
        raise ValueError(f"Attribute weights must sum to 1.0, got {weight_sum:.6f}")

    utilities = {}
    for drug, scores in drug_attributes.items():
        utilities[drug] = sum(
            attribute_weights[attr] * score for attr, score in scores.items()
        )
    return utilities


def utilities_to_shares(
    utilities: dict[str, float],
    logit_lambda: float = 0.5,
    active_drugs: list[str] | None = None,
) -> dict[str, float]:
    """Convert utilities to market shares via softmax; drugs not in active_drugs get share 0."""
    drugs_to_include = active_drugs if active_drugs else list(utilities.keys())
    exp_utils = {d: float(np.exp(logit_lambda * utilities[d])) for d in drugs_to_include}
    total = sum(exp_utils.values())
    shares = {d: e / total for d, e in exp_utils.items()}
    for d in utilities:
        if d not in shares:
            shares[d] = 0.0
    return shares


def get_active_drugs_for_year(
    year: int,
    competitor_launch_years: dict[str, int],
) -> list[str]:
    """Return list of drugs launched as of `year`."""
    return [drug for drug, launch in competitor_launch_years.items() if launch <= year]
