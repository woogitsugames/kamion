"""Draft for plantings.py; not imported by the baseline generator."""
import numpy as np
import shapely
from shapely.geometry import LineString,Polygon
from streetscape import plots as PLT
from terrain_mesh.chunks import CHUNK_M


def _garden_groups(buf, half):
    groups = {}
    for part in buf.parts:
        if part.layer not in (PLT.KIT_LAYER,PLT.KIT_LAYER_LOW) or part.mat != 'plot_kit':
            continue
        centers = part.V[part.T].mean(axis=1)
        cells = np.floor(np.column_stack((centers[:,0]+half,half-centers[:,1]))/CHUNK_M).astype(int)
        for cell in sorted(set(map(tuple,cells))):
            vertices = part.V[part.T[np.all(cells==cell,axis=1)]].reshape(-1,3)
            key=(part.layer,*cell);lo,hi=vertices.min(axis=0),vertices.max(axis=0)
            if key in groups:lo,hi=np.minimum(lo,groups[key][0]),np.maximum(hi,groups[key][1])
            groups[key]=(lo,hi)
    return groups


def _inside_garden_groups(output,layer,groups,half):
    V,_,T,_=output
    centers=V[T].mean(axis=1)
    cells=np.floor(np.column_stack((centers[:,0]+half,half-centers[:,1]))/CHUNK_M).astype(int)
    for cell in sorted(set(map(tuple,cells))):
        bounds=groups.get((layer,*cell))
        if bounds is None:return False
        vertices=V[T[np.all(cells==cell,axis=1)]].reshape(-1,3)
        if np.any(vertices<bounds[0]-1e-5) or np.any(vertices>bounds[1]+1e-5):return False
    return True


def front_gardens(buf, rp, zf, report, half=1024.0, triangle_limit=3600):
    """ADR0154: selected missing street hedges, merged into existing plot groups.

    WORKING_VALUE: additional share .70, inset .80m, thickness .65m,
    height fence+.2..+.45m (1.2..2m), based on typology P08/P12.
    No claim of surveyed hedge positions. OSM hedges remain handled separately.
    Gate/door/drive keepouts and original renderer bounds are hard constraints.
    """
    groups=_garden_groups(buf,half)
    rep={'source':'WORKING_VALUE; photos P08/P12, docs/refs/posesje-bialystok.md','plots':0,'segments':0,'m':0.,'tris_high':0,'tris_low':0,'triangle_limit':triangle_limit,'list':[],'skipped':{}}
    def skip(reason):rep['skipped'][reason]=rep['skipped'].get(reason,0)+1
    selected=set()
    for plot in sorted(rp.get('plots',[]),key=lambda p:PLT.hfloat(p['key'],'adr0154-priority')):
        key=plot['key'];lay=plot['lay'];age=plot['age']
        runs=[x for x in lay['runs'] if x['front'] and np.linalg.norm(x['b']-x['a'])>3.]
        old_hedge=bool(runs) and ((plot['front_style'] in PLT.SEE_THROUGH and PLT.hfloat(key,'hedge')<PLT.HEDGE_SHARE[age]*1.6) or PLT.hfloat(key,'hedge')<PLT.HEDGE_SHARE[age]*.5)
        if not runs or old_hedge or plot['front_style'] not in PLT.SEE_THROUGH:continue
        if PLT.hfloat(key,'adr0154-front')>=.70:continue
        blocked=[plot['foot'].buffer(1.)]+list(plot.get('door_zones') or [])
        if plot.get('hard') is not None:blocked.append(plot['hard'].buffer(.5))
        gates=([lay['gate']] if lay.get('gate') is not None else [])+([lay['wicket']] if lay.get('wicket') is not None else [])+list(lay.get('wickets') or [])
        for gate in gates:
            m,n=np.asarray(gate['m']),np.asarray(gate['n'])
            blocked.append(LineString([m-n*5,m+n*3]).buffer(gate['w']/2+.65,cap_style='flat'))
        forbidden=shapely.union_all(blocked)
        h=min(2.,max(1.2,plot['front_h']+.2+.25*PLT.hfloat(key,'adr0154-height')))
        for run in runs:
            a,b=np.asarray(run['a']),np.asarray(run['b']);normal=np.asarray(run['n']);t=(b-a)/np.linalg.norm(b-a)
            line=LineString([a+t*.4-normal*.8,b-t*.4-normal*.8]).difference(forbidden)
            for segment in getattr(line,'geoms',[line]):
                if segment.geom_type!='LineString' or segment.length<2.:continue
                if not plot['poly'].buffer(-.1).covers(segment.buffer(.45,cap_style='flat')):
                    skip('outside_plot');continue
                q0,q1=np.asarray(segment.coords[0]),np.asarray(segment.coords[-1])
                kit=PLT.Kit();kit.tag='garden_front_0154'
                length=PLT.hedge(kit,q0,q1,normal,zf,h,(key,'adr0154',round(float(q0[0]),2),round(float(q0[1]),2)),thick=.65)
                high,low=kit.out(),kit.out(low=True)
                if high is None or low is None:continue
                if rep['tris_low']+len(low[2])>triangle_limit:skip('triangle_limit');continue
                if not _inside_garden_groups(high,PLT.KIT_LAYER,groups,half) or not _inside_garden_groups(low,PLT.KIT_LAYER_LOW,groups,half):
                    skip('renderer_bounds');continue
                for layer,output in [(PLT.KIT_LAYER,high),(PLT.KIT_LAYER_LOW,low)]:
                    buf.add(layer,'plot_kit',output[0],output[1],output[2],src=f"plot:{plot['id']}:garden-front-0154",COL=output[3])
                rep['segments']+=1;rep['m']+=length;rep['tris_high']+=len(high[2]);rep['tris_low']+=len(low[2]);selected.add(plot['id'])
                rep['list'].append({'plot':plot['id'],'a':q0.tolist(),'b':q1.tolist(),'height_m':h,'length_m':length,'tris_low':len(low[2]),'source':'WORKING_VALUE'})
    rep['plots']=len(selected);rep['m']=round(rep['m'],2);report['garden_fronts']=rep
    return rep
