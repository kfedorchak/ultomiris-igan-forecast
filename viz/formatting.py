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
COMPETITOR_PALETTE: dict[str, str] = {
    "tarpeyo":      "#BFBFBF",
    "filspari":     "#A6A6A6",
    "fabhalta":     "#8C8C8C",
    "vanrafia":     "#737373",
    "voyxact":      "#595959",
    "atacicept":    "#404040",
    "povetacicept": "#2A2A2A",
    "ultomiris":    ALEXION_BLUE,
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
