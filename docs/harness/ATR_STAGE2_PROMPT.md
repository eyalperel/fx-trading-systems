# ATR stage 2 — ATR.c, series-length probe, cross-check script, pre-run records (Amendment 1), generated script

Planning chat, 2026-11-22. Branch `harness-atr`. Stage 1 (tooling + spec, pre-registered) at `2957476` (tooling) and `bd62493` (spec
`analysis/harness/specs/ATR_MT4Fidelity.toml`, tests, report `docs/harness/ATR_STAGE1_REPORT.md`). Review: `docs/harness/ATR_SOURCE_REVIEW.md`
(`e11270a`). The planning chat reviewed stage 1 before commit and accepted report §10 items 1-4 (user, 2026-11-21): window_hull fires at 1e-12
ABSOLUTE; the extra opt-in tooling (known_value, range_bound, absolute bound allowances, window, bar_args, band_flat); NCS / NCS2 `bound` and
`window_hull` REQUIRED (planning-chat replay in the generated order reproduced all 32 NCS values, min 2.570e-3, and atr down to -1.747e-3);
the two-commit split. User's Git Bash: 926/926 at `bd62493`. Labels: (a) source states, (b) measured / computed, (c) inference.
Run on **Sonnet, effort Medium**.

**Git:** do NOT commit. At the end print `git diff --stat` FIRST (Windows line endings: whole-file churn = stop and report), then ONE suggested
commit command covering everything (so the commit is green), and STOP. Do NOT click / run Zorro: the user clicks, in the order of §8.

Lessons (unchanged from stage 1): call order of a shared-state control from the generated script; conditioning per (input, column), all rows,
5 draws; explicit `series()` lengths in harness-run code (9d.10); `git diff --stat` before committing.

## 1. New `indicators/nnfx/ATR.c` (new folder)

Two functions, bodies = the spec's `[corrected_code]` lines and wrapper lines, VERBATIM: `ATRMT4Core(...)` then `ATRMT4(...)`. Header
(comments only), each statement labelled (a) / (b) / (c):
- Source (a): MetaQuotes `ATR.mq4` (MetaTrader 4, `MQL4/Indicators`; installed copies sha256 `134da529e0382b89…` / `c5c680c466e7d87f…`,
  code identical): TR = max(High, Close[1]) - min(Low, Close[1]); ATR = simple Length-bar mean of TR, kept as a running sum; row 0 TR = 0; ATR = 0
  on the instance's rows 0..Length-1; row Length = mean of TR[1..Length]. Default Length 14. This is NNFX's "ATR 14, default settings"
  (`docs/sources/NNFX_Sources.md` A §2.1, B §1.4; VP's charts are MT4) (c: the MT4 identification is the review's inference, §2).
- (a) Not Zorro's `ATR()` (Wilder's recursive form, manual ta.htm); equal in definition to Zorro's `ATRS()` (SMA of TrueRange), which reads the
  asset's own prices and cannot take caller series.
- (b) Behaviour (review §3, spec observations): exact known answers (flat 0; constant-range bars 2h; close-only ramp = slope); a 14- vs 15-bar
  window differs by 2-8% of the ATR level; Wilder vs this differs by up to 2-4% on band sines (0 when TR is constant); the first Length bars are 0,
  so a strategy's LookBack must cover Length + 1 bars (c).
- (a) NNFX use (template, step 4): stop 1.5 x ATR, TP1 1 x ATR, trailing after a close 2 x ATR beyond entry, trail 1.5 x ATR, size = risk /
  (1.5 x ATR), entry only within 1 x ATR of the baseline; the entry bar's ATR is frozen for the trade. Not implemented here.
- Caller requirements: High / Low / Close series of at least 2 values (the core reads Close[1] only); call unconditionally every bar (3.1);
  Length >= 1 integer.
- STATE: no statics; every `series()` call unconditional and first; per-instance state and counter (9d.9); explicit series lengths (9d.10;
  `series(0, Length + 2)`, see §2).
- Verification line: `analysis/harness/specs/ATR_MT4Fidelity.toml` (pre-registered `bd62493`). Not verified until that run passes.

## 2. Pre-run (vi): series-length probe (new; the user clicks it BEFORE the main run)

The spec's pre-run (vi) needs Zorro: does `series(0, Length + 2)` (length = a parameter expression) compile and give each call its own slot?
Write `strategies/tests/PROBE_SeriesExprLen.c` (prefix `pse_`, grep first):
- `#include <default.c>`; StartDate / EndDate / BarPeriod / asset as the generated script (EUR/USD D1 clock); `LookBack = 0`; INITRUN returns
  before any `series()` call (as the generator does).
- A function `var pse_f(int L, var x)` with `vars pse_s = series(0, L + 2); pse_s[0] = x; return pse_s[L + 1];` (reads the oldest slot).
- Per bar, unconditionally, in fixed order: `pse_f(14, bar)` and `pse_f(20, 1000 + bar)` where `bar` is a per-script counter from 1, built as
  an integer; export bar, both returns to `Data/PROBE_SeriesExprLen.csv` (header once; no-overwrite guard; written before `quit()`, 9d.4); quit
  after 60 bars.
- Expected (pre-registered here, (b) by construction): call 1 returns `bar - 15` for bar > 15, call 2 returns `1000 + bar - 21` for bar > 21;
  earlier rows return 0 (the series is created with the value 0 before `x` is written: gotchas 9d.6, `series(0, 2)` starts at 0) — a
  padding value other than 0 is a finding to report, not a failure. Any compile `Error` line, or a return that mixes the two calls, = STOP: switch the corrected code to the spec's fallback
  (fixed `series(0, 64)` with a `Length <= 62` guard) by an amendment, before the main run.
- Write a tiny checker `analysis/harness/tools/check_probe_series_len.py` (or put it in an existing tools module) that reads the CSV and prints
  PASS / FAIL with the first mismatching row; test it on a synthetic good file and a broken one (calls swapped).

## 3. Cross-check script (S8, AT-5; criterion pre-registered in the spec's `[cross_check]`)

`strategies/tests/XCHK_ATRMT4_vs_ATRS.c` (prefix `xa_`, grep first). Include `../../indicators/nnfx/ATR.c`. EUR/USD D1, Zorro history,
StartDate 20100101, EndDate 20240101, `LookBack = 100` (c: >= 100 per the spec). Per bar, BEFORE `if(is(LOOKBACK)) return;` (gotchas 4.1) and
unconditionally: `xa_h = series(priceHigh(), 16)`, `xa_l = series(priceLow(), 16)`, `xa_c = series(priceClose(), 16)`, `xa_m = ATRMT4(xa_h,
xa_l, xa_c, 14)`, `xa_z = ATRS(14)`; export every bar (including lookback bars, flagged) to `Data/XCHK_ATR_raw.csv`: date (`ymd()`), bar index
from 0, lookback flag, ATRMT4, ATRS, |diff|, |diff| / ATRS (0 when ATRS = 0), `%.15e`. Header once, no-overwrite guard. Plus
`analysis/harness/tools/check_xchk_atr.py`: rows >= 100 of the export, max relative |diff| vs 1e-9, prints PASS / FAIL, the max row and the
count of rows > 1e-12 relative (INFO). Test it on synthetic files (pass, fail by one row, ATRS = 0 row). Not run in this stage.

## 4. Gotchas 1.3

Add `at_` (ATRMT4Core), `atw_` (ATRMT4 wrapper), `ats_` (ATR NCS body), `ax0_` / `axi_` / `axr_` / `axz_` (ATR control bodies NC0 / NCWi /
NCR / NCZ, as in the spec), `pse_` (probe), `xa_` (cross-check) to the "Prefixes in use" line and table 1.3, and a change-log row. Nothing else.

## 5. Corrected-code test (new): `analysis/harness/tests/test_atr_corrected_code.py`

As `test_maf_corrected_code.py`:
- `ATR.c` contains the spec's corrected lines and wrapper lines verbatim (whitespace-normalised, comments stripped; body EQUALS);
- no `static`, no global `var`, no decimal literal, no expression starting with a product or quotient of literals, no `PI`, no `priceHigh` /
  `priceLow` / `priceClose` token in `ATR.c`;
- no caller of `ATRMT4` outside `XCHK_ATRMT4_vs_ATRS.c` and the generated script;
- guard fires on temp copies, at least: `static` before `vars at_n`; `at_n[0] == Length + 1` -> `at_n[0] == Length`; `Close[1]` -> `Close[0]`
  (both occurrences); `at_TR[Length]` -> `at_TR[Length - 1]`; `series(0, Length + 2)` -> `series(0, Length)`; the `if(at_n[0] > 1)` guard
  removed; `vars at_A = series(0, 2);` moved inside an `if`.

## 6. Generator

(b) Stage 1 generated the layout in memory (148 calls / bar, 304 columns, 671 lines) and own-model raw files gave 90/90 with every control
detected. **No generator change is expected.** If one is needed it may change the script layout only (never a criterion, tolerance, table,
floor, effect or variant); the 12 existing specs must still regenerate as recorded (`regen_baseline.json`), the full suite must pass, and the
change goes in Amendment 1 as A1.2. If the layout looks unsafe in Light-C, STOP and report.

## 7. Pre-run conditions (spec pass_condition, pre-run i-vii) and Amendment 1

- (i) `test_atr_corrected_code.py` passes; guard-fire evidence per broken copy.
- (ii) new file: no old blob; `ATRMT4` callers as listed; Zorro include grep recorded (stage 1: no hit; repeat).
- (iii) `test_reference_atr_spec.py` passes; largest deviation per section.
- (iv) `generator.py <spec> --lint-only` clean, now with the include resolving and the no-static check passing; record the INFO lines.
- (v) no-static lint: 0 hits on `ATR.c`; seen to fire on the NCS body (1 hit `ats_prev`).
- (vi) **pending the probe** (§2): write `cond_vi = "pending: PROBE_SeriesExprLen.c, run by the user before the main run"`. The planning chat
  records the probe result into `[prerun].cond_vi` after the user's click (a one-line edit, still before the main run and before the commit).
- (vii) conditioning recomputed = the spec's tables (0 INFO).
- Full suite `bash analysis/harness/run_tests.sh` (TOTAL before / after; tracebacks + rerun on any ERROR, CLAUDE.md §8).
- Append `[amendment_1]` to the spec (text above unchanged), same form as FRAMA Amendment 1: date, base_commit `bd62493`, before_run = true,
  A1.1 = pre-run records (+ A1.2 only if §6 needed a change); no criterion / tolerance / table / floor / effect / variant changed; `[prerun]`
  cond_i..cond_vii, tests_before / tests_after, blob hash of the new `ATR.c` (`git hash-object`), sha256 of the generated script, the probe and
  the cross-check script. If ANY criterion would need to change, STOP and report instead.

## 8. Generated script and the click order

`python analysis/harness/generator.py analysis/harness/specs/ATR_MT4Fidelity.toml` -> `strategies/tests/GEN_ATR_MT4.c` (report the actual path);
sha256 into `[prerun]`. Read it and report each item:
- the one include `../../indicators/nnfx/ATR.c`;
- every input series built from integers before any indicator call, each `series(X, 22)`; band H / L with h = 2/10000 and the sc / of copies
  built from integers; no decimal literal in the harness part or the control bodies; every generated static reset at INITRUN;
- every call unconditional, fixed order, variant-major; 148 calls per bar; NCS on its 16 inputs then NCS2 on the same 16, in the order stage 1's
  replay parsed (`flat, s5, s10, s20, s40, s100, ramp, rampdn, flatB, rampB, rampdnB, s5B .. s100B`): if the order differs, STOP and report
  (the spec's NCS values depend on it);
- out-parameters through local scalars, copied before the next call;
- raw file `Data/GEN_ATR_raw.csv` (304 columns), no-overwrite guard; header and rows written before `quit()` (9d.4);
- confirm none of `Data/GEN_ATR_raw.csv`, `Data/PROBE_SeriesExprLen.csv`, `Data/XCHK_ATR_raw.csv` exists yet under `C:/Zorro/Data/`.

Click order for the user (state it in the report; restart Zorro before each): (1) `PROBE_SeriesExprLen` -> planning chat records cond_vi;
(2) commit; (3) planning-chat prediction committed; (4) `GEN_ATR_MT4` (the main run); (5) `XCHK_ATRMT4_vs_ATRS` (the cross-check, read after the
main run).

## Done when

Write `docs/harness/ATR_STAGE2_REPORT.md`: `ATR.c` (full text), the probe and cross-check scripts (full text), both small checkers with their
test evidence, the gotchas diff, test summary with guard-fire evidence, generator change (expected none), pre-run i-vii (vi pending), suite
TOTAL before / after, script names + sha256 and the read-through checks, any deviation from this brief. Then print `git diff --stat` and ONE
commit command and STOP: no commit, no Zorro run.
