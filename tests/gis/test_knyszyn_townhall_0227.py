"""Contract checks for the authored town hall; this does not replace visual QA."""
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import MultiPoint, Point, Polygon

from streetscape import buildings_mesh as BM
from streetscape import knyszyn_townhall_0227 as townhall

ROOT = Path(__file__).resolve().parents[2]


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, vertices, uv, triangles, src, UV1=None):
        self.parts.append((layer, mat, np.asarray(vertices), np.asarray(triangles), src))


def source():
    fc = json.loads((ROOT / "Data/Regions/knyszyn/buildings.geojson").read_text(encoding="utf-8"))
    return {"features": [f for f in fc["features"] if f["id"] in townhall.IDS]}


def test_targets_are_region_specific_and_all_or_nothing():
    fc = source()
    assert townhall.hero_targets("knyszyn", fc) == {bid: townhall.ASSET_ID for bid in townhall.IDS}
    assert townhall.hero_targets("knyszyn-w", fc) == {}
    assert townhall.hero_targets("knyszyn", {"features": fc["features"][:1]}) == {}


def test_real_footprints_produce_valid_geometry_on_both_lods():
    fc = source()
    blds = BM.load(fc, [761611, 612607], [], hero=townhall.hero_targets("knyszyn", fc))
    buf, report = Buffer(), {}
    result = townhall.build(buf, "knyszyn", blds, lambda e,n: np.zeros_like(e)+125, report)
    assert result["status"] == "applied" and result["column_count"] == 4
    assert {p[0] for p in buf.parts} == set(townhall.LAYERS)
    assert {p[1] for p in buf.parts} == {"plaster_white", "plaster_cream", "plinth_dark", "roof_tiles_red", "glass"}
    for layer, material, v, tris, src in buf.parts:
        assert np.isfinite(v).all() and tris.min() >= 0 and tris.max() < len(v)
        area2 = np.linalg.norm(np.cross(v[tris[:,1]]-v[tris[:,0]], v[tris[:,2]]-v[tris[:,0]]), axis=1)
        assert (area2 > 1e-9).all()
        assert src == townhall.ASSET_ID


def test_generic_geometry_is_not_doubled_if_replacement_not_activated():
    blds = BM.load(source(), [761611, 612607], [])
    buf = Buffer()
    result = townhall.build(buf, "knyszyn", blds, lambda e,n: np.zeros_like(e), {})
    assert result["status"] == "skipped" and not buf.parts


def test_real_roof_and_facades_stay_on_bdot_footprints():
    """Regression: rectangle facade floated 3–5 m and roof exceeded footprint by ~150 m²."""
    fc = source()
    blds = BM.load(fc, [761611, 612607], [], hero=townhall.hero_targets("knyszyn", fc))
    by_id = {b["id"]: b["poly"] for b in blds}
    buf = Buffer()
    assert townhall.build(buf, "knyszyn", blds, lambda e,n: np.zeros_like(e)+125, {})["status"] == "applied"
    allowed = shapely.union_all(list(by_id.values())).buffer(1e-5)
    footprint = shapely.union_all(list(by_id.values()))
    for layer, mat, vertices, triangles, _ in buf.parts:
        if mat == "roof_tiles_red":
            planar_triangles = []
            for tri in triangles:
                # Red tile is also reused for the estimated entrance steps.
                if vertices[tri, 2].max() < 126.0:
                    continue
                shape = MultiPoint(vertices[tri,:2]).convex_hull
                assert allowed.covers(shape), (layer, shape.difference(allowed).area)
                if shape.geom_type == "Polygon" and shape.area > 1e-8:
                    planar_triangles.append(shape)
            roof = shapely.union_all(planar_triangles)
            assert footprint.difference(roof).area < .01
        if mat == "glass":
            # Floor windows (not dormers): all vertices sit within 6 cm of an actual source wall.
            lower = vertices[vertices[:,2] < 132.0]
            assert len(lower) > 0
            assert max(min(p.exterior.distance(Point(x,y)) for p in by_id.values()) for x,y in lower[:,:2]) < .06
        if mat == "plaster_cream":
            # Only the portico columns have this material at ground level.
            feet = vertices[np.isclose(vertices[:,2],125.0)]
            assert len(feet) >= 16
            wall = by_id[townhall.CULTURE].exterior
            assert max(wall.distance(Point(x,y)) for x,y in feet[:,:2]) < .71


def test_office_window_axes_cover_split_source_wall_without_floating():
    blds = BM.load(source(), [761611, 612607], [], hero=townhall.hero_targets("knyszyn", source()))
    office = next(b for b in blds if b["id"] == townhall.OFFICE)
    center,axis,*_ = townhall._frame(office["poly"])
    park=np.array([760943.5-761611,612382.3-612607])
    windows=townhall._window_plan(office["poly"],park,axis,9)
    assert len(windows)==9
    positions=[(p-center)@axis for p,t,n in windows]
    assert max(positions)-min(positions)>34.0
    assert all(office["poly"].exterior.distance(Point(p))<1e-6 for p,t,n in windows)
    assert min(np.linalg.norm(a[0]-b[0]) for i,a in enumerate(windows) for b in windows[i+1:])>=1.70


def test_culture_loggia_has_a_real_opening_and_recessed_back():
    fc=source(); blds=BM.load(fc,[761611,612607],[],hero=townhall.hero_targets("knyszyn",fc))
    culture=next(b for b in blds if b["id"]==townhall.CULTURE)
    office=next(b for b in blds if b["id"]==townhall.OFFICE)
    axis=townhall._frame(culture["poly"])[1]
    L,front,tan,out=townhall._facade(culture["poly"],townhall._frame(office["poly"])[0],axis)
    buf=Buffer(); townhall.build(buf,"knyszyn",blds,lambda e,n:np.zeros_like(e)+125,{})
    # The middle of the photographed loggia is actually open at ground floor height;
    # previously a full white wall occupied this plane behind the decorative columns.
    for layer,mat,v,tris,src in buf.parts:
        if layer not in townhall.LAYERS or mat!="plaster_white": continue
        for tri in tris:
            P=v[tri]
            if np.max(np.abs((P[:,:2]-front)@out)) > 1e-5: continue
            uv=np.column_stack(((P[:,:2]-front)@tan,P[:,2]))
            triangle=Polygon(uv)
            if triangle.is_valid and triangle.area>1e-8:
                assert not triangle.covers(Point(0,127.5))
    dark=[v for layer,mat,v,tris,src in buf.parts if layer=="buildings" and mat=="plinth_dark"]
    assert dark
    p=np.concatenate(dark)
    assert np.count_nonzero(np.isclose((p[:,:2]-front)@out,-1.2,atol=1e-5))>=4


def test_low_preserves_landmarks_with_fewer_triangles_and_materials():
    fc=source(); blds=BM.load(fc,[761611,612607],[],hero=townhall.hero_targets("knyszyn",fc))
    buf=Buffer(); r=townhall.build(buf,"knyszyn",blds,lambda e,n:np.zeros_like(e)+125,{})
    by_layer={layer:{mat:len(tris) for ly,mat,v,tris,src in buf.parts if ly==layer} for layer in townhall.LAYERS}
    low=by_layer["buildings_low"]; high=by_layer["buildings"]
    assert set(low)=={"plaster_white","plinth_dark","roof_tiles_red"}
    assert len(low)<len(high)
    assert sum(low.values()) < sum(high.values())*.5
    # Two window rows per planned axis, 2 triangles per pane, plus the dark portico.
    assert low["plinth_dark"] >= 4*sum(r["window_axes"].values())
    assert low["roof_tiles_red"] >= 10


def test_estimated_office_entrances_replace_ground_floor_windows():
    fc=source(); blds=BM.load(fc,[761611,612607],[],hero=townhall.hero_targets("knyszyn",fc))
    office=next(b for b in blds if b["id"]==townhall.OFFICE)
    axis=townhall._frame(office["poly"])[1]
    park=np.array([760943.5-761611,612382.3-612607])
    plan=townhall._window_plan(office["poly"],park,axis,9)
    buf=Buffer(); townhall.build(buf,"knyszyn",blds,lambda e,n:np.zeros_like(e)+125,{})
    for index in (2,7):
        p,tangent,out=plan[index]
        for layer in townhall.LAYERS:
            dark=next(v for ly,mat,v,tris,src in buf.parts if ly==layer and mat=="plinth_dark")
            points=dark[np.isclose((dark[:,:2]-p)@out,.045,atol=1e-5)]
            assert len(points)>=4 and np.isclose(points[:,2].min(),125.55)
        high_glass=next(v for ly,mat,v,tris,src in buf.parts if ly=="buildings" and mat=="glass")
        nearby=high_glass[np.linalg.norm(high_glass[:,:2]-p,axis=1)<1.0]
        assert len(nearby) and nearby[:,2].min() > 129.0


def test_culture_roof_reaches_real_eaves_and_has_upward_normals():
    fc=source(); blds=BM.load(fc,[761611,612607],[],hero=townhall.hero_targets("knyszyn",fc))
    poly=next(b["poly"] for b in blds if b["id"]==townhall.CULTURE)
    triangles=townhall._culture_roof_triangles(poly, 10., 13.)
    assert triangles
    for tri in triangles:
        assert poly.buffer(1e-7).covers(Polygon(tri[:,:2]))
        assert np.cross(tri[1]-tri[0],tri[2]-tri[0])[2]>0
        for p in tri:
            if poly.boundary.distance(Point(*p[:2]))<1e-7:
                assert abs(p[2]-10.)<1e-6
    roof=shapely.union_all([Polygon(t[:,:2]) for t in triangles])
    assert poly.difference(roof).area<1e-6
    assert poly.boundary.difference(roof.boundary.buffer(1e-6)).length<1e-5
    for tri in triangles[::10]:
        xy=tri[:,:2].mean(axis=0)
        assert np.isclose(townhall._culture_roof_sample(triangles,xy),tri[:,2].mean())


def test_culture_dormers_are_lower_on_the_existing_roof():
    fc=source(); blds=BM.load(fc,[761611,612607],[],hero=townhall.hero_targets("knyszyn",fc))
    culture=next(b for b in blds if b["id"]==townhall.CULTURE)
    office=next(b for b in blds if b["id"]==townhall.OFFICE)
    poly=culture["poly"]
    _,axis,_,_,width=townhall._frame(poly)
    length,front,tan,out=townhall._facade(poly,townhall._frame(office["poly"])[0],axis)
    triangles=townhall._culture_roof_triangles(poly,10.,13.)
    for count in (3,5):
        placements=[]
        for j in range(count):
            u=(j-(count-1)/2)*min(3.7,(length-3)/max(1,count-1))
            item=townhall._culture_dormer_placement(poly,triangles,front,tan,out,width,u,13.)
            if item is None:
                continue
            center,base,scale=item
            assert np.isclose((center-front)@out,-width*.12)
            assert np.isclose(base,townhall._culture_roof_sample(triangles,center+out*.55))
            assert base-.15+1.2*scale <= 13.-.08+1e-8
            placements.append(item)
        assert len(placements)>=2
