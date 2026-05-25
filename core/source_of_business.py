"""Source-of-business mix via linear interpolation between two mechanism-based anchors."""


# Year-0 (KOL early-adopter) anchor. Naive-heavy with modest switching as
# Ultomiris launches into a market still being educated. The original v1
# addon-to-existing bucket (0.17) has been removed and redistributed
# proportionally across the four switch_from_* categories — see
# docs/methodology.md for the rationale (combination targeted therapy
# not modeled in v2; addon patients reclassified as switches).
EARLY_MIX: dict[str, float] = {
    "treatment_naive": 0.55,
    "switch_from_corticosteroid": 0.1286,      # Tarpeyo (0.08 + 0.17 * 0.08/0.28)
    "switch_from_endothelin": 0.1125,          # Filspari, Vanrafia (0.07 + 0.17 * 0.07/0.28)
    "switch_from_oral_complement": 0.0482,     # Fabhalta (0.03 + 0.17 * 0.03/0.28)
    "switch_from_april_baff": 0.1607,          # Voyxact, Atacicept, Povetacicept (0.10 + 0.17 * 0.10/0.28)
}

# Year-8+ (mature-market) anchor. Naive share drops, switching grows as
# KOL adopter momentum decays and Ultomiris pulls from established
# mechanism-class cohorts. Addon (0.15) redistributed across switches.
MATURE_MIX: dict[str, float] = {
    "treatment_naive": 0.35,
    "switch_from_corticosteroid": 0.156,       # 0.12 + 0.15 * 0.12/0.50
    "switch_from_endothelin": 0.156,           # 0.12 + 0.15 * 0.12/0.50
    "switch_from_oral_complement": 0.078,      # 0.06 + 0.15 * 0.06/0.50
    "switch_from_april_baff": 0.260,           # 0.20 + 0.15 * 0.20/0.50
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
