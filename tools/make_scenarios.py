"""Write S2 scenarios as Zorro inputs (stage S3/S4 of the NNFX template).

For each scenario name (e.g. A2):
  <zorro>/History/SYN_<name>.t6           price bars, T6 structs, newest first
  <zorro>/History/SYN_<name>_states.csv   %w,c1,c2,baseline,atr,vol,ex (newest first)
  <out>/expected_SYN_<name>.csv           reference-engine trades on the same values

Sources: T6 = DATE time (UTC timestamp of the close) + float fHigh, fLow, fOpen, fClose,
fVal, fVol; files in descending time order (Zorro 3.11 manual history.htm; trading.h).
A record must lie strictly inside its bar ("a 10-minute bar ending at 12:00 contains all
ticks ... until 11:59:59.999", barperiod.htm), so each daily record is stamped 16:00
New York, one hour before the 17:00 New York bar end (M-D1).
Prices and states are rounded to float32 before the reference engine runs, so Zorro and
the engine see identical numbers (T6 and dataset fields are float32).

Usage: python tools/make_scenarios.py --zorro C:/Zorro --out <dir> --start 2024-03-06 A2 A3
       (ALL = set d: 30 scenarios + 30 short mirrors + 4 planted-bug controls; --header writes the batch include)
"""
import argparse
import csv
import math
import datetime as dt
import os
import struct
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "analysis", "template"))
sys.path.insert(0, os.path.join(ROOT, "analysis", "template", "tests"))
import reference_engine as E  # noqa: E402
import test_reference_engine as T  # noqa: E402

NY = ZoneInfo("America/New_York")
OLE0 = dt.datetime(1899, 12, 30, tzinfo=dt.timezone.utc)
STAMP_HOUR_NY = 16  # one hour inside the 17:00 New York bar end (M-D1, barperiod.htm)
# Zorro's first bar is a partial bar ending at the first record (probe run 1, 2026-11-22):
# neutral warm-up bars before each scenario absorb it. They cannot signal: price flat above
# the baseline, C1 = -1 (a short would need price below the baseline), C2 = +1.
PAD_BARS = 5
TAIL_BARS = 5
PAD = dict(o=0.9990, h=0.9995, l=0.9985, c=0.9990, c1=-1, c2=1, vol=True, ex=0)


def f32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]


def weekdays(start, n):
    d, out = start, []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def ole(day):
    local = dt.datetime(day.year, day.month, day.day, STAMP_HOUR_NY, tzinfo=NY)
    return (local.astimezone(dt.timezone.utc) - OLE0).total_seconds() / 86400.0


def pad(s):
    """PAD_BARS neutral bars before the scenario; TAIL_BARS flat bars after it.

    Lead: baseline / atr repeat the scenario's first value. Tail (Amendment 5): Zorro closes
    an asset's open trades at the first tick of its last day of history (TPL_Probe runs 3-5),
    so each scenario is followed by flat bars at its last close with its last states; nothing
    new can trigger and the scenario's own days run to completion.
    """
    out = dict(s)
    last_c = s["c"][-1]
    tail = dict(o=last_c, h=last_c, l=last_c, c=last_c)
    for k in ("o", "h", "l", "c"):
        out[k] = [PAD[k]] * PAD_BARS + list(s[k]) + [tail[k]] * TAIL_BARS
    for k in ("c1", "c2", "vol", "ex"):
        out[k] = [PAD[k]] * PAD_BARS + list(s[k]) + [s[k][-1]] * TAIL_BARS
    for k in ("baseline", "atr"):
        out[k] = [s[k][0]] * PAD_BARS + list(s[k]) + [s[k][-1]] * TAIL_BARS
    return out


# Intraday paths (TPL_Probe run 3, 2026-11-22): with one record per day, a Fill = 3 entry
# fills on that day's only tick and the day's range is never checked for stops / targets.
# Real history is M1, so each synthetic day is a path of records stamped at 17:00 New York
# of the previous day plus TICK_HOURS (all inside the bar, M-D1). Record 1 is the open
# (O = H = L = C = open, so a gap from the previous close stays a gap). Records 2-4 are
# segment candles from one path point to the next (O = start, C = end, H / L = span): a
# level inside a segment then fills at the level, not at a jumped price (fill.htm:
# "Max of TakeProfit and Open", "Min of Stop and Open").
# Default order: up day (close >= open) open -> low -> high -> close; down day
# open -> high -> low -> close. ORDER overrides it for named variants. Segments are cut
# into STEP-sized records (Amendment 4).
TICK_HOURS = (1, 6, 12, 23)
# With TICKS, Zorro fills at the price of the record that crosses a level (TPL_Probe run 4),
# so each segment is cut into steps of at most STEP: a fill overshoots its level by <= STEP.
STEP = 0.00001
SCENARIOS = {  # file name -> (scenario function, {scenario bar index: order})
    "A2": ("A2", {}), "A3": ("A3", {}), "A3HF": ("A3", {2: "HF"}), "P1": ("P1", {}),
    "A5": ("A5", {}), "A6": ("A6", {}), "B1": ("B1", {}), "B2": ("B2", {}),
    "C1": ("C1", {}), "C2": ("C2", {}), "C3": ("C3", {}), "A1": ("A1", {}), "A4": ("A4", {}),
    # S4 coverage set d (2026-11-23): the D / E entry-rule scenarios and the reversal R1
    "D1a": ("D1a", {}), "D1b": ("D1b", {}), "D1d": ("D1d", {}), "D2": ("D2", {}),
    "D5": ("D5", {}), "D6": ("D6", {}), "D7a": ("D7a", {}), "D7b": ("D7b", {}), "D7c": ("D7c", {}),
    "D8": ("D8", {}), "D9": ("D9", {}), "E1": ("E1", {}), "E2": ("E2", {}), "E3": ("E3", {}),
    "E4a": ("E4a", {}), "E4b": ("E4b", {}), "R1": ("R1", {}),
}
# Short mirror of every scenario: name + "M" (set d). Prices reflected around 1.0 (p -> 2 - p),
# high / low swapped, states negated (test_reference_engine.mirror, the F2 mirror). Each mirrored
# day gets the reflected intraday order explicitly: by the default rule a day with close == open
# (A3) is low-first in both files, which for the mirror would put the short's TP side first and
# silently turn A3M into the A3HF case.
MIRROR = "M"
TAIL_ENTRIES = []   # filled by check_padding, printed by main
VOLUME_MODE_ID = {"ALWAYS_YES": 0, "ALWAYS_NO": 1, "INDICATOR": 2}   # = nx_VolumeMode (NNFX_Config.h)


# Planted-bug control assets (S4 decision 4, 2026-11-23): the same price / state files as the named
# scenario, run with nx_CtlMutation set for that asset only. Expected trades are the correct ones, so
# the comparator must report FAIL on exactly these assets. Ids = NX_MUT_* in NNFX_Config.h.
MUT_M3, MUT_MF = 1, 2
CONTROLS = {"A6_CM3": ("A6", MUT_M3), "A6M_CM3": ("A6M", MUT_M3),
            "R1_CMF": ("R1", MUT_MF), "R1M_CMF": ("R1M", MUT_MF)}


def all_names():
    return list(SCENARIOS) + [n + MIRROR for n in SCENARIOS] + list(CONTROLS)


def mutation(name):
    return CONTROLS[name][1] if name in CONTROLS else 0


def split(name):
    if name in CONTROLS:
        name = CONTROLS[name][0]
    if name in SCENARIOS:
        return name, False
    if name.endswith(MIRROR) and name[:-1] in SCENARIOS:
        return name[:-1], True
    raise KeyError(name)


def path(o, h, l, c, order):
    if order is None:
        order = "LF" if c >= o else "HF"
    mid = (l, h) if order == "LF" else (h, l)
    return [o, mid[0], mid[1], c]


def tick_times(day):
    prev = dt.datetime(day.year, day.month, day.day, 17, tzinfo=NY) - dt.timedelta(days=1)
    # Monday: day - 1 = Sunday, so Monday's bar starts Sunday 17:00 New York as FX opens
    # (run 4 subtracted the weekend twice; fixed in Amendment 4).
    return [(prev + dt.timedelta(hours=hh)).astimezone(dt.timezone.utc) for hh in TICK_HOURS]


def effective_order(o, c, order):
    return order if order is not None else ("LF" if c >= o else "HF")


def build(name, start):
    """Padded scenario (mirrored if name ends in M), float32 prices, explicit per-bar order."""
    base, mirrored = split(name)
    fn, order = SCENARIOS[base]
    s = pad(getattr(T, "s_" + fn)())
    over = {PAD_BARS + k: v for k, v in order.items()}
    eff = {i: effective_order(s["o"][i], s["c"][i], over.get(i)) for i in range(len(s["o"]))}
    if mirrored:
        s = T.mirror(s)
        s["order"] = {i: ("HF" if v == "LF" else "LF") for i, v in eff.items()}
    else:
        s["order"] = over
    for k in ("o", "h", "l", "c", "baseline", "atr"):
        s[k] = [f32(x) for x in s[k]]
    days = weekdays(start - dt.timedelta(days=7), PAD_BARS + 7)
    days = [d for d in days if d < start][-PAD_BARS:] + weekdays(start, len(s["o"]) - PAD_BARS)
    return s, days


def check_padding(name):
    """Guard: the warm-up / trailing bars must not change any trade of the scenario.

    Engine on the unpadded scenario (as in the unit tests) vs on the padded one: same halves, bars
    shifted by PAD_BARS, same prices (to float32 rounding), same reasons. A half that the unpadded
    run closes as "end" is compared on entry only (the padded run continues into the tail bars).
    Returns a list of differences (empty = pass).
    """
    base, mirrored = split(name)
    fn = SCENARIOS[base][0]
    raw = getattr(T, "s_" + fn)()
    if mirrored:
        raw = T.mirror(raw)
    padded, _ = build(name, dt.date(2024, 3, 6))
    a = T.run(raw).halves
    kw = dict(padded)
    kw.pop("order")
    p = kw.pop("params")
    b = E.run(p=p, **kw).halves
    # Allowed (2026-11-23, found on D6): halves entered in the tail bars, from an entry decided on the
    # scenario's last bar. The unpadded run never fills that order (its history ends), the padded run
    # does; they close as "end" and are compared on entry only in S4. Reported, never silent.
    n_raw = len(raw["o"])
    tail = [y for y in b if y.entry_bar >= PAD_BARS + n_raw]
    TAIL_ENTRIES.extend(f"{name}: half {y.half} dir {y.dir} kind {y.kind} entered in tail at {y.entry}" for y in tail)
    b = [y for y in b if y.entry_bar < PAD_BARS + n_raw]
    if len(a) != len(b):
        return [f"{name}: {len(a)} halves unpadded vs {len(b)} padded (tail entries excluded)"]
    diffs, tol = [], 1e-6
    for x, y in zip(a, b):
        same = (x.dir == y.dir and x.half == y.half and x.kind == y.kind
                and x.entry_bar + PAD_BARS == y.entry_bar and abs(x.entry - y.entry) <= tol)
        if same and x.reason != "end":
            same = (x.reason == y.reason and x.exit_bar + PAD_BARS == y.exit_bar
                    and abs(x.exit_price - y.exit_price) <= tol)
        if not same:
            diffs.append(f"{name}: half {x.half} {x.reason}@{x.exit_bar} vs {y.reason}@{y.exit_bar}")
    return diffs


def write(name, s, days, zorro, out):
    hist = os.path.join(zorro, "History")
    n = len(days)
    nrec = 0
    # One unsplit file per scenario (TPL_Probe runs 1-2, 2026-11-22): a year-split file of
    # daily records was rejected by Zorro 3.11 (Error 047 "no 2024 history"), the unsplit
    # file loaded. Synthetic assets are never mixed with year-split M1 history in a script.
    with open(os.path.join(hist, f"SYN_{name}.t6"), "wb") as f:
        for i in reversed(range(n)):
            pts = path(s["o"][i], s["h"][i], s["l"][i], s["c"][i], s["order"].get(i))
            tts = tick_times(days[i])
            recs = [(tts[0], pts[0], pts[0])]
            for k in range(1, len(pts)):
                a, b = pts[k - 1], pts[k]
                m = max(1, math.ceil(round(abs(b - a) / STEP, 6)))
                for j in range(1, m + 1):
                    t_j = tts[k - 1] + (tts[k] - tts[k - 1]) * j / m
                    recs.append((t_j, f32(a + (b - a) * (j - 1) / m), f32(a + (b - a) * j / m)))
            nrec += len(recs)
            for t_utc, a, b in reversed(recs):
                w = (t_utc - OLE0).total_seconds() / 86400.0
                f.write(struct.pack("<d6f", w, max(a, b), min(a, b), a, b, 0.0, 0.0))
    with open(os.path.join(hist, f"SYN_{name}_states.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date_ole", "c1", "c2", "baseline", "atr", "vol", "ex"])
        for i in reversed(range(n)):
            w.writerow([repr(ole(days[i])), s["c1"][i], s["c2"][i], repr(s["baseline"][i]),
                        repr(s["atr"][i]), int(bool(s["vol"][i])), s["ex"][i]])
    kw = dict(s)
    kw.pop("order")
    p = kw.pop("params")
    res = E.run(p=p, **kw)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, f"expected_SYN_{name}.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "half", "dir", "kind", "entry_day", "entry", "exit_day", "exit", "reason", "pnl"])
        for hf in res.halves:
            w.writerow([name, hf.half, hf.dir, hf.kind, days[hf.entry_bar].isoformat(), repr(hf.entry),
                        days[hf.exit_bar].isoformat(), repr(hf.exit_price), hf.reason, repr(hf.pnl)])
    return res, nrec


def write_header(path, names, start):
    """Generated Light-C include for the equivalence batch: names and per-scenario settings."""
    lines = ["// TPL_Equivalence_Scenarios.h - GENERATED by tools/make_scenarios.py; do not edit.",
             f"// Scenarios written with --start {start.isoformat()}. Settings per scenario come from the",
             "// reference-engine test scenario (test_reference_engine.py); values follow NNFX_Config.h ids.",
             f"int tple_N() {{ return {len(names)}; }}", ""]
    for fn, key in (("tple_name", None), ("tple_volume_mode", "volume_mode"),
                    ("tple_btf_on", "btf_on"), ("tple_cont_after_stop", "cont_after_stop"),
                    ("tple_mutation", "mutation")):
        ret = "string" if key is None else "int"
        lines.append(f"{ret} {fn}(int i)")
        lines.append("{")
        for i, n in enumerate(names):
            base, _ = split(n)
            if key is None:
                v = f'"SYN_{n}"'
            elif key == "mutation":
                v = mutation(n)
            else:
                pv = getattr(getattr(T, "s_" + SCENARIOS[base][0])()["params"], key)
                v = VOLUME_MODE_ID[pv] if key == "volume_mode" else int(bool(pv))
            lines.append(f"\tif(i == {i}) return {v};")
        lines.append('\treturn "";' if key is None else "\treturn -1;")
        lines.append("}")
        lines.append("")
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(lines))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zorro", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--header", help="write the generated Light-C scenario include here")
    ap.add_argument("names", nargs="+", help="scenario names, or ALL (set d: 30 + 30 mirrors + 4 controls)")
    a = ap.parse_args(argv)
    start = dt.date.fromisoformat(a.start)
    names = all_names() if a.names == ["ALL"] else a.names
    bad = [d for n in names for d in check_padding(n)]
    if bad:
        print("PADDING CHANGES TRADES (nothing written):\n  " + "\n  ".join(bad))
        return 1
    for line in TAIL_ENTRIES:
        print("TAIL ENTRY (allowed, compared on entry only): " + line)
    total, last = 0, start
    counts = [["scenario", "halves", "same_bar_conflicts", "be_adverse_exits", "mutation", "bars", "last_day"]]
    for name in names:
        s, days = build(name, start)
        res, nrec = write(name, s, days, a.zorro, a.out)
        counts.append([name, len(res.halves), res.same_bar_conflicts, res.be_adverse_exits, mutation(name),
                       len(days), days[-1].isoformat()])
        total += nrec
        last = max(last, days[-1])
        print(f"SYN_{name}: {len(days)} bars {days[0]}..{days[-1]}, {len(res.halves)} expected halves, {nrec} records")
    with open(os.path.join(a.out, "expected_counts.csv"), "w", newline="") as f:
        csv.writer(f).writerows(counts)
    print(f"{len(names)} scenarios, padding check passed; {total} records = {total * 32 / 1e6:.1f} MB; last day {last}")
    if a.header:
        write_header(a.header, names, start)
        print(f"header: {a.header}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
