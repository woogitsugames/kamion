import csv,sys,os
import numpy as np
base=r'C:\Users\matma\Documents\Claude\kamion\artifacts\gate3'
for ts in sys.argv[1:]:
    rows=list(csv.reader(open(os.path.join(base,ts,'RFGL34SJYDZ','drive','frametimes.csv'))))[1:]
    a=np.array([[float(x) for x in r[1:5]] for r in rows]); t,f,c,g=a.T
    m=t>=t[0]+25; f,c,g=f[m],c[m],g[m]; gv=g[g>0]
    sp=f>40
    print(f"{ts} gpu p50 {np.percentile(gv,50):.2f} p90 {np.percentile(gv,90):.2f} p95 {np.percentile(gv,95):.2f} >33.3: {(gv>33.3).mean()*100:.1f}% >34: {(gv>34).mean()*100:.1f}% | cpu p50 {np.percentile(c,50):.1f} p95 {np.percentile(c,95):.1f} | spikes gpu>33.3 {(g[sp]>33.3).sum()}/{sp.sum()} gpu0 {(g[sp]==0).sum()} cpu>30 {(c[sp]>30).sum()} | gpu0 frames total {(g==0).sum()}")
