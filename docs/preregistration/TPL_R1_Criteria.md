# R1 — First EUR/USD real-data run: pre-registered criteria

**Written 2026-11-23, before any R1 run** (Phase 1 step 4; decisions R-D1..R-D7, R-D4 amended, in
`docs/template/NNFX_TEMPLATE_DECISIONS.md`). Commit before the first [Test] click. Changes after the commit are dated
amendments appended below, never in place. Labels: (a) source states, (b) measured, (c) inference.

**Mechanics only (R-D1).** The checker computes no P&L, win rate or R summary; the Zorro window's summary line is not
recorded or used. Trade counts and exit reasons are mechanics and may be read.

## What is run

- Script `strategies/tests/TPL_R1_EURUSD.c`: Strategy 1 variant 0 through `NNFX_Strategy1.h` (FAMA (0.5, 0.05) on
  (H+L)/2, Fisher 10 on (H+L)/2, Reflex 20 on Close, ATR 14 MT4), EUR/USD M1 history, 17:00 New York D1 bars, trades
  2007-02-01 .. 2026-05-29, LookBack 520 (decisions only after it), TICKS, Fill 3, Hedge 2, TR_FRC, sizing M-D8.
- **R1a**: `r1_Costs = 0` (spread, commission, rollover 0). **R1b**: `r1_Costs = 1` (asset-list costs x1:
  spread 0.00012, RollLong -0.8947, RollShort 0.4259, commission 0; `config/assets/AssetsNNFX_FX.csv`).
- After each click copy `Data/NNFX_Template_log.csv` and `Data/NNFX_Strategy1_ind.csv` to
  `Data/TPL_R1<a|b>_log_run<n>.csv` / `TPL_R1<a|b>_ind_run<n>.csv`.
- Checker: `python tools/check_r1.py <a|b> <log> <ind> C:/Zorro/History analysis/template/r1/results/TPL_R1<a|b>_run<n>.csv`
  (tests `tools/tests/test_check_r1.py` 12 + `test_r1_replay.py` 8: each check fails on a planted defect; resolver
  mutation check: 3/3 planted bugs caught). Engine extension (`open_fill`, `intrabar`): 32/32 engine tests, S4 expected
  trades regenerate byte-identical.

## Data facts measured before the run (b)

- 7,851,520 records 2005-01-03 .. 2026-05-29; 35,304 repeated records (the last 1-2 minutes of every 300-record download
  chunk) removed, each identical to the kept record with the same time (`tools/r1_data.load_m1`).
- Every weekday has one record stamped exactly 17:00:00 New York (453 of them on Fridays); no record inside the weekend
  gap (Friday 20:00 .. Sunday 17:00).
- Indicator conditioning on these bars: a relative price nudge of 1e-13 moves FAMA <= 1.1e-11 (relative), Fisher
  <= 4.8e-10, Reflex <= 3.7e-11, ATR <= 9.9e-12, no state flip. Exception: Reflex on the first bar (normaliser 0).

## Criteria

| # | Criterion | Pass condition |
|---|---|---|
| C0 | Zorro window | No line starting with `Error` (Warning 047 is not expected: 539 bars precede the start) |
| K0 | Setup / errors | INFO: costs 0 / 1, assetType 1, FixedLots 0, Capital 100000, LookBack 520, TradeModeFRC 1, Fill 3, Hedge 2, TICKS 1, BarOffset 1020, StartWeek 71700, Fisher 10, Reflex 20, ATR 14, LotAmount 1000; no ERROR or ASSETFAIL row |
| B1 | Bars | Zorro's RBAR rows equal ONE Python bar variant on every day of Zorro's range (first bar exempt: it may be partial, gotchas 9d.14); every bar ends 17:00 New York (within 1 s) |
| W1 | Wiring | Every IND field (MAMA, FAMA, period, alpha, phase, Fish, trigger, raw, Value1, range, Reflex, sum, MS, ATR, TR) within 1e-10 + 1e-9 x |model| of the reference models run on the matched bars from Zorro's first bar; Reflex rows with model MS = 0 excluded and counted; IND prices = bars |
| S1 | States | The template's BAR-row C1, C2, baseline and ATR equal the model's; bars within 1e-9 of a threshold counted, not failed |
| T1 | Replay (R1a only) | Zorro's halves equal the engine + M1 layer under ONE (fill_px, start) alternative: count, dir, half, kind, entry day, entry price (1e-5), exit reason, exit day, exit price (1e-5); halves the engine closes as `end` compared on entry only |
| K1 | Sizing | Every SIZE row recomputes from its own inputs within 1e-8 (M-D8); its ATR equals the IND ATR of that bar |
| K3 | Equity (R1a) | SIZE and ACCT Equity = 100000 + closed profits + open value at the close (0.01 + 1e-7 relative); ACCT Balance = 100000 + closed profits |
| K3b | Balance (R1b) | ACCT Balance = 100000 + closed profits |
| K4 | Profit | R1a: profit = dir x (exit - entry) x units, rollover and commission 0. R1b: profit = dir x (exit - entry) x units - spread x units - commission + rollover, and rollover = whole days x rate (P5 rule). Tolerance 2e-3 + 1e-6 relative (float32 TradeProfit) |
| K5 | Lots | Each half's lots (units / (PIPCost / PIP)) equal its signal's SIZE lots |
| K6 | Margin | No MARGINCALL on any ACCT row; max MarginTotal / Equity reported |

**Run verdict:** PASS only if C0 and every check above hold. Anything else is FAIL, investigated and recorded; no strategy
result is read from R1 in any case (R-D1).

## Alternatives the run decides (fixed before the run)

| Question | Alternatives | Python dry run on these bars (b) |
|---|---|---|
| Bar building | (next, own): a 17:00:00 record opens the next bar, Friday ones form a Saturday bar / (next, drop): Friday 17:00:00 records dropped / (next, monday): folded into the Monday bar / (same, own): a 17:00:00 record closes its bar | 5,987 / 5,535 / 5,538 / 5,535 bars from Zorro's first bar; 700 / 646 / 646 / 652 halves |
| Market fill at a bar start | first M1 record's open / its close | >= 607 halves differ between the two: distinguishable |
| Entry minute checked for exits | yes / no | 0 halves differ on this data: **not distinguishable**; reported as "both fit" |

**Prediction (c):** bars (same, own) (the 17:00:00 record is the 16:59 minute's close and closes its bar; (a) barperiod.htm
says the opposite, so this is a low-confidence inference); market fills at the first record's open; RUN PASS on all
checks; no MARGINCALL; zero ERROR rows. The first bar is predicted 2005-01-28 (520 bars before 2007-02-01 in that variant),
not a criterion.

## Variants counted

- 1 configuration (Strategy 1 variant 0), 2 cost modes (R1a, R1b); this is R1a run 1 and R1b run 1.
- Regressions in the same sitting: TPL_Equivalence run 5, TPL_Costs run 5, TPL_Sizing run 2 (amendments in their files).

---

## R1a run 1 — 2026-11-23 18:54 — FAIL (setup and data causes; the template's trades matched)

Commit `c0e7f47`. Log `C:/Zorro/Data/TPL_R1a_log_run1.csv` (sha256 `926bc6354b41841f…`), indicators
`TPL_R1a_ind_run1.csv` (`f72a711374075084…`); checker output `analysis/template/r1/results/TPL_R1a_run1.csv`.
Zorro: `Error 047: EUR/USD no 2004 history (History\EURUSD_2004.t6)`, `Test: TPL_R1_EURUSD EUR/USD (TICKS) 2007..2026`,
`Trades 654`. The window's performance figures are not recorded (R-D1).

- **C0 FAIL (b):** Error 047. Zorro's first real bar was 2005-01-28, exactly 520 bars before 2007-02-01, so the LookBack
  count was right; (c) Zorro also tried to open the 2004 file, apparently by calendar reach.
- **B1 FAIL (b):** no pre-registered variant matched every bar. Causes found:
  1. A record stamped exactly 17:00:00 **closes** its bar (variant (same, own), as predicted; barperiod.htm's wording says
     the opposite).
  2. (a) date.htm: `Holidays` default `{101, 1225}`, "treated like weekends": Zorro makes no bar on 1 January / 25 December;
     their records go into the next bar (2018-01-01, 2023-12-25, 2024-01-01).
  3. Good Friday 2007, 15:57: the record's close 1.33759 lies above its high 1.33749; Zorro's bar close is 1.33749. 3 of
     7.8 million records have a close outside their range.
  4. The first RBAR row (2005-01-03, not at 17:00) is the INITRUN call (the script ran its bar part in INITRUN).
- **W1 FAIL (b):** differences only in warm-up rows (last differing row 353; Reflex 521 at 1.7e-9). Cause: Zorro discards
  the series state of the INITRUN call; the indicators' first real call is the first bar. Diagnostic: models started at row 1
  agree on every field and row (max 7.9e-13, MAMA phase; every other field <= 2.1e-14).
- **Diagnostic re-check** with the corrected bar builder (`TPL_R1a_run1_diag.csv`, not a verdict): B1 bars PASS; S1 0
  differences; **T1 PASS: all 654 halves equal the engine + M1 layer** under (open, entry) and (open, after) (market fills at
  the first record's open, as predicted; the entry-minute question not distinguishable, as predicted); K1 327 SIZE rows, K3,
  K4, K5 0 differences; K6 no MARGINCALL, max margin share 0.040.

## Amendment 1 — 2026-11-23 (after R1a run 1, before run 2; user: approved)

Changes (setup and data model only; criteria, tolerances and checks unchanged):
1. **Start 2007-04-01** (first trade bar 2007-04-02; first Zorro bar predicted 2005-03-29, 520 bars earlier). (c) Keeps
   Zorro's calendar reach (~LookBack x 1.5 days = 780 days) inside 2005.
2. **Bar rule fixed to (same, own)** with holiday folding (Holidays {101, 1225}) and close clipping into each record's
   range (`tools/r1_data.py`: `BAR_RULE`, `_fold_holidays`, `load_m1`). B1 passes only for this rule; the other variants
   are still computed and reported.
3. **No slot call in INITRUN:** the script returns at the end of its INITRUN block, so the first IND / RBAR row is the first
   real bar and the models start there.
4. Checker: Python days between Zorro's first and second bar are left out of the bar comparison (partial first bar,
   gotchas 9d.14). Tests: 21 (holiday folding, fixed-rule rejection of another variant added).

Prediction for R1a run 2 (c): C0 met (no Error line); B1 PASS (first bar 2005-03-29 may be partial: exempt); W1 PASS on every
row (Reflex MS = 0 rows excluded); S1 0 differences; T1 PASS under (open, entry) and (open, after) and no (close, ·)
alternative; K1, K3, K4, K5 0 differences; no MARGINCALL. Runs so far: R1a 1 (FAIL). Variants unchanged.

## Amendment 2 — 2026-11-23 (after R1a run 2; user: approved)

Made after seeing run 2, so both changes are listed here next to the result they affect:
1. **C0 exception for one message.** `Error 047: <asset> no <year> history` for a year before the first history file is
   accepted **only if B1 passes** (every bar from Zorro's first bar on equals the Python bars, so nothing is missing). Any
   other Error line still fails C0. Evidence (b): in R1a runs 1 and 2 Zorro's first bar lay exactly 520 bars before the
   start and every bar matched; gotchas 9d.7 had filed the same message as harmless (as a Warning). The Amendment 1
   inference that a later start avoids it was **wrong**: it reappeared with 2007-04-01 (gotchas 9d.22 updated).
2. **Checker defect fixed (tool, not Zorro):** `check_r1.py` replaced Python's first bar with the RBAR values printed with 10
   decimals even when the first bar was not partial; the ~5e-11 rounding was amplified by Reflex's start-up (normaliser
   1.6e-9 on row 3) into 8.4e-9, one W1 row. Now the first bar is replaced only if it differs by more than the bar
   tolerance (1e-9). Criteria and tolerances unchanged.

## R1a run 2 — 2026-11-23 19:02 — PASS under Amendment 2

Commit `3aac0ce` (Amendment 1). Log `C:/Zorro/Data/TPL_R1a_log_run2.csv` (sha256 `051c1286dfb3ae8b…`), indicators
`TPL_R1a_ind_run2.csv` (`49309c429c06baf5…`). Checker as committed: 1 FAIL row (W1 Reflex, row 3, 8.4e-9; Amendment 2.2);
corrected checker: `analysis/template/r1/results/TPL_R1a_run2_fixedchecker.csv`, 0 FAIL of 30. Zorro: `Error 047: EUR/USD no
2004 history`, `Trades 650`; performance figures not recorded (R-D1).

| # | Result (b) |
|---|---|
| C0 | Only `Error 047 ... no 2004 history` (accepted under Amendment 2.1: B1 passes) |
| K0 | INFO settings as required; 0 ERROR / ASSETFAIL rows |
| B1 | All bars equal the Python bars, rule (same, own) + holidays; first bar 2005-03-29 (as predicted), equal to the full bar within 4.9e-11 (not partial); other variants 452 / 4,827 / 5 mismatches |
| W1 | Every IND field on every row within tolerance; max error 5.6e-16 from row 3 on; Reflex row with MS = 0 excluded (1) |
| S1 | 0 differences, 0 near-threshold bars |
| T1 | **650 of 650 halves equal the engine + M1 layer** under (open, entry) and (open, after); (close, ·): 613 differences. Market fills at the first record's open (as predicted); entry-minute question not distinguishable (as predicted). Same-bar stop/TP1 bars: 2 |
| K1 | 325 SIZE rows recompute exactly; ATR = IND ATR |
| K3, K4, K5 | 0 differences (Equity, Balance, profit identity, half lots) |
| K6 | No MARGINCALL; max MarginTotal / Equity 0.040 |

**Verdict: R1a PASS (run 2, under Amendments 1-2).** On 19 years of real EUR/USD bars the template's trades equal the
independent engine's, its indicator inputs equal the verified models, and sizing / Equity / profit are exact.
Runs: R1a 2 (run 1 FAIL). Variants: 1 configuration.

Prediction for R1b run 1 (c), `r1_Costs = 1`: C0 as amended; K0 (costs 1, Spread 0.00012, RollLong -0.8947, RollShort
0.4259); B1, W1, S1 PASS as in R1a run 2 (identical bars and indicators); K1, K3b, K4 (cost identity and whole-day rollover),
K5 0 differences; no MARGINCALL. The trades differ from R1a (spread moves triggers, M-D7) and are not replayed.
