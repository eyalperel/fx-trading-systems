# S4 — Template equivalence: pre-registered criteria

**Written 2026-11-23, before the run** (Phase 1 step 4, stage S4). Commit this file before the
[Test] click with `tpe_CompileOnly = 0`. Changes after the commit are dated amendments appended
below, never in place. Labels: (a) source states, (b) measured, (c) inference.

## What is tested

The Light-C template (`strategies/template/NNFX_Template.h`, architecture A: Zorro executes, the
template decides at each close) must produce the same trades as the Python reference engine
(`analysis/template/reference_engine.py`, 32 hand-calculated tests) on the same inputs.

- **Inputs:** 64 synthetic assets written by `tools/make_scenarios.py ... ALL` (start 2024-03-06):
  30 long scenarios (A1-A6, A3HF, P1, B1, B2, C1-C3, D1a, D1b, D1d, D2, D5, D6, D7a-c, D8, D9, E1-E3,
  E4a, E4b, R1), their 30 short mirrors (`<name>M`), and 4 planted-bug controls. Slots SCRIPTED
  from each scenario's states file; intraday paths of 0.1-pip records; spread 0, slippage 0,
  1 lot per half. (b) Generator padding guard passed: warm-up / tail bars change no trade, except
  D6 / D6M, whose tail entry from a decision on the scenario's last bar is reported and kept.
- **Expected:** `analysis/template/equivalence/expected/` (engine trades per scenario + counts).
- **Script:** `strategies/tests/TPL_Equivalence.c`, `tpe_CompileOnly = 0`. Compile check (flag 1)
  done 2026-11-23: no Error line, no result seen.
- **Checker:** `python tools/compare_equivalence.py C:/Zorro/Data/TPL_Equivalence_log_run1.csv
  analysis/template/equivalence/expected analysis/template/equivalence/results/TPL_Equivalence_run1.csv`
  (18 tests, each planted defect seen to flip the verdict).

## Criteria

| # | Criterion | Pass condition |
|---|---|---|
| C0 | Zorro window | No line starting with `Error`; no `ERROR` or `ASSETFAIL` row in the log |
| C1 | Setup, per asset | INFO row present; states rows = scenario bars; Fill 3, Hedge 2, TICKS 1, BarOffset 1020 |
| C2 | Trades, per scenario | Same number of halves as the engine; per half (in trade order): half, direction, kind, entry day equal |
| C3 | Prices | Entry and exit within **1e-5** of the engine (fills overshoot a level by <= one 0.1-pip path step, Amendment 4 of the probe; float32 inputs on both sides) |
| C4 | Exits | Exit reason and exit day equal; halves the engine closes as `end` (still open when the history ends, gotchas 9d.15) are compared on entry only |
| C5 | Documented difference | A3HF and A3HFM (high-first / mirrored path): Zorro takes TP1 on half 1, then stops the runner on the same bar (A3HF: tp1 1.0100 / stop 0.9850; A3HFM: tp1 0.9900 / stop 1.0150). The engine stops both (T5.2). Pass = Zorro shows exactly these trades. Reported as DOC, not as PASS |
| C6 | Counts | Template's same-bar stop/TP1 count (T5.2) and M-D3 runner-exit count equal the engine's per scenario; no half with reason `other`; no trade open after the last bar |
| C7 | Controls | Each of the 4 control assets (A6_CM3, A6M_CM3: breakeven placed without the M-D3 check; R1_CMF, R1M_CMF: entry only when no trade is open) shows **at least one FAIL row** |

**Run verdict:** PASS only if C0 holds and all 60 real scenarios meet C1-C6 (DOC and ENTRY_ONLY
rows allowed) and all 4 controls meet C7. Anything else is FAIL, investigated and recorded; the
template is not used for any strategy result until a run passes.

## Prediction (before the run)

- (c) All 60 real scenarios PASS; 4 DOC rows (A3HF, A3HFM halves); **40 ENTRY_ONLY rows**, one per
  engine `end` half, in A5, C3, D5, D6 (tail entry), D7b, D7c, D8, E1, E4a, P1, R1 and their mirrors
  (counted from the expected files, not from memory).
- **Open item, first evidence in this run:** an exit sent with `exitTrade` at a close under
  `Fill = 3` fills at the next bar's open (ZORRO_TRADE_MECHANICS §12 R1, (c), unprobed). Scenarios
  C1, C2, R1, A6, E1, E4a and mirrors depend on it. If it fills elsewhere, those fail on exit day or
  price; the cause is recorded and decided, not tuned away.
- Controls: MF (R1_CMF, R1M_CMF) predicted to miss the reversal entry (2 halves instead of 4).
  M3 (A6_CM3, A6M_CM3) sets the runner's stop above the close; Zorro's reaction is not stated in
  the manual ("immediately closed", stop.htm; price and timing under Fill 3 unknown, M-D3), so
  only "differs from the engine" is predicted. Its actual exit is recorded (it answers P2's
  second half as an observation).

## Variants counted

- Template configurations exercised: **5** — variant 0 (48 assets), volume ALWAYS_NO (D2, D2M),
  volume indicator states (E1-E4b and mirrors, 10), bridge-too-far off (D7c, D7cM), no continuation
  after a stop (E4b, E4bM). Controls are planted bugs, not system variants: 2 mutants, 4 assets.
- Runs: this is run 1 of S4. Every rerun is counted and recorded with its cause.

## Not tested here (later stages)

Costs (spread, swap, commission: P5), lot sizing and PIPCost (P6), real bars and real indicators
(P4 on EUR/USD), fill rounding to 1 pip on 5-decimal quotes (`TR_FRC`, ZORRO_TRADE_MECHANICS §12 R5),
the optimistic same-bar order (engine only).

---

## Run 1 — 2026-11-23 09:43 — FAIL (two setup causes found; template logic not implicated)

Commit `356315a` (criteria + code). Log `C:/Zorro/Data/TPL_Equivalence_log_run1.csv` (sha256
`162400b83510ecac…`); checker output `analysis/template/equivalence/results/TPL_Equivalence_run1.csv`.
Zorro: `Test: TPL_Equivalence (TICKS) 2024`, `Trades 112`, no Error line.

- (b) C0 met (no Error / ERROR / ASSETFAIL). C7 met: 4/4 controls detected (A6_CM3 and A6M_CM3 3 FAIL
  rows each, R1_CMF and R1M_CMF 1 each). 4 DOC rows as predicted (A3HF / A3HFM match C5).
- (b) **50/60 real scenarios PASS; FAIL: A4, A4M, A5, A5M, A6, A6M, D7b, D7bM, D7c, D7cM.** ENTRY_ONLY
  rows 36 (predicted 40; the missing 4 are D7c / D7cM).
- **Cause 1 (b): Zorro's trading week.** Every failing fill is a Monday fill at 03:00:00 UTC (Zorro
  trade log): A4 stops at 0.97801 (gap open 0.9800 expected), A5 TP1 at 1.01201 (1.0130), A6 M-D3
  exit at 0.99651 (0.9975), D7b entry at 0.99800 (0.9990), mirrors alike. On the synthetic Monday
  path that time is the day's low (high for mirrors). (a) `StartWeek` default 72300 = "Sunday 23:00"
  in local time of the BarZone; with `BR_WEEKEND` (default) Zorro does not "trade ... between
  EndWeek and StartWeek in the bar time zone, even when they contain price quotes" (date.htm,
  barmode.htm). BarZone = EST (M-D1) puts the week start at Sunday 23:00 New York = Monday 03:00
  UTC; the synthetic Monday starts Sunday 18:00 New York. (b) Real EUR/USD 2024 (`EURUSD_2024.t6`,
  53 weekly gaps): last quote Friday 16:47-17:00 New York, first quote Sunday 17:01-17:09 New York.
  So on real data too, Monday-open fills would be taken up to 6 h after the weekly open.
- **Cause 2 (b): bar creation follows the first asset.** All 64 assets' last BAR row is 2024-03-18,
  the last history day of SYN_A2 (asset 0). (a) "If that flag [BR_FLAT] is not set, bars are only
  created where the first asset has valid prices" (barmode.htm). D7c / D7cM decided their entry
  at the 03-18 close and never got another bar (0 halves); D7b / D7bM entered at 03-18 and were
  closed by the end of the test. The generator gave scenarios different lengths (13-20 days).
- (c) Neither cause involves the template's decisions: every non-Monday fill, every reason, kind and
  day outside these cases matched; the controls failed as planted.
- Not interpreted further while the setup is wrong. Next: decision on the trading week (M-D6),
  generator fix for a common last day, Amendment 1, run 2.

## Amendment 1 — 2026-11-23 (after run 1, before run 2)

Changes (setup only; criteria C0-C7, tolerance, documented differences and the template's decision
logic unchanged):
1. **M-D6 (user decision 2026-11-23):** `StartWeek = 71700` (Sunday 17:00 New York, BarZone EST),
   named config value `nx_StartWeek`, set before the first asset call. `EndWeek` stays at Zorro's
   default (Friday 20:00 New York; the last real quote is Friday ~17:00, run 1 cause 1).
   C1 gains `StartWeek = 71700` (INFO row), checked by the comparator.
2. **Common last day:** every scenario's tail is extended so all 64 end on 2024-03-26
   (`tools/make_scenarios.py`; the generator refuses to write if last days differ). Checked: the
   regenerated expected trades differ from run 1's only in the exits of `end` halves; 40 real
   `end` halves, as before.
3. Run 2 uses `tpe_CompileOnly = 0` unchanged in purpose.

Prediction for run 2 (unchanged from the original, now with both causes removed): C0 met; 60/60 real
scenarios PASS; 4 DOC rows (A3HF, A3HFM); 40 ENTRY_ONLY rows; 4/4 controls detected; every Monday
fill at the Monday open (first record, Sunday 18:00 New York on the synthetic path); last BAR row
2024-03-26 for every asset. Runs so far: 1 (FAIL, setup). Variants unchanged (5 configurations).

## Run 2 — 2026-11-23 09:49 — PASS, all predictions met

Commit `b3f31f9` (Amendment 1). Log `C:/Zorro/Data/TPL_Equivalence_log_run2.csv` (sha256
`d6492c5ce83aa9ff…`); checker output `analysis/template/equivalence/results/TPL_Equivalence_run2.csv`.
Zorro: `Test: TPL_Equivalence (TICKS) 2024`, `Trades 116` (120 expected halves minus the 4 the MF
controls lose), no Error line.

| # | Result (b) |
|---|---|
| C0 | No Error line; no ERROR / ASSETFAIL row |
| C1 | 64 INFO rows: Fill 3, Hedge 2, TICKS 1, BarOffset 1020, StartWeek 71700, all states rows loaded; last BAR row 2024-03-26 on all 64 assets |
| C2-C4, C6 | **60/60 real scenarios PASS**; 40 ENTRY_ONLY rows (predicted 40); counts equal the engine's; no `other` reason; nothing open after the last bar. Largest price difference on any compared fill 1.4e-8 (A3, half 1 exit), tolerance 1e-5 |
| C5 | 4 DOC rows as predicted: A3HF tp1 1.0100 then stop 0.9850; A3HFM tp1 0.9900 then stop 1.0150 |
| C7 | 4/4 controls detected: A6_CM3 / A6M_CM3 2 FAIL rows each (runner reason `be` for `be_adverse`, M-D3 count 0 for 1); R1_CMF / R1M_CMF 2 halves for 4 (the reversal's short never entered), as predicted |

Observations:
- (b) Monday-open fills now on the first record of the week (e.g. A6 runner "Sell 1@0.997500 at
  22:00:00 Sun" UTC = Sunday 18:00 New York): M-D6 confirmed.
- (b) **Exits sent at a close (exitTrade) fill at the next bar's open under Fill 3** (ZORRO_TRADE_MECHANICS
  §12 R1, open until now): C1, C2, R1, A6, E1, E4a and mirrors all matched the engine's next-open exits.
- (b) **Stop moved beyond the price at a close (probe P2, second half):** control A6_CM3 set the runner's
  stop to 1.0000 at the 0.9980 close; Zorro did not close the trade at that close but at the next tick,
  the next open 0.9975 ("Stop 1@0.997500", A6_CM3 log), the same price as the M-D3 exit at the next open.
  M-D3's explicit exit therefore changes the label and the count, not the fill (on this path).

**Verdict: S4 engine equivalence PASS** (2 runs; run 1 FAIL from setup, recorded above).
Variants: 5 template configurations, 2 planted mutants on 4 assets.

## Amendment 2 — 2026-11-23 (regression run 3, after P5; before the run)

**Why:** the template changed after run 2 (commits after `b3f31f9`, P5): `NNFX_Template.h` gained
`nx_costs_apply()` (spread level, T7) with two per-asset arrays, and every HALF row gained 5 cost
columns (TradeProfit, TradeRoll, TradeCommission, TradeSpread, TradeUnits). `TPL_Equivalence.c`
does not call `nx_costs_apply()` and still sets `Spread = 0`, so (c) no trade should change.

**Inputs checked unchanged (b, 2026-11-23):** `make_scenarios.py ... ALL` regenerated into a scratch
folder: all 128 `History/SYN_*` files (`.t6` and states) byte-identical to those in `C:/Zorro/History`,
and the expected folder identical to `analysis/template/equivalence/expected/`. The regenerated header
differs from the committed `TPL_Equivalence_Scenarios.h` only by two added functions
(`tple_stem`, `tple_costed`) that this script does not call; the committed header is kept as is.

**Run:** script unchanged except the `tpe_CompileOnly` comment; criteria C0-C7 and tolerance unchanged.
Log copied to `C:/Zorro/Data/TPL_Equivalence_log_run3.csv`; checker output to
`analysis/template/equivalence/results/TPL_Equivalence_run3.csv`.

**Prediction (c), written before the click:**
1. Verdict PASS, identical to run 2: C0 met; 64 INFO rows as in run 2; 60/60 real scenarios PASS;
   40 ENTRY_ONLY rows; 4 DOC rows; 4/4 controls detected with the same FAIL rows (A6_CM3 / A6M_CM3
   2 each; R1_CMF / R1M_CMF 1 each, 2 halves for 4); Zorro `Trades 116`, no Error line; largest
   compared price difference 1.4e-8.
2. **Checker output byte-identical to run 2's** (`TPL_Equivalence_run3.csv` = `TPL_Equivalence_run2.csv`):
   the checker reads only the first 12 HALF columns.
3. **Log identical to run 2's except the 5 new HALF columns:** run 3's log with HALF columns 15-19
   removed is byte-identical to `TPL_Equivalence_log_run2.csv`. Check:
   `python -c "import csv,sys; a=[r[:14] if r and r[0]=='HALF' else r for r in csv.reader(open(sys.argv[1]))]; b=list(csv.reader(open(sys.argv[2]))); print('IDENTICAL' if a==b else 'DIFF')" C:/Zorro/Data/TPL_Equivalence_log_run3.csv C:/Zorro/Data/TPL_Equivalence_log_run2.csv`
4. Observations only (not part of the verdict): on every HALF row TradeRoll = 0, TradeCommission = 0,
   TradeSpread = 0, TradeUnits = 1000 (LotAmount 1000, 1 lot); TradeProfit = dir x (exit − entry) x 1000
   (PIPCost 0.1 per 0.0001) within 1e-5 (TradeProfit is a float, gotchas 9d.11).

Runs of S4 so far: 2 (run 1 FAIL setup, run 2 PASS). This is run 3, a regression run. Variants unchanged
(5 configurations, 2 mutants on 4 assets).


## Run 3 — 2026-11-23 15:08 — PASS, all predictions met (regression after P5)

Commit `3b3d3dd` (Amendment 2). Log `C:/Zorro/Data/TPL_Equivalence_log_run3.csv` (sha256
`51407d9b0dfda1f4…`); checker output `analysis/template/equivalence/results/TPL_Equivalence_run3.csv`.
Zorro: `Test: TPL_Equivalence (TICKS) 2024`, `Trades 116`, no Error line.

| # | Prediction | Result (b) |
|---|---|---|
| 1 | Verdict as run 2 | RUN PASS: 60/60 real scenarios; 40 ENTRY_ONLY; 4 DOC; controls A6_CM3 / A6M_CM3 2 FAIL rows each, R1_CMF / R1M_CMF 1 each; 0 ERROR / ASSETFAIL rows; Trades 116 |
| 2 | Checker output byte-identical to run 2 | Byte-identical (`cmp`) |
| 3 | Log identical to run 2 without HALF columns 15-19 | IDENTICAL; 116 HALF rows, all with 19 columns |
| 4 | Cost columns (observation) | On all 116 halves: TradeRoll 0, TradeCommission 0, TradeSpread 0, TradeUnits 1000; largest TradeProfit − dir x (exit − entry) x 1000 = 4.8e-7 (tolerance 1e-5) |

(b) The Zorro summary line (Loss -153$, Capital 4671$) is the synthetic batch's P&L and has no meaning.

**Verdict: S4 still PASS after the P5 template changes.** Runs of S4: 3 (run 1 FAIL setup, run 2 PASS,
run 3 regression PASS). Variants unchanged (5 configurations, 2 mutants on 4 assets).

## Amendment 3 — 2026-11-23 (regression run 4, after P6; before the run)

**Why:** the template changed after run 3 (commit `1cc7f3e`, P6): `nx_template_init()` sets `Capital = 100000`,
and the entry block calls `nx_size()` only when `nx_FixedLots <= 0`. This batch sets `nx_FixedLots = 1`, so
(c) sizing is bypassed and no logged value changes (`Capital` affects Equity and margin-call simulation only;
1 lot per half uses < 0.1% of the margin). The generator edits change no input: all History files and expected
folders regenerate byte-identical (checked 2026-11-23, 160 files).

**Prediction (c):** `C:/Zorro/Data/TPL_Equivalence_run4.csv` **byte-identical** to `TPL_Equivalence_run3.csv` (sha256 `51407d9b0dfda1f4…`);
hence the checker output is identical and the verdict PASS. Zorro `Trades 116`, no Error line. Runs so far: 3; this is
run 4, a regression run. Variants unchanged.

## Run 4 — 2026-11-23 16:02 — PASS, prediction met (regression after P6)

Commit `2b22994` (Amendment 3). Log `C:/Zorro/Data/TPL_Equivalence_log_run4.csv` **byte-identical to run 3**
(sha256 `51407d9b0dfda1f4…`, `cmp`); checker output identical to run 3's: RUN PASS, 60/60, 4/4 controls,
4 DOC, 40 ENTRY_ONLY. Zorro: `Trades 116`, no Error line. (b) The window's summary `Capital` figure changed
(4671$ in run 3, 4678$ here): (c) a Zorro statistic affected by `Capital = 100000`; it is not in the log and
has no meaning for this batch.

**Verdict: S4 still PASS after P6.** Runs of S4: 4 (run 1 FAIL setup; runs 2-4 PASS).

## Amendment 4 — 2026-11-23 (regression run 5, R1 template changes; before the run)

**Why:** branch `eurusd-r1` changed the template: `nx_FillUnrounded = 1` sets TradeMode `TR_FRC` in
`nx_template_init()` (R-D5: stops, limits and fills no longer rounded to the PIP; (a) `include/trading.h:276`
"don't round to 1 PIP"), and the slot values `nx_s*` moved from `NNFX_Slots.h` to `NNFX_Config.h` (declaration
only). Inputs unchanged (generator output byte-identical, checked 2026-11-23).

**Prediction (c):** same verdict and counts as run 4 (RUN PASS, 60/60, 4/4 controls, 4 DOC, 40 ENTRY_ONLY, Trades 116). Logs need **not** be byte-identical: a level
that is not on the pip grid (stop = fill - 1.5 x float32 ATR) now fills unrounded. Recorded as an observation (b):
the largest change of any logged fill price vs run 4; > 0 shows that Zorro rounded before (R-D5), 0 that it did
not on these paths. Every price change must stay within the existing tolerances. Runs so far: 4; this is run 5.


## Run 5 — 2026-11-23 19:45 — PASS, prediction met (regression after the R1 template changes)

Commit `12aa643` (Amendment 4). Log `C:/Zorro/Data/TPL_Equivalence_log_run5.csv` **byte-identical to run 4** (sha256
`51407d9b0dfda1f4…`); checker: RUN PASS, 60/60, 4/4 controls, 4 DOC, 40 ENTRY_ONLY. Zorro: `Trades 116`, no Error line.
(b) Largest change of any logged fill price vs run 4: **0** (0 of 232 fills changed). With TR_FRC on, fills at levels off the
pip grid (stop = fill - 1.5 x float32 ATR) are identical to the run without it: on these paths Zorro did not round fills before
(R-D5; (c) the rounding in trademode.htm may apply to orders sent to a broker, not to backtest fills; not probed further).

**Verdict: S4 still PASS after R1.** Runs of S4: 5.

Correction to the run 5 note (after TPL_Costs run 5, 2026-11-23): Zorro **did** round fills before TR_FRC, to the 0.1-pip grid
(1e-5); S4's fills were already on that grid (paths in 1e-5 steps), hence no change here. The (c) remark about broker orders is
withdrawn.

## Amendment 5 — 2026-11-24 (regression run 6, PERF1 logging change; before the run)

**Why:** PERF1 Amendment 1 (A1.1), commit `d49c581`: logging-only template change. Every refused signal writes a
`REFUSED,asset,ymd,reason,kind` row (bridge-too-far in the baseline-cross skip branch; lots / risk / margin after the
existing ERROR row in `nx_size`); `nx_size` gains a kind argument (plumbing only). No condition, order, size or level
changed (diff read in the planning chat, 2026-11-24). (b) This checker ignores row types it does not read, so REFUSED
rows cannot change its verdict. Compare in Git Bash:
`diff <(grep -v '^REFUSED,' NEW | tr -d '\r') <(tr -d '\r' < OLD) && echo IDENTICAL`.

**Prediction (c):** same verdict and counts as run 5 (RUN PASS, 60/60, 4/4 controls, 4 DOC, 40 ENTRY_ONLY); Zorro
`Trades 116`, no Error line. Log `TPL_Equivalence_log_run6.csv` with REFUSED rows removed is identical to run 5's log
(sha256 `51407d9b0dfda1f4…`) up to line endings. REFUSED rows: reason `bridge-too-far`, kind `standard` only; 0 lots / risk /
margin rows (`nx_FixedLots` > 0: `nx_size` is never called). Their count is recorded as an observation (b), not predicted.
Runs so far: 5; this is run 6.

## Run 6 — 2026-11-24 16:23 — PASS, prediction met (regression after the PERF1 logging change)

Commit `94438e0` (Amendment 5). Log `C:/Zorro/Data/TPL_Equivalence_log_run6.csv` (sha256 `e3e9788d9166db4a…`); with the
REFUSED rows removed, identical to run 5's log (line endings normalised). Checker: RUN PASS, 60/60, 4/4 controls (A6_CM3,
A6M_CM3 2 FAIL rows each; R1_CMF, R1M_CMF 1 each), 4 DOC, 40 ENTRY_ONLY, 0 error rows. Zorro: `Trades 116`, no Error line.
(b) REFUSED rows: 2, both `bridge-too-far,standard` (observation, not predicted).

**Verdict: S4 still PASS after the PERF1 logging change.** Runs of S4: 6.
