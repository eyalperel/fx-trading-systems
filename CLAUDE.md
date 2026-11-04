# CLAUDE.md — fx-trading-systems

Rules for Claude Code in this repo. Read this first in every session.
The project's current state lives in `docs/PROJECT_STATE.md`. If this file and that one
disagree, PROJECT_STATE wins. Flag the conflict; don't resolve it silently.

## 1. What this project is

Building validated NNFX trading systems for FX and crypto in Zorro (Light-C), with
Python for analysis. Indicators come from John Ehlers (TASC articles, *Cybernetic Analysis*),
Stonehill Forex and others. No strategy has been backtested yet. Phase 1 builds the pipeline:
indicator harness → NNFX template → backtest-engine checks.

**Sources of truth — read before working on the matching area:**

| Topic | File |
|---|---|
| Current state, Phase 1 steps, known defects | `docs/PROJECT_STATE.md` |
| NNFX rules and template defaults (VP / Stonehill) | `docs/sources/NNFX_Sources.md` |
| Zorro Light-C pitfalls (many are silent) | `docs/ZORRO_LIGHTC_GOTCHAS.md` |
| Indicator code | `indicators/ehlers/*.c` |
| Existing test scripts (most cannot fail — see PROJECT_STATE §4) | `strategies/tests/*.c` |
| Surrogate / null-test harness (Python) | `analysis/null_tests/` |

## 2. Roles and the batch workflow

- **claude.ai project chat:** planning, decisions, research, review.
- **Claude Code (you):** writes code, tests and docs, and reads results.
- **The user:** clicks [Test] in Zorro and decides.

Zorro is the **free edition**. It has no command-line runs: `-run`, `-train`, `-h`, `-quiet`,
`-a`, `-d` and `-i` are Zorro S only. You cannot run Zorro yourself. The loop is:

1. You write one **batch script** that loops internally over indicators / assets / parameter
   sets and writes **all** results to file(s).
2. Before the run, you write down what the user should do (script name, which [Test] click)
   and what output files to expect.
3. The user clicks [Test] once and tells you when it is done.
4. You read the result files and report (see §6). Then you write the next batch.

Design every batch to need exactly one click. If a task seems to need many clicks, say so;
that is the signal for the Zorro S decision.

## 3. Paths

| What | Path |
|---|---|
| Repo | `C:/Users/eyalp/Documents/fx-trading-systems` (Git Bash: `/c/Users/eyalp/...`) |
| Zorro install | `C:/Zorro` (free edition, 2.70+) |
| Zorro runs scripts from | `C:/Zorro/Strategy` |
| Zorro file output (`file_append("Data/x.csv", ...)`) | `C:/Zorro/Data/` (relative to the Zorro install, not the repo) |
| Price history (`.t6`) | Zorro `History/` folder; not in git |

**Repo ↔ Zorro route (user-stated, 2026-11-03).** Zorro's script folder is switched in the
GUI, from the Script dropdown → `[Change Folder]`, so it points directly at the repo folder
that holds the scripts. Nothing is copied into `C:/Zorro/Strategy`.
- Put all scripts in `strategies/tests/` unless the user says otherwise. Zorro lists one
  folder at a time, and scripts there include indicators as
  `#include "../../indicators/ehlers/X.c"` (two levels up to the repo root).
- (c) Inference: Zorro resolves these relative includes from the script's own folder.
  The first harness batch must confirm this (a deliberately wrong include path must fail
  to compile).
- When you hand over a batch, tell the user which folder Zorro must point at, and the exact
  script name to pick in the dropdown.

Python on this machine: use `python`, not `python3`. Open text files with `encoding='utf-8'`.

## 4. Validation gate — non-negotiable

Speed applies to building, never to accepting results.

1. **Dev / confirmation split.**
   - Dev set: `EUR/USD` D1, `BTCUSD` H4, `EUR/JPY` D1, `AUD/USD` D1.
   - Confirmation set: the other majors and crosses, XAU, XAG, WTI (minors excluded).
   - **Never load, run on or read results from a confirmation-set asset.** That set stays
     untouched until a system is frozen and the user says so explicitly.
2. **Pre-registration.** Acceptance criteria are written to a file and committed **before**
   the test runs. Amendments are dated and appended, never edited in place. If no committed
   criteria exist for a test, stop and ask; don't write criteria after seeing results.
3. **Count every variant.** Every indicator / parameter / rule variant run in a batch is
   counted. The count goes in the results file and in the report next to the result.
4. **A guard never seen to fire is not a guard.** Every check you add gets a deliberately
   broken input (wrong asset, NaN, wrong period, etc.), and the report shows it firing.
5. **Test the measuring tool on a known answer first** (e.g. EMA ramp lag = 1.50 bars;
   the known-answer table is in PROJECT_STATE §5).
6. **Same parameters across assets.** No per-asset retuning.
7. **Judge an indicator by what it does**, not by what its article claims.
8. **Failures stay documented.** Never delete or hide a FAIL result.
9. **No single score in place of a trade-off.** Report trade-offs as a table.

A test that cannot fail is not a test. Every harness check needs a numeric tolerance
and an explicit PASS/FAIL. Reaching the end of the run is not a pass.

## 5. Sourcing labels — in code comments and docs

Comments and docs are later read as fact, so label claims:
- **(a)** the source states it (cite: article / video key from NNFX_Sources.md)
- **(b)** measurable / verified here (say how: which test, which file)
- **(c)** inference. Label it, or leave it out.

NNFX rules come from `docs/sources/NNFX_Sources.md`, never from memory. Every NNFX number
there is a **configurable default**. Expose it as a parameter. Changing one is a named,
counted variant. Risk per trade is configurable over 0.3%–2% (default 2%). Dead-market mode is
optional and off by default.

## 6. Light-C rules you will otherwise get wrong

The full list with reasons is in `docs/ZORRO_LIGHTC_GOTCHAS.md`. Re-read it before writing
any indicator or batch script. The ones that fail **silently**:

- Trig takes **radians**. Ehlers' EasyLanguage is in degrees: `360/P` → `2*PI/P`.
  A file with some coefficients converted and others not still gives plausible output.
- **No ternary operator.** `Period` is reserved. Use `void run()`.
- **Flat namespace across includes.** Prefix every global/static (`cc_`, `cyc_`, `rm_`,
  `rmo_`, `ab_`, `mstc_` are taken).
- `series()` slots are allocated by **call order**. Never call a `series()` user inside `if()`.
- **Compute all indicators before `if(is(LOOKBACK)) return;`**
- **Statics persist across [Test] presses** of a loaded script. Reset every static to its
  declared initialiser at `is(INITRUN)`. Use flag-based seeding, not `if(prev == 0)`.
- **`asset()` is not a validity guard** (it runs on a dummy asset). Guard on price magnitude.
  Crypto has no slash: `BTCUSD`, not `BTC/USD`.
- **`quit()` finishes the current bar.** Latch a flag and gate writes on it.
- **`file_append` appends.** Delete or uniquely name the output file at INITRUN, and write
  the header once.
- `LookBack` is auto-extended. Never key logic to `barCount == LookBack + 1`.
- Includes: `#include <default.c>` first, then dependencies in order (single pass).

## 7. Batch script and results conventions

- One results file per batch, CSV, with a header row. Name it
  `<BatchName>_<YYYYMMDD>.csv`. One row per check, with at least:
  `check_id, indicator, params, asset, input, expected, actual, tolerance, result`
  (`result` ∈ PASS / FAIL / ERROR).
- Write a footer or companion line with: batch name, number of variants run, number of
  PASS / FAIL / ERROR. A guard that fires writes an ERROR row; it never just stops.
- Synthetic inputs (flat line, unit sines, ramp) for correctness tests. Real-data checks use
  the committed EUR/USD D1 slices, never stitched together (PROJECT_STATE §5, D-14.1).
- Script header comment: purpose, pre-registration file it implements, inputs, outputs,
  and the expected-value sources with (a)/(b)/(c) labels.
- After reading results, report in this order: what ran (variants counted), PASS/FAIL table,
  what failed and the likely cause, next step. Keep it compact.

## 8. Git and file practice

- **The user runs every git command that changes anything** (`add`, `commit`, `branch`,
  `checkout`, `merge`, `push`, …). You may run read-only git (`status`, `diff`, `log`, `show`)
  to check your work.
- When a change is ready, give the user the exact git commands to run, one step at a time,
  and say why each one is needed. Then wait for their output before giving the next.
- Use a branch per coherent change and one logical change per commit. Commit messages:
  `area: summary` (e.g. `harness: SuperSmoother known-answer checks`).
- Never suggest push --force, rebase or history rewrites unless the user asks.
- Don't commit price data, Zorro `Log/` / `Results/`, or `audit/` (gitignored).
- Prefer editing existing files to creating new ones. Don't delete tracked files;
  propose the deletion instead.

## 9. Stop and ask before

- touching anything in the confirmation set (§4.1)
- writing or changing acceptance criteria, or running a test that has none committed
- changing an NNFX default or a known-answer value
- treating an existing "validated" indicator as verified (it isn't; see PROJECT_STATE §1.1)
- any decision between approaches. Explain the options briefly and pause.

Pause at decisions and results, not at every routine step. Writing a file, a self-check and
preparing a batch can go together.
