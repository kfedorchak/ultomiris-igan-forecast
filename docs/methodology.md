# Methodology

> **Status:** Partial. This document is built up incrementally as the prototype evolves.
> Step 12 of the build plan will fill in the remaining sections (Bass calibration, conjoint
> share, persistence cohorts, eGFR scenarios, attribute maturation, veteran cohorts, tornado
> mechanics, Gate #6 calibration). The sections below are the structurally-load-bearing
> pieces that need to be readable before the rest is written.

## Combination Use Rate

The model parameterizes **addon-to-existing** use — Ultomiris combined with another
targeted IgAN therapy rather than displacing it — at approximately **15–17%** across the
forecast horizon. The rate is 17% at Ultomiris launch (2027) and decays linearly to 15% by
year 8 post-launch via the early-to-mature mix interpolation in `core/source_of_business.py`.

This rate is reported as a separate scalar metric rather than included as a stacked-bar
bucket in the Source of New Ultomiris Patients chart, because addon patients also appear
in another drug's active stock. Including them in the SoB stacked plot would imply they
should also appear in stock-based views, creating double-counting against the Share of
Treated Patients chart.

## Scope of Patient-Flow Modeling

The model uses three patient-flow constructs that operate at different levels of
abstraction. The first two are mathematically consistent with each other; the third is
descriptive only.

1. **Class-wide new starts are mathematically consistent with aggregate stock-and-flow.**
   A single Bass diffusion curve on `total_M = high_risk_pool × market_potential_fraction`
   produces class-wide new starts per year. Allocating those new starts across the eight
   drugs via the time-varying conjoint share (and aging each drug's cohorts through the
   standard persistence schedule) produces per-drug stocks whose sum exactly equals the
   class-wide active stock shown on the funnel's "On targeted IgAN therapy" stage.
   Mathematically: `sum_d (Bass_class(t) × share_d(t)) = Bass_class(t)`, and persistence
   applies linearly to each cohort.

2. **Cross-drug switching attribution is descriptive only.** The Source of Business
   function parameterizes the origin mix of a new Ultomiris patient (treatment-naive,
   switched from a corticosteroid, switched from an endothelin antagonist, switched from
   an oral complement inhibitor, switched from an APRIL/BAFF agent, or addon-to-existing).
   These switch buckets are not actually driving corresponding outflows from the source
   drug's stock. A "switch_from_corticosteroid" bucket reporting that 9% of Ultomiris's
   2030 new starts switched from Tarpeyo does **not** mean Tarpeyo's 2030 stock in the
   Share of Treated chart decreases by that count. The two charts are decomposing
   different things. The SoB attribution is intended as a strategic-narrative input for
   commercial messaging ("where do our new patients come from?") rather than an internally
   consistent flow account.

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
