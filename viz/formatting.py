"""Currency/percent formatting helpers and the visualization color palette.

Color philosophy (revamped to Alexion brand-aligned palette):
- Alexion Blue is reserved for Ultomiris and for treatment-naive (the "new
  patient" bucket on the SoB chart). It's the only blue that appears anywhere.
- Alexion Red carries "downside" semantics: tornado low side, weak/neutral
  eGFR scenario.
- Everything else is greyscale, with sequential shades when categories need
  to be distinguishable in a stacked plot.
- Diverging palettes (tornado red/green, conjoint heatmap RdYlGn) are kept
  intact because the directional semantics are meaningful.
"""

# ──────────────────────────── brand ────────────────────────────
ALEXION_BLUE = "#273386"
ALEXION_RED = "#C50F23"

ULTOMIRIS_COLOR = ALEXION_BLUE  # Ultomiris uses Alexion blue everywhere

# ──────────────────────────── neutrals ─────────────────────────
GREY_DARK = "#404040"
GREY_MEDIUM = "#808080"
GREY_LIGHT = "#BDBDBD"
GREY_LIGHTEST = "#E0E0E0"

# Consistent dark near-black for all chart titles and section headers.
# Plotly's plotly_white default is #2a3f5f (navy-slate) which can look
# grey-ish next to true-black Streamlit body text — applying this
# explicitly to every fig title keeps the dashboard's typographic color
# uniform.
TITLE_COLOR = "#1F1F1F"

# ──────────────────────────── scenario palette ─────────────────
# Strong = forest green, Modest = neutral grey, Weak = Alexion red.
SCENARIO_COLORS: dict[str, str] = {
    "strongly_positive": "#2E7D32",
    "modestly_positive": GREY_MEDIUM,
    "weak_neutral": ALEXION_RED,
}

# ──────────────────────────── competitive palette ──────────────
# Sequential greys from oldest-launched (lightest) to newest competitor
# (darkest), with Ultomiris in Alexion blue. Ordering matches launch year.
# 10-step grey ramp from #CC down to #33 (10 non-Ultomiris drugs).
COMPETITOR_PALETTE: dict[str, str] = {
    "tarpeyo":       "#CCCCCC",
    "filspari":      "#BBBBBB",
    "fabhalta":      "#AAAAAA",
    "vanrafia":      "#999999",
    "voyxact":       "#888888",
    "atacicept":     "#777777",
    "povetacicept":  "#666666",
    "ultomiris":     ALEXION_BLUE,
    "cemdisiran":    "#555555",
    "telitacicept":  "#444444",
    "pegcetacoplan": "#333333",
}


def fmt_currency(x: float, scale_precision: int | None = None) -> str:
    """Currency with B / M / raw suffix.

    `scale_precision` overrides the default decimals on the scaled value:
    billions default 2 (e.g. $4.82B); millions default 0 (e.g. $825M).
    Pass scale_precision=0 to suppress decimals at every scale.
    """
    if abs(x) >= 1e9:
        p = scale_precision if scale_precision is not None else 2
        return f"${x / 1e9:.{p}f}B"
    if abs(x) >= 1e6:
        p = scale_precision if scale_precision is not None else 0
        return f"${x / 1e6:.{p}f}M"
    return f"${x:,.0f}"


def fmt_percent(x: float, decimals: int = 1) -> str:
    """Percent with configurable decimals (input on 0-1 scale)."""
    return f"{x * 100:.{decimals}f}%"


def fmt_patients(x: float) -> str:
    """Patient counts: thousands separator below 1K, K-suffix above."""
    if abs(x) >= 1000:
        return f"{x / 1000:.1f}K"
    return f"{x:,.0f}"
