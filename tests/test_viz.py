"""Tests for visualization-supporting pure functions (no Streamlit context required)."""

import pandas as pd
import pytest

from core.conjoint import (
    compute_drug_utilities,
    get_active_drugs_for_year,
    get_drug_attributes_for_year,
    utilities_to_shares,
)
from data.assumptions import DEFAULTS
from data.competitive_landscape import COMPETITOR_LAUNCH_YEARS, DRUG_ATTRIBUTES
from viz.conjoint_table import compute_conjoint_table_data


def test_conjoint_table_renders_at_default_year():
    """compute_conjoint_table_data returns a populated dataframe at year 2032."""
    df, weights, attr_keys = compute_conjoint_table_data(
        2032, DEFAULTS, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS
    )
    assert isinstance(df, pd.DataFrame)
    assert "Utility" in df.columns
    assert "Share" in df.columns
    # All 11 drugs are active by 2032 (Tarpeyo through Pegcetacoplan).
    assert len(df) == len(COMPETITOR_LAUNCH_YEARS)
    assert len(attr_keys) == 7                       # 7 attribute columns
    assert all(k in df.columns for k in attr_keys)


def test_only_active_drugs_shown_at_2025():
    """At 2025, the table excludes drugs that haven't launched yet."""
    df, _, _ = compute_conjoint_table_data(
        2025, DEFAULTS, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS
    )
    drug_names = {d.lower() for d in df.index}
    # Drugs launched by 2025: tarpeyo (2022), filspari (2023), fabhalta (2024), vanrafia (2025).
    # Voyxact moved to 2026 launch; Atacicept (2026), Povetacicept/Ultomiris (2027),
    # Cemdisiran/Telitacicept/Pegcetacoplan (2028) all excluded.
    assert drug_names == {"tarpeyo", "filspari", "fabhalta", "vanrafia"}
    for excluded in ("voyxact", "atacicept", "povetacicept", "ultomiris",
                     "cemdisiran", "telitacicept", "pegcetacoplan"):
        assert excluded not in drug_names


def test_utility_calculation_matches_internal():
    """The Utility column matches compute_drug_utilities — no double-computation drift."""
    df, weights, _ = compute_conjoint_table_data(
        2032, DEFAULTS, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS
    )
    year_attrs = get_drug_attributes_for_year(2032, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS)
    utilities = compute_drug_utilities(year_attrs, weights)
    for drug_display in df.index:
        drug = drug_display.lower()
        assert df.loc[drug_display, "Utility"] == pytest.approx(utilities[drug])


def test_share_calculation_matches_internal():
    """The Share column matches utilities_to_shares — same softmax allocation used elsewhere."""
    df, weights, _ = compute_conjoint_table_data(
        2032, DEFAULTS, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS
    )
    year_attrs = get_drug_attributes_for_year(2032, DRUG_ATTRIBUTES, COMPETITOR_LAUNCH_YEARS)
    utilities = compute_drug_utilities(year_attrs, weights)
    active = get_active_drugs_for_year(2032, COMPETITOR_LAUNCH_YEARS)
    shares = utilities_to_shares(utilities, DEFAULTS["conjoint"]["logit_lambda"], active)
    for drug_display in df.index:
        drug = drug_display.lower()
        assert df.loc[drug_display, "Share"] == pytest.approx(shares[drug])
