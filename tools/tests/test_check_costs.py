"""Tests for tools/check_costs.py (P5): fake Zorro logs built under a known world must pass and be
attributed to that world's rules; each planted cost error must fail the run."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check_costs as C  # noqa: E402

# (scenario, half) -> (dir, kind, exit reason, K0 exit price); entries 1.0 (scenario files)
TRADES = {
    ("A1", 1): (1, "stop", 0.985), ("A1", 2): (1, "stop", 0.985),
    ("A1M", 1): (-1, "stop", 1.015), ("A1M", 2): (-1, "stop", 1.015),
    ("A2", 1): (1, "tp1", 1.01), ("A2", 2): (1, "be", 1.0),
    ("A2M", 1): (-1, "tp1", 0.99), ("A2M", 2): (-1, "be", 1.0),
    ("B1", 1): (1, "tp1", 1.01), ("B1", 2): (1, "trail", 1.015),
    ("B1M", 1): (-1, "tp1", 0.99), ("B1M", 2): (-1, "trail", 0.985),
    ("C1", 1): (1, "c1_flip", 1.0015), ("C1", 2): (1, "c1_flip", 1.0015),
    ("C1M", 1): (-1, "c1_flip", 0.9985), ("C1M", 2): (-1, "c1_flip", 0.9985),
}


def fake_log(rule="H_UTC", short="S_ASK", plant=None):
    rows, units = [], 1000.0
    for sc in sorted({s for s, _ in TRADES}):
        for k in (0, 1):
            rows.append(f"INFO,{C.asset(sc, k)},0,rows=20,costed={k},type=1,list=29")
    for (sc, h), (d, reason, x0) in TRADES.items():
        n = C.roll_days(rule, C.E, C.CLOSE[(sc, h)])
        for k in (0, 1):
            entry, exitp = 1.0, x0
            prof = d * (exitp - entry) * units
            roll = comm = 0.0
            if k == 1:
                roll = n * C.ROLL[d]
                comm = 1.0          # TradeCommission holds the Commission setting (run 2: 1.0); 0.1 is charged
                prof = prof - C.SPREAD_COST - C.COMM + roll
                if d == 1 and reason == "tp1":      # M-D7: long TP fills at the level in bid terms
                    exitp += C.SPREAD
                    prof += C.SPREAD_COST
                if d == -1 and short == "S_BID" and reason in C.ENTRY_LEVEL_EXIT:
                    exitp -= C.SPREAD
                    prof += C.SPREAD_COST
                if plant == (sc, h, "profit"):
                    prof -= 0.05
                if plant == (sc, h, "position"):
                    exitp += 3 * C.TOL_PRICE
                    prof += d * 3 * C.TOL_PRICE * units
                if plant == (sc, h, "roll"):
                    roll += 0.02
            if k == 0 and plant == (sc, h, "k0roll"):
                roll = -0.1
            rows.append(f"HALF,{C.asset(sc, k)},1,{h},{d},c1,20240308,{entry},20240308,{exitp},{reason},0,6,7,"
                        f"{prof},{roll},{comm},{C.SPREAD if k else 0},{units}")
    if plant == "error":
        rows.append("ERROR,EUR_A21_USD,20240308,x")
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    f.write("\n".join(rows) + "\n")
    f.close()
    return f.name


def run(**kw):
    p = fake_log(**kw)
    try:
        return C.evaluate(*C.read_log(p))
    finally:
        os.unlink(p)


class CheckCosts(unittest.TestCase):
    def test_world_utc_ask_passes_and_is_identified(self):
        rows, ok, fr, fs = run(rule="H_UTC", short="S_ASK")
        self.assertTrue(ok)
        self.assertEqual(fr, ["H_UTC", "H_NY"])   # not distinguished by these trades (prediction table)
        self.assertEqual(fs, ["S_ASK"])

    def test_world_bar_bid_passes_and_is_identified(self):
        rows, ok, fr, fs = run(rule="H_BAR", short="S_BID")
        self.assertTrue(ok)
        self.assertEqual(fr, ["H_BAR"])
        self.assertEqual(fs, ["S_BID"])

    def test_planted_profit_error_fails(self):
        self.assertFalse(run(plant=("A2", 2, "profit"))[1])
        self.assertFalse(run(plant=("B1M", 1, "profit"))[1])

    def test_long_tp_paying_spread_fails(self):
        self.assertFalse(run(plant=("A2", 1, "profit"))[1])

    def test_fill_position_beyond_one_step_fails_but_costs_hold(self):
        rows, ok, fr, fs = run(plant=("B1", 2, "position"))
        self.assertFalse(ok)
        fails = [r[1] for r in rows if r[2] == "FAIL"]
        self.assertEqual(fails, ["h2_exit_position"])

    def test_planted_fractional_roll_fails(self):
        self.assertFalse(run(plant=("B1", 2, "roll"))[1])

    def test_costs_on_k0_fail(self):
        self.assertFalse(run(plant=("C1", 1, "k0roll"))[1])

    def test_error_row_fails(self):
        self.assertFalse(run(plant="error")[1])

    def test_prediction_table(self):
        p = {(r[0], r[1]): r[3:] for r in C.prediction()}
        self.assertEqual(p[("C1", 1)], (3, 3, 4))
        self.assertEqual(p[("B1", 2)], (6, 6, 6))
        self.assertEqual(p[("A1", 1)], (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
