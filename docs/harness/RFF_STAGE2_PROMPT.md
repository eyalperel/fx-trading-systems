# RFF stage 2 — corrected RoofingFilter.c, pre-run records (Amendment 1), generated script

Planning chat, 2026-11-17. Branch `harness-rff`. Spec pre-registered at `b6b5c5d` (tooling `f9f3561`); the planning chat
back-checked the spec's tables, floors, effects, [detect.required] and IMP fire test with independent code (agrees to
<= 2e-9 relative). User's Git Bash: 283/283 at b6b5c5d.

**Git:** do NOT commit. At the end print the suggested commands (one commit for the .c, one for Amendment 1 + generated
script) and STOP. Do NOT click / run Zorro.

## 1. Corrected `indicators/ehlers/RoofingFilter.c`

Function body = `[corrected_code].lines` of the spec, verbatim. Header (comments only), labels (a)/(b)/(c):
- Source (a): Ehlers, "Predictive And Successful Indicators", TASC V.32:1 (Jan 2014), sidebar "EasyLanguage Code To
  Compute The Roofing Filter": HP-A(48) then SuperSmoother(10) on (HP + HP[1])/2; HP and Filt histories start at 0.
  The article fixes 48 / 10; HPPeriod / SSPeriod are the library's parameters. (Fixes GAP-1.31: "Optimal Detrending" was wrong.)
- Remove: "Validated: EUR/USD D1, BTC/USD H4", "Result: only dominant cycle survives", "HPPeriod must be >> SSPeriod ...".
  Keep only statements that are (a) or (b); anything else labelled (c) or dropped.
- (b) Seeding: HP's first output is 0 and SuperSmoother2Pole seeds at its first input, so the output starts as the
  source's Filt(0) (spec [observations].O_SEED).
- (b) Article gain RoofingFilter(48,10): T = 20 0.8900165495219391; T = 2 ~0 (spec [known_answer_T20]).
- Call rules: callers invoke unconditionally every bar (series() allocates by call order, gotchas 3.1); include order
  HighPassFilter.c -> SuperSmoother2Pole.c -> RoofingFilter.c (gotchas 5.3).
- Verification line: `analysis/harness/specs/RFF_ArticleFidelity.toml` (pre-registered b6b5c5d). Not verified until that run passes.

## 2. Pre-run conditions (spec pass_condition, pre-run i–iv) — all must PASS

- (i) un-skip / enable the real-file assertion in `test_rff_corrected_code.py`: the new .c contains
  `[corrected_code].lines` verbatim (whitespace-normalised, comments stripped) inside the declared function.
  Show the guard firing on temp copies (e.g. rf_hp -> hp, SSPeriod -> HPPeriod in the SS call, series(...,3) -> series(...,2)).
- (ii) already PASS at stage 1 (blob bb717f1...): re-run and record.
- (iii) `test_reference_rff_spec.py` passes; record largest deviation per section.
- (iv) `python analysis/harness/generator.py analysis/harness/specs/RFF_ArticleFidelity.toml --lint-only` clean; record
  the INFO lines (incl. the NCO L_FLOAT32 exemption).
- Full suite: `bash analysis/harness/run_tests.sh` (report TOTAL; tracebacks + rerun on any ERROR, CLAUDE.md §8).

## 3. Amendment 1 (append to the spec; text above unchanged)

Same form as HPF Amendment 1: `[amendment_1]` (date, base_commit = the .c commit's parent b6b5c5d noted as base,
before_run = true, changes A1.1 = pre-run records only, no criterion / tolerance / table / floor / effect / variant
changed) + `[prerun]` cond_i..cond_iv, tests_before / tests_after / suite line, blob hashes of RoofingFilter.c old
(bb717f1...) and new (`git hash-object` of the new file). If ANY criterion would need to change, STOP and report instead.

## 4. Generated script

`python analysis/harness/generator.py analysis/harness/specs/RFF_ArticleFidelity.toml` -> `strategies/tests/GEN_RFF_RoofingFilter.c`.
Record its sha256 in `[prerun]`. Check by reading the script (report each):
- the three includes in dependency order, relative paths as in [zorro].include;
- the `alt` input: built from integers, sign static reset at INITRUN, flipped once per bar, before any filter call;
- every variant call unconditional, fixed order, `RoofingFilter(S, hp, ss)` for real variants; inline bodies present
  once each; no `Period` identifier; no decimal literal outside the NCO exemption;
- raw file `Data/GEN_RFF_raw.csv`, no-overwrite guard; writes happen before `quit()` (9d.4).
- Confirm `C:/Zorro/Data/GEN_RFF_raw.csv` does not exist yet (or report it).

## Done when

Report: new .c (full text), pre-run i–iv results with guard-fire evidence, suite TOTAL before/after, script sha256 and
the read-through checks above, any deviation from this brief. Then STOP: no commit, no Zorro run.
