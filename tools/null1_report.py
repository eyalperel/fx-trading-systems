"""NULL1 read (C6): statistics of the null and positive-control runs; writes analysis/null_template/NULL1_report.md.
Usage: python tools/null1_report.py <null_runs.csv> <pc_runs.csv> <sha_null_prefix> <sha_pc_prefix> <out.md>
Refuses on a sha256 mismatch and never overwrites. Real results used: PERF1 / PERF2 at x2 (Zorro, as pre-registered) and,
for transparency, the engine's own x2 results on the real states (V1)."""
import csv
import hashlib
import os
import sys

import numpy as np

REAL = {"F1": (-0.0304, -10.2514 / 325), "F2": (-0.0479, -14.0370 / 282)}   # (PERF x2 Zorro, engine x2 from V1)


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def stats(v):
    v = np.asarray(v, float)
    p = np.percentile(v, [2.5, 5, 50, 95, 97.5])
    return dict(n=len(v), mean=v.mean(), sd=v.std(ddof=1), p2_5=p[0], p5=p[1], p50=p[2], p95=p[3], p97_5=p[4])


def pct_rank(v, x):
    return float(np.mean(np.asarray(v, float) <= x))


def main(argv):
    if len(argv) != 5:
        print(__doc__)
        return 2
    nul, pc, sn, sp, out = argv
    if os.path.exists(out):
        print("refusing to overwrite", out)
        return 2
    for p, pre in ((nul, sn), (pc, sp)):
        if len(pre) < 16 or not sha(p).startswith(pre):
            print("sha256 mismatch", p)
            return 2
    R = list(csv.DictReader(open(nul)))
    P = list(csv.DictReader(open(pc)))
    g = {}
    for r in R:
        g.setdefault((r["set"], r["level"]), []).append(float(r["mean"]))
    sig = {}
    for r in R:
        if r["level"] == "x2":
            sig.setdefault(r["set"], []).append(int(r["signals"]))
    o = ["# NULL1 read 1 — the template's null distribution on EUR/USD D1", "",
         "Criteria: `docs/preregistration/NULL1_TemplateNull_Criteria.md`. Statistic: mean signal-R per run. "
         f"Null runs sha256 `{sha(nul)}`, positive control `{sha(pc)}`.", "",
         "## Null distributions (1,000 circular shifts each)", "",
         "| Set | Level | signals (median) | mean | sd | 2.5% | 5% | 50% | 95% | 97.5% |", "|---|---|---|---|---|---|---|---|---|---|"]
    for s in ("F1", "F2", "O1", "O2"):
        for lv in ("x2", "x0"):
            t = stats(g[(s, lv)])
            o.append(f"| {s} | {lv} | {int(np.median(sig[s]))} | {t['mean']:+.4f} | {t['sd']:.4f} | {t['p2_5']:+.4f} | "
                     f"{t['p5']:+.4f} | {t['p50']:+.4f} | {t['p95']:+.4f} | {t['p97_5']:+.4f} |")
    o += ["", "## F1 / F2: where the real PERF results sit (describe only; PERF1 / PERF2 verdicts unchanged)", "",
          "| Set | Real mean signal-R x2 (Zorro, PERF) | Percentile in null x2 | Engine's own real x2 (V1) | Percentile |",
          "|---|---|---|---|---|"]
    for s in ("F1", "F2"):
        z, e = REAL[s]
        o.append(f"| {s} | {z:+.4f} | {100 * pct_rank(g[(s, 'x2')], z):.1f}% | {e:+.4f} | {100 * pct_rank(g[(s, 'x2')], e):.1f}% |")
    o += ["", "## Positive control (C5; Q1 rule: detected if the carrier >= the null's 95th percentile)", "",
          "| Set | mu (x ATR / bar) | Carrier mean signal-R | Null 95% | Carrier percentile | Detected |", "|---|---|---|---|---|---|"]
    det = {}
    for s in ("O1", "O2"):
        for mu in ("mu0.01", "mu0.02", "mu0.05"):
            rows = [r for r in P if r["set"] == s and r["level"] == mu]
            car = [float(r["mean"]) for r in rows if r["offset"] == "carrier"][0]
            nv = [float(r["mean"]) for r in rows if r["offset"] != "carrier"]
            p95 = np.percentile(nv, 95)
            d = car >= p95
            det[(s, mu)] = d
            o.append(f"| {s} | {mu[2:]} | {car:+.4f} | {p95:+.4f} | {100 * pct_rank(nv, car):.1f}% | {'YES' if d else 'no'} |")
    o += ["", "## Predictions (c) against results", ""]
    cen = {s: stats(g[(s, 'x2')])["p50"] for s in ("F1", "F2")}
    o.append(f"- F1 / F2 null centre x2 in [-0.06, -0.01]: F1 {cen['F1']:+.4f}, F2 {cen['F2']:+.4f} -> "
             f"{'met' if all(-0.06 <= v <= -0.01 for v in cen.values()) else 'NOT met'}")
    inb = {s: 0.05 <= pct_rank(g[(s, 'x2')], REAL[s][0]) <= 0.95 for s in ("F1", "F2")}
    o.append(f"- real PERF results between the 5th and 95th percentile: {'met' if all(inb.values()) else 'NOT met'} ({inb})")
    c0 = {s: stats(g[(s, 'x0')])["p50"] for s in ("F1", "F2", "O1", "O2")}
    o.append("- x0 null centres within +-0.02 of 0: " + ", ".join(f"{k} {v:+.4f}" for k, v in c0.items()) +
             f" -> {'met' if all(abs(v) <= 0.02 for v in c0.values()) else 'NOT met'}")
    o.append(f"- mu 0.05 detected in O1 and O2: {'met' if det[('O1', 'mu0.05')] and det[('O2', 'mu0.05')] else 'NOT met'}")
    o.append(f"- mu 0.01 not detected in at least one: {'met' if not (det[('O1', 'mu0.01')] and det[('O2', 'mu0.01')]) else 'NOT met'}")
    o.append("- mu 0.02: not predicted")
    o += ["", "## Limitations (c)", "",
          "- Circular shifts of one series: neighbouring offsets are correlated; 1,000 runs are fewer independent draws.",
          "- The engine's cost model differs from Zorro on a few halves (V1: M-D7 trigger shifts); medians match exactly.",
          "- One asset, one feed; the positive control's drift is a construct (C5), its R is measured, not a market property.", ""]
    with open(out, "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(o))
    print("\n".join(o))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
