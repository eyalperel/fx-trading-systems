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


def build(name, start):
    s = getattr(T, "s_" + name)()
    for k in ("o", "h", "l", "c", "baseline", "atr"):
        s[k] = [f32(x) for x in s[k]]
    days = weekdays(start, len(s["o"]))
    return s, days


def write(name, s, days, zorro, out):
    hist = os.path.join(zorro, "History")
    n = len(days)
    with open(os.path.join(hist, f"SYN_{name}.t6"), "wb") as f:
        for i in reversed(range(n)):
            f.write(struct.pack("<d6f", ole(days[i]), s["h"][i], s["l"][i], s["o"][i], s["c"][i], 0.0, 0.0))
    with open(os.path.join(hist, f"SYN_{name}_states.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date_ole", "c1", "c2", "baseline", "atr", "vol", "ex"])
        for i in reversed(range(n)):
            w.writerow([repr(ole(days[i])), s["c1"][i], s["c2"][i], repr(s["baseline"][i]),
                        repr(s["atr"][i]), int(bool(s["vol"][i])), s["ex"][i]])
    kw = dict(s)
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
