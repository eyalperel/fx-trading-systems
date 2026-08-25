# C2 Screening — Laguerre RSI

**Date:** 2026-08-13, Week 13 Day 3
**Slot:** Strategy 2 C2 (FRAMA baseline + MESA Stochastic C1 + C2 open)
**Predictions:** `LaguerreRSI_Registered_Predictions.md`, committed `fd5e7fa`
**Criteria:** `C2_Selection_Criteria_PreRegistered.md` + Amendments 1-4

## Outcome

**SHORTLISTED. Not locked.**

Every measurable criterion passes. C-3a is flagged, which under Amendment 2 means
C-3b must pass decisively. C-3b requires a backtest that does not exist — no
walk-forward has been run, that is Week 15. C2 selection cannot be completed at
indicator level.

| | Result | |
|---|---|---|
| C-1 directional state | PASS | 0.5 boundary gives a state every bar |
| C-2 mechanistic distinctness | PASS | argued from theory |
| C-3a correlation | **FLAG** | 0.576 / 0.562, inside 0.50-0.65 |
| C-3b information gain | **PENDING** | decisive, needs a backtest |
| C-4 lag | PASS | 1.138 bars later than C1, within +2.0 |
| C-4b lag profile | PASS | leads C1, not a delayed copy |
| C-5 cross-asset | PASS | crossing ratio 1.10x |
| C-6 outlier | PASS | 12 bars faster than the reference |

## Source

Ehlers, *Cybernetic Analysis for Stocks and Futures* (2004), Fig 14.8, p.221.
Transcribed from the book, not reconstructed. Three points that were assumed
wrongly before reading it:

- Comparisons are **adjacent pairs** (L0-L1, L1-L2, L2-L3), not L0 against L3
- Input is **Close**. The Laguerre filter on p.216 takes (H+L)/2; the RSI does not
- Output is **0..1**, neutral 0.5 — not the -1..+1 of RSIH

Implemented as published, including the hold-previous behaviour when CU+CD is zero.

## Predictions: three hit, one missed

| | Predicted | EUR/USD | BTC | |
|---|---|---|---|---|
| P-LR1 saturation | 35-55% | 37.8% | 37.4% | hit |
| P-LR2 \|rho\| with C1 | 0.45-0.65 | 0.576 | 0.562 | hit |
| P-LR3 crossing ratio | under 1.5x | 1.10x | | hit |
| P-LR4a lag | 1.5-4.0 bars LAG | 4.595 bars LEAD | | **MISS** |
| P-LR4b ramp fails | yes | confirmed | | hit |

**P-LR4a missed in direction, not just magnitude.** The derivation accounted for the
four L stages lagging price by ~5.2 bars and forgot that the indicator is built from
DIFFERENCES between stages. Differencing acts like a derivative and leads by a
quarter cycle — 10 bars at the test period of 40.

    differencing        +10.0 bars lead
    four L stages        -5.2 bars lag
                        -----
    net                  +4.8 bars lead      measured 4.595

Explained after the fact, which is weaker than predicting it. Recorded as a miss.

## Criterion detail

**C-1 — PASS.** Ehlers' 0.2/0.8 rules fire on crossings, so they give no answer
between crossings, and C2 must answer on whatever bar C1 fires. State is taken as
RSI >= 0.5 up, below 0.5 down — decided before measurement. A crossing-window
variant is registered for strategy-level testing: under a strict same-bar rule
roughly 90% of C1 signals would be lost to non-coincidence rather than to
disagreement.

**C-2 — PASS.** Laguerre RSI: an EMA followed by three allpass delay elements, with
direction read from three adjacent-stage comparisons. MESA Stochastic: a roofing
filter (highpass then SuperSmoother) followed by stochastic rescaling. Different
filter classes, argued from theory.

Noted, as C-2 was noted in Week 12: this is a weak test. RMO passed C-2 on theory
and then measured 0.9965 against a plain EMA. C-2 catches obvious duplicates and
nothing subtler.

**C-3a — FLAGGED.** rho = 0.576 (EUR/USD) and 0.562 (BTC), inside the 0.50-0.65
band. Sign agreement 73.1% and 70.9%.

For comparison, RMO — eliminated in Week 12 — measured rho 0.799 with 84.7% sign
agreement. Laguerre RSI disagrees with C1 on 27-29% of bars against RMO's 15%,
roughly double the potential filtering. Whether those disagreements are informative
is exactly what C-3a cannot measure and C-3b decides.

**C-4 — PASS.** Measured by sine input at period 40, since the ramp method cannot
be used (P-LR4b).

    MESA Stochastic    leads price by 5.733 bars
    Laguerre RSI       leads price by 4.595 bars

Laguerre RSI is 1.138 bars later than C1, within the +2.0 margin.

Harness validated against a known answer per GOTCHAS section 8: SuperSmoother P=20
has an analytic phase delay of 4.3505 at period 40; the harness measured 4.349,
matching to 0.03%.

**C-4b — PASS.** Peak at shift -1 on both assets, refined -0.85 (EUR/USD) and -0.55
(BTC). The candidate LEADS C1, so this is not the delayed-copy signature C-4b was
written to catch. Amendment 4 added the missing row for this case.

Read with its qualifiers: the peak is 0.5929 against 0.5757 at shift 0 — a broad,
flat profile meaning "essentially in phase" rather than "leads by one bar". Sub-bar
magnitudes are within measurement resolution.

**C-5 — PASS.** Crossings per 100 bars: 10.0 (EUR/USD D1) and 9.1 (BTC H4), a ratio
of 1.10x against a 2x threshold. Identical parameters, no retuning.

Price scale cannot leak in: gamma is a fraction, and CU and CD are both in price
units so the final division cancels them. Output is bounded 0-1 whatever the input.

**C-6 — PASS.** March 2020 BTC crash, largest H4 drop 2020-03-12 at -20.5%
(6,037 -> 4,800).

    EMA(20)        26 bars stuck in the down state
    Laguerre RSI   14 bars
    difference     -12 bars, against a +5 allowance

The EMA must wait for price to climb back above an average that includes the crash
bar. Laguerre RSI only needs its four stages to reorder, which happens as soon as
price rises at all.

Two caveats. The criteria file's own limitation applies: one event is not a
distribution, so this shows the candidate handled THIS crash. And the comparison is
not like-for-like — EMA(20) is the project's Week 13 convention, not a matched
setting, and "price below EMA" is not the same kind of rule as "RSI below 0.5".
Matching "equivalent smoothing" between a bounded 0-1 oscillator and a price-level
EMA would produce a number without meaning behind it. The -12 bar margin is wide
enough that a different EMA period would not flip the verdict, but the figure itself
is not precise.

## Method findings

**Phase delay is not group delay.** A ramp measures group delay at DC; a sine
cross-correlation measures phase delay at that frequency. SuperSmoother P=20 is
4.039 by ramp and 4.3505 by sine at period 40 — both correct. Comparing a sine
result against the ramp figure made a working harness appear 7% in error. Recorded
as Amendment 4 A4.3 and in GOTCHAS.

**A single-frequency lag does not predict the market-data relationship.** The sine
implied Laguerre RSI would LAG MESA by 1.14 bars; market data shows it LEADS by
0.55-0.85. Opposite sign, because a sine is one frequency and markets contain many.
C-4 and C-4b measure different things and neither substitutes for the other.

**Saturation is input-dependent.** 70% on a clean sine, 37% on market data. A sine
trends steadily so the four stages stay ordered; real price reverses far more often.
P-LR1 was registered against market data and hit; the sine figure would have missed
it badly.

## What this does not establish

Every criterion measured here is a **screen**. None of them shows that Laguerre RSI
improves a strategy. That is C-3b, it is decisive, and it needs a backtest.

The specific open question: Laguerre RSI disagrees with MESA Stochastic on 27-29% of
bars. Are those bars informative, or is the disagreement noise? A candidate whose
disagreements are randomly distributed blocks winners and losers in equal measure and
is worth nothing. Correlation cannot tell the two apart.

**Next:** C-3b at Phase 2.5/3, out of sample, with costs, better on every development
asset. Note the cost model is currently incomplete — see
`Swap_Cost_Modelling_Open.md`.
