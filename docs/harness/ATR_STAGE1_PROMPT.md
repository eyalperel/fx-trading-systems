# ATR stage 1 — D7 tooling extensions + reference models + one spec draft (MT4 ATR(14))

Planning chat, 2026-11-21. Decisions accepted by the user: review `docs/harness/ATR_SOURCE_REVIEW.md` (`e11270a`, AT-1..AT-7) and the
spec-level decisions **S1..S8** below (user, 2026-11-21: "accept"). Build mode, speed over polish; the validation gate is unchanged
(CLAUDE.md). Labels: (a) source states, (b) measured / computed, (c) inference. Run on **Opus, effort High**.

**Git:** branch `harness-atr` (at `e11270a`). `docs/harness/ATR_STAGE1_NUMBERS.py`, its output `ATR_STAGE1_NUMBERS_output.txt` and this
brief are uncommitted in the working tree: commit them with the tooling. Do NOT commit. At the end print the `git add` / `git commit` commands
you suggest (one commit for tooling + tests + numbers + this brief, one for the spec draft), with `git diff --stat` FIRST (Windows line endings:
if a file shows whole-file churn, stop and report), and STOP. No `.c` file written, no Zorro run.

Read first: the review (all of it), `docs/harness/ATR_REVIEW_MODEL.py`, `docs/harness/ATR_STAGE1_NUMBERS.py` (the source of every number
below; run it and diff against `ATR_STAGE1_NUMBERS_output.txt`), HARNESS_DESIGN D7 and "D7 applied to MAMA / FAMA and FRAMA",
`analysis/harness/specs/FRAMA_ArticleFidelity.toml` (structure to follow; bars inputs), gotchas 1.3, 3.1, 9d.1, 9d.6, 9d.8, 9d.9, 9d.10.

**Lessons applied (MAF session + user, 2026-11-21):**
1. A back-check of a shared-state control takes the call order **from the generated script**, never from the input list. The NCS numbers below
   come from two ASSUMED orders; the tooling recomputes them in the actual order and the report states that order.
2. Conditioning is classified **per (input, column) over ALL rows with several perturbation draws** (5 here), never one.
3. Every `series()` in harness-run code has an **explicit length**, larger than the largest index read (gotchas 9d.10).
4. `git diff --stat` in Git Bash before committing (Windows line endings).
Plus from FSH / MAF: the back-check replays IMP and must_fail over ALL exported inputs (base, band, copies), so the spec lists every input IMP
runs on; callers use their own local prefix.

## Source (a) — verbatim in the review §2

MetaQuotes `ATR.mq4` (installed copy, sha256 prefixes `134da529e0382b89` / `c5c680c466e7d87f`, code identical): `InpAtrPeriod = 14`;
`TR[0] = 0`, `ATR[0] = 0`; `TR[i] = max(high[i], close[i-1]) - min(low[i], close[i-1])`; `ATR[1..P] = 0`, then `ATR[P] = sum(TR[1..P]) / P`;
from `i = P + 1`: `ATR[i] = ATR[i-1] + (TR[i] - TR[i-P]) / P`. Per indicator instance: row 0 of the instance = its first call.
D1: no literal in the source except the integer period; no `PI`, no trig. Nothing to replace. No NCL.

## Decisions S1..S8 (user, 2026-11-21)

- **S1 Family: D7 applied** (no D8), with three tooling additions: a column role `scale` for equivariance (copy = |k| x col; the offset has no
  effect; ATR and TR are both `scale` columns), a `window_hull` bound (min TR[r-P+1..r] <= ATR[r] <= max TR[r-P+1..r], rows >= P), and the
  `rampdn` input (exists since LRS) in the bars family.
- **S2 File:** `indicators/nnfx/ATR.c` (new folder; it is not an Ehlers indicator). Include path from `strategies/tests/`:
  `../../indicators/nnfx/ATR.c`. Function names `ATRMT4Core` / `ATRMT4` (Zorro has built-in `ATR()` overloads, manual ta.htm: do NOT name
  ours `ATR`; grep `C:/Zorro/include` for `ATRMT4` and report). Prefixes `at_` (core), `atw_` (wrapper), `ats_` (NCS body): repo grep found
  none (planning chat, `\b(at|atw|ats)_`); repeat it and add them to gotchas 1.3 in stage 2.
- **S3 Inputs:** point bars (H = L = C = x): flat, ramp, rampdn, s5, s10, s20, s40, s100. Band bars (H = x + h, L = x - h, C = x), suffix B, on
  the same 8, **h = 2/10000** built from integers (not FRAMA's 0.002: with h above every per-bar move TR is constant and the averaging is
  blind, review §3 item 4). Equivariance copies of s40B: `sc` = 10 x - 9.9 (H / L mapped the same way: h -> 10 h), `of` = x + 1.1.
  16 inputs + 2 copies. Level 1.1, amplitude 0.01, slope 1e-4, 3000 rows.
- **S4 Variants:** `AT14` (Length 14, the template), `AT20` (Length 20).
- **S5 Controls (vs AT14):** NCW (Length 15), NC0 (first window TR[0..P-1] at row P), NCWi (Wilder averaging, Zorro `ATR()` form), NCR
  (TR = H - L), NCZ (start-up: rows 1..P-1 output the mean of the TRs so far instead of 0), NCS (the correct body with the running ATR value in
  ONE file static shared by every call; two instances per input). Bodies in §Controls.
- **S6 Tolerances:** below (floor measured).
- **S7 Conditioning:** D7 rule 3 classifier, all rows, 5 draws, seed 20261121, per (input, column).
- **S8 Real-data cross-check (AT-5):** a separate small script in stage 2, pre-registered in the spec now (§Cross-check).

## Planning-chat numbers to reproduce (b)

Run `python docs/harness/ATR_STAGE1_NUMBERS.py` and reproduce with `reference.py`. Your reference model mirrors the corrected code's
operation order (below); the planning-chat script follows `ATR.mq4`'s. Report a difference as a finding only if it exceeds 10x the item-1 value
for that (input, column) or 1e-15, whichever is larger; effects within 1% relative.

1. **Conditioning** (perturbation C(1 + 2^-52 u), u in {-1, 0, 1} drawn per row, 5 draws, H / L rebuilt from the perturbed C with the same
   offsets; bound = trace tolerance / 10 = 1e-13): **every (input, column) checked**, none INFO. Max AT14: tr 4.441e-16, atr 3.965e-16
   (flat); AT20: tr 4.441e-16, atr 3.442e-16. The tooling recomputes this (same seed and draw order); a mismatch in classification is a pre-run STOP.
2. **Known answers**, rows >= P, both variants: flat 0 (diff 0); flatB, rampB, rampdnB 2h = 4e-4 (<= 4.407e-17); ramp, rampdn slope 1e-4
   (<= 1.118e-17). Rows 0..P-1 are exactly 0 on every input. Start-up s20: AT14 ATR[14] = 0.002107897511639391, AT20 ATR[20] =
   0.0020000000000000018.
3. **Bounds** (all inputs and copies): ATR >= 0 (min 0), TR - (H - L) >= 0 (min 0), window hull violation 0.
4. **Equivariance** s40B, all rows: AT14 sc tr 1.998e-15, atr 4.701e-16; of tr 4.441e-16, atr 6.332e-17. AT20 sc atr 4.406e-16, of atr 4.510e-17.
5. **IMP estimate** (model fed the %.15f-rounded H, L, C vs exact), every input incl. copies: AT14 tr 8.882e-16, atr 3.782e-16; AT20 tr
   8.882e-16, atr 3.652e-16. Floor x 10 = 8.9e-15 <= 1e-12.
6. **Control effects** vs AT14, max |diff| over all rows, atr column (full table in the output file):
   - NCW: 7.673e-03 (s5B); blind on flat only; rows 14..2999.
   - NC0: 2.738e-04 (s10B); blind on flat only; rows 14..2999 (persistent: the running update never restores the dropped TR[P]).
   - NCWi: 1.870e-04 (s40); blind on flat, flatB, ramp, rampB, rampdn, rampdnB (constant TR: Wilder = SMA); rows 15..2999.
   - NCR: atr 7.892e-03 (s5), tr up to 1.176e-02; blind on flat, flatB, rampB, rampdnB (C[1] inside the bar); rows 14..2999.
   - NCZ: 9.711e-03 (s5B); blind on flat only; rows 1..13 only (start-up: only a trace from row 1 sees it).
   - NCS: assumed order input-major (per bar: each input, instance 1 then 2): min over (instance, input) 3.265e-03; instance-major: 2.581e-03.
     Recompute in the generated order; if any (instance, input) is < 10x its tolerance, report it (expected: none).

## Tolerances (pre-registered; check each against D2 rule 3)

- trace **1e-12** (tr, atr), from row 1. Floor (item 5) 8.9e-16, x 10 = 8.9e-15 <= 1e-12; smallest required control effect (NCWi 1.870e-04)
  / 10 = 1.9e-5 >= 1e-12. If a measured floor x 10 exceeds a tolerance, STOP and report.
- bound: `atr >= 0` absolute 1e-15; `tr >= H - L` absolute 1e-15; `window_hull` relative allowance 1e-12 (D6 rule) with absolute 1e-15.
- equivariance (scale role) **1e-12**, rows >= 1 (no start-up exception: ATR is linear in TR and TR is scale-equivariant).
- known answers (flat / flat_band / ramp / ramp_band as values) **1e-12**. imp 1e-12. x 1e-12.

## Tooling (extensions only)

- **Bars inputs:** reuse FRAMA's family; `h` per spec (2/10000); `rampdn` and `rampdnB` added to the bars list. `series_len` >= Length + 1 for
  the CALLER's H / L / C series (the core reads Close[1] only, but NCW reads at_TR[15]: the core's own TR series has length Length + 2, below).
- **Two-column calls:** `ATRMT4Core` -> `atr` (= return), `tr` (out-parameter, local-scalar pattern `62b4e97`).
- **Column role `scale`** for equivariance: copy column = |k| x base column, offset ignored. Unit tests: fires on a 1e-9 scale error, ignores the
  offset, rejects a `level` role on a `scale` column.
- **Kind `window_hull`** (per spec: column atr against the TR window of length P, rows >= P). Fires on one row out by 1e-12 relative.
- **Kind `known_value`** (or reuse flat / ramp_exact if they generalise): column atr equals a pre-registered constant on rows >= P.
- **Reference models** (restricted grammar, no eval): `atr_mt4(P, tr_kind = "mt4" | "hl", avg = "sma" | "wilder", first = "mt4" |
  "with_tr0", startup = "mt4" | "tr")` (defaults = the corrected code); `atr_shared(P)` = NCS: the correct body with ONE file static
  `ats_prev` shared by every call, replayed in the generator's ACTUAL call order (RFX / LRS / FSH / MAF shared-state replay).
- **Conditioning classifier:** reuse MAF's (`checker.conditioning_table`), 5 draws, seed 20261121; output into the pre-run record, compared with
  the spec's list.
- `[zorro].include = ["../../indicators/nnfx/ATR.c"]` (written in stage 2; lint may report it missing: say so, do not create it).
  `[lint].no_static` on `ATR.c` (must fire on the NCS body: 1 hit `ats_prev`).
- Existing specs (H1, SS2F, SS3F, HPF, RFF, USE, RFX, MST, LRSI, FSH, MAMA, FRAMA) must regenerate BYTE-IDENTICAL scripts; checker outputs
  unchanged.

## Corrected code (pre-registered; `.c` written in stage 2, AFTER the spec is committed)

```c
// ATR.c — Average True Range, MetaTrader 4 definition (NNFX "ATR 14, default settings").
// Source: MetaQuotes ATR.mq4 (installed copy; docs/harness/ATR_SOURCE_REVIEW.md §2).
// Zorro's own ATR() is Wilder's recursive form and is NOT this indicator; ATRS() is.
var ATRMT4Core(vars High, vars Low, vars Close, int Length, var* pTR)
{
    vars at_n  = series(0, 2);            // per-instance CurrentBar (9d.9); row r = at_n[0] - 1
    vars at_TR = series(0, Length + 2);   // explicit length (9d.10): reads at_TR[Length]
    vars at_A  = series(0, 2);
    var at_th = 0;
    var at_tl = 0;
    var at_s  = 0;
    int at_i;
    at_n[0] = at_n[1] + 1;
    at_TR[0] = 0;                         // row 0: no previous close (ATR.mq4 line 76)
    at_A[0] = 0;                          // rows 0..Length-1: 0 (lines 77, 85)
    if(at_n[0] > 1) {
        at_th = High[0];
        if(Close[1] > at_th) at_th = Close[1];
        at_tl = Low[0];
        if(Close[1] < at_tl) at_tl = Close[1];
        at_TR[0] = at_th - at_tl;         // line 80 / 98
    }
    if(at_n[0] == Length + 1) {           // row Length: mean of TR[1..Length] (lines 83-90)
        for(at_i = 0; at_i < Length; at_i++)
            at_s = at_s + at_TR[at_i];
        at_A[0] = at_s/Length;
    }
    if(at_n[0] > Length + 1)              // line 99, running form kept (AT-4)
        at_A[0] = at_A[1] + (at_TR[0] - at_TR[Length])/Length;
    *pTR = at_TR[0];
    return at_A[0];
}

var ATRMT4(vars High, vars Low, vars Close, int Length)
{
    var atw_1;
    return ATRMT4Core(High, Low, Close, Length, &atw_1);
}
```
Notes: every `series()` unconditional and first (3.1); no `static` (lint); no literal other than small integers; expressions start with a
variable (9d.8); `Close[1]` on the instance's first call is never read (the `at_n[0] > 1` branch). (c) Check in stage 2 that a `series()` whose
length depends on a parameter compiles and allocates per call (it is constant per variant here); if Light-C refuses `series(0, Length + 2)`,
STOP and report (fallback: a fixed upper bound, e.g. 64, with a `Length <= 62` guard). The sum loop reads `at_TR[0..Length-1]` = rows
Length..1: the source's TR[1..Length]. Callers: none today (grep `ATRMT4`); the template (step 4) will pass `series(priceHigh())`,
`series(priceLow())`, `series(priceClose())`.

## Controls (inline bodies, own prefixes, variable-first)

- `NCW`: the corrected body called with Length 15 (param variant; model `atr_mt4(15)`), compared against the AT14 model.
- `NC0`: first window `for(i = 1; i <= Length; i++) s += TR[i]` at row Length (i.e. TR rows Length-1..0, including row 0's TR = 0); model
  `first = "with_tr0"`.
- `NCWi`: `A[0] = (A[1]*(Length - 1) + TR[0])/Length` from row Length + 1; model `avg = "wilder"`.
- `NCR`: `TR[0] = High[0] - Low[0]` (no previous close), row 0 still 0; model `tr_kind = "hl"`.
- `NCZ`: rows 1..Length-1 output the mean of TR[1..row]; model `startup = "tr"`.
- `NCS`: the corrected body with `at_A` replaced by `static var ats_prev` (read as the previous value, written at the end), counter and TR
  per instance; two instances per input (columns atr only); model `atr_shared`. Restart Zorro before a rerun (the static is reset only by a
  recompile, gotchas 9b.1).

## Spec draft `analysis/harness/specs/ATR_MT4Fidelity.toml` (id_prefix `ATR`)

Same structure as `FRAMA_ArticleFidelity.toml` (incl. [source] with the ATR.mq4 hashes, [corrected_code], [floor], [detect], [imp],
[conditioning], [observations], pass condition, pre-run i-iv, the restart-Zorro rule). Every number stored at full precision.
Real variants (`ATRMT4Core`, model `atr_mt4`): `AT14`, `AT20`. No INFO variant.
**Pass condition (real checks per variant):** trace 2 columns x 16 inputs = 32 (from row 1, start-up included); bound 3 (atr >= 0, tr >= H - L,
window_hull; every input and copy); known answers 6 (flat, flatB, ramp, rampdn, rampB, rampdnB); equivariance s40B, copies sc and of,
columns tr and atr = 4. **45 per variant, 90 total** expected: state the exact number and explain any difference.
State what is checked by code review only: the `Close[1]` read on the first call (unreachable by construction); the running vs direct form
(AT-4, measured <= 5.6e-17 in the review).
**IMP** must_pass: AT14, AT20, NCW, NC0, NCWi, NCR, NCZ with their models, NCS with `atr_shared`, on every input (point, band, sc, of);
must_fail: AT14 replayed with the NCWi model; NCS replayed with the AT14 model.
**[detect.required]:** each control on every kind where its effect is >= 10x tolerance, per the item-6 blind lists (e.g. NCZ on trace only, from
row 1; NCWi on sine traces only). `[detect.info_only]` for kinds that cannot discriminate (as FRAMA NCT bound). If any control has NO kind >=
10x, STOP.

### Cross-check (S8, AT-5; pre-registered here, script in stage 2)

`strategies/tests/XCHK_ATRMT4_vs_ATRS.c`: EUR/USD D1, Zorro history, `LookBack` >= 100; per bar, unconditionally: `ATRMT4(series(priceHigh(),
16), series(priceLow(), 16), series(priceClose(), 16), 14)` and `ATRS(14)`; export date, both values, |diff|, |diff| / ATRS.
**Criterion:** on rows >= 100 of the export, max relative |diff| <= 1e-9. Reason (c): both read the same stored prices; `ATRS`'s internal
precision and start-up are not documented (manual), so the threshold is not the 1e-12 trace tolerance; rows < 100 excluded for the
undocumented start-up. A miss is a finding to explain (e.g. a different TR at a weekend gap or a float accumulation), reported before the
ATR spec's result is accepted; it does not change the synthetic verdict. Variants counted: 1.

## Done when

- `bash analysis/harness/run_tests.sh` all PASS (report TOTAL before / after; 853 at `ddf9776`) incl. new tests for: `rampdn` bars inputs,
  two-column calls, the `scale` role, `window_hull`, the known-value kind, `atr_mt4` vs items 2-5, every control model vs item 6 (within 1%),
  `atr_shared` with a call order taken from a generated script, the no-static lint on the NCS body (1 hit), byte-identical regeneration of the
  12 existing specs.
- `python analysis/harness/generator.py <spec> --lint-only` clean (except the stage-2 include, reported).
- Report as `docs/harness/ATR_STAGE1_REPORT.md`: real-check counts, raw column counts, items 1-6 reproduced (diff vs the values above), the
  conditioning table, floors and the tolerance window per quantity, every control's effects and [detect.required], the NCS per (instance,
  input) results with the generated call order stated, IMP fire-test values at full precision (all inputs), the `ATRMT4` grep of Zorro's
  include folder, the prefix grep, anything that did not fit this prompt. Then STOP (no commit, no `.c` edit, no generated script run).
