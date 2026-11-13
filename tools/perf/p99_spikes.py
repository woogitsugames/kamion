import csv,sys,glob,os
import numpy as np
base=r'C:\Users\matma\Documents\Claude\kamion\artifacts\gate3'
for ts in sys.argv[1:]:
    p=os.path.join(base,ts,'RFGL34SJYDZ','drive','frametimes.csv')
    rows=list(csv.reader(open(p)))[1:]
    t=np.array([float(r[1]) for r in rows]); f=np.array([float(r[2]) for r in rows])
    c=np.array([float(r[3]) for r in rows]); g=np.array([float(r[4]) for r in rows])
    t0=t[0]; m=t>=t0+25
    tw,fw,cw,gw=t[m],f[m],c[m],g[m]
    n=len(fw); srt=np.sort(fw)[::-1]
    print(f"== {ts} n={n} p99={np.percentile(fw,99):.2f} >40:{(fw>40).sum()} >45:{(fw>45).sum()} >50:{(fw>50).sum()} >60:{(fw>60).sum()} 1%rank={int(n*0.01)} top25={np.round(srt[:25],1).tolist()}")
    idx=np.where(fw>40)[0]
    print("  spikes (t_rel, frame, cpu, gpu):")
    for i in idx: print(f"   {tw[i]-t0:7.2f} {fw[i]:6.1f} cpu {cw[i]:6.1f} gpu {gw[i]:6.1f}  prev {fw[i-1]:.1f} next {fw[min(i+1,n-1)]:.1f}")
    if len(idx)>1:
        d=np.diff(tw[idx]); print("  intervals:",np.round(d,2).tolist())
