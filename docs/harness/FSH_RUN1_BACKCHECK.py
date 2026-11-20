"""FSH run 1 back-check (planning chat, 2026-11-20). Independent of analysis/harness: own model = docs/harness/FISHER_REVIEW_MODEL.py.
Inputs rebuilt from integers (not the exported x) for the trace / start-up comparison; IMP replays the exported x.
Run: python docs/harness/FSH_RUN1_BACKCHECK.py C:/Zorro/Data/GEN_FSH_raw.csv docs/harness/FISHER_REVIEW_MODEL.py"""
import csv, math, sys, importlib.util, numpy as np
spec=importlib.util.spec_from_file_location("rm",sys.argv[2]); rm=importlib.util.module_from_spec(spec); spec.loader.exec_module(rm)
rows=list(csv.reader(open(sys.argv[1]))); hdr=rows[0]; D=np.array([[float(v) for v in r] for r in rows[1:]]); C={h:i for i,h in enumerate(hdr)}
col=lambda h: D[:,C[h]]
N=3000; W=700; LN=math.log(1999)
# inputs rebuilt from integers (not the exported x)
lev=11/10; amp=1/100; sl=1/10000; pi=4*math.atan(1)
X={"flat":[lev]*N,"ramp":[lev+sl*n for n in range(N)],"rampdn":[lev-sl*n for n in range(N)]}
for T in (5,10,20,40,100):
    X[f"s{T}"]=[lev+amp*math.sin(2*pi*n/T) for n in range(N)]
    X[f"sc{T}"]=[lev+10*amp*math.sin(2*pi*n/T) for n in range(N)]
    X[f"of{T}"]=[2*lev+amp*math.sin(2*pi*n/T) for n in range(N)]
xin=max(float(np.max(np.abs(col("x_"+k)-np.array(v)))) for k,v in X.items())
print("input guard max |x_csv - x_int| =",xin)
BASE=["flat","s5","s10","s20","s40","s100","ramp","rampdn"]; SIN=["s5","s10","s20","s40","s100"]
A=rm.SRC_A
P={"FR10":(10,A),"FR20":(20,A),"NCB":(10,rm.SRC_B),"NCW":(10,dict(A,a=.331)),"NCC":(10,dict(A,cl=.99)),"NCK":(10,dict(A,k=.25)),"NCL":(11,A),"NC32":(10,rm.CODE)}
def model(L,p,x):
    o=rm.run(x,L,p); return {k:np.array([r[k] for r in o]) for k in ("raw","pre","v","f","trig","rng")}
M={}
for v,(L,p) in P.items():
    for k in BASE+([f"sc{T}" for T in (5,10,20,40,100)]+[f"of{T}" for T in (5,10,20,40,100)] if v in("FR10","FR20") else []):
        M[(v,k)]=model(L,p,X[k])
# shared replay NCS/NCT in generator order
sh={"v":0.0,"f":0.0}; inst={(v,k):rm.Fisher(10,rm.CODE,sh) for v in ("NCS","NCT") for k in BASE}; so={key:[] for key in inst}
for n in range(N):
    for v in ("NCS","NCT"):
        for k in BASE: so[(v,k)].append(inst[(v,k)].step(X[k],n)["f"])
for key in so: M[key]={"f":np.array(so[key])}
def gate(m,k,clamp):
    g=m["rng"]/amp>=0.01
    if clamp: g&=np.minimum(np.abs(m["pre"]-.99),np.abs(m["pre"]+.99))>=1e-6
    return g
def kinds(v, ref):
    """all check values of variant v's run columns against reference variant ref's model (ref=v for real)."""
    out={}
    has=lambda o,k: f"{o}_{v}_{k}" in C
    for o,mk,cl in (("raw","raw",False),("v1","v",True),("out","f",True)):
        for T in (5,10,20,40,100):
            k=f"s{T}"
            if not has(o,k): continue
            m=M[(ref,k)]; g=gate(M[("FR10" if ref in("NCS","NCT") else ref,k)],k,cl) if "rng" in m else np.ones(N,bool)
            g[:W]=False; d=np.abs(col(f"{o}_{v}_{k}")-m[mk])[g]
            out[f"trace-{o}-T{T}"]=(float(d.max()), int((~g[W:]).sum()))
    # bounds over every base input (+ copies for real)
    ins=[k for k in hdr if k.startswith("x_")]
    for o,b in (("raw",1.0),("v1",.999)):
        vals=[col(h) for h in hdr if h.startswith(o+"_"+v+"_")]
        if vals: out[f"bound-{o}"]=(float(max(np.max(np.abs(a)) for a in vals))-b,0)
    vals=[col(h) for h in hdr if h.startswith("out_"+v+"_")]
    out["bound-out"]=(float(max(np.max(np.abs(a)) for a in vals))-LN,0)
    for o,mk,ex in (("raw","raw",{"ramp":1.0,"rampdn":-1.0}),("v1","v",{"ramp":.999,"rampdn":-.999}),("out","f",None)):
        for k in ("ramp","rampdn"):
            if not has(o,k): continue
            e = ex[k] if ex else M[(ref,k)][mk][W:]
            out[f"exact-{o}-{k}"]=(float(np.max(np.abs(col(f"{o}_{v}_{k}")[W:]-e))),0)
    if has("trig","flat"):
        out["trigger"]=(float(max(np.max(np.abs(col(f"trig_{v}_{k}")[1:]-col(f"out_{v}_{k}")[:-1])) for k in BASE)),0)
    if has("out","sc5"):
        for tag in ("sc","of"):
            out[f"inv-{tag}"]=(float(max(np.max(np.abs(col(f"out_{v}_{tag}{T}")[W:]-col(f"out_{v}_s{T}")[W:])) for T in (5,10,20,40,100))),0)
    fz=[np.max(np.abs(col(f"{o}_{v}_flat"))) for o in ("raw","v1","out") if has(o,"flat")]
    out["flatzero"]=(float(max(fz)),0)
    return out
TOL={"trace":1e-9,"bound":1e-12,"exact":1e-12,"trigger":0.0,"inv":1e-9,"flatzero":1e-12}
def tol(name):
    t=TOL[name.split("-")[0]]
    if name=="bound-out": t=LN*1e-12
    return t
print("\n== Real variants (Zorro vs own model; PASS if <= tol)")
nreal=0; nfail=0
for v in ("FR10","FR20"):
    ks=kinds(v,v)
    for name,(val,gated) in ks.items():
        t=tol(name); ok = val<=t; nreal+=1; nfail+= (not ok)
        print(f"  {v} {name:16s} {val: .6e}  tol {t:.0e}  {'PASS' if ok else 'FAIL'}" + (f"  gated {gated}" if gated else ""))
print(f"  real checks {nreal}, FAIL {nfail}")
print("\n== NCB INFO vs its own model and vs FR10")
for name,(val,g) in kinds("NCB","NCB").items(): print(f"  own {name:16s} {val: .6e}")
print("\n== Controls vs FR10 model: max ratio val/tol per kind (detected if >= 10)")
for v in ("NCW","NCC","NCK","NCL","NC32","NCS","NCT"):
    ks=kinds(v,"FR10"); best={}
    for name,(val,g) in ks.items():
        t=tol(name); r = val/t if t>0 else (math.inf if val>0 else 0.0); kd=name.split("-")[0]
        if name.startswith("bound"): r = val/t if val>0 else 0.0
        best[kd]=max(best.get(kd,0),r)
    print(f"  {v}: "+", ".join(f"{k} {r:.3g}" for k,r in best.items()))
    fails=sum(1 for name,(val,g) in ks.items() if val>tol(name))
    print(f"      FAIL rows vs FR10: {fails} of {len(ks)}")
print("\n== Controls vs their OWN model (should be at rounding level)")
for v in ("NCW","NCC","NCK","NCL","NC32","NCS","NCT"):
    if v in ("NCS","NCT"):
        val=max(float(np.max(np.abs(col(f"out_{v}_{k}")-M[(v,k)]["f"]))) for k in BASE); print(f"  {v} out all rows max {val:.3e}")
    else:
        val=max(float(np.max(np.abs(col(f"{o}_{v}_{k}")-M[(v,k)][mk]))) for k in BASE for o,mk in (("raw","raw"),("v1","v"),("out","f"))); print(f"  {v} raw/v1/out all rows max {val:.3e}")
print("\n== Start-up INFO, FR10 / FR20 rows < W, max |out - model| per sine")
for v in ("FR10","FR20"):
    print("  ",v,[f"{float(np.max(np.abs(col(f'out_{v}_s{T}')[:W]-M[(v,f's{T}')]['f'][:W]))):.3e}" for T in (5,10,20,40,100)])

print("\n== IMP (model fed the EXPORTED x, rows >= W)")
XE={k:list(col("x_"+k)) for k in BASE}
def imp(v,L,p,shared=False):
    mx=0.0
    if shared:
        sh={"v":0.0,"f":0.0}; inst={(w,k):rm.Fisher(10,rm.CODE,sh) for w in ("NCS","NCT") for k in BASE}; so={key:[] for key in inst}
        for n in range(N):
            for w in ("NCS","NCT"):
                for k in BASE: so[(w,k)].append(inst[(w,k)].step(XE[k],n)["f"])
        return max(float(np.max(np.abs(col(f"out_{v}_{k}")[W:]-np.array(so[(v,k)])[W:]))) for k in BASE)
    for k in BASE:
        o=rm.run(XE[k],L,p); m={"raw":np.array([r["raw"] for r in o]),"v1":np.array([r["v"] for r in o]),"out":np.array([r["f"] for r in o])}
        for oo in ("raw","v1","out"):
            mx=max(mx,float(np.max(np.abs(col(f"{oo}_{v}_{k}")[W:]-m[oo][W:]))))
    return mx
for v,(L,p) in P.items(): print(f"IMP must_pass {v}: {imp(v,L,p):.6e}")
for v in ("NCS","NCT"): print(f"IMP must_pass {v} (shared replay): {imp(v,0,0,True):.6e}")
print("IMP must_fail FR10 vs NCW model:", repr(imp("FR10",10,dict(A,a=.331))))
mxs=max(float(np.max(np.abs(col(f"out_NCS_{k}")[W:]-np.array([r["f"] for r in rm.run(XE[k],10,A)])[W:]))) for k in BASE)
print("IMP must_fail NCS vs FR10 model:", repr(mxs))
