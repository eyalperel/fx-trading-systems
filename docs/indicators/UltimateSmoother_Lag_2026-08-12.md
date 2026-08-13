# UltimateSmoother — Measured Lag

**Date:** 2026-08-12, Week 13 Day 2
**Commit:** `e30a3e9`

## Result

Ramp steady-state, Period 20:

| Filter | Lag (bars) |
|---|---|
| UltimateSmootherE (Ehlers' published form) | **0.0000** |
| UltimateSmoother.c (Week 5 file) | 3.8725 |
| SuperSmoother2Pole | 4.0387 |

Zero is exact. The numerator and denominator group delays are
algebraically identical and cancel, for every period — not a tuned
approximation.

Method validated: SuperSmoother's analytic DC group delay at P=20 is
4.039; measured 4.0387.

## Two findings

**The Week 5 file is not an UltimateSmoother.** It implements a
different algorithm and its "near-zero-lag" claim is refuted — 3.87
bars against SuperSmoother's 4.04. The Week 5 validation used
detrended cross-correlation, which GOTCHAS §8 later found reports
0.00 bars for an EMA with true lag 1.50.

**P2/P3's stated mechanism does not hold as written.** Both predict
that the band inflates because its centre line "trails price" in
sustained moves. The centre line has zero lag on a linear trend, so
there is no trailing to inflate it.

## What this predicts

The band width is `sqrt(d² + σ²)`, where `d` is the centre's offset
from price. With zero lag at DC, `d ≈ 0` for the linear part of a
trend. Any inflation that remains must come from **trend curvature**,
not trend slope — a much smaller effect than P2/P3 assumed.

Expect P2 and P3 to miss, in the direction of the band being closer
to the channel than predicted. That would support Ehlers' claim that
the two indicators do not differ in any major fashion.

**P1–P4 are not revised.** Recorded before the data, per additive
amendment discipline.
