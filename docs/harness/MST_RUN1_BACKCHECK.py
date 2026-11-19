"""MST run 1 planning-chat back-check (independent of checker.py). Reads C:/Zorro/Data/GEN_MST_raw.csv.
Run: python docs/harness/MST_RUN1_BACKCHECK.py <path to GEN_MST_raw.csv>   (2026-11-19, planning chat)"""
import numpy as np, sys

PI32=float(np.float32(3.14159))
D=np.genfromtxt(sys.argv[1],delimiter=',',names=True)
N=len(D); n=np.arange(N); W=700; r=slice(W,None); A=0.01; Ts=[5,10,20,40,100]
# ---- inputs
def sine(T,lev=1.1,amp=A): return lev+amp*np.sin(2*np.pi*n/T)
inp={'flat':np.full(N,1.1),'alt':1.1+0.01*np.where(n%2==0,1,-1),'ramp':1.1+1e-4*n}
for T in Ts: inp[f's{T}']=sine(T); inp[f'sc{T}']=sine(T,1.1,0.1); inp[f'of{T}']=sine(T,2.2,A)
xe=max(np.abs(D['x_'+k]-v).max() for k,v in inp.items())
print('input guard max |x - expected|:',f'{xe:.3e}')
# ---- generic model (pi used everywhere; NCL variant via literal args)
def model(x,L,H,S,win=None,scale=1.0,fb=0.5,da=0.0,seed='first',pi=np.pi,k=np.sqrt(2)/2,r2=np.sqrt(2),pi_exp=None):
    win=L if win is None else win
    pe=pi if pi_exp is None else pi_exp
    # HP
    w=k*2*pi/H; a=(np.cos(w)+np.sin(w)-1)/np.cos(w)
    xp=np.concatenate([[x[0],x[0]],x]); h=np.zeros(N)
    for i in range(N):
        h[i]=(1-a/2)**2*(xp[i+2]-2*xp[i+1]+xp[i])+2*(1-a)*(h[i-1] if i>=1 else 0)-(1-a)**2*(h[i-2] if i>=2 else 0)
    def sscoef(P,da=0.0):
        a1=np.exp(-r2*pe/P)+da; b1=2*a1*np.cos(r2*pi/P); return 1-b1+a1*a1, b1, -a1*a1
    def smooth(u,P,h0,da=0.0):
        c1,c2,c3=sscoef(P,da); y=np.zeros(N)
        for i in range(N):
            y[i]=c1*(u[i]+(u[i-1] if i>=1 else h0))/2+c2*(y[i-1] if i>=1 else h0)+c3*(y[i-2] if i>=2 else h0)
        return y
    f=smooth(h,S,h[0])   # SS2 seeds at first input (=0)
    st=np.zeros(N); rg=np.zeros(N)
    for i in range(N):
        wv=[f[i-j] if i-j>=0 else f[0] for j in range(win)]
        hh,ll=max(wv),min(wv); rg[i]=hh-ll
        st[i]=scale*(f[i]-ll)/(hh-ll) if hh!=ll else scale*fb
    out=smooth(st,S,st[0] if seed=='first' else 0.0,da)
    return f,st,out,rg
def lsfit(y,T):
    M=np.c_[np.sin(2*np.pi*n/T),np.cos(2*np.pi*n/T),np.ones(N)][r]
    c=np.linalg.lstsq(M,y[r],rcond=None)[0]; return np.hypot(c[0],c[1]),np.arctan2(c[1],c[0])
def Hroof(T,H,S):
    w=2*np.pi/T; z=np.exp(-1j*w); ww=(np.sqrt(2)/2)*2*np.pi/H; a=(np.cos(ww)+np.sin(ww)-1)/np.cos(ww)
    Hh=(1-a/2)**2*(1-z)**2/(1-2*(1-a)*z+(1-a)**2*z**2)
    a1=np.exp(-np.sqrt(2)*np.pi/S); b1=2*a1*np.cos(np.sqrt(2)*np.pi/S); c1=1-b1+a1*a1
    return Hh*c1*(1+z)/2/(1-b1*z+a1*a1*z**2)
TOL=dict(gain=3e-5,phase=3e-5,flat=1e-9,resid=1e-9,trace=5e-5,inv=1e-9,bound=1e-12,imp=1e-9)
def check(name,ref,real,has_roof=True,has_stoc=True,inv=False,impkw=None):
    L,H,S=ref; res={}; worst={}
    mods={T:model(inp[f's{T}'],L,H,S) for T in Ts}
    if has_roof:
        R=lambda k: D[f'roof_{name}_{k}']
        res['flat']=np.abs(R('flat')[r]).max()
        res['ramp']=np.abs(R('ramp')[r]).max()
        M=np.c_[np.ones(N)][r]  # alt gain: amplitude of alternating component
        alt=R('alt'); res['alt']=np.abs(np.mean(alt[r]*np.where(n[r]%2==0,1,-1)))/0.01
        g=[];p=[]
        for T in Ts:
            gg,pp=lsfit(R(f's{T}')/A,T); Hx=Hroof(T,H,S)
            g.append(abs(gg-abs(Hx))); p.append(abs((pp-np.angle(Hx)+np.pi)%(2*np.pi)-np.pi))
        res['gain']=max(g); res['phase']=max(p)
    tr=[];gated=0
    for T in Ts:
        f,st,out,rg=mods[T]; ok=(rg/A>=0.01); ok[:W]=False; gated+=int((~ok[W:]).sum())
        tr.append(np.abs(D[f'out_{name}_s{T}']-out)[ok].max())
    res['trace']=tr; res['gated']=gated
    if has_stoc:
        s=np.concatenate([D[f'stoc_{name}_{k}'] for k in ['flat','alt','ramp']+[f's{T}' for T in Ts]])
        res['bound']=(s.min(),s.max())
    if inv:
        res['inv']=max(max(np.abs(D[f'out_{name}_sc{T}']-D[f'out_{name}_s{T}'])[r].max(),np.abs(D[f'out_{name}_of{T}']-D[f'out_{name}_s{T}'])[r].max()) for T in Ts)
    if impkw is not None:
        im=0
        for T in Ts:
            _,_,o,_=model(inp[f's{T}'],*impkw[0],**impkw[1]); im=max(im,np.abs(D[f'out_{name}_s{T}']-o)[r].max())
        res['imp']=im
    return res
cases=[('L14',(14,48,10),True,True,True,True,((14,48,10),dict(pi=PI32))),
 ('L20',(20,48,10),True,True,True,True,((20,48,10),dict(pi=PI32))),
 ('L30',(30,48,10),True,True,True,True,((30,48,10),dict(pi=PI32))),
 ('S20',(20,48,20),True,True,True,True,((20,48,20),dict(pi=PI32))),
 ('NCL',(20,48,10),'info',True,True,False,((20,48,10),dict(pi=PI32,k=0.707,r2=1.414,pi_exp=3.14159))),
 ('NCZ',(20,48,10),'info',True,True,False,((20,48,10),dict(pi=PI32,seed='zero'))),
 ('NCW',(20,48,10),False,True,True,False,((20,48,10),dict(pi=PI32,win=21))),
 ('NCA',(20,48,10),False,True,True,False,((20,48,10),dict(pi=PI32,da=1e-3))),
 ('NCP',(20,48,10),False,True,True,False,((20,40,10),dict(pi=PI32))),
 ('NC1',(20,48,10),False,True,True,False,((22,48,10),dict(pi=PI32))),
 ('NCS',(20,48,10),False,False,False,False,((20,48,10),dict(pi=PI32,win=21,scale=100.0,fb=0.5)))]
for name,ref,real,hr,hs,inv,ik in cases:
    x=check(name,ref,real,hr,hs,inv,ik)
    print(f'== {name} (role {real})')
    for k,v in x.items():
        if k=='trace': print('   trace',' '.join(f'{t:.3e}' for t in v),f'| max {max(v):.3e} vs tol 5e-5 -> {"FAIL" if max(v)>5e-5 else "pass"}')
        elif k=='bound': print('   stoc min/max',v)
        elif isinstance(v,float) or isinstance(v,np.floating): print(f'   {k} {v:.3e}')
        else: print('  ',k,v)

print('--- per-T Roof gain/phase |diff| vs (48,10) tables')
for name in ['NCP','NCL']:
    gs=[];ps=[]
    for T in Ts:
        gg,pp=lsfit(D[f'roof_{name}_s{T}']/A,T); Hx=Hroof(T,48,10)
        gs.append(abs(gg-abs(Hx))); ps.append(abs((pp-np.angle(Hx)+np.pi)%(2*np.pi)-np.pi))
    print(name,'gain',' '.join(f'{v:.3e}' for v in gs),'| phase',' '.join(f'{v:.3e}' for v in ps))
# must_fail IMP
_,_,oA,_=model(inp['s10'],20,48,10,pi=PI32,da=1e-3)
print('IMP must_fail L20 vs NCA model (T=10):',f"{np.abs(D['out_L20_s10']-oA)[r].max():.3e}")
_,_,oL,_=model(inp['s100'],20,48,10)
print('IMP must_fail NCS vs L20 article model (T=100):',f"{np.abs(D['out_NCS_s100']-oL)[r].max():.3e}")
print('start-up INFO L20 s20 rows0-3 out', D['out_L20_s20'][:4], 'stoc', D['stoc_L20_s20'][:4])
print('flat stoc all 0.5?', all(np.all(D[f'stoc_{v}_flat']==0.5) for v in ['L14','L20','L30','S20']))
