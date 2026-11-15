"""ADR 0236: direction signs (E) of route C by research R2 and the sign regulation.

[ZNAKI-Z1] = Dz.U. 2019 poz. 2311, załącznik nr 1 (numbers and their tables: streetscape/sign_norms.py).
Unit tests need no raw data; the region tests read only files in git (overrides.yaml, roads.graph.json,
generated/streetscape_qa.json, generated/control_cameras.json, art-source/world/props/props_meta.json).
"""
from __future__ import annotations

import json
import re

import numpy as np
import pytest
import yaml

from conftest import REGION_DIR, REPO

from roads import build_world as BW
from streetscape import brand_filter as BF
from streetscape import gate3_landmarks as G3
from streetscape import landmarks as LM
from streetscape import life_props as LP
from streetscape import props as PP
from streetscape import sign_norms as SN
from streetscape import signs as SG
from streetscape import signs_route as SR

pytestmark = pytest.mark.unit

# Words that must never appear on a board: BRAND-SWEEP list of brand_filter + company forms. Place names, road
# numbers and street / district names are allowed.
FORBIDDEN = re.compile(BF.BRAND_RE.pattern + r"|(?i:\bspółka\b|\bsp\.? ?j\.|\bS\.A\b|®|™|\.pl\b|\.com\b|www\.)")
ALLOWED_TEXT = re.compile(r"^[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9 .:/\-|]+$")


def _overrides():
    return yaml.safe_load((REGION_DIR / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]


def _board_texts(o):
    out = []
    for bd in o.get("boards", []):
        out += [r[1] for r in LM._board_rows({"edges": []}, bd, {"stale": []}, o["id"])] if "from_osm" not in bd else []
        out += [x for r in LM._board_rows({"edges": []}, bd, {"stale": []}, o["id"]) for x in r[0]] if "from_osm" not in bd else []
    for pt in o.get("parts", []):
        out += [str(pt[k]) for k in ("text", "plate") if pt.get(k)]
    return out


# ------------------------------------------------------------------------------------------------------- the norm
def test_inscription_length_matches_the_regulation_example():
    # Tabela 1.10 e (s. 19): "Łącko" = 21,99 gr; at d = 210 mm (gr = 35 mm) 769,65 mm (pkt 1.4.2, s. 15)
    assert SN.text_len_gr("Łącko") == pytest.approx(21.99, abs=1e-6)
    assert SN.text_len_m("Łącko", 0.210) == pytest.approx(0.76965, abs=1e-5)
    assert SN.text_len_gr("a b") == pytest.approx(3.75 + 4.5 + 3.75)          # word gap h = 3 o = 4,5 gr


def test_letter_groups_and_tables_are_consistent():
    assert SN.LETTER_D_MM["VI"] == 210 and SN.LETTER_D_MM["IX"] == 420
    # Tabela 9.5.4: d of each size group is a letter group Tabela 1.9 allows for E-2 in that group
    for g, row in SN.E2_BOARD_MM.items():
        assert row["d"] in {SN.LETTER_D_MM[x] for x in SN.E_LETTER_GROUPS["E-2"][g]}, g
        assert row["b"] > row["b1"] > (row["b"] - row["b1"]) / 2 > row["d"]
    # Tabela 9.5.3: route number height = d1 + 2 b + 2 o (rys. 9.5.46), digits one letter group below the name
    for d, r in SN.ROUTE_NO_MM.items():
        assert r["h"] == pytest.approx(r["d1"] + 2 * r["b"] + 2 * r["o"], abs=2), d
        assert r["d1"] < d
    s = SN.ROUTE_NO_STANDALONE_MM
    assert s["h"] == 300 and s["h"] == s["d1"] + 2 * s["b"] + 2 * s["o"]       # pkt 6.3.7.8: 300 mm
    assert SN.size_group(dual=True, built_up=True, v_kmh=70) == "duze"          # pkt 1.2.1 lit. b
    assert SN.size_group(dual=True, built_up=True, v_kmh=50) == "srednie"       # pkt 1.2.1 lit. c
    assert SN.size_group(dual=False, built_up=False, v_kmh=90) == "srednie"
    with pytest.raises(ValueError):
        SN.letter_d_m("E-1", "male")                                            # Tabela 1.9: "-"


def test_row_height_is_the_norm_not_the_old_working_value():
    """Review of PR #62 (D4): overhead_board(row_m=0.62) was above anything the norm gives a general road. The pas
    pisma is 10 gr (pkt 1.4.1); with the largest letters of 'duże' (282 mm) 0.47 m, for group IX 0.70 m only on
    motorways; Tabela 9.5.4 'średnie' = 0.35 m per further row."""
    assert SN.E_OVERHEAD_ROW_M == pytest.approx(0.35)
    assert SN.E_OVERHEAD_ROW_M <= 0.56
    for n in (1, 2, 3, 5):
        im, w, h = SG.overhead_board([(["8"], "Augustów")] * n)
        assert h == pytest.approx(0.50 + 0.35 * (n - 1), abs=0.01), n          # Tabela 9.5.4 'średnie'
        assert h == pytest.approx(SN.e2_rows_h_m(n, 0.210), abs=0.01)
    b = SN.E2_BOARD_MM["srednie"]
    assert SN.e2_rows_h_m(3, 0.210) * 1000 == pytest.approx(b["b"])
    import inspect
    assert "0.62" not in str(inspect.signature(SG.overhead_board)) + str(inspect.signature(SG.panel_board))


def test_letters_have_the_norm_height_and_length():
    N = SG._Norm(0.210, 400)
    im = SG.Image.new("RGBA", (1200, 300), (0, 0, 0, 255))
    N.text(im, 50, 150, "HEN", SG.WHITE)
    a = np.asarray(im.convert("L")) > 128
    ys, xs = np.where(a)
    # capitals: 210 mm high; length by Tabela 1.10
    assert (ys.max() - ys.min() + 1) / 400 == pytest.approx(0.210, abs=0.012)
    # ink extent <= the length between the outer measuring points (the side bearings of the stand-in glyphs)
    ink = (xs.max() - xs.min() + 1) / 400
    assert SN.text_len_m("HEN", 0.210) - 0.05 <= ink <= SN.text_len_m("HEN", 0.210) + 0.005
    assert abs((ys.max() + ys.min()) / 2 - 150) < 4                            # capitals centred on the row axis


def test_rule_boards_use_letter_heights_the_norm_allows():
    assert int(SN.E_OVERHEAD_D_M * 1000) in SN.allowed_d_mm("E-2") & SN.allowed_d_mm("E-1")
    assert int(SN.E_RULE_BOARD_D_M * 1000) in SN.allowed_d_mm("E-2")
    assert int(SN.E1_RULE_D_M * 1000) in SN.allowed_d_mm("E-1")
    im, w, h = SG.direction_board(["Augustów", "Kuźnica PL/BY"], ["8", "19"], green=True)
    assert h == pytest.approx(SN.e2_rows_h_m(2, SN.E_RULE_BOARD_D_M), abs=0.01)   # 0.32 + 0.22 m ('małe' rows)
    assert h == pytest.approx(0.54, abs=0.02) and 1.5 < w < 2.6
    a = np.asarray(im.convert("RGB")).astype(int)
    assert tuple(a[a.shape[0] // 2, 12]) == SG.GREEN
    red = (a[..., 0] > 150) & (a[..., 1] < 80)
    assert red[:, : a.shape[1] // 3].sum() > 50 * red[:, a.shape[1] // 2:].sum()       # numbers LEFT of the names
    im, w, h = SG.direction_board(["os. Białostoczek"], [], green=False)
    assert tuple(np.asarray(im.convert("RGB"))[h and 20, 20]) == SG.WHITE
    im, w, h = SG.roundabout_diagram([(0.0, ["Augustów", "Kuźnica PL/BY"], ["8", "19"]),
                                      (-85.0, ["Lublin", "Bobrowniki PL/BY"], ["19", "65"]), (90.0, ["Centrum"], ["675"])])
    assert 2.5 < w < 6.0 and 1.5 < h < 3.0


def test_route_number_plates():
    """E-15a / E-16 on their own: 300 mm high (pkt 6.3.7.8), width = 2 m + digits at d1 = 162 mm (rys. 9.5.46)."""
    assert G3.face_dim("E-15", "19") == ("rect", pytest.approx(0.413, abs=0.002), 0.3)
    assert G3.face_dim("E-15", "8")[1] == pytest.approx(0.244 + 4.0 * 0.027, abs=0.002)
    w2 = G3.face_dim("E-15", "8|19")[1]
    assert w2 == pytest.approx(G3.face_dim("E-15", "8")[1] + G3.face_dim("E-15", "19")[1] + G3.ROUTE_NO_GAP_M, abs=0.002)
    im = G3.draw_face("E-15", 330, 240, "19")
    a = np.asarray(im).astype(int)
    assert tuple(a[30, 165]) == SG.RED and (a.min(axis=2) > 200).mean() > 0.08         # red field, white digits + frame
    g = np.asarray(G3.draw_face("E-16", 482, 240, "E67")).astype(int)
    assert tuple(g[30, 240]) == SG.GREEN
    lod0, lod1, col, atlas, (wm, hm), key, top = G3.assembly_mesh([{"face": "E-15", "text": "8|19"},
                                                                  {"face": "E-16", "text": "E67"}])
    assert sum(len(p["T"]) for p in lod0.out()) <= 40 and {p["mat"] for p in lod0.out()} == {f"sign_{key}"}
    assert top == pytest.approx(2.0 + 0.3 + 0.05 + 0.3 + 0.05)                # lower edge 2.00 m (Tabela 1.11)


def test_faces_are_deterministic():
    def b(im):
        return SG.png_bytes(SG.weather(im, "k", 0.7))
    makers = [
        lambda: SG.overhead_board([(["8", "E67"], "Warszawa"), (["65"], "Ełk")], size_m=(3.75, 0.82), arrows=2)[0],
        lambda: SG.panel_board([{"arrow": "none", "rows": [(["8", "E67"], "Warszawa")]},
                                {"arrow": "fork_right", "rows": [(["19"], "Kuźnica PL BY"), (["675"], "Centrum")]}],
                               size_m=(3.3, 1.5), single_frame=True)[0],
        lambda: SG.e1_cross_board([(["8", "E67"], "Warszawa")], [(["675"], "Centrum")], [(["19"], "Kuźnica PL BY")])[0],
        lambda: SG.direction_board(["Augustów"], ["8"], True)[0],
        lambda: SG.roundabout_diagram([(0.0, ["Augustów"], ["8"]), (90.0, ["Centrum"], [])])[0],
        lambda: G3.atlas([{"face": "E-15", "text": "8|19"}, {"face": "E-16", "text": "E67"}], "galv")[0],
    ]
    for mk in makers:
        assert b(mk()) == b(mk())


def test_authored_size_wins_and_content_fits():
    rows = [{"arrow": "up", "rows": [(["8", "E67"], "Warszawa"), (["65"], "Ełk")]},
            {"arrow": "right", "rows": [(["8", "E67"], "Augustów"), (["19"], "Kuźnica PL BY")]}]
    im, w, h = SG.panel_board(rows, size_m=(5.0, 2.3))
    assert (w, h) == pytest.approx((5.0, 2.3), abs=0.01)
    im, w, h = SG.e1_cross_board([(["8", "E67"], "Warszawa"), (["65"], "Ełk")], [(["675"], "Centrum")],
                                 [(["8", "E67"], "Augustów"), (["19"], "Kuźnica PL BY")], (4.6, 1.85))
    assert (w, h) == pytest.approx((4.6, 1.85), abs=0.01)
    a = np.asarray(im.convert("RGB")).astype(int)
    # nothing but the green field and the white frame in the outer 0.06 m: no inscription runs off the board
    k = int(0.06 * 160)
    edge = np.concatenate([a[:, :k].reshape(-1, 3), a[:, -k:].reshape(-1, 3)])
    assert not ((edge[:, 0] > 150) & (edge[:, 1] < 80)).any()                  # no red route number cut by the edge


# ------------------------------------------------------------------------------------------ brands, synthetic + C
def test_no_brand_reaches_a_board():
    kept, dropped = BF.neutral_destinations(["Augustów", "stacja paliw BP", "Galeria Biała", "Centrum handlowe"])
    assert kept == ["Augustów", "Centrum handlowe"] and len(dropped) == 2
    assert FORBIDDEN.search("stacja paliw Orlen") and not FORBIDDEN.search("Kuźnica PL BY")
    src = (REPO / "tools/worldgen/streetscape/furniture.py").read_text(encoding="utf-8")
    assert "BF.neutral_destinations" in src.split("def direction_boards")[1].split("\ndef ")[0]


def test_region_c_board_texts_have_no_brands():
    n = 0
    for o in _overrides():
        if o.get("kind") not in ("sign_gantry", "gate3_sign"):
            continue
        for t in _board_texts(o):
            n += 1
            assert not FORBIDDEN.search(t), (o["id"], t)
            assert ALLOWED_TEXT.match(t.replace("\n", " ")) or o.get("kind") == "gate3_sign", (o["id"], t)
    assert n >= 40
    graph = json.loads((REGION_DIR / "roads.graph.json").read_text(encoding="utf-8"))
    dests = sorted({d.strip() for e in graph["edges"] for d in str(e["attrs"].get("destination", {}).get("v", "")).split(";")
                    if d.strip()})
    kept, dropped = BF.neutral_destinations(dests)
    assert kept and all(not FORBIDDEN.search(d) for d in kept), kept


# --------------------------------------------------------------------------------------------- region C overrides
R2_ENTRIES = {
    "andersa-putry-e1-advance-gantry": "sign_gantry", "andersa-putry-cantilever-p37": "sign_gantry",
    "tysiaclecia-n-putry-e15-right": "gate3_sign", "tysiaclecia-n-putry-e15-left": "gate3_sign",
    "andersa-biezenstwa-e15-right": "gate3_sign", "andersa-biezenstwa-e15-left": "gate3_sign",
}


def test_r2_overrides_have_provenance_and_resolve_in_the_graph():
    ov = {o["id"]: o for o in _overrides()}
    graph = json.loads((REGION_DIR / "roads.graph.json").read_text(encoding="utf-8"))
    nodes = {n["id"] for n in graph["nodes"]}
    for oid, kind in R2_ENTRIES.items():
        o = ov[oid]
        assert o["kind"] == kind
        assert o["r2"] and all(re.fullmatch(r"R2-0\d\d", x) for x in o["r2"]), oid
        assert o.get("reason") and o.get("confidence") in ("low", "medium", "high") and o.get("verify"), oid
        spec = o.get("along", o)
        edges = [e for e in graph["edges"] if e.get("osm_way") == spec["osm_way"]]
        assert edges and spec["before_node"] in nodes, oid
        e = next(e for e in edges if e["to"] == spec["before_node"])
        assert 0 < spec["distance_m"] < e["length_m"], oid
        ref = str(e["attrs"].get("ref", {}).get("v", ""))
        if kind == "gate3_sign":                            # the numbers on the plates are the road's own numbers
            nums = [x for p in o["parts"] if p["face"] == "E-15" for x in p["text"].split("|")]
            assert set(nums) == set(ref.split(";")), (oid, ref)
            assert spec["distance_m"] <= e["length_m"] and o["parts"][0]["face"] == "E-15"
    # E-15 within 50 m after the junction (pkt 6.3.7.8 lit. a): measured from the node where the exit / slip begins
    e = next(e for e in graph["edges"] if e["id"] == "w552161976:3341716402-2367445386")
    assert e["length_m"] - ov["andersa-biezenstwa-e15-right"]["along"]["distance_m"] <= SN.E15_MAX_FROM_JUNCTION_M
    a = next(e for e in graph["edges"] if e["id"] == "w237183783:2629251371-2466608897")
    b = next(e for e in graph["edges"] if e["id"] == "w237183783:2466608897-2466608891")
    after_ring = a["length_m"] + b["length_m"] - ov["tysiaclecia-n-putry-e15-right"]["along"]["distance_m"]
    assert 0 < after_ring <= SN.E15_MAX_FROM_JUNCTION_M


def test_authored_overhead_boards_are_in_the_norm_letter_range():
    """Letter height implied by every authored board size: d = h / (ROW_U n + PAD_U per panel). Tabela 1.9 allows
    IV..VII (132..282 mm) for E-1 / E-2 on 'średnie' / 'duże' roads; +-12 % for the photo measurements."""
    seen = {}
    for o in _overrides():
        if o.get("kind") != "sign_gantry":
            continue
        for bd in o["boards"]:
            if bd.get("style") in ("vms", "e1_cross") or not bd.get("size_m"):
                continue
            panels = bd.get("panels") or [{"rows": bd["rows"]}]
            d = bd["size_m"][1] / sum(SG._panel_units(len(p["rows"])) for p in panels)
            seen[(o["id"], tuple(bd["lanes"]))] = round(d, 3)
            assert 0.132 * 0.88 <= d <= 0.282 * 1.12, (o["id"], d)
    # the boards measured on the frontal 2019 frame (ADR 0139) and on the R2-066 frame are group VI (210 mm)
    assert seen[("andersa-putry-approach-gantry", (0, 1))] == pytest.approx(0.210, rel=0.06)
    assert seen[("andersa-putry-approach-gantry", (2,))] == pytest.approx(0.210, rel=0.06)
    # R2-066 frame (+-10 %): two row groups in one frame, letters between groups V (162 mm) and VI (210 mm)
    assert 0.162 <= seen[("andersa-putry-e1-advance-gantry", (0, 1))] <= 0.215


def test_new_gantry_boards_build_from_the_override():
    o = next(x for x in _overrides() if x["id"] == "andersa-putry-e1-advance-gantry")
    bd = o["boards"][0]
    rows = LM._board_rows({"edges": []}, bd, {"stale": []}, o["id"])
    assert [r[1] for r in rows] == ["Warszawa", "Ełk", "Augustów", "Kuźnica PL BY", "Centrum"]
    im, w, h = SG.panel_board([{"rows": [(list(r[0]), r[1]) for r in pn["rows"]], "arrow": pn["arrow"]}
                               for pn in bd["panels"]], size_m=bd["size_m"], single_frame=bd.get("frame") == "single")
    assert (w, h) == pytest.approx(tuple(bd["size_m"]), abs=0.01)
    ca, cb = (np.asarray(v, float) for v in o["columns_en"])
    assert 12.0 < np.hypot(*(cb - ca)) < 15.0
    p37 = next(x for x in _overrides() if x["id"] == "andersa-putry-cantilever-p37")["boards"][0]
    assert p37["style"] == "e1_cross" and SG._rows(p37["top"])[0] == (["8", "E67"], "Warszawa")


# ------------------------------------------------------------------------------------------------ rule E-1 dedupe
class _Pl:
    def __init__(self, items):
        self.items = items


def test_rule_diagram_is_dropped_beside_an_authored_gantry():
    items = [
        {"p": "sign_gantry_10_72", "e": -475.7, "n": -8.8, "src": "override:andersa-putry-portal-p40"},
        {"p": "sign_post", "e": -476.5, "n": -1.0, "src": "rule:roundabout_diagram:j:a"},
        {"p": "sign_post", "e": -475.2, "n": -1.6, "src": "rule:roundabout_diagram:j:a"},
        {"p": "board_E-1_00001", "e": -475.9, "n": -1.3, "src": "rule:roundabout_diagram:j:a"},
        {"p": "sign_post", "e": 459.0, "n": -694.0, "src": "rule:roundabout_diagram:j:b"},
        {"p": "board_E-1_00002", "e": 459.4, "n": -694.0, "src": "rule:roundabout_diagram:j:b"},
        {"p": "plate_A-7", "e": -470.0, "n": 0.0, "src": "rule:junction:j:a"},
    ]
    pl, boards, rep = _Pl(items), {"E-1_00001": 1, "E-1_00002": 2}, {"roundabout_signs": {"diagrams": 2}}
    out = SR.drop_rule_diagrams_near_gantries(pl, boards, rep)
    assert [x["board"] for x in out] == ["E-1_00001"] and out[0]["by"] == "override:andersa-putry-portal-p40"
    assert [it["p"] for it in pl.items] == ["sign_gantry_10_72", "sign_post", "board_E-1_00002", "plate_A-7"]
    assert boards == {"E-1_00002": 2} and rep["roundabout_signs"]["diagrams"] == 1


# ----------------------------------------------------------------------------------------------------- the budget
def _tris(m):
    return sum(len(p["T"]) for p in m.out())


def test_sign_meshes_cost_less_than_before():
    meta = json.loads((REPO / "art-source/world/props/props_meta.json").read_text(encoding="utf-8"))["prototypes"]
    # the library in git is rebuilt by the leader (build_world C); until then it holds the pre-0236 counts
    old = {"sign_gantry_14_61_b6": (1008, 480), "sign_gantry_10_72": (1072, 480), "sign_cantilever_L8_86": (528, 240)}
    for k, v in old.items():
        if (meta[k]["tris_lod0"], meta[k]["tris_lod1"]) != v:
            pytest.skip("props library rebuilt after ADR 0236")
    l0, l1, _ = LP.sign_gantry(14.0, 6.1, 0.6)
    assert (_tris(l0), _tris(l1)) == (792, 208)
    l0, l1, _ = LP.sign_cantilever(8.0, 7.2, mirror=True)
    assert _tris(l0) < 528 and _tris(l1) < 240
    m, low, _ = PP.plate("B-33_70")
    assert _tris(m) == 176 < meta["plate_B-33_70"]["tris_lod0"] and _tris(low) == meta["plate_B-33_70"]["tris_lod1"]
    m, low, _ = PP.board("E-2_x", 2.0, 1.0)
    assert (_tris(m), _tris(low)) == (28, 4)


def test_plate_rim_faces_outward():
    m, _, _ = PP.plate("B-33_70")
    part = next(p for p in m.out() if p["mat"] == "plate_back")
    V, T = part["V"], part["T"]
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    c = V[T].mean(axis=1)
    rim = (np.abs(n[:, 1]) < 1e-9) & (np.hypot(c[:, 0], c[:, 2]) > 0.35)        # rim quads: normal in the plate plane
    assert rim.sum() == 64
    assert ((n[rim][:, 0] * c[rim][:, 0] + n[rim][:, 2] * c[rim][:, 2]) > 0).all()


def frame_delta():
    """Per control camera: change of the frame estimate (build_world.mesh_budget rules: 120 deg wedge beyond 200 m,
    LOD by distance and lodBias) caused by ADR 0236, for the instances whose positions are in git (gantries and
    their boards from streetscape_qa `landmarks`, the dropped rule E-1, the new portal, the four E-15 posts).
    Plates (rim -64 a disc within the LOD0 range) and rule boards beyond LOD0 only improve it further."""
    qa = json.loads((REGION_DIR / "generated/streetscape_qa.json").read_text(encoding="utf-8"))
    cams = json.loads((REGION_DIR / "generated/control_cameras.json").read_text(encoding="utf-8"))
    cams = cams["cameras"] if isinstance(cams, dict) else cams
    g = {x["id"]: x for x in qa["furniture"]["landmarks"]["gantries"]}
    P = "sign_gantry_x"
    inst = []           # (proto for the LOD rule, (e, n), (old lod0, old lod1), (new lod0, new lod1))
    old_new = {"andersa-putry-approach-gantry": ((1008, 480), (792, 208)), "andersa-putry-portal-p40": ((1072, 480), (840, 208)),
               "tysiaclecia-s-putry-e1-portal": ((960, 444), (756, 196)), "tysiaclecia-its-vms-gantry": ((1200, 624), (936, 256)),
               "tysiaclecia-s-putry-portal": ((1040, 504), (816, 216)), "andersa-putry-cantilever-p37": ((528, 240), (412, 108))}
    for gid, (o, n) in old_new.items():
        inst.append((P, g[gid]["at"], o, n))
        for _ in g[gid]["boards"]:
            inst.append(("board_OB_x", g[gid]["at"], (28, 28), (28, 4)))
    new = [-191.3, -264.6]
    inst += [(P, new, (0, 0), (792, 208)), ("board_OB_x", new, (0, 0), (28, 4)),
             ("gantry_footing", new, (0, 0), (24, 24))]
    e1 = next(r for r in qa["furniture"]["route_signs"] if r["src"].startswith("rule:roundabout_diagram:j:n2629251371"))
    inst += [("board_E-1_x", [e1["e"], e1["n"]], (28 + 60, 28 + 24), (0, 0))]
    for at in ([-551.0, 89.0], [-541.0, 89.0], [288.0, -556.0], [280.0, -571.0]):
        inst.append(("sign_g3_x", at, (0, 0), (32, 20)))
    out = {}
    for cam in cams:
        if cam["type"] != "persp":
            continue
        pos = np.array(cam["pos"][:2])
        look = np.array(cam["look_at"][:2]) - pos
        look /= max(np.linalg.norm(look), 1e-9)
        res = {}
        for prof, pol in BW.LOD_POLICY.items():
            tot = 0
            for proto, at, o, n in inst:
                v = np.asarray(at, float) - pos
                di = float(np.hypot(*v))
                if di > 200 and float(np.dot(v / di, look)) < 0.5:
                    continue
                k = next((i for i, (lim, _) in enumerate(BW.instance_rule(proto, 2, pol["lod_bias"])) if di < lim), None)
                if k is not None:
                    tot += n[k] - o[k]
            res[prof] = tot
        out[cam["id"]] = res
    return out


def test_budget_is_not_worse_on_the_cameras_at_the_limit():
    qa = json.loads((REGION_DIR / "generated/streetscape_qa.json").read_text(encoding="utf-8"))
    if any(r["src"] == "override:andersa-putry-e1-advance-gantry" for r in qa["furniture"]["route_signs"]):
        pytest.skip("world rebuilt after ADR 0236: read mesh_budget.frame_estimate directly")
    base = {f["camera"]: f for f in qa["mesh_budget"]["frame_estimate"]}
    delta = frame_delta()
    for cam, d in delta.items():
        if base[cam]["tris_high"] >= 1_850_000:           # stretch_04, route_onramp_andersa(_above)
            assert d["High"] <= 0, (cam, d)               # the 2 M High limit of PERFORMANCE_BUDGETS
            assert d["Low"] <= 60, (cam, d)               # two E-15 posts at LOD1 (2 x 20 triangles), see ADR 0236
        assert d["High"] <= 600 and d["Low"] <= 600, (cam, d)      # one camera beside the new portal: see ADR 0236
    assert sum(d["High"] for d in delta.values()) < 0 and sum(d["Low"] for d in delta.values()) < 0


if __name__ == "__main__":
    qa_ = json.loads((REGION_DIR / "generated/streetscape_qa.json").read_text(encoding="utf-8"))
    base_ = {f["camera"]: f for f in qa_["mesh_budget"]["frame_estimate"]}
    for cam_, d_ in frame_delta().items():
        print(f"{cam_:28s} High {base_[cam_]['tris_high']:>8d} {d_['High']:+6d}   Low {base_[cam_]['tris_low']:>7d} {d_['Low']:+6d}")
