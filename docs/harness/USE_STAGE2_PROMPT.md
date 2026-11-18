# USE stage 2 — corrected UltimateSmootherE.c, pre-run records (Amendment 1), generated script

Planning chat, 2026-11-18. Branch `harness-use`. Tooling `baa74a9`; spec pre-registered at `ca4454b`
(`analysis/harness/specs/USE_ArticleFidelity.toml`). The planning chat back-checked the spec's corrected-code lines, tables,
floors, effects, [detect.required] and IMP fire tests with independent code (agree <= 1.6e-15) and corrected one text line
before commit (`[tolerances.flat].source`: DC gain 1, expected output = level). User's Git Bash: 348/348 at ca4454b.
Labels: (a) source states, (b) measured/computed, (c) inference.

**Git:** do NOT commit. At the end print the suggested commands (one commit for the .c + its test, one for Amendment 1 +
generated script) and STOP. Do NOT click / run Zorro.

## 1. Corrected `indicators/ehlers/UltimateSmootherE.c`

Function signature `var UltimateSmootherE(vars Price, int Period)`; body = `[corrected_code].lines` of the spec, verbatim.
Header (comments only), each statement labelled (a)/(b)/(c) or dropped:
- Source (a): Ehlers, "The Ultimate Smoother", TASC V.42:04 (2024), pp. 8–15, sidebar "UltimateSmoother Function, In
  EasyLanguage". US = input − HP, with the V.42:04 $HighPass (NOT HP-A of V.32:1 implemented by HighPassFilter.c).
- Keep the construction comment (output = input − highpass; filtering by cancellation) and Ehlers' caveat (a, article
  conclusion 3: less smooth than SuperSmoother).
- Constants (D1 rule 1): 1.414 -> sqrt(2), built in `us_k` so no expression starts with a literal product (gotchas 9d.8).
  Degrees -> radians.
- Start-up (a): the first **3** outputs equal Price (EasyLanguage CurrentBar < 4). `us_n` is a per-instance counter equal
  to CurrentBar (1 on this instance's first call), replacing the global `Bar < 4` (base unconfirmed; the old comment said
  4 bars). (c) `series(0,2)` giving `us_n[1] = 0` on the first call is expected (gotchas 9d.6), verified by the s20 start-up
  check (spec finding 7).
- (b) DC gain 1, Nyquist gain 0, ramp lag 0 (spec [findings]). Passband gain > 1 (peak ~1.27 near T ≈ 1.3P) and phase at
  T = P ≈ −0.62 rad: the article's "zero lag" holds at DC, not across the pass band (spec O_PASSBAND).
- Replace the "SUFFIX 'E'" paragraph: the earlier file is now `UltimateSmoother_W5_Superseded.c`; (b) it does not implement
  the cited article (PROJECT_STATE §1.1). Drop the claim about its Week 5 method unless kept with the gotchas §8 reference.
- Keep the STATE paragraph (series(), two instances in UltimateChannelBands, unconditional calls, gotchas 3.1), now noting
  both `series()` calls (us_n, us_US) precede the early return.
- Verification line: `analysis/harness/specs/USE_ArticleFidelity.toml` (pre-registered ca4454b). Not verified until that run
  passes.

## 2. Corrected-code test (new, as `test_rff_corrected_code.py` / `test_hp_corrected_code.py`)

`analysis/harness/tests/test_use_corrected_code.py`: the real .c contains `[corrected_code].lines` verbatim
(whitespace-normalised, comments stripped) inside the declared function. Show the guard firing on temp copies, at least:
`us_n[0] < 4` -> `< 5`; `us_k*PI` -> `1.414*PI`; `/4.0` -> `/4.01`; `series(0, 2)` moved after the early return.

## 3. Pre-run conditions (spec pass_condition, pre-run i–iv) — all must PASS

- (i) `test_use_corrected_code.py` passes on the new .c; guard-fire evidence for each broken copy above.
- (ii) old blob `c545c201140e2927e9a5c1ec7664440ded1b3350` (ddbf9fa) recorded; the diff old -> new body is only D-1
  (`1.414 * PI` -> `us_k*PI` + the us_k line) and D-2 (`Bar < 4` -> the us_n counter, 2 lines) — state any other token
  difference (e.g. whitespace / `2.0 * us_a1` spacing) explicitly.
- (iii) `test_reference_use_spec.py` passes; record the largest deviation per section.
- (iv) `python analysis/harness/generator.py analysis/harness/specs/USE_ArticleFidelity.toml --lint-only` clean; record the
  INFO lines (D2 windows, per-control margins, NCL info line).
- Full suite: `bash analysis/harness/run_tests.sh` (report TOTAL; tracebacks + rerun on any ERROR, CLAUDE.md §8).

## 4. Amendment 1 (append to the spec; text above unchanged)

Same form as RFF / HPF Amendment 1: `[amendment_1]` (date, base_commit ca4454b, before_run = true, changes A1.1 = pre-run
records only, no criterion / tolerance / table / floor / effect / variant changed) + `[prerun]` cond_i..cond_iv,
tests_before / tests_after / suite line, blob hashes of UltimateSmootherE.c old (c545c201…) and new (`git hash-object`).
If ANY criterion would need to change, STOP and report instead.

## 5. Generated script

`python analysis/harness/generator.py analysis/harness/specs/USE_ArticleFidelity.toml` ->
`strategies/tests/GEN_USE_UltimateSmootherE.c`. Record its sha256 in `[prerun]`. Check by reading the script (report each):
- the two includes in dependency order (HighPassFilter.c, then UltimateSmootherE.c), relative paths as in [zorro].include;
- the `alt` input: built from integers, sign static reset at INITRUN, flipped once per bar, before any filter call;
- every variant call unconditional, fixed order; `UltimateSmootherE(S, P)` for P10/P14/P20/P30 and NC1 (21); inline bodies
  (NCL, NCA, NCB, NCS, NCX, NC2) present once each, locals uniquely prefixed; no `Period` identifier in generated code;
  no decimal literal starting an expression product (9d.8); NCL labelled info;
- raw file `Data/GEN_USE_raw.csv`, no-overwrite guard; writes happen before `quit()` (9d.4).
- Confirm `C:/Zorro/Data/GEN_USE_raw.csv` does not exist yet (or report it).

## Done when

Report: new .c (full text), test file summary with guard-fire evidence, pre-run i–iv results, suite TOTAL before/after,
script sha256 and the read-through checks above, any deviation from this brief. Then STOP: no commit, no Zorro run.
