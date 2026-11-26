# C1S2 — MAMA vs FAMA (C1-only) on the other dev pairs: AUD/USD and EUR/JPY — Criteria

**Status:** pre-registered 2026-11-25, before any MAF result exists on either pair and before any code for this step is
written. Amendments are dated and appended below, never edited in place (PROJECT_STATE §2.2).
**Decided:** planning chat 2026-11-25 (D1: E1; G1; P1: W1; P2: A; P3: K1; P4: V-b; user: as recommended on each).
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

## Purpose

(a) A C1 must be consistent across pairs [V05]. C1S1 shortlisted one reading on EUR/USD: **MAF** = sign(MAMA - FAMA),
MAMA(.5, .05) on (H+L)/2 (TASC V.19:9). This step tests MAF **unchanged** (no parameter, reading or rule changed after
C1S1) on the two other FX dev pairs (PROJECT_STATE §2.1). Nothing is selected here: one fixed candidate on new data.

## Data (D1: E1, G1)

Zorro free M1 packages (zorro-project.com/download.php, linked from the Zorro 3.11 manual history.htm), the same source family
as the EUR/USD files (installed by the Zorro setup, `Setup.log`). Copied into `C:/Zorro/History` 2026-11-25 (EUR/USD files
verified unchanged by sha256):
- **AUD/USD** `AUDUSD_2002..2026.t6`: "Forex M1 History 2002-2009" (2002-2009), "Forex/CFD M1 History 2010-2019",
  "Forex/CFD M1 History 2020+"; 8,556,543 records after removing 24,353 repeats (gotchas 9d.23); 2002-01-02 .. 2026-05-29.
- **EUR/JPY** `EURJPY_2010..2026.t6`: "Forex-28 M1 History 2010-2022" (holds 2010-2026); 5,925,178 records after 13,894
  repeats; 2010-01-03 .. **2026-01-15**. **Hole (b): 2017-12-11 23:34 -> 2018-01-01 21:57 UTC** (no records). Used as is
  (G1); trades open across the hole are counted and listed in the report.
Every history file's sha256 is listed in the report.

## Range (P1: W1)

LookBack 520 bars as EUR/USD (warm-up only, no decisions).
- **AUD/USD:** trades 2007-04-01 .. 2026-05-29 (StartDate 20070401, EndDate 20260529), the EUR/USD dates.
- **EUR/JPY:** trades from StartDate **2012-02-01** (c: about 520 trading bars after 2010-01-04, with a margin) .. EndDate
  **2026-01-15**. Gate (b): Zorro's first trade bar must have >= 520 bars before it (VB0 below); if not, a dated amendment
  moves StartDate before any read.

## Mode, costs, statistic (P3: K1)

C1-only engine mode (NULL1 C1, V3), M1 layer (fast resolver, NULL1 A1), bars by the R1 rule ((same, own) + holidays,
`tools/r1_data.py`) cut to Zorro's bars from VB1. Costs **spread x2 + asset-list rollover** (`config/assets/AssetsNNFX_FX.csv`):
AUD/USD spread 0.00008, RollLong -0.0968, RollShort +0.0454, PIP 0.0001, PIPCost 0.08561; EUR/JPY spread 0.023, RollLong
+0.2828, RollShort -0.6068, PIP 0.01, PIPCost 0.058102; LotAmount 1000; rollover in price units = days x rate x 1000 / 10000
/ (PIPCost / PIP), days as NULL1 C3. Information rows (never decisive): x2 without rollover, x0. (c) Rollover is a
2025-07-28 snapshot; if a pair's verdict differs between x2 with and without rollover, the report says so.
Statistic: mean signal-R; also t, total R, total without the best exit year (P-3 definitions), signals, halves.

## Null (P2)

Per pair: MAF's own state series over that pair's trade range, circularly shifted by 1,000 offsets drawn once without
replacement from 260 .. L - 260 (L = the pair's trade-range bar count) with `numpy.random.default_rng(20261125)`, sorted;
written to `analysis/c1screen/C1S2_offsets_<pair>.csv` with sha256 recorded **before** any null run. C1-only, same costs.

## Pass rule (P2: A)

MAF passes this step only if **on each pair**, at x2 with rollover:
1. real mean signal-R > the 95th percentile of its own null on that pair; **and**
2. real mean signal-R > 0; **and**
3. real total R with the best exit year removed > 0.
**Both pairs pass:** MAF goes on to C-3b (a C2, `C2_Selection_Criteria_PreRegistered.md` Amendment 1) and then a full P-3 read
in Zorro, each under its own pre-registration. **Either pair fails:** MAF stops, recorded as "passes on EUR/USD only"; the next
step is a separate decision. No parameter of MAF is changed in either case.

## Zorro checks before any read (P4: V-b)

New script `strategies/tests/TPL_BARS_PAIR.c` (switch `bp_Pair`: 1 = AUD/USD, 2 = EUR/JPY; bars + indicators only, **no
trades**, no account figures): template bar settings (BarZone EST, BarOffset 17:00, StartWeek 71700, Fill 3, TICKS, TR_FRC),
the project asset list, LookBack 520, the pair's StartDate / EndDate; logs INFO, RBAR (as R1) and IND (MAMA, FAMA, period,
alpha, phase, ATR, TR) per bar. One click per pair. Checker `tools/check_bars_pair.py`:
- **VC0** Zorro window: only `Error` lines pasted; `Error 047 ... no <year> history` accepted only with VB1 passing (as R1
  Amendment 2.1); any other `Error` fails.
- **VB0** INFO settings as above; >= 520 bars before the first trade bar.
- **VB1** Zorro's RBAR rows equal the Python bars of the R1 rule on every day (first bar exempt if partial, gotchas 9d.14);
  every bar ends 17:00 New York (within 1 s).
- **VW1** MAMA, FAMA, period, alpha, phase, ATR, TR equal the reference models on those bars (1e-10 + 1e-9 |m|, as R1 W1);
  the MAF state series from Zorro's MAMA / FAMA equals the model's (near-threshold bars counted, not failed).
Each check is first seen to fail on a planted defect (tests). A FAIL stops this step until a dated amendment.

## Predictions (c)

- VB1 / VW1 PASS on both pairs (same bar builder and indicator code as EUR/USD); EUR/JPY's hole gives no failed bar (no
  records, no bar on either side).
- MAF passes on both pairs: not predicted. (c) Prior from C1S1: one shortlisted reading at the 98.6th percentile of a
  best-of-six null, t +1.48. If its true edge were exactly the EUR/USD estimate and each pair had a similar signal
  count, one pair's 95% bar would be passed about 40% of the time (z 1.48 vs 1.645) and both about 1 in 5; selection as the
  best of six makes the EUR/USD estimate likely too high (winner's curse), so lower still.

## Run order

1. Commit this file.
2. Build `TPL_BARS_PAIR.c`, `tools/check_bars_pair.py` + tests; generalise `tools/null1.py` costs / pair constants (tested);
   commit.
3. User: compile check, then one click per pair; Claude copies the logs (standing permission), runs the checker; VC0-VW1 PASS
   required; record.
4. Offsets per pair written and recorded; null runs (2 x 1,000); results sha256 recorded.
5. Read: real MAF on both pairs; report `analysis/c1screen/C1S2_report.md`; results appended below as "C1S2 read 1".

## Count

C1-only readings tested: MAF on 2 more pairs (the candidate count K of C1S1 is unchanged: no new candidate). Project-wide
full-strategy variants: 2.

## Amendments

## Record: build + compile check (2026-11-26)

- Build committed e347be0 (TPL_BARS_PAIR.c, check_bars_pair.py, c1s2.py + tests; 33 tests OK). The `null1.py` cost
  generalisation of run order step 2 was done as a new module `tools/c1s2.py` instead (null1.py unchanged).
- (b) VC0: Zorro printed `TPL_BARS_PAIR: compile check only (bp_CompileOnly = 1), nothing run` and `compile check done`,
  no Error line. Prediction met. `bp_CompileOnly` set to 0 for the bar runs.
- Disclosure: the same paste carried Zorro's summary window of the earlier TPL_R2_EURUSD run (R2c, spread x2). PERF2 was
  already read and closed (STOP), and no C1S2 number uses it; recorded so the rule (Error lines only) is visibly kept.

### Prediction for the bar runs (written before the clicks)

- Zorro output: no Error line except, at most, `Error 047` for a history year before the pair's data (AUD/USD files start
  2002, EUR/JPY 2010).
- VB0 / VB1 / VW1 PASS on both pairs; EUR/JPY's 2017-12-11..2018-01-01 hole gives no failed bar.

## Record: bar run AUD/USD (2026-11-26)

- Zorro output: no Error line (prediction met). Log copied to `Zorro/Data/BARS_AUDUSD_log_run1.csv`
  (sha256 c379c15c7a98deabf16e6004e38178b226e93a0e4978275ec8481c9c2d43d168).
- Checker: `analysis/c1screen/results/C1S2_VB_AUDUSD_run1.csv`. **RUN PASS.** VB0 (no asset fail, info, lookback 520),
  VB1 bars fit rule (same, own) with 0 off (other rules 465-683 off), all bars end 17:00 NY; first bar 2005-06-29
  (diff 3.3e-11, not replaced). VW1: MAMA, FAMA, period, alpha, phase, ATR, TR 0 rows off (max error 5.7e-14);
  MAF states 0 differ, 0 near-threshold.

## Record: bar run EUR/JPY (2026-11-26) — VB1 FAIL, step stopped

- Zorro output: one `Error 047: EUR/JPY no 2009 history` (prediction met: allowed). Log copied to
  `Zorro/Data/BARS_EURJPY_log_run1.csv` (sha256 b3ba494414d1f91883e1c8c9ce6babeacc7e115a45dda9d6bb2a775f38941197).
- Checker: `analysis/c1screen/results/C1S2_VB_EURJPY_run1.csv`. **RUN FAIL.** VB0 PASS (no asset fail, info, lookback
  520); bar times PASS; **VB1 FAIL**: rule (same, own) 3 bars off. Prediction "the hole gives no failed bar" **not met**.
- (b) Diagnosis (measured, no rule changed): Zorro has 4,346 bars, Python 4,343. The 3 extra Zorro bars are 2017-12-18,
  2017-12-24, 2017-12-30, inside the hole, 6 days apart, each o = h = 133.739, l = c = 133.737. That is exactly the OHLC of the
  last M1 record before the hole (2017-12-11 23:34 UTC). The M1 files hold no record from then to 2018-01-01 22:00 UTC.
- (b) With those 3 Zorro bars put into the Python bar series (diagnostic only, script outside the repo): the other 4,343 bars
  match (0 off), and VW1 MAMA, FAMA, period, alpha, phase, ATR, TR all 0 rows off (max error 4.1e-10, phase); MAF states 0
  differ.
- (c) Inference: Zorro fills a long quote gap with flat bars repeating the last quote. The 6-day spacing and the rule behind it
  are not established from one instance and are not claimed.
- Per this file, the step stays stopped until a dated amendment.

### Amendment 1 (2026-11-26, after EUR/JPY bar run 1, before any C1S2 null or real-signal result): Zorro's gap filler bars

- User decision A1 = A: the Python EUR/JPY bars take Zorro's 3 filler bars (2017-12-18, 12-24, 12-30) with the values Zorro
  logged, listed in `tools/check_bars_pair.PAIRS["EURJPY"]["fillers"]`; inserted by `r1_data.insert_fillers`, used by both
  `check_bars_pair.py` and `c1s2.load`. These dates only: no general gap rule. A filler bar holds no M1 records (i1 = i0 - 1);
  a market fill due on it is taken at the first record after it (2018-01-01 22:00 UTC). (c) That Zorro fills there too is
  an assumption, not checked; on the real MAF series it does not arise: C1 is +1 on every bar 2017-12-11..2018-01-03, so no
  signal falls in the hole (shifted null series can place one there).
- Unchanged: ranges, costs, null, pass rule, AUD/USD (no fillers). Rejected: B (bars without fillers: VW1 would not hold,
  the null would test a signal Zorro does not make), C (start after the hole: loses about 6 of 14 years, changes a
  pre-registered range).
- Guards and tests (`tools/tests/test_fillers.py`, 5 tests; all 167 tools tests OK): without fillers the synthetic hole case
  fails (the run-1 FAIL reproduced); a planted wrong filler value fails; a filler on a day with records is refused; a bar
  variant that has records on a filler date counts as not fitting.
- Gotcha 9d.26 added.

## Record: EUR/JPY bar check re-run under Amendment 1 (2026-11-26)

- Same log (`BARS_EURJPY_log_run1.csv`, sha256 b3ba4944...1197), no new Zorro run. Checker:
  `analysis/c1screen/results/C1S2_VB_EURJPY_run2.csv`. **RUN PASS.** VB0 PASS; VB1 rule (same, own) 0 off (other rules
  294-522 off), bar times PASS, first bar 2010-05-23 (diff 4.7e-11, not replaced); VW1 MAMA, FAMA, period, alpha, phase, ATR,
  TR 0 rows off (max error 4.1e-10); MAF states 0 differ, 0 near-threshold. Bars 4,346; trade bars 3,826.
- VC0-VW1 now PASS on both pairs: run order step 3 complete.

## Record: offsets written (2026-11-26, before any null run)

`numpy.random.default_rng(20261125)`, 1,000 drawn without replacement from 260 .. L - 260, sorted; files created with
exclusive create (no overwrite). Checked: 1,000 unique each, sorted, inside the bounds.

| Pair | L (trade bars) | min | max | file | sha256 |
|---|---|---|---|---|---|
| AUD/USD | 5,370 | 267 | 5,109 | `analysis/c1screen/C1S2_offsets_AUDUSD.csv` | 69ffaa73280e71d3849468ee4ba521f1d75bd09b93df92d14d18bf0ed64e745c |
| EUR/JPY | 3,826 | 264 | 3,565 | `analysis/c1screen/C1S2_offsets_EURJPY.csv` | 2a357ac8eb2c4b5c194f14aeb918b548e94ed4c1acb1531135f6dbeed8cc1bb3 |

## Record: null runs (2026-11-26, before the real reading)

- `tools/c1s2.py null` per pair, C1-only, spread x2 + rollover, fast M1 resolver; one chunk per pair (each finished within
  the 150 s budget). File `analysis/c1screen/results/C1S2_null_runs.csv`: 2,000 rows (1,000 per pair), the offsets equal
  the recorded offsets files exactly, no NaN means; signals per run: AUD/USD min 230, EUR/JPY min 166.
- sha256 c9160b2edb47ee3bb3614d8c7994a585d56492e704108eec70c1b51a66594a12.
- The real MAF reading on these pairs has not been computed yet (it is computed only by `c1s2.py read`, after this commit).
