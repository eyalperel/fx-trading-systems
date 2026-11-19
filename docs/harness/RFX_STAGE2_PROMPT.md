# RFX stage 2 — corrected Reflex.c, Reflex_Superseded.c, pre-run records (Amendment 1), generated script

Planning chat, 2026-11-18. Branch `harness-rfx`. Tooling `853dc20`; spec pre-registered at `960ae09`
(`analysis/harness/specs/RFX_ArticleFidelity.toml`). The planning chat back-checked the spec draft with independent code:
Sum tables, floors, findings 1–11 and controls NCA–NCW within the brief's thresholds; NCS / NCT effects 1.347901 / 1.878025
reproduced for the real call order (16 calls per bar, one static MS; same for three input orders); NCS bound
5.000000055879. User's Git Bash: 445/445 at `853dc20`. Labels: (a) source states, (b) measured/computed, (c) inference.

**Git:** do NOT commit. At the end print the suggested commands (one commit for the two .c files + their test, one for the
generator change if any, one for Amendment 1 + generated script) and STOP. Do NOT click / run Zorro.

## 1. Corrected `indicators/ehlers/Reflex.c`

Two functions, bodies = `[corrected_code].lines` and `.wrapper_lines` of the spec, verbatim:
`var ReflexCore(vars Price, int Length, var* pSum, var* pMS)` then `var Reflex(vars Price, int Length)`.
Header (comments only), each statement labelled (a)/(b)/(c) or dropped:
- Source (a): Ehlers, "Reflex: A New Zero-Lag Indicator", TASC V.38:02 (2020), pp. 6–8, 21, sidebar "EasyLanguage Code For
  Reflex Indicator". Formula as `[source].formula`, in Light-C terms (radians).
- Deviations fixed (b), review `docs/harness/REFLEX_SOURCE_REVIEW.md` (`05be788`): R-1 per-instance `rx_MS` series (was a
  file-static shared by every call); R-2 real half length `.5*Length`, SuperSmoother computed in this file (was int
  `Length/2` via `SuperSmoother2Pole(int)`); R-3 weights built from integers (gotchas 9d.1); R-5 this header.
- Constants (D1 rule 1): 1.414 -> sqrt(2) in `rx_k` so no expression starts with a literal product (9d.8); degrees -> radians.
- Start-up (a): no rule in the source (R-4). Filt history starts at the first price (`series(Price[0], ...)`, 9d.6), MS at 0.
  (b) MS memory 0.96^n: start-up effect < 1e-12 after 677 bars; treat the first ~700 bars as warm-up.
- (b) Properties, spec [findings]: Sum (exported via `ReflexCore`) is linear, DC gain 0, zero on a ramp; |Reflex| <= 5 exactly
  (attained). On flat / ramp input Reflex is rounding noise divided by rounding noise (O_RAMP_ILLCONDITIONED): do not read it.
- (b) O_ZEROLAG: at T = Length the summation stage has phase 0, but the SuperSmoother(L/2) adds about −0.62 rad at L = 20
  (about 2 bars): Reflex is not zero-lag at its own design period.
- STATE: both `series()` calls unconditional, before any use (gotchas 3.1); every instance has its own Filt and MS.
- Verification line: `analysis/harness/specs/RFX_ArticleFidelity.toml` (pre-registered `960ae09`). Not verified until that
  run passes.

## 2. `indicators/ehlers/Reflex_Superseded.c` (new; the NCS / NCT control)

The CURRENT `Reflex.c` body (blob `7c6b235c00f053faef6f70dff71d9e09b99c440d`) verbatim, function renamed `Reflex` ->
`Reflex_Superseded`, every `rx_` identifier -> `rxo_` (flat namespace, gotchas 1.3). Nothing else changes: the `static`, the
INITRUN reset, the float32 `0.04` / `0.96`, the int half length and the `SuperSmoother2Pole` call all stay. Header: "SUPERSEDED
— do not use. Kept as the negative control NCS / NCT of RFX_ArticleFidelity (R-1 shared static MS, R-2 int half length,
R-3 float32 weights). Corrected file: Reflex.c." Report the token diff vs the old blob (must be renames + header only).

## 3. Corrected-code test (new, as `test_use_corrected_code.py`)

`analysis/harness/tests/test_rfx_corrected_code.py`:
- `Reflex.c` contains `[corrected_code].lines` inside `ReflexCore` and `wrapper_lines` inside `Reflex` (whitespace-normalised,
  comments stripped).
- `Reflex_Superseded.c` equals the old blob after the renames (comments stripped).
- Show the guard firing on temp copies, at least: `rx_w1 = rx_w1/100` -> `/1000`; `rx_half = rx_half/2;` removed;
  `vars rx_MS = series(0, 2);` -> `static var rx_MS;` (with `rx_MS[0]`/`rx_MS[1]` adapted or not, either way it must fail);
  `series(0, 2)` moved after the `rx_MS[0] = ...` line; in the superseded file, one `rxo_` left as `rx_`.

## 4. Generator: out-parameters through local scalars (decided 2026-11-18, planning chat)

(c) `&Y[k]` (address of an array element) as an out-parameter has never been compiled in this project; gotchas §7 shows only
`&scalar`. To avoid a failed [Test] click, the generator emits the proven form for every multi-output call:
```c
var rfx_o_sum; var rfx_o_ms;          // declared ONCE, before the first call
...
Y[k_r] = ReflexCore(S, 20, &rfx_o_sum, &rfx_o_ms);
Y[k_sum] = rfx_o_sum;
Y[k_ms] = rfx_o_ms;
```
(Use whatever array / index names the generator already uses; the two locals are reused by every call, which is safe because
each is copied before the next call.) This changes the generated layout only, no pre-registered criterion. Existing specs
(H1, SS2F, SS3F, HPF, RFF, USE) must still regenerate BYTE-IDENTICAL scripts. Update the tests that asserted `&Y[k]`; full suite
must pass. If you see a reason this is unsafe in Light-C, STOP and report instead.

## 5. Pre-run conditions (spec pass_condition, pre-run i–iv) — all must PASS

- (i) `test_rfx_corrected_code.py` passes on the new files; guard-fire evidence for each broken copy above.
- (ii) old blob `7c6b235c…440d` recorded; the diff old -> new `Reflex.c` is only R-1, R-2, R-3, R-5 (+ the new `ReflexCore` /
  wrapper structure): list every other token difference explicitly. Superseded file: renames + header only.
- (iii) `test_reference_rfx_spec.py` passes; record the largest deviation per section.
- (iv) `python analysis/harness/generator.py analysis/harness/specs/RFX_ArticleFidelity.toml --lint-only` clean, now including
  the three includes resolving; record the INFO lines (D2 windows, per-control margins, NCL info line).
- Full suite: `bash analysis/harness/run_tests.sh` (report TOTAL; tracebacks + rerun on any ERROR, CLAUDE.md §8).

## 6. Amendment 1 (append to the spec; text above unchanged)

Same form as USE / RFF Amendment 1: `[amendment_1]` (date, base_commit 960ae09, before_run = true, changes A1.1 = pre-run
records; A1.2 = the generator's local-scalar out-parameters (§4), a script-layout change, no criterion / tolerance / table /
floor / effect / variant changed) + `[prerun]` cond_i..cond_iv, tests_before / tests_after / suite line, blob hashes of
Reflex.c old (7c6b235c…) and new, Reflex_Superseded.c new (`git hash-object`). If ANY criterion would need to change, STOP
and report instead.

## 7. Generated script

`python analysis/harness/generator.py analysis/harness/specs/RFX_ArticleFidelity.toml` ->
`strategies/tests/GEN_RFX_Reflex.c`. Record its sha256 in `[prerun]`. Check by reading the script (report each):
- the three includes in dependency order (SuperSmoother2Pole.c, Reflex_Superseded.c, Reflex.c), relative paths as in [zorro].include;
- the alt input and the invariance copies (sc*, of*): built from integers, before any indicator call; alt sign static reset at INITRUN;
- every call unconditional, fixed order: ReflexCore for L14/L20/L21/L30 and NC1 (22) on every base input and (real variants)
  the 10 copies; inline bodies (NCL, NCA, NC2, NCH, NCK, NCW) present once each, locals uniquely prefixed;
  `Reflex_Superseded(S, 20)` then `Reflex_Superseded(S, 14)` on the 8 base inputs in the order the spec's effects assumed;
  calls per bar = 144 (state the count); no `Period` identifier; no expression starting with a product of decimal literals (9d.8);
- out-parameters through the two local scalars (§4), copied before the next call;
- raw file `Data/GEN_RFX_raw.csv`, 340 columns, no-overwrite guard; header and rows written in chunks as the generator now does;
  writes happen before `quit()` (9d.4).
- Confirm `C:/Zorro/Data/GEN_RFX_raw.csv` does not exist yet (or report it).

## Done when

Report: both .c files (full text), test summary with guard-fire evidence, generator change + updated tests, pre-run i–iv,
suite TOTAL before/after, script sha256 and the read-through checks above, any deviation from this brief. Then STOP: no
commit, no Zorro run.
