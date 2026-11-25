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
