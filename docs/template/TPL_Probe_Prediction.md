# TPL_Probe — prediction (written before the run)

**Date:** 2026-11-22. **Script:** `strategies/tests/TPL_Probe.c`. **Inputs:** made by
`python tools/make_scenarios.py --zorro C:/Zorro --out analysis/template/probe --start 2024-03-06 A2 A3`.
Expected trades from the reference engine: `analysis/template/probe/expected_SYN_A2.csv`,
`expected_SYN_A3.csv`. This is a probe of platform behaviour (like `PROBE_SeriesExprLen`),
not an acceptance test: each item below is the outcome predicted from the Zorro 3.11
manual (`docs/template/ZORRO_TRADE_MECHANICS.md`); a different outcome is recorded and
decided on, not argued away.

| # | Item | Predicted outcome | Basis |
|---|---|---|---|
| 0 | Zorro window | No line starting with `Error` | CLAUDE.md §7 |
| 1 | `INFO` row | `assetList_rc` > 0; `rows_A2=4`; `rows_A3=3`; `BarOffset=1020`; `Fill=3` | asset.htm, data.htm |
| 2 | P4 EUR/USD bars | `ldate_est` time of day = 17:00 on every bar; `wdate_utc` 22:00 UTC up to Fri 2024-03-08, 21:00 UTC from Mon 2024-03-11 | assetzone.htm (EST with DST), barperiod.htm |
| 3 | Synthetic bars | One `BAR` row per scenario day (A2: Mar 6, 7, 8, 11; A3: Mar 6, 7, 8), OHLC equal to the file values (float32), `dd` in [0, 1) day | history.htm |
| 4 | Entry signal | `ENTER` row for SYN_A2 and SYN_A3 on the Mar 7 bar; stop distance 0.0150, TP distance 0.0100 (float32 ATR) | T1-T3, scenario |
| 5 | P1 fill | Both halves of both scenarios: `TradePriceOpen` = 1.0000 (the Mar 8 open); `TradeBarOpen` = the Mar 8 bar | fill.htm mode 3 |
| 6 | A2 half 1 | Closed on the Mar 8 bar at 1.0100 (TP1) | fill.htm, stop.htm |
| 7 | A2 runner | Stop moved to 1.0000 at the Mar 8 close; closed on the Mar 11 bar at 1.0000 | trade.htm (TradeStopLimit), fill.htm "Min of Stop and Open" |
| 8 | P3 A3 | Both halves closed on the Mar 8 bar at 0.9850 (stop); half 1 not at its TP | stop.htm "Stop is always triggered earlier inside the bar than TakeProfit" |
| 9 | Prices vs reference engine | Exit prices equal the expected files within 1e-6 (float32 inputs, spread 0, slippage 0) | make_scenarios.py |

Unknowns (recorded, not predicted): whether Zorro creates bars for SYN_A2 / SYN_A3 on days
without a record (Mar 12-15); whether `TradePriceClose` / `TradeProfit` include anything
beyond price difference with spread 0; Zorro log warnings about the synthetic assets.

---

## Run 1 — 2026-11-22 18:53 (setup failure; predictions not reached)

Raw output kept as `C:/Zorro/Data/TPL_Probe_raw_run1.csv` (sha256 `3360997c87aeaeb0…`).
- (b) Compiled with no compile error. `INFO` row as predicted (item 1): assetList_rc=29,
  rows_A2=4, rows_A3=3, BarOffset=1020, Fill=3.
- (b) `Error 047: EUR/USD no 2024 history (History\EURUSD_2024.t6)` and
  `Error 047: EUR/USD 2024..2024 no data`, although the file is intact (371,157 records,
  strictly descending, ~1,440 records on 2024-03-06). (a) Zorro 3.11 errors.htm, Error 047:
  "Don't use ... a part of the data split into years and another part not." The synthetic
  files were named `SYN_A2.t6` (not year-split): **cause attributed to the generator**
  (c, confirmed only if run 2 loads EUR/USD).
- (b) Zorro's first bar is a partial bar ending at the first record (bar 0 stamped
  03-06 20:59 UTC); the 03-06 and 03-07 records fell into it, so the first full daily bar
  was 03-08 and the C1 signal (03-07) was never seen: no ENTER, no trades. Items 4-9 not
  tested.
- (b) Bars 1 and 2 were stamped Fri 03-08 22:00 UTC and Mon 03-11 21:00 UTC = 17:00
  New York on both sides of the DST change (item 2's mechanism, seen on synthetic bars).
- (b) With EUR/USD not loaded, `asset("EUR/USD")` left the previous asset selected and its
  rows repeated SYN_A3 prices: the probe did not check the return value.

## Amendment 1 — 2026-11-22 (before run 2)

Changes (generator and probe only; rules, expected trades and items 0-9 unchanged):
1. Synthetic history year-split: `SYN_A2_2024.t6`, `SYN_A3_2024.t6`. The old unsplit files
   were moved to `History/_to_delete/` (deletion is not enabled from the session).
2. Five neutral warm-up bars before each scenario (2024-02-28 .. 03-05): close 0.9990 above
   the baseline, C1 = -1, C2 = +1; they cannot signal. Scenario days unchanged (PRE 03-06,
   signal 03-07, entry 03-08, A2 runner exit 03-11).
3. `StartDate = 20240228`.
4. The probe logs `ASSETFAIL` when `asset()` returns 0.
Added prediction for run 2: no `ASSETFAIL` rows; EUR/USD bar rows carry EUR/USD prices
(around 1.08-1.09 in March 2024), not synthetic ones.

## Run 2 — 2026-11-22 18:56 (setup failure)

Raw output kept as `C:/Zorro/Data/TPL_Probe_raw_run2.csv`. Zorro window and log:
`Error 047: SYN_A2 no 2024 history (History\SYN_A2_2024.t6)`, `Error 047: SYN_A2 2024..2024
no data.`, `Error 047: No bars generated`.
- (b) Runs 1-2 together: an unsplit file of daily records (`SYN_A2.t6`) loaded; the same
  records year-split (`SYN_A2_2024.t6`) were rejected; year-split M1 EUR/USD was rejected
  when loaded after an unsplit daily synthetic asset (run 1).
- (c) Amendment 1's cause (year-split naming alone) is **refuted** by run 2. Working reading,
  not established: Zorro treats year-split files as high-resolution history and requires
  one history type across the assets of a script (errors.htm, "same type for all assets").
  Not pursued: the template never needs both kinds in one script.
- No user broker / demo account is involved: [Test] is an offline backtest on History files.

## Amendment 2 — 2026-11-22 (before run 3)

1. Synthetic history back to one unsplit file per scenario (`SYN_A2.t6`, `SYN_A3.t6`), as in
   run 1 where it loaded. Year-split synthetic files moved to `History/_to_delete/`.
2. EUR/USD removed from this probe. Synthetic and real (year-split M1) history are never
   mixed in one script. Item 2 (P4 on EUR/USD) moves to the later EUR/USD-only run; its
   mechanism on synthetic bars is item 2b below.
3. Warm-up bars (Amendment 1, item 2) and the asset() check kept.
Predictions for run 3: items 0, 1, 3-9 unchanged; the Amendment 1 EUR/USD prediction is
withdrawn. Item 2b: synthetic bars 03-08 (and earlier) stamped 22:00 UTC, 03-11 stamped
21:00 UTC, `ldate_est` 17:00 on every full bar (bar 0 is a partial bar ending at the first
record, run 1).

## Run 3 — 2026-11-22 19:07 (ran; items 6-9 failed, cause found)

Raw output kept as `C:/Zorro/Data/TPL_Probe_raw_run3.csv` (sha256 `dbe71dcb269a2465…`).
Zorro: `Trades 4 Win 0.0% Avg -106.0p`, no Error line.
- (b) Items 0, 1, 2b, 3, 4 as predicted: no Error; INFO rows 9 / 8; full bars stamped
  22:00 UTC up to 03-08 and 21:00 UTC on 03-11 (17:00 New York); ENTER for both scenarios
  on the 03-07 bar with stop distance 0.0150 and TP distance 0.0100.
- (b) Item 5: both halves of both scenarios filled at 1.00000 on the 03-08 bar. Not
  conclusive for P1: 1.0000 is also the 03-07 close.
- (b) Items 6-8 **failed**: no stop or target fired on 03-08 although A3's low (0.98449)
  crossed the stop and both highs (1.011) crossed TP1; all four trades were closed at the
  end of the test (03-11). (a) mode.htm: without `TICKS` "an intra-bar approximation is
  used", and "TICKS should be used when trades enter and exit at the same bar"; the probe
  did not set TICKS. A first explanation in the planning chat ("the single tick was used
  up") was a guess and is withdrawn.
- (b) The logged stop / target / profit values were garbage: those trade fields are 4-byte
  `float` and were printed with `%f` without a cast (gotchas 9d.11).

## Amendment 3 — 2026-11-22 (before run 4)

1. `TICKS` set in INITRUN (`nx_TicksOn = 1`; T5 amendment in NNFX_TEMPLATE_DECISIONS.md).
2. Each synthetic day is an intraday path of 4 records: the open (O = H = L = C), then three
   segment candles open -> first extreme -> second extreme -> close (up day: low first; down
   day: high first). A level inside a segment fills at the level, a gap at the day's open
   stays a gap (fill.htm). `tools/make_scenarios.py`.
3. New scenarios: **A3HF** (A3's day, high first) and **P1** (entry bar opens at 1.0010,
   signal close 1.0000; reference test `test_P1_entry_at_next_open_not_signal_close`).
4. Float trade fields cast to `var` when printed.

Predictions for run 4 (tolerance 1e-6 on prices; float32 inputs, spread 0, slippage 0):

| # | Item | Predicted |
|---|---|---|
| 0 | Zorro window | no line starting with `Error` |
| 1 | INFO | rows_A2=9, rows_A3=8, rows_A3HF=8, rows_P1=9, BarOffset=1020, Fill=3, TICKS=1 |
| 2b | Bar stamps | full bars 22:00 UTC up to 03-08, 21:00 UTC on 03-11; `ldate_est` 17:00 |
| 4 | Entries | ENTER on the 03-07 bar for all four scenarios |
| 5 | P1 fill | SYN_P1 both halves at **1.0010** (03-08 open, not the 03-07 close 1.0000); A2 / A3 / A3HF at 1.0000 |
| 6 | A2 half 1 | TP1 on 03-08 at 1.0100 |
| 7 | A2 runner | stop set to 1.0000 at the 03-08 close; stopped on 03-11 at 1.0000 |
| 8 | A3 (low first) | both halves stopped on 03-08 at 0.9850 (= reference engine, T5.2) |
| 8b | A3HF (high first) | half 1 TP1 on 03-08 at 1.0100; runner stopped on 03-08 at 0.9850. **Differs from the reference engine** (both halves stop, T5.2): the documented TICKS-order case, not a failure |
| 9 | Stop / TP prices while open | stop 0.9850 (A2, A3, A3HF), 0.9860 (P1); TP1 1.0100 (A2, A3, A3HF), 1.0110 (P1); runners no TP |
| 10 | P1 exits | both halves still open at the last scenario bar; closed by the end of the test (price recorded, not predicted) |

## Run 4 — 2026-11-22 19:13 (ran with TICKS; spread contamination found)

Raw output kept as `C:/Zorro/Data/TPL_Probe_raw_run4.csv` (sha256 `464f6b8a80a1d8ec…`).
Zorro: `TPL_Probe (TICKS) 2024`, `Trades 8 Win 25.0% Avg -98.8p`, no Error line.
- (b) Items 0, 1 (TICKS=1), 4 as predicted. **Item 5 (P1) passed:** SYN_P1 filled at 1.00100
  on the first tick of 03-08, not at the 03-07 close 1.00000 (next-open fill, T4).
  **Item 9 passed:** stop 0.98500 (P1 0.98600), TP1 1.01000 (P1 1.01100), runners TP 0.
- (b) Every trade result is 0.0100 x 1000 = 10 account units worse than its price
  difference (A3: (0.9845 - 1.0000) x 1000 = -15.5, Zorro -25.5; A3HF +11 -> +1.0; A2 -4 ->
  -6.0; P1 +1 -> -9.0), and every entry shows "Risk 25" = (stop 0.0150 + 0.0100) x 1000:
  an effective **spread of 0.0100** although `assetAdd(..., Spread 0, ...)` was given 0.
- (b) A3 stopped on its entry day at the low tick, filled at the tick price 0.98450, not at
  the stop 0.98500: with TICKS the fill is the crossing record's price.
- (b) Not explained, not interpreted while the spread is 100 pips: A3HF runner exited with
  half 1 at 1.011; A2 half 1 did not take TP1 on 03-08; A2 and P1 pairs exited together on
  the first Monday tick.
- (b) Generator bug: Monday ticks were stamped from Friday 18:00 New York (weekend
  subtracted twice); bar assignment unaffected.

## Amendment 4 — 2026-11-22 (before run 5)

1. `Spread = 0;` set in the probe after every `asset()` call (spread.htm: "For a backtest
   with no transaction costs, set Spread = 0").
2. Path segments cut into records of at most 0.1 pip (STEP = 1e-5): fills overshoot a level
   by at most 1e-5. Checked before the run: first crossings on 03-08 at 0.985000 (A3 stop)
   and 1.010001 (A3HF / A2 TP1).
3. Monday's bar ticks start Sunday 18:00 New York (checked: first tick Sun 03-10 22:00 UTC).

Predictions for run 5: the run 4 table (items 0, 1, 2b, 4, 5, 6, 7, 8, 8b, 9, 10), with every
stop / TP fill within **1e-5** of its level, and Zorro trade results = price difference x 1000
(no extra cost). Expected Zorro summary: 8 trades; A2 +10.0 / 0.0; A3 -15.0 / -15.0;
A3HF +10.0 / -15.0; P1 two trades closed by the end of the test (last scenario close 1.0025,
about +1.5 each, recorded not predicted).

## Run 5 — 2026-11-22 19:17 (spread fixed; end-of-history close found)

Raw output kept as `C:/Zorro/Data/TPL_Probe_raw_run5.csv` (sha256 `79cc361459cf8a4a…`).
Zorro: `Trades 8 Win 50.0% Avg +20.0p`, PF inf, no Error line.
- (b) Spread fixed: every entry "Risk 15" = 0.0150 x 1000.
- (b) **Item 6 passed:** A2 half 1 closed at 1.010000 (TP1), profit 10.000.
- (b) **Item 7, first half passed:** A2 runner stop moved to 1.000000 at the 03-08 close.
- (b) Item 5 again: P1 filled at 1.001000.
- (b) Every other exit fell on the **first tick of the asset's last day of history**: A3 / A3HF
  (history ends 03-08) both halves closed 12-16 s after entry at 0.99999 / 1.00001; A2 runner
  and both P1 halves (history ends 03-11) closed on the first Monday tick (Sun 22:00 UTC) at
  1.004 / 1.002. The same pattern accounts for the unexplained run 4 exits (spread aside).
  (c) Zorro closes an asset's open trades at the start of its final history bar. Items 7
  (second half), 8, 8b, 10 not tested.

## Amendment 5 — 2026-11-22 (before run 6)

1. Five flat trailing bars after each scenario (at its last close, last states unchanged):
   nothing new can trigger; the scenario's own days complete. `EndDate = 20240322`.
2. Expected trades regenerated: unchanged except P1's "end" date (03-18).
3. For the S4 criteria (to be written): trades still open when the history ends (reason
   "end") are compared on entry only; Zorro and the engine close them at different moments.

Predictions for run 6: the run 4 table, fills within 1e-5, results = price difference x 1000.
Expected Zorro trades: A2 +10.0 (TP1 03-08) and 0.0 (runner stop 1.0000 during 03-11, not at
the open); A3 -15.0 / -15.0 (03-08); A3HF +10.0 (TP1) / -15.0 (runner stop, 03-08);
P1 two trades closed at the end of its history (about +1.5 each, recorded not predicted).
Summary: 8 trades, 4 wins counting P1 (A2 runner 0.0 is not a win).

## Run 6 — 2026-11-22 19:19 — ALL PREDICTIONS MET

Raw output kept as `C:/Zorro/Data/TPL_Probe_raw_run6.csv` (sha256 `8aa68c81286bb98c…`).
Zorro: `Trades 8 Win 50.0% Avg -27.5p`, total -22.00, no Error line (predicted: 8 trades,
4 wins, +10 + 0 - 15 - 15 + 10 - 15 + 1.5 + 1.5 = -22).

| # | Result (b) |
|---|---|
| 0, 1 | no Error; INFO as predicted, TICKS=1 |
| 2b | all 12 full bars `ldate_est` 17:00; UTC 22:00 on 03-08, 21:00 on 03-11 (DST) |
| 4, 5 | ENTER on 03-07; fills at the 03-08 first tick: 1.000000, SYN_P1 **1.001000** (next open, not the 1.0000 close) |
| 6 | A2 half 1 "Target 1@1.01000 +10.00" (|d| 9.3e-9 vs expected) |
| 7 | A2 runner stop 1.000000 from the 03-08 close; "Stop 1@1.00000: 0 at 08:08:39 Mon" (inside 03-11, not at the open) |
| 8 | A3: both halves "Stop 1@0.985000: -15.00" on 03-08 (|d| 1.4e-8) |
| 8b | A3HF: half 1 "Target 1@1.01000 +10.00 at 03:32:45", runner "Stop 1@0.985000 -15.00 at 09:53:13": the predicted TICKS-order difference from the engine (engine: both stop, T5.2) |
| 9 | stop / TP levels as predicted |
| 10 | P1 both halves closed at the end of history at 1.002500 (+1.50 each) |

Probe complete. Mechanics confirmed for the template: next-open fill (Fill 3), TICKS
entry-bar exits, stop / TP fills at the level on fine paths, breakeven by `TradeStopLimit`
at a close, 17:00 New York bars across DST, `assetList` of the project list, dataset states
(`%w`), unsplit synthetic history, `Spread = 0` by script. Constraints learned: gotchas
9d.11-9d.14 plus the end-of-history close (Zorro closes an asset's trades at the first tick
of its last history day; synthetic scenarios carry 5 trailing bars).
