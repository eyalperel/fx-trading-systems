# RFF stage 1 — tooling + reference models + spec draft (RoofingFilter)

Planning chat, 2026-11-17. Decisions accepted by the user: 1A, 2A, 3 (below). Build mode, speed over polish,
but the validation gate is unchanged (CLAUDE.md). Labels: (a) source states, (b) measured/computed, (c) inference.

**Git:** branch `harness-rff` from `main` (9b117fc). Do NOT commit. At the end print the `git add` / `git commit`
commands you suggest (one commit for tooling+tests, one for the spec draft), and STOP.

## Source (a) — TASC V.32:1 (Jan 2014), sidebar "EasyLanguage Code To Compute The Roofing Filter"

```
alpha1 = (Cosine(.707*360 / 48) + Sine (.707*360 / 48) - 1) / Cosine(.707*360 / 48);
HP = (1 - alpha1 / 2)*(1 - alpha1 / 2)*(Close - 2*Close[1] + Close[2]) + 2*(1 - alpha1)*HP[1] - (1 - alpha1)*(1 - alpha1)*HP[2];
a1 = expvalue(-1.414*3.14159 / 10);
b1 = 2*a1*Cosine(1.414*180 / 10);
c2 = b1;  c3 = -a1*a1;  c1 = 1 - c2 - c3;
Filt = c1*(HP + HP[1]) / 2 + c2*Filt[1] + c3*Filt[2];
Vars: ... HP(0) ... Filt(0) ...      (both histories start at 0)
```
D1 rule 1: `.707` -> 1/sqrt(2), `1.414` -> sqrt(2), `3.14159` -> pi. Degrees -> radians. The article fixes 48 and 10;
HPPeriod/SSPeriod as parameters is the library's generalisation (HP: same lines with HPPeriod in V.33:09).

## Planning-chat findings to record in the spec (b)

1. **Seeding.** HP's first output is 0 (input history = x[0] by series seeding, 9d.6; HP history 0), so SS2's
   `series(Price[0],3)` seeds Filt at 0 = the source's `Filt(0)`. Simulated: code cascade (HP seed zero, SS seed =
   hp[0]) vs the single cascaded article filter with seed zero: max diff 9.3e-17 (ramp), 1.7e-15 (sine T=20).
2. **T = 2 cannot be a sine:** sin(pi*n) = 0 at integer n, so "s2" would be a flat input. Hence the alternating input (2A).
3. **Stage order is not detectable:** from the zero-seed steady state, SS->HP == HP->SS on every input (LTI). Not a
   control; record as an [observations] note.
4. **PROJECT_STATE §5 known answer 0.890038 is superseded:** it is the OLD code (0.707 HP + sqrt(2) SS).
   Article (exact) RoofingFilter(48,10): gain T=20 = 0.8900165495219456, phase -0.05338683922280491 rad;
   article-as-printed literals 0.8900220682097724; old code 0.8900377520202766. Gain at T=2 = 6.0e-18 (zero).
5. Floor (PI gap, code vs article, P = (48,10),(48,20),(30,10),(125,10)): gain <= 5.6e-7, phase <= 1.6e-6 rad.

## Decision 1A — tooling: two integer parameters

- Variants may give `params = [48, 10]` (list of ints) instead of `param = 48`; the generated call is
  `Y[k] = Fn(S, 48, 10);`. Existing specs (`param`) must regenerate BYTE-IDENTICAL scripts (test it for H1, SS2F,
  SS3F, HPF) and their checker outputs must not change.
- `[zorro].include` may be a list (dependency order, gotchas 5.3):
  `../../indicators/ehlers/HighPassFilter.c`, `.../SuperSmoother2Pole.c`, `.../RoofingFilter.c`. A string still works.

## Decision 2A — tooling: alternating (Nyquist) input

- New optional `[inputs] alternating = true` -> extra input id `alt`, x[n] = level + amp*(-1)^n, built at run time
  from integers (9d.1; e.g. a sign variable flipped each bar). Placed after the sines, before `ramp`, so existing
  input ids/slots are unchanged when the flag is absent (byte-identical old scripts).
- Checker, input `alt`: least-squares fit y = a*(-1)^n + c over n >= warmup; gain = |a|/amp. Phase at Nyquist is
  0 or pi only; it is checked only where expected gain >= `[checks].phase_gate`, otherwise the phase row is written
  as SKIP (not PASS) with reason `gain < phase_gate`. This is the first time the gate binds: a test must show the
  gate firing (row SKIP) and not firing (row checked) on synthetic data.
- Expected tables get `gain_alt` (and `phase_alt` only when gain >= gate). Reference: `gain_at(f, 2)`.
- `startup_inputs` may include `alt` and sine ids (`s20`) if not already allowed.
- Input guard (x vs recomputed, 1e-12) covers `alt`.

## Reference models (reference.py)

- `cascade(f, g)` -> one Filter (polynomial products). `roof_article(hp, ss) = cascade(hp_article(hp), ss2_article(ss))`.
  `roof_code(hp, ss, ...) = cascade(hp_code(hp, k=sqrt(2)/2), ss2_code(ss))` with control hooks below.
- `simulate_cascade(stages, x)`: stage by stage, each with its own seed (HP seed 'zero' or 'price'; SS seed 'price' =
  its own first input). Needed by NCO (old HP has a price seed, not representable as one filter). Test: for the
  corrected code it equals `simulate(roof_code, x, seed='zero')` to <= 1e-14 on all inputs.
- `article_model` accepts `roof_article(48,10)` (restricted grammar, no eval). IMP_MODELS entries for every variant.

## Decision 3 — corrected code (pre-registered lines; .c written AFTER the spec is committed)

```c
var RoofingFilter(vars Price, int HPPeriod, int SSPeriod)
{
    var* rf_hp = series(HighPassFilter(Price, HPPeriod), 3);
    var rf_out = SuperSmoother2Pole(rf_hp, SSPeriod);
    return rf_out;
}
```
Header to write with the .c: source V.32:1 sidebar (GAP-1.31 fix); remove "Validated", "only dominant cycle
survives", "HPPeriod must be >> SSPeriod" (unsourced); verification line pointing at the spec. No NCH control: the
corrected file is numerically identical to the current one (renames only); NCO is the "what changed" control.

## Spec draft: `analysis/harness/specs/RFF_ArticleFidelity.toml`

Same structure as `HP_ArticleFidelity.toml` (incl. [corrected_code], [floor], [detect], [imp], pass condition,
pre-run i–iv; no NCH, so pre-run (ii) becomes: the current RoofingFilter.c blob hash is recorded and is
token-identical to [corrected_code] apart from the two renames). id_prefix `RFF`. dc_gain 0. Inputs as HPF +
`alternating = true`. startup_inputs `["flat", "ramp", "s20"]`.

**Every number stored at full precision** (HP Amendment 1, A1.2), including fire-test and floor per-variant values.

Real variants (indicator `RoofingFilter`, seed zero, article model `roof_article(hp,ss)`):
`P48S10` [48,10] (source), `P30S10` [30,10], `P125S10` [125,10], `P48S20` [48,20].

Negative controls (all at [48,10] unless stated; inline bodies call the verified `HighPassFilter` /
`SuperSmoother2Pole` where they can; every expression starts with a variable, 9d.8; locals uniquely prefixed per body):
- `NCA` SS pole factor a1 + 1.0/1000 (bump3 at SS=10: 0.6412805 -> 0.6422805) BEFORE b1, c3, c0. DC gain stays 1.
- `NCB` SS input weight c0 + 1.0/1000 (bump3: 0.1265974 -> 0.1275974) after the coefficients.
- `NCU` SS input not averaged: `Filt = (1 - b1 + a1*a1)*hp[0] + c2*Filt[1] + c3*Filt[2]` (full weight on HP, no
  HP[1] term). Expected: alt gain far from 0.
- `NCO` old pipeline: the old HighPassFilter body (= HPF spec variant NCH body, literal 0.707, `series(Price[0],3)`)
  feeding `SuperSmoother2Pole` as RoofingFilter.c does. lint_allow_float32 ["0.707"]. IMP model: HP stage
  `hp_code(48, theta_const=ZORRO_FOLD_0707x2xPI)` seed price, then ss2_code(10) seed price (simulate_cascade).
  (b, planning chat) gain effect at T=20 is ~2.1e-5 < tol: expect detection by start-up only; confirm.
- `NC1` params [49,10] vs P48S10 table. `NC1s` params [48,11] vs P48S10.
- `NC2` SS cosine argument in degrees (sqrt(2)*180/SSP), exponent unchanged (gotchas §2 mixed-file mode).

Tolerances: gain 3e-5, phase 3e-5 rad, resid 1e-9, startup 1e-6, flat 1e-9, x 1e-12, imp 1e-9 (D4 rule 5 defaults).
Check each against the measured window (D2 rule 3); if a default fails, STOP and report — do not pick a new value.
Compute every [variants.effect] with the checker's own measurement functions (incl. alt). [detect.required] = every
kind whose effect >= 10x its tolerance; report the list. If any control has NO kind >= 10x, STOP and report.
IMP must_pass: every variant with its own model; must_fail: P48S10 replayed with the NCO model; NCO replayed with
the corrected model. Record fire-test values at full precision.

Pass condition: as HPF, with the real-check count = 4 variants x (flat + 5 gains + alt gain + 5 phases [+ alt phase
only if gated in] + ramp resid + 3 start-up) — state the exact number.

## Done when

- `bash analysis/harness/run_tests.sh` all PASS (report TOTAL before/after) incl. new tests for 1A, 2A,
  cascade/simulate_cascade, gate SKIP firing, byte-identical regeneration of the 4 existing specs.
- `python analysis/harness/generator.py analysis/harness/specs/RFF_ArticleFidelity.toml --lint-only` clean.
- Report: real-check count, the 4 expected tables (gain, phase, gain_alt), floors, every control's effects and
  [detect.required], IMP fire-test values, anything that did not fit this prompt. Then STOP (no commit, no .c edit,
  no generated script run).
