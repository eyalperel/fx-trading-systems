# FINDINGS 2 — C1 timing closed on D1 FX, and why: no trend memory to time (2026-11-26 .. 11-27)

**Status:** write-up of three pre-registered studies (C1S3, DIAG1, PREM1) and two correction records; no new test. Numbers are
copied from the run records named in each row. Follows `FINDINGS1_C1_Timing_D1FX.md`.
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Short answer

(b) No reading from the verified indicator library times D1 FX entries better than random on any of the three dev pairs once
multiple testing is accounted for (C1S1-C1S3). The one unexplained template number (Strategy 2's slots losing R with random C1)
is path noise plus some rollover (DIAG1). And the pairs' own returns show no directional memory at 2-60 days above the
detection bounds, with a weak, non-significant tilt toward reversal (PREM1). (c) The C1 failures are therefore best read as
"nothing strong to time on these pairs at these horizons", not as poor indicators or a broken template. That is "no evidence of
strong memory", not "evidence of no memory": bounds below.

## The three studies

| Study | Question | Result (b) | Record |
|---|---|---|---|
| C1S3 | Do the five C1S1 readings (FSH, MSS, RFX, ROF, LRS), C1-only, beat a pooled best-of-5 random-timing null on AUD/USD + EUR/JPY (clean data for them)? | Bar +0.034; pooled means -0.046 .. -0.003; every reading inside its own null's 5-95%: **0 survivors** | `docs/preregistration/C1S3_FiveC1_Pooled_Criteria.md` |
| DIAG1 | Does Strategy 2's slot set lose R with random C1 at true zero cost, and which part? | Pooled -0.0105 (calendar-year jackknife z -0.87), EUR/JPY +0.004; no component (baseline, bridge-too-far, C2) at z <= -2; random C1 alone -0.0015 (z -0.33): **not distinguishable from path noise** | `DIAG1_S2Slots_ZeroCost_Criteria.md` |
| PREM1 | Do the pairs' daily returns carry directional memory at q = 2-60 days (variance ratios, random-sign null)? | Max \|z\| 1.33 vs bar 2.41 (stochvol 1.52 vs 2.46); pooled VR - 1 between -0.074 and -0.009 at every q: **no horizon flagged** | `PREM1_D1FX_Predictability_Criteria.md` |

## What the evidence supports

1. (b) Across C1S1-C1S3, 6 readings were screened on 3 pairs; none passes on more than one pair; on clean data none is outside
   its random-timing null in either direction.
2. (b) NULL1's EUR/USD "zero-cost" -0.028 split into about -0.008 rollover (NULL1's x0 rows included it) and -0.021 one-path
   noise; on the other two pairs the same slots read -0.011 and +0.004.
3. (b) The template measures no bias: random C1 at true zero cost scores -0.0015 R per signal (DIAG1 A4).
4. (b) Detection bounds (PREM1 positive control, 90%): lag-1 memory phi >= 0.05; 20-day momentum kappa >= 0.30 (trend side
   >= 0.20, i.e. pooled VR(20) about 1.23, VR(40) about 1.37). Real values sit inside the null at every horizon.
5. (c) Taken together: on EUR/USD, AUD/USD and EUR/JPY D1, a price-only trend-timing rule has no strong memory to work with at
   NNFX holding horizons.

## What it does not show

- (c) That no trend premium exists: one weaker than the PREM1 bounds would be invisible to PREM1 and to any single C1 read.
- (c) Anything about other markets (BTC/USD H4 untested), other timeframes, or non-price information.
- (c) Anything about the confirmation set (untouched).

## Corrections made on the way

- **NULL1 Amendment 2:** NULL1's x0 rows included rollover (`null1.half_r` adds it at every multiplier); wording corrected in
  NULL1, FINDINGS1 and PROJECT_STATE; no verdict changed.
- **DIAG1 Amendment 2:** the G0 guard's tolerance (5e-7) sat exactly at half a unit of NULL1's 6th stored decimal; 2 of 2,000
  offsets failed on half-way rounding; tolerance 5e-7 + 1e-9, failure kept on record.
- **PREM1 Amendment 1:** the momentum ladder missed 90% on the negative side at 0.20; extended to 0.30 / 0.40 before the read,
  bound rule unchanged.
- Missed predictions recorded as such (e.g. my rollover back-of-envelope about 2.5x too high; PREM1 U2 sd, U4).

## Variant count (carried forward)

Full-strategy variants: **2** (both STOP). C1-only readings: 6 on EUR/USD, MAF on 2 more pairs, the other 5 on 2 more pairs (0
pass on more than one pair). DIAG1: 5 diagnostic arms; PREM1: premise test (no variant). No parameter was tuned on any result.

## Open next question (for decision, not decided here)

- BTC/USD H4 (the one untested dev market; different volatility structure; outside NNFX's FX D1 sources) vs stopping D1-FX
  price-timing. Before a large BTC build, a PREM1-style premise test on BTC H4 would be the cheap first step (c).
