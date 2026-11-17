"""Test fixture for the HighPassFilter tooling stage (NOT a spec, never committed under specs/, never run in Zorro).

Builds, in memory, a spec dict in the shape generator.load_spec() returns, plus synthetic raw columns built
with reference.simulate. It exercises the new tooling (dc_gain, phase, ramp residual, start-up, seed, IMP seed)
the way the real HP spec will; every number in it is a fixture value, labelled (c) where it is a judgement.
Tolerances here are fixture values (c), NOT candidates for the HP spec.
Labels: (a) source states, (b) measured / computed, (c) inference.
"""
import copy
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)

import reference as R   # noqa: E402

SQRT_HALF = math.sqrt(2.0) / 2.0
TS = [5, 10, 20, 40, 100]
LEVEL, AMP, SLOPE = 1.1, 0.01, 1e-4
GATE = 0.1
TOL = dict(flat=1e-9, gain=3e-5, phase=3e-5, resid=1e-6, startup=1e-6, x=1e-12, imp=1e-9)
REAL_PS = (20, 30, 48, 125)

# id -> (label, param, Filter factory, seed); expected table is P48 for every control except NC2 (P125)
CONTROLS = {
    "NCA": ("alpha1 +1 in 3rd digit", 48, lambda: R.hp_code(48, k=SQRT_HALF, alpha_bump=1), "zero"),
    "NCB": ("input weight +1 in 3rd digit", 48, lambda: R.hp_code(48, k=SQRT_HALF, in_bump=1), "zero"),
    "NCF": ("fb2 +1 in 3rd digit", 48, lambda: R.hp_code(48, k=SQRT_HALF, fb2_bump=1), "zero"),
    "NCZ": ("1st-difference numerator", 48, lambda: R.hp_code(48, k=SQRT_HALF, num="1st"), "zero"),
    "NCS": ("price seed, corrected k", 48, lambda: R.hp_code(48, k=SQRT_HALF), "price"),
    "NCH": ("current .c: float32 k, price seed", 48, lambda: R.hp_code(48), "price"),
    "NC1": ("P=49 vs P=48", 49, lambda: R.hp_code(49, k=SQRT_HALF), "zero"),
    # degrees bug at P = 125 vs the P125 table: at P = 48 the degrees form is UNSTABLE (pole radius 3.29, overflows to
    # inf, the whole raw file would trip G_NONFINITE), so it cannot be a control there (b, stage report).
    "NC2": ("trig args in degrees, P=125", 125, lambda: R.hp_code(125, k=SQRT_HALF, deg=True), "zero"),
}
# fixture detection lists: kinds each control is expected to be caught by at the fixture tolerances (measured,
# see the exploration in the stage report; NCK is not a fixture control: no kind reaches 10x at these tolerances)
REQUIRED = {"NCA": ["gain", "phase"], "NCB": ["gain"], "NCF": ["gain", "phase"], "NCZ": ["gain", "phase", "resid"],
            "NCS": ["startup"], "NCH": ["startup"], "NC1": ["gain", "phase"], "NC2": ["gain"]}


def wrap(d):
    return (d + math.pi) % (2 * math.pi) - math.pi


def real_filter(p):
    return R.hp_code(p, k=SQRT_HALF)


def filters():
    """variant id -> (Filter, seed) for the synthetic raw file."""
    out = {"P%d" % p: (real_filter(p), "zero") for p in REAL_PS}
    for vid, (_, _, fac, seed) in CONTROLS.items():
        out[vid] = (fac(), seed)
    return out


def _table(p):
    f = R.hp_article(p)
    g = [R.gain_at(f, t) for t in TS]
    return dict(flat=0.0, gains=g, phases={t: R.phase_at(f, t) for t, gg in zip(TS, g) if gg >= GATE},
                resid=R.ramp_residual(f, LEVEL, SLOPE), article="hp_article(%d)" % p,
                source="(b) hp_article(%d), computed from reference.py (fixture)" % p)


def _inputs_for(n_bars=3000):
    n = np.arange(n_bars, dtype=float)
    x = {"flat": np.full(n_bars, LEVEL)}
    for t in TS:
        x["s%d" % t] = LEVEL + AMP * np.sin(2 * math.pi * n / t)
    x["ramp"] = LEVEL + SLOPE * n
    return x


def _effects(vid, f, seed, p=48):
    """Analytic gain / phase / resid / flat effect and simulated start-up effect vs hp_article(p)."""
    art = R.hp_article(p)
    eff = dict(gain=max(abs(R.gain_at(f, t) - R.gain_at(art, t)) for t in TS),
               phase=max(abs(wrap(R.phase_at(f, t) - R.phase_at(art, t)))
                         for t in TS if R.gain_at(art, t) >= GATE),
               resid=abs(R.ramp_residual(f, LEVEL, SLOPE) - 0.0), flat=0.0)
    x = _inputs_for(500)
    st = 0.0
    for i in ("flat", "ramp"):
        st = max(st, float(np.max(np.abs(R.simulate(f, x[i], seed=seed) - R.simulate(art, x[i], seed="zero")))))
    eff["startup"] = st
    return eff


def build():
    ts = TS
    d = {
        "batch": dict(name="HPFIX_Fixture", id_prefix="HPF", indicator="HighPassFilter",
                      asset_label="synthetic (EURUSD D1 bar clock)", prereg="(test fixture, not a spec)",
                      script_name="GEN_HPF_fixture"),
        "zorro": dict(include="../../indicators/ehlers/HighPassFilter.c", raw_file="Data/GEN_HPF_raw.csv",
                      marker_file="Data/GEN_HPF_exit_marker.txt", clock_asset="EUR/USD", bar_period=1440,
                      start_date=20080101, end_date=20240101, series_len=3),
        "inputs": dict(n_bars=3000, warmup=500, level=[11, 10], amp=[1, 100], slope=[1, 10000], sine_periods=ts),
        "clock": dict(lo=0.8, hi=1.7, source="(b) fixture"),
        "checks": dict(dc_gain=0.0, phase_gate=GATE, startup_inputs=["flat", "ramp"]),
        "tolerances": {q: dict(value=v, source="(c) test fixture value") for q, v in TOL.items()},
        "expected": {"P%d" % p: _table(p) for p in (20, 30, 48, 125)},
        "variants": [],
        "imp": dict(must_pass={"P%d" % p: "hp_code(%d, PI_ZORRO, SQRT_HALF)" % p for p in REAL_PS},
                    must_fail={"NCH": "hp_code(48, PI_ZORRO, SQRT_HALF)"}),
    }
    d["imp"]["must_pass"]["NCH"] = "hp_code(48, PI_ZORRO, F32_0707)"
    d["tolerances"]["lag"] = dict(value=1e-3, source="(c) test fixture value (unused at dc_gain 0)")
    for p in REAL_PS:
        d["variants"].append(dict(id="P%d" % p, role="real", label="P=%d" % p, kind="param", param=p,
                                  expected="P%d" % p, seed="zero"))
    floors = dict(gain=0.0, phase=0.0, resid=0.0, startup=0.0, flat=2.2e-16)
    for p in REAL_PS:
        f, art = real_filter(p), R.hp_article(p)
        floors["gain"] = max(floors["gain"], max(abs(R.gain_at(f, t) - R.gain_at(art, t)) for t in TS))
        floors["phase"] = max(floors["phase"], max(abs(R.phase_at(f, t) - R.phase_at(art, t))
                                                   for t in TS if R.gain_at(art, t) >= GATE))
        x = _inputs_for(500)
        for i in ("flat", "ramp"):
            floors["startup"] = max(floors["startup"], float(np.max(np.abs(
                R.simulate(f, x[i], seed="zero") - R.simulate(art, x[i], seed="zero")))))
    d["floor"] = dict(floors, source="(b) fixture: corrected code (Zorro PI) vs article")
    for vid, (label, p, fac, seed) in CONTROLS.items():
        v = dict(id=vid, role="neg_control", label=label, kind="param" if vid == "NC1" else "inline", param=p,
                 expected="P125" if vid == "NC2" else "P48", seed=seed,
                 effect=dict(_effects(vid, fac(), seed, 125 if vid == "NC2" else 48), source="(b) fixture"))
        if v["kind"] == "inline":
            v["function"] = "hpf_%s" % vid.lower()
            v["body"] = "var hpf_%s(vars Price, int P)\n{\n\treturn Price[0];\n}" % vid.lower()
        d["variants"].append(v)
    d["detect"] = dict(source="(b) fixture", rule="fixture", required={k: list(v) for k, v in REQUIRED.items()})
    return d


_cache = {}


def toml_spec():
    if "d" not in _cache:
        _cache["d"] = build()
    return copy.deepcopy(_cache["d"])


def build_cols(spec, override=None):
    """{column: list of float} for the raw file. override: {variant id: (Filter, seed)}."""
    x = {}
    n_bars = spec["n_bars"]
    n = np.arange(n_bars, dtype=float)
    x["flat"] = np.full(n_bars, spec["level"])
    for t in spec["ts"]:
        x["s%d" % t] = spec["level"] + spec["amp"] * np.sin(2 * math.pi * n / t)
    x["ramp"] = spec["level"] + spec["slope"] * n
    fl = filters()
    fl.update(override or {})
    cols = {"n": [float(k) for k in range(n_bars)], "clock_close": [1.1] * n_bars}
    ins = ["flat"] + ["s%d" % t for t in spec["ts"]] + ["ramp"]
    for i in ins:
        cols["x_" + i] = [float(v) for v in x[i]]
    for v in spec["variants"]:
        f, seed = fl[v["id"]]
        for i in ins:
            cols["y_%s_%s" % (v["id"], i)] = [float(t) for t in R.simulate(f, x[i], seed=seed)]
    return cols


_cols_cache = {}


def base_cols(spec):
    if "c" not in _cols_cache:
        _cols_cache["c"] = build_cols(spec)
    return {k: list(v) for k, v in _cols_cache["c"].items()}


def to_text(header, cols, n_bars):
    lines = [",".join(header)]
    for r in range(n_bars):
        lines.append(",".join(("%d" % cols[c][r]) if c == "n" else ("%.15f" % cols[c][r]) for c in header))
    return "\n".join(lines) + "\n"
