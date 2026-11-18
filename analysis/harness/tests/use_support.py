"""Shared helpers for the USE tests (UltimateSmootherE, specs/USE_ArticleFidelity.toml). NOT a test module.

Builds, from the spec itself, the checker dict, the exact inputs and the OWN-MODEL outputs of every variant (what a
perfect Zorro run would export, floating-point noise aside), cached per process, plus a synthetic raw CSV text.
No .c file is read, Zorro is not run.
Labels: (a) source states, (b) verified here, (c) inference.
"""
import math
import os
import sys

import numpy as np

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HARNESS)

import checker as C      # noqa: E402
import generator as G    # noqa: E402
import reference as R    # noqa: E402

SPEC_PATH = os.path.join(HARNESS, "specs", "USE_ArticleFidelity.toml")
KINDS = ("flat", "gain", "lag", "phase", "startup")
_cache = {}


def spec():
    if "spec" not in _cache:
        with open(SPEC_PATH, "rb") as f:
            _cache["spec"] = tomllib.load(f)
    return _cache["spec"]


def cs():
    if "cs" not in _cache:
        _cache["cs"] = G.to_checker_spec(G.load_spec(SPEC_PATH))
    return _cache["cs"]


def inputs():
    if "x" not in _cache:
        _cache["x"] = C.make_inputs(cs())
    return _cache["x"]


def own_model_outputs():
    """{variant id: {input: output array}}: every variant simulated with ITS OWN [imp].must_pass model and its seed."""
    if "y" not in _cache:
        sp, c, x = spec(), cs(), inputs()
        out = {}
        for v in c["variants"]:
            model = R.IMP_MODELS[sp["imp"]["must_pass"][v["id"]]]()
            out[v["id"]] = {i: R.simulate_any(model, x[i], seed=v["seed"]) for i in C.input_names(c)}
        _cache["y"] = out
    return _cache["y"]


def check_rows_of(vid, yv=None):
    c = cs()
    v = [v for v in c["variants"] if v["id"] == vid][0]
    return C.check_rows(c, v, inputs(), yv or own_model_outputs()[vid], xe=inputs())


def kind_max(vid):
    """kind -> max |actual - expected| over that kind's checks of the variant (SKIP rows excluded)."""
    m = {}
    for r in check_rows_of(vid):
        if r["result"] == "SKIP":
            continue
        k = C._kind(r["check_id"])
        m[k] = max(m.get(k, 0.0), r["abs_diff"])
    return m


def raw_cols(override=None):
    """{column: list of float} as Zorro would export. override: {variant id: {input: array}}."""
    c, x = cs(), inputs()
    names = C.input_names(c)
    cols = {"n": [float(k) for k in range(c["n_bars"])], "clock_close": [1.1] * c["n_bars"]}
    for i in names:
        cols["x_" + i] = [float(v) for v in x[i]]
    y = dict(own_model_outputs())
    y.update(override or {})
    for v in c["variants"]:
        for i in names:
            cols["y_%s_%s" % (v["id"], i)] = [float(t) for t in y[v["id"]][i]]
    return cols


def to_text(header, cols, n_bars):
    lines = [",".join(header)]
    for r in range(n_bars):
        lines.append(",".join(("%d" % cols[h][r]) if h == "n" else ("%.15f" % cols[h][r]) for h in header))
    return "\n".join(lines) + "\n"


def wrap(d):
    return C.wrap_phase(d)
