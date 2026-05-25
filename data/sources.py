"""Citation dictionary keyed by assumption.

Entries in PLACEHOLDERS are non-production values Kyle must replace with
actuals before final use (spec Section 13).
"""

SOURCES = {
    "us_adult_population": "US Census Bureau 2024 estimate (258M adults).",
    "diagnosed_prevalence_per_100k": (
        "Wyatt & Julian, NEJM 2013; AZ I CAN trial press release "
        "(560K diagnosed IgAN patients across US + EU5 + JP)."
    ),
    "annual_incidence_per_100k": (
        "Multiple registry studies; KDIGO 2021 Glomerular Diseases guideline range."
    ),
    "high_risk_pct": (
        "KDIGO 2021 Clinical Practice Guideline for Glomerular Diseases — "
        "patients with proteinuria >1g/day and/or declining eGFR are high-risk."
    ),
    "annual_progression_to_eskd_pct": (
        "Pitcher et al. CJASN 2023 natural history; ranges 3-8% depending on baseline severity."
    ),
    "annual_mortality_pct": "All-cause mortality in IgAN cohorts; KDIGO 2021 reference data.",
    "diagnostic_expansion": (
        "Increasing rates of routine urinalysis screening + nephrologist referral; "
        "consensus across Tarpeyo/Filspari/Fabhalta investor analyst reports."
    ),
    "bass_fallback_defaults": (
        "Sultan, Farley, Lehmann (1990) meta-analysis of Bass diffusion fits across "
        "consumer/pharma launches: p ~ 0.01-0.03, q ~ 0.3-0.5 median."
    ),
    "market_potential_penetration_assumptions": (
        "Tarpeyo Bass fit uses 50% peak penetration of 2022 high-risk pool (~27,000 patients), "
        "reflecting first-mover constraints: single-mechanism corticosteroid class, "
        "pre-diversified market, less mature diagnostic infrastructure. "
        "Ultomiris-era market_potential_fraction set at 60%, reflecting mature 8-drug class "
        "(corticosteroid, ERA, complement, APRIL/BAFF), 5+ years of KDIGO guideline evolution "
        "toward earlier targeted therapy, and diagnostic expansion. "
        "The 10pp difference is intentional and reflects therapy class maturation."
    ),
    "tarpeyo_market_potential_2022": (
        "27,000 = 2022 high-risk pool (~54,000) x 0.50 first-mover penetration. "
        "See market_potential_penetration_assumptions for rationale on the 50%/60% asymmetry."
    ),
    "class_treated_at_ultomiris_launch": (
        "PLACEHOLDER: ~20,000 active patients on a targeted IgAN therapy at Ultomiris "
        "launch (start of 2027). Derived from issuer disclosures: Tarpeyo ~7,500 "
        "end-2024 (Asahi Kasei), Filspari ~4,500 end-2024 (Travere 10-Q), Fabhalta "
        "~2,000 end-2024 (Novartis, early launch), with Vanrafia/Voyxact early-ramp "
        "additions through 2025-2026 and continuing class growth. Kyle replaces "
        "with reconciled actuals before final use."
    ),
    "drug_veteran_cohorts_2027": (
        "PLACEHOLDER per-drug split of the 20K class veteran cohort at end-2026: "
        "Tarpeyo 10K (first mover, 4yr ramp), Filspari 5K (3yr), Fabhalta 3K (2yr), "
        "Vanrafia 1K + Voyxact 0.5K (2025 launches), Atacicept 0.5K (2026 launch). "
        "Drives first-mover stock advantage in the share-of-treated chart. Kyle "
        "replaces with reconciled actuals."
    ),
    "asymptotic_attribute_maturation": (
        "Real-world clinical & commercial perception of a drug evolves post-launch: "
        "prescriber familiarity grows with experience, the safety profile gets "
        "characterized through registries, and payer access matures via formulary "
        "negotiations. We model this with asymptotic growth: "
        "boost(t) = max_boost × (1 − exp(−t/tau)), where t is years since launch. "
        "Parameters chosen to be intuitive rather than calibrated: "
        "mechanism_familiarity (max_boost=2.0, tau=3yr — prescribers learn fast); "
        "safety_burden (max_boost=1.5, tau=4yr — registry data matures over years); "
        "payer_access (max_boost=1.0, tau=5yr — formulary cycles are slow). "
        "Scores cap at 10. Other attributes (efficacy, route, dosing) are fixed by "
        "molecular properties and don't mature. Sigmoid or logistic would be the "
        "natural refinement if a learning-curve inflection becomes empirically observable."
    ),
    "p_ultomiris_adjustment": (
        "Multiplier on Tarpeyo-fitted innovation rate to reflect IV q8w + meningococcal "
        "REMS friction vs. Tarpeyo's oral self-administered profile. Analyst consensus "
        "0.6-0.8 for IV biologic launches into oral-dominated markets."
    ),
    "conjoint_attribute_weights": (
        "Adapted from prior physician conjoint studies in nephrology (chronic biologic "
        "and oral therapies). Kyle's prioritization judgment governs final weights."
    ),
    "drug_attributes": (
        "Composite of trial readouts (proteinuria, eGFR), label features (route, dosing, "
        "safety), and analyst commentary on payer positioning. See clinical references in "
        "docs/data_sources.md."
    ),
    "vanrafia_egfr_score": (
        "Scored 5 reflecting ALIGN trial Phase 3 eGFR endpoint miss; FiercePharma Feb 2026."
    ),
    "voyxact_attributes": (
        "Sibeprenlimab (Otsuka/Visterra) Phase 3 readout; first-in-class APRIL inhibitor."
    ),
    "source_of_business_mix": (
        "Mechanism-based switch buckets (corticosteroid, endothelin, oral complement, "
        "APRIL/BAFF). Initial mix favors treatment-naive in Y1-5 (KOL adopters), "
        "shifts toward switching as market matures (Y6+). Kyle's judgment governs."
    ),
    "persistence": (
        "Chronic biologic real-world persistence benchmarks (PNH/aHUS Ultomiris analogs); "
        "Y1 ~75%, Y2+ ~85% annual retention."
    ),
    "net_price_per_patient_year": (
        "Third-party analyst estimates; ICER complement inhibitor reports; "
        "Ultomiris PNH/aHUS price points adjusted for IgAN payer mix."
    ),
    "annual_price_growth": "Specialty biologic WAC growth trend, 2-3%/yr.",
    "launch_timing": (
        "AZ I CAN Phase 3 timeline: wk 34 proteinuria readout 2026, wk 106 eGFR readout 2029, "
        "US launch 2027 contingent on accelerated approval."
    ),
    "egfr_readout_timing": (
        "Wk 106 readout is timed from trial enrollment, not drug approval. "
        "Backsolving from the April 2026 wk 34 interim: first-cohort patients "
        "reach wk 106 around September 2027 (egfr_signal_year, modeling early "
        "prescriber anticipation); formal LPLV-based topline analysis around "
        "mid-2028 (egfr_readout_year). The 0.5 partial strength in 2027 reflects "
        "gradual prescriber response to anticipated data."
    ),
    "egfr_scenario_multipliers": (
        "Moderated v2 (1.18 / 1.00 / 0.78) based on: Fabhalta APPLAUSE-IgAN 2yr eGFR data "
        "(Novartis, 2025); Vanrafia ALIGN trial eGFR miss with continued FDA accelerated "
        "approval (FiercePharma, Feb 2026). eGFR is now a class characteristic, not a unique "
        "differentiator."
    ),
    "egfr_scenario_probabilities": (
        "40/40/20 split. Strong proteinuria signal at wk 34 positively correlates with "
        "eventual eGFR benefit; tilts probability toward positive readout outcomes."
    ),
    "probability_of_approval": (
        "0.88 reflects accelerated approval pursuit with positive wk 34 interim. "
        "PoA precedes the wk 106 readout; full-approval conversion uncertainty is captured "
        "implicitly in eGFR scenario share multipliers."
    ),
    "tarpeyo_trajectory": (
        "PLACEHOLDER: 14-quarter S-curve approximation for Bass calibration. "
        "Kyle replaces with actuals from Calliditas 10-Qs (Q1 2022 - Q3 2024) and "
        "Asahi Kasei pharma segment reports (Q4 2024+, post-acquisition Sep 2024)."
    ),
}


# Entries here are non-production placeholders Kyle must replace before final use.
PLACEHOLDERS = {
    "tarpeyo_trajectory",
}
