# Week 12 Retrospective — Noise Reduction & Signal Quality

**Dates:** 2026-08-05 to 2026-08-06
**Phase:** 2 — Indicator Deep Dive (Week 12 of 48)
**Primary objective:** Fill Strategy 2's open C2 slot
**Outcome:** ⛔ **Not met — and that is the correct result.**

---

## 1. What happened

The week's stated objective was not achieved. No C2 candidate was accepted, and the audit
work additionally put Strategy 1's *existing* C2 in question. The week ended with **two**
open C2 slots where it began with one.

That is a worse-looking position and a more honest one. Everything below explains why it
is also the right one.

| Planned | Actual |
|---|---|
| Implement Kalman Filter (#21) | Implemented as **Alpha-Beta Filter** — the Kalman attribution was false |
| Implement Recursive Median (#22) | Done; RM validated, RMO eliminated as C2 |
| Implement Correlation Cycle (#23) + null test | Done; classified as filter |
| Fill Strategy 2 C2 | **Failed** — no candidate passed |
| — | **Unplanned:** Strategy 1 C2 audit, C-3 criterion amendment, gotchas consolidation, radians documentation sweep |

---

## 2. The three predictions

Pre-registration only means something if predictions can fail. Three were registered this
week. **One held exactly; two were wrong in the same direction.**

| # | Prediction | Actual | Verdict |
|---|---|---|---|
| 1 | RM lag = 3.37 bars (2.00 median + 1.37 EMA), Day 1, before any code | **3.366 bars**, decomposition exact | ✅ Confirmed to 3 decimals |
| 2 | RMO \|ρ\| with MESA Stochastic ∈ 0.40–0.65 | **0.799 / 0.682** | ❌ Wrong |
| 3 | Reflex \|ρ\| with Fisher ∈ 0.25–0.50 | **0.597 / 0.595** | ❌ Wrong |

### 2.1 The pattern in the failures

Predictions 2 and 3 both **overestimated how much mechanistic difference translates into
signal independence**. Both reasoned from construction ("different filter family,
therefore decorrelated") rather than from measurement.

The diagnosis for RMO is precise and generalises:

```
corr(RM, plain EMA) = 0.9965 (FX)   0.9997 (BTC)
```

RM's non-linear median gate is **dormant**. A median differs from a mean only when
outliers are present, so on ~99% of bars RM ≈ EMA and RMO ≈ band-pass — which is what
MESA Stochastic is.

> **Lesson: "mechanism exists" ≠ "mechanism operates."** A gate that fires on 1% of bars
> leaves the filter behaving linearly on the other 99%. Criterion C-2 (mechanistic
> distinctness) passed on theory that described a mechanism which mostly doesn't fire.

The same reasoning error appeared twice in one week, on two different indicators. It is
now a named failure mode rather than an intuition.

**Prediction 1 is the counterweight.** Derived from first principles, written and pushed
before implementation, and reproduced by the code to three decimals. A sorting-network
error, misplaced 0.707, or wrong alpha would each have broken it. That is what
theory-before-code buys.

---

## 3. Three source errors found

None were sought. All three fell out of doing derivations rather than trusting text.

| # | Source | Error |
|---|---|---|
| 1 | Ehlers, *Recursive Median Filters* | Critical-period description is **inverted** — describes a high-pass while the RM is a low-pass. Text appears carried over from his one-pole high-pass design, which uses the identical α. |
| 2 | Project's own indicator plan | Indicator #21 labelled "Ehlers Kalman Filter." **No such article exists** in the 102-article library; `Every Little Bit Helps.pdf` was mis-mapped and concerns averaging open+close at Nyquist. The filter is an α–β tracker. "Optimal minimum-variance estimator" **retracted**. |
| 3 | Ehlers, *Correlation As A Cycle Indicator* | The monotonicity ratchet **manufactures the signature it claims to detect**. It forbids phase from decreasing, holding the angle flat on 26.6% (FX) / 28.6% (BTC) of bars — so "trend-mode flatlining" appears on any input, including pure noise. |

Error 2 was the project's own, not Ehlers'. Worth stating: the mis-mapping propagated
from `Week5-14_Indicator_Plan.md` into the roadmap and survived two roadmap revisions.

---

## 4. The bug that would have gone unnoticed

The 5-element median sorting network was **wrong** — 12 of 120 permutations returned a
non-median. On 2,236 bars that is ~220 silently corrupted values, and the resulting chart
would have looked entirely plausible.

Caught by exhaustive verification before compiling. Replaced with Knuth's optimal
9-comparator network, verified via the **0-1 principle**: a network that correctly sorts
all 2⁵ = 32 binary inputs provably sorts *all* inputs over any ordered type. 32 test cases
is a complete proof, not a sample.

**This is the class of bug that inspection does not catch.** It produces correct output
90% of the time.

---

## 5. The measurement instrument was nearly wrong

Criterion C-4 (lag) was almost measured with a method that produces confident nonsense.

| Method | Pure 3-bar delay | EMA α=0.40 (analytic 1.50) | Verdict |
|---|---|---|---|
| First-difference cross-correlation | — | **0.00** | ⛔ Invalid |
| MSE-minimising shift | 3.00 ✅ | 0.94 | ⚠️ ~0.65× biased for smoothers |
| **Ramp steady-state** | 3.00 ✅ | **1.500** ✅ | ✅ Exact |

First-difference cross-correlation reported **zero lag for a filter with known 1.50-bar
lag**. Differencing an EMA yields α·(P[t] − EMA[t−1]), dominated by the current price
change, so it peaks at lag 0 regardless of how much the level trails.

Caught only because the instrument was validated against a case with a known answer
*before* being applied to an unknown one.

> **Standing rule adopted:** validate any measurement instrument against a known ground
> truth before applying it to the quantity of interest.

---

## 6. The C-3 criterion was insufficient — and revised properly

The Strategy 1 audit exposed a real flaw. Reflex and Fisher correlate at ≈0.60 on **both**
assets, yet a preliminary information-gain test splits:

| Asset | C1 & C2 agree | C1 alone | C2 filter |
|---|---|---|---|
| EUR/USD D1 | −5.19 bp | −12.09 bp | **adds +6.90 bp** |
| BTC/USD H4 | +6.83 bp | +21.75 bp | **destroys −14.93 bp** |

**Near-identical correlation, opposite value.** Correlation cannot distinguish these
cases, because what matters is whether the ~26% of bars where C2 *disagrees* are
informative — and ρ does not measure that.

### 6.1 How the revision was handled

The revision arrived *after* seeing results that failed the old threshold. That is exactly
the situation pre-registration exists to guard against, so the handling matters:

- **Original text preserved unedited**, amendment appended below with a date
- **RMO's elimination stands** — decided under the criterion as written
- **Registered before Week 13 data exists** — Laguerre RSI not yet implemented
- **The new criterion is stricter, not looser** — C-3b would have eliminated RMO anyway
- **Reflex flagged, not unlocked** — the preliminary figure is a crude proxy (no entry
  rules, no costs, arbitrary horizon) and per §5's rule does not unseat a locked decision

### 6.2 Structural consequence

**C2 selection cannot be completed at indicator level.** C-3b is a strategy-level test
requiring entry rules, costs and walk-forward. Phase 2 can shortlist; Phase 3 decides.

This changes Week 13's framing: Laguerre RSI is evaluated as a **shortlisted candidate**,
not a lock.

---

## 7. On the multi-pair objection

A proposal was raised mid-week: rather than rejecting on two-asset correlation, test
across many FX pairs and accept whatever survives backtesting, Monte Carlo and WFO.

**The valid part** was decisive — it identified that correlation measures the wrong
quantity, and it produced the C-3b revision.

**The part that was pushed back on:** FX majors are not independent tests. EUR/USD,
GBP/USD, AUD/USD and NZD/USD share the USD leg, with pairwise correlations typically
0.6–0.9. Twenty pairs give perhaps three to five effective independent samples, while
multiple-comparison inflation prices as if there were twenty. Run enough pairs and
something passes on noise alone.

This project has already measured that effect: the Week 11 regime addendum found a
max-statistic null 95th percentile of **61.45** against a real value of **20.47**.

**Resolution:** multi-pair testing is *confirmation* after a candidate passes on
pre-specified assets — not a search over pairs for one that works.

---

## 8. Cycle premise — cumulative state

| Week | Mechanism | Statistic | Tests | Min p | Result |
|---|---|---|---|---|---|
| 11 | Band-pass (Roofing → CyberCycle) | Spectral peak prominence | 48 | 0.070 | No rejection |
| 12 | Quadrature projection | Phase coherence | 8 | 0.379 | No rejection |
| 12 | Autocorrelation | Correlogram peak prominence | 8 | 0.117 | No rejection |

**Three mechanistically distinct methods. 64 tests. No rejection.** Week 11's obvious
objection — that only one filter chain had been tested — is now closed.

**The week's sharpest single result:**

```
Correlation Cycle phase coherence R:
   EUR/USD D1        0.9706
   IID random walk   0.9705   (null median)
```

R ≈ 0.97 looks like near-mechanical cycle regularity. It is a **window artefact**:
consecutive 20-bar windows share 19 of 20 bars, so consecutive phase angles are
near-identical by construction. Real FX sits at the **51st percentile** of the noise
distribution.

> The roadmap's original Day 5 check was *"does the reading align with visually obvious
> cycle/trend periods."* **That check would have passed.** On pure noise the phase looks
> coherent and the state variable flips convincingly on a third of all bars. Without the
> surrogate comparison, the indicator appears to work. Principle 6 earned itself this
> week.

---

## 9. What went well

- **Theory-before-code validated concretely** — a lag prediction derived on Day 1 and
  confirmed to three decimals on Day 3
- **Pre-registration functioned as designed** — a candidate that passed 6 of 7 criteria
  was eliminated by the one designated decisive in advance, with the threshold unmoved
- **Verification caught what inspection would not** — the sorting network, the alpha
  placement, the invalid lag instrument
- **Retrospective audit of a locked decision** — Strategy 1's C2 had never been measured
  against the standard later applied to Strategy 2. Applying it retroactively was
  uncomfortable and correct
- **Reuse worked** — RMO's high-pass stage reused the existing `HighPassFilter` with no
  duplicated code

## 10. What to do differently

- **Read the actual source article on Day 1**, not an adjacent one. The Correlation Cycle
  mechanism error cost a re-registration mid-week and would have invalidated the Day 5
  test had it gone unnoticed.
- **Check provenance before scheduling an indicator.** Indicator #21's missing article
  should have surfaced when the week was planned, not on Day 2.
- **Stop predicting decorrelation from mechanism.** Two failures in one week. Measure
  first, explain after.
- **Correction sweeps must cover prose.** The May 2026 radians fix touched code only;
  five stale documentation claims survived, including a broken snippet in the active
  roadmap that would have reintroduced the Week 3 bug.

---

## 11. Deliverables

| Item | Path |
|---|---|
| Recursive Median + RMO | `indicators/ehlers/RecursiveMedian.c` |
| Alpha-Beta Filter | `indicators/ehlers/AlphaBetaFilter.c` |
| Correlation Cycle | `indicators/ehlers/CorrelationCycle.c` |
| Theory | `docs/indicators/RecursiveMedian_Theory.md` |
| Pre-registered criteria + Amendment 1 | `docs/indicators/C2_Selection_Criteria_PreRegistered.md` |
| C2 decision record | `docs/indicators/C2_Decision_Week12.md` |
| RM findings + reclassification | `docs/indicators/RecursiveMedian_Findings.md` |
| Second null test | `docs/research/Cycle_Premise_Second_Null_Test.md` |
| Null-test harness (seeded) | `analysis/null_tests/phase_coherence_null_test.py` |
| Platform reference | `docs/ZORRO_LIGHTC_GOTCHAS.md` |
| README | `README.md` — reframed, Week 11 action 9 closed |

**Commits:** `c310e14` → `2f495bc`, 14 commits, all pushed.

---

## 12. Carried into Week 13+

| # | Item | Target |
|---|---|---|
| 1 | Laguerre RSI as a **shortlisted** C2 candidate (both slots) | Week 13 |
| 2 | Action 10 — null-test Reflex and MESA Stochastic | Week 14 |
| 3 | Formal C-3b resolution for both C2 slots | Phase 2.5 / 3 |
| 4 | Alpha-Beta gain sweep at corrected 0.02/0.05/0.10/0.20 | Low priority |
| 5 | Autocorrelation periodogram Light-C port | Only if a future test rejects |
| 6 | Duplicate `InstantTrendline_Validation.md` in `docs/` and `docs/indicators/` | Housekeeping |
| 7 | Does RM help on genuinely corrupted data? Needs tick data or synthetic bad-tick injection | If RM is proposed for live use |

---

*Objective not met. Three source errors found, one silent bug caught before it shipped,
one locked decision reopened for audit, and a selection criterion replaced with a
stricter one. The slot stays open because nothing earned it.*
