"""Small read-only SBS topology diagnostic; graph centre lines are not road surface proof."""
import json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[2]
REGION=ROOT/'Data/Regions/bialystok-industrial-c'
OUT=Path(__file__).with_name('pose-topology');OUT.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
graph=read(REGION/'roads.graph.json');manifest=read(REGION/'generated/world_manifest.json');origin=manifest['origin_epsg2180']
refs=read(REGION/'sbs_references.json')['references'];cameras=read(REGION/'sbs_cameras.json')['cameras']
intrinsics=read(REGION/'sbs_intrinsics.json')['images']
segments=read(REGION/'gate3_segment.json')
value=lambda attrs,key,default=None:attrs.get(key,{}).get('v',default)
normal=[];elevated=[]
for edge in graph['edges']:
    pts=[(p[0]-origin['x'],p[1]-origin['y']) for p in edge['geometry']]
    if not any(-720<x<-360 and -150<y<180 for x,y in pts):continue
    attrs=edge['attrs'];layer=value(attrs,'layer',0)
    is_bridge=value(attrs,'bridge') not in (None,False,'no') or float(layer or 0)>0
    (elevated if is_bridge else normal).append(pts)
fig,ax=plt.subplots(figsize=(9.6,9.6),dpi=100)
fig.patch.set_facecolor('#14202a');ax.set_facecolor('#14202a')
for lines,color,label in ((normal,'#a4adb6','Ground graph centre lines'),(elevated,'#7bbcff','Elevated graph centre lines')):
    ax.add_collection(LineCollection(lines,colors=color,linewidths=2,label=label))
for seg in segments['segments']:
    pts=seg['points_en']
    ax.plot([p[0] for p in pts],[p[1] for p in pts],color='#ffcb62',linewidth=1.5,label=seg['id']+' sampled route')
for name,ring in segments['ring_fits'].items():
    x,y=ring['centre_en']
    if -720<x<-360 and -150<y<180:
        ax.add_patch(plt.Circle((x,y),ring['radius_m'],fill=False,linestyle=':',edgecolor='#f5c7ff',linewidth=1.2,label='Stored ring fit (not a surface)'))
rows=[]
for ident,color,label in [('182011943700132','#ff767e','182 SfM pose (C)'),('494288258686575','#76e0b1','494 deck pose (B)')]:
    cam=next(c for c in cameras if c['id'].endswith(ident));x,y,z=cam['pos'];dx=cam['look_at'][0]-x;dy=cam['look_at'][1]-y
    length=math.hypot(dx,dy);dx=dx/length*40;dy=dy/length*40
    ax.scatter([x],[y],c=color,s=65,zorder=8,label=label)
    ax.annotate('',xy=(x+dx,y+dy),xytext=(x,y),arrowprops={'color':color,'arrowstyle':'->','lw':2})
    ax.annotate(ident[:3]+' U='+str(round(z,2)),(x,y),xytext=(8,5),textcoords='offset points',color=color,fontsize=9)
    record=intrinsics[ident];lon,lat=record['geometry']['coordinates']
    e,n=Transformer.from_crs('EPSG:4326','EPSG:2180',always_xy=True).transform(lon,lat);e-=origin['x'];n-=origin['y']
    ax.scatter([e],[n],c=color,marker='x',s=70,zorder=8)
    ax.plot([x,e],[y,n],color=color,linestyle=':',linewidth=1)
    rows.append({'camera':cam['id'],'stored_pos_enu':cam['pos'],'original_gps_en':[e,n],'gps_delta_en':[e-x,n-y],'note':'Original GPS cross and SfM marker; graph-only diagnostic, no pose approval.'})
ax.set_xlim(-720,-360);ax.set_ylim(-150,180);ax.set_aspect('equal');ax.grid(alpha=.18,color='white')
ax.tick_params(colors='#d6e2ea');ax.set_xlabel('Local East [m]',color='#d6e2ea');ax.set_ylabel('Local North [m]',color='#d6e2ea')
ax.set_title('Putry: stored camera poses and graph topology\nArrows: camera view; crosses: original GPS. North is up.',color='white',fontsize=12)
legend=ax.legend(loc='lower left',fontsize=8,facecolor='#1e2d39',edgecolor='#526777',labelcolor='white')
fig.text(.1,.025,'WORKING_VALUE: source graph, not generated road surfaces; no height or pose correction inferred.',color='#bfccd8',fontsize=8)
fig.subplots_adjust(bottom=.1,left=.1,right=.97,top=.91)
fig.savefig(OUT/'putry-camera-topology.png',facecolor=fig.get_facecolor())
fig.savefig(OUT/'putry-camera-topology.svg',facecolor=fig.get_facecolor())
(OUT/'camera-gps-deltas.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows))
