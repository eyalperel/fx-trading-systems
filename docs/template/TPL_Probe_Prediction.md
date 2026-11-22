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
