"""Small diagnostic resection from two vertical shafts; no generator or asset edit.

Known single-flue diameter provides scale. The GPS is a soft initial estimate,
not a constraint. This is a working photographic fit, not a surveyed pose.
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.optimize import least_squares

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
P = ROOT / 'Data/raw/refs/commons/cmFile_20200711_073128_Elektrociep_ownia_Bia_ystok.jpg.jpg'
im = np.asarray(Image.open(P).convert('RGB')).astype(float)
centres = np.array([[718.26, -1133.29, 137.243], [624.25, -1083.96, 137.262]])
windows = [([(505,545),(675,710)], (2876,3048)),
           ([(65,130),(280,330),(515,560),(720,735)], (3560,3764))]
observed = []
terrain=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/terrain.json').read_text(encoding='utf-8'))
enc=terrain['encoding']; bbox=terrain['bbox']
heightmap=np.memmap(ROOT/enc['file'],dtype='<u2',mode='r',shape=tuple(terrain['samples']))
def ground(e,n):
    x=(e+777995-bbox[0])*(heightmap.shape[1]-1)/(bbox[2]-bbox[0])
    y=(bbox[3]-n-596223)*(heightmap.shape[0]-1)/(bbox[3]-bbox[1])
    i,j=int(x),int(y); dx,dy=x-i,y-j
    q=float(heightmap[j,i])*(1-dx)*(1-dy)+float(heightmap[j,i+1])*dx*(1-dy)+float(heightmap[j+1,i])*(1-dx)*dy+float(heightmap[j+1,i+1])*dx*dy
    return q*enc['scale_m_per_unit']+enc['offset_m']
for spans, (x0,x1) in windows:
    rows = []
    for a,b in spans:
        for y in range(a,b):
            c = im[y,x0:x1]
            good = np.flatnonzero((c[:,0]-c[:,1]>10)&(c[:,0]-c[:,2]>12))
            runs = np.split(good,np.flatnonzero(np.diff(good)>1)+1)
            run = max(runs,key=len)
            if len(run)>=30:
                rows.append([y,x0+(run[0]+run[-1])/2,run[-1]-run[0]+1])
    rows=np.array(rows)
    slope, intercept=np.polyfit(rows[:,0],rows[:,1],1)
    observed.append(dict(slope=float(slope),intercept=float(intercept),rows=rows.tolist()))

def basis(h,p,r):
    h,p,r=np.radians([h,p,r])
    f=np.array([math.sin(h)*math.cos(p),math.cos(h)*math.cos(p),math.sin(p)])
    right=np.array([math.cos(h),-math.sin(h),0.])
    up=np.cross(right,f)
    return np.array([right*math.cos(r)+up*math.sin(r),up*math.cos(r)-right*math.sin(r),f])

def project(points,par):
    xyz=(np.asarray(points)-par[:3])@basis(*par[3:6]).T
    return np.column_stack([1920+par[6]*xyz[:,0]/xyz[:,2],1080-par[6]*xyz[:,1]/xyz[:,2]])

def at_row(i,y,par):
    a=centres[i].copy(); b=a.copy(); b[2]+=120
    # y=(linear z)/(linear z); invert this projection analytically.
    B=basis(*par[3:6]); q=(a-par[:3])@B.T
    target=(1080-y)/par[6]
    z=(target*q[2]-q[1])/(B[1,2]-target*B[2,2])
    return z

def width(i,y,par):
    z=at_row(i,y,par)
    d=7.65+(4.8-7.65)*z/120 if i==1 else 8.27189+(par[7]-8.27189)*z/120
    angles=np.arange(64)*2*math.pi/64
    pts=centres[i]+np.column_stack([np.cos(angles)*d/2,np.sin(angles)*d/2,np.full(64,z)])
    x=project(pts,par)[:,0]
    return x.max()-x.min()

def residual(par):
    vals=[]
    for i,top in enumerate([320.,22.]):
        obs=observed[i]
        pix=project([centres[i]+[0,0,120]],par)[0]
        vals.extend([(pix[0]-(obs['intercept']+obs['slope']*top))/3,(pix[1]-top)/6])
        axis=project([centres[i]+[0,0,70],centres[i]+[0,0,110]],par)
        slope=(axis[1,0]-axis[0,0])/(axis[1,1]-axis[0,1])
        vals.append((slope-obs['slope'])/.002)
        # Window medians reduce texture-edge noise; use 3px uncertainty.
        for spans,_ in [windows[i]]:
            for a,b in spans:
                rows=np.array(obs['rows']); rows=rows[(rows[:,0]>=a)&(rows[:,0]<b)]
                y=np.median(rows[:,0]); w=np.median(rows[:,2])
                vals.append((width(i,y,par)-w)/3)
    vals.extend([(par[2]-ground(*par[:2])-1.65)/1.,(par[6]-2880)/500])
    return vals

solutions=[]
for focal in [2300.,2880.,3400.]:
    for north in [-700.,-850.]:
        init=[600.,north,142.,140.,5.,0.,focal,7.]
        fit=least_squares(residual,init,bounds=([0,-1050,132,80,-15,-10,1600,4],[1000,-400,152,200,20,10,4400,9]),max_nfev=300)
        par=fit.x
        solutions.append(dict(parameters=par.tolist(),cost=float(fit.cost),residual=residual(par),
                              projections=[project([c+[0,0,120]],par)[0].tolist() for c in centres],
                              estimated_bands_z=[[float(at_row(i,y,par)) for y in yy] for i,yy in enumerate([[400,482,567,650,735],[150,256,478,584,689]])]))
result=dict(status='WORKING_VALUE photographic fit; not surveyed. Manual top picks, assumed 120m top, diameter/EXIF and lens uncertainty remain.',
            parameter_order=['local_e','local_n','camera_absolute_z','heading_deg','pitch_deg','roll_deg','focal_pixels','multi_top_diameter_WORKING_VALUE'],
            assumptions='Single-flue base/top 7.65/4.80m from ENEA; multi base 8.27189m from OSM outline (uncertain interpretation). Radial envelope approximated at centre height. No lens distortion.',
            source=str(P.relative_to(ROOT)),observed=observed,solutions=solutions)
(OUT/'photo-pose-fit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
best=min(solutions,key=lambda s:s['cost'])
best['camera_ground_NMT']=ground(*best['parameters'][:2])
print(json.dumps({k:v for k,v in best.items()},indent=2))
