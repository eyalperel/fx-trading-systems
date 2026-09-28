"""
roofing_playground.py -- poke at the Roofing Filter.

Companion to docs/learning/RoofingFilter_Explained.md. Every number in that
document is printed by one of the sections below. Change the parameters at the
top and re-run to see what moves.

    python docs/learning/roofing_playground.py            # run every section
    python docs/learning/roofing_playground.py gain       # run one section
    python docs/learning/roofing_playground.py --list     # list sections

Needs numpy only. No market data, no Zorro.
"""
import sys
import numpy as np

# ---------------------------------------------------------------------------
# Parameters -- change these
# ---------------------------------------------------------------------------
HP_PERIOD = 48      # HighPassFilter.c HPPeriod
SS_PERIOD = 10      # SuperSmoother2Pole.c Period (RoofingFilter's SSPeriod)
SEED      = 11      # random seed for the coin-flip sections

PI = np.pi

# ---------------------------------------------------------------------------
# The filters, written exactly as the library computes them (radians, 0.707)
# ---------------------------------------------------------------------------
def hp_alpha(hp_period, with_0707=True, degrees_bug=False):
    """alpha1 for the 2-pole high-pass.
    degrees_bug=True reproduces the pre-May-2026 error: Ehlers' degree
    arguments fed to a radians cos()/sin()."""
    k = 0.707 if with_0707 else 1.0
    arg = k * 360.0 / hp_period if degrees_bug else k * 2 * PI / hp_period
    return (np.cos(arg) + np.sin(arg) - 1) / np.cos(arg)

def hp_coeffs(hp_period, **kw):
    """num/den lists: HP[t] = c*(P - 2P1 + P2) + 2b*HP1 - b^2*HP2"""
    a1 = hp_alpha(hp_period, **kw)
    c, b = (1 - a1 / 2) ** 2, 1 - a1
    return np.array([c, -2 * c, c]), np.array([1.0, -2 * b, b * b])

def ss_coeffs(period, degrees_bug=False):
    """num/den lists: F[t] = c1*(x + x1)/2 + c2*F1 + c3*F2
    Uses sqrt(2), as SuperSmoother2Pole.c does. Ehlers' published code uses
    1.414; the difference shows in the 4th decimal."""
    a = np.exp(-np.sqrt(2) * PI / period)
    cos_arg = np.sqrt(2) * 180.0 / period if degrees_bug else np.sqrt(2) * PI / period
    c2 = 2 * a * np.cos(cos_arg)
    c3 = -a * a
    c1 = 1 - c2 - c3
    return np.array([c1 / 2, c1 / 2, 0.0]), np.array([1.0, -c2, -c3])

def run_filter(num, den, x, seed=None):
    """Run a 2nd-order recursion over x. seed=None starts the memory at zero;
    seed=v fills the memory with v (what the library's series(Price[0],3) does)."""
    y = np.zeros(len(x))
    s = 0.0 if seed is None else seed
    y1 = y2 = s
    xp = np.concatenate([[x[0], x[0]], x])       # flat price history before bar 0
    for t in range(len(x)):
        y[t] = (num[0] * xp[t + 2] + num[1] * xp[t + 1] + num[2] * xp[t]
                - den[1] * y1 - den[2] * y2)
        y2, y1 = y1, y[t]
    return y

def highpass(x, hp_period=HP_PERIOD, seed=None, **kw):
    return run_filter(*hp_coeffs(hp_period, **kw), x, seed)

def supersmoother(x, period=SS_PERIOD, seed="first", **kw):
    s = x[0] if seed == "first" else seed        # library: seeds at input's first value
    return run_filter(*ss_coeffs(period, **kw), x, s)

def roofing(x, hp_period=HP_PERIOD, ss_period=SS_PERIOD, hp_seed=None):
    return supersmoother(highpass(x, hp_period, seed=hp_seed), ss_period)

# ---------------------------------------------------------------------------
# Exact gain from coefficients: |num(z)| / |den(z)| at z = e^(-j*2*pi/P)
# ---------------------------------------------------------------------------
def gain(num, den, period):
    w = 2 * PI / period
    zn = np.exp(-1j * w * np.arange(len(num)))
    zd = np.exp(-1j * w * np.arange(len(den)))
    return abs(num @ zn) / abs(den @ zd)

def roof_gain(p, hp_period=HP_PERIOD, ss_period=SS_PERIOD):
    return gain(*hp_coeffs(hp_period), p) * gain(*ss_coeffs(ss_period), p)

def corner(f, lo, hi):
    """period where gain f crosses 1/sqrt(2), by bisection"""
    t = 1 / np.sqrt(2)
    for _ in range(80):
        m = (lo + hi) / 2
        if (f(m) < t) == (f(lo) < t): lo = m
        else: hi = m
    return (lo + hi) / 2

def amplitude_at(y, period):
    """least-squares amplitude of the period-P sine in y (phase-proof)"""
    t = np.arange(len(y))
    M = np.column_stack([np.sin(2 * PI * t / period), np.cos(2 * PI * t / period), np.ones(len(y))])
    c, *_ = np.linalg.lstsq(M, y, rcond=None)
    return np.hypot(c[0], c[1]), np.abs(y - M @ c).max()

def hr(title):
    print("\n" + "=" * 72 + "\n" + title + "\n" + "=" * 72)

# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
def s_ingredients():
    hr("1. Three ingredients: drift, 20-bar cycle, 2-bar jitter")
    hn, hd = hp_coeffs(HP_PERIOD); sn, sd = ss_coeffs(SS_PERIOD)
    print(f"alpha1 = {hp_alpha(HP_PERIOD):.6f}   SS c1,c2,c3 = "
          + ", ".join(f"{v:.6f}" for v in [2 * sn[0], -sd[1], -sd[2]]))
    print(f"{'ingredient':22s} {'HP gain':>8s} {'SS gain':>8s}")
    for name, p in [("A slow drift (inf)", 1e9), ("B 20-bar cycle", 20), ("C 2-bar jitter", 2)]:
        print(f"{name:22s} {gain(hn, hd, p):8.4f} {gain(sn, sd, p):8.4f}")

def s_gain():
    hr("2. Gain table and the band")
    hn, hd = hp_coeffs(HP_PERIOD); sn, sd = ss_coeffs(SS_PERIOD)
    print(f"{'period':>7} {'HP':>8} {'SS':>8} {'product':>8}")
    for p in [2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 20, 25, 30, 40, 48, 60, 80, 120, 200, 400]:
        g1, g2 = gain(hn, hd, p), gain(sn, sd, p)
        print(f"{p:>7} {g1:8.4f} {g2:8.4f} {g1 * g2:8.4f}")
    print(f"HP -3 dB corner: {corner(lambda p: gain(hn, hd, p), 10, 400):.2f} bars")
    print(f"SS -3 dB corner: {corner(lambda p: gain(sn, sd, p), 3, 60):.2f} bars")
    ps = np.arange(3, 400, 0.01); g = np.array([roof_gain(p) for p in ps])
    band = ps[g >= 1 / np.sqrt(2)]
    print(f"roofing peak: period {ps[g.argmax()]:.2f}, gain {g.max():.4f}")
    print(f"half-power band: {band.min():.2f} to {band.max():.2f} bars")

def s_cascade():
    hr("3. Cascading multiplies gains: A + B + C through the roofing filter")
    t = np.arange(6000.0)
    price = (100 + 0.05 * t) + 2 * np.sin(2 * PI * t / 20) + 0.4 * (-1.0) ** t
    out = roofing(price)[-1000:]
    amp, resid = amplitude_at(out, 20)
    print(f"predicted amplitude: 2 x {roof_gain(20):.6f} = {2 * roof_gain(20):.6f}")
    print(f"measured amplitude : {amp:.6f}")
    print(f"residual after removing the 20-bar sine: {resid:.1e}")
    print(f"(naive (max-min)/2 reads {(out.max() - out.min()) / 2:.4f} -- the sampling trap)")

def s_twobar():
    hr("4. The trap: a 2-bar average on a period-4 sine")
    t = np.arange(40.0); x = np.sin(2 * PI * t / 4)
    y = (x[1:] + x[:-1]) / 2
    print("output samples:", np.round(y[:8], 3))
    print(f"largest sample : {y.max():.4f}")
    print(f"true gain      : |1 + z|/2 at z=e^(-j*pi/2) = {gain(np.array([.5, .5]), np.array([1.]), 4):.6f}")
    print("samples sit 45 deg off the peak: 0.707107 x cos(45deg) = 0.5")

def s_byhand():
    hr("5. Gain at period 20, term by term")
    w = 2 * PI / 20; z = np.exp(-1j * w); z2 = z * z
    print(f"z = {z.real:.7f} {z.imag:+.7f}j   z^2 = {z2.real:.7f} {z2.imag:+.7f}j")
    a1 = hp_alpha(HP_PERIOD); c = (1 - a1 / 2) ** 2; b = 1 - a1
    n = 1 - 2 * z + z2; d = 1 - 2 * b * z + b * b * z2
    print(f"HP: c={c:.7f} b={b:.6f} 2b={2*b:.6f} b^2={b*b:.7f}")
    print(f"    1-2z+z^2 = {n.real:+.7f} {n.imag:+.7f}j  |.|={abs(n):.7f}  x c = {c*abs(n):.7f}")
    print(f"    den      = {d.real:+.7f} {d.imag:+.7f}j  |.|={abs(d):.7f}")
    print(f"    gain = {c*abs(n)/abs(d):.6f}")
    sn, sd = ss_coeffs(SS_PERIOD); c1 = 2 * sn[0]; c2, c3 = -sd[1], -sd[2]
    d2 = 1 - c2 * z - c3 * z2
    print(f"SS: c1/2={c1/2:.7f} c2={c2:.6f} c3={c3:.6f}")
    print(f"    |1+z| = 2cos(w/2) = {abs(1+z):.7f}  x c1/2 = {c1/2*abs(1+z):.7f}")
    print(f"    den   = {d2.real:+.7f} {d2.imag:+.7f}j  |.|={abs(d2):.7f}")
    print(f"    gain = {c1/2*abs(1+z)/abs(d2):.6f}")
    print(f"product = {roof_gain(20):.6f}")

def s_coinflip():
    hr("6. No cycle in, cycle out: a coin-flip walk through the roofing filter")
    rng = np.random.default_rng(SEED)
    x = np.cumsum(rng.choice([-1.0, 1.0], size=3000))
    seg = roofing(x)[1000:1060]
    s = np.sign(seg); runs, n = [], 1
    for a, b in zip(s[:-1], s[1:]):
        if a == b: n += 1
        else: runs.append(n); n = 1
    runs.append(n)
    print("60 bars:", " ".join(f"{v:+.1f}" for v in seg[:20]), "...")
    print("same-sign stretch lengths:", runs)
    rng = np.random.default_rng(7)
    for name, gen in [("white noise (the coin flips)", lambda n: rng.standard_normal(n)),
                      ("random walk (their running sum)", lambda n: np.cumsum(rng.standard_normal(n)))]:
        zc = []
        for _ in range(40):
            y = roofing(gen(6000))[500:]
            sg = np.signbit(y); zc.append(2 * len(y) / np.count_nonzero(sg[1:] != sg[:-1]))
        print(f"{name:32s} zero-crossing period {np.mean(zc):6.2f} bars (sd {np.std(zc):.2f})")

def s_collapse():
    hr("7. Does the band 'collapse to nothing' when HPPeriod nears SSPeriod?")
    ps = np.arange(2.5, 1000, 0.01)
    print(f"{'HP':>4} {'SS':>4} {'ratio':>6} {'peak':>7} {'at':>7}  half-power band")
    for H in [10, 15, 20, 30, 48, 80]:
        g = np.array([roof_gain(p, H, SS_PERIOD) for p in ps]); band = ps[g >= 1 / np.sqrt(2)]
        bs = f"{band.min():.2f} to {band.max():.2f}" if len(band) else "none"
        print(f"{H:>4} {SS_PERIOD:>4} {H/SS_PERIOD:>6.1f} {g.max():7.4f} {ps[g.argmax()]:7.2f}  {bs}")

def s_seed():
    hr("8. Seeding at price level, and why a repeated pole fades slowly")
    P0 = 1.10; x = np.full(120, P0)
    hp = highpass(x, seed=P0); ro = supersmoother(hp)
    b = 1 - hp_alpha(HP_PERIOD)
    print(f"first HP output = P0*(1-alpha1^2) = {hp[0]:.6f}")
    print(f"{'bar':>4} {'HP':>9} {'roofing':>9} {'b^bar*P0 (part 3)':>18}")
    for t in [0, 10, 20, 30, 50, 75, 100]:
        print(f"{t:>4} {hp[t]:9.5f} {ro[t]:9.5f} {P0 * b**t:18.5f}")
    print(f"roofing below 1% of seed at bar {np.argmax(np.abs(ro) < 0.01 * P0)}")
    print("\ntwo one-pole stages, b = 0.5, kick of 1:")
    s1 = 0.5 ** np.arange(5); s2 = np.zeros(5); s2[0] = 1
    for t in range(1, 5): s2[t] = 0.5 * s2[t - 1] + s1[t]
    for t in range(5): print(f"  bar {t}: stage1 {s1[t]:.4f}  stage2 {s2[t]:.4f}  ratio {s2[t]/s1[t]:.0f}")
    n = np.arange(40); r = (n + 1) * b ** n
    print(f"(bar+1)*b^bar with real b: peak at bar {n[r.argmax()]}, height {r.max():.4f}")

def s_ratio():
    hr("9. 'Smoothing ratio': size vs jaggedness, and the 10.9x")
    t = np.arange(30000.0)
    slow = 10 * np.sin(2 * PI * t / 30); fast = np.sin(2 * PI * t / 3 + 0.3)
    print(f"toy size       : {(slow+fast).std():.4f} -> {slow.std():.4f}  ratio {(slow+fast).std()/slow.std():.4f}")
    d = np.diff
    print(f"toy jaggedness : {d(slow+fast).std():.4f} -> {d(slow).std():.4f}  ratio {d(slow+fast).std()/d(slow).std():.4f}")
    rng = np.random.default_rng(9); R = {"size": [], "jag": [], "jag_old": []}
    for _ in range(30):
        p = 1.20 + np.cumsum(rng.normal(0, 0.006, 2596))
        h = highpass(p, seed=p[0]); r = supersmoother(h)
        R["size"].append(h[500:].std() / r[500:].std())
        R["jag"].append(d(h[30:]).std() / d(r[30:]).std())
        ho = highpass(p, seed=p[0], with_0707=False, degrees_bug=True)
        ro = supersmoother(ho, degrees_bug=True)
        R["jag_old"].append(d(ho[30:]).std() / d(ro[30:]).std())
    print(f"random walk, size ratio              : {np.mean(R['size']):.2f}")
    print(f"random walk, jaggedness (library)    : {np.mean(R['jag']):.2f}")
    print(f"random walk, jaggedness (pre-fix)    : {np.mean(R['jag_old']):.2f}"
          f"  range {min(R['jag_old']):.2f}-{max(R['jag_old']):.2f}")

def s_oldbug():
    hr("10. The pre-fix coefficients and the file that exploded")
    P = np.array([1.20248, 1.19239, 1.19143])
    for label, kw in [("library", {}), ("no 0.707", dict(with_0707=False)),
                      ("degrees bug, no 0.707", dict(with_0707=False, degrees_bug=True)),
                      ("degrees bug, with 0.707", dict(degrees_bug=True))]:
        a1 = hp_alpha(HP_PERIOD, **kw)
        print(f"{label:25s} alpha {a1:+.4f}  b {1-a1:+.4f}  HP rows 1-3: "
              + ", ".join(f"{v:.5f}" for v in highpass(P, seed=P[0], **kw)))

SECTIONS = {"ingredients": s_ingredients, "gain": s_gain, "cascade": s_cascade,
            "twobar": s_twobar, "byhand": s_byhand, "coinflip": s_coinflip,
            "collapse": s_collapse, "seed": s_seed, "ratio": s_ratio, "oldbug": s_oldbug}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg == "--list": print("\n".join(SECTIONS))
    elif arg: SECTIONS[arg]()
    else:
        for f in SECTIONS.values(): f()
