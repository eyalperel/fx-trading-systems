# Zorro 3.11 — Trade Mechanics for the NNFX Template (stage S0)

**Date:** 2026-11-22 (planning chat). **Purpose:** what Zorro does with orders, stops,
bars and costs, read from the manual before any template code, so that decisions T4,
T5, T7 and T8 (`NNFX_TEMPLATE_DECISIONS.md`) are implemented on stated behaviour.

**Source.** `C:/Zorro/zorro.chm` (dated 2026-07-12, shipped with the install), unpacked
with `hh.exe -decompile` to `C:/Zorro/manual_311/` (408 files). Its "What's new" page:
"Updating Zorro 3.01 to Zorro 3.11", i.e. the manual of the installed version.
`C:/Users/eyalp/zorro_help/` is an older copy (newest version mentioned: 2.70); not
used here. Page names below are files in `manual_311/en/`.

Labels: **(a)** the 3.11 manual states · **(b)** measured or read here · **(c)** inference.
Every (a) item that a decision depends on is still confirmed by a probe (§10) or by
the hand-calculated trades of Phase 1 step 5.

---

## 1. Entry fill — T4 (next-open fill)

- (a) `Fill` mode 3, "Delayed realistic order filling. Trades do not fill immediately,
  but wait for the next price quote. With daily bars, this mode simulates trading at the
  market open price of the next day." Manual example: `Fill = 3; // enter trades at next
  day's open` (fill.htm).
- (a) Default is mode 1: "With daily bars, this mode simulates trading right before the
  market closes" (fill.htm).
- **Consequence:** T4 is `Fill = 3`. Mode 1 is the close-fill variant named in T4.

## 2. Stop and take-profit fills inside a bar — T5.1

- (a) Without `TICKS`, an intrabar fill is estimated from the bar's open, high and low.
  Table for Fill 1 / 2: Long Stop = "Min of Stop and Open"; Short Stop = "Max of Stop
  and Open"; Long TakeProfit (Fill 1) = "Max of TakeProfit and Open"; Short TakeProfit
  (Fill 1) = "Min of TakeProfit and Open" (fill.htm).
- (c) Mode 3 is "delayed realistic", i.e. mode 1 with a delayed entry; the table lists
  modes 0-2 only, so the mode-3 limit fills are assumed equal to mode 1. Probe P1.
- **Consequence:** a gap past the stop fills at the open, which is T5.1. A gap past TP1
  fills at the open too (better than the limit, in the trade's favour).

## 3. Same-bar stop and take-profit — T5.2

- (a) "Stop is always triggered earlier inside the bar than TakeProfit, causing a
  slightly pessimistic test result when multiple limits are triggered within the same
  bar. Entry and exit limits will not be triggered at the same time." (stop.htm)
- (a) "When the Stop limit is already met at entering, the trade will be opened and
  immediately closed, losing slippage and spread." (stop.htm)
- **Consequence:** Zorro's built-in order is T5.2 (stop first). No workaround needed.
  (c) The optimistic-order sensitivity run of T5.2 cannot be produced by Zorro without
  `TICKS`; it is computed by the Python reference engine only.

## 4. Changing a stop after entry; trailing — T5.3, T5.4

- (a) `Stop`, `TakeProfit`, `Trail` "have no effect on ... already entered trades. For
  changing a stop or profit target of a trade that was already entered, use either a
  TMF, or call exitTrade with the new price limit" (stop.htm).
- (a) `TradeStopLimit`: "Current stop level ... The trade will be closed when the price
  reaches this value. Can be modified ... by setting it to the desired price (not to a
  distance!)" (trade.htm). The manual modifies it inside `run()` in a
  `for(open_trades)` loop (fortrades.htm examples).
- (a) Zorro's own `Trail`, `TrailSlope`, `TrailStep`, `TrailLock` trail intrabar: "On a
  long trade, the stop limit is trailed by the High and limited by the Low" (stop.htm).
- (a) "When the Stop is moved inside the price range of the current bar or tick, the
  trade will be immediately closed." (stop.htm)
- **Consequence:** Zorro's `Trail*` variables stay 0. They trail on intrabar highs,
  while M13 trails on closes. Breakeven and the close-based trail are set by assigning
  `TradeStopLimit` (a price) in `for(open_trades)` at each bar close.
- (c) Edge case, open: breakeven is due (T5.3) but the close is already on the wrong
  side of entry. Setting the stop there puts it beyond the current price. What Zorro then
  does under `Fill = 3` (close at once, or at the next open) is not stated for this case.
  Probe P2; decision M-D3.

## 5. Ask, bid and spread on limits — T7

- (a) "all prices are given as ask prices ... long trades are filled at the ask price and
  closed at the bid price, short trades are filled at the bid price and closed at the ask
  price. The bid price is the ask price minus Spread." (stop.htm)

## 6. Daily bars and their close time — A17

- (a) "daily bars will start and end at BarZone midnight plus BarOffset"; BarZone default
  UTC (assetzone.htm). `BarOffset` "default = 940 with daily bars ... the 940 default sets
  it to 15:40 in the bar time zone" (barperiod.htm).
- (a) `BarZone = EST` is New York, "Daylight saving time is used"; manual example: daily
  trading at 15:30 New York = `BarOffset = 15*60+30; BarZone = EST;` (assetzone.htm).
- (b) `C:/Zorro/History/EURUSD_2005.t6` .. `EURUSD_2026.t6`, about 11.8 MB per year:
  about 370k 32-byte records a year, i.e. 1-minute data. Zorro builds the daily bars
  from it.
- (b) No script in the repo sets `BarOffset` or `BarZone` (grep, 2026-11-22). Every D1
  bar used so far closed at **15:40 UTC**, not at the 17:00 New York close VP trades
  against (A17: 2 pm Pacific = 17:00 New York). This does not affect the indicator
  verifications (synthetic inputs; the ATR cross-check compared two calculations on the
  same bars). It does affect the template. Decision M-D1.

## 7. Costs — T7

- (a) Without a broker connection, Spread, Commission, RollLong / RollShort come from the
  asset list. If `assetList` is not called, the default list is `AssetsFix.csv`
  (spread.htm, asset.htm).
- (b) `C:/Zorro/History/AssetsFix.csv`, EUR/USD row: Spread 0.00008 (0.8 pip),
  RollLong -0.6317, RollShort 0.3004 (daily, per 10000 contracts), Commission 0.0,
  PIP 0.0001, PIPCost 0.085849, lot amount 1000. AUD/USD and BTC/USD rows exist; no
  EUR/JPY row.
- (a) `Slippage`: "Simulated slippage in seconds (default = 5), effective in [Test] mode
  ... estimated by extrapolation of the next candle" (spread.htm). This is a number with
  a cost effect that T7 did not cover. Decision M-D2.
- (a) Historical spreads are possible (`Spread = marketVal()`); the default is the fixed
  asset-list value (spread.htm).

## 8. Sizing — T8

- (a) The trade size is an integer number of lots (lots.htm). Risk per trade at a given
  stop = Lots x (Stop / PIP) x PIPCost (lots.htm). `Risk` can size trades automatically;
  its formula also includes spread and commission (lots.htm).
- (c) PIPCost 0.085849 for 1000 units of EUR/USD = 0.1 USD / 1.16487: the AssetsFix
  account currency appears to be **EUR**, not USD. T8's "$100,000" reads as 100,000
  units of the account currency.
- (c) Rough size: 1% of 100,000 = 1,000; stop 1.5 x 80 pips = 120 pips; per lot
  120 x 0.0858 = 10.3, so about 97 lots per half, and integer rounding about 1%.
  Measured per run (T8.3).

- **P6 reading, 2026-11-23 (decided as M-D8):**
  - (a) Equity = Balance + WinValTotal - LossValTotal; in test Balance = Capital + WinTotal - LossTotal
    (balance.htm, winloss.htm). Capital > 0 enables the simulated margin call (lots.htm).
  - (a) PIPCost comes from the asset list and "should normally remain constant during the simulation";
    a script may recompute it (pip.htm). (b) In `AssetsNNFX_FX.csv` it is a 2025-07-28 snapshot
    (EUR/USD 0.08561 = 0.1 / 1.16815; EUR/JPY 0.058102 ~ 10 / 172.12).
  - (a) MarginCost = price x PIPCost / PIP / Leverage, settable by script before entry; negative values are
    a percentage (pip.htm, account.htm). (b) The list has -1 (leverage 100); T8 wants 20.
  - (a) Zorro's `Risk` sizer adds the spread and commission to the stop distance (lots.htm); not used.
  - (c) Open: valuation price of open trades in Equity, and Equity's update timing in a multi-asset loop.

## 9. Data availability (dev set) — found while reading

- (b) `C:/Zorro/History` holds only `EURUSD_*.t6` plus asset lists. BTC/USD H4, EUR/JPY
  D1 and AUD/USD D1 (dev set, PROJECT_STATE §2) are **not** there. To locate before any
  dev-set run (they may sit elsewhere; PROJECT_STATE §1.3 lists EUR/JPY and AUD/USD as
  Darwinex MT4 imports).

## 10. Probes for S3 / S4 (one batch, one click)

| # | Question | Pass condition (to pre-register) |
|---|---|---|
| P1 | `Fill = 3`: entry at the next bar's open; stop / TP fills follow the mode-1 table | Hand-calculated fills match on chosen bars |
| P2 | `TradeStopLimit` set at a close: effective from the next bar; behaviour when the new stop is already beyond the close | Observed behaviour recorded; matches M-D3 |
| P3 | Stop before TakeProfit on a bar touching both | Stop fill, TP not filled |
| P4 | `BarZone` / `BarOffset` give bars closing 17:00 New York | Bar timestamps checked across a DST change |
| P5 | Spread and rollover charged as the asset list states | Costs on vs off differ by the hand-computed amount (T7 guard) |
| P6 | Lot rounding and PIPCost in the account currency | Hand-computed lots match |

## 11. Decisions this raises (taken one at a time in the planning chat)

- **M-D1** Daily bar close time: **decided 2026-11-22**: `BarZone = EST; BarOffset = 17*60;`
  (bars close 17:00 New York). Record in `NNFX_TEMPLATE_DECISIONS.md`.
- **M-D2** `Slippage`: **decided 2026-11-22**: 0 in variant 0; 5 s (default) as a T11
  sensitivity level.
- **M-D3** Breakeven due while the close is already beyond entry: **decided 2026-11-22**:
  the template exits the runner at the next open (T5.5 handling); events counted.
- **M-D4** Asset list and account currency: **decided 2026-11-22**: project copy
  `config/assets/AssetsNNFX_FX.csv` of AssetsForex.csv, loaded explicitly; account EUR,
  100,000 EUR start.

## 12. Manual reads before the template code (2026-11-23, S3 template / S4)

| # | Question | Manual (a) | Consequence |
|---|---|---|---|
| R1 | `exitLong` sent at a close under `Fill = 3` | Mode 3: "Trades do not fill immediately, but wait for the next price quote" (fill.htm); the exit price "can be affected with the Fill variable" (selllong.htm). Exits not named explicitly | (c) next open, like entries. Unprobed: an explicit S4 prediction item (scenarios C1, C2) |
| R2 | `Hedge` default | 0 = NFA default, 1 = non-NFA default; 0 / 1 close opposite trades on entry; 2 never (hedge.htm, buylong.htm). Backtest default not stated | Set explicitly: M-D5, `Hedge = 2` |
| R3 | `enterLong` return | `TRADE*`, 0 when no trade was entered; assignable to `ThisTrade` (buylong.htm). When an entry is refused (`MaxLong` etc.), "stop limits, profit targets, and life times of open trades with the same asset and algo are updated to the current values" | Store `TradeID` per half. The template enters only when flat, so the refused-entry update cannot touch an open trade |
| R4 | Limits for a 58-asset batch | Free license limits account / profit, bar period and data resolution, not assets (restrictions.htm); dataset handles 1..1000 (data.htm); memory is the stated asset constraint, `TICKS` adds to it (errors.htm) | Allowed; the generator reports total records before the run |
| R5 | Fill rounding | "Fill prices are normally rounded to the point value of the asset. TR_FRC enables unrounded fill prices." (fill.htm) | (b) Run 6 fills within 1.4e-8 of their levels: not binding at the 1e-5 tolerance |
| R6 | Trading week and bar creation (S4 run 1) | `StartWeek` default Sunday 23:00 in the BarZone; no trading between EndWeek and StartWeek (date.htm, barmode.htm). Without BR_FLAT, bars exist only where the first asset has prices (barmode.htm) | M-D6: `StartWeek = 71700`. Synthetic batches share one last day. (b) Real EUR/USD 2024 opens Sunday 17:01-17:09 New York |
| R7 | Costs (P5 run 1, PROBE_AssetType) | Spread / commission / rollover rules (spread.htm, stop.htm); Forex only for real pair names (asset.htm) | (b) Forex costing needs a real pair name (gotchas 9d.18); long TP1 pays no spread, every other exit one; rollover per bar day incl. weekend days (9d.19, M-D7) |
