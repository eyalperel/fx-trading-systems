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

## Record: build part 2 (2026-11-26, before any null run)

- `tools/c1s3.py` (load from the TPL_IND_PAIR logs, offsets with sha256 check, pairing P-a, resumable null runs writing all
  five ids per offset, pooled read with the P-a rule; refuses partial offsets, duplicates, a sha mismatch, overwrites) +
  `tools/tests/test_c1s3.py` (7 tests: pairing deterministic, complete, not sorted, seed-dependent; pooled stats and best
  year; signal-weighted pooled null and draw maximum on a hand-built table, planted pairing reuse detected; each pass
  condition fails alone, incl. the **planted per-pair negative mean** (EUR/JPY -0.01 with the pooled mean above the bar);
  duplicate null row refused). With `tools/diag1.py` + 9 tests (DIAG1 record): all tools tests 192 / 192 OK (VM shell).
- Smoke test (load only, no engine run): EUR/JPY 4,346 bars / 3,826 trade bars (= C1S2), both offset files pass sha256.
  Disclosure: it printed each reading's share of +1 states on EUR/JPY's trade range (FSH .508, MSS .489, RFX .500, ROF .506,
  LRS .538): an input property, no trade or R computed.
- Next: run order step 4 (pairing file + sha256 recorded, then null runs).

## Record: pairing written (2026-11-26, before any null run)

- Build part 2 committed bab6aed. `python tools/c1s3.py pairing` (exclusive create): `analysis/c1screen/C1S3_pairing.csv`,
  1,000 draws; AUD/USD offsets in file order (1,000 unique), EUR/JPY offsets permuted by
  `numpy.random.default_rng(20261126).permutation(1000)` (1,000 unique, not sorted); draw 0 = (267, 1402).
  sha256 **d722f2849afc03c403fb4c67ed986f4149013fa31a824130a32070db77b0a5a7**.
- Next: null runs (5 ids x 2 pairs x 1,000) into `analysis/c1screen/results/C1S3_null_runs.csv`.

## Record: null runs (2026-11-26, before the real reading)

- Pairing committed 5836658. `tools/c1s3.py null` per pair (VM shell, 2 workers), x2 + rollover, C1-only. A first background
  run was stopped when its shell call ended (182 complete offsets, 0 partial; resumable by design); the rest ran in
  foreground chunks of about 155 s.
- File `analysis/c1screen/results/C1S3_null_runs.csv`: **10,000 rows** (5 ids x 2 pairs x 1,000), 0 duplicates, offsets equal
  the committed offset files for every id and pair, 0 NaN means; signals per run: AUD/USD min 430, EUR/JPY min 318.
- sha256 **e609197f389b280a1c459e469bac2c011c99990db27a2724a8e924d7a23f8567**.
- Disclosure: while checking the stopped run, one `tail` printed the last 5 null rows (AUD/USD offset 1106, one row per id).
  Null values only; no pooled null, bar or real C1S3 result had been computed. The real reading is computed only by
  `c1s3.py read`, after this commit.

## C1S3 read 1 (2026-11-26) — 0 survivors; the D1-FX C1-only line closes

`python tools/c1s3.py read <IND_AUDUSD_log_run1.csv> <IND_EURJPY_log_run1.csv> <History> analysis/c1screen/results/C1S3_null_runs.csv
e609197f389b280a analysis/c1screen/C1S3_report.md` (null file committed e8d9592; sha prefix verified). Report
`analysis/c1screen/C1S3_report.md`.

**Pooled max-statistic null (b):** best of 5 per draw: median -0.0035, **95th percentile +0.0344** (the bar).

| Id | Signals AUD / JPY | Pooled mean x2 | t | Total w/o best year | AUD/USD | EUR/JPY | Own-null median (5th / 95th) | Own pct | Max pct | Pass |
|---|---|---|---|---|---|---|---|---|---|---|
| FSH | 999 / 685 | -0.0186 | -1.04 | -42.66 | -0.0123 | -0.0277 | -0.0277 (-0.0560 / +0.0026) | 68.6% | 22.4% | no |
| MSS | 537 / 375 | -0.0423 | -1.48 | -44.33 | -0.0486 | -0.0334 | -0.0294 (-0.0750 / +0.0144) | 32.0% | 1.4% | no |
| RFX | 479 / 331 | -0.0031 | -0.10 | -16.94 | +0.0270 | -0.0467 | -0.0285 (-0.0770 / +0.0200) | 81.3% | 51.1% | no |
| ROF | 431 / 320 | -0.0431 | -1.34 | -46.67 | +0.0067 | -0.1102 | -0.0289 (-0.0805 / +0.0222) | 32.9% | 1.2% | no |
| LRS | 475 / 338 | -0.0463 | -1.56 | -46.26 | -0.0419 | -0.0525 | -0.0291 (-0.0743 / +0.0170) | 24.2% | 0.7% | no |

Information (never decisive), pooled: x2 without rollover FSH -0.0150, MSS -0.0367, RFX +0.0015, ROF -0.0380, LRS -0.0415;
x0 FSH +0.0063, MSS -0.0152, RFX +0.0230, ROF -0.0161, LRS -0.0202.

**Predictions:** Q1 met (records above). Q2 bar in [+0.03, +0.07]: **met** (+0.0344). Q3 own-null medians in [-0.06, -0.01]:
**met** (-0.0277 .. -0.0294). Q4 0 survivors most likely: **met**. Q5 every real pooled mean inside its own null's 5-95%:
**met** (all five; own-null percentiles 24.2-81.3%).

**Reading.**
1. (b) No candidate meets any of the three P-a conditions except per-pair positivity on one pair each (RFX, ROF on AUD/USD).
2. Per O-a: recorded as "**no verified-library C1 reading (6) beats random timing on the three D1 FX dev pairs**". The
   D1-FX C1-only line closes; the next step (BTC/USD H4, a different slot, or a rethink of the template) is a separate decision.
3. (c) With about twice one pair's signals the bar fell from +0.074 (C1S1) to +0.034; every reading sits inside its own
   random-timing null, none reliably below it either (Q5). The detectable pooled edge for one reading is roughly +0.03 R per
   signal above its null median at this cost level; a smaller true edge is not excluded.
4. No parameter or reading is changed on these results.

**Count:** C1-only readings: 6 on EUR/USD (C1S1), MAF on 2 more pairs (C1S2), these 5 on 2 more pairs (C1S3, K = 5): 0 pass on
more than one pair. Project-wide full-strategy variants: 2 (unchanged).
