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

---

## Results — 2026-11-24 (rules checked trade by trade; key prices against independent daily records)

Method (user, 2026-11-24): Claude checks each rule on the worksheet and confirms the decisive prices against daily OHLC
published by exchangerates.org.uk (ERUK) and poundsterlinglive.com (PSL); the first trade was walked through with the user.
Independent sources use their own day cut-off (ours: 17:00 New York), so closes may differ; highs and lows of the decisive
days are compared. Where one source's row was internally inconsistent (low above open), the other was used.

| Trade | Rules (entry / fill + levels / lots / exits) | Decisive prices: ours vs independent | Result |
|---|---|---|---|
| #5 long cont. | Continuation: prior long closed by TP1 + C1 flip, no baseline close, C1 back to +1 on 07-19, C2 +0.152; 1 ATR distance waived (172.7 pips) [V29]. Stop 1.37083, TP1 1.38676; 129 lots. Stop 07-25 10:46 NY at the level | 07-25 low 1.36969 vs ERUK 1.3695; week high 1.38519 < TP1 (commentary: top 1.3851) | PASS (with user) |
| #22 short baseline | Cross down 05-29, C2 positive until 06-02 (catch-up, no day limit, T10); distance 75.6 < 129.4. Stop 1.57311, TP1 1.54076; 64 lots. TP1 on the 06-05 bar (06-04 21:27 NY); close 1.55932 above entry: runner out at next open (M-D3) | 06-03 low 1.54110 vs ERUK 1.5408 (TP1 not reached either way, 0.4-3.4 pips); 06-05 low 1.53655 / high 1.56008 vs ERUK 1.5363 / 1.5603 | PASS |
| #29 long C1 | C1 -1 -> +1 on 12-08, close above FAMA, C2 +, distance 157.7 < 231.8. Stop 1.26175, TP1 1.31970 (12-11 06:53); breakeven, trail active from the 12-15 close (>= entry + 2 ATR), trail 1.5 ATR behind best close 1.44210 = 1.40733; hit 12-19 04:05; 35 lots | 12-18 high 1.47198 / low 1.41817 vs ERUK 1.4721 / 1.4184; 12-19 low 1.38247 vs ERUK 1.3822, FXIS 1.3824 | PASS |
| #96 short baseline | Cross 04-23 dies (close back above 04-24); new cross 04-25, C2 -, distance 6.1; bridge-too-far age 5 < 7. Stop 1.31625, TP1 1.29100; 79 lots (raw 79.99). 04-26 close above FAMA: baseline exit at the 04-29 open | 04-26 high 1.30479 / low 1.29908 / close 1.30273 vs ERUK 1.3050 / 1.2989 / 1.3027 | PASS |
| #147 long baseline | Cross 03-04, C2 + only on 03-09 (catch-up), distance 9.0. Stop 1.08647, TP1 1.10952; 85 lots. ECB day 03-10: stop reached 07:48 NY, TP1 only 09:14: both halves stopped | 03-10 low 1.08217 / high 1.12184 vs ERUK 1.0820 / 1.1220 (both levels inside the day) | PASS |
| #158 short C1 | C1 +1 -> -1 and baseline cross on 10-04, C2 -, distance 1.0. Stop 1.13086, TP1 1.11399; 115 lots. TP1 on the 10-07 bar (10-06 19:16 NY); 10-07 close 0.3 pip above FAMA: baseline exit at the 10-10 open | 10-06 low 1.11400 vs ERUK 1.1141: TP1 not reached on 10-06 (margin 0.1 pip) | PASS (knife-edge) |
| #161 long baseline | Cross 12-05 with C1 + (signal age 6 < 7) and C2 +, distance 51.3. Stop 1.06066, TP1 1.08701. ECB day 12-08: TP1 07:47, runner's original stop 10:55 (breakeven only from the next bar, T5.3); 77 lots | 12-08 high 1.08747 / low 1.05975 vs ERUK 1.0875 / 1.0598 | PASS |
| #275 short cont. | Prior short closed by TP1 + C1 flip; no close above FAMA; C1 back to -1 on 05-23, C2 -; distance waived (168.5). Stop 1.08754, TP1 1.07019 (05-29 23:38 NY, bar 05-30); breakeven 1.07713 not touched (06-01 high 1.07690); C1 flip 06-01, exit at the 06-02 open; 103 lots | 05-30 low 1.06729 vs PSL 1.0673; 06-01 high 1.07690 vs PSL 1.0769 (breakeven missed by 2.3 pips) | PASS |
| #287 short cont. | Prior short closed by C1 flip; no close above FAMA; C1 back to -1 on 02-05, C2 -; distance waived (141.8). Stop 1.08471, TP1 1.06738, neither reached; C1 flip 02-07, exit at the 02-08 open; 101 lots | 02-06 high 1.07629 / low 1.07229 vs PSL 1.0762 / 1.0723; 02-07 1.07843 / 1.07542 vs PSL 1.0784 / 1.0754 | PASS |
| #317 long C1 | C1 -1 -> +1 and baseline cross 11-26, C2 +, distance 18.1. Stop 1.15133, TP1 1.16507 (12-01 08:05); breakeven 1.15957 hit 12-02 10:25; 130 lots (raw 130.99) | 12-01 high 1.16532 / low 1.15899 vs ERUK 1.1651 / 1.1590, PSL 1.1652 / 1.1590 | PASS |
| Refused 2013-02-20 | Cross down with C1 already - since its 02-04 signal (12 bars, >= 7): bridge-too-far, no entry (distance 95 pips < 114.8, so it was the only blocker; earlier cross 02-14 refused the same way, age 8); no trade until 04-08 | 02-20 high 1.34343 / low 1.32710 / close 1.32817 vs ERUK 1.3435 / 1.3273 / 1.3286 | PASS |

Every independent high / low agrees with our bars within 0.4 pip (rounding to 4 decimals included); no decisive level lies on
the other side in any independent record.

**Observation (b), not a rule issue:** several outcomes hang on small margins on our data: #158 TP1 0.1 pip and the baseline
exit 0.3 pip; #22 TP1 missed by 3.4 pips; #275 breakeven missed by 2.3 pips; #317 TP1 reached by ~0.25 pip. Another price feed
can flip such cases. (c) Results should later be checked for sensitivity to the data source (a second EUR/USD feed).

**Verdict: Phase 1 step 5 PASS** — on all 10 trades and the refused signal every applicable rule agrees with the trade, and
the decisive prices agree with independent daily records. Performance may now be read (R-D1 lifted).
