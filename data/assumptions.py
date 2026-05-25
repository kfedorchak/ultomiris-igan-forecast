"""Default forecast parameters for the Ultomiris IgAN model.

All assumptions live here. See sources.py for citations and placeholder flags.
The DEFAULTS dict is the single source of truth; the Streamlit UI mutates copies
of it via slider state.
"""

# Tarpeyo's 2022 launch M for Bass fit. Set at 50% of 2022 high-risk pool
# reflecting first-mover single-mechanism era. NOT the same conceptually as
# market_potential_fraction (which is class-wide peak in mature 8-drug era).
# See sources.py for full rationale.
TARPEYO_MARKET_POTENTIAL_2022 = 27_000

# Active patients per drug at the start of Ultomiris launch year (2027).
# Derived from issuer disclosures: Tarpeyo ~7.5K end-2024 (Asahi Kasei) growing
# to ~10K by end-2026 with continued KOL adoption; Filspari ~4.5K end-2024
# (Travere) growing to ~5K; Fabhalta ~2K end-2024 (Novartis early launch)
# growing to ~3K; Vanrafia/Voyxact 2025 launches; Atacicept 2026 launch.
# Total sums to CLASS_TREATED_AT_ULTOMIRIS_LAUNCH = 20,000.
DRUG_VETERAN_COHORTS_2027: dict[str, float] = {
    "tarpeyo": 10_000,
    "filspari": 5_000,
    "fabhalta": 3_000,
    "vanrafia": 1_000,
    "voyxact": 500,
    "atacicept": 500,
}

# Sum of per-drug veteran cohorts. Used to seed class-wide active stock in the
# funnel so it doesn't artificially start from zero in 2027.
CLASS_TREATED_AT_ULTOMIRIS_LAUNCH = sum(DRUG_VETERAN_COHORTS_2027.values())


DEFAULTS = {
    "epi": {
        "us_adult_population": 258_000_000,
        "diagnosed_prevalence_per_100k": 60,           # range 40-80
        "annual_incidence_per_100k": 1.5,              # range 1.0-2.5
        "high_risk_pct": 0.35,                         # range 0.25-0.50
        "annual_progression_to_eskd_pct": 0.05,        # range 0.03-0.08
        "annual_mortality_pct": 0.015,
    },
    "diagnostic_expansion": {
        "annual_growth_rate": 0.04,                    # 4%/yr growth in diagnosed prevalence
    },
    "bass": {
        "innovation_p_default": 0.012,                 # fallback only if Tarpeyo fit fails
        "imitation_q_default": 0.42,                   # fallback only if Tarpeyo fit fails
        "p_ultomiris_adjustment": 0.7,                 # multiplier on p_fit for IV/REMS friction
        # Peak fraction of high-risk pool treated with ANY targeted therapy in
        # the mature 8-drug class era (2027+). Higher than Tarpeyo's first-mover
        # 50% — see sources.py for rationale.
        "market_potential_fraction": 0.60,
    },
    "conjoint": {
        "attribute_weights": {
            "proteinuria_efficacy": 0.20,
            "egfr_preservation": 0.18,
            "route_of_admin": 0.18,
            "dosing_frequency": 0.10,
            "safety_burden": 0.12,
            "mechanism_familiarity": 0.07,
            "payer_access": 0.15,
        },
        "logit_lambda": 0.5,                           # softmax steepness
    },
    # Source-of-business mix is computed via linear interpolation between
    # EARLY_MIX (year 0) and MATURE_MIX (year >= 8) inside
    # core/source_of_business.py — anchor constants live in that module, not here.
    "persistence": {
        "year_1_persistence": 0.75,                    # range 0.65-0.85
        "year_2plus_persistence": 0.85,                # range 0.75-0.92
    },
    "pricing": {
        "net_price_per_patient_year": 450_000,         # range 350k-550k
        "annual_price_growth": 0.02,
    },
    "launch": {
        "us_launch_year": 2027,
        "forecast_start_year": 2026,
        "forecast_horizon_years": 10,
        "egfr_readout_year": 2029,                     # wk 106 readout; eGFR scenarios gate here
    },
    # eGFR readout scenario multipliers act on Ultomiris share inside
    # compute_new_starts_per_year, gated on year >= egfr_readout_year.
    #
    # Rationale for moderated multipliers (v2):
    # - eGFR benefit is becoming a class characteristic in IgAN, not a unique
    #   differentiator. Fabhalta showed positive eGFR data in APPLAUSE-IgAN at
    #   2 years; multiple drugs in the class are establishing eGFR as table
    #   stakes.
    # - FDA has been lenient on eGFR confirmation: Vanrafia missed its Phase 3
    #   eGFR endpoint and still received accelerated approval, with Novartis
    #   pursuing full approval despite the miss.
    # - Commercial impact of eGFR outcome is therefore meaningful but not
    #   transformative. Strongly positive helps but doesn't make Ultomiris
    #   uniquely differentiated; weak/neutral hurts but doesn't collapse it.
    # - Probability split (40/40/20) preserved: strong proteinuria signal at
    #   week 34 positively correlates with eventual eGFR benefit.
    "egfr_readout_scenarios": {
        "strongly_positive": {
            "probability": 0.40,
            "share_multiplier": 1.18,
            "label": "Strongly positive eGFR (modest commercial uplift; eGFR benefit at class-leading level)",
        },
        "modestly_positive": {
            "probability": 0.40,
            "share_multiplier": 1.00,
            "label": "Modestly positive eGFR (proteinuria + eGFR within class norms)",
        },
        "weak_neutral": {
            "probability": 0.20,
            "share_multiplier": 0.78,
            "label": "Weak/neutral eGFR (real disadvantage but not catastrophic; cf. Vanrafia precedent)",
        },
    },
    # PoA represents accelerated approval (which precedes the wk 106 readout).
    # Full approval conversion uncertainty is captured implicitly in eGFR
    # scenario share multipliers.
    "probability_of_approval": 0.88,
}
