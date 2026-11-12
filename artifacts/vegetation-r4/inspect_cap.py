"""Small, read-only four-bed geometry study on flat ground; no build or tests."""
import hashlib
import argparse
import json
import sys
from pathlib import Path

here=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--label',default='a')
args=parser.parse_args()
root=here.parents[1]
sys.path.insert(0,str(root/'tools/worldgen'))
import numpy as np
import shapely
import yaml
from shapely.geometry import Polygon
from streetscape import plantings as pt

origin=json.loads((here/'snapshot-candidate-a/world_manifest.json').read_text())['origin_epsg2180']
origin=np.array([origin['x'],origin['y']])
plans=yaml.safe_load((root/'Data/Regions/bialystok-industrial-c/overrides.yaml').read_text(encoding='utf-8'))['overrides']
original=pt._fill
original_annulus=pt._annulus_triangles
original_strip=pt._hedge_ring_strip
records=[]
triangle_counts={}
footprints=[]
strip_metrics=[]
active=None
ring_sets=[]
annuli=[]
def capture_annulus(lower,upper):
    triangles=original_annulus(lower,upper)
    points=np.vstack([lower,upper])
    faces=shapely.polygons(points[triangles])
    union=shapely.union_all(faces)
    target=Polygon(lower).symmetric_difference(Polygon(upper))
    annuli.append(dict(triangles=len(triangles),invalid_triangles=int((~shapely.is_valid(faces)).sum()),
        overlap_m2=float(shapely.area(faces).sum()-union.area),
        annulus_difference_m2=union.symmetric_difference(target).area))
    return triangles
def capture_strip(rings,*args,**kwargs):
    ring_sets.append(rings)
    return original_strip(rings,*args,**kwargs)
def capture_fill(ring,spacing):
    vertices,triangles=original(ring,spacing)
    edges=vertices[triangles[:,[1,2,0]]]-vertices[triangles]
    faces=shapely.polygons(vertices[triangles])
    union=shapely.union_all(faces)
    records.append(dict(bed=active,spacing_m=spacing,boundary_vertices=len(ring),
        interior_vertices=len(vertices)-len(ring),triangles=len(triangles),
        ring_valid=Polygon(ring).is_valid,ring_reason=shapely.is_valid_reason(Polygon(ring)),
        ring_area_m2=Polygon(ring).area,
        overlap_m2=float(shapely.area(faces).sum()-union.area),
        outside_m2=union.difference(Polygon(ring)).area,
        coverage_difference_m2=union.symmetric_difference(Polygon(ring)).area,
        maximum_triangle_edge_m=float(np.linalg.norm(edges,axis=2).max())))
    return vertices,triangles
class Capture:
    def __init__(self): self.parts=[]
    def add(self,layer,material,vertices,uv,triangles,**kwargs):
        triangle_counts[active]=triangle_counts.get(active,0)+len(triangles)
        self.parts.append(np.asarray(vertices))
pt._fill=capture_fill
pt._annulus_triangles=capture_annulus
pt._hedge_ring_strip=capture_strip
try:
    for plan in plans:
        if plan.get('kind')!='plantings': continue
        for bi,bed in enumerate(plan.get('beds',[])):
            poly=Polygon(np.asarray(bed['ring'],float)-origin)
            poly=shapely.make_valid(poly).buffer(-float(bed.get('rim_m',.6))).buffer(.25)
            preset=pt.species(bed.get('plant','berberis_red'))
            for gi,g in enumerate(getattr(poly,'geoms',[poly])):
                if g.geom_type!='Polygon' or g.area<1: continue
                key=(plan['id'],bi,gi)
                width=bed.get('band_m')
                if width is None and preset.get('band'):
                    width=preset['band'][0]+pt._h(*key,'band')*(preset['band'][1]-preset['band'][0])
                if width: g=pt.band_of(g,float(width))
                if g.geom_type!='Polygon' or g.area<.5: continue
                active=bed.get('name',str(bi))
                sampled=Polygon(pt._offset_ring(g,0.0,step=.3,anchor=np.asarray(g.exterior.coords)[0]))
                footprints.append(dict(bed=active,authored_band_area_m2=g.area,
                    sampled_area_m2=sampled.area,area_difference_percent=100*(sampled.area/g.area-1),
                    boundary_hausdorff_m=g.boundary.hausdorff_distance(sampled.boundary)))
                capture=Capture()
                ring_sets.clear()
                annuli.clear()
                pt.hedge_mass(capture,g,lambda x,y:np.zeros_like(x),key,
                    h=bed.get('height_m'),plant=bed.get('plant','berberis_red'))
                cr=[p for p,z in ring_sets[0]]
                sr=[p for p,z in ring_sets[1]]
                outside=[Polygon(c).difference(Polygon(s)).area for c,s in zip(cr,sr)]
                strip_metrics.append(dict(bed=active,core_outside_shell_m2=outside,
                    core_ring_sizes=[len(p) for p in cr],shell_ring_sizes=[len(p) for p in sr],strips=list(annuli)))
finally:
    pt._fill=original
    pt._annulus_triangles=original_annulus
    pt._hedge_ring_strip=original_strip
result=dict(source_sha256=hashlib.sha256((root/'tools/worldgen/streetscape/plantings.py').read_bytes()).hexdigest(),
    caps=records,footprints=footprints,strip_metrics=strip_metrics,
    triangles_by_bed=triangle_counts,total_triangles=sum(triangle_counts.values()),
    note='Four authored footprints, flat z=0; no World, GIS pytest, Unity, or production write. Internal fill observation only; no visual acceptance.')
(here/('cap-study-'+args.label+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
