# Phase 1 step 5 — hand-checked real trades: plan and pass rule

**Written 2026-11-24, before any trade is examined.** Changes after the commit are dated amendments appended below.
Labels: (a) source states, (b) measured, (c) inference.

## Purpose

R1 showed that the Zorro template and the Python engine make the same trades on real EUR/USD data. Both were written from
the same decision document (`docs/template/NNFX_TEMPLATE_DECISIONS.md`), so a misread NNFX rule would be shared and invisible.
Step 5 checks real trades against the rules themselves, by the user, with Claude laying out the numbers.

## What is checked

Source: R1a run 2 (`C:/Zorro/Data/TPL_R1a_log_run2.csv`, sha256 `051c1286dfb3ae8b…`; 325 trades, 650 halves; no costs).
Worksheets: `python tools/step5_worksheet.py <group>` (daily bars from the raw M1 records, slot values, levels, sizing,
the M1 record of each intrabar exit). No profit or performance figure is shown (R-D1).

**Selection rule (fixed, seed 20261124):** one trade at random for each exit combination that occurs (9); every trade with a
daily bar whose range covers both the stop and TP1 while half 1 is open (2); then, if missing, one random trade per entry kind
and direction (none needed). Result, in date order:

| Trade | Dir | Entry kind | Entry - last exit | Halves | Reason picked |
|---|---|---|---|---|---|
| #5 | long | continuation | 2007-07-20 - 07-25 | stop / stop | exit stop/stop |
| #22 | short | baseline | 2008-06-03 - 06-06 | tp1 / be_adverse | exit tp1/be_adverse |
| #29 | long | c1 | 2008-12-09 - 12-19 | tp1 / trail | exit tp1/trail |
| #96 | short | baseline | 2013-04-26 - 04-29 | baseline / baseline | exit baseline/baseline |
| #147 | long | baseline | 2016-03-10 - 03-10 | stop / stop | same-bar stop + TP1 day |
| #158 | short | c1 | 2016-10-05 - 10-10 | tp1 / baseline | exit tp1/baseline |
| #161 | long | baseline | 2016-12-06 - 12-08 | tp1 / stop | exit tp1/stop; same-bar day |
| #275 | short | continuation | 2023-05-24 - 06-02 | tp1 / c1_flip | exit tp1/c1_flip |
| #287 | short | continuation | 2024-02-06 - 02-08 | c1_flip / c1_flip | exit c1_flip/c1_flip |
| #317 | long | c1 | 2025-11-27 - 12-02 | tp1 / be | exit tp1/be |

Plus one **refused signal**: a bridge-too-far case drawn at random (same seed) from the 35 baseline-cross bars where C1 already
agreed and its signal was >= 7 bars old: **2013-02-20, short, C1 signal 12 bars old** (`step5_worksheet.py btf 20130220`).

(b) Not reachable on real trades: **pullback entries** (none in 19 years). Covered by the synthetic S4 scenarios only.

## Rules checked on every trade (sources in NNFX_TEMPLATE_DECISIONS / NNFX_Sources)

1. Entry allowed: close on the trade's side of the baseline; C1 signal on the decision bar (or baseline cross with C1 agreeing,
   or continuation conditions T9); C2 agrees; |close - baseline| <= 1 x ATR (not for continuation); bridge-too-far (T10).
2. Fill at the next bar's first price (T4); stop = fill -/+ 1.5 x ATR of the decision bar; TP1 = fill +/- 1 x ATR.
3. Lots per half = floor(Equity x 1% / (stop pips x PIPCost)) (M-D8).
4. Each exit: right reason, day and price (stop / TP1 intrabar at the level or a gap open; breakeven after TP1; trail after a
   close 2 x ATR beyond entry, 1.5 x ATR behind the best close; C1 flip and baseline cross at the next open; M-D3).
5. One trade (#5, #96 suggested) checked against an independent chart (ATR or a candle) outside our tools.

## Pass rule

Step 5 PASS if, on all 10 trades and the refused signal, every applicable rule agrees with the trade. Any disagreement is
investigated and recorded with its cause; a template or engine defect means a fix, the S4 / R1 reruns, and step 5 again.
No performance figure is read before step 5 passes.
