# Week 13 — P1-P4 Results

**Date:** 2026-08-12, Week 13 Day 2
**Predictions:** `Week13_Registered_Predictions.md` (unrevised)
**Data:** EUR/USD D1 2,596 bars, BTC/USD H4 7,534 bars.
Length = STRLength = 20, NumSTRs = NumSDs = 1. No retuning.

## Summary

| | Predicted | EUR/USD | BTC | Verdict |
|---|---|---|---|---|
| P1 corr(str, sd) | 0.85-0.90 / 0.60-0.70, BTC lower | 0.666 | 0.786 | Miss, **direction reversed** |
| P2 median str/sd | 1.2-1.3 / 0.9-1.1, BTC lower | 1.509 | 1.459 | Miss, direction correct |
| P3 gap | 0.5-0.6, BTC larger | 0.026 | 0.008 | Miss, **direction reversed** |
| P4 lag-20 in d(sd) | present in band, absent in channel | 8.82x | — | **Confirmed** |

P4 first: it is a verification, not a discovery. The band's
first-differenced autocorrelation at lag 20 is **-0.4686**, 8.82x its
neighbours at lags 15-25. The channel shows 1.16x — nothing. The
negative sign is the confirmation: a bar enters the 20-bar window,
lifts the width, then drops out abruptly 20 bars later. The
implementation is sound, so P1-P3 are real results, not bugs.

## P2 — predicted miss, for the registered reason

P2 assumed the band inflates because its centre line trails price in
sustained moves. It does not. UltimateSmoother measures **0.0000 bars
lag** (`UltimateSmoother_Lag_2026-08-12.md`), exactly, by algebraic
cancellation.

The miss was recorded before the data. Measured 1.509 against a
random-walk baseline of 1.6 means the band is inflated ~6%, not the
~25% predicted. The remaining 6% is plausibly the fat-tails half of
the reasoning, which the lag finding leaves untouched.

## P1 — reversed, and the premise is wrong

BTC correlates **higher**, not lower. All eight cells of the
diagnostic grid below show BTC above EUR/USD. Systematic, not noise.

P1 reasoned: fatter tails hit the squared measure harder, so the two
widths disagree more. The premise is true; the inference is not. A
large shock enlarges the bar range **and** pushes price from the
centre — it moves both widths together. Big common shocks are shared
signal, which **raises** correlation. What lowers it is disagreement
on ordinary bars, where each measure is dominated by its own
behaviour. EUR/USD has proportionally more ordinary bars.

**Fat tails synchronise the two estimators rather than decoupling
them.**

### Why P1 missed its level: a 2x2

STR and SD differ in two ways at once — input (bar range vs distance
from centre) and filter class (recursive smoother vs hard 20-bar
window). Two extra columns fill the missing corners:

| corr | EUR/USD | BTC |
|---|---|---|
| same input, different averaging (str~tr_box) | 0.746 | 0.832 |
| same input, different averaging (dev_sm~sd) | 0.581 | 0.734 |
| same averaging, different input (str~dev_sm) | 0.696 | 0.825 |
| **same averaging, different input (tr_box~sd)** | **0.867** | 0.939 |
| both different (P1's comparison) | 0.666 | 0.786 |

`tr_box~sd` = 0.867 lands **inside P1's predicted 0.85-0.90**. So
P1's reasoning about the inputs was sound; the prediction missed
because the two indicators also differ in filter class, which P1 did
not account for.

Not clean: `str~dev_sm` = 0.696 is low despite matched averaging.
Corner 4 uses absolute rather than squared deviation, so it differs
from SD in two ways. Not pursued.

## P3 — the split variable inverted the test

Both ratios came in **below 1**; both were predicted well above 1.
Bars in the trending bucket have *smaller* widths than bars in the
flat bucket.

Cause: `trend_score = |Close - FRAMA| / STR` divides by STR, so
high-volatility bars get a smaller score and land in the **flat**
bucket. The split sorts by volatility as much as by trend state.

The pre-registration identified this (Known Limitation 2) and judged
it survivable because it shares no term with the band width. That
reasoning was about circularity, and it holds. The severity was
underestimated: the bias is strong enough to invert both ratios,
leaving no headroom for the effect being tested.

A future version needs a split variable that does not normalise by a
volatility measure.

## Coherence

P1, P2 and P3 were registered as resting on one claim: BTC decouples
the two width estimators more than EUR/USD does. The document states
a reversal would contradict all three at once. P1 and P3 both
reversed. The shared premise is refuted.

## Observed, not investigated

`dev_sm` reaches **-0.000472** on an input that is always positive —
the UltimateSmoother overshoots. This is Ehlers' own caveat (output
less smooth than SuperSmoother) appearing in our data. Recorded only.

## Practical consequence

P4's cliff is real and matters for the ATR slot. A stop placed on the
band jumps inward roughly 20 bars after a volatility event, unrelated
to conditions at that moment. The channel has no such artifact. For
stop placement, prefer the channel.
