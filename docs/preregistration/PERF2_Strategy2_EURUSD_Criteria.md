# PERF2 — Performance read: Strategy 2 variant 0, EUR/USD D1 — Criteria

**Status:** pre-registered 2026-11-24, before any Strategy 2 code is run and before any Strategy 2 number exists.
Amendments are dated and appended below, never edited in place (PROJECT_STATE §2.2).
**Decided:** planning chat 2026-11-24, one point at a time (user: T3 amendment 1 option B; 2a option B; 2b option A).
**Format:** copies `PERF1_Strategy1_EURUSD_Criteria.md` (P-1..P-4 and its Amendments 1-3). Where this file says
"as PERF1", the PERF1 text applies word for word with Strategy 1 replaced by Strategy 2.
Labels as `docs/sources/NNFX_Sources.md`: (a) source states, (b) measurable, (c) inference.

**What is read:** Strategy 2 variant 0 (new `strategies/template/NNFX_Strategy2.h`), EUR/USD D1 (17:00 New York bars),
the same history, range and template settings as PERF1 (T1-T11, M-D1..M-D8, R-D3..R-D7 defaults), TICKS on M1 history,
TR_FRC on, 100,000 EUR, 2% per signal (two 1% halves).

| Slot | Indicator | Parameters | Input | Reading (state +1 / -1 / 0) | Source |
|---|---|---|---|---|---|
| Baseline | FRAMA | N = 32 | Price (H+L)/2, High, Low | sign(close - FRAMA) (T3.1) | (a) TASC V.23:10 (source default N = 16; N = 32 = slot choice, PROJECT_STATE §1.2) |
| C1 | MESA Stochastic vs SMA(10) of its own output | Length 20 (HP 48, SS 10 fixed in the source) | Close | two-lines cross: +1 MESA > SMA, -1 MESA < SMA, 0 equal | (a) TASC V.32:1; SMA 10 (a) V18; reading (c), T3 amendment 1 |
| C2 | Laguerre RSI | gamma 0.5 | Close | +1 above 0.5, -1 below, 0 equal | (a) *Cybernetic Analysis* p. 221; 0.5 reading (c), T3.2 |
| Volume | none | ALWAYS_YES | — | — | T2 |
| ATR | ATR MT4 | 14 | H, L, C | — | (a) NNFX [V03, V16] |
| Exit | none | opposite C1 | — | — | T1 [V12] |

- **Bridge-too-far on** (two-lines-cross C1, V34; T3 amendment 1.2), age >= 7 (T10.2).
- **SMA (decision 2a, user: B):** computed in `NNFX_Strategy2.h` as the plain mean of the last 10 MESA outputs, from an
  explicit-length series (gotchas 9d.10); C1 state 0 until 10 MESA outputs exist (c). Zorro's `SMA()` (TA-Lib; manual
  `ta.htm`: "the mean of the Data series", start-up not stated) is used only as a cross-check (X1).
- **Range:** StartDate 2007-04-01 (first trade bar 2007-04-02) .. 2026-05-29, LookBack 520, exactly as the R1 runs read
  by PERF1 (R1 Amendment 1). (b) Note: PERF1's header says "2007-02-01"; the runs it read used 2007-04-01 (`TPL_R1_EURUSD.c`
  line 46). Same bars as PERF1 keep the two reads comparable.
- **Start-up (b), limitation:** FRAMA's start-up memory decays with alpha >= exp(-4.6) = 0.0100518; worst case
  (1 - 0.0100518)^520 = 5.2e-3 of the initial difference remains at the first trade bar. No longer history exists before
  2005, so a longer LookBack would only move the trade start later. MESA (HP 48) and Laguerre RSI (gamma 0.5: ~60 bars)
  decay well inside 520 bars (LRSI: outputs differ from a price-seeded start only in the first ~60 bars, PROJECT_STATE §1.1).
- **Template:** unchanged. If any template file must change, S4, P5 and P6 regressions re-run before R2a, each equal to
  its last PASS.

---

## P-1 What is reported — as PERF1

R units (half-R, signal-R on actual risk), report items 1-13 (all / standard / continuation, at spread x1 and x2 side by
side), information-only items, limitations and the measuring tool `tools/perf_report.py`: **as PERF1 P-1**, with the
conventions of PERF1 Amendment 1.2 (year of the last half's close; drawdown from 0, same-day halves in log order;
near-miss life rule; earliest year removed on a tie) and the refusals of PERF1 A1.3.

Item 11 now includes bridge-too-far refusals for Strategy 2 (bridge-too-far is on). (b) Strategy 1's 35 bridge-too-far
refusals are not a prediction for Strategy 2.

---

## P-2 Data and mechanics gate (decision 2b, user: A)

New script `strategies/tests/TPL_R2_EURUSD.c` (copy of `TPL_R1_EURUSD.c` pointed at `NNFX_Strategy2.h`), own switch
`r2_SpreadLevel` (0 = costs off). `TPL_R1_EURUSD.c` keeps its settings: it stays at `r1_SpreadLevel = 2` as the record of R1c,
and is reset to 0 before any reuse (lesson 3, P-5; only a header comment is added).

| Run | Costs | Checks (all must PASS) | Read by perf_report.py |
|---|---|---|---|
| **R2a** | off | C0, K0, B1, W1, X1, S1, T1 (M1 replay), K1, K3, K4, K5, K6 | no (mechanics only, R-D1) |
| **R2b** | x1 | C0, K0, B1, W1, X1, S1, K1, K3b, K4, K5, K6 | **yes, x1** |
| **R2c** | x2 (`r2_SpreadLevel = 2`, one-line edit committed before the click) | as R2b, every half pays exactly one doubled spread | **yes, x2** |

Check definitions are those of `TPL_R1_Criteria.md` (C0, K0, B1, W1, S1, T1, K1, K3, K3b, K4, K5, K6, same tolerances),
re-pointed to Strategy 2:
- **C0** as R1 Amendment 2.1: `Error 047: EUR/USD no 2004 history` is accepted only with B1 passing on every bar; any
  other `Error` line fails the run.
- **K0** INFO row adds FramaN 32, MesaLen 20, C1SmaLen 10, LrsiGamma 0.5, AtrLen 14, BtfOn 1, SpreadMult, Tp1Atr,
  RefusedLog (replaces FastLimit / SlowLimit / FisherLen / ReflexLen).
- **W1** every IND field (FRAMA, dimension, alpha; MESA out, Roof, raw Stoc, SMA; LRSI l0, l3, den, out; ATR, TR) within
  1e-10 + 1e-9 x |model| of the reference models (`analysis/harness/reference.py`; SMA model new, tested on a known answer
  first) run on the matched bars from Zorro's first bar. **No exclusions pre-registered**: the start-ups and zero-range
  holds of all three are defined by their verified files. Any exclusion found necessary is an amendment before the read.
- **X1 (new, decision 2a)** on every bar where 10 MESA outputs exist: |own SMA - Zorro `SMA()`| <= 1e-9 x |own SMA| + 1e-15.
  Report the max; bars where `SMA()` differs only during its own start-up are counted and reported, not failed (its
  start-up is not stated in the manual).
- **S1** baseline, C1 (MESA vs SMA), C2, ATR states equal the model's; bars within 1e-9 of a threshold counted, not failed.
- **T1** Zorro's halves equal the engine + M1 layer (R-D6), bridge-too-far refusals included (REFUSED rows equal the
  engine's refusals).
- Each extended check is first seen to fail on a planted defect (`tools/tests`), incl. a planted SMA length 9 and a
  planted C1 reading at 0.5 midline (S1 must flip).

Log sha256 of R2b and R2c recorded before `perf_report.py` reads them; it recomputes and refuses on a mismatch.
Disclosure rule: nothing from the R1 / step-5 Strategy 1 runs says anything about Strategy 2; no Strategy 2 trade
outcome is hand-checked before the read (decision 2b).

---

## P-3 Verdict: continue or stop — as PERF1 (unchanged)

All conditions at **spread x2** (T7.2); x1 reported, not decisive.

| Verdict | Condition |
|---|---|
| **CONTINUE — evidence** | t >= 2 on mean signal-R **and** total R > 0 with the best year removed |
| **CONTINUE — no evidence yet** | mean signal-R > 0 **and** total R > 0 with the best year removed, t < 2. Goes to Phase 2 labelled "no evidence of an edge yet"; the Phase 2 surrogate test decides |
| **STOP** | mean signal-R <= 0, **or** total R <= 0 with the best year removed. Recorded as a failure (§2.9); Strategy 2 is not tuned on this data to rescue it |

Definitions, notes (t >= 2 a convention (c); independence approximate (c); size estimate; not gated: win rate, drawdown,
exit mix, longs / shorts) and the verdict-code guard: **as PERF1 P-3**. (c) The PERF1 size estimate (about 325 signals,
standard error ~0.055 R) does not carry over: the signal count of Strategy 2 is not predicted.

**Variant count.** Strategy 2 variant 0 on EUR/USD = 1 variant. T3 amendment 1 and decision 2a redefine variant 0 before
any run and add none. Spread x1 / x2 are T7 reporting levels, not variants. **Project-wide strategy variants tested:
1 before this read, 2 after it.** The verdict line reports both numbers.

---

## P-4 One data feed — as PERF1

Same feed (Zorro EUR/USD M1, 2005-2026), same label ("Strategy 2 v0 on this EUR/USD feed"), history sha256 list, near-miss
table at 0.5 / 1 / 2 pips (information only), second feed as a Phase 2 item only for a system that passes.

---

## P-5 Lessons from PERF1 (written into this run)

1. **Zorro window:** after every click only `Error` lines and the trade count are pasted, as text. Nothing from Zorro's
   summary window is shown or recorded (PERF1 A3.1 / A3.2). Screenshots of the Zorro window are not used.
2. **Log fields checked before any run:** `perf_report.py` is run on a synthetic Strategy 2 log (built from the template's
   row formats, with the INFO / REFUSED / SIZE / HALF / ACCT fields this report needs) and must exit 0 before R2a. A
   missing field stops the sequence before a click, not after (PERF1 Amendment 1).
3. **Scripts:** R2 uses its own script; `TPL_R1_EURUSD.c` stays at `r1_SpreadLevel = 2` and gets a header comment
   "reset to 0 before reuse" (comment only, committed separately).

---

## Run order

1. Commit this file and T3 amendment 1 (before any Strategy 2 code runs).
2. `NNFX_Strategy2.h` + config (lint clean, T11); SMA model + test; `TPL_R2_EURUSD.c`; checker extended to Strategy 2 with
   planted-defect tests; synthetic-log run of `perf_report.py` (P-5.2); commit.
3. R2a prediction written and committed (c); user clicks R2a; checker PASS required.
4. R2b prediction committed; click; checker PASS; sha256 recorded.
5. Switch edit `r2_SpreadLevel = 2` + R2c prediction committed; click; checker PASS; sha256 recorded.
6. Read: `perf_report.py` on R2b (x1) and R2c (x2); results and verdict appended below as "PERF2 read 1".
A FAIL anywhere stops the sequence; nothing is read until R2a, R2b and R2c all PASS.

## Amendments

### Amendment 1 — 2026-11-24, before any Strategy 2 run (build stage; no rule of P-1, P-3, P-4 changed)

Reason (b): writing the code showed three details the criteria left implicit.

**A1.1 W1 `sma` from row 10.** The SMA of the MESA output has no value until 10 MESA outputs exist (decision 2a). W1
compares `sma` from the 10th IND row on; rows 1-9 hold whatever Zorro's series held and are not used (C1 state 0 there,
checked by S1 against the model, which reads 0 on those rows). This is the definition of the field, not an exclusion of a
defined value; every other IND field is compared on every row. New W1 item `nmesa` (= row number, exact) proves the counter
that gates C1. X1 compares the same rows; rows 1-9 are reported as INFO.

**A1.2 Engine refusals.** T1's "REFUSED rows equal the engine's refusals" needs the engine to record its bridge-too-far
skips. `analysis/template/reference_engine.py` now appends (bar, dir, reason) to `Result.refusals` at the existing skip
(behaviour unchanged: 32 earlier engine tests PASS; new test D7 refusal recorded, seen to fail with the append removed).
T1 compares the days of the template's `REFUSED,...,bridge-too-far` rows with the engine's refusal days.

**A1.3 Report header.** `tools/perf_report.py --read perf2` writes PERF2's title, criteria path, variant count (1 for
Strategy 2; project-wide 2 after the read) and disclosure (no Strategy 2 trade hand-checked). Everything else in the
report is the PERF1 code unchanged (default `--read perf1` output unchanged: 51 earlier tests PASS). P-5.2's synthetic
Strategy 2 log run is test `test_perf2_synthetic_strategy2_log` (exit 0, all 13 items present, no PERF1 lines).

### Amendment 2 — 2026-11-25, R2a prediction (before the click)

**Compile check (b):** `TPL_R2_EURUSD.c` with `r2_CompileOnly = 1` (commit `8ddf09d`): "compile check done", no `Error`
line, as predicted. Now `r2_CompileOnly = 0`, `r2_SpreadLevel = 0` (R2a).

**Dry run behind the prediction (b), mechanics only.** The reference models and the engine + M1 layer were run in Python on
the same bars as R1 (bar rule (same, own), 5,490 bars from 2005-03-29, first trade bar index 520, first bar not patched;
bars cut by R1d run 1's RBAR rows). Printed: conditioning, near-threshold counts, half / refusal counts. No P&L, R, exit
reason or year figure was computed or printed.
- Conditioning: a relative price nudge of 1e-13 moves every field by <= 1.6e-13 absolute (relative <= 7.2e-10, Roof,
  where values pass near 0; the W1 tolerance is 1e-10 + 1e-9 |m|), and flips no C1 or C2 state.
- Near-threshold bars in the trade range: C1 0, C2 0, baseline 0. Laguerre RSI exactly 0 or 1 on 39.4% of trade-range bars
  ((b), the pinning of T3 amendment 1). MESA raw Stoc fallback (range 0): 1 row (the first).
- Engine + M1 layer, all four (fill_px, start) alternatives identical: **564 halves (282 signals)**, by entry kind (halves):
  baseline 326, c1 184, continuation 40, pullback 14; **158 bridge-too-far refusals**; 0 same-bar stop + TP1; 0 `end` halves.
- **Disclosure (b):** these counts (entry-kind mix, refusal count) are now seen before the read. (c) They carry no outcome
  information; the verdict rule (P-3) is unchanged.

**R2a prediction (c).**
- Zorro: `Error 047: EUR/USD no 2004 history` (as every R1 run; accepted under C0), no other `Error` line, `Trades 564`.
- `python tools/check_r2.py a C:/Zorro/Data/TPL_R2a_log_run1.csv C:/Zorro/Data/TPL_R2a_ind_run1.csv C:/Zorro/History
  analysis/template/r2/results/TPL_R2a_run1.csv`: **RUN PASS**. K0 settings ok, 0 ERROR rows; B1 rule (same, own), first bar
  20050329 not replaced; W1 every field within tolerance, max errors of the R1 order (<= 1e-11; `nmesa` exact); X1 0 off
  from row 10 (Zorro `SMA()` = the plain mean; its start-up rows 1-9 reported, count not predicted); S1 0 differ, 0
  near-threshold; T1 fits all four alternatives, 158 bridge-too-far refusals equal; K1 282 SIZE rows exact; K3, K4, K5 0 off;
  K6 no MARGINCALL.
- Copy after the click: `Data/NNFX_Template_log.csv` -> `Data/TPL_R2a_log_run1.csv`, `Data/NNFX_Strategy2_ind.csv` ->
  `Data/TPL_R2a_ind_run1.csv`.

### R2a run 1 — 2026-11-25 10:01 — FAIL (setup: indicator log row; checker model: holiday fills)

Commit `90e210c`. Log `C:/Zorro/Data/TPL_R2a_log_run1.csv` (sha256 `a462d4bc77f74cbe28da7b795a676d225c716aa015e33a2ec91752299cedbfc9`), indicators `TPL_R2a_ind_run1.csv`
(`7d082a5f15643717b741f5e51c755e30454212d9a7126fdde433440d3ca58d54`). Zorro: `Error 047: EUR/USD no 2004 history` only, `Trades 564` (= the prediction).
`check_r2.py a` stopped reading the IND file (no results file written): **FAIL**. Diagnosis (b), from the log and the IND
fields that precede the defect:
1. **IND row broken** (template unaffected): `(int)s2_cnt[0]` printed with `%i` shifted every later column (25 fields for
   24 headers; LRSI, ATR fields unreadable). Fields before it equal the models: FRAMA, dim, alpha <= 8.9e-16; MESA 9.2e-14;
   Roof 2.7e-15; Stoc 2.0e-13; own SMA and Zorro `SMA()` both <= 7.2e-14 of the model (0 rows off). Gotchas 9d.24.
2. **T1: 4 of 564 halves differ** (fit (open, entry) and (open, after) otherwise): two market fills on bars holding folded
   12-25 records, 2012-12-26 (baseline exit, both halves) and 2013-12-26 (entry, both halves). Zorro filled at the first
   record of 12-26 00:00 New York (1.31787 / 1.36766), the engine at the bar's first record (late 12-25: 1.31770 /
   1.36759). (a) date.htm: holidays "treated like weekends". Gotchas 9d.25.
Also (b): K0 settings equal, 0 ERROR rows; B1 rule (same, own), 5,490 bars; S1 0 differ, 0 near-threshold; 158 REFUSED
rows, all bridge-too-far, equal to the engine's 158 refusal days.

### Amendment 3 — 2026-11-25, after R2a run 1, before run 2

**A3.1 Disclosure (b).** The user's text paste of the Zorro window after R2a run 1 included Zorro's summary lines (account
figures of the costs-off run: Loss, MI, DD, Capital, Win, Avg, CAGR, PF, SR, UI, R2). Seen by the user and the planning chat
before any read, against P-5.1. They are a costs-off (x0) run, Zorro's account accounting, not the PERF2 report; not
recorded here, not used in any verdict. The verdict rule (P-3, x2) is unchanged. P-5.1 stands for R2a run 2, R2b and R2c:
only `Error` lines and `Trades` are pasted.

**A3.2 Fixes (no rule changed).**
- `NNFX_Strategy2.h`: `nmesa` printed as a var with `%.15f` (no cast); `check_r2.py` rounds it. Slot logic unchanged.
- `tools/r1_replay.open_fill`: market fills skip records whose New York date is a holiday (default 101, 1225); tested on a
  synthetic 12-25 / 12-26 case (and the old rule with `holidays=()`). Regression: `check_r1.py a` on R1a run 2 (log
  `TPL_R1a_log_run2.csv`) still RUN PASS, 650 halves (R1 had no fill on such a bar). On R2a run 1's log the new rule makes
  T1 fit (open, entry) and (open, after) with 0 differences, refusals equal.
- Gotchas 9d.24, 9d.25 added.

**A3.3 R2a run 2 prediction (c).** Same script and switch (`r2_SpreadLevel = 0`), template unchanged, so the same trades.
- Zorro: `Error 047` only, `Trades 564`.
- `check_r2.py a` on `TPL_R2a_log_run2.csv` / `TPL_R2a_ind_run2.csv`: **RUN PASS**. W1 every field within tolerance (max
  <= 1e-12 order), `nmesa` exact; X1 0 off from row 10; S1 0 differ, 0 near-threshold; T1 fits (open, entry) and
  (open, after), 158 refusals equal; K1 282 SIZE rows; K3, K4, K5 0 off; K6 no MARGINCALL.
- The template log of run 2 is byte-identical to run 1's (same script, same template; only the IND file changes) (c).

### R2a run 2 — 2026-11-25 10:15 — checks PASS; one unpredicted log defect (stray IND column)

Commit `294576e`. Log `TPL_R2a_log_run2.csv` byte-identical to run 1's (sha256
`a462d4bc77f74cbe28da7b795a676d225c716aa015e33a2ec91752299cedbfc9`, as predicted); indicators `TPL_R2a_ind_run2.csv`
(`d266f512007a2b43fa205523b5da9fdd7c0b7143731e2d9ea382ecb6339b676f`). Zorro: `Error 047` only, `Trades 564` (as predicted). `check_r2.py a`
(`analysis/template/r2/results/TPL_R2a_run2.csv`): **RUN PASS, 32 rows, 0 FAIL**. W1 every field <= 2.0e-13 (13 fields, 5,490
rows; `sma` 5,481 rows from row 10), `nmesa` exact; X1 0 of 5,481 off (max 0: Zorro `SMA()` = own mean exactly), its 9 start-up
rows also equal; S1 0 differ, 0 near-threshold; T1 fits (open, entry) and (open, after), 0 diffs, 158 refusals equal, 0
same-bar; K1 0 of 282 off; K3, K4, K5 0 off; K6 no MARGINCALL, max margin share 0.0373.
**Not predicted (b):** every IND data row has 25 fields for 24 headers; the last is garbage. Cause: the format string had
20 `%.15f` for 19 float arguments (also the real cause of run 1's shifted columns; gotchas 9d.24 corrected). The checker read
fields by header name, so every named field was verified, but it did not notice the extra field: a guard gap.

### Amendment 4 — 2026-11-25, after R2a run 2

**A4.1 Fixes.** `NNFX_Strategy2.h` IND format: 19 `%.15f` for 19 floats (log-only; slot logic unchanged). `check_r2.read_ind`
now refuses a file whose data rows do not all have the header's field count (RUN FAIL "K0 ind_columns"); seen to fire on a
planted stray field (test) and on R2a run 2's real file (5,490 rows refused).
**A4.2 Gate.** Decided in the planning chat (see below): whether R2a run 2 counts as the R2a PASS or an R2a run 3 is
required with the fixed row.

**A4.2 decided (user: B, 2026-11-25).** R2a run 2 does not count as the gate; **R2a run 3** runs with the fixed IND row
(commit `f00d612` + this amendment). Run 3 is the R2a gate run.

**A4.3 R2a run 3 prediction (c).** Same script `TPL_R2_EURUSD.c`, `r2_SpreadLevel = 0`.
- Zorro: `Error 047` only, `Trades 564`.
- Template log byte-identical to runs 1-2 (sha256 `a462d4bc77f74cbe`...).
- Every IND data row has 24 fields (the new column-count guard passes); IND named-field values equal run 2's.
- `check_r2.py a` on `TPL_R2a_log_run3.csv` / `TPL_R2a_ind_run3.csv`: RUN PASS, 32 rows, 0 FAIL, same figures as run 2.
