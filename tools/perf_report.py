"""PERF1 report: first performance read of Strategy 1 v0 on EUR/USD (criteria: docs/preregistration/PERF1_Strategy1_EURUSD_Criteria.md).

Usage: python tools/perf_report.py --x1 <log> --x2 <log> --sha-x1 <prefix> --sha-x2 <prefix> --history <dir> --out <report.md>

Inputs : two template logs (x1, x2 spread level), their sha256 prefixes, the Zorro History folder.
Output : one Markdown report (written with exclusive-create: an existing file is never overwritten).
Exit   : 0 report written | 2 refused (sha256 mismatch, bad arguments, output exists) |
         3 STOP: a field the criteria need is not in the log (named in the message; nothing is inferred) |
         4 STOP: the log is inconsistent (a guard fired).
Every definition below is from the criteria file (P-1 items 1-13, P-3 verdict, P-4 near-miss); (c) marks the few
places where the criteria leave a detail open and this file had to choose one.

Log rows read (layout as tools/check_r1.py and NNFX_Template.h):
  INFO   asset,0,key=value...            settings (PIP, Tp1Atr, RefusedLog needed here)
  SIZE   asset,ymd, eq,bal,mt,atr,pip,pipcost,lotamount,pct,target,stop_pips,risk_lot,raw,lots,actual,mc,margin
  ENTER  asset,ymd,group,dir,kind,atr
  HALF   asset,group,half,dir,kind,entry_ymd,entry,exit_ymd,exit,reason,flags,bar_open,bar_close,profit,roll,comm,spread,units
  STOP   asset,ymd,group,level,reason     runner stop moves
  ERROR  asset,ymd,reason,message         refusals by the sizing guard (lots / risk / margin)
  RBAR   asset,bar,ymd,wdate,lookback,o,h,l,c
  ACCT   ,bar,ymd,equity,balance,margintotal,margincall
  REFUSED asset,ymd,reason,kind           (NOT IN THE TEMPLATE YET, see missing_fields())

Units. Half-R = TradeProfit / (lots x stop pips x PIPCost), the ACTUAL risk after floor rounding (SIZE row), never the
target. Signal-R = (P&L half 1 + P&L half 2) / (risk half 1 + risk half 2). (a) criteria P-1.
"""
import argparse
import bisect
import collections
import csv
import hashlib
import math
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)      # r1_data (loaded only for the near-miss bars)

VERDICT_EVIDENCE = "CONTINUE — evidence"
VERDICT_NO_EVIDENCE = "CONTINUE — no evidence yet"
VERDICT_STOP = "STOP"
T_MIN = 2.0                                   # P-3 (c): statistical convention, reported with t
KINDS = ("all", "standard", "continuation")   # T9.4
SHIFTS_PIPS = (0.5, 1.0, 2.0)                 # P-4.2
EPS_PIPS = 1e-9                               # tie tolerance of the near-miss comparisons
YEARS_RANGE = tuple(range(2007, 2027))        # P-1 item 12
REASONS = ("c1_flip", "baseline", "stop", "tp1", "be", "trail", "exit_ind", "be_adverse", "end", "other")
REFUSAL_REASONS = (("btf", "bridge-too-far"), ("lots", "below 1 lot"), ("margin", "margin"),
                   ("risk", "risk above configured"))
# exits where the level is hit inside the bar (the exit bar belongs to the half's life); close-decided exits fill
# at the next open, so their exit bar is not part of the life (template: nxt_h1Active counts tp1 / stop only).
LEVEL_EXITS = ("tp1", "stop", "be", "trail")
TOL_REL = 1e-8                                # SIZE row recompute (as check_r1 K1)
TOL_PROFIT_ABS, TOL_PROFIT_REL = 2e-3, 1e-6   # TradeProfit is float32 (as check_r1 K4)
TOL_UNITS_REL = 1e-6


class PerfError(Exception):
    exit_code = 4


class ShaMismatch(PerfError):
    exit_code = 2


class MissingField(PerfError):
    exit_code = 3


class DataError(PerfError):
    exit_code = 4


# ---- sha256 -----------------------------------------------------------------------------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_sha(path, prefix, label):
    """Full digest if the file's sha256 starts with prefix; ShaMismatch otherwise. A short prefix would match too much."""
    p = (prefix or "").strip().lower()
    if len(p) < 8 or any(c not in "0123456789abcdef" for c in p):
        raise ShaMismatch(f"{label}: sha prefix {prefix!r} must be at least 8 hex characters")
    got = sha256_file(path)
    if not got.startswith(p):
        raise ShaMismatch(f"{label}: sha256 of {path} is {got}, expected prefix {p}")
    return got


# ---- log reader -------------------------------------------------------------------------------------------------
def read_log(path):
    L = dict(info={}, size=[], enter=[], half=[], stop=[], error=[], refused=[], acct=[], rbar=collections.defaultdict(dict))
    with open(path, encoding="utf-8", newline="") as f:
        for n, r in enumerate(csv.reader(f), 1):
            if not r:
                continue
            k = r[0]
            try:
                if k == "INFO":
                    L["info"] = dict(x.split("=", 1) for x in r[3:] if "=" in x)
                    L["info_asset"] = r[1]
                elif k == "SIZE":
                    v = [float(x) for x in r[3:19]]
                    if len(v) != 16:
                        raise ValueError("SIZE needs 16 values")
                    L["size"].append(dict(asset=r[1], ymd=int(r[2]), eq=v[0], atr=v[3], pip=v[4], pipcost=v[5],
                                          target=v[8], stop_pips=v[9], risk_lot=v[10], lots=int(v[12]), actual=v[13]))
                elif k == "ENTER":
                    L["enter"].append(dict(asset=r[1], ymd=int(r[2]), group=int(r[3]), dir=int(r[4]), kind=r[5],
                                           atr=float(r[6])))
                elif k == "HALF":
                    if len(r) < 19:
                        raise ValueError("HALF needs 19 fields")
                    L["half"].append(dict(idx=len(L["half"]), asset=r[1], group=int(r[2]), half=int(r[3]), dir=int(r[4]),
                                          kind=r[5], entry_ymd=int(r[6]), entry=float(r[7]), exit_ymd=int(r[8]),
                                          exit=float(r[9]), reason=r[10], profit=float(r[14]), roll=float(r[15]),
                                          comm=float(r[16]), spread=float(r[17]), units=float(r[18])))
                elif k == "STOP":
                    L["stop"].append(dict(asset=r[1], ymd=int(r[2]), group=int(r[3]), level=float(r[4]), reason=r[5]))
                elif k == "ERROR":
                    L["error"].append(dict(asset=r[1], ymd=int(r[2]), reason=r[3]))
                elif k == "REFUSED":
                    L["refused"].append(dict(asset=r[1], ymd=int(r[2]), reason=r[3], kind=r[4]))
                elif k == "ACCT":
                    L["acct"].append(dict(ymd=int(r[3]), eq=float(r[4]), mt=float(r[6])))
                elif k == "RBAR":
                    L["rbar"][r[1]][int(r[3])] = (float(r[7]), float(r[8]))
            except (ValueError, IndexError) as e:
                raise DataError(f"{path} line {n}: bad {k} row ({e})")
    return L


def missing_fields(L):
    """Fields the criteria items need that this log does not carry (nothing is inferred; the run stops on any)."""
    out = []
    info = L["info"]
    if not info:
        out.append("INFO row (settings)")
    if "PIP" not in info:
        out.append("INFO token PIP (price of one pip; P-4 near-miss pip shifts)")
    if "Tp1Atr" not in info:
        out.append("INFO token Tp1Atr (first-target distance in ATR; items 8 same-bar stop+TP1 and P-4 TP1 level): "
                   "no row of the template log holds the TP1 level or its multiple, and the template's own same-bar "
                   "count (nx_aNSameBar) is not logged")
    if info.get("RefusedLog") != "1":
        out.append("INFO token RefusedLog=1 and REFUSED rows asset,ymd,reason,kind (item 11): bridge-too-far skips leave "
                   "no log row, and the ERROR rows of the sizing guard (lots / risk / margin) carry no signal kind, so "
                   "refusals cannot be split into standard / continuation")
    if not L["acct"]:
        out.append("ACCT rows (information-only items: final equity, margin share)")
    return out


# ---- model ------------------------------------------------------------------------------------------------------
def half_risk(size, basis="actual"):
    """Risk of one half in EUR. 'actual' = lots x stop pips x PIPCost (the criteria). 'target' exists only so a test can
    plant the defect 'target risk instead of actual risk' and see the output change."""
    if basis == "target":
        return size["target"]
    return size["lots"] * size["stop_pips"] * size["pipcost"]


def build_model(L, basis="actual"):
    """Join HALF rows to signals (ENTER group) and to their SIZE row; every join is guarded (DataError)."""
    assets = {h["asset"] for h in L["half"]} | {e["asset"] for e in L["enter"]}
    if len(assets) != 1:
        raise DataError(f"expected exactly one asset in the log, found {sorted(assets)}")
    asset = assets.pop()
    sizes = {}
    for z in L["size"]:
        key = (z["asset"], z["ymd"])
        if key in sizes:
            raise DataError(f"two SIZE rows for {key}")
        sizes[key] = z
    enters = {}
    for e in L["enter"]:
        key = (e["asset"], e["group"])
        if key in enters:
            raise DataError(f"two ENTER rows for group {key}")
        enters[key] = e
    by_group = collections.defaultdict(list)
    for h in L["half"]:
        by_group[(h["asset"], h["group"])].append(h)
    for key in by_group:
        if key not in enters:
            raise DataError(f"HALF row(s) of group {key} have no ENTER row")
    moves = collections.defaultdict(list)
    for s in L["stop"]:
        moves[(s["asset"], s["group"])].append((s["ymd"], s["level"]))
    sigs = []
    for key, e in sorted(enters.items(), key=lambda kv: kv[1]["group"]):
        hs = sorted(by_group.get(key, []), key=lambda h: h["half"])
        if [h["half"] for h in hs] != [1, 2]:
            raise DataError(f"group {key}: halves logged {[h['half'] for h in hs]}, need exactly [1, 2] "
                            "(a trade still open or a half missing)")
        z = sizes.get((e["asset"], e["ymd"]))
        if z is None:
            raise DataError(f"group {key}: no SIZE row for decision day {e['ymd']}")
        if z["lots"] < 1:
            raise DataError(f"group {key}: SIZE row has {z['lots']} lots but the signal traded")
        actual = z["lots"] * z["risk_lot"]
        if abs(z["actual"] - actual) > TOL_REL * max(1.0, abs(actual)):
            raise DataError(f"group {key}: SIZE actual {z['actual']} != lots x risk_lot {actual}")
        if abs(z["stop_pips"] * z["pipcost"] - z["risk_lot"]) > TOL_REL * max(1.0, abs(z["risk_lot"])):
            raise DataError(f"group {key}: SIZE risk_lot != stop_pips x PIPCost")
        risk = half_risk(z, basis)
        sg = types.SimpleNamespace(asset=e["asset"], group=e["group"], dir=e["dir"], kind=e["kind"], atr=e["atr"],
                                   size=z, halves={}, risk=0.0)
        for h in hs:
            if h["dir"] != e["dir"] or h["kind"] != e["kind"]:
                raise DataError(f"group {key} half {h['half']}: dir/kind differ from its ENTER row")
            want_units = z["lots"] * z["pipcost"] / z["pip"]
            if abs(h["units"] - want_units) > TOL_UNITS_REL * want_units:
                raise DataError(f"group {key} half {h['half']}: units {h['units']} != lots {z['lots']} x PIPCost / PIP")
            base = h["dir"] * (h["exit"] - h["entry"]) * h["units"]
            want = base - h["spread"] * h["units"] - h["comm"] + h["roll"]
            if abs(h["profit"] - want) > TOL_PROFIT_ABS + TOL_PROFIT_REL * abs(want):
                raise DataError(f"group {key} half {h['half']}: profit {h['profit']} breaks the cost identity ({want})")
            if h["exit_ymd"] < h["entry_ymd"]:
                raise DataError(f"group {key} half {h['half']}: exit before entry")
            hh = types.SimpleNamespace(**h)
            hh.risk = risk
            hh.R = hh.profit / risk
            hh.sig = sg
            hh.moves = sorted(moves.get(key, [])) if h["half"] == 2 else []
            sg.halves[h["half"]] = hh
            sg.risk += risk
        sg.halves = [sg.halves[1], sg.halves[2]]
        sg.pnl = math.fsum(h.profit for h in sg.halves)
        sg.R = sg.pnl / sg.risk
        sg.exit_ymd = max(h.exit_ymd for h in sg.halves)       # (c) a signal closes with its last half
        sg.year = sg.exit_ymd // 10000
        sigs.append(sg)
    # every SIZE row without an ENTER must be a logged refusal (guard)
    entered = {(e["asset"], e["ymd"]) for e in L["enter"]}
    errs = {(r["asset"], r["ymd"]) for r in L["error"]}
    for key in sizes:
        if key not in entered and key not in errs:
            raise DataError(f"SIZE row {key} has neither an ENTER row nor an ERROR row")
    return asset, sigs


def check_refused(L):
    """REFUSED rows must agree with the template's ERROR rows for the sizing reasons (guard)."""
    sizing = [r for r in L["refused"] if r["reason"] in ("lots", "risk", "margin")]
    a = sorted((r["asset"], r["ymd"], r["reason"]) for r in sizing)
    b = sorted((r["asset"], r["ymd"], r["reason"]) for r in L["error"])
    if a != b:
        raise DataError(f"REFUSED rows (lots/risk/margin) {len(a)} differ from ERROR rows {len(b)}")
    for r in L["refused"]:
        if r["reason"] not in dict(REFUSAL_REASONS):
            raise DataError(f"REFUSED row with unknown reason {r['reason']!r}")


# ---- bars: levels, life of a half -------------------------------------------------------------------------------
class BarSet:
    """Daily bars by ymd: (high, low)."""

    def __init__(self, hl):
        self.hl = dict(hl)
        self.days = sorted(self.hl)

    def life(self, half):
        """Days the half was exposed to its levels: entry bar .. exit bar. The exit bar counts only for level exits."""
        if half.entry_ymd not in self.hl or half.exit_ymd not in self.hl:
            raise DataError(f"group {half.sig.group} half {half.half}: no bar for entry {half.entry_ymd} "
                            f"or exit {half.exit_ymd}")
        i = bisect.bisect_left(self.days, half.entry_ymd)
        j = bisect.bisect_right(self.days, half.exit_ymd)
        d = self.days[i:j]
        if half.reason not in LEVEL_EXITS:
            d = [x for x in d if x != half.exit_ymd]
        return d


def stop_distance(sig):
    return sig.size["stop_pips"] * sig.size["pip"]


def tp1_level(half, tp1_atr):
    return half.entry + half.dir * tp1_atr * half.sig.atr


def same_bar(sigs, bars, tp1_atr):
    """Item 8: signals whose half 1 had its stop and its TP1 inside one daily bar (entry bar included), and the half-1
    exit reason (how Zorro resolved it). Same test as the template's nx_aNSameBar, from logged fields only."""
    res = collections.Counter()
    n = 0
    for s in sigs:
        h1 = s.halves[0]
        stop = h1.entry - h1.dir * stop_distance(s)
        tp = tp1_level(h1, tp1_atr)
        hit = False
        for d in bars.life(h1):
            hi, lo = bars.hl[d]
            if h1.dir == 1:
                hit = hit or (lo <= stop and hi >= tp)
            else:
                hit = hit or (hi >= stop and lo <= tp)
        if hit:
            n += 1
            res[h1.reason] += 1
    return dict(count=n, resolved=dict(res))


# ---- statistics (items 1-13) ------------------------------------------------------------------------------------
def max_drawdown(steps):
    """Largest peak-to-trough of the running sum of steps; the peak starts at 0 (c)."""
    cum = peak = dd = 0.0
    for x in steps:
        cum += x
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return dd


def mean(xs):
    return math.fsum(xs) / len(xs) if xs else None


def compute_stats(sigs, refused, bars, tp1_atr):
    S = {}
    halves = [h for s in sigs for h in s.halves]
    S["n_signals"], S["n_halves"] = len(sigs), len(halves)
    S["total_R"] = math.fsum(s.R for s in sigs)
    S["mean_R"] = mean([s.R for s in sigs])
    S["mean_half_R"] = mean([h.R for h in halves])
    S["mean_half_R_tp1"] = mean([h.R for h in halves if h.half == 1])
    S["mean_half_R_runner"] = mean([h.R for h in halves if h.half == 2])
    S["wins"] = sum(1 for s in sigs if s.R > 0)
    S["win_rate"] = S["wins"] / len(sigs) if sigs else None
    order = sorted(halves, key=lambda h: (h.exit_ymd, h.idx))     # stepped at each half's close; same day: log order
    S["max_dd"] = max_drawdown([h.profit / h.sig.risk for h in order])
    S["swap_R"] = math.fsum(h.roll / h.sig.risk for h in halves)
    S["swap_pct"] = S["swap_R"] / S["total_R"] * 100.0 if S["total_R"] != 0 else None
    S["spread_R"] = math.fsum(h.spread * h.units / h.sig.risk for h in halves)    # cost, positive
    S["same_bar"] = same_bar(sigs, bars, tp1_atr)
    S["long_tp1"] = sum(1 for h in halves if h.dir == 1 and h.half == 1 and h.reason == "tp1")
    S["exits"] = dict(collections.Counter(h.reason for h in halves))
    S["refused"] = dict(collections.Counter(r["reason"] for r in refused))
    by_year = collections.defaultdict(list)
    for s in sigs:
        by_year[s.year].append(s.R)
    S["by_year"] = {y: math.fsum(v) for y, v in by_year.items()}
    for name, d in (("longs", 1), ("shorts", -1)):
        sel = [s.R for s in sigs if s.dir == d]
        S[name] = (len(sel), math.fsum(sel))
    return S


def in_kind(kind, k):
    if kind == "all":
        return True
    return (k == "continuation") == (kind == "continuation")


# ---- verdict (P-3) ----------------------------------------------------------------------------------------------
def verdict(signals):
    """signals: list of (signal-R, exit calendar year). All signals, continuation included. Returns a dict."""
    n = len(signals)
    if n < 2:
        raise DataError("verdict needs at least 2 signals")
    rs = [r for r, _ in signals]
    m = math.fsum(rs) / n
    sd = math.sqrt(math.fsum((r - m) ** 2 for r in rs) / (n - 1))
    if sd == 0:
        t = math.inf if m > 0 else (-math.inf if m < 0 else 0.0)
    else:
        t = m / (sd / math.sqrt(n))
    by_year = collections.defaultdict(list)
    for r, y in signals:
        by_year[y].append(r)
    year_R = {y: math.fsum(v) for y, v in by_year.items()}
    best = min(year_R, key=lambda y: (-year_R[y], y))          # highest total R; a tie goes to the earliest year (c)
    total = math.fsum(rs)
    excl = math.fsum(r for r, y in signals if y != best)
    if m <= 0 or excl <= 0:
        v = VERDICT_STOP
    elif t >= T_MIN:
        v = VERDICT_EVIDENCE
    else:
        v = VERDICT_NO_EVIDENCE
    return dict(n=n, mean=m, sd=sd, t=t, total=total, best_year=best, best_year_R=year_R[best], total_excl=excl,
                verdict=v)


# ---- P-4 near-miss ----------------------------------------------------------------------------------------------
def margins(half, bars, pip, tp1_atr):
    """Per level of one half: signed margins in pips over its life, one per bar. margin > 0: the bar stayed short of the
    level by that many pips; margin <= 0: the level was crossed, overshoot = -margin. Returns (stop list, tp1 list)."""
    d = half.dir
    stop0 = half.entry - d * stop_distance(half.sig)
    tp = tp1_level(half, tp1_atr) if half.half == 1 else None
    st, tl = [], []
    for day in bars.life(half):
        hi, lo = bars.hl[day]
        lvl = stop0
        for ymd, level in half.moves:                     # a runner stop moved at a close applies from the next bar
            if ymd < day:
                lvl = level
        st.append(((lo - lvl) if d == 1 else (lvl - hi)) / pip)
        if tp is not None:
            tl.append(((tp - hi) if d == 1 else (lo - tp)) / pip)
    return st, tl


def would_flip(ms, s):
    """A shift of s pips (either way) changes the level's outcome on some bar: an uncrossed bar within s of the level,
    or a crossing bar whose overshoot is smaller than s."""
    return any(-s + EPS_PIPS < m <= s + EPS_PIPS for m in ms)


def near_miss(sigs, bars, pip, tp1_atr, shifts=SHIFTS_PIPS):
    res = dict(halves=0, flips={s: dict(stop=0, tp1=0, either=0) for s in shifts}, stop_min_gap=None, tp1_min_gap=None,
               stop_crossed=0, tp1_crossed=0, stop_min_over=None, tp1_min_over=None)
    for sg in sigs:
        for h in sg.halves:
            st, tl = margins(h, bars, pip, tp1_atr)
            res["halves"] += 1
            for s in shifts:
                a, b = would_flip(st, s), would_flip(tl, s)
                res["flips"][s]["stop"] += a
                res["flips"][s]["tp1"] += b
                res["flips"][s]["either"] += a or b
            for name, ms in (("stop", st), ("tp1", tl)):
                gaps = [m for m in ms if m > 0]
                if gaps:
                    g = min(gaps)
                    cur = res[name + "_min_gap"]
                    res[name + "_min_gap"] = g if cur is None else min(cur, g)
                over = [-m for m in ms if m <= 0]
                if over:
                    res[name + "_crossed"] += 1
                    o = over[0]                                # the first crossing bar (list is in time order)
                    cur = res[name + "_min_over"]
                    res[name + "_min_over"] = o if cur is None else min(cur, o)
    return res


# ---- history ----------------------------------------------------------------------------------------------------
def history_stem(asset):
    return asset.replace("/", "")


def history_files(history, asset, y0, y1):
    """(path, sha256) of every <stem>_<year>.t6 of the log's range. A missing year is a DataError."""
    out = []
    for y in range(y0, y1 + 1):
        p = os.path.join(history, f"{history_stem(asset)}_{y}.t6")
        if not os.path.exists(p):
            raise DataError(f"history file missing: {p}")
        out.append((p, sha256_file(p)))
    return out


def load_history_bars(history, asset, y0, y1):
    """Daily (high, low) by ymd from the M1 history with the fixed bar rule of R1 (r1_data.BAR_RULE)."""
    import r1_data as D
    m1 = D.load_m1(history, stem=history_stem(asset), years=range(y0, y1 + 1))
    b = D.daily_bars(m1, edge=D.BAR_RULE[0], friday=D.BAR_RULE[1])
    return BarSet({D.ymd_int(d): (float(h), float(l)) for d, h, l in zip(b["day"], b["h"], b["l"])})


# ---- report -----------------------------------------------------------------------------------------------------
def f4(x):
    return "n/a (none)" if x is None else f"{x:+.4f}"


def f2(x):
    return "n/a" if x is None else f"{x:.2f}"


def item_rows(S, years, reasons):
    """(label, text) rows of items 1-13 for one subset; the labels are the same for every subset."""
    sb = S["same_bar"]
    rows = [
        ("1 signals", str(S["n_signals"])),
        ("1 halves", str(S["n_halves"])),
        ("2 total R (signal-R)", f4(S["total_R"])),
        ("2 mean R per signal", f4(S["mean_R"])),
        ("3 mean R per half (all)", f4(S["mean_half_R"])),
        ("3 mean R, TP1 half", f4(S["mean_half_R_tp1"])),
        ("3 mean R, runner half", f4(S["mean_half_R_runner"])),
        ("4 win rate (signals, net R > 0)", "n/a (none)" if S["win_rate"] is None else f"{S['win_rate'] * 100:.1f}% ({S['wins']}/{S['n_signals']})"),
        ("5 max drawdown, closed halves (signal-R)", f"{S['max_dd']:.4f}"),
        ("6 swap, summed (R)", f4(S["swap_R"])),
        ("6 swap, % of total net R", "n/a (total R = 0)" if S["swap_pct"] is None else f"{S['swap_pct']:+.2f}%"),
        ("7 spread cost, summed (R, cost positive)", f"{S['spread_R']:.4f}"),
        ("8 same-bar stop + TP1, signals", str(sb["count"])),
        ("8 ... resolved by half-1 exit", ", ".join(f"{k} {v}" for k, v in sorted(sb["resolved"].items())) or "none"),
        ("9 long TP1 halves", str(S["long_tp1"])),
    ]
    rows += [(f"10 exit reason: {r}", str(S["exits"].get(r, 0))) for r in reasons]
    rows += [(f"11 refused: {name}", str(S["refused"].get(code, 0))) for code, name in REFUSAL_REASONS]
    rows += [(f"12 total R, exit year {y}", f4(S["by_year"][y]) if y in S["by_year"] else "0 (no signal)") for y in years]
    rows += [("13 longs: count, total R", f"{S['longs'][0]}, {f4(S['longs'][1])}"),
             ("13 shorts: count, total R", f"{S['shorts'][0]}, {f4(S['shorts'][1])}")]
    return rows


def render(run, hist_files, nm):
    """run: dict level -> dict(path, sha, stats{kind: S}, verdict, acct, nm). Returns Markdown text."""
    years = sorted(set(YEARS_RANGE) | {y for lv in run.values() for S in lv["stats"].values() for y in S["by_year"]})
    reasons = list(REASONS) + sorted({r for lv in run.values() for S in lv["stats"].values() for r in S["exits"]
                                      if r not in REASONS})
    o = ["# PERF1 read 1 — Strategy 1 v0 on this EUR/USD feed", "",
         "Criteria: `docs/preregistration/PERF1_Strategy1_EURUSD_Criteria.md` (P-1 table, P-3 verdict, P-4). "
         "Not a result about EUR/USD in general (P-4.1).", "",
         "## What ran", "",
         "- Variants counted: **1** (Strategy 1, variant 0, EUR/USD). x1 / x2 are reporting levels, not variants (P-3).",
         "- Computed by `tools/perf_report.py` from two template logs; half-R and signal-R use the ACTUAL risk "
         "(lots x stop pips x PIPCost, SIZE row).", ""]
    for lv in ("x1", "x2"):
        o.append(f"- {lv} log: `{run[lv]['path']}`, sha256 `{run[lv]['sha']}`")
    o += ["", "## Verdict (spread x2, P-3)", ""]
    v = run["x2"]["verdict"]
    o += [f"**{v['verdict']}**", "",
          f"- signals n = {v['n']}, mean signal-R = {v['mean']:+.6f}, sample sd = {v['sd']:.6f}, **t = {v['t']:.4f}** "
          f"(rule t >= {T_MIN:g}, (c) a convention)",
          f"- total R = {v['total']:+.4f}; best year (exit year) = {v['best_year']} with {v['best_year_R']:+.4f}; "
          f"total R with the best year removed = {v['total_excl']:+.4f}",
          f"- x1 for reading only (not decisive): t = {run['x1']['verdict']['t']:.4f}, mean = "
          f"{run['x1']['verdict']['mean']:+.6f}, total R without best year = {run['x1']['verdict']['total_excl']:+.4f} "
          f"(would read: {run['x1']['verdict']['verdict']})", "",
          "## Items 1-13 (all signals / standard only / continuation only; x1 and x2)", ""]
    head = ["Item"] + [f"{k} {lv}" for k in KINDS for lv in ("x1", "x2")]
    o.append("| " + " | ".join(head) + " |")
    o.append("|" + "---|" * len(head))
    cols = {(k, lv): item_rows(run[lv]["stats"][k], years, reasons) for k in KINDS for lv in ("x1", "x2")}
    base = cols[("all", "x1")]
    for i, (label, _) in enumerate(base):
        o.append("| " + " | ".join([label] + [cols[(k, lv)][i][1] for k in KINDS for lv in ("x1", "x2")]) + " |")
    o += ["", "Item 10 counts halves. Item 12: calendar year of the signal's last exit (c: the criteria say 'year of the "
          "exit'; a signal is placed whole in the year its last half closed). Item 5: the running sum of "
          "half-R x its share of signal risk, in log order within a day, peak starts at 0 (c).", "",
          "## Information only (never used in a verdict)", "",
          "| | x1 | x2 |", "|---|---|---|"]
    o.append("| final equity (EUR, 2025-07-28 rates, M-D8.4), last ACCT row | " + " | ".join(
        f"{run[lv]['acct']['final_eq']:.2f}" for lv in ("x1", "x2")) + " |")
    o.append("| max MarginTotal / Equity | " + " | ".join(f"{run[lv]['acct']['max_margin']:.4f}" for lv in ("x1", "x2")) + " |")
    o += ["", "## P-4 near-miss table (information only; counts possible flips, R is not recomputed)", "",
          "Daily bars from the M1 history (r1_data, bar rule of R1). Margin = pips between a bar's extreme and the level, "
          "over the half's life (entry bar to exit bar; the exit bar only for level exits). A half 'could flip' under a "
          "shift of s pips when some bar stayed within s of a level without crossing it, or crossed it by less than s.", "",
          "| level | halves | " + " | ".join(f"flip at {s:g} pip: stop / TP1 / either" for s in SHIFTS_PIPS)
          + " | closest uncrossed (stop / TP1, pips) | crossed halves (stop / TP1) | smallest overshoot (stop / TP1, pips) |",
          "|" + "---|" * (5 + len(SHIFTS_PIPS))]
    for lv in ("x1", "x2"):
        n = run[lv]["nm"]
        cells = [f"{n['flips'][s]['stop']} / {n['flips'][s]['tp1']} / {n['flips'][s]['either']}" for s in SHIFTS_PIPS]
        o.append("| " + " | ".join([lv, str(n["halves"])] + cells + [
            f"{f2(n['stop_min_gap'])} / {f2(n['tp1_min_gap'])}", f"{n['stop_crossed']} / {n['tp1_crossed']}",
            f"{f2(n['stop_min_over'])} / {f2(n['tp1_min_over'])}"]) + " |")
    o += ["", "## History files used (P-4.1)", "", "| file | sha256 |", "|---|---|"]
    o += [f"| `{os.path.basename(p)}` | `{h}` |" for p, h in hist_files]
    o += ["", "## Limitations (c)", "",
          "- Drawdown is on closed trades only; drawdown inside an open trade is not counted, so the real one can be deeper.",
          "- When total net R is near 0 the swap % is large and unstable; read the swap sum in R.",
          "- The t formula treats signals as independent; a runner can overlap the next signal.",
          "- Disclosure (P-2): the outcomes of 10 R1a trades were seen in Phase 1 step 5; this read is not fully blind.", ""]
    return "\n".join(o)


# ---- orchestration ----------------------------------------------------------------------------------------------
def analyse(path, sha, history_bars, label, basis="actual"):
    L = read_log(path)
    info = L["info"]
    tp1_atr, pip = float(info["Tp1Atr"]), float(info["PIP"])
    check_refused(L)
    asset, sigs = build_model(L, basis)
    if not sigs:
        raise DataError(f"{label}: no signals in the log")
    bars = BarSet(L["rbar"][asset])
    stats = {}
    for k in KINDS:
        stats[k] = compute_stats([s for s in sigs if in_kind(k, s.kind)], [r for r in L["refused"] if in_kind(k, r["kind"])],
                                 bars, tp1_atr)
    ver = verdict([(s.R, s.year) for s in sigs])
    acct = dict(final_eq=L["acct"][-1]["eq"], max_margin=max((a["mt"] / a["eq"] for a in L["acct"] if a["eq"] > 0), default=0.0))
    nm = near_miss(sigs, history_bars, pip, tp1_atr)
    return asset, dict(path=path, sha=sha, stats=stats, verdict=ver, acct=acct, nm=nm)


def log_years(path):
    """First and last calendar year of the log's RBAR rows (the range its bars cover)."""
    L = read_log(path)
    days = [d for per in L["rbar"].values() for d in per]
    if not days:
        raise DataError(f"{path}: no RBAR rows")
    return min(days) // 10000, max(days) // 10000


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for a in ("--x1", "--x2", "--sha-x1", "--sha-x2", "--history", "--out"):
        ap.add_argument(a, required=True)
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        if os.path.exists(args.out):
            raise ShaMismatch(f"refusing to overwrite {args.out}")          # results are never overwritten
        shas = {"x1": verify_sha(args.x1, args.sha_x1, "x1"), "x2": verify_sha(args.x2, args.sha_x2, "x2")}
        paths = {"x1": args.x1, "x2": args.x2}
        miss = [f"{lv}: {m}" for lv in ("x1", "x2") for m in missing_fields(read_log(paths[lv]))]
        if miss:
            raise MissingField("STOP, the log lacks fields the criteria need (nothing was inferred):\n  - " + "\n  - ".join(miss))
        ranges = {log_years(p) for p in paths.values()}
        y0, y1 = min(r[0] for r in ranges), max(r[1] for r in ranges)
        run, assets = {}, set()
        asset0 = None
        hist = None
        for lv in ("x1", "x2"):
            if hist is None:
                asset0 = build_model(read_log(paths[lv]))[0]
                hist = load_history_bars(args.history, asset0, y0, y1)
            asset, run[lv] = analyse(paths[lv], shas[lv], hist, lv)
            assets.add(asset)
        if len(assets) != 1:
            raise DataError(f"x1 and x2 logs are for different assets {sorted(assets)}")
        text = render(run, history_files(args.history, asset0, y0, y1), None)
        with open(args.out, "x", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except PerfError as e:
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        return e.exit_code
    print(f"wrote {args.out}; verdict at x2: {run['x2']['verdict']['verdict']}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
