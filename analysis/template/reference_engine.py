"""NNFX reference engine: an independent Python implementation of the template rules.

Phase 1 step 4, stage S2. Decisions: docs/template/NNFX_TEMPLATE_DECISIONS.md (T1-T11,
M-D1..M-D4); Zorro mechanics: docs/template/ZORRO_TRADE_MECHANICS.md. Purpose: the Zorro
template's trade list must match this engine's on the same inputs (stage S4). It works in
price, pips and R; swap and integer-lot sizing are checked separately (probes P5, P6).

Inputs per bar t: o, h, l, c; baseline[t]; atr[t]; c1[t], c2[t] in {+1, -1, 0} (T3 states;
0 = exactly on the line); vol[t] (bool, used when volume_mode == "INDICATOR");
ex[t] = exit-indicator state (used when exit_mode == "INDICATOR").

Order of events in bar t (T4, T5):
  1. at the open: close-decided exits from bar t-1, then the entry decided at bar t-1
     (both halves, ATR of the signal bar frozen for the trade);
  2. inside the bar: stop before TP1 (Zorro 3.11 stop.htm, T5.2); a gap past a level
     fills at the open (fill.htm, T5.1);
  3. at the close: breakeven / M-D3 check, trailing (closes only), close-decided exits,
     then entry decisions (C1 signal, continuation, baseline cross with catch-up,
     pullback, bridge-too-far).
Optional per-bar inputs for real data (R1, decision R-D6; default None = the daily rules above, unchanged):
  open_fill[t]  price of market fills at the start of bar t (entries and close-decided exits) instead of o[t];
  intrabar(t, halves)  replaces step 2: returns the stop / TP1 events inside bar t in time order as
                (half, fill price, "stop" | "tp"), e.g. from M1 records (tools/r1_replay.py). A half listed
                twice is closed once (first event).
Costs: `spread` (price units) is subtracted once per half (long: exit at bid; short:
entry at bid), the convention of stop.htm "ask/bid" handling; checked in S4 (P5).
"""
import re
from dataclasses import dataclass, field

LONG, SHORT = 1, -1


def sgn(x):
    return (x > 0) - (x < 0)


@dataclass
class Params:
    """Variant 0 defaults; must equal strategies/template/NNFX_Config.h (test enforces)."""
    stop_atr: float = 1.5            # (a) [V25, M3]
    tp1_atr: float = 1.0             # (a) [V25, C17, M13]
    tp1_fraction: float = 0.5        # (a) [V25]; two halves (T8)
    be_offset_atr: float = 0.0       # (a) [M6]
    trail_start_atr: float = 2.0     # (a) [M13]
    trail_dist_atr: float = 1.5      # (a) [M13]
    baseline_max_dist_atr: float = 1.0  # (a) [V28]
    pullback_wait_bars: int = 1      # (a) [V28]
    btf_on: bool = True              # Strategy 1 (T3.3)
    btf_max_age: int = 7             # (a) [V34]; T10
    catchup_limit_on: bool = False   # (c) T10
    catchup_max_bars: int = 3        # sensitivity level only (T11)
    cont_after_stop: bool = True     # (c) T9
    volume_mode: str = "ALWAYS_YES"  # T2; "ALWAYS_NO" guard stub; "INDICATOR"
    exit_mode: str = "NONE"          # T1; "INDICATOR"
    spread: float = 0.0              # price units (T7)
    baseline_mode: str = "on"        # "on" = the template; "off" = C1-only test mode (NULL1 C1, VP's C1 test (a) V05):
                                     # every C1 signal enters; no baseline / C2 / volume / distance / window / BTF; no baseline exit


CONFIG_MAP = {
    "nx_StopAtr": "stop_atr", "nx_Tp1Atr": "tp1_atr", "nx_Tp1Fraction": "tp1_fraction",
    "nx_BeOffsetAtr": "be_offset_atr", "nx_TrailStartAtr": "trail_start_atr",
    "nx_TrailDistAtr": "trail_dist_atr", "nx_BaselineMaxDistAtr": "baseline_max_dist_atr",
    "nx_PullbackWaitBars": "pullback_wait_bars", "nx_BtfMaxAgeBars": "btf_max_age",
    "nx_CatchupLimitOn": "catchup_limit_on", "nx_CatchupMaxBars": "catchup_max_bars",
    "nx_ContAfterStop": "cont_after_stop", "nx_BtfOn": "btf_on",
}


def read_config(path):
    """Evaluate the integer assignments of NNFX_Config.h (`x = n;`, `x /= n;`, `x *= n;`)."""
    vals = {}
    stmt = re.compile(r"\b(nx_\w+)\s*(=|/=|\*=)\s*(\d+)\s*;")
    with open(path, encoding="utf-8") as f:
        for line in f:
            code = line.split("//")[0]
            for name, op, num in stmt.findall(code):
                v = float(num)
                if op == "=":
                    vals[name] = v
                elif op == "/=":
                    vals[name] /= v
                else:
                    vals[name] *= v
    return vals


def signals(states):
    """T3: signal when the state becomes +-1 and the last non-zero state was the opposite."""
    out, last = [], 0
    for s in states:
        out.append(s if (s != 0 and last == -s) else 0)
        if s != 0:
            last = s
    return out


@dataclass
class Half:
    dir: int
    half: int
    trade_id: int
    kind: str
    entry_bar: int
    entry: float
    atr: float
    stop: float
    tp: object
    stop_reason: str = "stop"
    exit_bar: object = None
    exit_price: object = None
    reason: object = None
    pnl: object = None
    r: object = None


@dataclass
class Result:
    halves: list = field(default_factory=list)
    same_bar_conflicts: int = 0
    be_adverse_exits: int = 0
    refusals: list = field(default_factory=list)   # (bar, dir, reason): bridge-too-far skips (PERF2 T1; template REFUSED rows)


def run(o, h, l, c, baseline, atr, c1, c2, vol=None, ex=None, p=None, open_fill=None, intrabar=None):
    p = p or Params()
    n = len(o)
    vol = vol if vol is not None else [True] * n
    ex = ex if ex is not None else [0] * n
    res = Result()
    open_ = []
    tstate = {}
    pending_exit = None
    pending_entry = None
    last_c1 = last_b = 0
    c1_sig_bar = {LONG: None, SHORT: None}
    window = None
    chain = {LONG: False, SHORT: False}
    last_trade = None
    tid = 0

    def close(hf, t, price, reason):
        hf.exit_bar, hf.exit_price, hf.reason = t, price, reason
        hf.pnl = hf.dir * (price - hf.entry) - p.spread
        hf.r = hf.pnl / (p.stop_atr * hf.atr)
        if all(x.reason is not None for x in res.halves if x.trade_id == hf.trade_id):
            last_trade["reason"] = reason

    def volume_ok(t):
        if p.volume_mode == "ALWAYS_YES":
            return True
        if p.volume_mode == "ALWAYS_NO":
            return False
        return bool(vol[t])

    for t in range(n):
        # 1. at the open
        px_open = o[t] if open_fill is None else open_fill[t]
        if pending_exit and open_:
            for hf in open_:
                close(hf, t, px_open, pending_exit)
            open_ = []
        pending_exit = None
        if pending_entry:
            d, a, kind = pending_entry
            tid += 1
            e = px_open
            stop = e - d * p.stop_atr * a
            tp = e + d * p.tp1_atr * a
            open_ = [Half(d, 1, tid, kind, t, e, a, stop, tp), Half(d, 2, tid, kind, t, e, a, stop, None)]
            res.halves.extend(open_)
            tstate[tid] = dict(tp1_bar=None, trail=False, best=None)
            chain[d], chain[-d] = True, False
            last_trade = dict(dir=d, reason=None)
            pending_entry = None

        # 2. inside the bar: stop before TP1 (or the intrabar resolver's events, R-D6)
        if intrabar is not None:
            for hf in list(open_):
                stop_hit = l[t] <= hf.stop if hf.dir == LONG else h[t] >= hf.stop
                tp_hit = hf.tp is not None and (h[t] >= hf.tp if hf.dir == LONG else l[t] <= hf.tp)
                if stop_hit and tp_hit:
                    res.same_bar_conflicts += 1
            for hf, price, kind in intrabar(t, list(open_)):
                if hf not in open_:
                    continue
                open_.remove(hf)
                if kind == "stop":
                    close(hf, t, price, hf.stop_reason)
                else:
                    close(hf, t, price, "tp1")
                    tstate[hf.trade_id]["tp1_bar"] = t
        for hf in (list(open_) if intrabar is None else []):
            d = hf.dir
            stop_hit = l[t] <= hf.stop if d == LONG else h[t] >= hf.stop
            tp_hit = hf.tp is not None and (h[t] >= hf.tp if d == LONG else l[t] <= hf.tp)
            if stop_hit and tp_hit:
                res.same_bar_conflicts += 1
            if stop_hit:
                fill = min(hf.stop, o[t]) if d == LONG else max(hf.stop, o[t])
                open_.remove(hf)
                close(hf, t, fill, hf.stop_reason)
            elif tp_hit:
                fill = max(hf.tp, o[t]) if d == LONG else min(hf.tp, o[t])
                open_.remove(hf)
                close(hf, t, fill, "tp1")
                tstate[hf.trade_id]["tp1_bar"] = t

        # 3. at the close
        b = sgn(c[t] - baseline[t])
        c1sig = c1[t] if (c1[t] != 0 and last_c1 == -c1[t]) else 0
        if c1sig:
            c1_sig_bar[c1sig] = t
        if c1[t] != 0:
            last_c1 = c1[t]
        bcross = b if (b != 0 and last_b == -b) else 0
        if b != 0:
            last_b = b
            chain[-b] = False

        # breakeven (M-D3) and trailing on the runner
        for hf in list(open_):
            st = tstate[hf.trade_id]
            if hf.half != 2 or st["tp1_bar"] is None:
                continue
            d, a = hf.dir, hf.atr
            if st["tp1_bar"] == t:
                if d * (c[t] - hf.entry) < 0:
                    pending_exit = "be_adverse"
                    res.be_adverse_exits += 1
                    continue
                be = hf.entry + d * p.be_offset_atr * a
                if d * (be - hf.stop) > 0:
                    hf.stop, hf.stop_reason = be, "be"
            if not st["trail"] and d * (c[t] - hf.entry) >= p.trail_start_atr * a:
                st["trail"], st["best"] = True, c[t]
            elif st["trail"] and d * (c[t] - st["best"]) > 0:
                st["best"] = c[t]
            # Only a new best close can tighten the stop; recomputing on every close gives
            # the same stop because it never loosens (equivalent mutant M4, 2026-11-22).
            if st["trail"]:
                new = st["best"] - d * p.trail_dist_atr * a
                if d * (new - hf.stop) > 0:
                    hf.stop, hf.stop_reason = new, "trail"

        # close-decided exits (T1, T3, T5.5)
        if open_ and pending_exit is None:
            d = open_[0].dir
            if c1[t] == -d:
                pending_exit = "c1_flip"
            elif p.exit_mode == "INDICATOR" and ex[t] == -d:
                pending_exit = "exit_ind"
            elif b == -d and p.baseline_mode == "on":
                pending_exit = "baseline"

        # entries (only when flat after any pending exit)
        flat = not open_ or pending_exit is not None
        if not flat:
            continue
        a = atr[t]
        if p.baseline_mode == "off":            # C1-only (NULL1): a C1 signal is the whole entry rule
            if c1sig:
                pending_entry = (c1sig, a, "c1")
            continue
        dist_ok = abs(c[t] - baseline[t]) <= p.baseline_max_dist_atr * a
        vol_ok = volume_ok(t)
        dec = None
        if c1sig:
            d = c1sig
            cont = (not open_ and last_trade is not None and last_trade["dir"] == d
                    and last_trade["reason"] not in (None, "baseline") and chain[d]
                    and (p.cont_after_stop or last_trade["reason"] != "stop"))
            if cont:
                if c2[t] == d and b != -d:
                    dec = (d, "continuation")
            elif b == d and c2[t] == d and vol_ok and dist_ok:
                dec = (d, "c1")
        if dec is None and bcross:
            d = bcross
            age = None if c1_sig_bar[d] is None else t - c1_sig_bar[d]
            if p.btf_on and c1[t] == d and age is not None and age >= p.btf_max_age:
                window = None
                res.refusals.append((t, d, "bridge-too-far"))
            else:
                window = dict(dir=d, start=t, pull=not dist_ok)
        if dec is None and window is not None:
            d, k = window["dir"], t - window["start"]
            alive = b != -d and c1[t] != -d
            if window["pull"] and k > p.pullback_wait_bars:
                alive = False
            if p.catchup_limit_on and k > p.catchup_max_bars:
                alive = False
            if not alive:
                window = None
            elif b == d and c1[t] == d and c2[t] == d and vol_ok and dist_ok:
                dec = (d, "pullback" if window["pull"] else "baseline")
                window = None
            # A failed pullback candle needs no extra close: the window dies at the next
            # bar through k > pullback_wait_bars (mutation test M8, 2026-11-22).
        if dec is not None:
            pending_entry = (dec[0], a, dec[1])

    for hf in open_:
        close(hf, n - 1, c[n - 1], "end")
    return res
