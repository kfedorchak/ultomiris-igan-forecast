"""Source-of-business mix via linear interpolation between two mechanism-based anchors."""


# Year-0 (KOL early-adopter) anchor. Naive-heavy with modest switching as
# Ultomiris launches into a market still being educated.
EARLY_MIX: dict[str, float] = {
    "treatment_naive": 0.55,
    "switch_from_corticosteroid": 0.08,        # Tarpeyo
    "switch_from_endothelin": 0.07,            # Filspari, Vanrafia
    "switch_from_oral_complement": 0.03,       # Fabhalta
    "switch_from_april_baff": 0.10,            # Voyxact, Atacicept, Povetacicept
    "addon_to_existing": 0.17,
}

# Year-8+ (mature-market) anchor. Naive share drops, switching grows as
# KOL adopter momentum decays and Ultomiris pulls from established
# mechanism-class cohorts.
MATURE_MIX: dict[str, float] = {
    "treatment_naive": 0.35,
    "switch_from_corticosteroid": 0.12,
    "switch_from_endothelin": 0.12,
    "switch_from_oral_complement": 0.06,
    "switch_from_april_baff": 0.20,
    "addon_to_existing": 0.15,
}

# Years over which the early-to-mature blend runs linearly. Sigmoid is the
# natural refinement; see docs/methodology.md.
TRANSITION_YEARS: int = 8


def source_of_business_by_year(years_since_launch: int) -> dict[str, float]:
    """Linear interpolation between EARLY_MIX (Y0) and MATURE_MIX (Y >= TRANSITION_YEARS), defensively normalized."""
    weight = max(0.0, min(years_since_launch / TRANSITION_YEARS, 1.0))
    mix = {
        k: (1.0 - weight) * EARLY_MIX[k] + weight * MATURE_MIX[k]
        for k in EARLY_MIX
    }
    total = sum(mix.values())
    return {k: v / total for k, v in mix.items()}
