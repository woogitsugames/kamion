"""ADR 0324: reed clumps, irregular shore, roadside sward (verge_flora), U-1a guide posts, forest HLOD wall tops."""
import math
import sys
from pathlib import Path

import numpy as np
import shapely

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from roads.meshing import MeshBuf, grid_tris          # noqa: E402
from streetscape import forest_hlod as FH             # noqa: E402
from streetscape import guide_posts as GP             # noqa: E402
from streetscape import reeds as RD                   # noqa: E402
from streetscape import verge_flora as VF             # noqa: E402
from streetscape import water as WT                   # noqa: E402


def _rural_side(n=30, step=2.0, depth=0.6):
    st = np.arange(n) * step

    def strip(u0, z0, u1, z1):
        V = np.zeros((2 * n, 3))
        V[0::2] = np.column_stack([st, np.full(n, 3.5 + u0), np.full(n, 100 + z0)])
        V[1::2] = np.column_stack([st, np.full(n, 3.5 + u1), np.full(n, 100 + z1)])
        return V
    buf = MeshBuf()
    T = grid_tris(n, 2)
    rows = (("road_asphalt", (0, 0, 0.5, -0.01)), ("shoulder_gravel", (0.5, -0.01, 1.25, -0.05)),
            ("verge_grass", (1.25, -0.05, 1.25 + 1.5 * depth, -0.05 - depth)),
            ("verge_grass", (1.25 + 1.5 * depth, -0.05 - depth, 1.65 + 1.5 * depth, -0.05 - depth)),
            ("verge_grass", (1.65 + 1.5 * depth, -0.05 - depth, 1.65 + 3.0 * depth, 0.0)))
    for mat, (a, b, c, d) in rows:
        buf.add("road", mat, strip(a, b, c, d), np.zeros((2 * n, 2)), T, src="c1:R")
    return buf


def test_verge_flora_cards_stand_on_the_cross_section():
    buf = _rural_side()
    secs = VF.sections(buf.parts)
    assert len(secs) == 1 and secs[0]["ditch"] and secs[0]["X"].shape == (30, 5, 3)
    rep = {}
    ntri = VF.build(buf, secs, rep)
    cards = rep["verge_flora"]["cards"]
    assert ntri == 2 * sum(cards.values()) and all(cards[k] > 10 for k in ("edge", "slope", "bottom"))
    p = buf.parts[-1]
    assert (p.layer, p.mat) == ("banks", "verge_tufts") and p.COL is not None
    V = p.V.reshape(-1, 4, 3)
    # feet: never above the shoulder, never below the ditch bottom (minus the sink); tops within the tallest card
    assert V[:, :2, 2].max() <= 100.0 and V[:, :2, 2].min() >= 100 - 0.65 - VF.SINK_M - 1e-6
    h = V[:, 2:, 2].max(1) - V[:, :2, 2].min(1)
    assert h.max() <= VF.H_BOTTOM[1] * 1.1 + 2 * VF.SINK_M + 0.6 and h.min() >= VF.H_EDGE[0]
    # tall grass only in the bottom: cards taller than the slope range stand between the two bottom edges (+- card)
    tall = h > VF.H_SLOPE[1] + 2 * VF.SINK_M + 0.2
    assert tall.any() and (np.abs(V[tall][:, :2, 1].mean(1) - (3.5 + 2.35)) < 1.0).all()
    # some shoulder-edge tufts stand on the gravel (the edge is not a ruler line)
    short = h < VF.H_EDGE[1] + 2 * VF.SINK_M + 0.02
    assert (V[short][:, :2, 1].mean(1) < 3.5 + 1.25 - 0.05).sum() >= 5
    # deterministic
    buf2 = _rural_side()
    VF.build(buf2, VF.sections(buf2.parts), {})
    assert np.array_equal(buf2.parts[-1].V, p.V)


def test_verge_flora_flat_verge_has_no_tall_grass_and_skips_culled_stations():
    buf = _rural_side(depth=0.06)
    rep = {}
    VF.build(buf, VF.sections(buf.parts), rep)
    assert rep["verge_flora"]["cards"]["bottom"] == 0
    buf = _rural_side()
    g = next(p for p in buf.parts if p.mat == "shoulder_gravel")
    g.T = g.T[np.asarray(g.T).min(1) // 2 >= 15]                # first half culled (under a junction plate)
    VF.build(buf, VF.sections(buf.parts), {})
    assert buf.parts[-1].V[:, 0].min() > 15 * 2.0 - 1.2


def test_ditch_becomes_terrain_with_damp_masks():
    buf = _rural_side()
    secs = VF.sections(buf.parts)
    assert VF.tag_for_terrain(secs) == 3 and VF.tag_for_terrain(secs) == 0
    assert [p.src for p in buf.parts[:5]] == ["c1:R", "c1:R", "c1:R:vg", "c1:R:vg", "c1:R:vg"]
    assert len(VF.sections(buf.parts)) == 1 and VF.sections(buf.parts)[0]["ditch"]      # tagged parts still found

    class HF:
        x0, y1 = -10.0, 20.0
    col = np.zeros((40, 80, 4), np.float32)
    col[..., 2] = 0.95                                          # farmland flag: must survive
    c = VF.ditch_colours(col, HF, secs, {})
    assert c[..., 1].max() > 0.2 and c[..., 3].max() <= 0.45 and (c[..., 2] == 0.95).all()
    j, i = np.nonzero(c[..., 1] > 0)
    assert (np.abs((HF.y1 - j) - (3.5 + 2.35)) <= 2.0).all()    # only around the bottom line


def test_guide_post_spacing_and_mesh():
    assert GP.spacing(float("inf")) == 100.0 and GP.spacing(2000.0) == 100.0      # GDDKiA: 100 m on a straight
    assert GP.spacing(100.0) < GP.spacing(300.0) < GP.spacing(1000.0) < 100.0
    for side in ("right", "left"):
        m, _, col = GP.post(side)
        assert col is None
        z = np.concatenate([v for p in m.prims.values() for v in p[0]])[:, 2]
        assert abs(z.max() - GP.H_M) < 1e-6
        assert set(m.prims) == {"paint_white_reflective", "paint_ral3020"}


def _reed_doc(n=40):
    e = np.arange(n) * RD.SEG_M
    return {"runs": [np.column_stack([e, np.zeros(n), np.zeros(n), np.ones(n), np.full(n, 6.0)]).ravel().tolist()]}


def test_reed_belt_is_dense_clumps_of_summer_height():
    buf = MeshBuf()
    rep = {}
    flat = lambda e, n: np.full(np.shape(np.asarray(e, float)), 100.0)                       # noqa: E731
    lvl = lambda e, n: np.where(np.asarray(n, float) < -0.5, 100.0, np.nan)                  # noqa: E731
    RD.build(buf, _reed_doc(), flat, lvl, shapely.Polygon(), rep, layer="banks", low=False)
    V = np.concatenate([p.V.reshape(-1, 4, 3) for p in buf.parts])
    h = V[:, 2:, 2].mean(1) - V[:, :2, 2].mean(1)
    assert h.min() >= RD.HERB_H[0] * RD.H_GEOM * 0.8 and h.max() <= RD.REED_H[1] * RD.H_GEOM * 1.15
    length = 39 * RD.SEG_M
    # at least 4 cards per metre of bank over the 4 rows (ADR 0321: ~2 per 2 m sample and row)
    assert len(V) / length >= 4.0
    # rows 0 / 1 (reed): nominal height 1.5-2.5 m
    front = V[:, :2, 1].mean(1) < 1.6
    assert (h[front] / RD.H_GEOM >= RD.REED_H[0] * 0.8).all()
    # cards lean in every direction (a top view shows faces, not lines)
    lean = np.hypot(*(V[:, 2, :2] - V[:, 0, :2]).T)
    assert np.percentile(lean, 75) > 0.15
    rep2 = {}
    buf2 = MeshBuf()
    RD.build(buf2, _reed_doc(), flat, lvl, shapely.Polygon(), rep2, layer="banks", low=False)
    assert rep2 == rep


def test_forest_wall_noise_is_smooth_and_bounded():
    a = [FH._vnoise2(x, 3.0, FH.TOP_NOISE_M) for x in np.arange(0, 400, 1.0)]
    assert 0.0 <= min(a) and max(a) <= 1.0 and max(a) - min(a) > 0.5
    assert np.abs(np.diff(a)).max() < 0.15                      # no step from one metre to the next
    assert FH._vnoise2(12.5, 7.0, 16.0) == FH._vnoise2(12.5, 7.0, 16.0)
    assert FH.TOP_VAR[0] < 1.0 < FH.TOP_VAR[1] and FH.CORNER_DROP < 0.8 and FH.SKIRT_KEEP > 0.18


def test_shore_constants_keep_the_sheet_overlap_rule():
    # a land node may dip only where the sheet (outline + SHEET_OVERLAP_M) covers it, and never deeper than the bed
    assert WT.SHEET_OVERLAP_M >= 1.0 and WT.SHORE_DIP_M <= WT.BED0_M and WT.SHORE_BAR_M < WT.FREEBOARD_M
    assert WT.MUD_BAND_M[0] < WT.MUD_BAND_M[1] <= WT.BANK_M


def test_real_network_dk65_07_gets_sward_and_guide_posts():
    """dk65-07 (old DK65 between fields and a wood) on a flat heightfield: every kerbless side gets grass cards, the
    ditch parts go to the terrain, U-1a posts stand in pairs outside the built-up area and off the carriageway."""
    import json
    import pytest
    from roads import pipeline
    from roads.profile import Heightfield
    from streetscape import built_up as BU
    rid = "dk65-07"
    rdir = pipeline.REGIONS / rid
    if not (rdir / "generated" / "streetscape_sources.json").exists():
        pytest.skip("dk65-07 sources not generated")
    region = pipeline.load_region(rid)
    origin = (region["origin"]["x"], region["origin"]["y"])
    tm = json.loads((rdir / "terrain.json").read_text(encoding="utf-8"))
    w_, h_ = tm["samples"]
    wd = pipeline.build(rid, hf=Heightfield(np.full((h_, w_), float(region["origin"]["z"])), tm["bbox"], origin))
    secs = VF.sections(wd.buf.parts)
    assert len(secs) >= 8 and all(s["ditch"] for s in secs)
    rep = {}
    assert VF.build(wd.buf, secs, rep) > 4000 and rep["verge_flora"]["triangles"] < 40000        # budget guard
    assert VF.tag_for_terrain(secs) == 3 * len(secs)

    class PL:
        surf = None

        def __init__(self):
            self.items = []

        def add(self, name, p, yaw, z=None, sz=1.0, src="", group=None):
            self.items.append({"p": name, "e": float(p[0]), "n": float(p[1]), "src": src})
            return 0.0
    pl = PL()
    src = json.loads((rdir / "generated" / "streetscape_sources.json").read_text(encoding="utf-8"))
    frep = {}
    n = GP.place(pl, wd.net, BU.zone_for(wd.net, src, origin), frep)
    assert n >= 4 and n % 2 == 0 and frep["guide_posts_u1a"]["skipped"]["built_up"] > 0
    chains = {c.id: c for c in wd.net.chains}
    for it in pl.items:
        c = chains[it["src"].split(":", 2)[2].rsplit(":", 2)[0]]
        s, lat = c.line.project(np.array([it["e"], it["n"]]))
        assert abs(lat) - float(c.hw_at(s)) >= GP.MIN_FROM_CARRIAGEWAY_M - 1e-6        # never on the carriageway
