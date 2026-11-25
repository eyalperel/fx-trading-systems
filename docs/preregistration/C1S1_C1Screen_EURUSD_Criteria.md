# C1S1 — C1-only screen of the verified library on EUR/USD D1 (step B, first round) — Criteria

**Status:** pre-registered 2026-11-25, before any real C1-only result of any candidate exists. Amendments are dated and
appended below, never edited in place (PROJECT_STATE §2.2).
**Decided:** planning chat 2026-11-25 (decision N1: C -> B; NULL1 C6 Q2; B1: K-b; B2: R-b; user: as recommended on each).
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Purpose

(a) VP tests the slots one at a time, C1 first, "with the ATR-based risk profile so wins and losses are real" [V05; A §5.1],
and a C1 must hold across pairs [V05]. This round screens every C1-capable reading of the already verified library on
EUR/USD in C1-only mode against the random-timing null of NULL1. A pass is a **shortlist entry**, not acceptance.

## Candidates (K = 6, fixed; decision B1: K-b)

One reading each, source defaults, no parameter variation. Inputs as their verified files; every slot value equals Zorro's on
these bars (R1 / R2 W1: MAMA / FAMA, Fisher, Reflex, MESA incl. its Roof stage, Laguerre RSI).

| # | Id | Reading (state +1 / -1 / 0, T3.1) | Type (V05) | Basis |
|---|---|---|---|---|
| 1 | FSH | sign(Fish - Fish[1]), Fisher(10) on (H+L)/2 | two-lines | (a) TASC V.20:11 "Fish and Fish delayed by one bar give a crossover system" |
| 2 | MSS | sign(MESA - SMA(10) of MESA), MESA Stochastic(20, 48, 10) on Close; 0 until 10 outputs | two-lines | (a) V.32:1, [V18]; reading (c), T3 amendment 1 |
| 3 | MAF | sign(MAMA - FAMA), MAMA(.5, .05) on (H+L)/2 | two-lines (on chart) | (a) TASC V.19:9 "The crossover of MAMA and FAMA is a good trend signal" |
| 4 | RFX | sign(Reflex), Reflex(20) on Close | zero cross | (c) no rule in the article; Stonehill tested a zero cross (C12) |
| 5 | ROF | sign(Roof), Roofing Filter(48, 10) on Close | zero cross | (b) zero-mean oscillator (V.32:1); Stonehill: zero cross better than two-lines (C7) |
| 6 | LRS | sign(LRSI - 0.5), Laguerre RSI(0.5) on Close | midline = zero cross (C21) | (c) our reading (T3.2); (b) pins at 0 / 1 in trends |

Other readings (Fisher zero cross, Reflex 50, other lengths, colour changes) are not in this round; each would be a new
counted candidate in a new round with its own K.

## Mode, data, costs, statistic

C1-only engine mode (NULL1 C1, `baseline_mode = "off"`, V3), the PERF bars (5,490, trade range rows 520..5489), M1 layer
(fast resolver, NULL1 Amendment 1), costs spread x2 + rollover (NULL1 C3, V1), statistic mean signal-R; also t, total R,
total R without the best exit year (P-3 definitions), signals, halves. The engine is the instrument (V1: equal to Zorro on
99.1-99.8% of halves, medians exact); a survivor gets its own Zorro read later.

## Null (NULL1 C2 / C4 / C6)

For each candidate, its own C1 series circularly shifted by each of the 1,000 offsets of `NULL1_offsets.csv` (sha256
`f54e5308...`), C1-only, x2. FSH and MSS reuse NULL1's O1 / O2 x2 rows (same engine, mode, costs; sha256 `201a14f9...`);
MAF, RFX, ROF, LRS are run new (4 x 1,000). **Max-statistic null:** for each offset, the maximum of the six candidates'
shifted mean signal-R; its 95th percentile is the bar.

## Pass rule (decision B2: R-b)

A candidate passes the EUR/USD screen only if, at x2:
1. its real mean signal-R > the 95th percentile of the max-statistic null; **and**
2. its real mean signal-R > 0; **and**
3. its real total R with the best exit year removed > 0.
Every candidate's result is reported (pass or not): mean, t, total, total without the best year, its percentile in its own
null and in the max-statistic null.

**0 survivors:** recorded as "no verified-library C1 beats random timing on EUR/USD under this template"; the next step
(a K-c round, or a rethink of the template) is a separate decision. **1+ survivors:** all go forward unchanged (none
dropped or preferred by EUR/USD numbers beyond the rule) to the other dev pairs (step D's data), each pair with its own null
run, under a new pre-registration; then C-3b (C2) and a full P-3 read in Zorro.

## Checks before the read

- **W0:** the six real state series are built from the reference models on the PERF bars; for FSH and MSS they equal the
  states of the R1 / R2 checks (S1 0 differences); MAF, RFX, ROF, LRS take values W1 already compared with Zorro on these
  bars (R1d / R2a run 3 IND files): each state series is recomputed from those IND files and must equal the model's except
  near-threshold bars (|x| < 1e-9), counted.
- **Null rows:** 6 x 1,000 x2 rows available, 0 duplicates; the new rows' file sha256 recorded before the read.
- No real C1-only result of any candidate is computed before W0 and the null rows are complete and recorded.

## Predictions (c)

- W0: 0 state differences on all six (near-threshold count not predicted).
- Max-statistic 95th percentile between +0.02 and +0.06 R (NULL1: single-set 95th percentiles +0.013 to +0.032).
- **0 survivors** is the most likely outcome (NULL1: both full strategies sit at the 43rd / 48th percentile of their nulls);
  not a certainty.

## Run order

1. Commit this file (before any C1-only real result exists).
2. `tools/c1s1.py`: readings, W0, null runs (resumable), read; tests (a planted wrong reading, e.g. FSH sign flipped, must
   fail W0; the max-statistic and pass rule on a hand-built table); commit.
3. W0; null runs for MAF, RFX, ROF, LRS; record sha256.
4. Read: real C1-only results of all six; report `analysis/c1screen/C1S1_report.md`; results appended below as
   "C1S1 read 1".

## Variant count

C1-only screen readings tested: **6** (this round). Project-wide strategy variants (full-template reads) stay 2.

## Amendments

### Build, W0 and null runs (run order 2-3) — 2026-11-25 — W0 PASS; nulls complete; recorded before any real C1-only result

**Built (b):** `tools/c1s1.py` (readings, W0, resumable null runs via `null1`'s driver, read with the R-b rule; refuses a
sha256 mismatch and never overwrites) and `tools/tests/test_c1s1.py` (4 tests: hand-set reading values incl. on-the-line 0
and the MSS start-up 0; W0 identical case and **planted FSH sign flip** (FSH fails, the other five unaffected);
near-threshold difference counted, not failed; max-statistic and R-b on a hand-built table incl. a negative bar and a
missing candidate row).
**Procedural note (b):** as in NULL1, W0 and the null runs ran before the build commit; the code is committed unchanged with
this record.

**W0 (b)** (`analysis/c1screen/results/C1S1_W0.csv`, sha256 `faaee5817b455c9edb66f25d961c514610d5fada7b26f6d207081143a3835062`):
all six state series recomputed from Zorro's logged indicator values (R1d run 1 IND for FSH / MAF / RFX; R2a run 3 IND for
MSS / ROF / LRS) equal the model's on the 4,970 trade-range bars: **0 differences, 0 near-threshold, on every id. PASS**
(prediction: 0 differences, met).

**Null rows (b):** `analysis/c1screen/results/C1S1_null_runs.csv`: MAF, RFX, ROF, LRS x 1,000 offsets at x2, 0 duplicates,
sha256 `788e5fc4fd204c40ac8153109d31c003b962336c00e75bb4219dc8d2eaf405a6`. FSH / MSS: NULL1 O1 / O2 rows (sha256
`201a14f904d5e559...`). Only row counts were inspected. No real C1-only result has been computed.

## C1S1 read 1 — 2026-11-25 — **1 survivor: MAF (MAMA vs FAMA)**

`python tools/c1s1.py read C:/Zorro/Data C:/Zorro/History analysis/null_template/results/NULL1_null_runs.csv
analysis/c1screen/results/C1S1_null_runs.csv 201a14f904d5e559 788e5fc4fd204c40 analysis/c1screen/C1S1_report.md` (both sha
prefixes verified). Report `analysis/c1screen/C1S1_report.md` (sha256 `eab0ca96dc8e10c84600b4cd0d0ca002e2d7b02024831a90658ef579503dc2ee`).

**Max-statistic null (b):** best of six per offset: median +0.0140, **95th percentile +0.0739** (the bar).

| Id | Signals | Mean signal-R x2 | t | Total R | Total w/o best year | Own-null pct | Max-null pct | Pass |
|---|---|---|---|---|---|---|---|---|
| FSH | 914 | -0.0129 | -0.54 | -11.75 | -18.68 | 70.1% | 16.2% | no |
| MSS | 505 | -0.0224 | -0.59 | -11.31 | -19.41 | 55.7% | 9.4% | no |
| **MAF** | **205** | **+0.1012** | **+1.48** | **+20.74** | **+14.47** (best 2010, +6.27) | 98.8% | **98.6%** | **PASS** |
| RFX | 433 | -0.0129 | -0.31 | -5.60 | -12.93 | 65.0% | 16.2% | no |
| ROF | 442 | -0.0749 | -1.83 | -33.12 | -39.34 | 11.2% | 0.0% | no |
| LRS | 463 | -0.0465 | -1.14 | -21.51 | -24.48 | 30.0% | 1.4% | no |

**Predictions:** max-statistic 95th in [+0.02, +0.06]: **NOT met** (+0.0739; (c) the six candidates' shifted results are
more spread than NULL1's single sets suggested, notably MAF's: few signals, so a noisier mean). "0 survivors most likely":
**NOT met** (1 survivor).

**Reading (c).**
1. MAF passes every R-b condition: above the max-statistic bar (the multiple-testing correction over all six), positive
   mean, positive without its best year.
2. It is a screen pass on one asset with 205 signals; t = +1.48 alone would not pass P-3's evidence line (t >= 2). The
   max-statistic percentile (98.6%) says roughly 1.4% of random-timing draws give a best-of-six this good.
3. (a) It is also the one reading whose trading rule is stated by its source ("The crossover of MAMA and FAMA is a good
   trend signal", TASC V.19:9); the other five are our or Stonehill's readings. Noted, not used as evidence.
4. Per the pre-registered rule, MAF goes forward unchanged; the five others are recorded as failures of this screen.
   Next (pre-registered here): MAF C1-only on the other dev pairs (step D's data), each with its own null, under a new
   pre-registration; then C-3b (C2) and a full P-3 read in Zorro. **No parameter or reading of MAF is changed on EUR/USD.**

**Count:** C1-only screen readings tested: 6 (1 shortlisted). Project-wide full-strategy variants: 2.
