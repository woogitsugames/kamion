"""Streetscape generator (tools/worldgen/streetscape): paved areas, buildings, furniture, vegetation.

Unit tests run without raw data; output tests read the generated files of the last
`build_world.py --region bialystok-industrial-c` run (instances are in gitignored Data/raw -> skipped).
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest
import shapely
from shapely.geometry import Polygon

from conftest import REGION_DIR, REGION_ID, REPO

WORLD = REPO / "Data" / "raw" / "derived" / REGION_ID / "world"


# ------------------------------------------------------------------------------------------ units
def test_paved_triangulation_covers_polygon():
    from streetscape import paved as PV
    poly = Polygon([(0, 0), (37.3, 2.1), (41.0, 25.5), (12.2, 31.0), (-3.0, 14.0)],
                   [[(10, 10), (15, 10), (15, 14), (10, 14)]])
    T = PV.triangulate(poly)
    a = 0.5 * np.abs((T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) -
                     (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0]))
    assert abs(a.sum() - poly.area) < 1e-3 * poly.area
    edge = np.max(np.linalg.norm(np.diff(np.concatenate([T, T[:, :1]], axis=1), axis=1), axis=2))
    assert edge <= PV.CELL * math.sqrt(2) + 1e-6          # follows the ground every <= 4 m


def test_wall_openings_are_holes():
    """Wall area = full rectangle minus the openings (openings are real holes, not decals)."""
    from streetscape import buildings_mesh as BM
    acc = BM.Acc()
    ops = [(2.0, 3.5, 1.0, 2.5, 0.15, "window", "glass"), (5.0, 8.0, 0.0, 3.0, 0.25, "dock", "dock_door")]
    BM.wall_with_openings(acc, "buildings", "hall_wall_grey", np.array([0.0, 0.0]), np.array([1.0, 0.0]),
                          np.array([0.0, -1.0]), 10.0, 0.0, 6.0, ops)
    V, T = acc.d[("buildings", "hall_wall_grey")][0][:2]
    area = 0.0
    for (V_, T_, *_) in acc.d[("buildings", "hall_wall_grey")]:
        a, b, c = V_[T_[:, 0]], V_[T_[:, 1]], V_[T_[:, 2]]
        area += 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum()
        n = np.cross(b - a, c - a)
        assert (n[:, 1] < 0).all()                         # every wall triangle faces outward (-N here)
    assert abs(area - (60.0 - 1.5 * 1.5 - 3.0 * 3.0)) < 1e-6
    assert ("buildings", "dock_door") in acc.d and ("buildings", "glass") in acc.d


def test_sign_heights_from_regulation():
    from roads import standards as S
    assert S.SIGN_H_MIN == 2.00 and S.SIGN_H_SIDEWALK == 2.20 and S.SIGN_H_OVERHEAD == 5.00   # Tabl. 1.11


def test_sign_faces_shapes_and_determinism():
    from streetscape import signs as SG
    for code in ("A-7", "B-20", "C-12", "D-1", "D-6", "D-15", "B-33_70"):
        shape, im = SG.face(code)
        a = np.asarray(im)[..., 3]
        assert a[256, 256] == 255                          # centre opaque
        assert a[2, 2] == 0                                # corner transparent (plate outline is the shape)
        assert SG.png_bytes(im) == SG.png_bytes(SG.face(code)[1])
    _, a7 = SG.face("A-7")
    rgb = np.asarray(a7)[..., :3].astype(int)
    assert tuple(rgb[180, 256]) == SG.YELLOW                # A-7: yellow field
    assert tuple(rgb[60, 256]) == SG.RED                    # red border at the top edge


# ------------------------------------------------------------------------------------------ outputs
@pytest.fixture(scope="module")
def qa():
    p = REGION_DIR / "generated" / "streetscape_qa.json"
    if not p.exists():
        pytest.skip("streetscape_qa.json not generated")
    return json.loads(p.read_text(encoding="utf-8"))


def test_hero_warehouse_has_docks(qa):
    b = qa["buildings"]
    assert any("9962cca0" in f for f in b["dock_facades"]), "Kwadrat Park override (overrides.yaml) not applied"
    assert b["docks"] >= 10


def test_paved_sources_used(qa):
    src = qa["paved_m2_by_source"]
    assert src["bdot10k_PTPL"][1] > 50_000                   # depot yards etc. are not lawn any more
    assert src["dock_apron"][0] >= 1
    mats = qa["paved_m2_by_material"]
    assert {"yard_paving", "yard_concrete", "yard_asphalt"} <= set(mats)


def test_furniture_counts(qa):
    f = qa["furniture"]
    assert f["lamps"]["rule"] > 100
    assert f["signal_approaches"] > 0
    assert f["junction_signs"].get("C-12", 0) == f["junction_signs"].get("A-7", 0) or \
        f["junction_signs"].get("A-7", 0) > f["junction_signs"].get("C-12", 0)
    assert f["noise_barriers_m"] > 500                      # BDOT10k OT_OIKM_L (Andersa)
    assert f["guardrails_m"]["bridge"] > 0


def test_budget_table_present(qa):
    mb = qa["mesh_budget"]
    assert len(mb["per_chunk"]) == 64
    ids = {f["camera"] for f in mb["frame_estimate"]}
    assert {"stretch_01", "stretch_02", "stretch_03", "stretch_04"} <= ids
    for f in mb["frame_estimate"]:
        assert f["tris_low"] < f["tris_high"]


def test_instances_reference_existing_prototypes():
    if not WORLD.exists() or not list(WORLD.glob("instances_*.json")):
        pytest.skip("world instances not built (Data/raw is gitignored)")
    props = json.loads((REPO / "art-source/world/props/props_meta.json").read_text(encoding="utf-8"))["prototypes"]
    trees = json.loads((REPO / "art-source/world/vegetation/trees_meta.json").read_text(encoding="utf-8"))["trees"]
    # authored landmark assets (ADR 0067 / 0071): prototypes listed in art-source/world/landmarks/<asset>/<asset>_meta.json
    props = dict(props)
    for mf in (REPO / "art-source/world/landmarks").glob("*/*_meta.json"):
        for seg in json.loads(mf.read_text(encoding="utf-8")).get("segments", []):
            props[seg["name"]] = {"tris_lod0": seg["tris"][0]}
    man = json.loads((REGION_DIR / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    n = 0
    for ch in man["chunks"]:
        data = json.loads((REPO / ch["instances"]["file"]).read_text(encoding="utf-8"))
        b = ch["bounds_local_m"]
        for it in data["instances"]:
            if it["p"].startswith("tree_"):
                assert f"{it['p']}_{it['v']}" in trees
            elif it["p"].startswith("landmark_") and it["p"] not in props:                      # hero assets (ADR 0067): own GLB + meta
                lm = {s["name"] for f in (REPO / "art-source/world/landmarks").glob("*/*_meta.json")
                      for s in json.loads(f.read_text(encoding="utf-8"))["segments"]}
                assert it["p"] in lm, it["p"]
            else:
                assert it["p"] in props, it["p"]
            assert b["e_min"] - 0.01 <= it["e"] <= b["e_max"] + 0.01 or b["e_min"] <= -1024 or b["e_max"] >= 1024
            assert 100.0 < it["z"] < 200.0
            n += 1
    assert n > 1000


# ------------------------------------------------------------------------------------------ r2 kit (critic R2)
def test_life_prototypes_budget_and_lods():
    """Static life props: LOD1 well below LOD0, mobile-sized LOD0 (docs/06 par. 6), every prototype buildable."""
    from streetscape import life_props as LP
    P = LP.build_all()
    # prototypes are (lod0, lod1, collision[, lod2]); the optional third LOD came with ADR 0041
    tris = {k: (sum(len(p["T"]) for p in v[0].out()), sum(len(p["T"]) for p in v[1].out())) for k, v in P.items()}
    for k, (t0, t1) in tris.items():
        assert t1 <= t0, k
    for k, v in P.items():
        if k.startswith(("car_", "van_")):
            t2 = sum(len(p["T"]) for p in v[3].out())
            assert 0 < t2 <= 60 and t2 < tris[k][1], k
    # ADR 0041 par. 7 / 9 / r8 (WORKING_VALUE until the phone measurement): cars are seen from 5-12 m, LOD0 is drawn
    # only below 16 m on Low / 37.5 m on High, so LOD0 <= 4000; LOD1 is the Low car from 16 to 45 m (r8, REVIEW r7
    # N-14: rounded shoulders, 10-gon wheels with spoke windows, lamp lenses, housing back plates; the frame limits
    # of test_frame_budget_with_forest_hlod are unchanged) <= 900 (was 650); LOD2 (42.5 / 127.5 - 300 m) <= 60 triangles
    assert max(t0 for k, (t0, _) in tris.items() if k.startswith(("car_", "van_"))) <= 4000
    assert max(t1 for k, (_, t1) in tris.items() if k.startswith(("car_", "van_"))) <= 900
    assert max(t0 for k, (t0, _) in tris.items() if k.startswith("trailer_")) <= 1200
    assert max(t1 for k, (_, t1) in tris.items() if k.startswith("trailer_")) <= 250


def test_parked_cars_road_film_glass_mask_and_wheels():
    """ADR 0041 par. 8: every car / van carries one road-film level on LOD0 and LOD1 (all three levels occur in the
    fleet), LOD0 glazing uses the car-glass shader with a dust mask in UV0, wheels vary, materials exist."""
    import numpy as np
    from streetscape import export as E
    from streetscape import life_cars as LC
    from streetscape import life_props as LP
    from streetscape.materials import M
    levels, wheels = set(), set()
    for k, v in LP.build_all().items():
        if not k.startswith(("car_", "van_")):
            continue
        m0 = {p["mat"]: p for p in v[0].out()}
        m1 = {p["mat"]: p for p in v[1].out()}
        assert set(m0) | set(m1) <= set(M), k
        film = [x for x in m0 if x.startswith("car_dirt_")]
        assert len(film) == 1 and film[0] in m1, k
        levels.add(film[0])
        f = m0[film[0]]
        assert f["UV"][:, 1].min() >= 0.0 and f["UV"][:, 1].max() <= 1.0 + 1e-9
        assert f["V"][:, 2].min() > 0.15 and f["V"][:, 2].max() < 1.25, k        # sills .. below the belt line
        g = np.array(m0["car_glass_tint"]["UV"], float)
        pv = np.abs(g[:, 0]) > 2.0                                                # privacy panes: u offset (par. 9)
        g[pv, 0] -= np.sign(g[pv, 0]) * LC.PRIVACY_U
        g = np.abs(g)
        assert 0.69 <= g.max() <= 1.0 + 1e-9, k
        assert pv.any() == (LC._style(k[4:])["privacy"] and not k.startswith("van_")), k
        assert "car_glass_tint" not in m1 and "car_lamp" in m0
        wheels.add(LC._style(k[4:])["wheel"])
    assert levels == {"car_dirt_1", "car_dirt_2", "car_dirt_3"} and len(wheels) >= 3
    assert M["car_glass_tint"]["shader"] == "car_glass" and M["car_glass_tint"]["rough"] <= 0.1
    assert M["car_dirt_1"]["alpha"] < M["car_dirt_2"]["alpha"] < M["car_dirt_3"]["alpha"]
    a = np.asarray(E.car_dirt_png())[:, :, 3] / 255.0
    assert a[0].max() < 0.05 and a[-8:].mean() > 0.6                              # clear top edge, dense at the sill
    assert np.abs(a[:, 0] - a[:, -1]).mean() < 0.12                                # tiles along the body


def test_facade_signs_are_functional_text_only():
    """Fascia signs carry functional lettering only (no brand names, CLAUDE.md rule 8)."""
    from streetscape import life_props as LP
    allowed = {"HALA", "A", "B", "C", "D", "BIURO", "RECEPCJA", "DOSTAWY", "PORTIERNIA", "MAGAZYN", "SERWIS"}
    for code, text in LP.SIGNS.items():
        assert set(text.split()) <= allowed, text
        im = LP.sign_texture(code)
        assert im.size[1] == 64 and im.size[0] >= 64


def test_decal_lift_order():
    """Decals never z-fight: patch < oil < paint, all above the road surface."""
    from roads import decals as DC
    from roads import standards as S
    assert 0 < DC.LIFT_PATCH < DC.LIFT_OIL < S.MARKING_LIFT


def test_band_edges_avoid_openings():
    """Cladding band edges and colour-field edges move off openings (no fake sills or jambs)."""
    from streetscape import facade_kit as FK
    ops = [(2.0, 5.0, 1.2, 4.2, 0.25, "dock", "dock_door"), (8.0, 9.0, 0.15, 2.25, 0.08, "door", "door_steel")]
    z = FK.safe_z(3.0, ops, 0.6, 9.0)
    assert z is not None and all(not (o[2] < z < o[3]) for o in ops)
    u = FK.safe_u(8.5, ops, 20.0)
    assert u is not None and all(not (o[0] <= u <= o[1]) for o in ops)


def test_life_props_and_gate_kit_placed(qa):
    life = qa["furniture"]["life"]
    assert life["dock_trailers"] >= 20
    assert life["parking"]["cars"] + life["parking"]["vans"] >= 50
    assert life["pallets"] >= 50 and life["bins"] >= 10
    gates = qa["furniture"]["gates"]
    assert gates["stale"] == [] and [g["id"] for g in gates["applied"]] == ["kwadrat-park-gate-kit"]
    assert gates["applied"][0]["gatehouse"] is not None and gates["applied"][0]["fence_m"] > 10


def test_truck_yards_are_behaton(qa):
    mats = qa["paved_m2_by_material"]
    assert mats.get("yard_behaton", 0) > 20_000
    assert mats.get("yard_paving", 0) > 0                   # car parks / footways keep rectangular blocks


def test_embankment_barriers_found(qa):
    """The embankment rule (fill > 2 m) measured at the toe of the slope, not on the berm."""
    f = qa["furniture"]
    assert f["guardrails_m"]["embankment"] > 0
    assert f["embankment_check"]["max_drop_m"] > f["embankment_check"]["threshold_m"]


def test_gate_split_has_kerb_chamfer():
    """Kwadrat Park gate: the two-way access road splitting into entry/exit lanes is joined by a kerb chamfer,
    not a lateral kerb step (visual-critic R2 #10)."""
    p = REGION_DIR / "generated" / "roads_qa.json"
    if not p.exists():
        pytest.skip("roads_qa.json not generated")
    notes = json.loads(p.read_text(encoding="utf-8"))["junction_notes"]
    gate = [v for k, v in notes.items() if "1882887381" in k]
    assert gate and any("chamfer" in n or "kerb line continued" in n for n in gate[0])


def test_photo_matched_overrides_applied(qa):
    """Bridge styles, the Putry gantry and the EC chimneys (CC0 photos / OSM ground truth) are all applied."""
    lm = qa["furniture"]["landmarks"]
    assert lm["stale"] == []
    assert {g["id"] for g in lm["gantries"]} == {"andersa-putry-approach-gantry",            # + ADR 0069 (Mapillary)
                                                 "andersa-putry-cantilever-p37", "andersa-putry-portal-p40"}
    assert len(lm["landmarks"]) == 2
    man = json.loads((REGION_DIR / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    ids = {o["id"] for o in man["overrides_applied"]}
    assert {"andersa-viaduct-biezenstwa-style", "andersa-viaduct-putry-style"} <= ids
    assert man["overrides_stale"] == []


def test_overhead_board_layout():
    from streetscape import signs as SG
    im, w, h = SG.overhead_board([(["E67"], "Warszawa"), (["65"], "Ełk")])
    assert 1.0 < h < 2.0 and w > h
    r, g, b = im.convert("RGB").getpixel((im.size[0] // 2, im.size[1] - 2))
    assert g > r                                            # green field (white border is inside the edge)


def test_yards_have_trucks_and_containers(qa):
    """Truck yards are not empty plains (critic R2 #2): parked trailers, coupled and solo tractors, containers."""
    life = qa["furniture"]["life"]
    assert life["yard_trailers"] >= 50 and life["coupled"] >= 10 and life["solo_tractors"] >= 10
    assert life["containers"] >= 4
    assert life["tyre_scrub_tracks"] >= 2 * qa["furniture"]["life"]["dock_trailers"]


def test_second_lamp_family_on_side_streets(qa):
    fam = qa["furniture"]["lamps"]["by_family"]
    old = sum(v for k, v in fam.items() if k.startswith("lamp_old_"))
    assert old >= 50 and fam.get("lamp_12m", 0) > 0          # older family exists, main roads keep the modern one


def test_vehicle_prototypes_are_plain():
    """Tractor and container prototypes: two LODs, LOD1 much lighter, no texture beyond plate/corrugation."""
    from streetscape import life_props as LP
    for m0, m1, col in (LP.tractor("white"), LP.container(40, "rust"), LP.container(20, "blue")):
        t0 = sum(len(p["T"]) for p in m0.out())
        t1 = sum(len(p["T"]) for p in m1.out())
        assert 0 < t1 < t0 <= 1500 and col is not None
    a, b = LP.tractor_extent()
    assert -2.0 < a < -1.0 and 4.0 < b < 5.5                      # 4x2 tractor ~6.2 m long


def test_ground_props_off_the_carriageway(qa):
    """Lamp / sign / signal bases are pushed off the carriageway (the Unity importer counted 88 on the road)."""
    r = qa["furniture"]["props_off_carriageway"]
    assert r["moved"] > 0 and r["still_on_road"] <= 5


# ------------------------------------------------------------------------------------------ wires / run-off (r6 W-P0)
@pytest.mark.parametrize("L", [5.0, 7.3, 14.0, 41.0, 80.0, 123.0, 250.0, 350.0])
@pytest.mark.parametrize("dz", [-8.0, 0.0, 2.5, 12.0])
def test_wire_catenary_smooth(L, dz):
    """Power-line conductor = catenary sampled every <= 5 m; no segment turns > 10 deg against its neighbour within
    one span (REVIEW r6 W-P0: zigzags), ends exactly on the supports, level span sags sag_ratio * L."""
    from streetscape import furniture as FU
    za = 140.0
    t, z, dzdx = FU.catenary_span(L, za, za + dz)
    x = t * L
    assert abs(z[0] - za) < 1e-6 and abs(z[-1] - (za + dz)) < 1e-6
    seg = np.hypot(np.diff(x), np.diff(z))
    assert seg.max() <= FU.WIRE_SAMPLE_M + 0.05
    assert FU._max_turn_deg(np.column_stack([x, z])) <= 10.0
    # analytic tangent agrees with the chord slopes (the engine ribbon expands across this tangent)
    mid = 0.5 * (dzdx[1:] + dzdx[:-1])
    assert np.abs(mid - np.diff(z) / np.diff(x)).max() < 0.02
    if dz == 0.0:
        sag = za - z.min()
        assert abs(sag - FU.WIRE_SAG_RATIO * L) <= 0.03 * FU.WIRE_SAG_RATIO * L + 0.02


def test_wires_in_region_smooth(qa):
    f = qa["furniture"]
    assert f["wire_max_seg_m"] <= 5.05
    assert f["wire_max_turn_deg"] <= 10.0


def test_runoff_uv1_half_float_safe():
    """Wall-top TEXCOORD_1 is shifted by whole layer periods per quad: |u| stays small (half floats in the engine)
    while the pattern position (u mod period) is unchanged."""
    from streetscape import buildings_mesh as BM
    P = BM.RUNOFF_PERIOD_M
    for ua in (0.0, 13.7, 230.4, 1999.0):
        uv = np.array(BM.runoff_uv1((10.0, 5.3, 0.8), ua, ua + 31.0, 4.0, 9.6))
        assert 0.0 <= uv[0, 0] < P and abs(uv[1, 0] - uv[0, 0] - 31.0) < 1e-9
        assert abs(((uv[0, 0] - (5.3 + ua)) / P) - round((uv[0, 0] - (5.3 + ua)) / P)) < 1e-9
        assert abs(uv[0, 1] - (1 + 6.0 / 0.8)) < 1e-9 and abs(uv[2, 1] - (1 + 0.4 / 0.8)) < 1e-9
    assert BM.runoff_uv1(None, 0, 1, 0, 1) is None


def test_every_hall_wall_has_runoff_uv1(qa):
    """Parapet run-off streaks need TEXCOORD_1 on every hall_wall_* triangle (LOD0 and LOD1)."""
    r = qa["buildings"]["hall_wall_runoff_tris"]
    assert r["with_uv1"] > 1000 and r["without_uv1"] == 0
