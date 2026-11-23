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
    """Prepend PAD_BARS neutral bars; baseline / atr repeat the scenario's first value."""
    out = dict(s)
    for k in ("o", "h", "l", "c", "c1", "c2", "vol", "ex"):
        out[k] = [PAD[k]] * PAD_BARS + list(s[k])
    for k in ("baseline", "atr"):
        out[k] = [s[k][0]] * PAD_BARS + list(s[k])
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
}


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


def build(name, start):
    fn, order = SCENARIOS[name]
    s = pad(getattr(T, "s_" + fn)())
    s["order"] = {PAD_BARS + k: v for k, v in order.items()}
    for k in ("o", "h", "l", "c", "baseline", "atr"):
        s[k] = [f32(x) for x in s[k]]
    days = weekdays(start - dt.timedelta(days=7), PAD_BARS + 7)
    days = [d for d in days if d < start][-PAD_BARS:] + weekdays(start, len(s["o"]) - PAD_BARS)
    return s, days


def write(name, s, days, zorro, out):
    hist = os.path.join(zorro, "History")
    n = len(days)
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
    return res


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zorro", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("names", nargs="+")
    a = ap.parse_args(argv)
    start = dt.date.fromisoformat(a.start)
    for name in a.names:
        s, days = build(name, start)
        res = write(name, s, days, a.zorro, a.out)
        print(f"SYN_{name}: {len(days)} bars {days[0]}..{days[-1]}, {len(res.halves)} expected halves")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
