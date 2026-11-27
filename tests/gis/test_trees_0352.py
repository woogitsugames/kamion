"""ADR 0352: species-specific foliage (oak blade + oak in the library, blade stamps of the garden crown cards),
oaks among the roadside lindens / maples, no flat shade polygon in the crown cards.

Blender-free: make_trees.py is read through ast; the baked library is checked through trees_meta.json.
"""
import ast
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools/worldgen"))
from streetscape import leaf_sprays as LS      # noqa: E402
from streetscape import plot_kit as PK         # noqa: E402
from streetscape import tree_crown_profile as TCP   # noqa: E402
from streetscape import vegetation as VG       # noqa: E402
from streetscape.foliage_policy import osm_tree_species   # noqa: E402

SCRIPT = REPO / "tools/blender/world/make_trees.py"
VEG = REPO / "art-source/world/vegetation"


def _tables():
    tree = ast.parse(SCRIPT.read_text(encoding="utf8"))
    keep = [n for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("CROWN", "ADDED_0352", "NVAR", "HREF")]
    assert len(keep) == 4
    ns = {"math": math, "random": random}
    exec(compile(ast.fix_missing_locations(ast.Module(body=keep, type_ignores=[])), str(SCRIPT), "exec"), ns)
    return ns


def _lobes(species):
    """Lobes of one side of the blade: maxima of the half width that stand >= 0.05 blade lengths above the sinuses
    beside them (the fine teeth of a linden or birch margin are ~0.02-0.04)."""
    from scipy.signal import find_peaks
    pts = np.asarray(LS.blade(species))
    side = pts[pts[:, 1] > 1e-4]
    side = side[np.argsort(side[:, 0])]
    w = np.concatenate([[0.0], side[:, 1], [0.0]])
    return len(find_peaks(w, prominence=0.05)[0])


def test_oak_blade_is_round_lobed_and_unlike_the_other_species():
    assert "oak" in LS.SPECIES
    assert 3 <= _lobes("oak") <= 5, "pedunculate oak: 3-5 rounded lobes a side"
    assert _lobes("linden") <= 1 and _lobes("alder") <= 1 and _lobes("poplar") <= 1
    pts = np.asarray(LS.blade("oak"))
    assert pts[:, 0].min() >= -0.01 and pts[:, 0].max() <= 1.01
    widest = pts[np.argmax(np.abs(pts[:, 1])), 0]
    assert 0.45 < widest < 0.85, "obovate: widest beyond the middle"
    lum = {s: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2] for s, c in LS.COL.items() if s in LS.SPECIES}
    assert lum["oak"] < min(lum[s] for s in ("linden", "maple", "birch", "poplar")), "oak: the darkest crown of the avenue"
    a = LS.spray("oak", 7, 256)
    assert np.array_equal(a, LS.spray("oak", 7, 256)) and 0.15 < LS.coverage(a) < 0.70


def test_oak_crown_form_is_the_broadest_of_the_library():
    ns = _tables()
    C = ns["CROWN"]
    assert ns["ADDED_0352"] == ("oak",) and ns["NVAR"]["oak"] == 2 and ns["HREF"]["oak"] == VG.HREF_DEFAULT["oak"]
    assert C["oak"]["rmax"] > C["maple"]["rmax"] > C["linden"]["rmax"]
    assert C["oak"]["bole"] <= C["linden"]["bole"] and C["oak"]["arch"] < C["maple"]["arch"], "short bole, level limbs"
    assert C["oak"]["hang"] == 0 and C["oak"]["mono"] < 0.6
    assert VG.CROWN_FORM["oak"][0] == C["oak"]["rmax"] and VG.NVAR["oak"] == 2
    assert "oak" not in VG.SPECIES, "not in the BDOT forest mixes (positional weights): oak_share / rows / overrides"
    assert osm_tree_species({"species": "Quercus robur"}) == "oak" and osm_tree_species({"genus": "Tilia"}) == "linden"


def test_library_has_the_oak_within_the_budget():
    tr = json.loads((VEG / "trees_meta.json").read_text(encoding="utf-8"))["trees"]
    for v in range(2):
        t = tr[f"tree_oak_{v}"]
        assert t["species"] == "oak" and t["tris_lod0"] <= 3800 and t["tris_lod1"] <= 0.5 * t["tris_lod0"] and t["tris_lod2"] == 2
        assert (VEG / f"impostor_tree_oak_{v}.png").exists() and (VEG / f"impostor_tree_oak_{v}_n.png").exists()
    assert "tree_oak_2" not in tr
    assert (VEG / "leaves_oak.png").exists()
    # the clearance pass measures the oak mesh, not the nominal envelope
    assert TCP.proto_name("oak", 0) == "tree_oak_0" and TCP.proto_name("oak", 5) in ("tree_oak_0", "tree_oak_1")
    r = TCP.low_radius("tree_oak_0", TCP.scale_for("tree_oak_0", 17.0), VG.CLEAR_H_M)
    assert 2.0 < r < 0.62 * 17.0


def _tree(e, n, p="tree_linden", h=14.0, **kw):
    return dict({"p": p, "v": 2, "e": e, "n": n, "z": 120.0, "h": h, "yaw": 1.0, "lean": 0.01, "src": "bdot:x"}, **kw)


def test_oak_share_touches_only_mature_open_grown_lindens_and_maples():
    rng = np.random.default_rng(3)
    base = [_tree(round(float(x), 2), round(float(y), 2), p="tree_linden" if i % 2 else "tree_maple")
            for i, (x, y) in enumerate(rng.uniform(-1000, 1000, (4000, 2)))]
    rep = {}
    out = VG.oak_share(base, rep)
    assert len(out) == len(base) and out == VG.oak_share(base, {}), "deterministic, order kept"
    oaks = [t for t in out if t["p"] == "tree_oak"]
    assert rep["oak_share"]["oaks"] == len(oaks)
    assert 0.10 < len(oaks) / len(base) < 0.45, len(oaks) / len(base)
    assert all(t["v"] in (0, 1) and t["h"] <= VG.CHM_MAX_SCALE * 17.0 * 1.1 for t in oaks)
    for a, b in zip(base, out):
        assert (a["e"], a["n"], a["z"], a["yaw"], a["lean"], a["src"]) == (b["e"], b["n"], b["z"], b["yaw"], b["lean"], b["src"])
        assert b["p"] in (a["p"], "tree_oak")
    # in groups, not salt and pepper: the nearest neighbour of an oak is an oak far more often than the share
    P = np.array([[t["e"], t["n"]] for t in out])
    is_oak = np.array([t["p"] == "tree_oak" for t in out])
    from scipy.spatial import cKDTree
    _, idx = cKDTree(P).query(P[is_oak], k=2)
    assert is_oak[idx[:, 1]].mean() > 1.8 * is_oak.mean()
    # never: forest trees, High-only garden library trees, authored / OSM / plot trees, young trees, other species
    keep = ([_tree(e, n, fk="broadleaf") for e, n in P[is_oak][:50]] + [_tree(e, n, fc=7) for e, n in P[is_oak][:50]]
            + [_tree(e, n, tier="high") for e, n in P[is_oak][:50]] + [_tree(e, n, src="override:rows:1") for e, n in P[is_oak][:50]]
            + [_tree(e, n, src="osm:node/1") for e, n in P[is_oak][:50]] + [_tree(e, n, src="plot:p:g7-lib") for e, n in P[is_oak][:50]]
            + [_tree(e, n, h=8.9) for e, n in P[is_oak][:50]] + [_tree(e, n, p="tree_birch") for e, n in P[is_oak][:50]])
    assert VG.oak_share(keep, {}) == keep


def test_garden_crown_cards_use_the_blade_of_their_species():
    rng = np.random.default_rng(1)
    st = {sp: PK._blade_stamps(rng, sp, n=12) for sp in ("linden", "maple", "birch")}
    width = {sp: float(np.mean([s.shape[1] for s in ss])) for sp, ss in st.items()}
    assert width["linden"] > 1.2 * width["birch"], width      # broad heart vs slim rhombus
    fill = {sp: float(np.mean([s[..., 3].mean() for s in ss])) for sp, ss in st.items()}
    assert fill["maple"] < 0.75 * fill["linden"] and fill["birch"] < fill["linden"], "a lobed blade covers less of its box than a heart"
    assert set(PK._CROWN_BLADE) == {"ovoid", "round", "birch"}
    assert {v[0] for v in PK._CROWN_BLADE.values()} == {"linden", "maple", "birch"}


def test_crown_cards_have_no_flat_shade_polygon():
    """critic s24 wave 11 P0 # 3: the (22, 34, 20) shade polygon showed between the leaves as a straight-edged patch."""
    im = np.asarray(PK.atlas())
    y0, h = PK.ROW_Y["tall"]
    for name in ("crown_ovoid", "crown_round"):
        x0, w = PK._SPR_X[name]
        card = im[y0:y0 + h, x0:x0 + w]
        opaque = card[..., 3] > 200
        flat = opaque & (np.abs(card[..., :3].astype(int) - np.array([22, 34, 20])).max(axis=2) <= 2)
        assert opaque.mean() > 0.45
        assert flat.sum() / opaque.sum() < 0.02, (name, flat.sum() / opaque.sum())


def test_avenue_rows_break_twin_clones_and_stay_within_library_and_clearance():
    """ADR 0352 addendum (neon-avenue-s24, critic build #10 TOP #10): both default BDOT OT_OIPR_L rows and
    tree_rows.yaml avenues vary age/scale (0.70-1.15), model variant (no consecutive twin), yaw (>= 60 deg apart),
    along/across offsets, missing-tree gaps, young replacements / self-seeded saplings and species mix (with oak),
    deterministically, using only existing library prototypes and respecting ADR 0347 clearance."""
    from types import SimpleNamespace
    from shapely.geometry import LineString, box
    from streetscape import tree_rows as TR

    tr_meta = json.loads((VEG / "trees_meta.json").read_text(encoding="utf-8"))["trees"]
    line_coords = [[10.0, 60.0], [1990.0, 60.0]]
    src = {"bdot10k": {"OT_PTLZ_A": [], "OT_PTRK_A": [], "OT_OIPR_P": [], "OT_PTNZ_A": [], "OT_PTTR_A": [],
                       "OT_OIPR_L": [{"id": "PL.TEST.AVENUE.1", "props": {"rodzaj": "rząd drzew"},
                                      "geometry": {"coordinates": line_coords}}]},
           "osm": {"nodes": []}}
    blocked = np.zeros((121, 2001), bool)
    hf = SimpleNamespace(x0=0.0, y1=120.0)
    zc = np.zeros(blocked.shape, np.float32)

    # 1. Default BDOT OT_OIPR_L row path (used by dk65-monki-*, dw671-tykocin-*, non-corridor rows)
    bdot_a, _ = VG.place(src, (0.0, 0.0), hf, zc, blocked, {}, overrides=[], tree_rows=None)
    bdot_b, _ = VG.place(src, (0.0, 0.0), hf, zc, blocked, {}, overrides=[], tree_rows=None)
    assert bdot_a == bdot_b and len(bdot_a) >= 90

    # 2. Opted-in tree_rows.py path (used by knyszyn-w, dk65-01..11)
    graph = {"edges": [{"id": "m", "from": "A", "to": "B", "geometry": [[0.0, 50.0], [2000.0, 50.0]],
                        "osm_way": 1, "attrs": {"highway": {"v": "secondary"}, "width": {"v": 7.0}, "maxspeed": {"v": 90}}}]}
    plan = TR.plan([("bdot:PL.TEST.AVENUE.1", LineString(line_coords), "bdot")],
                   TR.roads_from_graph(graph, (0.0, 0.0)), {}, graph=graph)
    for r in plan["rows"]:
        r["key"] = f"treerow:{r['key']}"
    plan["height_m"] = {r["key"]: r["height_m"] for r in plan["rows"]}
    tr_a, _ = VG.place(src, (0.0, 0.0), hf, zc, blocked, {}, overrides=[], tree_rows=plan)
    tr_b, _ = VG.place(src, (0.0, 0.0), hf, zc, blocked, {}, overrides=[], tree_rows=plan)
    assert tr_a == tr_b and len(tr_a) >= 80 and plan["report"]["replants"] >= 1

    carriage = box(0.0, 46.5, 2000.0, 53.5)
    for label, row in (("bdot", bdot_a), ("tree_rows", tr_a)):
        # Only existing library prototypes (zero new prototypes / zero DC growth)
        assert all(f"{t['p']}_{t['v']}" in tr_meta for t in row), label
        # Species admixture (including oak) and young replacements / self-seeded plants
        species = {t["p"] for t in row}
        assert len(species) >= 4 and "tree_oak" in species, (label, species)
        young = [t for t in row if t["h"] < 8.5 or t["p"] in ("tree_birchyoung", "tree_shrub")]
        assert len(young) >= 3, (label, len(young))
        # Age/scale spread on mature trees
        mature_h = [t["h"] for t in row if t["h"] >= 8.5 and t["p"] not in ("tree_birchyoung", "tree_shrub")]
        assert max(mature_h) - min(mature_h) >= 5.0, (label, min(mature_h), max(mature_h))
        # Lateral scatter (+-1-2.5 m) and real missing-tree gaps (> 22 m)
        ns = np.array([t["n"] for t in row])
        assert ns.max() - ns.min() >= 3.0 and np.max(np.abs(ns - 60.0)) <= 2.6, (label, ns.min(), ns.max())
        es = np.sort([t["e"] for t in row])
        gaps = np.diff(es)
        assert gaps.std() > 3.0 and gaps.max() > 22.0, (label, gaps.std(), gaps.max())
        # Anti-clone: no consecutive identical (species, variant) where NVAR > 1, and yaw separation >= 60 deg
        for a, b in zip(row, row[1:]):
            sp = a["p"][5:]
            if a["p"] == b["p"] and VG.NVAR.get(sp, 3) > 1:
                assert a["v"] != b["v"], (label, a, b)
            da = abs((b["yaw"] - a["yaw"] + math.pi) % (2.0 * math.pi) - math.pi)
            assert da >= VG.AVENUE_ROW_MIN_YAW_DIFF - 0.02, (label, a["yaw"], b["yaw"], da)
        # ADR 0347 clearance: zero violations after road_clearance
        rep = {}
        cleared = VG.road_clearance(row, carriage, rep, free_fn=lambda P: np.ones(len(P), bool))
        assert rep["road_clearance"]["violations_after"] == 0 and len(cleared) > 0, (label, rep)
