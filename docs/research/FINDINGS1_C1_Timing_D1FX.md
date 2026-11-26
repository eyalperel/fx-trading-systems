# FINDINGS 1 — Does an NNFX C1 time entries better than chance on D1 FX? (2026-11-24 .. 11-26)

**Status:** write-up of five pre-registered studies; no new test. Numbers are copied from the run records named in each row.
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Short answer

(b) Not on the evidence so far. Two full NNFX strategies (EUR/USD) read STOP; both sit mid-distribution of a random-timing null.
Of six C1 readings screened C1-only on EUR/USD, one (MAMA vs FAMA) passed a multiple-testing bar; tested unchanged on two more
development pairs it failed on both, sitting mid-null. (c) The working premise "a C1 from this library gives D1 FX entries a
timing edge under this template" has no support yet. That is "no evidence of an edge", not "evidence of no edge": the
detectable edge size is limited (below).

## What was held fixed (the setting)

- (a) NNFX / VP rules as recorded in `docs/template/NNFX_TEMPLATE_DECISIONS.md` (T1-T11, M-D1..M-D8, R-D1..R-D7); slots are
  tested one at a time, C1 first, with the ATR risk profile [V05; A §5.1].
- (b) Zorro 3.11 Light-C template; D1 bars ending 17:00 New York; M1 (TICKS) history; spread x2 + asset-list rollover as the
  decision cost level; outcome unit **signal-R** (net P&L / actual stop distance, two equal halves averaged).
- (b) The Python engine reproduces Zorro: bars, indicator values and trades checked on EUR/USD (R1, PERF V1); bars and
  indicators on AUD/USD and EUR/JPY (C1S2 VB1 / VW1, 0 bars or values off).
- (b) Development pairs only (EUR/USD, AUD/USD, EUR/JPY D1). **The confirmation set has not been touched.** BTC/USD H4 (dev)
  not yet tested.

## The five studies

| Study | Question | Result (b) | Record |
|---|---|---|---|
| PERF1 | Strategy 1 v0 (FAMA baseline, Fisher 10 C1, Reflex 20 C2), EUR/USD | 325 signals, mean -0.030, t -0.87, without best year -12.9 R: **STOP** | `docs/preregistration/PERF1_Strategy1_EURUSD_Criteria.md` |
| PERF2 | Strategy 2 v0 (FRAMA, MESA Stochastic vs SMA(10) C1, Laguerre RSI C2), EUR/USD | 282 signals, mean -0.048, t -1.18, without best year -16.0 R: **STOP** | `PERF2_Strategy2_EURUSD_Criteria.md` |
| NULL1 | What does a C1 with random timing score under this template? | Null medians -0.025 (S1 slots) / -0.046 (S2 slots); PERF1 at the 42.7th, PERF2 at the 47.5th percentile | `NULL1_TemplateNull_Criteria.md` |
| C1S1 | Do any of 6 C1 readings (C1-only) beat a best-of-6 random-timing null on EUR/USD? | 1 of 6 passes: MAF, 205 signals, mean +0.101, t +1.48, 98.6th percentile of the max-null | `C1S1_C1Screen_EURUSD_Criteria.md` |
| C1S2 | Does MAF, unchanged, hold on AUD/USD and EUR/JPY? | AUD/USD mean -0.064 (25th pct of own null); EUR/JPY -0.064 (34th); negative even at zero cost: **MAF stops** | `C1S2_MAF_OtherPairs_Criteria.md` |

## What the evidence supports

1. (b) Both full strategies' results are ordinary draws from random C1 timing (NULL1). Their STOPs carry no information
   about which slot is to blame.
2. (b) In C1-only mode, 5 of 6 readings score at or below random timing on EUR/USD; the sixth (MAF) did not replicate on
   two more pairs. (c) The EUR/USD MAF reading is best explained as a selection effect (best of six, 205 signals): its
   pre-registered chance of passing both new pairs was put at about 1 in 5 before the winner's-curse discount, and both
   new readings sit inside their nulls rather than just under the bar.
3. (b) NULL1 found the Strategy 2 slot set losing about -0.028 R per signal **with no costs and random C1**. (c) Something in
   that combination (FRAMA baseline, LRSI C2, bridge-too-far) costs R independently of C1 timing; not investigated.
4. (b) Detection limit: one read of this size separates from its null only above roughly +0.013 to +0.032 R per signal
   (single-set 95th percentiles, NULL1); with a best-of-six correction the bar was +0.074 (C1S1). (c) A real C1 edge of a
   few hundredths of R per signal would usually go unseen by one pair's read; pooling pairs would raise the power.

## What it does not show

- (c) That C1 timing never works: only these six readings, at source defaults, on three D1 pairs, under this template's
  exits and costs.
- (c) Anything about the other slots in isolation (baseline, C2, volume, exits): not tested one at a time.
- (c) Anything about the confirmation set, other timeframes, or crypto.

## Variant count (carried forward)

Full-strategy variants: **2** (both STOP). C1-only readings: **6** on EUR/USD (1 shortlisted) + MAF on 2 more pairs (0
pass). No parameter was tuned on any result.

## Process notes (for the record)

- Every acceptance rule, null and prediction was committed before its run; misses are recorded (e.g. NULL1 x0 centres, C1S1
  bar 0.074 vs predicted 0.02-0.06, C1S2 EUR/JPY filler bars).
- Guards were seen to fire on planted defects (column-count guard, bar and wiring checks, offsets sha256, filler tests).
- Disclosures: Zorro summary lines seen during PERF2 runs (PERF2 A3.1) and once after PERF2 closed (C1S2 record); some
  checks ran before their build commits (NULL1 V1, C1S1 W0), disclosed in those files.
- Data and tooling problems found on the way became gotchas 9d.24-9d.26 (format-string count, holiday fills, gap filler bars).

## Open next questions (for decision, not decided here)

- B: the five untested C1 readings on AUD/USD + EUR/JPY with a pooled max-statistic null (clean data for those five).
- C: a different slot or market (exits / trailing; baseline as a filter; BTC/USD H4).
- Why the Strategy 2 slot set loses R at zero cost (NULL1 point 2).
