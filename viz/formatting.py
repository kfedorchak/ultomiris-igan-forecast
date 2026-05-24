"""Currency/percent formatting helpers and the visualization color palette."""


ULTOMIRIS_COLOR = "#0066B3"  # Alexion blue, reserved for Ultomiris across all charts

SCENARIO_COLORS: dict[str, str] = {
    "strongly_positive": "#2CA02C",   # green
    "modestly_positive": "#7F7F7F",   # grey
    "weak_neutral": "#D62728",        # red
}

COMPETITOR_PALETTE: dict[str, str] = {
    "tarpeyo": "#8C564B",
    "filspari": "#E377C2",
    "fabhalta": "#9467BD",
    "vanrafia": "#17BECF",
    "voyxact": "#BCBD22",
    "atacicept": "#FF7F0E",
    "povetacicept": "#A0A0A0",
    "ultomiris": ULTOMIRIS_COLOR,
}


def fmt_currency(x: float) -> str:
    """Currency with B / M / raw suffix."""
    if abs(x) >= 1e9:
        return f"${x / 1e9:.2f}B"
    if abs(x) >= 1e6:
        return f"${x / 1e6:.0f}M"
    return f"${x:,.0f}"


def fmt_percent(x: float, decimals: int = 1) -> str:
    """Percent with configurable decimals (input on 0-1 scale)."""
    return f"{x * 100:.{decimals}f}%"


def fmt_patients(x: float) -> str:
    """Patient counts: thousands separator below 1K, K-suffix above."""
    if abs(x) >= 1000:
        return f"{x / 1000:.1f}K"
    return f"{x:,.0f}"
