# Step 2 handoff — reusable harness: reference model, checker, generator

**For:** Claude Code (VS Code). **From:** planning chat, 2026-11-06.
**Implements:** `docs/harness/HARNESS_DESIGN.md` §7 step 2 (read §3–§6 first; D1–D3 are decided).
**Rules:** `CLAUDE.md` applies throughout (validation gate, sourcing labels, git = user only).

---

## How to work

- **One stage at a time.** Do stage 1 only. When its self-test result is in, STOP and report.
  Do not start the next stage until the user says so; the result goes to the planning chat
  for review first.
- **Step by step with the user.** Give the user one instruction at a time (one command, one
  git step), say why it matters, and wait for their output before the next.
- Report each stage as: files written, self-test table (check, expected, actual, |diff|,
  PASS/FAIL), guards seen to fire, open questions.
- Tests use the standard library `unittest` (pytest is not installed; do not install it).
  The user runs them with `python -m unittest discover -s analysis/harness/tests -v`.
- **Do not modify** H1 files: `analysis/harness/h1_check.py`,
  `strategies/tests/H1_SuperSmoother2Pole_Harness.c`, `docs/preregistration/H1_*`,
  `analysis/harness/results/H1_*`. Reuse their logic by copying, with a comment citing the
  source function.
- Work on a branch: ask the user to create `harness-step2` before the first file.

## File layout

```
analysis/harness/
  reference.py        stage 1
  checker.py          stage 2
  generator.py        stage 3
  specs/              stage 3 (one spec file per indicator; format proposed in stage 3)
  tests/
    test_reference.py
    test_checker.py
    test_generator.py
```

---

## Stage 1 — reference model (`reference.py`)

**Purpose:** compute expected values for a linear filter from a formula, never from a `.c` file.

**Contents**
- Filters as coefficient sets (b, a) for a direct-form IIR, built from parameters. Version 1:
  SuperSmoother 2-pole only, in two forms:
  - `ss2_article(period)`: TASC V.42:04 (a) with D1 replacements: `1.414`→√2, `3.14159`→π,
    `Cosine(1.414*180/Period)` in degrees = `cos(√2·π/Period)` in radians. Each replacement
    listed in a module-level table (literal, exact value, source) per the literal-constant rule.
  - `ss2_code(period)`: the coefficients exactly as `SuperSmoother2Pole.c` computes them
    (read the `.c` once to write this down, cite file and line; Zorro `PI` = 3.14159, gotchas
    9d.2). This is the H1 known-answer path (HARNESS_DESIGN §5). Check and record whether the
    `.c` uses `PI` inside the cosine (open (c) item in HARNESS_DESIGN D1).
- Measurements, analytic (no simulation needed for linear filters):
  - DC gain (flat input).
  - Steady-state gain at sine period T: |H(e^{-jω})|, ω = 2π/T.
  - Ramp lag (group delay at ω→0) = Σ(n·h[n]) / Σ h[n]; compute from (b, a) in closed form.
- A simulation function (run the recursion on an input array) used only to cross-check the
  analytic values.

**Self-test (`tests/test_reference.py`)** — acceptance criteria, fixed now:

| Check | Expected (source) | Tolerance |
|---|---|---|
| `ss2_code`, P = 10/14/20/30: gains at T = 5,10,20,40,100 | H1 criteria §4 table (a), = `EXPECT` in `h1_check.py` | 1e-6 (table stores 6 decimals) |
| `ss2_code`, same P: ramp lag | same table (a) | 1e-6 |
| `ss2_code`, any P: DC gain | 1 | 1e-12 |
| Analytic vs simulated gain and lag, P = 20, all T | each other (b) | 1e-6 |
| `ss2_article` vs `ss2_code`, largest gain diff, P = 10..30 | ~6e-7 if the `.c` uses `PI` in the cosine (HARNESS_DESIGN D1, b) | report the value; FAIL only if > 1e-5 |
| Measuring-tool check: EMA ramp lag, α = 0.4 | 1.50 bars. README §198 states the 1.50 but not α (a); α = 0.4 gives (1−α)/α = 1.50 (b) | 1e-9 |
| **Negative control:** `ss2_code` with c1 changed in the 3rd significant digit | must FAIL the H1 gain check at P = 20 | — |

Report the negative control's gain error: it is the first ceiling value for the D2 window.

**Then STOP.** Give the user the test command, wait for their output, give git steps one at a
time (add, commit `harness: reference model + self-tests`), and tell them to bring the result
to the planning chat.

---

## Stage 2 — checker (`checker.py`) — criteria pre-registered 2026-11-06, after stage 1 review

Stage 1 committed as `e03b026` (9/9 OK on both machines).

**Purpose:** generalise `h1_check.py` from one indicator to any spec: build inputs, read a Zorro
raw CSV, run guards, measure, compare, write the results file. No Zorro run in this stage.

**Contents**
- Inputs: flat, unit sines (any list of T), ramp; level/amplitude/slope as parameters; same
  construction as H1 `make_inputs()` (copy, cite).
- Measurements: flat error, least-squares sine gain, ramp lag — H1 §3 methods (copy, cite).
- Guards: all eleven H1 guards (`G_EMPTY`, `G_RAGGED`, `G_UNPARSEABLE`, `G_NONFINITE`,
  `G_HEADER`, `G_ROWCOUNT`, `G_N_REPEAT`, `G_N_GAP`, `G_N_SEQUENCE`, `G_CLOCK`,
  `G_INPUT_MISMATCH`), with the column list and row count taken from the spec, not hard-coded.
  A guard that fires writes an ERROR row and the run continues to the results file.
- Negative-control report per D2 Amendment 1: for each control, every check's error/tolerance
  ratio; "fails as required" (any check FAILs) and "10× margin met" (any ratio ≥ 10) as two
  separate fields.
- Results writer per CLAUDE.md §7: one row per check with `check_id, indicator, params, asset,
  input, expected, actual, abs_diff, tolerance, result`; `expected/actual/abs_diff` as `%.3e` or
  full precision; exclusive create (refuses to overwrite, next name gets `_run<k>`); footer with
  batch name, variant count, PASS/FAIL/ERROR counts, raw file path + sha256.
- The spec is passed in as a plain Python dict for now (format is stage 3's job); stage 2 uses
  one hand-written dict reproducing H1's setup.

**Self-test (`tests/test_checker.py`)** — acceptance criteria:

| # | Check | Expected (source) | Tolerance |
|---|---|---|---|
| C1 | Measurement accuracy: checker measures `reference.simulate` output for `ss2_code` P = 10/14/20/30 (exact π) and EMA(0.4) | `reference` analytic gain, lag (b, stage 1) | 1e-9 each. Report the worst value: it is the checker's term of the D2 floor |
| C2 | Same verdicts as H1: on `h1_check.fake_zorro_csv()` output (clean, and each of its mutations), checker rows vs `h1_check.evaluate()` rows | identical PASS/FAIL per check; actual values equal | 1e-12 |
| C3 | H1 run 2 reproduction, **if** `C:/Zorro/Data/H1_SS2P_raw.csv` exists and its sha256 = `e8ffc043…5a6f` (recorded in `H1_SuperSmoother2Pole_20261105_run2.csv` line 49) | the run-2 results file: all 28 checks PASS, NC1 + NC2 FAIL as required, actual values equal to the 6 decimals stored | exact at `%.6f`. If the file is missing or the hash differs: report "C3 not available" (not a FAIL), do not search further |
| C4 | Each of the eleven guards fires on its own deliberately broken file, and writes an ERROR row | one firing guard each, with the right id | — |
| C5 | Clean file fires no guard (no false alarm) | zero ERROR rows | — |
| C6 | Inputs equal H1 `make_inputs()` for H1's parameters | each other | 1e-12 |
| C7 | Results writer: second write to the same name is refused; `_run2` is created; sha256 in the footer equals a fresh hash of the raw file; footer counts equal row counts | — | exact |
| C8 | NC report reproduces stage 1 numbers for NC-A / NC-B (simulated output, P = 20): gain ratio 9.71× / 25.28×, "fails as required" = yes / yes, "10× margin met" = no / yes | stage 1 report (b) | ratio 1e-6 relative |

**Do not** change `h1_check.py`; import it read-only for C2 (or copy the two functions, cite).

**Then STOP**, as in stage 1: test command → user's output → git steps one at a time
(`harness: checker + self-tests`) → bring the report to the planning chat.

## Stage 3 — generator (`generator.py`) + spec format — criteria pre-registered 2026-11-07

Stage 2 committed as `54be500` (18/18 OK on both machines; C3 reproduced H1 run 2).

**Purpose:** turn a spec file into (1) the dict the checker uses and (2) one Zorro batch script
(one [Test] click) that writes the raw CSV the checker reads. No Zorro run in this stage; the
proven H1 harness `strategies/tests/H1_SuperSmoother2Pole_Harness.c` is the known answer.

**Contents**
- **Spec format: TOML**, one file per indicator in `analysis/harness/specs/`, read with the
  standard-library `tomllib` (Python ≥ 3.11; no install). Comments allowed, so sources sit next
  to the numbers they support. First spec: `specs/H1_SuperSmoother2Pole.toml`, reproducing H1.
- **Spec validator** (refuses a spec, with a reason, when):
  - an id (batch prefix, variant id, input id) contains `-` (stage 2 check-id rule
    `<prefix>-<variantid>-<check>`) or is not a valid C identifier fragment;
  - an expected value or tolerance has no source label (a)/(b)/(c);
  - there is no negative control (D2 Amendment 1);
  - a D1 literal replacement is listed without literal, exact value and source.
  It reports, never refuses on: the D2 floor × 10 ≤ tolerance check per quantity, and the
  per-control 10× margin, as INFO lines.
- **Negative controls, two kinds:** `param` (same indicator, wrong parameter, e.g. H1 NC1 = P21)
  and `inline` (a Light-C function body in the spec, written into the script, e.g. H1 NC2,
  stage 1 NC-A / NC-B).
- **Script writer:** H1's proven pattern (copy, cite): constants from integers at run time
  (`11/10`, `4*atan(1)`), unconditional fixed-order calls, one row per fed bar, latch + write
  before `quit()`, header from the spec, values `%.15f`.
- **Script lint** (generator refuses to write a script that fails it):
  - no `PI` token in harness code (the included indicator file may use it, D3);
  - no decimal literal whose float32 value differs from its float64 value (gotcha 9d.1;
    `2.0`, `180.0`, `0.5` pass, `1.1`, `0.01` fail);
  - no `file_append` after `quit(` in the same branch (9d.4);
  - every `#include` path resolves from `strategies/tests/` to an existing file (9d.3).
- **Test summary runner** `analysis/harness/run_tests.sh`: runs the suite with `python -u`,
  prints at the end one line `TOTAL n  PASS p  FAIL f  ERROR e  SKIP s`, and lists every skip
  with its reason.

**Self-test (`tests/test_generator.py`)** — acceptance criteria:

| # | Check | Expected (source) | Tolerance |
|---|---|---|---|
| G1 | H1 spec → checker dict | equal to stage 2's hand-written H1 dict (b) | exact |
| G2 | Call list of the generated H1 script: ordered (output slot, function, input series, parameter) tuples | parsed from the H1 harness `.c`, lines 114–155 (b) | exact, all 42 |
| G3 | Raw CSV header written by the generated script | `checker` expected header for the same spec | exact string |
| G4 | Input expressions in the generated script, evaluated in Python (math namespace only) for n = 0..N−1 | `checker` inputs | 1e-12 (= `TOL_X`) |
| G5 | Inline NC function in the generated H1 script | H1 `h1_ss_deg` body, whitespace-normalised | exact |
| G6 | Validator fires on each deliberately broken spec (one per refusal rule above) | refused, with the right reason | — |
| G7 | Lint fires on each deliberately broken script (one per lint rule) and passes the generated H1 script | refused / passed | — |
| G8 | Generated script is written under a new name (no overwrite of an existing `.c`); the H1 harness file is unchanged (sha256 before = after) | — | exact |
| G9 | `run_tests.sh` on this suite | summary line counts = unittest's own counts; skips listed with reason | exact |

**Not in this stage:** running the generated script in Zorro (that is stage 4), and specs for
any indicator other than H1's SuperSmoother2Pole.

**Then STOP**, same protocol: test command (now `bash analysis/harness/run_tests.sh`) → user's
output → git steps one at a time (`harness: generator + spec format + self-tests`) → report.

## Stage 4 — tool acceptance (Zorro, user clicks) — HARNESS_DESIGN §5

Reproduce H1 on SS2: 28/28 PASS, NC1 + NC2 FAIL as required.

---

## Amendment 1 — 2026-11-06 (stage 1 criteria; decided in the planning chat)

**Reason.** The stage 1 table compared `ss2_code` (Zorro `PI` = float32(3.14159)) against H1's
`EXPECT`, which `h1_check.py` `coeffs()` computes with exact π (`math.pi`, lines 65–69) (b).
The `PI` gap (gotchas 9d.2: lag +1.76e-6 … +5.43e-6 bars; gain ~6.2e-7) exceeds the 1e-6
tolerance for lag, so the criterion was inconsistent as written. First run (9 tests, 8 ok,
1 FAIL: lag 4/4) is kept in the record; nothing was changed to make it pass.

**A1.1 — known-answer rows, gain and lag.** Compare H1's `EXPECT` against `ss2_code` evaluated
with **exact π** (and against `ss2_article`, which is algebraically the same filter: the `.c`'s
`c0·(P0+P1)` equals the article's `c1·(P0+P1)/2`), tolerance 1e-6. Both forms were written
independently, so matching both also cross-checks article form vs code form.

**A1.2 — `PI` gap as INFO.** Report `ss2_code(Zorro PI) − ss2_code(exact π)`: largest gain diff
and largest lag diff, P = 10..30. INFO only, never PASS/FAIL. This is the `PI` floor term for
D2 (HARNESS_DESIGN §6).

**A1.3 — sourcing.** `ss2_article` is (a): TASC V.42:04, sidebar "SuperSmoother Function, In
EasyLanguage" (`a1 = expvalue(-1.414*3.14159 / Period); b1 = 2*a1*Cosine(1.414*180 / Period);
c2 = b1; c3 = -a1*a1; c1 = 1 - c2 - c3;`), with the D1 replacements. Relabel from (c).

**A1.4 — negative controls.** NC-A and NC-B stay as run; both must still FAIL. Their per-check
error/tolerance ratios are reported for the amended D2 rule (per-control detection).

## Amendment 2 — 2026-11-07 (stage 3 criteria; before any stage 3 code)

**Reason.** Conflict found in review: the lint rule "no `PI` token in harness code" would reject
the generated H1 script, because H1's inline negative control `h1_ss_deg` (harness `.c` line 47)
uses `PI`, and G5 requires that body unchanged while G7 requires the generated H1 script to pass.

**A2.1 — lint scope.** "Harness code" means the script's own plumbing: constants, input
construction, series calls, output and file writing. **Inline negative-control bodies** are
mutated copies of indicator code and follow the indicator rule (D3: `PI` allowed). The lint
still applies the float32-literal, `quit()` and `#include` rules to them.

**A2.2 — G7 adds one case:** a script with `PI` in input construction is refused, while the same
token inside an inline NC body is accepted.

**A2.3 — test output location.** Tests write generated scripts to a temporary directory, never
into `strategies/tests/`, so the suite can be rerun and leaves no files. G8 runs there.
