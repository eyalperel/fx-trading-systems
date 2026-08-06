"""
Phase Coherence & Autocorrelation Periodogram Null Test
=======================================================
Week 12 Day 5 (2026-08-05). Second null test of the Ehlers cycle premise.
Companion to analysis/null_tests/ (Week 11, spectral peak prominence).

Tests two statistics against four null models on two assets:

  1. PHASE COHERENCE  - Ehlers Correlation Cycle (TASC V.38:06, 2020).
     Quadrature projection of price onto a fixed-period cosine/sine basis.
     Statistic: circular mean resultant length R of phase steps.
     R = 1 -> every phase step identical (genuine cycle).
     R = 0 -> steps uniformly scattered.
     Computed on the RAW angle, BEFORE Ehlers' monotonicity ratchet, which
     forbids phase from decreasing and manufactures the trend-mode flatline
     signature on any input (fires on ~27% of bars).

  2. ACF PERIODOGRAM  - Ehlers autocorrelation periodogram (TASC V.34:09, 2016).
     Correlogram -> Fourier across trial periods 8..48.
     Statistic: peak prominence of the resulting spectrum, in sd units.
     Computed on RAW log returns with NO roofing pre-filter: Ehlers band-passes
     before correlating, which reimports the artefact under test.

Nulls: IID permutation, fBm (Hurst-matched, Davies-Harte circulant embedding),
IAAFT (spectrum- and distribution-preserving), stochastic volatility.

KEY RESULT: R ~ 0.97 on real markets AND on pure noise. Consecutive 20-bar
windows share 19 of 20 bars, so consecutive phase angles are near-identical by
construction. The sliding window MANUFACTURES phase coherence from any input.

Usage:
    python phase_coherence_null_test.py
Expects in the working directory:
    RM_C2_EURUSD_D1.csv, RM_C2_BTCUSD_H4.csv        (price)
    CorrCycle_EURUSD_D1.csv, CorrCycle_BTCUSD_H4.csv (Zorro AngleRaw, cross-check)

Seed 20260805 -> results reproduce exactly.
"""

import numpy as np, pandas as pd

rng = np.random.default_rng(20260805)

# ---------- Indicator: Ehlers Correlation Cycle (quadrature projection) ----------
def corr_cycle_angles(price, Period=20):
    """Returns RAW phase angle (degrees), Ehlers' construction, no ratchet."""
    n=len(price); ang=np.full(n, np.nan)
    idx=np.arange(Period)
    C=np.cos(2*np.pi*idx/Period); S=-np.sin(2*np.pi*idx/Period)
    Cc=C-C.mean(); Sc=S-S.mean()
    Cn=np.sqrt((Cc**2).sum()); Sn=np.sqrt((Sc**2).sum())
    # sliding windows: Price[cyc_n] with cyc_n=0..Period-1 means most recent first
    W=np.lib.stride_tricks.sliding_window_view(price, Period)[:, ::-1]  # col0 = current bar
    Wc=W-W.mean(axis=1, keepdims=True)
    Wn=np.sqrt((Wc**2).sum(axis=1))
    good=Wn>0
    Real=np.zeros(len(W)); Imag=np.zeros(len(W))
    Real[good]=(Wc[good]@Cc)/(Wn[good]*Cn)
    Imag[good]=(Wc[good]@Sc)/(Wn[good]*Sn)
    a=np.zeros(len(W))
    nz=Imag!=0
    a[nz]=90.0+np.degrees(np.arctan(Real[nz]/Imag[nz]))
    a[Imag>0]-=180.0
    ang[Period-1:]=a
    return ang

def phase_stats(ang):
    """R = mean resultant length of phase steps; plus Ehlers' <9deg fraction."""
    d=np.diff(ang[~np.isnan(ang)])
    d=(d+180)%360-180                      # wrap to (-180,180]
    r=np.radians(d)
    R=np.abs(np.mean(np.exp(1j*r)))
    frac9=np.mean(np.abs(d)<9.0)
    return R, frac9

# ---------- Autocorrelation periodogram (Ehlers 2016, Measuring Market Cycles) ----------
def acf_periodogram_prominence(price, avglen=3, maxlag=48, pmin=8, pmax=48):
    """Correlogram -> Fourier across trial periods -> peak prominence of the spectrum."""
    x=np.diff(np.log(price))               # work on returns (no roofing pre-filter)
    x=x-x.mean()
    n=len(x)
    corr=np.zeros(maxlag+1)
    for lag in range(maxlag+1):
        M=avglen
        a=x[maxlag-lag: n-lag] if lag>0 else x[maxlag:]
        b=x[maxlag:]
        L=min(len(a),len(b))
        a=a[:L]; b=b[:L]
        if a.std()>0 and b.std()>0:
            corr[lag]=np.corrcoef(a,b)[0,1]
    pwr=[]
    for P in range(pmin,pmax+1):
        N=np.arange(3,maxlag+1)
        cp=(corr[N]*np.cos(2*np.pi*N/P)).sum()
        sp=(corr[N]*np.sin(2*np.pi*N/P)).sum()
        pwr.append(cp*cp+sp*sp)
    pwr=np.array(pwr)
    if pwr.max()<=0: return 0.0
    pwr=pwr/pwr.max()
    return (pwr.max()-np.median(pwr))/ (pwr.std()+1e-12)   # peak prominence in sd units

# ---------- Null models ----------
def null_iid(ret, rng):
    return rng.permutation(ret)

def null_fbm(ret, rng, H):
    n=len(ret)
    k=np.arange(n)
    # Davies-Harte via circulant embedding (fGn autocovariance)
    g=0.5*(np.abs(k+1)**(2*H)-2*np.abs(k)**(2*H)+np.abs(k-1)**(2*H))
    c=np.concatenate([g, g[-2:0:-1]])
    lam=np.fft.fft(c).real
    lam[lam<0]=0
    m=len(c)
    w=rng.standard_normal(m)+1j*rng.standard_normal(m)
    y=np.fft.fft(np.sqrt(lam/(2*m))*w).real[:n]
    return y/ (y.std()+1e-12) * ret.std()

def null_iaaft(ret, rng, iters=60):
    amp=np.abs(np.fft.rfft(ret)); srt=np.sort(ret)
    y=rng.permutation(ret)
    for _ in range(iters):
        Y=np.fft.rfft(y); Y=amp*np.exp(1j*np.angle(Y))
        y=np.fft.irfft(Y, n=len(ret))
        y=srt[np.argsort(np.argsort(y))]
    return y

def null_stochvol(ret, rng, H=0.7):
    lv=null_fbm(np.ones(len(ret)), rng, H)
    vol=np.exp(lv*0.5); vol=vol/vol.mean()*ret.std()
    return rng.standard_normal(len(ret))*vol

def hurst_dfa(x, scales=None):
    x=np.cumsum(x-x.mean()); n=len(x)
    if scales is None: scales=np.unique(np.logspace(1.2, np.log10(n//4), 18).astype(int))
    F=[]
    for s in scales:
        m=n//s
        if m<2: F.append(np.nan); continue
        seg=x[:m*s].reshape(m,s); t=np.arange(s)
        f=[]
        for r in seg:
            p=np.polyfit(t,r,1); f.append(np.mean((r-np.polyval(p,t))**2))
        F.append(np.sqrt(np.mean(f)))
    F=np.array(F); ok=~np.isnan(F)
    return np.polyfit(np.log(scales[ok]), np.log(F[ok]),1)[0]



import time

NSUR=1000

def run_asset(csv, label, angcsv):
    d=pd.read_csv(csv)
    price=d.Price.values
    ret=np.diff(np.log(price))
    H=hurst_dfa(ret)
    Habs=hurst_dfa(np.abs(ret))
    print(f"\n{'='*70}\n{label}  (n={len(price)})   H(ret)={H:.3f}  H(|ret|)={Habs:.3f}\n{'='*70}")

    # --- observed, from ZORRO export (ground truth for the indicator) ---
    dz=pd.read_csv(angcsv)
    R_zorro, f9_zorro = phase_stats(dz.AngleRaw.values)

    # --- observed, from the python reimplementation (must agree) ---
    R_obs, f9_obs = phase_stats(corr_cycle_angles(price,20))
    print(f"Phase coherence R : Zorro {R_zorro:.4f} | Python {R_obs:.4f}  -> agreement {'OK' if abs(R_zorro-R_obs)<0.02 else 'MISMATCH'}")
    print(f"frac|dAngle|<9deg : Zorro {f9_zorro:.4f} | Python {f9_obs:.4f}")
    prom_obs = acf_periodogram_prominence(price)
    print(f"ACF-periodogram prominence: {prom_obs:.4f}")

    nulls={'A IID walk':      lambda r: null_iid(r,rng),
           'B fBm (H-match)': lambda r: null_fbm(r,rng,H),
           'C IAAFT':         lambda r: null_iaaft(r,rng),
           'D StochVol':      lambda r: null_stochvol(r,rng,Habs)}

    print(f"\n{'Null':<17}{'stat':<14}{'obs':>9}{'null med':>10}{'null p95':>10}{'pctile':>8}{'p':>8}  verdict")
    print("-"*84)
    results={}
    for nm,gen in nulls.items():
        Rs=[]; Ps=[]
        for i in range(NSUR):
            sr=gen(ret)
            sp=price[0]*np.exp(np.cumsum(sr))
            sp=np.concatenate([[price[0]],sp])
            Rs.append(phase_stats(corr_cycle_angles(sp,20))[0])
            if i<300: Ps.append(acf_periodogram_prominence(sp))
        Rs=np.array(Rs); Ps=np.array(Ps)
        for stat,obs,arr in [('phase R',R_obs,Rs),('ACF prom',prom_obs,Ps)]:
            pct=100*np.mean(arr<obs); p=np.mean(arr>=obs)
            v='REJECT' if p<0.05 else 'no rej'
            print(f"{nm:<17}{stat:<14}{obs:>9.4f}{np.median(arr):>10.4f}{np.percentile(arr,95):>10.4f}{pct:>7.1f}%{p:>8.3f}  {v}")
        results[nm]=(Rs,Ps)
    return results

t0=time.time()
run_asset('RM_C2_EURUSD_D1.csv','EUR/USD D1','CorrCycle_EURUSD_D1.csv')
run_asset('RM_C2_BTCUSD_H4.csv','BTC/USD H4','CorrCycle_BTCUSD_H4.csv')
print(f"\nelapsed {time.time()-t0:.0f}s")
