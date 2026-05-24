"""Dynamic prevalent IgAN patient pool with diagnostic expansion."""

from dataclasses import dataclass


@dataclass
class PatientPool:
    """Snapshot of diagnosed prevalent and high-risk patient counts at a single year."""

    diagnosed_prevalent: float
    high_risk: float


def compute_patient_pool(
    year: int,
    forecast_start_year: int,
    epi_params: dict,
    diagnostic_expansion_rate: float,
) -> PatientPool:
    """Compute diagnosed prevalent + high-risk pool at `year`, with diagnostic expansion and net incidence/outflow."""
    year_offset = year - forecast_start_year

    base_prevalent = (
        epi_params["us_adult_population"]
        * epi_params["diagnosed_prevalence_per_100k"]
        / 100_000
    )

    diagnostic_growth = (1 + diagnostic_expansion_rate) ** year_offset

    net_annual_change = (
        epi_params["us_adult_population"]
        * epi_params["annual_incidence_per_100k"]
        / 100_000
        - base_prevalent
        * (
            epi_params["annual_progression_to_eskd_pct"]
            + epi_params["annual_mortality_pct"]
        )
    )

    diagnosed_prevalent = base_prevalent * diagnostic_growth + net_annual_change * year_offset
    high_risk = diagnosed_prevalent * epi_params["high_risk_pct"]

    return PatientPool(
        diagnosed_prevalent=diagnosed_prevalent,
        high_risk=high_risk,
    )
