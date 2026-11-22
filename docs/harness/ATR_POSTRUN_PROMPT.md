# ATR run 1 — checker (read 2 of 2), comparison with the prediction, Amendment 2 draft

Planning chat, 2026-11-22. Branch `harness-atr`. The run is done (user click, Zorro restarted; no `Error` line). Raw copy
`C:/Zorro/Data/GEN_ATR_raw_run1.csv`, sha256 `4f22e7c1834f1c72637f89a733c8e5e3557b76d1a1f54e2c791e32a03f22a441` (verify it first; a
mismatch = STOP). The planning chat's prediction (read 1) is committed BEFORE this step: `348838b`, `docs/harness/ATR_RUN1_PREDICTION.md`
(+ `ATR_RUN1_BACKCHECK.py`, `_output.txt`). Do NOT edit those three files. Run on **Sonnet, effort Medium**. Do NOT commit; do NOT run Zorro.

1. Run the checker: `python analysis/harness/checker.py analysis/harness/specs/ATR_MT4Fidelity.toml C:/Zorro/Data/GEN_ATR_raw_run1.csv`, writing
   the results CSV as the earlier specs did (`analysis/harness/results/ATR_MT4Fidelity_20261122.csv`, run suffix if it exists; never overwrite).
2. Compare with the prediction, row by row where the prediction gives a value: verdict; real-check count and PASS count; per-kind maxima for AT14
   / AT20; floor; every control's FAIL count per kind and max ratio; IMP must_pass values (full precision) and both must_fail values; gated rows.
   Report each as AGREE / DIFFER with both numbers. A difference above ulp level is a finding: explain its cause (prediction side or checker
   side) with evidence; do not change the spec or the prediction to make it agree. A count difference with the same verdict may be a counting
   convention (the prediction states its convention): show it.
3. Draft `[amendment_2]` (post-run record) at the end of the spec, form as FRAMA / MAMA Amendment 2: date, base commit `348838b`, before_run =
   false; A2.1 the run record (Zorro window lines, raw sha256, results file + its sha256, verdict and counts); A2.2 the read-twice comparison
   (agreements, each difference and its cause); A2.3 anything else observed. No criterion, tolerance, table, floor, effect or variant changes.
4. Write `docs/harness/ATR_POSTRUN_REPORT.md` with items 1-3 and the full checker console output. Run `bash analysis/harness/run_tests.sh`
   (TOTAL; tracebacks + rerun on any ERROR). Print `git diff --stat` FIRST, then ONE suggested commit command, and STOP.

Not in this step: the cross-check script (`XCHK_ATRMT4_vs_ATRS`, read after this result is accepted), PROJECT_STATE, HARNESS_DESIGN, merge.
