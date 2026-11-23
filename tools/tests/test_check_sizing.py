"""Tests for tools/check_sizing.py (P6): a fake Zorro log written from the model must pass, under the
timing alternative it was written with; each planted sizing defect must fail the run."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check_sizing as C  # noqa: E402

INFO = ("type=1,list=29,FixedLots=0,Capital=100000.00,RiskPct=2.000000,Leverage=20.000000,"
        "StopAtr=1.500000,Fill=3,Hedge=2,TICKS=1,BarOffset=1020,StartWeek=71700")
SC = C.scenarios()


def fake_log(timing="TA", plant=None):
    sig, acct = C.model(timing)
    rows = []
    for i, n in enumerate(C.names()):
        rows.append(f"INFO,{C.params(n)['pair']},{i},rows=20,mut={C.params(n)['mut']},{INFO}")
    for j, x in enumerate(sig):
        n, pr = x["asset"], C.params(x["asset"])
        pair = pr["pair"]
        lots, eq, pct = x["lots"], x["eq"], x["pct"]
        if plant == "lots" and j == len(sig) - 1:
            lots += 1
        if plant == "equity" and j == len(sig) - 1:
            eq += 1.0
        if plant == "mutant_fixed" and pr["mut"]:
            pct = 1.0
        target = eq * pct / 100
        raw = target / x["risk_lot"]
        if plant != "lots":
            lots = int(raw // 1)
        rows.append(f"SIZE,{pair},{x['ymd']},{eq:.6f},{eq:.6f},0.000000,{SC[n]['atr'][x['dec_bar']]:.15f},"
                    f"{pr['pip']:.15f},{pr['pipcost']:.15f},1000,{pct:.6f},{target:.6f},{x['stop_pips']:.12f},"
                    f"{x['risk_lot']:.15f},{raw:.10f},{lots},{lots * x['risk_lot']:.6f},{x['mc']:.10f},"
                    f"{2 * lots * x['mc']:.6f}")
        rows.append(f"ASSET,{pair},{x['dec_bar']},{x['ymd']},{SC[n]['c'][x['dec_bar']]:.10f},"
                    f"{pr['pip']:.10f},{pr['pipcost']:.10f},1000")
        if x["refuse"] and not (plant == "drop_margin_error" and x["refuse"] == "margin"):
            rows.append(f"ERROR,{pair},{x['ymd']},{x['refuse']},planted")
        if not x["refuse"]:
            for h in x["halves"]:
                units = pr["pipcost"] / pr["pip"] * (x["lots"] + (1 if plant == "units" and h.half == 2 else 0))
                ey = int(SC[n]["days"][h.entry_bar].strftime("%Y%m%d"))
                rows.append(f"HALF,{pair},1,{h.half},{h.dir},c1,{ey},{h.entry},0,{h.exit_price},{h.reason},0,0,0,"
                            f"0,0,0,0,{units:.8f}")
    for k, (ymd, e) in enumerate(sorted(acct.items())):
        mc = 1 if plant == "margincall" and k == 10 else 0
        rows.append(f"ACCT,,{k},{ymd},{e:.6f},{e:.6f},0.000000,{mc}")
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
    f.write("kind,asset,a,b,c\n" + "\n".join(rows) + "\n")
    f.close()
    return f.name


def run(path):
    rows, verdict = C.check(C.read_log(path))
    fails = [r for r in rows if r["result"] == "FAIL"]
    det = [r for r in rows if r["result"] == "DETECTED"]
    fits = [tm for tm in ("TA", "TB") if not verdict[tm][0] and verdict[tm][1] == 0]
    return fails, det, fits


class TestCheckSizing(unittest.TestCase):
    def test_clean_TA_passes_and_fits_TA_only(self):
        fails, det, fits = run(fake_log("TA"))
        self.assertEqual(fails, [])
        self.assertEqual(len(det), 1)
        self.assertEqual(fits, ["TA"])

    def test_clean_TB_fits_TB_only(self):
        fails, det, fits = run(fake_log("TB"))
        self.assertEqual(fits, ["TB"])
        # ACCT rows are written from the TA end-of-bar model in both worlds, so K3 still passes
        self.assertEqual([f for f in fails if f["check"] != "K3"], [])

    def test_planted_lots(self):
        fails, _, _ = run(fake_log(plant="lots"))
        self.assertTrue(any(f["check"] == "K1" for f in fails))

    def test_planted_equity(self):
        fails, _, fits = run(fake_log(plant="equity"))
        self.assertTrue(any(f["check"] == "K3" for f in fails))
        self.assertEqual(fits, [])

    def test_planted_missing_guard_error(self):
        fails, _, _ = run(fake_log(plant="drop_margin_error"))
        self.assertTrue(any(f["check"] == "K2" and f["asset"] == "A1_GMRG" for f in fails))

    def test_planted_mutant_not_detected(self):
        fails, det, _ = run(fake_log(plant="mutant_fixed"))
        self.assertEqual(det, [])
        self.assertTrue(fails)

    def test_planted_margincall(self):
        fails, _, _ = run(fake_log(plant="margincall"))
        self.assertTrue(any(f["check"] == "K2" and f["got"] == 1 for f in fails))

    def test_planted_half_units(self):
        fails, _, _ = run(fake_log(plant="units"))
        self.assertTrue(any(f["check"] == "K4" for f in fails))


if __name__ == "__main__":
    unittest.main()
