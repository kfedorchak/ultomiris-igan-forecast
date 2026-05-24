"""Source-of-business mix by years-since-launch (mechanism-based buckets)."""


# Year 1-2 favors treatment-naive (KOL early adopters). Identical to the
# DEFAULTS year-3-5 base mix today; carved out as a separate constant so the
# early-launch phase can be retuned independently from the base mix later.
YEAR_1_2_MIX: dict[str, float] = {
    "treatment_naive": 0.55,
    "switch_from_corticosteroid": 0.08,
    "switch_from_endothelin": 0.07,
    "switch_from_oral_complement": 0.03,
    "switch_from_april_baff": 0.10,
    "addon_to_existing": 0.17,
}

# Year 6+ shifts toward switching as the market educates and Ultomiris pulls
# from established patients on each mechanism class.
YEAR_6PLUS_MIX: dict[str, float] = {
    "treatment_naive": 0.35,
    "switch_from_corticosteroid": 0.12,
    "switch_from_endothelin": 0.12,
    "switch_from_oral_complement": 0.06,
    "switch_from_april_baff": 0.20,
    "addon_to_existing": 0.15,
}


def source_of_business_by_year(
    years_since_launch: int,
    base_mix: dict[str, float],
) -> dict[str, float]:
    """Return mechanism-based source-of-business mix for `years_since_launch`, defensively normalized to 1.0."""
    if years_since_launch <= 2:
        mix = YEAR_1_2_MIX
    elif years_since_launch <= 5:
        mix = base_mix
    else:
        mix = YEAR_6PLUS_MIX

    total = sum(mix.values())
    return {k: v / total for k, v in mix.items()}
