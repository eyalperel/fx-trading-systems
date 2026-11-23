"""S4 engine equivalence: compare the Zorro template's trade log with the reference engine.

Usage: python tools/compare_equivalence.py <zorro_log.csv> <expected_dir> <results.csv>
Exit code 0 = run PASS, 1 = run FAIL.

Criteria: docs/preregistration/TPL_Equivalence_Criteria.md (committed before the run). The
constants below are those criteria in code; changing one after the run is an amendment.

Zorro log: rows written by strategies/template/NNFX_Template.h and strategies/tests/TPL_Equivalence.c
  HALF,asset,group,half,dir,kind,entry_ymd,entry,exit_ymd,exit,reason,flags,bar_open,bar_close
  INFO,asset,i,rows=..,vol=..,btf=..,cont=..,mut=..,list=..,Fill=..,Hedge=..,TICKS=..,BarOffset=..
  CNT,asset,bar,same_bar,be_adverse     (every bar; the last row per asset counts)
  OPEN,asset,bar,group,half,pending,entry,stop   (every bar; rows of the last bar = never closed)
  ERROR,... / ASSETFAIL,...             (any one fails the run)
Expected: expected_SYN_<name>.csv (reference engine) and expected_counts.csv (make_scenarios.py).
"""
import csv
import os
import sys

PRICE_TOL = 1e-5   # criteria C3: fills overshoot a level by <= STEP = 1e-5 (make_scenarios, Amendment 4)
# Documented differences (criteria C5): with TICKS, Zorro follows the stated intraday path; the engine
# sees daily OHLC and applies stop-first (T5.2, T5 amendment). On the high-first A3 day (and its
# mirror) Zorro takes TP1 on half 1 first, then stops the runner on the same bar. These are the
# predicted Zorro trades for those halves, replacing the engine's.
DOC_DIFF = {
    ("A3HF", 1): ("tp1", 1.0100), ("A3HF", 2): ("stop", 0.9850),
    ("A3HFM", 1): ("tp1", 0.9900), ("A3HFM", 2): ("stop", 1.0150),
}
SETUP = {"Fill": "3", "Hedge": "2", "TICKS": "1", "BarOffset": "1020", "StartWeek": "71700"}   # C1 (+ Amendment 1)


def ymd_to_iso(v):
    v = str(v)
    return f"{v[0:4]}-{v[4:6]}-{v[6:8]}"


def read_log(path):
    log = dict(half={}, info={}, cnt={}, open_last={}, errors=[], last_bar=-1)
    open_rows = []
    with open(path, encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row:
                continue
            k = row[0]
            if k == "HALF":
                a = row[1].replace("SYN_", "", 1)
                log["half"].setdefault(a, []).append(dict(
                    group=int(row[2]), half=int(row[3]), dir=int(row[4]), kind=row[5],
                    entry_day=ymd_to_iso(row[6]), entry=float(row[7]), exit_day=ymd_to_iso(row[8]),
                    exit=float(row[9]), reason=row[10], flags=int(row[11])))
            elif k == "INFO":
                a = row[1].replace("SYN_", "", 1)
                log["info"][a] = dict(x.split("=", 1) for x in row[3:] if "=" in x)
            elif k == "CNT":
                a = row[1].replace("SYN_", "", 1)
                log["cnt"][a] = (int(row[3]), int(row[4]))
                log["last_bar"] = max(log["last_bar"], int(row[2]))
            elif k == "OPEN":
                open_rows.append((row[1].replace("SYN_", "", 1), int(row[2])))
            elif k in ("ERROR", "ASSETFAIL"):
                log["errors"].append(",".join(row))
    for a, bar in open_rows:
        if bar == log["last_bar"]:
            log["open_last"][a] = log["open_last"].get(a, 0) + 1
    return log


def read_expected(d):
    counts, exp = {}, {}
    with open(os.path.join(d, "expected_counts.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            counts[r["scenario"]] = r
    for name in counts:
        with open(os.path.join(d, f"expected_SYN_{name}.csv"), encoding="utf-8") as f:
            exp[name] = [dict(half=int(r["half"]), dir=int(r["dir"]), kind=r["kind"], entry_day=r["entry_day"],
                              entry=float(r["entry"]), exit_day=r["exit_day"], exit=float(r["exit"]),
                              reason=r["reason"]) for r in csv.DictReader(f)]
    return counts, exp


def compare_scenario(name, exp, got, counts, cnt, info, open_n):
    """Rows (scenario, check, status, expected, got) for one scenario. status PASS / FAIL / DOC."""
    rows = []

    def chk(check, ok, e, g, status_ok="PASS"):
        rows.append((name, check, status_ok if ok else "FAIL", e, g))

    base = name.split("_C")[0]
    chk("info_present", info is not None, "INFO row", "missing" if info is None else "ok")
    if info is not None:
        chk("states_rows", info.get("rows") == counts["bars"], counts["bars"], info.get("rows"))
        for k, v in SETUP.items():
            chk(f"setup_{k}", info.get(k) == v, v, info.get(k))
    got = sorted(got, key=lambda x: (x["group"], x["half"]))
    chk("n_halves", len(got) == len(exp), len(exp), len(got))
    for j, (e, g) in enumerate(zip(exp, got)):
        tag = f"h{j}"
        chk(f"{tag}_half", e["half"] == g["half"], e["half"], g["half"])
        chk(f"{tag}_dir", e["dir"] == g["dir"], e["dir"], g["dir"])
        chk(f"{tag}_kind", e["kind"] == g["kind"], e["kind"], g["kind"])
        chk(f"{tag}_entry_day", e["entry_day"] == g["entry_day"], e["entry_day"], g["entry_day"])
        chk(f"{tag}_entry", abs(e["entry"] - g["entry"]) <= PRICE_TOL, repr(e["entry"]), repr(g["entry"]))
        if e["reason"] == "end":   # C4: closed at the end of history: compared on entry only
            rows.append((name, f"{tag}_exit", "ENTRY_ONLY", "end", g["reason"]))
            continue
        doc = DOC_DIFF.get((base, e["half"]))
        if doc is not None:       # C5: documented TICKS-order difference
            ok = g["reason"] == doc[0] and abs(g["exit"] - doc[1]) <= PRICE_TOL and g["exit_day"] == e["exit_day"]
            chk(f"{tag}_docdiff", ok, f"{doc[0]}@{doc[1]} (engine {e['reason']}@{e['exit']})",
                f"{g['reason']}@{g['exit']}", status_ok="DOC")
            continue
        chk(f"{tag}_reason", e["reason"] == g["reason"], e["reason"], g["reason"])
        chk(f"{tag}_exit_day", e["exit_day"] == g["exit_day"], e["exit_day"], g["exit_day"])
        chk(f"{tag}_exit", abs(e["exit"] - g["exit"]) <= PRICE_TOL, repr(e["exit"]), repr(g["exit"]))
    for g in got:
        chk(f"g{g['group']}h{g['half']}_reason_known", g["reason"] != "other", "not other", g["reason"])
    same_ok = cnt is not None and cnt[0] == int(counts["same_bar_conflicts"])
    chk("same_bar_count", same_ok, counts["same_bar_conflicts"], None if cnt is None else cnt[0])
    bead_ok = cnt is not None and cnt[1] == int(counts["be_adverse_exits"])
    chk("be_adverse_count", bead_ok, counts["be_adverse_exits"], None if cnt is None else cnt[1])
    chk("none_open_at_end", open_n == 0, 0, open_n)
    return rows


def evaluate(log, counts, exp):
    """All rows plus the run verdict (C6): every real scenario PASS (DOC / ENTRY_ONLY allowed),
    every control with at least one FAIL row, no ERROR / ASSETFAIL row."""
    rows, real_ok, ctl = [], True, {}
    for err in log["errors"]:
        rows.append(("RUN", "error_row", "FAIL", "none", err))
    for name in counts:
        r = compare_scenario(name, exp[name], log["half"].get(name, []), counts[name],
                             log["cnt"].get(name), log["info"].get(name), log["open_last"].get(name, 0))
        fails = sum(1 for x in r if x[2] == "FAIL")
        if int(counts[name]["mutation"]) != 0:
            ctl[name] = fails
            r = [(n, c, "CTL_" + s, e, g) for (n, c, s, e, g) in r]
            rows.append((name, "control_detected", "PASS" if fails > 0 else "FAIL", ">= 1 FAIL row", fails))
        elif fails:
            real_ok = False
        rows.extend(r)
    ok = real_ok and all(v > 0 for v in ctl.values()) and not log["errors"]
    return rows, ok, ctl


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    log = read_log(argv[0])
    counts, exp = read_expected(argv[1])
    rows, ok, ctl = evaluate(log, counts, exp)
    with open(argv[2], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "check", "status", "expected", "got"])
        w.writerows(rows)
    real = [n for n in counts if int(counts[n]["mutation"]) == 0]
    bad = sorted({r[0] for r in rows if r[2] == "FAIL" and r[0] in real})
    print(f"real scenarios: {len(real) - len(bad)}/{len(real)} PASS"
          + (f"; FAIL: {', '.join(bad)}" if bad else ""))
    print("controls: " + ", ".join(f"{k} {'DETECTED' if v else 'NOT DETECTED'} ({v} FAIL rows)" for k, v in ctl.items()))
    print(f"DOC rows: {sum(1 for r in rows if r[2] == 'DOC')}, ENTRY_ONLY rows: {sum(1 for r in rows if r[2] == 'ENTRY_ONLY')}, "
          f"error rows: {len(log['errors'])}")
    print("RUN " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
