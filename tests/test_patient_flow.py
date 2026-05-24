"""Tests for core.patient_flow."""

import pytest

from core.patient_flow import PatientPool, compute_patient_pool
from data.assumptions import DEFAULTS


def test_base_year_matches_simple_formula():
    """At year_offset=0, diagnosed_prevalent = pop x prev/100k (no expansion, no flow)."""
    epi = DEFAULTS["epi"]
    pool = compute_patient_pool(2026, 2026, epi, 0.04)
    expected = epi["us_adult_population"] * epi["diagnosed_prevalence_per_100k"] / 100_000
    assert pool.diagnosed_prevalent == pytest.approx(expected)
    assert pool.high_risk == pytest.approx(expected * epi["high_risk_pct"])


def test_diagnostic_expansion_compounds_correctly():
    """With incidence tuned to balance outflows, growth is pure (1+r)^year_offset."""
    # 258M x 3.9/100k = 154,800 x 0.065 -> net_annual_change = 0
    epi = dict(DEFAULTS["epi"], annual_incidence_per_100k=3.9)
    base = epi["us_adult_population"] * epi["diagnosed_prevalence_per_100k"] / 100_000
    pool = compute_patient_pool(2030, 2026, epi, 0.04)
    assert pool.diagnosed_prevalent == pytest.approx(base * (1.04 ** 4), rel=1e-9)


def test_high_risk_pct_scales_proportionally():
    """high_risk = diagnosed_prevalent x high_risk_pct."""
    epi = dict(DEFAULTS["epi"], high_risk_pct=0.40)
    pool = compute_patient_pool(2027, 2026, epi, 0.04)
    assert pool.high_risk == pytest.approx(pool.diagnosed_prevalent * 0.40)


def test_2027_sanity_bound():
    """Spec sanity: at default params in 2027, high_risk lands in 54-60K."""
    pool = compute_patient_pool(
        year=2027,
        forecast_start_year=DEFAULTS["launch"]["forecast_start_year"],
        epi_params=DEFAULTS["epi"],
        diagnostic_expansion_rate=DEFAULTS["diagnostic_expansion"]["annual_growth_rate"],
    )
    assert 54_000 <= pool.high_risk <= 60_000


def test_patient_pool_dataclass_shape():
    """PatientPool exposes diagnosed_prevalent and high_risk."""
    pool = compute_patient_pool(2026, 2026, DEFAULTS["epi"], 0.04)
    assert isinstance(pool, PatientPool)
    assert hasattr(pool, "diagnosed_prevalent")
    assert hasattr(pool, "high_risk")
