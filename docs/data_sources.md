# Data Sources

Per-assumption sourcing for the Ultomiris IgAN forecast prototype. Programmatic
citations also live in `data/sources.py` under the `SOURCES` dict (keyed by assumption).
Entries here include URLs and reading notes.

## Epidemiology

- **US adult population (258M)**: US Census Bureau 2024 estimate.
- **Diagnosed IgAN prevalence (60/100K)**: Wyatt & Julian, *N Engl J Med* 2013;
  AstraZeneca I CAN trial registry materials cite 560K diagnosed IgAN patients across
  US + EU5 + Japan.
- **Annual incidence (1.5/100K)**: KDIGO 2021 Clinical Practice Guideline for
  Glomerular Diseases.
- **High-risk fraction (35%)**: KDIGO 2021 — patients with proteinuria >1 g/day and/or
  declining eGFR are classified as high-risk and are candidates for targeted add-on
  therapy beyond foundational RAAS inhibition.
- **Annual progression to ESKD (5%)**: Pitcher *et al.*, *CJASN* 2023, IgAN natural-
  history meta-analysis. Range 3–8% depending on baseline severity.
- **Annual all-cause mortality (1.5%)**: KDIGO 2021 reference data; broadly consistent
  with registry-based IgAN cohorts.
- **Diagnostic expansion (4%/yr default; 1–8% slider range)**: Consensus from
  Tarpeyo/Filspari/Fabhalta investor commentary regarding underdiagnosis and increasing
  rates of routine urinalysis screening + nephrologist referral. Tightened from the
  initial -2%–12% range during the diagnostic-expansion audit (Step ~50).

## Bass diffusion calibration

- **Tarpeyo trajectory (Q1 2022 – Q2 2024)**: 10 quarters of Calliditas-disclosed US
  net revenue. Sources:
  - [Q1 2022 interim](https://www.prnewswire.com/news-releases/calliditas-therapeutics-interim-report-q1-2022-301549804.html) — $1.9M (launch quarter, late Jan)
  - [Q2 2022 interim (SEC 6-K)](https://www.sec.gov/Archives/edgar/data/0001795579/000141057822002673/calt-20220630xex99d1.htm) — $6.6M
  - [Q3 2022 interim](https://www.prnewswire.com/news-releases/calliditas-therapeutics-interim-report-q3-2022-301676615.html) — $12.1M
  - [FY2022 / Q4 2022 (SEC 6-K)](https://www.sec.gov/Archives/edgar/data/0001795579/000110465923024759/tm237694d1_ex99-1.htm) — $16.1M
  - [Q1 2023 interim](https://www.biospace.com/calliditas-therapeutics-interim-report-q1-2023) — $17.8M
  - [Q2 2023 interim](https://www.prnewswire.com/news-releases/interim-report-q2-2023-calliditas-therapeutics-301903279.html) — $24.7M
  - [Q3 2023 interim](https://www.prnewswire.com/news-releases/calliditas-interim-report-january--september-2023-301979524.html) — $26.3M
  - [Q4 2023 preliminary](https://www.prnewswire.com/news-releases/calliditas-therapeutics-provides-business-update-ahead-of-jp-morgan-conference-302028169.html) and [FY2023 release](https://www.prnewswire.com/news-releases/calliditas-year-end-report-january--december-2023-302066986.html) — $32.8M (SEK 347.3M ÷ ~10.6)
  - [Q1 2024 interim](https://www.prnewswire.com/news-releases/calliditas-q1-report-january--march-2024-302153828.html) — \$26.6M (carried ~\$4.7M Change Healthcare cyberattack GTN drag)
  - [Q2 2024 interim](https://www.prnewswire.com/news-releases/calliditas-interim-report-january-to-june-2024-302220664.html) — $46.3M (record quarter, +90% YoY)
- **Patient conversion**: `estimated_patients = revenue_musd × 1e6 / 15000`, where
  \$15K is the midpoint of Tarpeyo's annual WAC range (\$14.5K at 2022 launch, raised to
  ~\$16K by 2024).
- **Post-Sep-2024 omitted**: Calliditas was acquired by Asahi Kasei (close Sep 4 2024,
  delist Oct 10 2024). No standalone Calliditas Q3 2024 interim was filed. Subsequent
  Asahi Kasei pharma-segment disclosures don't break out Tarpeyo at a quarterly USD
  cadence that reconciles cleanly with the prior trajectory; including those quarters
  would corrupt the Bass fit.
- **Bass fallback (p=0.012, q=0.42)**: Sultan, Farley, Lehmann (1990) meta-analysis of
  Bass fits across consumer + pharma launches; median range p ≈ 0.01–0.03, q ≈ 0.3–0.5.
- **Bounds rationale**: `p ∈ [0.0001, 0.10]`, `q ∈ [0.05, 2.0]` — wider than spec's
  original `q_max=1.0` because observed Tarpeyo uptake exhibits q > 1.0. Specialty
  drugs with strong clinical evidence and few launch-era alternatives can produce high
  imitation.
- **Tarpeyo M (27,000)**: 2022 high-risk pool (~54,000) × 50% first-mover penetration.
  See `market_potential_penetration_assumptions` in `data/sources.py`.
- **`p_ultomiris_adjustment` (0.7)**: Analyst consensus 0.6–0.8 multiplier for IV
  biologic launches into oral-dominated markets. Reflects REMS + IV q8w friction.

## Competitive landscape

- **Drug attributes**: Composite of trial readouts (proteinuria, eGFR), label features
  (route, dosing, REMS), and analyst commentary on payer positioning. References:
  - **KDIGO 2024 IgAN guideline update** — drives the weighted-attribute framework
    (proteinuria primary endpoint, eGFR slope as hard endpoint).
  - **Tarpeyo NefIgArd 2-yr eGFR data** — Calliditas readout supporting the December
    2023 full FDA approval; eGFR slope benefit drives Tarpeyo's eGFR=7 score.
  - **Filspari (sparsentan) USPI** — Travere label documents REMS for hepatotoxicity
    and teratogenicity (drives safety=5 score).
  - **Fabhalta (iptacopan) USPI** — Novartis label; BID dosing supports
    dosing_frequency=4.
  - **Vanrafia (atrasentan) ALIGN trial** — Novartis Phase 3 missed primary eGFR
    endpoint; FDA still granted accelerated approval. Drives eGFR=5 score.
  - **Voyxact (sibeprenlimab) VISIONARY trial** — Otsuka/Visterra Phase 3 readout
    supports efficacy=8 and familiarity=6 scores.
- **Launch years**: best public-disclosure estimates as of mid-2026; see
  `data/competitive_landscape.py` `COMPETITOR_LAUNCH_YEARS` for the table.
- **Drug veteran cohorts (sum = 28,500 at end-2026)**: Issuer-disclosed end-2024 counts
  extrapolated forward with continued growth through end-2026:
  - Tarpeyo 13K (from 7.5K end-2024, Asahi Kasei segment data)
  - Filspari 8K (from 4.5K end-2024, Travere Q3'24 10-Q)
  - Fabhalta 5K (from ~2K end-2024, Novartis early launch)
  - Vanrafia 1.5K (2025 launch)
  - Voyxact + Atacicept 500 each (2026 launches; mid-2026 onward)

## Pricing

- **Net price per patient-year ($450K)**: Third-party analyst estimates and ICER
  complement-inhibitor reports; Ultomiris's PNH/aHUS price points adjusted for the IgAN
  payer mix.
- **Annual price growth (2%)**: Specialty biologic WAC growth trend.

## eGFR readout scenarios

- **Probability split (40/40/20)**: Strong proteinuria signal at I CAN wk 34 positively
  correlates with eventual eGFR benefit; tilts probability toward positive readout
  outcomes.
- **Multipliers (1.18 / 1.00 / 0.78)**: Moderated v2 values reflecting evidence that
  eGFR is becoming a class characteristic:
  - Fabhalta APPLAUSE-IgAN 2-yr eGFR data (Novartis 2025)
  - Vanrafia ALIGN trial eGFR miss with continued FDA accelerated approval
    (FiercePharma, Feb 2026)
- **Readout timing**: I CAN trial wk 106 milestone is timed from trial enrollment, not
  from drug approval. Signal year 2027 (first-cohort wk 106, prescriber anticipation);
  readout year 2028 (LPLV-based topline). See *eGFR Readout Timing and Phased Scenario
  Impact* in methodology.md.
- **Probability of approval (0.88)**: Reflects accelerated-approval pursuit with a
  positive wk 34 interim. Full-approval conversion uncertainty is captured implicitly
  in the eGFR scenario share multipliers.

## Persistence

- **Year 1 (75%) / Year 2+ (85%) retention**: Chronic biologic real-world persistence
  benchmarks from PNH/aHUS Ultomiris analogs and similar specialty biologic launches.

## Source-of-business mix

- **Anchor mixes (`EARLY_MIX`, `MATURE_MIX`)**: anchored to mechanism-class
  share-of-prescribing patterns observed in the early-Tarpeyo-era and projected
  post-eGFR-readout mature-class environments. Linear interpolation over 8 years
  post-Ultomiris launch.

## Files cross-reference

| Concept | Data file | Methodology section |
|---|---|---|
| Epi parameters | `data/assumptions.py::DEFAULTS["epi"]` | Layer 1 |
| Tarpeyo trajectory | `data/tarpeyo_trajectory.csv` | Layer 2 |
| Bass parameters | `data/assumptions.py::DEFAULTS["bass"]` | Layer 2 |
| Drug attributes | `data/competitive_landscape.py` | Layer 3 |
| Conjoint weights | `data/assumptions.py::DEFAULTS["conjoint"]` | Layer 3 |
| Persistence | `data/assumptions.py::DEFAULTS["persistence"]` | Layer 4 |
| Veteran cohorts | `data/assumptions.py::DRUG_VETERAN_COHORTS_2027` | Layer 4 |
| eGFR scenarios | `data/assumptions.py::DEFAULTS["egfr_readout_scenarios"]` | eGFR Readout Timing |
| SoB mix | `core/source_of_business.py::EARLY_MIX, MATURE_MIX` | Source-of-business mix |
| Pricing | `data/assumptions.py::DEFAULTS["pricing"]` | Revenue composition |
