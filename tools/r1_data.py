"""R1 data layer (decisions R-D4, R-D6): read Zorro .t6 M1 history and build 17:00 New York daily bars.

Sources (a): T6 record = DATE time (UTC timestamp of the record's close) + float fHigh, fLow, fOpen, fClose, fVal, fVol;
files in descending time order (history.htm, trading.h). A bar "ending at 12:00 contains all ticks ... until
11:59:59.999" (barperiod.htm): a record stamped exactly at the bar end belongs to the NEXT bar. Daily bars end at
BarZone midnight + BarOffset = 17:00 New York (M-D1). BR_WEEKEND (default): no bars between EndWeek (Friday 20:00,
default 52000) and StartWeek (Sunday 17:00, nx_StartWeek 71700, M-D6), "even when they contain price quotes"
(barmode.htm). (c) What Zorro does with quotes inside that window (dropped or folded into the next bar) is not
stated: `weekend_counts()` counts them and `daily_bars(gap=...)` builds both readings.

Vectorised: New York local time from the UTC stamp with the DST transition instants of zoneinfo.
All prices stay float32 values (as Zorro reads them).
"""
import datetime as dt
import os
from zoneinfo import ZoneInfo

import numpy as np

NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
OLE0 = dt.datetime(1899, 12, 30, tzinfo=UTC)
BAR_END = 17.0 / 24.0          # M-D1, as a fraction of a day
REC_DT = np.dtype([("t", "<f8"), ("h", "<f4"), ("l", "<f4"), ("o", "<f4"), ("c", "<f4"), ("val", "<f4"), ("vol", "<f4")])
EPS = 1e-9                     # days (~86 microseconds): OLE stamps of whole minutes are exact to ~1e-10 days


def ole_to_dt(w):
    return OLE0 + dt.timedelta(days=float(w))


def dt_to_ole(d):
    return (d - OLE0).total_seconds() / 86400.0


def load_m1(history, stem="EURUSD", years=range(2005, 2027), report=None):
    """All records of <history>/<stem>_<year>.t6, oldest first (t = OLE days, UTC), repeated records removed.

    (b) 2026-11-23: the EUR/USD files repeat the last 1-2 minutes of every 300-record chunk (download overlap):
    ~1,200 records per year step back in time (to 2017) or repeat a stamp (from 2018). A record is kept only if its
    time is later than every earlier record's; every dropped record must equal, field for field, the kept record
    with the same time (ValueError otherwise). report (dict, optional) receives the counts."""
    parts = []
    for y in years:
        fn = os.path.join(history, f"{stem}_{y}.t6")
        if os.path.exists(fn):
            parts.append(np.fromfile(fn, dtype=REC_DT)[::-1])
    a = np.concatenate(parts)
    runmax = np.maximum.accumulate(a["t"])
    keep = np.ones(len(a), bool)
    keep[1:] = a["t"][1:] > runmax[:-1]
    kept = a[keep]
    drop = a[~keep]
    pos = np.searchsorted(kept["t"], drop["t"])
    pos = np.minimum(pos, len(kept) - 1)
    same = kept["t"][pos] == drop["t"]
    for f in ("h", "l", "o", "c"):
        same &= kept[f][pos] == drop[f]
    if not np.all(same):
        raise ValueError(f"{int((~same).sum())} repeated records differ from the kept record with the same time")
    # R1 Amendment 1 (b, R1a run 1): a record whose close lies outside its own high-low range has the close clipped
    # into it (Good Friday 2007, 15:57: close 1.33759 > high 1.33749; Zorro's bar close = 1.33749). 3 such records.
    kept = kept.copy()
    bad = (kept["c"] > kept["h"]) | (kept["c"] < kept["l"])
    kept["c"] = np.minimum(np.maximum(kept["c"], kept["l"]), kept["h"])
    if report is not None:
        report.update(records=len(a), kept=len(kept), dropped=len(drop), close_clipped=int(bad.sum()))
    return kept


def _ny_offsets(y0=2003, y1=2028):
    """(UTC OLE instants of offset changes, offset in days after each), from zoneinfo."""
    inst, offs = [], []
    t = dt.datetime(y0, 1, 1, tzinfo=UTC)
    end = dt.datetime(y1, 1, 1, tzinfo=UTC)
    prev = None
    while t < end:                                   # hourly scan: NY changes offset on whole UTC hours
        o = t.astimezone(NY).utcoffset().total_seconds() / 86400.0
        if o != prev:
            inst.append(dt_to_ole(t))
            offs.append(o)
            prev = o
        t += dt.timedelta(hours=1)
    return np.array(inst), np.array(offs)


_INST, _OFFS = _ny_offsets()


def ny_local(t):
    """New York local time (OLE days) for UTC OLE stamps t (array)."""
    k = np.searchsorted(_INST, t, side="right") - 1
    return t + _OFFS[k]


def weekday(ole_day):
    """Monday = 0 for integer OLE day numbers (day 0 = 1899-12-30, a Saturday)."""
    return (np.asarray(ole_day, dtype=np.int64) + 5) % 7


def classify(t, edge="next"):
    """Per record: bar day (OLE day number of the New York date whose 17:00 bar holds it), gap flag, Friday-late flag.
    edge = "next": a record stamped exactly 17:00:00 belongs to the next bar (barperiod.htm, (a));
           "same": it closes the bar ending at 17:00 (the alternative; (b) every weekday has one such record)."""
    loc = ny_local(t)
    day = np.floor(loc + EPS).astype(np.int64)
    frac = loc - day
    if edge == "next":
        after = frac >= BAR_END - EPS
    else:
        after = frac > BAR_END + EPS
    bday = day + after
    wd = weekday(day)
    gap = ((wd == 4) & (frac >= 20.0 / 24.0 - EPS)) | (wd == 5) | ((wd == 6) & (frac < BAR_END - EPS))
    fri_late = (wd == 4) & after & ~gap
    return bday, gap, fri_late


def weekend_counts(m1):
    _, gap, fri_late = classify(m1["t"])
    return dict(friday_after_close=int(fri_late.sum()), weekend_gap=int(gap.sum()))


BAR_VARIANTS = (("same", "own"), ("next", "own"), ("next", "drop"), ("next", "monday"))
BAR_RULE = ("same", "own")      # R1 Amendment 1 (b, R1a run 1): the only variant matching Zorro's bars
HOLIDAYS = (101, 1225)          # (a) date.htm: Holidays default { 101, 1225, 0 }; "treated like weekends"


def _fold_holidays(bday, holidays=HOLIDAYS):
    """Bars dated on a holiday (mmdd) do not exist: their records go to the next day that is neither a weekend day nor
    a holiday (R1 Amendment 1; (b) R1a run 1: 2018-01-01, 2023-12-25, 2024-01-01 folded into the next bar)."""
    bday = bday.copy()
    for d in np.unique(bday):
        y, m, dd = _ymd(d)
        if m * 100 + dd not in holidays:
            continue
        nd = d + 1
        while weekday(nd) >= 5 or (lambda q: q[1] * 100 + q[2])(_ymd(nd)) in holidays:
            nd += 1
        bday[bday == d] = nd
    return bday


def daily_bars(m1, gap="drop", edge="same", friday="own", holidays=True):
    """17:00 New York daily bars as a dict of arrays: day (OLE day number), end_ole (UTC), o, h, l, c, i0, i1 (first / last
    record index into m1). gap = "drop": weekend-gap records left out; "fold": kept where their time puts them.
    edge: see classify(). friday (edge "next" only), for records at/after Friday 17:00 (b: 453 records, all exactly 17:00):
    "own" = a bar of their own dated Saturday; "drop" = left out; "monday" = folded into the next Monday bar.
    Alternatives for the R1 bar check (BAR_VARIANTS); the run decides which one Zorro uses."""
    bday, g, fri = classify(m1["t"], edge)
    if holidays:
        bday = _fold_holidays(bday)
    keep = ~g if gap == "drop" else np.ones(len(bday), bool)
    if edge == "next" and friday == "drop":
        keep &= ~fri
    if edge == "next" and friday == "monday":
        bday = bday.copy()
        bday[fri] += 2                                # Saturday -> Monday
    idx = np.nonzero(keep)[0]
    bd = bday[idx]
    starts = np.concatenate(([0], np.nonzero(np.diff(bd))[0] + 1))
    ends = np.concatenate((starts[1:], [len(bd)])) - 1
    rec = m1[idx]
    o = rec["o"][starts].astype(float)
    c = rec["c"][ends].astype(float)
    h = np.maximum.reduceat(rec["h"], starts).astype(float)
    l = np.minimum.reduceat(rec["l"], starts).astype(float)
    days = bd[starts]
    end_ole = np.array([dt_to_ole(dt.datetime(*_ymd(d), 17, tzinfo=NY).astimezone(UTC)) for d in days])
    return dict(day=days, end_ole=end_ole, o=o, h=h, l=l, c=c, i0=idx[starts], i1=idx[ends], keep=keep)


def _ymd(ole_day):
    d = dt.date(1899, 12, 30) + dt.timedelta(days=int(ole_day))
    return d.year, d.month, d.day


def ymd_int(ole_day):
    y, m, d = _ymd(ole_day)
    return y * 10000 + m * 100 + d
