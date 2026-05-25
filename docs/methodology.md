# Methodology

> **Status:** Partial. This document is built up incrementally as the prototype evolves.
> Step 12 of the build plan will fill in the remaining sections (Bass calibration, conjoint
> share, persistence cohorts, eGFR scenarios, attribute maturation, veteran cohorts, tornado
> mechanics, Gate #6 calibration). The sections below are the structurally-load-bearing
> pieces that need to be readable before the rest is written.

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
