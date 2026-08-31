# Week 14 — Session 1 Handoff (part 1 of 2)

**Date:** 2026-08-31
**Scope planned:** SuperSmoother 2P/3P, UltimateSmoother + UltimateSmootherE,
HighPass, RoofingFilter, Decycler
**Scope covered:** SuperSmoother only. Session 1 continues.
**Repo at start:** main, acd46fa. Two commits added: 12a6c35, 191404b.

---

## 1. What was covered

SuperSmoother 2-pole: mechanism, why it was built, Week 5's validation method,
and the reproducibility of that validation. Full recall -> probe -> read -> gap
check -> fix cycle completed for this indicator.

Not reached: SS3 review, UltimateSmoother, UltimateSmootherE, HighPass,
RoofingFilter, Decycler.

## 2. What reconstructed cleanly

- **What a smoother does.** Noisy series in, less noisy series out, still
  tracking price. Correct on first statement.
- **Why smoothers came first.** Correct on the structural half: they are the
  base layer that later indicators consume.
- **The EMA update rule**, from memory, including the recursion, and correctly
  identified as the first use of feedback in the library.
- **Reasoning under probe.** The lag/noise trade-off was correctly extended to
  a new weight set without prompting; the ATR input chain was traced back to
  raw OHLC unaided, correctly killing a proposed downstream effect.

## 3. What did not reconstruct

- **GAP-1.1 (now closed).** SuperSmoother's mechanism was not recalled at all.
  Rebuilt in session from the EMA: one feedback term vs two, what the second
  pole buys. Closed by reconstruction, not by reading.
- **The lag framing was wrong.** SuperSmoother was recalled as "a first attempt
  at fixing lag." It does not fix lag — measured 4.04 bars. What it improves is
  the shape of the frequency response: at matched lag it rejects far more fast
  noise and preserves more slow movement than an EMA.
- **GAP-1.5 / GAP-1.7.** Week 5's validation method was not recalled, nor the
  reason for choosing it. This turned out to be the load-bearing gap.

## 4. Findings

### 4.1 Week 5's SNR could not have failed

Notebook cell 7 defines SNR as var(indicator) / var(price - indicator). The
reference is the candidate's own output, so:

- noise is whatever the filter removed, which means every candidate is graded
  against a different quantity — no fixed yardstick
- a filter that smooths less has a smaller residual and therefore scores higher
- the ideal case is a filter that outputs price unchanged, which scores
  infinity — present in the code as a division-by-zero guard rather than as a
  sign the metric points the wrong way

PASS criterion was SNR > SMA(20), plus visual inspection and a NaN check. The
only quantitative gate is passed by any filter smoothing less than SMA(20).

**This is the mechanism behind the known item in plan section 4.1.** The notes
record "Ultimate Smoother: zero-lag claim credible, confirmed by mean absolute
difference metric." A small residual was read as low lag. It is not — it is
evidence of tracking price closely, which the do-nothing filter does perfectly.
Week 13 measured UltimateSmoother at 3.87 bars.

### 4.2 A validation capable of failing already exists in the repo

Notebook cells 11-12 compute the frequency response from coefficients using
scipy freqz. No price data, no signal/noise split, no reference series. It was
used once, as a debugging tool for the SS3 anomaly, and never promoted to the
PASS gate.

Independently verified this session: SS2 -3 dB point at 20.11 bars, SS3 at
31.33 bars, matching the notebook's stated -3.01 and -6.93 dB at Period=20.

That analysis is also the only part of Week 5 that survives a fresh clone.

### 4.3 What a validation needs

Arrived at from first principles, then found to match cells 11-12:

1. The reference must be fixed across candidates, or you are not comparing them.
2. The candidate's output must enter the score, or you are describing the data.
3. There must be a result a wrong implementation would produce and a correct one
   would not. If failure cannot be described, passing means nothing.

Synthetic inputs satisfy all three for free, because signal and noise are known
by construction: ramp for lag, single-period wiggle for rejection, slow wave for
signal preservation.

### 4.4 One number standing in for a trade-off

Three instances in one session, same shape:

- SNR: smaller residual read as better
- "SS3 better?" defined as more attenuation, including in the passband
- mean absolute difference read as evidence of low lag

In each case a one-directional quantity was treated as a quality score when the
correct answer needs two columns — behaviour at the fast end and at the slow end.

### 4.5 Week 2 vs Week 5 implementations differ

archive/week2/SuperSmoother.c and indicators/ehlers/SuperSmoother2Pole.c are
different filters, not a rename.

- Input side: Week 2 uses a 1-2-1 three-bar average over 4; Week 5 uses a 1-1
  two-bar average over 2. Both pass DC at 100%, both reject period 2 exactly.
  Different mid-band shape.
- Feedback side: identical. 4.44288 equals sqrt(2)*pi. Week 5 is more legible.
- Initialisation: Week 2 seeds state at zero, so its first output on EUR/USD is
  near 0.087 against a price of 1.10, and it must climb. Week 5 seeds at
  Price[0]. **Week 2's initialisation is defective.**

## 5. Gaps logged

| ref | finding | status |
|---|---|---|
| GAP-1.1 | SuperSmoother mechanism not recalled | closed — reconstructed |
| GAP-1.2 | Fisher Transform input series unknown: raw price or smoothed? | open — session 3 |
| GAP-1.3 | "Lag" means different things in Week 5 (detrended cross-correlation, cell 5) and Week 13 (ramp offset). Same word, two measurements, not comparable. | open — session 6 |
| GAP-1.4 | 4.04 bars corroborated for Ehlers' published coefficients; SuperSmoother2Pole.c confirmed to use them | closed for 2-pole |
| GAP-1.6 | Degrees/radians code block inverted, contradicting its own prose and the working .c | FIXED — 12a6c35 |
| GAP-1.7 | Week 5 SNR definition unknown | closed — it is definition A, see 4.1 |
| GAP-1.8 | Main validation tables record no Period for any indicator. Inferred as 20 from a coincident SNR value in the sensitivity table. | open |
| GAP-1.9 | Notebook cells 11-12 define "better" as more attenuation at all frequencies including the passband. "SS3 beats SS2 at ALL frequencies" is not a valid reading; SS3's curve is shifted, not superior. Contradicts the same cell's own SS3(28-30) recommendation. | open |
| GAP-1.10 | **Week 5's validation is not reproducible.** Notebook reads three CSVs from C:/Zorro/Data/, none tracked. Same class as the Week 9 finding — plan section 1.1 treats Week 5 as sound and Week 9 as not; both fail. | open |
| GAP-1.11 | 3-pole coefficient block carried the degrees form | FIXED — 191404b |
| GAP-1.12 | "The naive published 3-pole formula is unstable (net feedback > 1.0)" — asserted with no source reference and no measurement. Verify against the article or relabel as inference. | open — with SS3 |

Resolved with no action: the volatility branch (ATR, NATR, stops, sizing) reads
raw OHLC and is untouched by any filter, so filter-side effects cannot reach it.

Prediction registered and **missed**: warmup discard would hide a bad seed. There
is no warmup discard — cell 2 loads everything. Mechanism was wrong; the general
principle stands (discarding warmup removes the region where initialisation
errors are visible, so initialisation needs its own test).

## 6. Corrections to material produced in session

Claude produced two sets of wrong numbers, both caught by later verification:

- EMA lag on a ramp given as 0.75 and 3.2 bars for alpha 0.5 and 0.2. Correct:
  1.00 and 4.00. The alpha=0.2 frequency table was estimated, not computed.
- A 109% passband overshoot at period 40, and a claim that SS2's corner sits at
  1.41x Period. Both false. Butterworth is maximally flat and monotonic — no
  overshoot; the -3 dB point is at 20.11 bars, essentially at Period. The error
  came from measuring square-wave peaks, which carry harmonic content, and
  reading them as a frequency response.

Recorded because the failure mode is identical to the one under review: a table
of numbers to three significant figures inside an otherwise correct argument.

## 7. Fixes made

- 12a6c35 — degrees/radians block corrected; unit conversion separated from the
  Butterworth sqrt(2); argument-magnitude sanity check added
- 191404b — 3-pole coefficient line corrected to PI

**Deliberately not fixed:** the status header and validation tables in
SuperSmoother_Notes.md. That file covers SS2, SS3 and UltimateSmoother under one
shared status and one shared results table. Rewriting it now would set
UltimateSmoother's claims before UltimateSmoother has been reviewed — the
pattern this week exists to undo.

## 8. Next sitting starts here

1. SS3 review — carries GAP-1.12.
2. UltimateSmoother and UltimateSmootherE — the plan section 4.1 known item.
   Section 4.1 above supplies the mechanism; what remains is which file is
   referenced where, and what Week 5's claims should now say.
3. Then the status-table rewrite for the whole family, once.
4. Then HighPass, RoofingFilter, Decycler.

**Open decision for the rewrite:** whether to re-run Week 5's validation using
the cells 11-12 method, and whether the tracked-CSV problem (GAP-1.10) is solved
by committing the CSVs or by replacing market-data validation with synthetic
inputs, which need no data at all.
