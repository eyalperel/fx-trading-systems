# C1S3 — The five C1S1 non-survivors, C1-only, pooled over AUD/USD + EUR/JPY D1 — Criteria

**Status:** pre-registered 2026-11-26, before any result of FSH, MSS, RFX, ROF or LRS exists on AUD/USD or EUR/JPY and
before any code for this step is written. Amendments are dated and appended below, never edited in place (PROJECT_STATE §2.2).
**Decided:** planning chat 2026-11-26 (decision N3: B, with DIAG1 alongside; P-a; V-a; O-a; Q1-Q5; user: as recommended on
each). Branch `c1s3-pooled-c1-screen` off `main` 24fb559. Companion study: `DIAG1_S2Slots_ZeroCost_Criteria.md` (own verdict,
shares only the Zorro check click).
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Purpose

(a) A C1 must be consistent across pairs [V05]; VP tests C1 alone with the ATR risk profile [V05; A §5.1].
(b) C1S1 screened six readings on EUR/USD: five failed (FSH, MSS, RFX, ROF, LRS); MAF passed and then failed on AUD/USD and
EUR/JPY (C1S2). The five have never been run on AUD/USD or EUR/JPY: for them those pairs are clean data.
(c) This round asks whether any of the five beats a best-of-5 random-timing null when the two clean pairs are pooled (about
twice the signals of one pair, so a lower bar). It is the last C1-only round on the D1 FX dev set: with O-a below it either
closes that line or sends a survivor to a fresh market, never directly to C-3b.

## Candidates (K = 5, fixed; carried from C1S1 unchanged)

FSH, MSS, RFX, ROF, LRS exactly as defined in `C1S1_C1Screen_EURUSD_Criteria.md` "Candidates" (readings, parameters, inputs,
MSS start-up 0). No parameter or reading is changed after C1S1. MAF is not a candidate (stopped, C1S2).

## Data, ranges, mode, costs (carried from C1S2 unchanged)

- History, bars and ranges as `C1S2_MAF_OtherPairs_Criteria.md` "Data" and "Range": AUD/USD trades 2007-04-01 .. 2026-05-29;
  EUR/JPY 2012-02-01 .. 2026-01-15; LookBack 520; bars by the R1 rule; EUR/JPY with Zorro's 3 filler bars (C1S2 Amendment 1).
- C1-only engine mode (NULL1 C1, V3), fast M1 resolver (NULL1 A1).
- Decision cost level: **spread x2 + asset-list rollover**, constants as C1S2 "Mode, costs, statistic". Information rows
  (never decisive): x2 without rollover, x0.

## Statistic and null (decision P-a)

- **Pooled statistic:** signal-weighted pooled mean signal-R = (total R on AUD/USD + total R on EUR/JPY) / (signals on
  AUD/USD + signals on EUR/JPY). Also reported per pair and pooled: signals, halves, mean, t, total R, total R without the
  best calendar exit year (P-3 definitions).
- **Offsets:** C1S2's committed files, reused (drawn without reference to any indicator):
  `analysis/c1screen/C1S2_offsets_AUDUSD.csv` (sha256 69ffaa73280e71d3849468ee4ba521f1d75bd09b93df92d14d18bf0ed64e745c),
  `analysis/c1screen/C1S2_offsets_EURJPY.csv` (sha256 2a357ac8eb2c4b5c194f14aeb918b548e94ed4c1acb1531135f6dbeed8cc1bb3).
  Within a pair all five candidates are shifted by the same offset (as C1S1), keeping their correlation.
- **Joint pairing:** null draw i uses AUD/USD offset i (file order) and EUR/JPY offset pi(i), pi = a permutation of 0..999
  from `numpy.random.default_rng(20261126).permutation(1000)`, written to `analysis/c1screen/C1S3_pairing.csv` and its sha256
  recorded **before** any null run. (c) Random pairing, not sorted order: nearby offsets give similar results, and sorted
  pairing would couple those trends across pairs.
- **Max-statistic null:** for each draw i, the maximum over the five candidates of the pooled mean; its **95th percentile is
  the bar**. Also reported: each candidate's own pooled null (median, 5th / 95th percentiles).

## Pass rule (decision P-a)

A candidate passes C1S3 only if, at spread x2 + rollover:
1. its real pooled mean signal-R > the 95th percentile of the pooled max-statistic null; **and**
2. its real pooled mean > 0 **and** its real mean on each pair > 0; **and**
3. its real pooled total R with the best calendar exit year removed > 0.
Every candidate's result is reported, pass or not, with its percentile in its own pooled null and in the max-statistic null.

## What a result leads to (decision O-a)

- **0 survivors:** recorded as "no verified-library C1 reading (6) beats random timing on the three D1 FX dev pairs". The
  D1-FX C1-only line closes; the next step (BTC/USD H4, a different slot, or a rethink of the template) is a separate decision.
- **1+ survivors:** each recorded as "passes pooled AUD/USD + EUR/JPY, failed EUR/USD (C1S1)". **No direct path to C-3b.** A
  survivor may go forward, unchanged, only to a fresh test on data it has not seen (in the dev set: BTC/USD H4), under a new
  pre-registration. The confirmation set stays untouched.
- In no case is any parameter or reading changed on these results.

## Zorro checks before any read (decision V-a)

New script `strategies/tests/TPL_IND_PAIR.c` (`TPL_BARS_PAIR.c` stays unchanged): same bar settings, asset list, LookBack,
ranges and `bp`-style pair switch (`ip_Pair`: 1 = AUD/USD, 2 = EUR/JPY), compile-only switch, **no trades**. Logs INFO, RBAR
rows (as TPL_BARS_PAIR) and IND rows per bar: Fisher(10) on (H+L)/2 (Fish, trigger), MESA Stochastic(20, 48, 10) on Close
(output, Roof stage), SMA(10) of MESA by our own code (as `NNFX_Strategy2.h`) plus Zorro `SMA()` as cross-check X1, Reflex(20)
on Close, Laguerre RSI(0.5) on Close, and, for DIAG1, FRAMA(N = 32; (H+L)/2, High, Low) and ATR(14) MT4. Every `strf` carries
a specifier-count comment (gotchas 9d.24). One click per pair. Checker `tools/check_ind_pair.py`:
- **VC0** Zorro window: only `Error` lines pasted; `Error 047 ... no <year> history` accepted only with VB1 passing.
- **VB0** INFO settings as TPL_BARS_PAIR; >= 520 bars before the first trade bar.
- **VB1** Zorro's RBAR rows equal the Python bars (R1 rule, EUR/JPY fillers) on every day; every bar ends 17:00 New York.
- **VW2** every logged indicator value equals its reference model (1e-10 + 1e-9 |m|, as R1 W1); X1: own SMA vs Zorro SMA
  (1e-12 + 1e-12 |m|); the five state series from Zorro's values equal the model states (near-threshold |x| < 1e-9 counted,
  not failed).
Each check is first seen to fail on a planted defect (tests: e.g. a shifted bar, a wrong indicator length, a flipped state).
A FAIL stops this study until a dated amendment.

## Predictions (decision Q1-Q5; (c), committed before any build or run)

- **Q1** VB1 PASS on both pairs; VW2 PASS on every logged indicator, max error <= 1e-9; X1 agrees within 1e-12; 0 state
  differences (near-threshold count not predicted).
- **Q2** Pooled max-statistic 95th percentile in [+0.03, +0.07]. (Back-of-envelope: per-signal sd about 1.0 R (MAF C1S1:
  0.1012 x sqrt(205) / 1.48); pooled signals per candidate about 1.85 x EUR/USD = 800-1,690; SE 0.024-0.035; null centre about
  -0.03; best-of-5 95th about -0.03 + 2.2 x 0.035 = +0.05.)
- **Q3** Each candidate's pooled null median in [-0.06, -0.01].
- **Q4** 0 survivors is the most likely outcome (all five at or below random on EUR/USD); not a certainty.
- **Q5** Each candidate's real pooled mean lies inside the 5-95% range of its own pooled null. (A candidate below its own 5th
  percentile is reported as such: a reliably bad timing signal is also a finding.)

## Run order

1. Commit this file and the DIAG1 file (before any code for either).
2. Build `TPL_IND_PAIR.c`, `tools/check_ind_pair.py` + tests (planted defects), `tools/c1s3.py` (readings on the new pairs,
   pairing file, resumable null runs, pooled read with the P-a rule) + tests (hand-built pooled table, a planted per-pair
   negative mean must fail condition 2); commit.
3. User: compile check, then one click per pair; Claude copies each log to a run name without overwriting and runs the
   checker; VC0-VW2 PASS required; record (appended below).
4. Pairing file written and recorded; null runs (5 candidates x 2 pairs x 1,000); results sha256 recorded.
5. Read: real C1-only results of the five on both pairs; report `analysis/c1screen/C1S3_report.md`; appended below as
   "C1S3 read 1".

## Count

C1-only readings: this round adds the five C1S1 readings on 2 more pairs (K = 5 for the max-statistic; no new candidate).
Running total after this round: 6 readings on EUR/USD, MAF on 2 more pairs, these 5 on 2 more pairs. Project-wide
full-strategy variants: 2 (unchanged).

## Amendments

## Record: build part 1, the Zorro check (2026-11-26)

- Run order step 2 is done in two commits, both before any null run or read: (1) `strategies/tests/TPL_IND_PAIR.c`,
  `tools/check_ind_pair.py`, `tools/tests/test_check_ind_pair.py` (this commit); (2) `tools/c1s3.py`, `tools/diag1.py` + tests.
- (b) `strf` specifier counts checked by script: 26 / 26 (INFO), 2 / 2 (ASSETFAIL), 21 / 21 (RIND, 22 fields with the kind).
- (b) Tests 9 / 9: consistent input passes; planted defects fail exactly their own items: one FRAMA value (frama), Fisher(11)
  for Fisher(10) (fish, trig), LRSI mirrored on one bar (lrsi, state_LRS), Zorro SMA off (X1_sma), counter off (nmesa), first
  defined SMA off (sma), one row missing (rows), INFO parameters (5 cases), a 21-field RIND row (refused). VB1 reuses
  `check_r1.match_bars` / `check_bar_times` / fillers, whose planted cases are in `test_check_r1.py` and `test_fillers.py`.
  All tools tests 176 / 176 OK (VM shell, python 3.10, numpy 2.2.6).
- `ip_CompileOnly = 1` in the committed file.

### Prediction for the compile check (written before the click)

- Zorro prints `TPL_IND_PAIR: compile check only (ip_CompileOnly = 1), nothing run` and `compile check done`; no Error line.

## Record: compile check (2026-11-26)

- Build part 1 committed 530eec1. (b) Zorro printed `TPL_IND_PAIR: compile check only (ip_CompileOnly = 1), nothing run` and
  `compile check done`, no Error line. Prediction met. `ip_CompileOnly` set to 0 for the pair runs (`ip_Pair = 1` AUD/USD
  first, then 2 EUR/JPY).

### Prediction for the pair runs (written before the clicks)

- Zorro output: AUD/USD no Error line; EUR/JPY at most `Error 047: EUR/JPY no 2009 history` (as C1S2's bar runs).
- check_ind_pair: VB0, VB1 (rule (same, own), 0 off; EUR/JPY with the 3 fillers), VW2 PASS on both pairs; every indicator
  max error <= 1e-9; X1 within 1e-12; 0 state differences on all five ids (Q1).
- (c) The bars are those of C1S2's checks (same settings, same history files): AUD/USD 0 bars off, EUR/JPY 4,346 bars.

## Record: pair run AUD/USD (2026-11-26) — PASS

- Committed before the click: 15c9202. Zorro output: no Error line (prediction met). Log copied (no overwrite) to
  `Zorro/Data/IND_AUDUSD_log_run1.csv` (sha256 1c78f4ddc3b170abd2cf42f912d99b2e2a3dcadb8404a6a25cd62cd5d5e62f4f; 5,890 RIND rows).
- Checker (VM shell, python 3.10): `analysis/c1screen/results/C1S3_VW_AUDUSD_run1.csv`. **RUN PASS.** VB0 no asset fail,
  info (settings, costs, indicator parameters), lookback 520; VB1 rule (same, own) 0 off (other rules 465-683 off), all bars
  end 17:00 NY, first bar 2005-06-29 (diff 3.3e-11, not replaced); VW2 fish, trig, mesa, roof, sma, reflex, lrsi, frama, atr,
  tr 0 rows off (max error 1.2e-13, mesa), nmesa exact, X1 0 off (max 0), states FSH / MSS / RFX / ROF / LRS 0 differ, 0
  near-threshold. Predictions met.
- `ip_Pair` set to 2 (EUR/JPY) for the second click.

## Record: pair run EUR/JPY (2026-11-26) — PASS; Q1 met on both pairs

- Committed before the click: 973528f. Zorro output: one `Error 047: EUR/JPY no 2009 history` (allowed, VB1 passes;
  prediction met). Log copied (no overwrite) to `Zorro/Data/IND_EURJPY_log_run1.csv` (sha256
  d96a3019e0e216e1272080ebddebb374981eab694e90dd83ae32ba34deb1d604; 4,346 RIND rows).
- Checker: `analysis/c1screen/results/C1S3_VW_EURJPY_run1.csv`. **RUN PASS.** VB0 PASS; VB1 rule (same, own) 0 off with the 3
  fillers (other rules 294-522 off), bar times PASS, first bar 2010-05-23 (diff 4.7e-11, not replaced); VW2 all ten indicators
  0 rows off (max error 3.3e-11, tr; (c) larger than AUD/USD because JPY prices are ~130 printed with 15 decimals), nmesa exact,
  X1 0 off, states FSH / MSS / RFX / ROF / LRS 0 differ, 0 near-threshold.
- **VC0-VW2 PASS on both pairs: run order step 3 complete (Q1 met).** The DIAG1 inputs (MESA, SMA, LRSI, FRAMA, ATR) are
  covered by the same checks. Next: build part 2 (`tools/c1s3.py`, `tools/diag1.py` + tests), committed before any null run.
