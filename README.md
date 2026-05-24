# Ultomiris IgAN Forecast Prototype

Interactive patient-based revenue forecast for Ultomiris (ravulizumab) in IgA nephropathy (IgAN) in the United States. Built around the I CAN Phase III trial's week 106 eGFR readout as one of three scenario dimensions, with mechanism-based source-of-business switching and Tarpeyo-calibrated Bass diffusion against a stable class-wide market potential.

## Installation

```bash
pip install -r requirements.txt
```

Python 3.11+ recommended.

## Run

```bash
streamlit run app.py
```

## Test

```bash
pytest tests/
```

## Architecture

```
Patient Flow ─→ Bass Diffusion ─→ Conjoint Share ─→ Revenue
     ↑              ↑                  ↑              ↑
 Disease Epi   Tarpeyo Fit       Attribute        Stock-and-flow
 + Diagnostic                    Weights +        patient-years
 Expansion                       Drug Scores      × Net price
                                                  × PoA (0.88)
                                                  × eGFR scenario
                                                  (post-readout)
```

Bass models the full IgAN treated market against a stable `total_M = high_risk × market_potential_fraction`. The conjoint share then allocates each year's new starts to Ultomiris. eGFR scenario multipliers act on Ultomiris share only from the readout year (2029) onward.

## Where assumptions live

- `data/assumptions.py` — all default parameters (epi, Bass, conjoint, persistence, pricing, eGFR scenarios, launch timing)
- `data/competitive_landscape.py` — 8 competitor launch years and drug attribute scores
- `data/sources.py` — citation dictionary keyed by assumption
- `data/tarpeyo_trajectory.csv` — quarterly Tarpeyo trajectory used to calibrate Bass `(p, q)`

## REVIEW BEFORE FINAL USE

The following defaults are placeholders pending Kyle's judgment (spec Section 13):

- `data/tarpeyo_trajectory.csv` — placeholder S-curve. Replace with actuals from Calliditas 10-Qs (pre-Sep 2024) and Asahi Kasei pharma segment reports (post-Sep 2024).
- `data/assumptions.py` `conjoint.attribute_weights` — Kyle's prioritization judgment.
- `data/competitive_landscape.py` `DRUG_ATTRIBUTES` — Kyle's read of clinical and commercial data (note: Voyxact and Vanrafia scores reflect v2 additions/adjustments — review against ALIGN, APPLAUSE-IgAN, and sibeprenlimab data).
- `data/assumptions.py` `egfr_readout_scenarios` — probability split (40/40/20) and share multipliers (1.18/1.00/0.78) are moderated v2 values based on class-characteristic evidence.

## Data sources

See `docs/data_sources.md` for full source list with URLs.
