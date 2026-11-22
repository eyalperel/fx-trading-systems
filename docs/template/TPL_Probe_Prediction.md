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
