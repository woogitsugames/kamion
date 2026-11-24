"""ADR 0339: stand heights, openings, young growth and the HLOD top line from the canopy height model of the tile
(GUGiK NMPT - NMT, streetscape.forest_chm). Synthetic model + the shipped products of the prototype tiles."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import shapely

from streetscape import forest_chm as FCH
from streetscape import forest_hlod as FH
from streetscape import vegetation as VG
from test_house_greenery_0163 import _forest_src

REPO = Path(__file__).resolve().parents[2]
RING = [[0, 0], [400, 0], [400, 200], [0, 200]]
PROTOTYPES = ("dk65-04", "dk65-05", "dw671-tykocin-03")


def _chm():
    """400 x 200 m stand on a 4 m grid: west third old (27 m, one 33 m veteran), middle a 5 m plantation with a
    40 x 40 m opening (centre 200, 100), east third a 16 m pole stand with half the cover. Grid origin (0, 200), 10 cells of margin."""
    top = np.zeros((70, 120))
    cov = np.zeros((70, 120))
    top[10:60, 10:43], cov[10:60, 10:43] = 27.0, 0.9
    top[30, 20] = 33.0
    top[10:60, 43:77], cov[10:60, 43:77] = 5.0, 0.3
    top[30:40, 55:65], cov[30:40, 55:65] = 0.0, 0.0
    top[10:60, 77:110], cov[10:60, 77:110] = 16.0, 0.36
    return FCH.Chm(top, cov, -40.0, 240.0, 4.0, {"source": {"product": "synthetic"}, "stats": {}})


def _place(chm, overrides=None, kat="iglasty"):
    src = _forest_src("F1:0", RING)
    src["bdot10k"]["OT_PTLZ_A"][0]["props"]["kategoria"] = kat
    hf = SimpleNamespace(x0=-20.0, y1=220.0)
    zc = np.zeros((241, 441))
    rep = {}
    trees, forests = VG.place(src, (0.0, 0.0), hf, zc, np.zeros_like(zc, bool), rep, overrides or [], chm=chm)
    return trees, forests, rep


def _canopy(trees):
    return [t for t in trees if t["src"] == "bdot:F1:0"]


def test_no_model_no_change():
    """Opt-in by data: a tile without forest_chm.png is generated exactly as before."""
    a, _, ra = _place(None)
    src = _forest_src("F1:0", RING)
    hf = SimpleNamespace(x0=-20.0, y1=220.0)
    zc = np.zeros((241, 441))
    b, _ = VG.place(src, (0.0, 0.0), hf, zc, np.zeros_like(zc, bool), {}, [])
    assert a == b and "forest_chm" not in ra


def test_heights_follow_the_model():
    trees, _, rep = _place(_chm())
    can = _canopy(trees)
    old = [t for t in can if t["e"] < 120]
    young = [t for t in can if 150 < t["e"] < 260]
    pole = [t for t in can if t["e"] > 290]
    assert len(old) > 800 and len(young) > 300 and len(pole) > 200
    h = np.array([t["h"] for t in old if (t["e"] - 42) ** 2 + (t["n"] - 118) ** 2 > 20 ** 2])
    assert h.max() <= 27.0 and np.percentile(h, 90) > 25.0, "dominant trees reach the measured tops, none above"
    assert np.percentile(h, 10) < 0.8 * 27.0, "co-dominant and suppressed trees: no single crown height"
    vet = [t["h"] for t in old if (t["e"] - 42) ** 2 + (t["n"] - 118) ** 2 <= 6 ** 2]
    assert vet and max(vet) > 29.7, "the veteran of the model stands above the stand"
    assert {t["p"] for t in young} <= {"tree_pineyoung", "tree_birchyoung", "tree_spruce"}, "plantation = young prototypes"
    assert max(t["h"] for t in young) <= 5.0 and all(t["v"] == VG.SPRUCE_OPEN for t in young if t["p"] == "tree_spruce")
    hp = np.array([t["h"] for t in pole])
    assert hp.max() <= 16.0 and np.median(hp) > 12.0
    r = rep["forest_chm"]
    assert r["stands"] == 1 and r["young"] >= len(young) and r["mature"] > 1500 and r["gap"] > 20
    assert r["canopy_h_m"]["max"] > 29.7 and r["canopy_h_m"]["p10"] < 6.0 < 20.0 < r["canopy_h_m"]["p90"]


def test_openings_and_thinning():
    with_m, forests, rep = _place(_chm())
    without, forests0, _ = _place(None)
    box = lambda ts: [t for t in ts if t["src"] == "bdot:F1:0" and 188 < t["e"] < 212 and 88 < t["n"] < 112]  # noqa: E731
    assert len(box(without)) > 15 and not box(with_m), "no canopy tree in the opening of the model"
    assert rep["forest_chm"]["openings_m2"] >= 1000.0
    assert forests0[0].area - forests[0].area == pytest.approx(rep["forest_chm"]["openings_m2"], rel=1e-6)
    assert not forests[0].contains(shapely.Point(200, 100)), "the opening is cut out of the stand (HLOD, floor mask)"
    dens = lambda ts, e0, e1: len([t for t in ts if t["src"] == "bdot:F1:0" and e0 < t["e"] < e1]) / (e1 - e0)  # noqa: E731
    assert dens(with_m, 300, 390) < 0.65 * dens(without, 300, 390), "half the cover -> fewer trees"
    assert dens(with_m, 10, 110) == pytest.approx(dens(without, 10, 110), rel=0.01), "a closed stand keeps its trees"


def test_untouched_stream_outside_the_stand_rule():
    """Only the canopy trees of the stand change: understorey, floor and their positions are the same trees. Round 2:
    inside a pine stand most understorey birch saplings become spruce regeneration / hazel (same positions)."""
    a, _, _ = _place(_chm())
    b, _, _ = _place(None)
    key = lambda t: (t["src"], t["e"], t["n"])  # noqa: E731
    ua = {key(t): t for t in a if t["src"].endswith((":under", ":floor"))}
    ub = {key(t): t for t in b if t["src"].endswith((":under", ":floor"))}
    assert len(ua) >= len(ub), "the final thinning keeps more of them"
    rest = {k: v for k, v in ub.items() if v["p"] != "tree_birchyoung"}
    same = [k for k, v in rest.items() if ua.get(k) == v]
    assert len(same) >= 0.95 * len(rest), "plants other than the birch saplings are untouched"
    nb = sum(v["p"] == "tree_birchyoung" for v in ub.values())
    na = sum(v["p"] == "tree_birchyoung" for v in ua.values())
    assert 0.25 * nb < na < 0.75 * nb, "birch saplings stay in the edge zone, a third of them inside"
    c, _, _ = _place(_chm(), kat="mieszany")
    uc = {key(t): t for t in c if t["src"].endswith((":under", ":floor"))}
    d, _, _ = _place(None, kat="mieszany")
    ud = {key(t): t for t in d if t["src"].endswith((":under", ":floor"))}
    assert len([k for k, v in ud.items() if uc.get(k) == v]) >= 0.95 * len(ud), "mixed stands: understorey unchanged"
    pa, pb = {key(t) for t in _canopy(a)}, {key(t) for t in _canopy(b)}
    assert len(pa - pb) <= 0.02 * len(pa) and len(pa) < len(pb), "canopy trees are dropped, not moved"


def test_mantle_stays_under_the_measured_stand():
    trees, _, _ = _place(_chm())
    edge = [t for t in trees if t["src"].endswith(":edge") and t["p"] != "tree_shrub" and 160 < t["e"] < 250]
    assert edge and max(t["h"] for t in edge) <= 5.0 * 0.85 + 1e-6, max(t["h"] for t in edge)


def test_no_mantle_where_no_stand_stands():
    chm = _chm()
    chm2 = FCH.Chm(np.where(np.arange(120)[None, :] < 43, 0.0, chm.top), np.where(np.arange(120)[None, :] < 43, 0.0, chm.cover),
                   -40.0, 240.0, 4.0, chm.meta)                      # the west third of the BDOT polygon is open land
    trees, _, _ = _place(chm2)
    west = [t for t in trees if t["src"].endswith(":edge") and t["e"] < 100]
    east = [t for t in trees if t["src"].endswith(":edge") and t["e"] > 300]
    assert not west and len(east) > 50


def test_authored_stand_wins():
    ov = [{"kind": "forest_stand", "id": "s1", "target": {"bdot": "F1"}, "height_m": [20.0, 21.0]}]
    trees, forests, rep = _place(_chm(), ov)
    can = [t for t in _canopy(trees) if t["p"] != "tree_shrub"]
    assert min(t["h"] for t in can) >= 20.0 and rep["forest_chm"]["stands"] == 0
    assert forests[0].contains(shapely.Point(200, 100))


def test_species_clumps_and_wet_hollows():
    rng = np.random.default_rng(1)
    P = rng.uniform(0, 600, (6000, 2))
    sp = VG.chm_species(P, ["pine"] * len(P), "conifer", np.zeros(len(P), bool))
    share = lambda s: float(np.mean(sp == s))  # noqa: E731
    assert 0.08 < share("spruce") < 0.40 and 0.03 < share("birch") < 0.30 and share("pine") > 0.45
    # clumps: the spruces of a 30 m cell are far from the tile mean
    cell = (P // 30).astype(int)
    frac = {}
    for c, s in zip(map(tuple, cell), sp):
        frac.setdefault(c, []).append(s == "spruce")
    f = np.array([np.mean(v) for v in frac.values() if len(v) >= 8])
    assert f.std() > 0.15 and (f == 0).mean() > 0.3, "spruce in groups, not salt and pepper"
    wet = VG.chm_species(P, ["pine"] * len(P), "conifer", np.ones(len(P), bool))
    assert 0.6 < np.mean(wet == "alder") < 0.8 and np.mean(wet == "pine") < 0.25
    bl = VG.chm_species(P, ["birch"] * len(P), "broadleaf", np.zeros(len(P), bool))
    assert set(bl) == {"birch"}
    assert list(VG.chm_species(P, ["pine"] * len(P), "conifer", np.zeros(len(P), bool))) == list(sp), "deterministic"


def _hlod(chm):
    trees, forests, _ = _place(chm)
    rep = {}
    fm = [(forests[0], "conifer")]
    zg = lambda e, n: np.zeros(np.shape(e))  # noqa: E731
    cells = FH.build(trees, fm, shapely.Polygon(), zg, 512.0, rep, chm=chm)
    return cells, rep


def test_hlod_top_line_is_the_measured_one():
    cells, rep = _hlod(_chm())
    cells0, rep0 = _hlod(None)
    assert cells and cells0

    def canopy_tops(cs, e0, e1):
        z = []
        for c in cs.values():
            if not c["prims"][0]["mat"].startswith("forest_canopy"):
                continue
            V = c["prims"][0]["V"]
            m = (V[:, 0] > e0) & (V[:, 0] < e1) & (V[:, 1] > 30) & (V[:, 1] < 170)
            z += list(V[m, 2])
        return np.array(z)

    old, young, pole = (canopy_tops(cells, *r) for r in ((20, 110), (160, 180), (310, 380)))
    assert np.median(old) == pytest.approx(FH.CHM_CANOPY_K * 27.0, abs=1.0)
    assert np.median(young) == pytest.approx(FH.CHM_CANOPY_K * 5.0, abs=0.6)
    assert np.median(pole) == pytest.approx(FH.CHM_CANOPY_K * 16.0, abs=1.0)
    flat = canopy_tops(cells0, 20, 380)
    assert np.percentile(flat, 90) - np.percentile(flat, 10) < 8.0, "class rule: one crown level over the whole stand"
    allz = canopy_tops(cells, 20, 380)
    assert np.percentile(allz, 90) - np.percentile(allz, 10) > FH.CHM_CANOPY_K * 20.0
    # walls: the crown line of the edge picture sits at the measured tops (old stand 27 m, pole stand 16 m)
    def wall_tops(e0, e1):
        z = []
        for c in cells.values():
            for pr in [q for q in c["prims"] if q["mat"].startswith("forest_edge")]:
                V, UV = pr["V"], pr["UV"]
                m = (V[:, 0] > e0) & (V[:, 0] < e1) & (np.abs(UV[:, 1] - 0.75) < 1e-6) & (V[:, 1] > 201 - 0.8 - FH.CHM_EDGE_WOBBLE_M) & (V[:, 1] < 201.8)  # north edge (+ 1 m, r2: moved in by up to CHM_EDGE_WOBBLE_M), main wall
                z += list(V[m, 2])
        return np.array(z)

    wo, wp = wall_tops(30, 100), wall_tops(320, 380)
    assert len(wo) and len(wp)
    k = FH.CHM_WALL_TOP_FRAC["conifer"]
    assert np.median(wo) * k == pytest.approx(27.0, rel=0.08)
    assert np.median(wp) * k == pytest.approx(16.0, rel=0.08)
    # ... and of the second wall 6 m further in: no crown line above the tallest measured crown + 10 %
    for c in cells.values():
        for pr in [q for q in c["prims"] if q["mat"].startswith("forest_edge")]:
            top = pr["V"][np.abs(pr["UV"][:, 1] - 0.75) < 1e-6]
            assert (top[:, 2] * k <= 33.0 * 1.1).all(), float(top[:, 2].max())
    # no canopy sheet over the opening
    for c in cells.values():
        if not c["prims"][0]["mat"].startswith("forest_canopy"):
            continue
        V, T = c["prims"][0]["V"], c["prims"][0]["T"]
        cen = V[T].mean(axis=1)
        assert not ((abs(cen[:, 0] - 200) < 12) & (abs(cen[:, 1] - 100) < 12)).any()
    # no steep canopy triangle (from the road a sloping sheet is a pale shard), ribs every RIB_M carry the crowns there
    for c in cells.values():
        if not c["prims"][0]["mat"].startswith("forest_canopy"):
            continue
        tv = c["prims"][0]["V"][c["prims"][0]["T"]]
        n = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
        assert (np.hypot(n[:, 0], n[:, 1]) <= FH.CHM_SHEET_MAX_SLOPE * np.abs(n[:, 2]) + 1e-9).all()
    ribs = 0
    for c in cells.values():
        for pr in [q for q in c["prims"] if q["mat"].startswith("forest_edge")]:
            V = pr["V"]
            ribs += int(((V[:, 0] > 40) & (V[:, 0] < 100) & (V[:, 1] > 40) & (V[:, 1] < 160)).sum())    # deep inside the stand
    assert ribs > 100, "walls cross the stand, not only its outline"
    # triangle cost: walls around openings, stand steps and the ribs stay within 2.2 x of the class rule
    assert rep["forest_hlod"]["triangles"] <= 2.2 * rep0["forest_hlod"]["triangles"], (rep, rep0)


def test_wall_top_fraction_matches_the_baked_edge_pictures():
    from PIL import Image
    from conftest import require_lfs
    veg = REPO / "art-source" / "world" / "vegetation"
    for mix, frac in FH.CHM_WALL_TOP_FRAC.items():
        f = veg / f"forest_edge_{mix}.png"
        require_lfs(f)
        a = np.asarray(Image.open(f).convert("RGBA"))[..., 3]
        main = a[int(round(a.shape[0] * (1.0 - FH.edge_v_main(FH.bake_info()[mix]["edge"])))):] > 127
        tops = np.array([(main.shape[0] - np.argmax(main[:, c])) / main.shape[0] for c in range(main.shape[1]) if main[:, c].any()])
        assert np.percentile(tops, 90) == pytest.approx(frac, abs=0.02), (mix, np.percentile(tops, 90))


def test_reduce_and_gaps():
    dsm = np.full((16, 16), 100.0, np.float32)
    dsm[0:4, 0:4] = 125.0
    dsm[4, 4] = 400.0                       # a mast / bird: no tree
    dsm[8, 8] = np.nan
    top, cover = FCH.reduce_chm(dsm, np.full((17, 17), 100.0))
    assert top.shape == (4, 4) and top[0, 0] == 25.0 and cover[0, 0] == 1.0
    assert top[1, 1] == 0.0 and top[2, 2] == 0.0 and cover[1:, 1:].max() == 0.0
    chm = _chm()
    g = chm.gaps(shapely.Polygon(RING), 3.0, 300.0)
    assert g is not None and g.contains(shapely.Point(200, 100)) and not g.contains(shapely.Point(60, 100))
    assert 28 * 28 <= g.area <= 40 * 40, g.area       # the 40 m opening less the 4 m reach of the crowns around it
    assert chm.gaps(shapely.Polygon(RING), 3.0, 5000.0) is None


@pytest.mark.parametrize("rid", PROTOTYPES)
def test_shipped_products(rid):
    rdir = REPO / "Data" / "Regions" / rid
    meta = json.loads((rdir / "forest_chm.json").read_text(encoding="utf-8"))
    png = rdir / "forest_chm.png"
    assert meta["schema"] == FCH.SCHEMA and hashlib.sha256(png.read_bytes()).hexdigest() == meta["sha256_png"]
    assert png.stat().st_size < 400_000, "the product stays small enough for git"
    assert "geoportal.gov.pl" in meta["source"]["service"] and "google" not in json.dumps(meta).lower()
    assert meta["source"]["survey_date"] == "UNVERIFIED" and meta["source"]["missing_share"] < 0.01
    reg_bbox = meta["bbox"]
    chm = FCH.load(rid, (reg_bbox[0] + 1024.0, reg_bbox[1] + 1024.0))
    assert chm.top.shape == (512, 512) and chm.top.max() <= 63.75
    t = meta["stats"]["top_m"]
    assert 8.0 < t["p50"] < 32.0 and t["p90"] < 40.0 and t["p90"] - t["p10"] > 6.0, t      # real stands are not level


# ---- round 2 (critic r5): birch share of pine stands, prototype scale, crown line from the single cell, edge ----

def test_r2_pine_stand_keeps_a_few_per_cent_of_birch_inside():
    trees, _, _ = _place(_chm())
    can = [t for t in _canopy(trees) if t["h"] >= 9.0]
    inside = [t for t in can if 35 < t["e"] < 365 and 35 < t["n"] < 165]
    edge = [t for t in can if not (30 < t["e"] < 370 and 30 < t["n"] < 170)]
    broad = ("tree_birch", "tree_alder", "tree_maple", "tree_linden")
    share = lambda ts: sum(t["p"] in broad for t in ts) / len(ts)  # noqa: E731
    assert len(inside) > 500 and len(edge) > 300
    assert share(inside) < 0.08, share(inside)
    assert not [t for t in inside if t["p"] in ("tree_maple", "tree_linden")], "no maple / linden inside a pine stand"
    assert share(edge) > 1.5 * share(inside), "birch stands at the stand edge"
    # a mixed stand keeps its broadleaves
    mixed, _, _ = _place(_chm(), kat="mieszany")
    mi = [t for t in _canopy(mixed) if t["h"] >= 9.0 and 35 < t["e"] < 365 and 35 < t["n"] < 165]
    assert share(mi) > 0.30


def test_r2_no_prototype_scaled_beyond_the_limit():
    href = VG.proto_href()
    assert href.get("birch") and href.get("pine"), "tree library meta"
    for kat in ("iglasty", "mieszany", "liściasty"):
        trees, _, rep = _place(_chm(), kat=kat)
        can = _canopy(trees)
        sc = np.array([t["h"] / href[t["p"][5:]][t["v"]] for t in can])
        assert sc.max() <= VG.CHM_MAX_SCALE + 0.01, (kat, float(sc.max()))
        if kat == "liściasty":          # 27 m measured, the tallest broadleaf prototype reaches ~ 21.8 m
            old = np.array([t["h"] for t in can if 20 < t["e"] < 110])
            cap = VG.chm_cap_m("broadleaf")
            assert old.max() <= cap + 0.05
            # ... and the stand keeps its structure: heights x (limit / stand height), not a ruler line at the limit
            assert np.percentile(old, 90) - np.percentile(old, 10) > 0.15 * cap, np.percentile(old, [10, 50, 90])
    t = {"p": "tree_birch", "v": 1, "h": 20.5, "e": 1.0, "n": 2.0}
    assert VG.chm_fit(t, href) is False and t["v"] == 0 and t["h"] == 20.5, "a taller variant instead of a larger scale"
    t = {"p": "tree_spruce", "v": 2, "h": 40.0, "e": 1.0, "n": 2.0}
    assert VG.chm_fit(t, href) is True and t["v"] == 2, "the open spruce form keeps its variant"


def _rough_chm():
    """200 x 200 m old stand whose single cells alternate 27 / 21 m (crown tops and the dips between crowns)."""
    top = np.full((70, 70), 21.0)
    top[::2, ::2] = 27.0
    top[:10], top[60:], top[:, :10], top[:, 60:] = 0.0, 0.0, 0.0, 0.0
    return FCH.Chm(top, np.where(top > 0, 0.9, 0.0), -40.0, 240.0, 4.0, {"source": {}, "stats": {}})


def test_r2_crown_line_from_the_single_cell_and_tone():
    chm = _rough_chm()
    src = _forest_src("F1:0", [[0, 0], [200, 0], [200, 200], [0, 200]])
    src["bdot10k"]["OT_PTLZ_A"][0]["props"]["kategoria"] = "iglasty"
    zc = np.zeros((241, 241))
    trees, forests = VG.place(src, (0.0, 0.0), SimpleNamespace(x0=-20.0, y1=220.0), zc, np.zeros_like(zc, bool), {}, [], chm=chm)
    cells = FH.build(trees, [(forests[0], "conifer")], shapely.Polygon(), lambda e, n: np.zeros(np.shape(e)), 512.0, {}, chm=chm)
    k = FH.CHM_WALL_TOP_FRAC["conifer"]
    tops, nz_top, nz_bot = [], [], []
    for c in cells.values():
        for pr in [q for q in c["prims"] if q["mat"].startswith("forest_edge")]:
            V, UV, N = pr["V"], pr["UV"], pr["N"]
            deep = (V[:, 0] > 30) & (V[:, 0] < 170) & (V[:, 1] > 30) & (V[:, 1] < 170)
            tops += list(V[deep & (np.abs(UV[:, 1] - 0.75) < 1e-6), 2] * k)
            out = ~deep & (N[:, 2] < 0.999)
            nz_top += list(N[out & (np.abs(UV[:, 1] - 0.75) < 1e-6), 2])
            nz_bot += list(N[out & (UV[:, 1] == 0.0), 2])
    tops = np.array(tops)
    assert len(tops) > 100
    # ribs: both levels of the model show (the dominant height alone gave 27 m everywhere), none above the measured top
    assert np.percentile(tops, 15) < 23.5 and np.percentile(tops, 85) > 25.0, np.percentile(tops, [15, 50, 85])
    assert tops.max() <= 27.0 * FH.CHM_TOP_VAR[1] * (1 + FH.CHM_TOP_JITTER) + 0.05
    assert tops.min() >= 27.0 * FH.CHM_LINE_FLOOR * FH.CHM_TOP_VAR[0] * (1 - FH.CHM_TOP_JITTER) - 0.05
    # walls: crown row lit from above, bole row nearly horizontal
    assert len(nz_top) and len(nz_bot) and min(nz_top) > 0.8 and max(nz_bot) < 0.3


def test_r2_edge_follows_the_falling_crowns():
    """Crowns come down to 10 m in the last 8 m before the north outline: the outer wall follows them (not below
    CHM_EDGE_FLOOR x the dominant height), the stand 20 m inside keeps its 27 m line."""
    top = np.zeros((70, 70))
    top[10:60, 10:60] = 27.0
    top[10:12, 10:60] = 10.0
    chm = FCH.Chm(top, np.where(top > 0, 0.9, 0.0), -40.0, 240.0, 4.0, {"source": {}, "stats": {}})
    src = _forest_src("F1:0", [[0, 0], [200, 0], [200, 200], [0, 200]])
    src["bdot10k"]["OT_PTLZ_A"][0]["props"]["kategoria"] = "iglasty"
    zc = np.zeros((241, 241))
    trees, forests = VG.place(src, (0.0, 0.0), SimpleNamespace(x0=-20.0, y1=220.0), zc, np.zeros_like(zc, bool), {}, [], chm=chm)
    cells = FH.build(trees, [(forests[0], "conifer")], shapely.Polygon(), lambda e, n: np.zeros(np.shape(e)), 512.0, {}, chm=chm)
    k = FH.CHM_WALL_TOP_FRAC["conifer"]
    north, inside = [], []
    for c in cells.values():
        for pr in [q for q in c["prims"] if q["mat"].startswith("forest_edge")]:
            V, UV = pr["V"], pr["UV"]
            t = (np.abs(UV[:, 1] - 0.75) < 1e-6) & (V[:, 0] > 40) & (V[:, 0] < 160)
            north += list(V[t & (V[:, 1] > 196.5), 2] * k)
            inside += list(V[t & (V[:, 1] > 100) & (V[:, 1] < 180), 2] * k)
    assert len(north) > 10 and len(inside) > 50
    north = np.array(north)
    lo = 27.0 * FH.CHM_EDGE_FLOOR * FH.CHM_TOP_VAR[0] * (1 - FH.CHM_TOP_JITTER) - 0.05
    wall = north[north >= lo]               # (the low mantle skirt in front of the wall has the same v)
    assert len(wall) > 10 and np.percentile(wall, 75) < 0.62 * 27.0, np.percentile(north, [0, 25, 50, 75, 100])
    assert np.median(inside) > 24.0


def test_r2_ablation_switch(monkeypatch):
    """KAMION_FOREST_CHM_R2=0: the round 1 rules (no scale limit, class mix of the pine stand, sheet at 0.80)."""
    monkeypatch.setenv("KAMION_FOREST_CHM_R2", "0")
    trees, forests, rep = _place(_chm(), kat="liściasty")
    assert rep["forest_chm"]["scale_capped"] == 0
    assert max(t["h"] for t in _canopy(trees)) > VG.chm_cap_m("broadleaf") + 2.0
    cells = FH.build(trees, [(forests[0], "conifer")], shapely.Polygon(), lambda e, n: np.zeros(np.shape(e)), 512.0, {}, chm=_chm())
    z = np.concatenate([c["prims"][0]["V"][:, 2] for c in cells.values() if c["prims"][0]["mat"].startswith("forest_canopy")])
    assert z.max() == pytest.approx(0.80 * 33.0, abs=0.5)
