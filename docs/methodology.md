# Methodology

Patient-based US revenue forecast for Ultomiris (ravulizumab) in IgA nephropathy. The
model produces a 10-year forecast (2026–2035) under three eGFR readout scenarios plus a
probability-weighted "Risk-adjusted" view. Eleven targeted IgAN drugs compete for share;
Ultomiris launches in 2027.

## Layer 1 — Patient pool

`core.patient_flow.compute_patient_pool` returns the diagnosed-prevalent IgAN population
and the high-risk subset at any forecast year. Inputs (`DEFAULTS["epi"]`):

| Parameter | Default | Source |
|---|---|---|
| US adult population | 258M | US Census 2024 |
| Diagnosed IgAN per 100K | 60 | Wyatt & Julian 2013; AZ I CAN registry |
| Annual incidence per 100K | 1.5 | KDIGO 2021 |
| High-risk fraction | 0.35 | KDIGO 2021 (proteinuria >1g/day or declining eGFR) |
| Annual progression to ESKD | 5% | Pitcher CJASN 2023 |
| Annual all-cause mortality | 1.5% | KDIGO 2021 |

Forward dynamics: `diagnosed(t) = base × (1+r)^t + net_annual_change × t`, where `r` is
diagnostic expansion (default **4%/yr**) and `net_annual_change` is incidence in minus
ESKD/mortality out. High-risk = diagnosed × 35%. By 2032 the model produces ~55K
high-risk patients (Gate #1 sanity bound: 54-60K).

## Layer 2 — Class-wide adoption (Bass diffusion)

`core.bass_model.bass_cumulative_adoption` evaluates the closed-form Bass curve. The
fitted `(p, q)` come from `core.bass_model.fit_bass_to_tarpeyo`, which calibrates against
**actual Calliditas-disclosed Tarpeyo US quarterly revenue from Q1 2022 through Q2 2024**
(10 quarters; see `data/tarpeyo_trajectory.csv` and the matching `sources.py` entry).
The fit is performed against `TARPEYO_MARKET_POTENTIAL_2022 = 27,000`, defined as 50% of
the 2022 high-risk pool — a first-mover penetration ceiling for the single-mechanism
Tarpeyo-alone era.

At default parameters the fit lands at **p ≈ 0.050, q ≈ 1.564** within bounds
`p ∈ [0.0001, 0.10]` and `q ∈ [0.05, 2.0]`. The bounds were widened from the spec's
original `q_max = 1.0` because real-world Tarpeyo uptake exhibits genuinely high
imitation behavior; specialty IgAN drugs with strong clinical evidence and limited
launch-era alternatives can produce `q > 1.0`. Fallback `(p=0.012, q=0.42)` engages on
convergence failure or bound-edge fits.

Class-wide new starts per forecast year (`compute_class_new_starts_per_year`) evaluate
Bass against a **stable, share-independent** `total_M = high_risk_pool(year) ×
market_potential_fraction`. `market_potential_fraction` defaults to **0.60** — the peak
fraction of high-risk patients treated with any targeted therapy in the mature 8-drug
class era — higher than Tarpeyo's 50% first-mover ceiling because diagnostic expansion,
KDIGO guideline evolution, and class diversification all expand the treatable population
over time.

This Risk-#2-aware design — single Bass on stable M, share-allocated downstream —
prevents the per-drug new-starts series from going negative when a new competitor
launches and Ultomiris's share drops. Pre-Risk-#2 designs used `cumulative_treated(t) −
cumulative_treated(t−1)` with M itself share-adjusted, which could produce negative
deltas around launch years. The current implementation logs a warning if any year's
class-wide delta is negative (would indicate a deeper bug — pool shrinking is the only
legitimate cause).

`p_ultomiris_adjustment` (default **0.70**) multiplies the fitted `p` only, modeling
Ultomiris's slower individual adoption due to IV + REMS friction relative to Tarpeyo's
oral self-administered profile. `q_fit` is used directly.

## Layer 3 — Per-drug share allocation (conjoint)

`core.conjoint.compute_drug_utilities` produces a weighted score per drug:

```
utility_d = Σ_a (attribute_weight[a] × drug_attributes[d][a])
```

Attribute weights post-audit (sum to 1.00):

| Attribute | Weight | Notes |
|---|---|---|
| Proteinuria efficacy | 0.20 | Primary endpoint for regulatory + prescribing |
| eGFR preservation | 0.18 | Hard long-term endpoint; KDIGO 2024 emphasis |
| Route of admin | 0.15 | Reduced from 0.18 (was overweighting Ultomiris IV penalty) |
| Dosing frequency | 0.10 | |
| Safety burden | 0.13 | Multiple drugs carry REMS |
| Mechanism familiarity | 0.07 | |
| Payer access | 0.17 | Reflects $450K/yr biologic access reality |

Each drug's scores are tuned against published trial and label data. Notable revisions
during the audit (Step 20):

- **Filspari safety 7 → 5**: Filspari carries a REMS for hepatotoxicity and
  teratogenicity that prior scoring missed
- **Tarpeyo eGFR 6 → 7**: NefIgArd 2-yr eGFR slope data drove the December 2023 full FDA
  approval (first IgAN drug with confirmed disease-modifying benefit)
- **Ultomiris proteinuria 8 → 9, route 3 → 4, safety 5 → 4, payer 5 → 4**: stronger
  efficacy signal, q8w infrequency partially offsets IV burden, REMS and price
  realities recognized
- **APRIL/BAFF differentiation**: Voyxact, Atacicept, and Povetacicept were previously
  scored identically; now differentiated on data maturity, program history, and dosing
  frequency

### Asymptotic attribute maturation

Three attributes evolve post-launch via `core.conjoint.get_drug_attributes_for_year`:

```
boost(t) = max_boost × (1 − exp(−years_since_launch / tau))
```

| Attribute | max_boost | tau (yr) | Rationale |
|---|---|---|---|
| Mechanism familiarity | 2.0 | 3.0 | Prescribers learn fast |
| Safety burden | 1.5 | 4.0 | Registry data matures over years |
| Payer access | 1.0 | 5.0 | Formulary cycles are slow |

Scores cap at 10. Other attributes (efficacy, route, dosing) are fixed by molecular
properties and don't mature. Sigmoid or logistic would be the natural refinement if a
learning-curve inflection becomes empirically observable.

### Softmax → share

`utilities_to_shares` applies a softmax over drugs active at the given year:

```
share_d(t) = exp(λ × utility_d(t)) / Σ_active exp(λ × utility(t))
```

`logit_lambda` defaults to **0.5**. At a typical 11-drug active year with the
post-audit weights and scores, Ultomiris share-of-new-starts lands at **~7.2%**. The
original spec's Gate #6 cited 8-12% based on an earlier 8-drug landscape; with the
expanded competitive set (Tier 3 of the share audit added cemdisiran+pozelimab,
telitacicept, and pegcetacoplan), the natural Ultomiris share dropped about 2pp. The
8-12% bound should be revised to roughly **6-8%** for the 11-drug landscape.

## Layer 4 — Stock-and-flow with persistence

`core.revenue.compute_treated_stock` ages cohorts discretely:

- Year of start (Y): full count, no aging
- Year Y+1: × `year_1_persistence` (default **0.75**)
- Year Y+2 onward: × `year_2plus_persistence` each year (default **0.85**)

Each year's active stock = sum of surviving cohorts. The same persistence schedule
applies to each drug separately when computing per-drug stocks.

### Veteran cohorts

Pre-Ultomiris-launch patients on competitor drugs are seeded explicitly via
`DRUG_VETERAN_COHORTS_2027` (sum = `CLASS_TREATED_AT_ULTOMIRIS_LAUNCH = 28,500`):

| Drug | Veterans at end-2026 |
|---|---|
| Tarpeyo | 13,000 |
| Filspari | 8,000 |
| Fabhalta | 5,000 |
| Vanrafia | 1,500 |
| Voyxact / Atacicept | 500 each |
| Povetacicept / Ultomiris / 3 × 2028 launches | 0 |

These were calibrated against end-2024 issuer disclosures (Tarpeyo 7.5K, Filspari 4.5K,
Fabhalta 2K) extrapolated forward with continued growth through end-2026. Veterans are
seeded at `forecast_start_year` (= 2026) inside `compute_treated_stock` via the
`veteran_cohort` argument and decay at `year_2plus_persistence` thereafter (they're
already past Y1).

## eGFR Readout Timing and Phased Scenario Impact

The eGFR readout drives the scenario multiplier mechanism, but the multiplier is not
applied as a single step at one year. The wk 106 readout is timed from trial enrollment
(not drug approval), so it does not align cleanly with the US launch year. Backsolving
from the AZ I CAN trial's April 2026 wk 34 interim readout:

- First-cohort patients reach wk 106 around **September 2027** — this is the
  `egfr_signal_year`. By this point investigators see enough data to discuss it at
  congresses, and prescribers begin to anticipate the formal readout.
- Formal LPLV-based topline analysis lands around **mid-2028** — this is the
  `egfr_readout_year`. This is when the full data response materializes in commercial
  behavior.

The model applies a phased multiplier in `core.revenue.get_scenario_multiplier`:

| Year window | Multiplier |
|---|---|
| Pre-signal (< 2027) | 1.0 (no impact) |
| Signal year (2027) | `1.0 + egfr_signal_partial_strength × (full_multiplier − 1.0)` |
| Readout year onward (≥ 2028) | `full_multiplier` |

`egfr_signal_partial_strength` (default **0.5**) parameterizes the anticipation strength
in the signal year.

### Scenario probabilities and multipliers

The three eGFR readout scenarios (40/40/20 probability split):

| Scenario | Probability | `share_multiplier` |
|---|---|---|
| Strongly positive | 0.40 | 1.18 |
| Modestly positive | 0.40 | 1.00 |
| Weak / neutral | 0.20 | 0.78 |

Moderated v2 values: a strongly positive eGFR readout *helps* Ultomiris but doesn't
make it uniquely differentiated (Fabhalta showed positive eGFR data in APPLAUSE-IgAN;
eGFR is becoming a class characteristic). A weak readout hurts but doesn't collapse the
asset (Vanrafia missed its Phase 3 eGFR endpoint and still received accelerated approval).

Inside `compute_new_starts_per_year`, when the multiplier ≠ 1.0 in a given year, all
active drug shares are renormalized so they still sum to 1.0 — when Ultomiris is
boosted, competitor shares decrease proportionally (zero-sum). Renormalization factor:
`1 + ultomiris_raw_share × (multiplier − 1)`.

**Probability of approval** is applied as a uniform `0.88` multiplier to all scenario
revenues and the expected value, representing accelerated-approval pursuit with the
positive wk 34 interim. PoA precedes the wk 106 readout; full-approval conversion
uncertainty is captured implicitly in the scenario multipliers.

## Source-of-business mix

`core.source_of_business.source_of_business_by_year` linearly interpolates between two
mechanism-based anchor mixes:

| Bucket | Year-0 (KOL adopter) | Year-8+ (mature) |
|---|---|---|
| Treatment naive | 0.55 | 0.35 |
| Switch from corticosteroid (Tarpeyo) | 0.13 | 0.16 |
| Switch from endothelin (Filspari, Vanrafia) | 0.11 | 0.16 |
| Switch from oral complement (Fabhalta) | 0.05 | 0.08 |
| Switch from APRIL/BAFF (Voyxact, Atacicept, Povetacicept) | 0.16 | 0.26 |

The blend at year *t* uses `weight = min(t / 8, 1)` and produces a smooth shift over 8
years post-Ultomiris-launch. Sigmoid would be the natural refinement if a learning
inflection becomes observable. Buckets sum to 1.0 after defensive normalization. Note
that the original v2 `addon_to_existing` bucket was removed and redistributed
proportionally across the four switch categories — see *Combination Targeted Therapy Not
Modeled* below for the rationale.

## Combination Targeted Therapy Not Modeled

Combination targeted therapy is not modeled in v2. Patients who would adopt Ultomiris as
an addon to existing targeted therapy are reclassified as switches from that therapy
class, which better reflects real-world prescribing patterns for high-burden IV biologics
in IgAN. Practically, payer access and clinical guideline support for layering a
high-cost C5 inhibitor on top of an already-approved targeted IgAN therapy is limited:
KDIGO 2024 recommends sequential rather than concurrent escalation, and US payer
authorization for two simultaneous targeted IgAN therapies remains rare in the absence
of compelling combination trial data.

Operationally, the v1 addon-to-existing bucket (which carried 0.15–0.17 of new Ultomiris
starts across the forecast horizon) has been redistributed proportionally across the
four `switch_from_*` categories in `core/source_of_business.py`. Each switch category
receives `original + addon × (original / total_switches)`, preserving the relative
weights of the mechanism classes. `treatment_naive` is unchanged. Both `EARLY_MIX` and
`MATURE_MIX` sum to 1.00 after redistribution.

This simplification also resolves the stacked-bar / stock-of-treated double-counting
problem that the v1 addon bucket created: an addon patient appears in both Ultomiris's
stock AND the source drug's stock, which the SoB stacked bar could not honestly
represent. With addon removed, the SoB chart now sums to 100% with five mutually-exclusive
buckets, all of which represent net flows that the Share of Treated chart's stock
mechanics can accommodate (a switch is an outflow from the source drug + an inflow to
Ultomiris, conceptually consistent even if v2 doesn't actually track the cross-drug
outflow — see *Scope of Patient-Flow Modeling* below).

## Scope of Patient-Flow Modeling

The model uses three patient-flow constructs that operate at different levels of
abstraction. The first two are mathematically consistent with each other; the third is
descriptive only.

1. **Class-wide new starts are mathematically consistent with aggregate stock-and-flow.**
   A single Bass diffusion curve on `total_M = high_risk_pool × market_potential_fraction`
   produces class-wide new starts per year. Allocating those new starts across the eleven
   drugs via the time-varying conjoint share (and aging each drug's cohorts through the
   standard persistence schedule) produces per-drug stocks whose sum exactly equals the
   class-wide active stock shown on the funnel's "On targeted IgAN therapy" stage.
   Mathematically: `sum_d (Bass_class(t) × share_d(t)) = Bass_class(t)`, and persistence
   applies linearly to each cohort.

2. **Cross-drug switching attribution is descriptive only.** The Source of Business
   function parameterizes the origin mix of a new Ultomiris patient (treatment-naive,
   switched from a corticosteroid, switched from an endothelin antagonist, switched from
   an oral complement inhibitor, switched from an APRIL/BAFF agent). These switch buckets
   are not actually driving corresponding outflows from the source drug's stock. A
   "switch_from_corticosteroid" bucket reporting that 9% of Ultomiris's 2030 new starts
   switched from Tarpeyo does **not** mean Tarpeyo's 2030 stock in the Share of Treated
   chart decreases by that count. The two charts are decomposing different things. The
   SoB attribution is intended as a strategic-narrative input for commercial messaging
   ("where do our new patients come from?") rather than an internally consistent flow
   account.

3. **The natural extension is a multi-state Markov transition framework.** Each drug
   becomes a state, with a transition probability matrix governing patient movement
   between states (and an absorbing state for discontinuation). The class-wide stock
   evolution would then be `s(t+1) = T × s(t) + new_naive(t) × π_intake`, where `T` is
   the inter-drug transition matrix and `π_intake` is the share of class-wide naive new
   starts each drug captures. This formulation would unify SoB attribution and
   stock-derived shares into a single internally consistent model. The cost is
   substantial — transition matrix calibration requires switching-rate parameters per
   drug pair, additional clinical-judgment inputs, and a much larger validation surface.
   For the v2 prototype, this extension was scoped out: the dashboard's strategic
   questions (peak revenue, scenario sensitivity, share dynamics) are well-served by the
   simpler attribution-only model, and the inconsistency between the SoB and Share charts
   is acknowledged in this document and surfaced in the chart titles themselves
   ("Descriptive Attribution" vs. "Stock-Derived").

## Revenue composition

`core.revenue.compute_yearly_revenue` composes per-scenario revenues:

```
revenue_d,scenario(y) = stock_d,scenario(y) × price(y) × probability_of_approval
price(y) = net_price_per_patient_year × (1 + annual_price_growth)^(y − launch_year)
EV(y) = Σ_scenarios prob × revenue(y)
```

Default `net_price_per_patient_year = $450,000`; `annual_price_growth = 2%`; `PoA = 0.88`.

## Tornado sensitivity

`viz.tornado.build_tornado_chart` perturbs each of six drivers to its low/high bound,
re-runs the full forecast, and reports the delta in **cumulative EV revenue across the
forecast horizon** (not point-in-time). The cumulative metric eliminates an artifact
that fixed-year tornadoes had: year 2032 sits at the base-case peak under default
parameters, so faster-ramp scenarios (e.g. lower IV/REMS friction) would appear to
*reduce* revenue because their stock had aged past the haircut threshold by 2032.
Cumulative captures the full ramp-speed benefit and produces directionally clean
sensitivities. Bounds were widened beyond the spec's original slider ranges to represent
literature-extreme stress tests; diagnostic expansion bound was subsequently tightened
to 0.01–0.08 (from the originally proposed -0.02–0.12) after audit, because compounded
negative growth had no real-world driver and the upper bound exceeded clinical
plausibility.

## Calibration notes and known limitations

- **Gate #6 floor**: needs revision from 8-12% to ~6-8% for the 11-drug landscape (Tier
  3 of the share audit added cemdisiran+pozelimab, telitacicept, pegcetacoplan;
  Ultomiris share-of-new-starts now lands at ~7.2% with the expanded set).
- **Tarpeyo trajectory**: 10 quarters of Calliditas-disclosed actuals (Q1 2022 – Q2
  2024). Post-Sep-2024 quarters are unreliable due to Asahi Kasei consolidation and
  inconsistent segment-level disclosures. Bass fit is calibrated on the Calliditas-era
  data only.
- **Veteran cohorts**: `DRUG_VETERAN_COHORTS_2027` is an estimate built up from
  end-2024 issuer-disclosed counts plus continued-growth assumptions through end-2026.
  Subject to update when 2025/2026 actuals are reported.
- **Drug attribute scores**: tuned against published trial readouts and label features.
  Specific Phase 3 readouts (Voyxact VISIONARY, Vanrafia ALIGN, Atacicept ORIGIN,
  Povetacicept RAINIER) can shift scores materially when fully published.
- **Combination therapy and inter-drug switching**: not modeled (see *Scope* and
  *Combination* sections above).
- **Patient pool dynamics**: linear net flow on a compounding diagnostic base. Real
  epidemiology is more complex (age-dependent incidence, ESKD progression conditional
  on therapy class, etc.) but well-scoped for a 10-year forecast.

## Future improvements

The v2 prototype covers the strategic-decision questions (peak revenue, scenario
sensitivity, share dynamics, source-of-business attribution) but several substantive
refinements would strengthen accuracy, defensibility, and granularity. Grouped by area:

**Model structure**

- **Multi-state Markov transition framework** for inter-drug switching. Each drug
  becomes a state with a transition probability matrix; would unify the SoB attribution
  and stock-derived shares into a single internally consistent model. See *Scope of
  Patient-Flow Modeling* above for the trade-offs.
- **Semi-Markov / patient-level discrete-event simulation**. Track individual patients
  through diagnosis → eligibility → therapy choice → persistence → discontinuation
  rather than aggregate stock-and-flow. Enables time-on-therapy distributions, response-
  dependent switching, and individual-level scenario analysis at the cost of
  computational complexity and parameter calibration burden.
- **Sigmoid (logistic) transitions** for source-of-business mix and attribute
  maturation, replacing linear interpolation. Captures empirical S-curve learning
  dynamics if observed.
- **Time-value discounting (rNPV)**. Add a discount-rate parameter and produce
  risk-adjusted NPV alongside the current cumulative-EV figure. Standard for asset-
  valuation conversations.

**Data and calibration**

- **Multi-drug Bass calibration**. Currently calibrated on Tarpeyo alone (the cleanest
  first-mover trajectory). A class-wide Bass fit using Tarpeyo + Filspari + Fabhalta
  combined adoption would capture imitation dynamics across the class and reduce
  dependence on a single drug's commercial idiosyncrasies (e.g. the Q1 2024 Change
  Healthcare cyberattack drag).
- **AZ-specific internal data**. The current model uses public-domain inputs only.
  Integrating AZ's internal sources — Ultomiris franchise commercial intelligence,
  proprietary payer-access data, longitudinal IgAN patient claims, KOL advisory boards
  — would tighten veteran cohorts, persistence assumptions, payer-access scoring, and
  source-of-business mixes.
- **Primary KOL research to tune conjoint inputs**. Current attribute weights and drug
  scores are derived from published trial readouts, labels, and analyst commentary.
  A structured conjoint exercise with nephrologist KOLs (or a max-diff / best-worst
  scaling survey) would replace these heuristic inputs with empirically-elicited
  prescriber preferences.
- **Real-world evidence (RWE) integration**. Once Ultomiris launches, recalibrate
  Bass parameters and persistence assumptions against observed claims data (Symphony,
  IQVIA, Komodo) instead of pure forecasting.
- **Scenario-dependent PoA**. Currently a uniform 0.88 across all eGFR scenarios. A
  weak/neutral eGFR readout has different full-approval-conversion probability than a
  strongly positive readout; could be modeled per-scenario.
- **Calibrated `egfr_signal_partial_strength`**. The 0.5 midpoint heuristic for
  signal-year impact could be tuned to historical prescriber-anticipation patterns
  around comparable trial readouts.

**Scope expansion**

- **EU / Japan / RoW geographies**. Current model is US-only. AZ I CAN is a global
  trial; the launch will be multi-geography. Each geography has distinct epi, payer
  dynamics, and competitive landscape.
- **Combination targeted therapy modeling**. Currently excluded based on KDIGO 2024
  sequential-escalation guidance and payer-access limitations (see *Combination
  Targeted Therapy Not Modeled*). If real-world prescribing patterns evolve toward
  combination use, the model would need an explicit combination state.
- **Indication-level cannibalization**. Ultomiris is already approved for PNH, aHUS,
  and gMG. IgAN adoption may cannibalize internal commercial bandwidth, manufacturing
  capacity, and payer goodwill across indications. Currently treated as independent
  but could be modeled jointly.
- **Detailed payer access modeling**. The current `payer_access` attribute is a single
  1-10 score per drug. Could decompose into formulary tier, prior-auth criteria, step
  edits, copay-assistance utilization, and Medicare/commercial mix — each of which
  affects Ultomiris's effective rate of conversion from prescribed-to-paid.
- **Operational / launch-execution drivers**. Currently abstract drivers like "IV/REMS
  friction" capture launch-execution headwinds. Could be decomposed into infusion-site
  capacity, REMS enrollment friction, sales-force coverage, and other ground-truth
  commercial-execution variables.

**Validation and refinement**

- **Out-of-sample backtesting**. Hold out the Q1-Q2 2024 Tarpeyo data, fit Bass on
  Q1 2022 – Q4 2023, and verify the forecast matches the held-out quarters. Quantifies
  model fit confidence.
- **Cross-validation against analyst consensus**. Compare peak EV ($728M) and trajectory
  shape to Wall Street IgAN forecasts (Jefferies, Cantor, Leerink, BMO). Material gaps
  flag either model assumptions or analyst optimism/pessimism worth investigating.
- **Sensitivity to attribute scoring uncertainty**. Currently the tornado covers six
  numeric drivers but doesn't perturb the drug attribute scores themselves. A
  share-allocation sensitivity layer (e.g., ±1 point on each Ultomiris attribute)
  would quantify how much the conjoint-share output depends on scoring judgment.
