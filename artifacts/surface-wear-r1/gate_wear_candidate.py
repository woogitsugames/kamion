"""INACTIVE candidate for tools/worldgen/streetscape/gate_wear.py (ADR0099).
Straight paired approach strips follow actual gate-builder chains/travel, never procedural arcs.
All dimensions/strength are WORKING_VALUE appearance rules, not measured tyre evidence.
"""
import numpy as np
import shapely
from shapely.geometry import Polygon
from roads.build_world import chunk_of
from .furniture import SurfaceTop
from .bus_stop_wear import _height

SPACING_M, WIDTH_M, LENGTH_M, STRENGTH, LIFT_M = 1.6, .20, 4.2, .9, .005
CLEARANCE_M = .15


def _covered(top, polygon):
    """Exact plan-area coverage, not only vertex/centroid sampling."""
    lo=np.floor(np.asarray(polygon.bounds[:2])/top.CELL).astype(int)
    hi=np.floor(np.asarray(polygon.bounds[2:])/top.CELL).astype(int)
    ids=set()
    for i in range(lo[0],hi[0]+1):
        for j in range(lo[1],hi[1]+1):ids.update(top.grid.get((i,j),[]))
    support=shapely.union_all([Polygon(top.A[i,:,:2]) for i in ids])
    return polygon.difference(support).area <= 1e-8


def emit(buf,cases,half_m,forbidden,report):
    rep=report.setdefault("tyre_tracks",{"applied":[],"rejected":[]})
    top=SurfaceTop([p for p in buf.parts if p.layer=="road" and p.mat in ("road_asphalt","road_asphalt_new")],layers=("road",))
    groups=set()
    for p in buf.parts:
        if p.layer=="markings" and p.mat=="decal_tyre":
            centers=p.V[p.T,:2].mean(axis=1);ci,cj=chunk_of(centers[:,0],centers[:,1],half_m)
            groups.update(zip(ci.tolist(),cj.tolist()))
    paint=[Polygon(p.V[t,:2]) for p in buf.parts if p.layer=="markings" and p.mat.startswith("marking_") for t in p.T]
    for case in cases:
        c,s=case["chain"],case["station"]
        tangent=c.line.frame(s)[0];sign=1 if float(np.dot(tangent,case["travel"]))>0 else -1
        stations=s-sign*np.linspace(5.,.8,9)
        center=np.asarray(c.line.offset_point(s-sign*2.9,0.))
        ci,cj=chunk_of(center[0:1],center[1:2],half_m);anchor=(int(ci[0]),int(cj[0]))
        pending=[];reason=None
        if anchor not in groups:reason="would_add_material_group"
        if reason is None:
            for side in (-1,1):
                lat=side*SPACING_M*.5
                a=np.array([c.line.offset_point(float(st),lat+WIDTH_M*.5) for st in stations])
                b=np.array([c.line.offset_point(float(st),lat-WIDTH_M*.5) for st in stations])
                points=np.vstack([a,b]);n=len(stations)
                triangles=np.array([(i,i+1,n+i+1) for i in range(n-1)]+[(i,n+i+1,n+i) for i in range(n-1)])
                polygon=Polygon(np.vstack([a,b[::-1]]))
                clearance=polygon.buffer(CLEARANCE_M,join_style="mitre")
                if not polygon.is_valid or any(clearance.intersects(p) for p in forbidden if p is not None):reason="kerb_island_clearance";break
                if any(polygon.intersects(p) for p in paint):reason="paint_overlap";break
                if not _covered(top,clearance):reason="whole_footprint_outside_asphalt";break
                test=np.vstack([points,points[triangles].mean(axis=1)])
                ci,cj=chunk_of(test[:,0],test[:,1],half_m)
                if any((int(i),int(j))!=anchor for i,j in zip(ci,cj)):reason="cross_chunk_pair";break
                try:z=np.array([_height(top,q) for q in test])
                except ValueError as exc:reason=str(exc);break
                if np.ptp(z)>.20:reason="road_height_discontinuity";break
                vertices=np.column_stack([points,z[:len(points)]+LIFT_M])
                tri=vertices[triangles[0]]
                if np.cross(tri[1]-tri[0],tri[2]-tri[0])[2]<0:triangles=triangles[:,[0,2,1]]
                ss=np.linspace(0,LENGTH_M,n)
                uv=np.column_stack([np.tile(ss,2),np.repeat([0.,1.],n)])
                uv1=np.column_stack([np.full(len(points),LENGTH_M),np.full(len(points),STRENGTH)])
                pending.append((vertices,uv,triangles,uv1,side))
        if reason is not None:
            rep["rejected"].append({"source":case["src"],"lane":case["name"],"reason":reason})
            continue
        # Pair-atomic: never leave a single unsupported wheel strip.
        for vertices,uv,triangles,uv1,side in pending:
            buf.add("markings","decal_tyre",vertices,uv,triangles,UV1=uv1,src=f"tyre:{case['src']}:{case['name']}:{side}")
        rep["applied"].append({"source":case["src"],"lane":case["name"],"working_value":True,
                               "chunk":list(anchor),"spacing_m":SPACING_M,"width_m":WIDTH_M,"length_m":LENGTH_M,
                               "strength":STRENGTH,"lift_m":LIFT_M,"clearance_m":CLEARANCE_M,
                               "triangles":32,"vertices":36,"new_source_material_groups":0,
                               "center_en":center.tolist(),"travel_en":np.asarray(case["travel"]).tolist()})
    return rep
