# FSH stage 1 — report (tooling, reference models, tests, spec draft)

**Date:** 2026-11-19. **Branch:** `harness-fisher` (HEAD `bdc83da`); the work is not committed yet.
**Brief:** `docs/harness/FISHER_STAGE1_PROMPT.md`. **Source review:** `docs/harness/FISHER_SOURCE_REVIEW.md` (`bdc83da`).
**Spec draft:** `analysis/harness/specs/FSH_ArticleFidelity.toml`. It is not committed yet, so it is not yet pre-registered.

No `.c` file was edited, Zorro was not run, and no generated script was written (`--lint-only` only).
Labels: (a) source states, (b) measured here, (c) inference.

## 1. Outcome

- **No STOP condition fired.**
  - Trace floor ×10 = 1.064e-10 ≤ 1e-9.
  - Every control has at least one kind at 10× or more.
  - NCS differs from the model on rows ≥ W on every input, flat included.
  - (c) No pre-registered line raises a Light-C concern: no decimal literal, no `PI`, no `Period`, no `static`, both `series()` calls first, and every expression starts with a variable (all asserted).
- **Tests.** `bash analysis/harness/run_tests.sh` gives **TOTAL 719  PASS 719  FAIL 0  ERROR 0  SKIP 0**. That is 657 before plus 62 new.
  - The "before" count is the brief's 657 at `f3f85ef`. My run after the tooling edits, before the new tests, was also 657/657.
  - I also tried a `git archive bdc83da` export as a baseline. It is not comparable: 37 FAIL, 6 SKIP, because it has no `.git` and none of the gitignored raw copies.
  - One run only, since nothing failed.
  - The intermittent `test_checker_amend1.test_cli` MemoryError did not occur.
- **Byte-identical.** All 9 existing specs (H1, SS2F, SS3F, HPF, RFF, USE, RFX, MST, LRSI) regenerate byte-identical scripts. The older checker dicts carry no FSH key (asserted).
- **Synthetic perfect run** (every variant equal to its own model): VERDICT PASS.
  - 56/56 real checks pass.
  - All 7 controls are detected on every required kind.
  - IMP: 12/12 rows pass.
  - Floor guard: 10/10 rows pass.

## 2. Tooling (all opt-in)

| Brief item | Where | Tests |
|---|---|---|
| Five columns per call: `FisherCore(S, Len, &raw, &v1, &rng, &trig)` returns `out` | `OUTPUT_NAMES` += raw / v1 / rng / trig; the existing local-scalar call path (no generator code change) | `test_generator_fsh` 04, 05 (84 five-output calls, copies right after each call; header / data / slots = checker order) |
| No linear stage (F-7) | **new `[checks].linear_stage = false`**. No `linear_output`; the flat / gain / lag / phase / resid tolerances and table keys are refused if present; tables carry `article` + `source` only. Checker: `linear_list` → [], no gain / lag floor rows, no `O_PEAK` | `test_generator_fsh` refusals 01 |
| Trace on several outputs, per-output gates on the MODEL | `[checks].trace_outputs = {raw = ["range"], v1 = ["range","clamp"], out = ["range","clamp"]}`, `[checks].clamp_gate`; checker `osc_mask`, `_trace_rows_multi`; ids `trace-<output>-T<t>`; gated rows counted in the input text; every row gated = ERROR | `test_checker_fsh` 01–03: one-output defects fire only their own row. **Clamp gate with gated rows:** g2 = 0.0012 gates 46 rows of FR10 v1 / out at T = 100 (raw: 0); a defect on a gated row is not seen, and with g2 = 1e-6 it is; g2 = 10 → ERROR; a run pushed to .99 cannot gate itself |
| Bounds on raw / v1 / out | `[checks].bounds = {raw = [-1, 1], v1 = [-.999, .999], out = ln(1999)}` (pair = absolute, number = relative allowance); ids `bound-<output>` | Fire at 1 + 2e-12 (raw), −.999 − 2e-12 (v1, low side reported), ln(1999)(1 + 2e-12) (out); pass at 5e-13; NaN → ERROR |
| `ramp_exact` on raw, v1 and out | `[checks].ramp_exact_outputs` (a number or `"model"`); ids `exact-<output>-<input>`; the input text reports max \|out\| | Fire at 1e-11 on each output; rows < W are not read |
| New kind `trigger` | `[checks].trigger = true`, `[tolerances.trigger] = 0`. trig[n] must equal out[n−1] exactly for n ≥ 1 on every base input | Fires on trig = out (no delay), on a 2-row delay and on **one ulp**; NaN → ERROR |
| `flat_zero` on raw, v1 and out | `[checks].flat_zero`, every flat row (n ≥ 0) | Fires on **1e-9** in each of raw / v1 / out, also on a row < W; passes at 5e-13 |
| `fisher_article(L, a, b, thr, cl, k, literals)` | reference: integer pairs, `literals = "exact" \| "float32"`, `simulate_fisher`, `fisher_window`; `article` grammar `fisher_article(L)` only (no eval) | `test_reference_fsh` (18 tests) |
| `fisher_superseded(Ls, index)` | `simulate_fisher_shared`: `ft_Value1` / `ft_Fish` (and the global `ft_Trigger`) shared by all calls in the generator's ACTUAL call order; float32 literals; checker `fisher_shared_slots`, `_imp_fisher` | A single slot equals the float32 per-instance model bit for bit; call order matters; trig = the Fish left by the previous call of ANY slot; the brief's 0.707983 / 2.692527 / 2.695127 reproduced; swapped NCS / NCT columns fail IMP |
| `[lint].no_static` | as LRS | `git show bdc83da:indicators/ehlers/FisherTransform.c` (blob `259954ed…` asserted): **2 hits, `ft_Value1` (line 58), `ft_Fish` (line 69)**; the renamed copy gives `fto_Value1`, `fto_Fish`; 0 hits on the pre-registered lines |
| `[zorro].include` | spec | `--lint-only` exit 3, with exactly the 2 stage-2 items (§8) |

Two more generator changes:
- With a zero tolerance (trigger) the INFO margin ratio is `inf` / 0.
- The floor row ratio is NaN, not a division by zero.

## 3. Counts

| Quantity | Value |
|---|---|
| Variants | **10** = 2 real (FR10, FR20) + 7 controls (NCW, NCC, NCK, NCL, NC32, NCS, NCT) + 1 info (NCB) |
| Real checks | **56** = 2 × 28, exactly as the brief: raw 5 trace + 1 bound + 2 ramp_exact; v1 the same; out 5 trace + 2 invariance + 1 bound + 2 ramp_exact + 1 trigger; 1 flat_zero |
| Checks per variant | real 28; NCB and the 5 inline controls 26 each (no invariance); NCS / NCT 9 each (out only: 5 trace, bound, 2 ramp_exact, flat_zero) |
| IMP rows / floor rows | 12 (10 must_pass + 2 must_fail) / 10 (2 real × trace, invariance, ramp_exact, trigger, flat_zero) |
| Raw columns | **376** = 2 + 18 inputs + 356 outputs. Real: 4 × 8 + 18 = 50 each. Inline: 5 × 8 = 40 each. NCS / NCT: 8 each |
| Calls per bar | **100** (36 `FisherCore`, 48 inline, 16 `FisherTransform_Superseded`) |
| Input series | 18 × `series(X[k], 21)` (§8, item 3) |

## 4. Findings 1–8 vs the brief

`fisher_article` matches `FISHER_REVIEW_MODEL.py` on every row of 8 inputs × 2 Len, for raw / pre / v1 / out / trig / rng: max |diff| **0.0**.

| # | Finding | vs brief |
|---|---|---|
| 1 | raw in [−1, 1]; \|v1\| ≤ .999 with no value in (.99, .999); FR10 T100 max \|Fish\| 7.6004023343329665, FR20 7.60040233312112; jump 1.1535487548879537 | exact. **One correction (b):** on the ramps Fish is EXACTLY ln(1999) = 7.6004023345004 in float64 on rows ≥ W, so the bound is attained in float64, not only approached. The check (≤ with allowance) passes |
| 2 | Range / amplitude margins, 10 values | exact (0.0) |
| 2 | Clamp-distance margins, 10 values | exact (0.0) |
| 2 | Gated rows on FR10 / FR20 | 0 |
| 3 | Fish ranges ±0.943519 / ±2.614129 / ±7.421263; T5 −0.333957..+0.352907; unchanged from rows ≥ 200 | equal to 6 decimals |
| 4 | Ramps, L10 and L20 measured identical: raw = ±1 from row 1 (row 0 = guard); v1 = ±.999 from row 12; Fish within 1e-12 from row 53 | exact |
| 5 | Flat: guard fires on 3000 / 3000 rows; raw = v1 = Fish = 0 | exact |
| 6 | Invariance FR10 2.6565416533230746e-12 / 5.31930055558405e-12; FR20 5.32018873400375e-13 / 1.0578204978628492e-12 | exact |
| 7 | Memory: n = 69 (.67^n), 40 (.5^n). Start-up INFO, A vs an EFS-style start, FR10: max 0.4815 / 1.2615 / 2.4514 / 3.5279 / 4.6964, last row > 1e-12 at 66 / 80 / 80 / 61 / 60 | review values reproduced |
| 7 | Start-up INFO, FR20 | max 0.4815 / 1.3721 / 2.6920 / 4.4290 / 7.5776, last row ≤ 97; W = 700 is 7.2× the largest |
| 8 | Floor | §5 |

## 5. Floors and tolerance windows

The model is the code, so the checker on the own-model raw file gives 0 for trace, ramp_exact, flat_zero, trigger and bound. The floor estimates (b) below are max over raw / v1 / out, rows ≥ W.

**IMP residual.** Model on x printed with `%.15f` (what IMP replays) vs the model on the exact x:
- FR10: **5.234e-12**
- FR20: 1.474e-12
- The brief's (c) "up to ~1e-11" holds.

**Zorro vs model estimate (c).** x moved by −1 / 0 / +1 ulp per row (seed 12345; flat excluded, because Zorro's flat is one double):
- FR10: **1.064e-11**
- FR20: 2.86e-12
- The brief's (c) "rounding level (~5e-16)" holds only if Zorro's `sin()` equals numpy's. This is the worst case if it does not.

| Quantity | Floor (spec) | ×10 | Tolerance | Window | Floor guard (tol / 10) |
|---|---|---|---|---|---|
| trace (raw / v1 / out) | 1.064e-11 | 1.064e-10 | 1e-9 | ok | 1e-10 |
| invariance | 5.319e-12 | 5.3e-11 | 1e-9 | ok | 1e-10 |
| ramp_exact | 0 | 0 | 1e-12 | ok | 1e-13 |
| flat_zero | 0 | 0 | 1e-12 | ok | 1e-13 |
| trigger | 0 | 0 | 0 (exact) | ok | 0 |
| bound | 0 | 0 | 1e-12 (abs) / ln(1999)·1e-12 (rel) | ok | — |
| imp | 5.2e-12 expected | 5.2e-11 | 1e-9 | ok | — |

## 6. Controls

Effects (b) are max |diff| vs the FR10 model over rows ≥ W, at T = 5 / 10 / 20 / 40 / 100. All match the brief's printed values within half a unit of the 7th digit.

| Control | Fish | v1 | raw | Ramps | `[detect.required]` (ratio) |
|---|---|---|---|---|---|
| NCW (.331) | 1.147e-3 / 3.621e-3 / 2.326e-2 / 1.300 / 1.304 | 9.97e-4 … 1.076e-2 | 0 | v1 .999 (no effect) | trace (1.3e9×) |
| NCC (cl = .99) | 0 / 0 / 0 / 2.163 / 2.307 | 0 / 0 / 0 / 9e-3 / 9e-3 | 0 | v1 .99, Fish 5.2933048247244905 | trace (2.3e9×), ramp_exact (2.3e12×) |
| NCK (k = .25) | 0.1765 / 0.4718 / 1.307 / 3.711 / 3.800 | 0 | 0 | Fish 3.8002011672502 | trace (3.8e9×), ramp_exact (3.8e12×) |
| NCL (Len + 1) | 8.2e-14 / 5.2e-14 / 0.1960 / 0.3303 / 1.210 | 6.7e-14 / 3.1e-14 / 0.134 / 0.159 / 0.166 | 2.1e-13 / 9.3e-14 / 0.326 / 0.377 / 0.389 | no effect | trace (1.2e9×). (b) Invisible at T ≤ L |
| NC32 (float32 literals) | 1.396e-8 / 5.860e-8 / 5.316e-7 / 1.242e-5 / 1.288e-5 | 1.25e-8 … 8.57e-8 | 0 | v1 0.9990000128746033, Fish 7.600415215627072 > ln(1999) | trace (1.29e4×), bound, ramp_exact (both ≥ 1.29e4×; see §8, item 9) |
| NCS (superseded, instance 1) | 1.02 … 8.54 | — | — | 8.68 / 9.20 | trace (8.5e9×), ramp_exact (9.2e12×), flat_zero (1.06e12×) |
| NCT (superseded, instance 2) | 1.05 … 8.54 | — | — | 8.69 / 9.20 | trace, ramp_exact, flat_zero (same order) |

NC32 makes F-3 a checked fix at 1.3e4× the trace tolerance. It also fires bound and ramp_exact, which the brief did not list (§8, item 9).

**NCS / NCT per (instance, input).** These come from the shared-statics replay in the generator's actual call order: 16 calls per bar, NCS on flat … rampdn, then NCT on flat … rampdn. Max |diff| vs FR10:

| Input | NCS rows ≥ W | NCS rows < W | NCT rows ≥ W | rows with \|diff\| > 1e-12 (NCS / NCT) |
|---|---|---|---|---|
| flat | 0.98955 | 1.05887 | 0.98813 | 2998 (from row 2) / 2999 (from row 1) |
| s5 | 1.02369 | 1.02369 | 1.05086 | 2999 / 2999 (from row 1) |
| s10 | 1.47712 | 1.47712 | 1.51767 | 2999 / 2999 |
| s20 | 2.89554 | 2.89554 | 2.95249 | 2999 / 2999 |
| s40 | 7.66203 | 7.66203 | 7.68757 | 2999 / 2999 |
| s100 | 8.53877 | 8.53877 | 8.54159 | 2999 / 2999 |
| ramp | 8.68314 | 8.68314 | 8.68741 | 2999 / 2999 |
| rampdn | 9.19823 | 9.19823 | 9.20075 | 2999 / 2999 |

(b) The effect is large on every input and every row, as the brief's (c) predicted. It is not a start-up effect.

**NCB INFO (source B).**
- Fish vs FR10: 0.07980365618307178 / 0.30664356104690893 / 0.9611959629789821 / 2.628208085949269 / 2.7090517957574587. This matches the brief.
- v1 vs FR10: 0.212 … 0.358.
- Ramp Fish: 4.951718775643098.
- v1 reaches .9999, so its bound-v1 row is 9e-4 above the FR10 bound. That row is INFO.

## 7. IMP fire tests

All values are at full precision on the synthetic own-model raw file, so they are model vs model.

- **must_pass, own model:** 0.0 for all 10 variants.
- **must_fail, FR10 vs the NCW model:** 1.3044958329183087.
- **must_fail, NCS vs the FR10 model:** 9.198226649480118.

Discrimination vs the FR10 model:

| Variant | Value |
|---|---|
| FR20 | 3.0598542837263594 |
| NCB | 2.7090517957574587 |
| NCW | 1.3044958329183087 |
| NCC | 2.307097509775909 |
| NCK | 3.8002011672502 |
| NCL | 1.2104669944656683 |
| NC32 | 1.2881126671970833e-05 |
| NCS | 9.198226649480118 |
| NCT | 9.200746131800337 |

Every one is above 1e-9. FR10 itself is 0.

## 8. Callers (F-2) and items that did not fit the brief

**Callers.** I grepped for `FisherTransform(` and `ft_Trigger` in `*.c`, `*.h`, `*.py`, `*.md` and `*.toml`. I did not edit any of them.
- `strategies/tests/Test_Fisher_IFT_COG.c:31` (include), `:51` `FisherTransform(10)`, `:52` `var f_trig = ft_Trigger;`.
- `strategies/tests/Test_S1_C2_Audit.c:10` (include), `:32` `FisherTransform(FISHER_PERIOD)`. (c) Its `Price` there is `series(priceClose())`, built for Reflex. Stage 2 should pass a separate (H+L)/2 series, not reuse `Price`.
- Docs only, not callers: `docs/roadmap/FX_Roadmap_v2026.08.03.md:907`, `FX_Roadmap_v2026.08.10.md:917` and `Unified_FX_Crypto_Trading_Roadmap_2025_v4.md:829` show an old `FisherTransform(vars Price, int Period)` snippet.
- The usage comment in the current `FisherTransform.c`, lines 22–23.

**Items that did not fit the brief:**

1. **NCT is a negative control, not info.** The brief lists only NCS, "called as two instances". Unlike LRS, NCT is not bit-identical to the model: it differs by 0.99–9.2, the same as NCS. I followed RFX, where NCT is a control. This makes the counts 7 controls / 10 variants (pass items 2 and 5). It is easy to revert: role `info`, then drop it from `[detect.required]`.
2. **Ramp Fish reaches ln(1999) exactly in float64** (§4, row 1). The spec states this in its header, `[checks].source` and O_RAMP.
3. **`[zorro].series_len = 21` (new for this spec; the older specs use 3).** `MaxVal` / `MinVal(Price, Len)` read the caller's input series. A length-3 series would make Len 10 / 20 read past it. (c) 21 ≥ 20 (FR20) and ≥ 11 (NCL). The `[corrected_code].notes` asks stage 2 to state the length requirement in the header.
4. **The id `NCL` is used for the window Len + 1 control, as the brief names it.** The spec also says "No NCL variant" (no literals-as-printed form). Both the comment and `[source].no_ncl` say so.
5. **New spec keys, names chosen here (c):** `linear_stage`, `trace_outputs`, `clamp_gate`, `bounds`, `ramp_exact_outputs`, `trigger`, `flat_zero`.
   - Trace ids are `trace-<output>-T<t>`, so the single-output `trace-T<t>` form is not used here.
   - The flat-zero id is `flatzero`, because `_kind` defaults unknown tails to `flat`.
6. **The clamp gate removes only the flip row (c).** A real clamp flip would also move later rows, through v1 memory .67^n and Fish .5^n. No flip is expected: the model margin is 7.1e-4, against g2 = 1e-6. Recorded in `checker.osc_mask`.
7. **The no-static lint does not see the non-static global `var ft_Trigger`** (asserted). F-1's global is covered by `[corrected_code]` and by the trigger check instead.
8. **Invariance uses the out gates (range + clamp)** of the base sine's model. The brief does not say which gate applies.
9. **The INFO margin lines divide every bound effect by the absolute 1e-12.** For NC32 the out bound effect is really 1.288e-5 / (ln(1999)·1e-12) ≈ 1.7e6×, and the v1 bound 1.29e-8 / 1e-12 = 1.29e4×. Both are ≥ 10×, so `[detect.required]` is unaffected. The checker's PASS/FAIL uses the correct allowance.
10. **IMP compares rng and trig absolutely; raw, v1 and out are gated on the sines.** On flat and the ramps every output is compared absolutely, because they are exact known answers there.
11. **Start-up was measured only on the model side** (finding 7, EFS-style comparison). The run's Zorro-vs-model start-up rows go in the existing `info-startup` row (INFO).
12. **Stage-2 lint items (expected):**
    - `L_INCLUDE`: `FisherTransform_Superseded.c` is missing.
    - `L_NO_STATIC`: `FisherTransform.c` has 2 statics (`ft_Value1` line 58, `ft_Fish` line 69).
    - `--lint-only` exits 3 until stage 2, as LRS did.
13. **Commit split.** As in LRS (`c2fcd44` / `824a3cc`), the spec-dependent tests in commit 1 (`test_generator_fsh`, `test_checker_fsh`, `test_reference_fsh_spec`) pass only once commit 2 adds the spec.

## 9. Files

- **Modified:**
  - `analysis/harness/generator.py`
  - `analysis/harness/checker.py`
  - `analysis/harness/reference.py`
  - `analysis/harness/tests/rfx_support.py`
- **New (tooling and tests):**
  - `analysis/harness/tests/fsh_support.py`
  - `test_reference_fsh.py` (18 tests)
  - `test_generator_fsh.py` (23 tests)
  - `test_checker_fsh.py` (16 tests)
  - `test_reference_fsh_spec.py` (5 tests; 296 `[findings]` values reproduced, exactly)
- **New (spec and report):**
  - `analysis/harness/specs/FSH_ArticleFidelity.toml`
  - this report
- **Brief:** `docs/harness/FISHER_STAGE1_PROMPT.md` (untracked, unchanged).
