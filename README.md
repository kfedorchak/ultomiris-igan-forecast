# Ultomiris IgAN Forecast — Interactive Prototype

Patient-based US revenue forecast for Ultomiris (ravulizumab) in IgA nephropathy (IgAN), built as a portfolio prototype. The model combines disease epidemiology, Bass diffusion calibrated against real Calliditas-disclosed Tarpeyo uptake, conjoint-based share allocation across an 11-drug competitive set, and a phased I CAN Phase III eGFR-readout scenario tree.

**Live app:** [link added once deployed]

## What the model does

```
Patient Flow ─→ Bass Diffusion ─→ Conjoint Share ─→ Revenue
     ↑              ↑                  ↑              ↑
 Disease Epi   Tarpeyo Fit       Attribute        Stock-and-flow
 + Diagnostic                    Weights +        patient-years
 Expansion                       Drug Scores      × Net price
                                                  × PoA (0.88)
                                                  × eGFR scenario
                                                  (phased 2027/28)
```

Bass models the full IgAN treated market against a stable `total_M = high_risk × market_potential_fraction`, calibrated against 10 quarters of Calliditas-disclosed Tarpeyo US revenue (Q1 2022 – Q2 2024). The conjoint share then allocates each year's new starts to Ultomiris vs 10 competitors across 7 weighted attributes (proteinuria, eGFR, route, dosing, safety, familiarity, payer). eGFR scenario multipliers act on Ultomiris share with a 2027 signal-year partial impact and full impact from the 2028 readout onward.

## Reading the dashboard

The default view is **Risk-adjusted (EV)** — a probability-weighted expected value across the three eGFR scenarios (40% strongly positive / 40% modestly positive / 20% weak-neutral), with revenues multiplied by a 0.88 probability of approval.

The sidebar exposes the six most decision-relevant drivers; the tornado quantifies single-driver sensitivity around the central case. The conjoint table and weights chart make the share-allocation logic fully transparent. Click any drug in the Source-of-Business or Share-of-Treated pills to highlight that drug's trajectory.

For modeling detail, click **Methodology** and **Data sources** in the app header — both render the full markdown specs inline.

## Modeling choices worth flagging

- **Bass on stable class-wide M, not per-drug M.** Prevents negative new starts when competitors launch — share allocation happens downstream, on a class total that doesn't shift with the competitive set.
- **Real Tarpeyo calibration, not synthetic.** `(p, q)` fitted against Calliditas SEC + investor releases; q bound widened to 2.0 because observed specialty-launch imitation exceeded the standard Sultan-Farley-Lehmann range.
- **Phased eGFR impact.** Signal year (2027, partial strength 0.5) reflects prescriber anticipation from the I CAN wk 34 interim; readout year (2028, full impact) is timed off LPLV, not approval date.
- **PoA applied to revenues only.** Patient counts shown are conditional on approval; revenues include the 0.88 PoA multiplier throughout.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
pytest tests/
```

Python 3.11+ recommended. 65/65 tests pass.

## Repository layout

```
app.py                          Streamlit entry point
core/
  bass_model.py                 (p, q, M) Bass fit + projection
  conjoint.py                   7-attribute softmax share allocation
  patient_flow.py               Disease epi + stock-and-flow patient years
  revenue.py                    Forecast orchestrator
  source_of_business.py         5-bucket SoB mix interpolation
data/
  assumptions.py                DEFAULTS dict — all sliders default here
  competitive_landscape.py      11-drug landscape + launch years + attribute scores
  sources.py                    Programmatic citation dictionary
  tarpeyo_trajectory.csv        10 quarters of Calliditas-disclosed revenue
viz/                            Plotly chart builders + formatting
docs/
  methodology.md                Full model methodology (also accessible from app)
  data_sources.md               Per-assumption sourcing with URLs
tests/                          65 tests across all layers
```

## Sources

All assumptions cite to public material: KDIGO 2021/2024 guidelines, AstraZeneca I CAN trial registry materials, Calliditas SEC filings + PR Newswire interim reports, drug labels (Tarpeyo / Filspari / Fabhalta / Vanrafia), and published analyst commentary. See `docs/data_sources.md` for the full per-assumption source list.

No proprietary or confidential data is used.
