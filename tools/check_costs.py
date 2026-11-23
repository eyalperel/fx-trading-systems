"""P5 cost probe checker: costs off (K0) vs on (K1), same scenarios, one Zorro run.

Usage: python tools/check_costs.py <zorro_log.csv> <results.csv>     (exit 0 = PASS)
       python tools/check_costs.py --predict                         (print the prediction table)
Criteria: docs/preregistration/TPL_Costs_P5_Criteria.md (committed before the run).

Costs per lot (LotAmount 1000, PIPCost 0.1 per pip, account units): spread 2 pips = 0.2 per half;
commission 1 per 10000 units = 0.1 per round turn; rollover -1 (long) / +0.5 (short) per 10000
units per day = -0.1 / +0.05 per day (Zorro 3.11 spread.htm: "per 10000 contracts for currencies";
rollover added "for any trade that was longer open than 12 hours at any new day, including
Saturday and Sunday").
Open questions, answered by the run, each with its candidates fixed here before the run:
  day rule  H_UTC (new day at 00:00 UTC) / H_NY (00:00 New York) / H_BAR (17:00 New York, our bar close)
  short     S_ASK (short stop / TP levels measured from the ask entry, as the engine) /
            S_BID (measured from the bid fill: levels and exits one spread lower)
"""
import csv
import datetime as dt
import sys
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc
NY = ZoneInfo("America/New_York")
SPREAD_COST = 0.2
COMM = 0.1
ROLL = {1: -0.1, -1: 0.05}      # per day, by direction
SPREAD = 0.0002                 # price units
TOL_PRICE = 1e-5                # as S4 C3
TOL_MONEY = 1e-4                # TradeProfit / TradeRoll are float32 (trading.h); values <= ~16

E = dt.datetime(2024, 3, 7, 23, 0, 0, tzinfo=UTC)   # every entry: Thu 18:00 New York (run 2 log)


def t(d, hh, mm, ss):
    return dt.datetime(2024, 3, d, hh, mm, ss, tzinfo=UTC)


# (scenario, half) -> close time UTC, from the S4 run 2 Zorro log (TPL_Equivalence_test.log)
CLOSE = {
    ("A1", 1): t(8, 9, 42, 51), ("A1", 2): t(8, 9, 42, 51),
    ("A1M", 1): t(8, 9, 42, 52), ("A1M", 2): t(8, 9, 42, 52),
    ("A2", 1): t(8, 9, 30, 1), ("A2", 2): t(11, 8, 8, 39),
    ("A2M", 1): t(8, 9, 30, 1), ("A2M", 2): t(11, 8, 8, 39),
    ("B1", 1): t(8, 9, 30, 1), ("B1", 2): t(14, 8, 30, 18),
    ("B1M", 1): t(8, 9, 30, 1), ("B1M", 2): t(14, 8, 30, 1),
    ("C1", 1): t(11, 22, 0, 0), ("C1", 2): t(11, 22, 0, 0),
    ("C1M", 1): t(11, 22, 0, 0), ("C1M", 2): t(11, 22, 0, 0),
}
# Exits at a level derived from the ENTRY price (initial stop, TP1, breakeven): under S_BID these sit one
# spread lower for a short. The trailing stop is derived from closes, so it is the same under both.
ENTRY_LEVEL_EXIT = {"stop", "tp1", "be"}


def boundaries(rule, start, end):
    """Day-change instants strictly inside (start, end] under the rule."""
    out = []
    day = (start - dt.timedelta(days=1)).date()
    while True:
        if rule == "H_UTC":
            b = dt.datetime(day.year, day.month, day.day, tzinfo=UTC)
        elif rule == "H_NY":
            b = dt.datetime(day.year, day.month, day.day, tzinfo=NY).astimezone(UTC)
        else:
            b = dt.datetime(day.year, day.month, day.day, 17, tzinfo=NY).astimezone(UTC)
        if b > end:
            return out
        if b > start:
            out.append(b)
        day += dt.timedelta(days=1)


def roll_days(rule, start, end):
    """Charges: one per new day at which the trade has been open longer than 12 hours."""
    return sum(1 for b in boundaries(rule, start, end) if b - start > dt.timedelta(hours=12))


RULES = ("H_UTC", "H_NY", "H_BAR")


def prediction():
    rows = []
    for (sc, h), end in CLOSE.items():
        rows.append((sc, h, end.isoformat(), *(roll_days(r, E, end) for r in RULES)))
    return rows


def read_log(path):
    half, info, errors = {}, {}, []
    with open(path, encoding="utf-8") as f:
        for r in csv.reader(f):
            if not r:
                continue
            if r[0] == "HALF":
                half.setdefault(r[1], []).append(dict(
                    group=int(r[2]), half=int(r[3]), dir=int(r[4]), kind=r[5], entry_day=r[6],
                    entry=float(r[7]), exit_day=r[8], exit=float(r[9]), reason=r[10],
                    profit=float(r[14]), roll=float(r[15]), comm=float(r[16]), spread=float(r[17]),
                    units=float(r[18])))
            elif r[0] == "INFO":
                info[r[1]] = dict(x.split("=", 1) for x in r[3:] if "=" in x)
            elif r[0] in ("ERROR", "ASSETFAIL"):
                errors.append(",".join(r))
    return half, info, errors


def asset(sc, k):
    return f"EUR_{sc}{k}_USD"


def evaluate(half, info, errors):
    rows = []

    def add(sc, check, ok, exp, got, status=None):
        rows.append((sc, check, status or ("PASS" if ok else "FAIL"), exp, got))

    for e in errors:
        add("RUN", "error_row", False, "none", e)
    fit_rule = {r: True for r in RULES}
    fit_short = {"S_ASK": True, "S_BID": True}
    scens = sorted({sc for sc, _ in CLOSE})
    for sc in scens:
        for k in (0, 1):
            inf = info.get(asset(sc, k))
            add(sc, f"K{k}_info", inf is not None, "INFO row", "missing" if inf is None else "ok")
            if inf is not None:
                add(sc, f"K{k}_assetType", inf.get("type") == "1", "1 (FOREX)", inf.get("type"))
                add(sc, f"K{k}_costed", inf.get("costed") == str(k), k, inf.get("costed"))
        h0 = sorted(half.get(asset(sc, 0), []), key=lambda x: (x["group"], x["half"]))
        h1 = sorted(half.get(asset(sc, 1), []), key=lambda x: (x["group"], x["half"]))
        add(sc, "n_halves", len(h0) == len(h1) == 2, "2 / 2", f"{len(h0)} / {len(h1)}")
        for a, b in zip(h0, h1):
            tag = f"h{a['half']}"
            for key in ("half", "dir", "kind", "entry_day", "exit_day", "reason"):
                add(sc, f"{tag}_{key}", a[key] == b[key], a[key], b[key])
            # K0: no costs at all (guard for the off copy)
            add(sc, f"{tag}_K0_zero_costs", abs(a["roll"]) < TOL_MONEY and abs(a["comm"]) < TOL_MONEY,
                "roll 0, comm 0", f"{a['roll']}, {a['comm']}")
            p0 = a["dir"] * (a["exit"] - a["entry"]) * a["units"]
            add(sc, f"{tag}_K0_profit_is_price", abs(p0 - a["profit"]) < TOL_MONEY, repr(p0), repr(a["profit"]))
            # rollover: an integer number of days of the direction's rate
            rate = ROLL[a["dir"]]
            n = b["roll"] / rate
            add(sc, f"{tag}_roll_integer_days", abs(n - round(n)) < 1e-3, "integer", f"{n:.4f}")
            for r in RULES:
                if round(n) != roll_days(r, E, CLOSE[(sc, a["half"])]):
                    fit_rule[r] = False
            # commission: one round turn per half
            dprof = a["profit"] - b["profit"]
            if a["dir"] == 1:
                add(sc, f"{tag}_long_prices_equal", abs(a["entry"] - b["entry"]) <= TOL_PRICE
                    and abs(a["exit"] - b["exit"]) <= TOL_PRICE, f"{a['entry']} / {a['exit']}", f"{b['entry']} / {b['exit']}")
                exp = SPREAD_COST + COMM - b["roll"]
                add(sc, f"{tag}_long_cost_identity", abs(dprof - exp) < TOL_MONEY, repr(exp), repr(dprof))
            else:
                exp_ask = SPREAD_COST + COMM - b["roll"]
                exp_bid = (COMM - b["roll"]) if a["reason"] in ENTRY_LEVEL_EXIT else exp_ask
                ok_ask, ok_bid = abs(dprof - exp_ask) < TOL_MONEY, abs(dprof - exp_bid) < TOL_MONEY
                fit_short["S_ASK"] &= ok_ask
                fit_short["S_BID"] &= ok_bid
                add(sc, f"{tag}_short_cost_identity", ok_ask or ok_bid,
                    f"S_ASK {exp_ask:.6f} / S_BID {exp_bid:.6f}", repr(dprof))
                add(sc, f"{tag}_short_K1_entry", True, "recorded", repr(b["entry"]), status="INFO")
    fr = [r for r, ok in fit_rule.items() if ok]
    fs = [s for s, ok in fit_short.items() if ok]
    add("RUN", "day_rule_fits", len(fr) >= 1, "one of " + "/".join(RULES), "/".join(fr) or "none")
    add("RUN", "short_rule_fits", len(fs) >= 1, "S_ASK or S_BID", "/".join(fs) or "none")
    ok = all(r[2] != "FAIL" for r in rows)
    return rows, ok, fr, fs


def main(argv):
    if argv == ["--predict"]:
        print("scenario,half,close_utc," + ",".join(RULES))
        for r in prediction():
            print(",".join(str(x) for x in r))
        return 0
    if len(argv) != 2:
        print(__doc__)
        return 2
    half, info, errors = read_log(argv[0])
    rows, ok, fr, fs = evaluate(half, info, errors)
    with open(argv[1], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "check", "status", "expected", "got"])
        w.writerows(rows)
    print(f"FAIL rows: {sum(1 for r in rows if r[2] == 'FAIL')}; day rule fits: {fr or 'none'}; short rule fits: {fs or 'none'}")
    print("RUN " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
