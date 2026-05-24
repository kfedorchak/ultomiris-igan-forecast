"""Conjoint-based market share: weighted utility scoring + softmax allocation."""

import numpy as np


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
