"""Find real generated repair patches in the requested views. Projection is an unoccluded upper bound."""
import json
import sys
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0,str(ROOT/'artifacts/surface-wear-r1'))
from bus_world_proof import read

cams = json.loads((OUT/'cameras.json').read_text(encoding='utf-8-sig'))['cameras']
rows = {c['id']:[] for c in cams}
unique = set()
pieces = 0
for file in sorted((ROOT/'Data/raw/derived/bialystok-industrial-c/world').glob('chunk_*.low.glb')):
    _,nodes = read(file)
    for material,attrs in nodes.get('markings',[]):
        if material != 'decal_patch':
            continue
        groups,indices = np.unique(attrs['TEXCOORD_1'],axis=0,return_inverse=True)
        for i,key in enumerate(groups):
            points = attrs['POSITION'][indices==i].astype(float)
            points = np.column_stack((-points[:,0],points[:,2],points[:,1])) # GLTF -> E,N,U
            unique.add(tuple(float(v) for v in key));pieces += 1
            for c in cams:
                eye = np.asarray(c['pos'],float)
                forward = np.asarray(c['look_at'],float)-eye
                forward /= np.linalg.norm(forward)
                right = np.cross(forward,[0,0,1]);right /= np.linalg.norm(right)
                up = np.cross(right,forward)
                relative = points-eye
                z = relative@forward
                if np.any(z <= .1):
                    continue
                tan = np.tan(np.deg2rad(c['fov_deg'])/2)
                uv = np.column_stack((.5+.5*(relative@right)/z/(tan*2340/1080),
                                      .5-.5*(relative@up)/z/tan))
                lo,hi = np.maximum(uv.min(0),0),np.minimum(uv.max(0),1)
                if np.any(hi<=lo):
                    continue
                area = float(np.prod(hi-lo)*2340*1080)
                rows[c['id']].append(dict(chunk=file.name,age=float(key[0]),seed=float(key[1]),
                    centre_enu_m=points.mean(0).tolist(),distance_m=float(np.linalg.norm(points.mean(0)-eye)),
                    screen_bbox_01=[lo.tolist(),hi.tolist()],bbox_area_px_upper_bound=area))
for row in rows.values():
    row.sort(key=lambda p:p['bbox_area_px_upper_bound'],reverse=True)
result = dict(unique_age_seed_pairs=len(unique),chunk_pieces=pieces,
              note='Projection only, before occlusion and rasterisation. Bounds are not a count of visible pixels or photographed repairs. FOV interpretation must be checked against the final Unity views.',
              cameras={k:dict(projected_pieces=len(v),largest=v[:4]) for k,v in rows.items()})
(OUT/'patch-inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(dict(unique_age_seed_pairs=len(unique),chunk_pieces=pieces,
    views={k:dict(pieces=len(v),largest_bbox_px=round(v[0]['bbox_area_px_upper_bound'],1) if v else 0) for k,v in rows.items()}),indent=2))

