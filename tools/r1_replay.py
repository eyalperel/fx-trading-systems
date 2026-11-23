"""R1 replay (decision R-D6): indicator states from the harness reference models, and the reference engine run with an
M1 layer, on Python-built 17:00 New York bars.

M1 rules (a) fill.htm: a stop fills at "Min of Stop and Open" (long; short: Max), a take-profit at "Max of TakeProfit
and Open" (long; short: Min), i.e. at the level when the record crosses it, at the record's open when the record already
opens beyond it; (b) gotchas 9d.12 (TPL_Probe runs 4 and 6). Inside one record a stop is checked before a target
(T5 amendment: Zorro's stop-first rule applies within one history record). Records are visited in time order.

Alternatives the run decides (pre-registered, R1 criteria):
  fill_px  "open" | "close": price of a market fill at the start of a bar (entries, close-decided exits) = the first
           record's open or close;
  start    "entry" | "after": the entry record itself is checked for the new trade's stop / TP1, or only later records.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "analysis", "template"))
sys.path.insert(0, os.path.join(ROOT, "analysis", "harness"))
import reference_engine as E  # noqa: E402
import reference as R  # noqa: E402

LONG = E.LONG


def indicators(bars, fast=(1, 2), slow=(1, 20), fisher_len=10, reflex_len=20, atr_len=14):
    """Strategy 1 indicator values on bars (dict of arrays from r1_data.daily_bars, already cut to Zorro's first bar)."""
    mid = (bars["h"] + bars["l"]) * 0.5
    mm = R.simulate_mama(R.mama_article(fast, slow), mid)
    fi = R.simulate_fisher(R.fisher_article(fisher_len), mid)
    rx = R.simulate_reflex(R.reflex_code(reflex_len), bars["c"])
    at = R.simulate_atr(R.atr_mt4(atr_len), bars["c"], bars["h"], bars["l"])
    return dict(mama=mm.mama, fama=mm.fama, period=mm.period, alpha=mm.alpha, phase=mm.phase,
                fish=fi.out, trig=fi.trig, raw=fi.raw, v1=fi.v1, rng=fi.rng,
                reflex=rx.r, sum=rx.sum, ms=rx.ms, atr=at.atr, tr=at.tr)


def states(ind):
    sg = np.sign
    return dict(baseline=ind["fama"], atr=ind["atr"], c1=sg(ind["fish"] - ind["trig"]).astype(int),
                c2=sg(ind["reflex"]).astype(int))


def open_fill(m1, bars, fill_px="open"):
    """Price of market fills at the start of each bar: first record's open or close."""
    k = "o" if fill_px == "open" else "c"
    return [float(m1[k][i]) for i in bars["i0"]]


def resolver(m1, bars, start="entry", fill_px="open"):
    """Intrabar events for the engine (E.run intrabar=...), from the bar's M1 records."""
    i0s, i1s = bars["i0"], bars["i1"]
    keep = bars.get("keep")

    def recs(t):
        idx = np.arange(i0s[t], i1s[t] + 1)
        if keep is not None:
            idx = idx[keep[idx]]
        return idx

    def ev(t, halves):
        out = []
        live = list(halves)
        idx = recs(t)
        for j, k in enumerate(idx):
            o, hi, lo = float(m1["o"][k]), float(m1["h"][k]), float(m1["l"][k])
            for hf in list(live):
                if hf.entry_bar == t and j == 0 and start == "after":
                    continue
                if hf.dir == LONG:
                    if lo <= hf.stop:
                        out.append((hf, min(hf.stop, o), "stop"))
                        live.remove(hf)
                    elif hf.tp is not None and hi >= hf.tp:
                        out.append((hf, max(hf.tp, o), "tp"))
                        live.remove(hf)
                else:
                    if hi >= hf.stop:
                        out.append((hf, max(hf.stop, o), "stop"))
                        live.remove(hf)
                    elif hf.tp is not None and lo <= hf.tp:
                        out.append((hf, min(hf.tp, o), "tp"))
                        live.remove(hf)
            if not live:
                break
        return out
    return ev


def replay(m1, bars, st, first_trade, p=None, start="entry", fill_px="open"):
    """Engine run on bars[first_trade:] with states st (full arrays), M1 layer on. Returns (Result, bar slice offset)."""
    sl = slice(first_trade, None)
    sub = {k: (v[sl] if hasattr(v, "__len__") and not isinstance(v, str) else v) for k, v in bars.items()}
    sub["keep"] = bars.get("keep")
    lst = lambda a: [float(x) for x in a]       # the engine works on Python numbers (its sgn() rejects numpy bools)
    res = E.run(lst(sub["o"]), lst(sub["h"]), lst(sub["l"]), lst(sub["c"]), lst(st["baseline"][sl]), lst(st["atr"][sl]),
                [int(x) for x in st["c1"][sl]], [int(x) for x in st["c2"][sl]],
                p=p, open_fill=open_fill(m1, sub, fill_px), intrabar=resolver(m1, sub, start, fill_px))
    return res, first_trade
