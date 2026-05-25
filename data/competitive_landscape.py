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
        "proteinuria_efficacy": 9,     # I CAN trial wk 34 — among the strongest UPCR signals in class
        "egfr_preservation": 7,        # interim; awaiting wk 106 readout
        "route_of_admin": 4,           # IV q8w — better than daily IV (1-2) but worse than oral (9); q8w infrequency is a partial offset
        "dosing_frequency": 8,         # q8w is a meaningful advantage over daily oral therapy (Tarpeyo, Filspari, Fabhalta, Vanrafia)
        "safety_burden": 4,            # REMS for meningococcal infection — serious, requires vaccination
        "mechanism_familiarity": 7,    # carryover prescriber familiarity from Alexion's aHUS/PNH franchise (same molecule)
        "payer_access": 4,             # $450K/yr is a real payer hurdle even with Alexion's nephrology infrastructure
    },
    "tarpeyo": {
        # eGFR 6 -> 7 reflects NefIgArd 2-yr eGFR slope data that drove full
        # FDA approval Dec 2023 (first IgAN drug with confirmed disease-
        # modifying eGFR benefit).
        "proteinuria_efficacy": 6, "egfr_preservation": 7, "route_of_admin": 9,
        "dosing_frequency": 5, "safety_burden": 6, "mechanism_familiarity": 8, "payer_access": 8,
    },
    "filspari": {
        # safety 7 -> 5: Filspari carries REMS for hepatotoxicity and
        # teratogenicity; prior 7 (high = better) didn't reflect this.
        "proteinuria_efficacy": 7, "egfr_preservation": 7, "route_of_admin": 9,
        "dosing_frequency": 6, "safety_burden": 5, "mechanism_familiarity": 7, "payer_access": 7,
    },
    "fabhalta": {
        # dosing 5 -> 4: BID dosing is less convenient than once-daily peers.
        "proteinuria_efficacy": 7, "egfr_preservation": 7, "route_of_admin": 9,
        "dosing_frequency": 4, "safety_burden": 6, "mechanism_familiarity": 6, "payer_access": 6,
    },
    "vanrafia": {
        # eGFR scored at 5 reflecting ALIGN trial miss; commercial position
        # remains strong as "foundational" therapy for broad high-risk population.
        "proteinuria_efficacy": 6, "egfr_preservation": 5, "route_of_admin": 9,
        "dosing_frequency": 6, "safety_burden": 7, "mechanism_familiarity": 7, "payer_access": 7,
    },
    "voyxact": {
        # sibeprenlimab (Otsuka/Visterra); first-in-class APRIL inhibitor.
        # efficacy 7 -> 8 and familiarity 5 -> 6 reflect Phase 3 data maturity;
        # most clinical data of the three APRIL/BAFF drugs in this set.
        "proteinuria_efficacy": 8, "egfr_preservation": 6, "route_of_admin": 7,
        "dosing_frequency": 7, "safety_burden": 7, "mechanism_familiarity": 6, "payer_access": 6,
    },
    "atacicept": {
        # Vera Therapeutics' atacicept; oldest APRIL/BAFF program (originally
        # Merck/Serono) so familiarity 5 -> 6 reflects longest history.
        # dosing 7 -> 6: weekly SC less convenient than monthly SC peers.
        "proteinuria_efficacy": 7, "egfr_preservation": 6, "route_of_admin": 7,
        "dosing_frequency": 6, "safety_burden": 6, "mechanism_familiarity": 6, "payer_access": 6,
    },
    "povetacicept": {
        # Alpine/Vertex povetacicept; newest of the three (Phase 2/3, SC q4w).
        # Less data maturity than Voyxact, less program history than Atacicept.
        "proteinuria_efficacy": 7, "egfr_preservation": 6, "route_of_admin": 7,
        "dosing_frequency": 7, "safety_burden": 6, "mechanism_familiarity": 5, "payer_access": 6,
    },
}
