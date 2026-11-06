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

## Stage 2 — checker (`checker.py`) — do not start before review of stage 1

Input construction (integers at run time, H1 pattern), least-squares sine gain, ramp lag from
filter output, input guards, results writer (no-overwrite, sha256, `%.3e`, footer with variant
count). Self-test on simulated outputs with known gain/lag, and every guard fed a broken input
and seen to fire. Detailed criteria will be added to this file after the stage 1 review.

## Stage 3 — generator (`generator.py`) — do not start before review of stage 2

Spec format, Light-C batch script writer (one click), lint that rejects decimal literals and
`PI` in harness inputs. Detailed criteria added after the stage 2 review.

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
