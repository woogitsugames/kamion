"""fields3-s24 (ADR 0334 r3, critic s24 wave10-pre 1): layout warp mirror, grassland flag as the low code, ragged
field margins, maize rows and baulk sward as cards (streetscape.field_crops), verge atlas of distinct growth forms
and the Poisson-like scatter (streetscape.verge_flora r5 / verge_atlas)."""
import re
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from roads.meshing import MeshBuf
from streetscape import field_crops as FC
from streetscape import vegetation as VG
from streetscape import verge_atlas as VA
from streetscape import verge_flora as VF

ROOT = Path(__file__).resolve().parents[2]
HLSL = (ROOT / "game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl").read_text(encoding="utf-8")
EDGE_CS = (ROOT / "game/Assets/_Project/World/Import/WorldEdgeBuilder.cs").read_text(encoding="utf-8")
ORIGIN = (761611.0, 612607.0)        # knyszyn


class _Hf:
    def __init__(self, n=1200, x0=-600.0, y1=600.0):
        self.z = np.zeros((n, n))
        self.x0, self.y1 = x0, y1


def test_warp_constants_match_the_shader():
    (cl, al, s1, s2), (cs, as_, s3, s4) = VG.FIELD_WARP
    for name, v in (("KF_WARP_L_M", cl), ("KF_WARP_AL", al), ("KF_WARP_S_M", cs), ("KF_WARP_AS", as_)):
        assert f"#define {name} {v:.1f}" in HLSL
    for salt in (s1, s2, s3, s4):
        assert f"{salt}u" in HLSL
    assert "float2 cD = floor((lw + origin) / KF_DISTRICT_M);" in HLSL
    assert "float rowc = dot(relR, dir) + wob;" in HLSL            # rows stay on the unwarped coordinate
    assert f"KFBand(rc + 0.375, {FC.MAIZE_ROW_M}, 0.30, fpr)" in HLSL   # the card rows stand on the shader's rows


def test_layout_warp_bows_the_edges_by_metres_and_inverts():
    rng = np.random.default_rng(5)
    P = rng.uniform(0, 6000, (20000, 2)) + np.array([758000.0, 609000.0])
    dx, dy = VG.field_warp(P[:, 0], P[:, 1])
    lim = 0.5 * sum(a for _, a, _, _ in VG.FIELD_WARP)
    assert np.abs(dx).max() <= lim and np.abs(dy).max() <= lim and np.abs(dx).max() > 0.6 * lim
    assert 1.2 < np.std(dx) < 3.0                                  # metres: visible 300 m away, not a zigzag
    dx2, _ = VG.field_warp(P[:, 0] + 10.0, P[:, 1])               # 10 m on: well under a metre (no kinks)
    assert np.abs(dx2 - dx).max() < 1.2
    x, y = VG.field_unwarp(P[:, 0] + dx, P[:, 1] + dy)
    assert np.abs(x - P[:, 0]).max() < 0.01 and np.abs(y - P[:, 1]).max() < 0.01


def test_grassland_flag_is_the_low_code_and_margins_are_ragged():
    assert VG.FIELD_FLAG_B["roślinność trawiasta"] == 0.0 and VG.FIELD_FLAG_B["uprawa na gruntach ornych"] == 1.0
    m0, m1 = (float(re.search(rf"#define {n} ([0-9.]+)", HLSL).group(1)) for n in ("KF_MEADOW_B0", "KF_MEADOW_B1"))
    assert 0.0 < m0 < m1 < VG.GROUND_B_MIN                          # open ground never reads as a meadow
    assert "bc.b >= 219 || bc.b <= 8" in EDGE_CS and 8 / 255.0 < m1 and 219 / 255.0 > VG.GROUND_B_MAX
    hf = _Hf(n=700, x0=-350.0, y1=350.0)
    far = np.full(hf.z.shape, 100.0)
    sq = [[[-250, -250], [250, -250], [250, 250], [-250, 250], [-250, -250]]]

    def masks(rodzaj):
        src = {"bdot10k": {"OT_PTTR_A": [{"id": "t", "geometry": {"type": "Polygon", "coordinates": sq},
                                          "props": {"rodzaj": rodzaj}}], "OT_PTNZ_A": []}, "osm": {"areas": []}}
        return VG.ground_masks(src, (0.0, 0.0), hf, far, [])[..., 2]
    B = masks("uprawa na gruntach ornych")
    field = B > 0.985
    assert field[300:400, 300:400].all()
    # the crop stops 1 .. 9 m short of the polygon line, by a different amount along it
    d = np.array([np.argmax(field[j, 100:350]) for j in range(150, 550)])        # first field cell west of centre
    assert d.min() >= 1 and d.max() <= 1 + sum(VG.FIELD_MARGIN_M) + 3 and d.max() - d.min() >= 2
    assert VG.GROUND_B_MIN - 1e-6 <= B[:90, :90].min() and B[:90, :90].max() <= VG.GROUND_B_MAX + 1e-6
    M = masks("roślinność trawiasta")
    assert np.allclose(M[300:400, 300:400], 0.0, atol=1e-4) and M[:90, :90].min() >= VG.GROUND_B_MIN - 1e-6


def _crop_world(n=500):
    """A flat arable square 60 m from any road."""
    hf = _Hf(n=n, x0=-n / 2.0, y1=n / 2.0)
    col = np.zeros((n, n, 4), np.float32)
    col[10:-10, 10:-10, 2] = 1.0
    return MeshBuf(), hf, col, np.full((n, n), 60.0)


def _maize_origin():
    """A layout origin whose 500 m square holds maize strips (the layout is a function of the position)."""
    for k in range(40):
        o = (ORIGIN[0] + 700.0 * k, ORIGIN[1] + 300.0 * k)
        x, y = np.meshgrid(np.arange(-240.0, 240.0, 12.0) + o[0], np.arange(-240.0, 240.0, 12.0) + o[1])
        if (VG.field_use(VG.field_layout(x, y), True) == VG.FIELD_USES.index("maize")).mean() > 0.15:
            return o
    raise AssertionError("no maize within the search")


def test_maize_cards_stand_on_the_rows_of_maize_strips_at_summer_height():
    o = _maize_origin()
    buf, hf, col, dist = _crop_world()
    rep = {}
    ntri = FC.build(buf, col, hf, np.zeros(hf.z.shape), o, dist, None, rep)
    mz = [p for p in buf.parts if p.src == "field_crops:maize"]
    assert ntri > 0 and len(mz) == 1 and (mz[0].layer, mz[0].mat) == ("banks", "verge_tufts")
    V = mz[0].V.reshape(-1, 4, 3)
    assert len(V) == rep["field_crops"]["maize"]["row_cards"] > 100
    h = V[:, 2:, 2].mean(1) - V[:, :2, 2].mean(1)
    assert h.min() >= FC.MAIZE_H[0] and h.max() <= FC.MAIZE_H[1] + FC.MAIZE_SINK_M + 1e-6      # 2-2.5 m (WORKING_VALUE)
    assert 2.0 <= FC.MAIZE_H[0] and FC.MAIZE_H[1] <= 2.5
    mid = V[:, :2, :2].mean(1)
    L = VG.field_layout(mid[:, 0] + o[0], mid[:, 1] + o[1])
    assert (VG.field_use(L, True) == VG.FIELD_USES.index("maize")).all()
    assert (np.minimum(L["across"], L["w"] - L["across"]) > FC.MAIZE_SEAM_CLEAR_M - 0.3).all()   # off the baulks
    # every card lies on a crop row of the shader: row coordinate = whole multiples of the card-row pitch
    rx, ry = mid[:, 0] + o[0] - L["sx"], mid[:, 1] + o[1] - L["sy"]
    rowc = rx * np.cos(L["th"]) + ry * np.sin(L["th"]) + L["wob"]
    pitch = FC.MAIZE_ROW_M * FC.MAIZE_CARD_ROWS
    assert np.abs(rowc / pitch - np.rint(rowc / pitch)).max() * pitch < 0.10
    assert np.allclose(np.hypot(*(V[:, 1, :2] - V[:, 0, :2]).T), FC.MAIZE_CARD_L, atol=0.08)
    uv = mz[0].UV.reshape(-1, 4, 2)
    assert uv[..., 1].min() >= VA.V_MAIZE[0] and uv[..., 1].max() <= VA.V_MAIZE[1]
    assert np.allclose(np.abs(uv[:, 1, 0] - uv[:, 0, 0]), 2.0 / VA.N_MAIZE)
    # deterministic; nothing without arable land, nothing when disabled (town tiles)
    buf2 = MeshBuf()
    FC.build(buf2, col, hf, np.zeros(hf.z.shape), o, dist, None, {})
    assert np.array_equal(next(p for p in buf2.parts if p.src == "field_crops:maize").V, mz[0].V)
    assert FC.build(MeshBuf(), col * 0.0, hf, np.zeros(hf.z.shape), o, dist, None, {}) == 0
    assert FC.build(MeshBuf(), col, hf, np.zeros(hf.z.shape), o, dist, None, {}, enabled=False) == 0
    # far from every road: no cards (the flat colour is enough there)
    assert not [p for p in _far(col, hf, o).parts if p.src.startswith("field_crops:maize")]


def _far(col, hf, o):
    buf = MeshBuf()
    FC.build(buf, col, hf, np.zeros(hf.z.shape), o, np.full(hf.z.shape, FC.MAIZE_ROAD_RANGE_M + 50.0), None, {})
    return buf


def test_baulk_sward_stands_on_baulks_in_clumps_of_several_forms():
    buf, hf, col, dist = _crop_world(n=700)
    rep = {}
    FC.build(buf, col, hf, np.zeros(hf.z.shape), ORIGIN, dist, None, rep)
    bk = next(p for p in buf.parts if p.src == "field_crops:baulk")
    n = rep["field_crops"]["baulk_sward"]["plants"]
    V = bk.V.reshape(-1, 4, 3)[:n]
    mid = V[:, :2, :2].mean(1)
    L = VG.field_layout(mid[:, 0] + ORIGIN[0], mid[:, 1] + ORIGIN[1])
    e = np.minimum(L["across"], L["w"] - L["across"])
    on_seam = e < FC.BAULK_BAND_M + 0.7
    on_border = L["block_edge"] < FC.BAULK_BORDER_M[1] + 0.7
    assert (on_seam | on_border).all() and on_seam.mean() > 0.5
    h = V[:, 2:, 2].mean(1) - V[:, :2, 2].mean(1)
    assert 0.3 <= h.min() and h.max() <= 1.30 + VF.SINK_M + 1e-6 and h.std() > 0.12
    forms = rep["field_crops"]["baulk_sward"]["forms"]
    assert sum(1 for v in forms.values() if v > 0.03 * n) >= 4               # several growth forms, none alone
    d = cKDTree(mid).query(mid, k=2)[0][:, 1]                                # clumps and gaps, not a picket line
    assert np.std(d) / np.mean(d) > 0.6
    uv = bk.UV.reshape(-1, 4, 2)
    assert uv[..., 1].min() >= VF.V_TALL[0] and uv[..., 1].max() <= VF.V_TALL[1]


def test_verge_atlas_has_distinct_growth_forms_and_the_scatter_has_no_rhythm():
    assert len(set(VA.TALL_FORMS)) == VA.NT and len(set(VA.SHORT_FORMS)) == VA.NT
    assert sum(1 for f in VA.TALL_FORMS if f not in VF.GRASS) >= 4 and sum(1 for f in VA.SHORT_FORMS if f not in VF.GRASS) >= 3
    for table in (VF.FORMS_EDGE, VF.FORMS_SLOPE, VF.FORMS_BOTTOM, VF.FORMS_BAULK):
        assert abs(sum(w for _, w in table) - 1.0) < 1e-6
        assert all(n in VA.TALL_FORMS + VA.SHORT_FORMS for n, _ in table)
    u0, u1, v0, v1 = VF.form_uv("tansy")                                     # one plant per card
    assert abs((u1 - u0) - 1.0 / VA.NT) < 1e-9 and VF.V_TALL[0] <= v0 < v1 <= VF.V_TALL[1]
    ss = np.arange(0.0, 4000.0, 0.7)
    picks = [VF.pick_form(VF.FORMS_SLOPE, "c7:R", s, VF._h("u", s)) for s in ss]
    share = {n: picks.count(n) / len(picks) for n, _ in VF.FORMS_SLOPE}
    assert share["tussock"] > 0.15 and all(share[n] > 0.01 for n, _ in VF.FORMS_SLOPE)
    # colonies: the same forb for metres on end, another one further on
    tansy = np.array([p == "tansy" for p in picks], float)
    cnt = tansy[: len(tansy) // 40 * 40].reshape(-1, 40).sum(1)              # per 28 m of road
    assert cnt.var() > 2.5 * cnt.mean() and (cnt == 0).mean() > 0.3           # stands and stretches without any
    wins = [[q for q in picks[i:i + 40] if q not in VF.GRASS] for i in range(0, len(picks) - 40, 40)]
    assert len({max(set(w), key=w.count) for w in wins if len(w) >= 10}) >= 3     # another forb's stand further on
    # scatter: slots on the global chainage, kept by a density with bare stretches
    pos = [sc for sc, q in VF._slots(0.0, 600.0, "c7:R", "e")
           if VF._h("c7:R", "e", q, "k") < VF._density("c7:R", "e", sc) * VF.RATE_EDGE * VF.SLOT_M]
    gaps = np.diff(pos)
    assert len(pos) > 150 and np.std(gaps) / np.mean(gaps) > 1.0 and gaps.max() > 6.0      # Poisson = 1.0; clusters > 1
    sc = np.array([VF._scale(("k", i)) for i in range(2000)])
    assert sc.min() >= VF.SCALE[0] and sc.max() <= VF.SCALE[1] and sc.min() < 0.7 and sc.max() > 1.3


def test_atlas_image_layout():
    im = np.asarray(VA.texture())
    assert im.shape == (VA.TEX_H, VA.TEX_W, 4)
    a = im[..., 3] > 127
    cw, q = VA.TEX_W // VA.NT, VA.TEX_H // 4
    for r in (2, 3):                                 # plant rows: every cell holds a plant with clear side margins
        for k in range(VA.NT):
            cell = a[r * q:(r + 1) * q, k * cw:(k + 1) * cw]
            assert cell.mean() > 0.02 and not cell[:, :3].any() and not cell[:, -3:].any()
    mz = a[: VA.TEX_H // 2]
    assert mz[int(0.25 * mz.shape[0]):int(0.9 * mz.shape[0])].mean() > 0.6      # a dense wall of leaves
    assert mz[: int(0.03 * mz.shape[0])].mean() < 0.35                          # tassels against the sky at the top
