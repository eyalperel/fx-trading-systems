# FSH stage 2 — corrected FisherTransform.c, FisherTransform_Superseded.c, callers, pre-run records (Amendment 1), generated script

Planning chat, 2026-11-19. Branch `harness-fisher`. Tooling `c1c222e`; spec pre-registered at `258b24a`
(`analysis/harness/specs/FSH_ArticleFidelity.toml`). Stage 1 report: `docs/harness/FSH_STAGE1_REPORT.md`. Review:
`docs/harness/FISHER_SOURCE_REVIEW.md` (`bdc83da`). The planning chat back-checked stage 1 before commit: findings 1–8 equal to its
own model; NCS / NCT per-input effects reproduced independently (16 values, 5 decimals, e.g. NCS s100 8.53877, NCT rampdn
9.20075); user decisions: NCT = negative control, NC32 required on trace / bound / ramp_exact; series_len 21 accepted.
User's Git Bash: 719/719 at `c1c222e` (spec present in the working copy).
Labels: (a) source states, (b) measured/computed, (c) inference. Run on **Sonnet, effort Medium**.

**Git:** do NOT commit. At the end print the suggested commands (one commit for the two .c files + the caller updates + their
test, one for Amendment 1 + generated script + this brief; a third only if the generator had to change) and STOP. Do NOT click /
run Zorro.

## 1. Corrected `indicators/ehlers/FisherTransform.c`

Two functions, bodies = `[corrected_code]` lines and wrapper lines of the spec, VERBATIM:
`var FisherCore(vars Price, int Len, var* pRaw, var* pV1, var* pRng, var* pTrig)` then `var FisherTransform(vars Price, int Len)`.
Header (comments only, replaces the whole old header), each statement labelled (a)/(b)/(c) or dropped:
- Source (a): Ehlers, "Using The Fisher Transform", *Technical Analysis of Stocks & Commodities* V.20:11 (2002), pp. 40-42,
  Fig. 5 (EasyLanguage), p. 41. Formula in Light-C terms: Price input (default (H+L)/2), Len (default 10); raw = 2((Price - MinL)/
  (MaxH - MinL) - .5) over the last Len values incl. the current one; Value1 = .33 raw + .67 Value1[1], clamped (> .99 -> .999,
  < -.99 -> -.999: trigger and set value differ, as printed); Fish = .5 ln((1 + Value1)/(1 - Value1)) + .5 Fish[1]; trigger =
  Fish[1]. (a) The book version (*Cybernetic Analysis*, 2004, Fig. 1.7, p. 7: .5 / .5, .9999, .25 ln) is a DIFFERENT indicator;
  not implemented (review §1).
- Deviations fixed (b), review `docs/harness/FISHER_SOURCE_REVIEW.md` (`bdc83da`): F-1 per-instance state (the old `static
  ft_Value1`, `static ft_Fish` and global `ft_Trigger` were shared by every call: a second instance or an asset loop silently
  corrupted every instance, by up to 2.7 in Fish; review §3); F-2 Price is a parameter (the old file read priceHigh() / priceLow()
  itself); F-3 constants built from integers (the old float32 literals moved Fish by up to 1.29e-5); F-7 `FisherCore` exports raw,
  Value1, the range and the trigger; F-8 this header. **Outputs after the first ~100 bars of a single instance on one asset differ
  from the old file only by the F-3 rounding (<= 1.3e-5 on these test inputs); any second instance or asset loop was wrong.**
- Our guard (b, F-4): when MaxH - MinL is not > 0 (flat window), raw = 0 (mid-channel). Not in the source (it divides by zero).
- Caller requirements: pass a series of at least Len values (MaxVal / MinVal read Price[0..Len-1]); for the source's input use
  `series((priceHigh() + priceLow())/2)`. Call unconditionally every bar (gotchas 3.1). Trigger: `FisherCore(..., &trig)` or the
  caller's own Fish[1].
- Start-up: the source defines none (review F-5). Value1 and Fish start at 0 on the instance's first call; the window is padded
  with the first value until Len values exist (gotchas 9d.6). Treat the first ~100 bars as warm-up (the harness uses W = 700).
- (b) Behaviour (review §3; spec observations): raw in [-1, 1]; |Value1| <= .999; |Fish| <= ln(1999) = 7.6004 (reached on a
  steady trend). Fisher SATURATES on long cycles: at T = 100 about two thirds of bars sit at the clamp and Fish at about ±7.6; at
  T = 40, Len 10, 20% of bars. Readings beyond ±2.5 are routine on any cycle with T >= 20 (Len 10). Drop the old "Extreme readings
  (±2.5) are statistically meaningful" claim (unsourced). The Fish feedback is not an EMA: the gain from arctanh(Value1) to Fish
  is 1/(1 - .5) = 2.
- (a) Use stated by the source: Fish crossing its one-bar-delayed trigger identifies cyclic turning points. Not implemented here.
- STATE: no statics; both `series()` calls unconditional and first; each instance has its own state. No includes needed.
- Verification line: `analysis/harness/specs/FSH_ArticleFidelity.toml` (pre-registered `258b24a`). Not verified until that run passes.

## 2. `indicators/ehlers/FisherTransform_Superseded.c` (new; the NCS / NCT control)

The CURRENT `FisherTransform.c` body (blob `259954ed90f4674733f41c46b6694c5f1320cfd0`) with exactly these changes, per the spec's
`[corrected_code].notes`: function `FisherTransform(int Period)` -> `FisherTransform_Superseded(vars Price, int Period)`; line 42's
`series((priceHigh() + priceLow()) * 0.5)` -> the `Price` parameter (the ONLY behavioural edit; keep the name `fto_Mid` as an
alias if that keeps the body unchanged: `vars fto_Mid = Price;`, or replace its uses — say which and why); every `ft_` identifier
-> `fto_` (statics, the global `fto_Trigger`, locals; flat namespace, gotchas 1.3). Statics, literals (.33, .67, .99, .999), the
guard, the clamp, the INITRUN resets and the trigger global all stay. Header: "SUPERSEDED — do not use. Kept as the negative
control NCS / NCT of FSH_ArticleFidelity (F-1 file statics and a global trigger shared by every call; F-3 float32 literals). Only
edit vs the original: the input is a parameter (for synthetic inputs). Corrected file: FisherTransform.c." Report the token diff
vs the old blob (must be renames + input + header only).

## 3. Callers (F-2)

Update the two callers stage 1 found; nothing else:
- `strategies/tests/Test_Fisher_IFT_COG.c:51-52`: build `vars fi_mid = series((priceHigh() + priceLow())/2, <n>);` (n >= the
  Len used, unconditional, before the call; name it with the script's own prefix if one exists) and call
  `FisherCore(fi_mid, 10, &a, &b, &c, &trig)` (or `FisherTransform` plus the caller's own Fish[1]) so `ft_Trigger` is no longer
  read. Keep the script's outputs and column names unchanged.
- `strategies/tests/Test_S1_C2_Audit.c:32`: its `Price` is a CLOSE series built for Reflex — do NOT reuse it. Add a separate
  (H+L)/2 series as above and pass it.
- (c) These scripts are not run in this stage; their outputs change by design (F-1..F-3). Say in the report that they are
  compile-unverified until next used. The roadmap snippets in `docs/roadmap/` stay as they are (history).

## 4. Corrected-code test (new, as `test_lrs_corrected_code.py`)

`analysis/harness/tests/test_fsh_corrected_code.py`:
- `FisherTransform.c` contains the spec's corrected lines inside `FisherCore` and its wrapper lines inside `FisherTransform`
  (whitespace-normalised, comments stripped).
- `FisherTransform_Superseded.c` equals the old blob after the renames and the input edit (comments stripped).
- No `static` in `FisherTransform.c` (the spec's no-static lint, same function); no global `var` outside functions; no decimal
  literal (digits with a `.`) anywhere in the corrected code; no expression starting with a product or quotient of literals (9d.8).
- No caller in the repo still reads `ft_Trigger` or calls `FisherTransform(` with one argument.
- Show the guard firing on temp copies, at least: `static` added before `var fi_hi`; `var fi_a = 33;` -> `var fi_a = 0.33;` (and
  its division removed); `vars fi_V = series(0, 2);` moved inside the `if`; the clamp set value `fi_c` -> `fi_t`; `*pTrig =
  fi_F[1];` -> `*pTrig = fi_F[0];`; a global `var ft_Trigger = 0;` added; in the superseded file, one `fto_` left as `ft_`.

## 5. Generator

(b) Stage 1: the five-column call path, series_len 21 and the per-output checks generate the FSH layout, and a synthetic own-model
raw file gave 56/56 with every control detected. **No generator change is expected.** If one turns out to be needed, it may change
the script layout only (never a criterion, tolerance, table, floor, effect or variant); the 9 existing specs (H1, SS2F, SS3F, HPF,
RFF, USE, RFX, MST, LRSI) must still regenerate as recorded, the full suite must pass, and the change goes in Amendment 1 as A1.2.
If you see a reason the layout is unsafe in Light-C, STOP and report.

## 6. Pre-run conditions (spec pass_condition, pre-run i–v) — all must PASS

- (i) `test_fsh_corrected_code.py` passes on the new files; guard-fire evidence for each broken copy above.
- (ii) old blob `259954ed…cfd0` recorded; the diff old -> new `FisherTransform.c` is only F-1, F-2, F-3, F-7, F-8 (+ the new
  `FisherCore` / wrapper structure): list every other token difference explicitly. Superseded file: renames + input + header only.
- (iii) `test_reference_fsh_spec.py` passes; record the largest deviation per section.
- (iv) `python analysis/harness/generator.py analysis/harness/specs/FSH_ArticleFidelity.toml --lint-only` clean, now including both
  includes resolving and the no-static check passing; record the INFO lines (D2 windows, per-control margins, NCB info, gates,
  L_NO_STATIC).
- (v) no-static lint: 0 hits on the new `FisherTransform.c`; 2 hits (`fto_Value1`, `fto_Fish`) when pointed at the new superseded
  file (seen to fire on the real file, not only on the old blob).
- Full suite: `bash analysis/harness/run_tests.sh` (report TOTAL; tracebacks + rerun on any ERROR, CLAUDE.md §8).

## 7. Amendment 1 (append to the spec; text above unchanged)

Same form as LRSI Amendment 1 (`b85cfd9`): `[amendment_1]` (date, base_commit 258b24a, before_run = true, changes A1.1 = pre-run
records; A1.2 only if §5 needed a generator change; no criterion / tolerance / table / floor / effect / variant changed) +
`[prerun]` cond_i..cond_v, tests_before / tests_after / suite line, blob hashes of FisherTransform.c old (259954ed…) and new,
FisherTransform_Superseded.c new (`git hash-object`). Run note: **restart Zorro before any rerun** (generated scripts return at
INITRUN before any indicator call, so the superseded file's own INITRUN resets never run; a second [Test] press would start NCS /
NCT from the previous run's statics). If ANY criterion would need to change, STOP and report instead.

## 8. Generated script

`python analysis/harness/generator.py analysis/harness/specs/FSH_ArticleFidelity.toml` -> `strategies/tests/GEN_FSH_FisherTransform.c`
(spec `script_name`; report the actual path). Record its sha256 in `[prerun]`. Check by reading the script (report each):
- the two includes in order (FisherTransform_Superseded.c, FisherTransform.c), relative paths as in [zorro].include;
- the 18 input series built from integers before any indicator call, each `series(X[k], 21)`; no decimal literal in the harness
  part; every generated static reset at INITRUN;
- every call unconditional, fixed order: `FisherCore` for FR10 / FR20 on every base input and their invariance copies; the inline
  bodies (NCB, NCW, NCC, NCK, NCL, NC32) present once each, locals uniquely prefixed (NC32's float32 literals are deliberate: report
  them, they are the control); `FisherTransform_Superseded(S, 10)` as NCS on flat … rampdn, then NCT on flat … rampdn (16 calls,
  the order stage 1's replay used); calls per bar = 100; no `Period` identifier outside the superseded file;
- out-parameters through local scalars, copied before the next call;
- raw file `Data/GEN_FSH_raw.csv`, 376 columns, no-overwrite guard; header and rows written before `quit()` (9d.4).
- Confirm the raw file does not exist yet under `C:/Zorro/Data/` (or report it).

## Done when

Write the report as `docs/harness/FSH_STAGE2_REPORT.md`: both .c files (full text), the caller diffs, test summary with guard-fire
evidence, generator change (expected none), pre-run i–v, suite TOTAL before/after, script name + sha256 and the read-through
checks above, any deviation from this brief. Then STOP: no commit, no Zorro run.
