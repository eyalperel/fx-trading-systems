# Scope Correction — Cycle Premise Work Demoted to a Bounded Research Result

**Date:** 2026-08-10, Week 13
**Status:** Governing. Supersedes the forward-looking recommendations in
`Cycle_Premise_Conclusions_and_Impact.md` §2.3.
**Does not supersede:** any measured result. Parts 1 and 3 of that document stand unedited.

---

## 1. What changed

The Week 11–12 surrogate work produced a correct, carefully bounded negative result. It was
then promoted to the organising frame of the project: the README's largest section, two
mandatory Phase 2 principles, and an elimination criterion (C-7) in the Strategy 2 C2
pre-registration.

**The finding was right. Its promotion was disproportionate to its scope.**

What was actually established:

> On EUR/USD D1 (2015–2024) and BTC/USD H4 (2020–2024), at one parameterisation
> (HP=48 / SS=10 / P=20), across a 10–48 bar passband, no cyclic component was detectable
> above ~4.4% (FX) / ~5.0% (crypto) of return variance by three linear-projection
> mechanisms.

What was **not** established, and was never claimed in the research documents themselves:

- That no cycles exist in these assets at other periods, bands or parameterisations
- That no cycles exist in other instruments
- That band-pass filters are without value — explicitly denied in
  `Cycle_Premise_Conclusions_and_Impact.md` §1.5
- Anything about strategy-level profitability

Gating future indicator work on a result of this scope was an over-extension.

## 2. What the project is evaluating instead

The operative question moves from **"is the source's justification true?"** to
**"what does this filter do, and does the combination outperform its parts?"**

This is not a new criterion. It is C-3b — conditional information gain — already registered
in `C2_Selection_Criteria_PreRegistered.md` Amendment 1 (2026-08-06), promoted from a
deferred tiebreaker to the project's central selection test.

An indicator's frequency response, lag and bandwidth are measurable facts about the filter.
They are sufficient grounds to include it in a trading system, independent of whether the
phenomenon its author invoked to motivate it exists.

## 3. Withdrawn

| Item | Location | Disposition |
|---|---|---|
| Principle 6 — null gate for cycle-justified indicators | Roadmap v4.3 | **Replaced** (see §4) |
| Principle 7 — mechanism determines the evidential bar | Roadmap v4.3 | **Replaced** (see §4) |
| C-7 — mechanism must survive the Week 11 null finding | C2 criteria | **Withdrawn** — Amendment 2 |
| "Cycle extraction" as a general negative | Roadmap "What Doesn't Work" | **Rescoped** to the tested assets and band |
| Null test as README centrepiece | README | **Demoted** to a linked research entry |

**Consequence of the C-7 withdrawal:** Correlation Cycle is no longer excluded *a priori*
as a C2 candidate. It was never assessed on merit — only on cycle-justification. It remains
subject to C-3a, and as a normalised single-bin DFT it is expected to correlate highly with
MESA Stochastic. RMO's elimination is unaffected; it was decided under C-3, not C-7.

## 4. Replacement principles

**Principle 6 (revised) — Classify by mechanism, not by source claim.**
Every indicator enters the library with measured frequency response, lag, bandwidth and
cross-asset stability. Where a source claims cycle detection but the mechanism is a linear
filter, the library entry says *filter*. This classification follows from the mathematics
and requires no surrogate test.

**Principle 7 (revised) — Information contribution is decided at strategy level.**
Indicator-level metrics screen candidates; they do not decide them. Whether a component
earns its slot is measured in combination, with transaction costs and walk-forward
validation, in Phase 2.5 and beyond.

## 5. Instrument universe

Two sets, fixed before testing, to preserve pre-registration discipline while trading broadly.

**Development set** — where every selection decision is made. Chosen for low mutual overlap,
not coverage:

| Instrument | Rationale |
|---|---|
| EUR/USD D1 | Continuity; all existing validation |
| BTC/USD H4 | Continuity; different asset class and timeframe |
| EUR/JPY D1 | Non-USD cross — no shared USD leg |
| AUD/USD D1 | Commodity block — different macro driver |

**Confirmation set** — instruments used to *test* a component after it has been selected,
never to select it. The procedure is one-directional:

1. The component is selected on the development set.
2. It is then run **unchanged** on the confirmation set — no retuning, no parameter search.
3. If it does not hold there, the component is **ruled out**. It does not return to the
   development set for adjustment.

Composition: majors and crosses outside the development set, plus metals and energy —
**XAU/USD, XAG/USD, WTI/USD**. Minors are excluded.

Metals and energy strengthen the test more than additional USD pairs would, because their
macro drivers differ. Two qualifications: XAU/USD and XAG/USD still carry a USD leg and
correlate with each other at roughly 0.8, so XAG adds less independent information than XAU;
and WTI/USD is a CFD instrument whose roll and financing behaviour differs from spot FX.

> **Open — the pass condition is not yet defined.** What counts as "holding" on the
> confirmation set requires strategy-level metrics that do not exist until Phase 2.5.
> Registering a threshold before it is measurable would be pre-registration in appearance
> only. It is to be fixed as a dated pre-registration **before the first confirmation run**,
> not after.

The retained objection: FX majors share the USD leg with pairwise correlations of roughly
0.6–0.9, so twenty pairs yield perhaps three to five effective independent samples while
multiple-comparison inflation prices as if there were twenty. Broad testing is
**confirmation, not search**. That rule is independent of the cycle question and is retained.

**Also open before Phase 2.5:** native data availability must be verified per instrument in
Zorro, and contract specifications and cost models confirmed for XAU, XAG and WTI, which are
not spot FX and do not share its position-sizing or ATR-scaling assumptions.

## 6. Schedule

Phase 2 completes the library first. Phase 2.5 begins after Week 14 and its duration is
**elastic** — strategy-level machinery is now the project's critical path, and the previous
three-week allocation was set when it was a supporting phase. It is not to be compressed to
protect a week number.

## 7. What this is not

This is not a retraction. No measurement, p-value, positive control or limitation in the
Week 11–12 research is altered. The code remains in `analysis/null_tests/`, seeded and
reproducible, and the documents remain in `docs/research/`.

The methodology also remains directly applicable at strategy level, where its scope
objection does not apply: testing whether a strategy's Sharpe ratio is distinguishable from
its distribution on surrogate price series is a stronger overfitting check than walk-forward
alone. That use is carried into Phase 2.5 as a tool rather than a gate.

What changed is the weight the result carries in decisions it does not bear on.

## 8. Affected documents

| Document | Change |
|---|---|
| `README.md` | Reframed as a DSP filter library; null test demoted to a linked entry |
| `docs/roadmap/FX_Roadmap_v2026.08.10.md` | v4.4 — principles replaced, scope corrected, universe added |
| `docs/indicators/C2_Selection_Criteria_PreRegistered.md` | Amendment 2 — C-7 withdrawn |
| `docs/research/Cycle_Premise_Conclusions_and_Impact.md` | Header note — §2.3 superseded |
| `docs/indicators/Week5-14_Indicator_Plan.md` | Week 14 mapping task — null-gate language removed |
| `indicators/ehlers/CyberCycle.c`, `CorrelationCycle.c` | Header classification wording |

Unchanged: all indicator implementations, all validation code, all weekly notes, and the
Week 11–12 research documents themselves.
