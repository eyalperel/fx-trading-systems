# NULL1 — The template's null distribution (random-timing C1) on EUR/USD D1 — Criteria

**Status:** pre-registered 2026-11-25, before any null code is written or run. Amendments are dated and appended below,
never edited in place (PROJECT_STATE §2.2).
**Decided:** planning chat 2026-11-25, one point at a time (decision N1: C -> B with D alongside; C1-C6 below, user: as
recommended on each). Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Purpose

Answer, before any slot-by-slot search (B): **what mean signal-R does a C1 with no timing edge produce under this
template's money management and costs, and what edge can a read of this size detect?** (c) PERF1 and PERF2 both read about
-0.02 R per signal before costs; without a null that number cannot be placed.

**Not a strategy test.** The null cannot reopen PERF1 or PERF2 (both STOP, final); for them it only describes. No variant
is selected here. (b) NULL1 never computes the real, unshifted, uninjected **C1-only** result of Fisher or MESA Stochastic:
those are B's likely first candidates, and their C1-only results stay unseen until B's own pre-registration (B counts them
in its K). The full-template real results are already known (PERF1 / PERF2 reports).

## Data and tools

- Bars: the PERF1 / PERF2 bars (rule (same, own), 5,490 EUR/USD D1 bars from 2005-03-29, cut by R1d run 1's RBAR rows; trade
  range = rows 520..5489, 4,970 bars). M1 history `C:/Zorro/History/EURUSD_*.t6` (P-4 sha256 list in the PERF reports).
- Engine: `analysis/template/reference_engine.py` + M1 layer (`tools/r1_replay.py`, holiday rule of PERF2 A3), verified
  trade-for-trade against Zorro (S4, R1a run 2, R2a run 3). Fill alternative (open, entry), the one Zorro fits.
- Slot values: reference models (`r1_replay.indicators` / `r2_replay.indicators`), equal to Zorro's (R1 / R2 W1).

## C1 — Configurations (decision C1: c)

| Set | Configuration | Real slots kept | C1 randomised |
|---|---|---|---|
| F1 | Full template, Strategy 1 v0 (FAMA, Reflex C2, bridge-too-far on) | baseline, C2, ATR | Fisher C1 |
| F2 | Full template, Strategy 2 v0 (FRAMA, Laguerre RSI C2, bridge-too-far on) | baseline, C2, ATR | MESA vs SMA(10) C1 |
| O1 | **C1-only**, Fisher C1 | ATR | Fisher C1 |
| O2 | **C1-only**, MESA vs SMA(10) C1 | ATR | MESA C1 |

**C1-only mode (c), our reading of VP's C1 test** ((a) V05: test C1 "with the ATR-based risk profile so wins and losses are
real"; A §5.1): entry at the next open on every C1 signal (T3.1 signal rule); no baseline gate, baseline exit, distance rule,
pullback, catch-up window or bridge-too-far; no C2, volume or exit slot; stop 1.5 x ATR, TP1 1 x ATR on half 1, breakeven,
trail, C1-flip exit exactly as variant 0 (T4, T5, M-D3); continuation logic not applicable (every C1 signal is a new entry).
Implemented as an engine parameter (`baseline_mode = "off"`), tested on hand-built cases before use (V3).

## C2 — Random process (decision C2: P3, circular shift)

For each offset k, the real C1 state series over the trade range (rows 520..5489) is rotated by k bars: state'[t] =
state[520 + ((t - 520 - k) mod 4970)]. Everything else (prices, baseline, C2, ATR) stays real. Rows 0..519 are not traded.
(b) Keeps the C1's signal count, run-length distribution and order exactly; breaks only its timing against price.
(c) Limitation: one wrap-around join per run; neighbouring offsets give correlated results (not 1,000 independent draws).

## C3 — Costs (decision C3: K1)

Spread x2 (0.00024, as P-3) once per half + rollover (asset-list RollLong -0.8947 / RollShort 0.4259 per 10,000 units per
day, whole days by the rule P5 confirmed, `tools/check_costs.py`, gotchas 9d.19), added to the engine. x0 (no costs) run
on the same offsets as a reading. R = net P&L / actual stop distance per half; signal-R as PERF1 P-1 (equal halves, so
signal-R = mean of the two half-R).

**V1 — cost-model check (must PASS before any null run).** The engine with costs, run on the **real** states, is compared
with Zorro's logs: S1 vs R1c run 1 (x2) and R1d run 1 (x1); S2 vs R2c run 1 (x2) and R2b run 1 (x1).
Pass, per log: (1) same number of halves; (2) >= 98% of halves equal in entry day, exit day and exit reason (M-D7 moves some
triggers); (3) |total signal-R engine - Zorro| <= 1.0 R and |mean signal-R difference| <= 0.005 R. All differences
reported. A FAIL stops NULL1 until a dated amendment.

## C4 — Number of runs (decision C4: R2)

1,000 offsets, drawn once without replacement from 260..4710 with `numpy.random.default_rng(20261125)`, sorted:
`analysis/null_template/NULL1_offsets.csv` (sha256 `f54e5308cd7daa7865b111e59f1af5b3b1a60b9733ec8f522ce9c84678753fa4`,
committed with this file; min 266, max 4707). The same offsets for every set and cost level (paired). Run in resumable
chunks; every run writes one row (set, cost level, offset, signals, halves, mean signal-R, total R, t); the results file's
sha256 is recorded before it is read.

## C5 — Positive control (decision C5: E3, drift injection)

Configurations O1 and O2 only (B's ruler). **Carrier:** the C1 state series shifted by **2,485 bars** (half the trade range;
not in the offset list), so the carrier has no real timing and the injected result reveals nothing about the real C1-only
result (Purpose). For drift level mu in {0.01, 0.02, 0.05} (x ATR per bar, (c) fixed band): for every trade-range bar t+1
after a closed bar t with carrier state s_t != 0, every M1 record of bar t+1 is moved by s_t x mu x ATR_t x f, f = the
record's time fraction of the bar (0 at the bar's open, 1 at its close); later bars carry the full amount (cumulative). ATR
stays that of the original data (c). The engine then runs (a) the carrier on the injected prices and (b) the 1,000 null
series of C2 (the real C1 shifted by each listed offset k, 266..4707: none near 0, so no null run carries the real timing),
on the same injected prices. (c) Offsets near 2,485 lie near the carrier's timing and partly carry the planted drift: this
makes detection slightly conservative, not easier.
**V2 — injection known-answer test (before use):** a synthetic flat series with states +1 for 3 bars then -1 for 2 must give
the hand-computed record prices exactly (<= 1e-12); planted defects (drift applied one bar early; f = 1 throughout) must
change the result.
Detection at level mu: the carrier's mean signal-R on injected prices >= the 95th percentile of its shifted null on the same
prices (one-sided). The carrier's resulting mean signal-R per level is reported (the detection bound in R).

## C6 — Reading (decision C6: Q2)

Statistic: mean signal-R at x2.
- **F1, F2 (describe only):** the real result's percentile in its own null (PERF1 -0.0304, PERF2 -0.0479 at x2); null
  mean, sd, 2.5 / 50 / 97.5 percentiles; same at x0. No verdict changes.
- **O1, O2:** null distribution and positive-control detection per level (Q1).
- **For B (fixed here, applied there):** B will pre-register its candidate count K before any candidate runs; a candidate
  passes the C1-only screen on EUR/USD only if its real mean signal-R exceeds the 95th percentile of the **max-statistic
  null**: for each offset, the best shifted result across all K candidates (same offsets, C1-only, x2). A pass is a
  shortlist, not acceptance (other dev pairs, C-3b, a P-3 read follow under their own pre-registrations).

## V3 — C1-only engine mode tests (before use)

Hand-built scenarios with known answers: entry on a C1 signal with price far from any baseline (refused in full mode,
entered in C1-only); no baseline exit; C1-flip exit; stop / TP1 / breakeven / trail unchanged versus full mode on a case
where the baseline never binds; a planted defect (baseline gate left on) must fail a test. Full-mode engine tests (33)
still PASS.

## Predictions (c)

- V1 PASS for both strategies at x1 and x2 (S4 / R1 / R2 equivalence, cost identity K4 per half).
- F1 / F2 null centre (median mean signal-R at x2) between -0.06 and -0.01 R (costs: spread x2 about -0.018 R per signal,
  swap about -0.011 R, PERF reports); the real PERF1 / PERF2 results between the 5th and 95th percentile of their nulls.
- x0 null centres within +-0.02 R of 0.
- Positive control: mu = 0.05 detected in O1 and O2; mu = 0.01 not detected in at least one; mu = 0.02 not predicted.

## Run order

1. Commit this file + the offsets file (before any null code runs).
2. Engine: rollover, `baseline_mode = "off"`; injection function; tests V2, V3; commit.
3. V1 on the real states (S1, S2; x1, x2): PASS required; record.
4. Null runs F1, F2, O1, O2 at x2 and x0 (8 x 1,000), chunked; results file sha256 recorded.
5. Positive control (O1, O2 x 3 levels x (1 carrier + 1,000 shifted)); sha256 recorded.
6. Read: report `analysis/null_template/NULL1_report.md`; results appended below as "NULL1 read 1".
A FAIL in 2-3 stops the sequence until a dated amendment.

## Variant count

No strategy variant is tested (PERF1 / PERF2 real results are re-used, not re-read; no real C1-only result is computed: the positive control uses a
shifted carrier, C5).
Project-wide strategy variants tested stays **2**. Null runs, cost levels and drift levels are measurements, not variants.

## Amendments

### Build (run order 2) and V1 run 1 — 2026-11-25 — **V1 PASS** (all four logs)

**Built (b):** `reference_engine.Params.baseline_mode` ("off" = C1-only, C1 table); `tools/null1.py` (costs, shift, injection,
V1, resumable null / positive-control runs; refuses offset 0 and an offsets file whose sha256 differs); tests
`analysis/template/tests/test_c1only_mode.py` (V3: 5 hand-calculated cases; planted defects "gate left on" 3 failures,
"baseline exit left on" 1 failure) and `tools/tests/test_null1.py` (V2 known answer <= 1e-12 on close and high; planted
"one bar early" in-test, "f = 1 throughout" by mutation: both fail; shift and cost arithmetic by hand). Regression: tools 150 /
150, engine 38 / 38 (33 earlier + 5 V3).
**Procedural note (b):** V1 was run before the build was committed (run order 2 says commit first). The code that ran V1 is the
code committed with this record, unchanged.

**V1** (`python tools/null1.py v1 C:/Zorro/Data C:/Zorro/History analysis/null_template/results/NULL1_V1.csv`, sha256
`e170946efef2e9054b13ca18675710f826fc3833c538a6a9e5f91b1566e70db0`):

| Log | Mult | Halves engine / Zorro | Same days + reason | Total signal-R engine / Zorro | Mean diff | Median / max half-R diff | Result |
|---|---|---|---|---|---|---|---|
| R1c run 1 | x2 | 650 / 650 | 644 (99.1%) | -10.25 / -9.87 | -0.0012 | 0 / 1.33 | PASS |
| R1d run 1 | x1 | 650 / 650 | 647 (99.5%) | -7.27 / -7.64 | +0.0012 | 0 / 0.49 | PASS |
| R2c run 1 | x2 | 564 / 564 | 561 (99.5%) | -14.04 / -13.52 | -0.0018 | 0 / 1.33 | PASS |
| R2b run 1 | x1 | 564 / 564 | 563 (99.8%) | -11.45 / -11.64 | +0.0007 | 0 / 0.03 | PASS |

(b) The median half matches exactly (cost model: spread, whole-day rollover by date difference); the few differing halves are
trigger-time differences from Zorro's ask / bid handling (M-D7), as predicted. All within the C3 limits (1.0 R total, 0.005 R
mean). The totals shown are the already-read PERF1 / PERF2 results, not new information. NULL1 may proceed to run order 4.
