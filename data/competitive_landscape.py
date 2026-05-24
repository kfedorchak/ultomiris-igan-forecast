"""Competitor launch years and drug attribute scores for conjoint share.

Scores are 1-10 with 10 = best. Each score should be defensible from public
data. Kyle reviews these against ALIGN, APPLAUSE-IgAN, sibeprenlimab, and
other clinical readouts before final use.
"""

COMPETITOR_LAUNCH_YEARS = {
    "tarpeyo": 2022,
    "filspari": 2023,
    "fabhalta": 2024,
    "vanrafia": 2025,
    "voyxact": 2025,            # sibeprenlimab; Otsuka; first-in-class APRIL inhibitor
    "atacicept": 2026,
    "povetacicept": 2027,
    "ultomiris": 2027,
}

DRUG_ATTRIBUTES = {
    "ultomiris": {
        "proteinuria_efficacy": 8,
        "egfr_preservation": 7,        # interim; awaiting wk 106 readout
        "route_of_admin": 3,           # IV q8w
        "dosing_frequency": 7,         # q8w beats oral daily
        "safety_burden": 5,            # REMS for meningococcal infection
        "mechanism_familiarity": 6,
        "payer_access": 4,             # high-priced biologic
    },
    "tarpeyo": {
        "proteinuria_efficacy": 6, "egfr_preservation": 6, "route_of_admin": 9,
        "dosing_frequency": 5, "safety_burden": 6, "mechanism_familiarity": 8, "payer_access": 8,
    },
    "filspari": {
        "proteinuria_efficacy": 7, "egfr_preservation": 7, "route_of_admin": 9,
        "dosing_frequency": 6, "safety_burden": 7, "mechanism_familiarity": 7, "payer_access": 7,
    },
    "fabhalta": {
        "proteinuria_efficacy": 7, "egfr_preservation": 7, "route_of_admin": 9,
        "dosing_frequency": 5, "safety_burden": 6, "mechanism_familiarity": 6, "payer_access": 6,
    },
    "vanrafia": {
        # eGFR scored at 5 reflecting ALIGN trial miss; commercial position
        # remains strong as "foundational" therapy for broad high-risk population.
        "proteinuria_efficacy": 6, "egfr_preservation": 5, "route_of_admin": 9,
        "dosing_frequency": 6, "safety_burden": 7, "mechanism_familiarity": 7, "payer_access": 7,
    },
    "voyxact": {
        # sibeprenlimab (Otsuka/Visterra); first-in-class APRIL inhibitor.
        "proteinuria_efficacy": 7, "egfr_preservation": 6, "route_of_admin": 7,
        "dosing_frequency": 7, "safety_burden": 7, "mechanism_familiarity": 5, "payer_access": 6,
    },
    "atacicept": {
        "proteinuria_efficacy": 7, "egfr_preservation": 6, "route_of_admin": 7,
        "dosing_frequency": 7, "safety_burden": 6, "mechanism_familiarity": 5, "payer_access": 6,
    },
    "povetacicept": {
        "proteinuria_efficacy": 7, "egfr_preservation": 6, "route_of_admin": 7,
        "dosing_frequency": 7, "safety_burden": 6, "mechanism_familiarity": 5, "payer_access": 6,
    },
}
