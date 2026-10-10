"""M7 development: candidate support diagnostics per cell (all own-logger cells W1-W4 and
the W1 HPA-50 / HPA-85 logger cells), sorted by |SLA error|. Output: real/runs/m7_dev_cells.csv."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/labtlc/autoscaler-ope'); sys.path.insert(0,'/home/labtlc/autoscaler-ope/real')
from ope.twin import twin_v2
from ope.policies import REAL_TARGETS
from m5_report import frames, truth_of
sets = {f'{w} own': (w,[f'on_{w}_log_eps{e}_r{r}' for e in ('0.1','0') for r in (1,2)]) for w in ('w1','w2','w3','w4')}
sets['w1 b85']=('w1',[f'on_w1_log_b85_eps0.1_r{r}' for r in (1,2)])
sets['w1 b50']=('w1',[f'on_w1_log_b50_eps0.1_r{r}' for r in (1,2)])
rows=[]
for lab,(w,tags) in sets.items():
    logs=[d for _,d in frames(tags)]; rps,lf=logs[0].rps_target.values,logs[0].load_frac.values
    tw=twin_v2(logs)
    for name,f in REAL_TARGETS.items():
        if name=='hpa70': continue
        tr=truth_of(w,name); rng=np.random.default_rng(0)
        S=[];W=[];M=[];F=[]
        for _ in range(20):
            sla,cost=tw.rollout(f,rps,lf,rng); S.append(100*sla.mean())
            W+=tw._width; M+=tw._mix; F+=tw._far
        W=np.array(W); M=np.array(M)
        est=np.mean(S)
        # K-sensitivity
        ks=[]
        for k in (5,20):
            tw.k=k; rng=np.random.default_rng(0); ks.append(np.mean([100*tw.rollout(f,rps,lf,rng)[0].mean() for _ in range(20)]))
        tw.k=10
        mixed=(M>0.1)&(M<0.9)
        rows.append(dict(set=lab,target=name,err=abs(est-tr['sla']),far=np.mean(F),
            mixed=mixed.mean(), wide_mixed=(mixed&(W>0.15)).mean(), wide_mixed2=(mixed&(W>0.3)).mean(),
            width_med=np.median(W), ksens=abs(ks[0]-ks[1])))
    print(lab,'done',file=sys.stderr,flush=True)
r=pd.DataFrame(rows); r.to_csv('/home/labtlc/autoscaler-ope/real/runs/m7_dev_cells.csv',index=False)
pd.set_option('display.width',200)
print(r.round(3).sort_values('err',ascending=False).to_string(index=False))
