# Laguerre RSI — Registered Predictions

**Date:** 2026-08-13, Week 13 Day 3
**Status:** Registered BEFORE implementation. No Laguerre RSI code exists yet.
**Governed by:** `C2_Selection_Criteria_PreRegistered.md` + Amendments 1-3
**Slot:** Strategy 2 C2 (open). Shortlist only — C-3b needs a backtest, so this
cannot be locked in Phase 2.

## Source

Ehlers, *Cybernetic Analysis for Stocks and Futures* (2004), Figure 14.8, p.221.
Verified against the book text on 2026-08-13, not reconstructed from memory.

    Inputs: gamma(.5);
    L0 = (1-gamma)*Close + gamma*L0[1];
    L1 = -gamma*L0 + L0[1] + gamma*L1[1];
    L2 = -gamma*L1 + L1[1] + gamma*L2[1];
    L3 = -gamma*L2 + L2[1] + gamma*L3[1];
    CU = 0; CD = 0;
    If L0 >= L1 then CU = L0 - L1      Else CD = L1 - L0;
    If L1 >= L2 then CU = CU + L1 - L2 Else CD = CD + L2 - L1;
    If L2 >= L3 then CU = CU + L2 - L3 Else CD = CD + L3 - L2;
    If CU + CD <> 0 then RSI = CU / (CU + CD);

Three ADJACENT comparisons, not L0 against L3. Input is **Close**, not (H+L)/2 —
the Laguerre filter on p.216 uses (H+L)/2, the RSI does not. Output is **0 to 1**,
neutral at 0.5, not the -1..+1 of RSIH.

## C-1 interpretation, decided before measurement

Ehlers' suggested rules are re-entry rules: buy when the line crosses back above
0.2, sell when it crosses back below 0.8. Those fire on a crossing — a moment, not
a state — so between crossings they give no answer, and C2 must answer on whatever
bar C1 fires.

**For C-1, state is taken as RSI >= 0.5 up, < 0.5 down.**

A crossing-based variant is registered as a strategy-level test, not used here:
require C2 to have crossed in the same direction within the last N bars. N=1 is
Ehlers' strict rule; N=infinity collapses to the state version, since "crossed up
and has not crossed down since" IS the state. Under strict N=1 with independent
timing, roughly 90% of C1 signals would be lost to non-coincidence rather than to
disagreement. Trade count and whether the lost signals were good belongs to C-3b.

## Predictions

**P-LR1 — Saturation.** With only three comparisons, the four L values fall into
order whenever price trends, so CU or CD reaches zero and the output pins at
exactly 1.0 or 0.0.

> **35-55% of bars sit at exactly 0.0 or 1.0, on both assets.**

Ehlers describes the excursions as "lock to lock" and Figure 14.10 shows long flat
stretches, but that is his data on his instrument. The range is a genuine guess.

**P-LR2 — C-3a correlation with MESA Stochastic.**

> **|rho| in 0.45-0.65 on both assets — the flagged band.**

A saturated indicator agrees with anything trending, and MESA Stochastic also reads
high in uptrends. But the mechanisms genuinely differ: Laguerre RSI compares filter
stages, MESA Stochastic is a roofing filter plus stochastic scaling. High but not
duplicate.

**P-LR3 — Cross-asset stability (C-5).**

> **Crossings-per-100-bars ratio under 1.5x, passing the 2x threshold.**

Price scale cannot leak in. gamma is a fraction, not a price. CU and CD are both in
price units and the final step divides one by the other, so the units cancel:
CU=1500/CD=400 gives 0.789, and CU=0.0015/CD=0.0004 gives 0.789. Output is bounded
0-1 whatever the input. RSIH and the Laguerre oscillator behaved consistently
across assets for the same reason.

**P-LR4a — Lag.**

> **Between 1.5 and 4.0 bars at gamma 0.5**, at matched variance reduction, both
> assets.

Derivation. At gamma 0.5 each stage trails the previous by ~1.4 bars (gap falls to
1/e), so L3 trails L0 by ~4.2. L0 is itself an EMA with alpha 0.5, lag
(1-alpha)/alpha = 1.0 bar, so L3 trails price by ~5.2.

But the indicator is neither L0 nor L3 — it is a ratio of differences between
adjacent stages, and the ratio is non-linear. The stage lags therefore do not
compose cleanly into an indicator lag. The range is deliberately wide because this
is a bounded estimate, not a derivation. A result outside it would say something
real about how the ratio behaves.

**Explicitly NOT the reasoning:** "Ehlers claims low lag, therefore we predict low
lag." That would make confirmation vacuous and refutation look surprising.
Precedent: `UltimateSmoother.c` was described as near-zero-lag and measured 3.87
bars against SuperSmoother's 4.04.

**P-LR4b — The ramp method will fail on this indicator.**

> **Fed a straight-line ramp, Laguerre RSI returns a constant 1.0 and no lag can
> be read.**

On a monotonic ramp all four stages stay in order permanently, so CD is always zero
and the output pins at 1.0 forever. A step or a sine input will be needed instead.

This is a prediction about our METHOD, not the indicator.

## Not predicted

MESA Stochastic's own lag has not been measured. Amendment 3 requires it as C-4's
reference point, so it is measured first. No prediction is registered, because
there is no basis for one — and predicting a candidate's lag against an unmeasured
reference plus 2 bars would not be falsifiable.

## Reminder

C-3b is decisive and requires a backtest that does not exist. **The outcome
available this week is shortlist or eliminate, not lock.**
