"""fields-s24 (ADR 0334, critic build #5 pt 3 "pola i łąki to jedna zielona płaszczyzna"): uses of the strips of the
field mosaic (shader KFUse <-> vegetation.field_use), the shader layout mirror (field_layout) and the plants of the
mosaic (baulk scrub, samosiew on fallow)."""
import re
from pathlib import Path

import numpy as np

from streetscape import vegetation as VG

ROOT = Path(__file__).resolve().parents[2]
HLSL = (ROOT / "game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl").read_text(encoding="utf-8")
ORIGIN = (761611.0, 612607.0)        # knyszyn


class _Hf:
    def __init__(self, n=1200, x0=-600.0, y1=600.0):
        self.z = np.zeros((n, n))
        self.x0, self.y1 = x0, y1


def _sq(h):           # EPSG:2180 ring around the origin (paved._poly_local subtracts the origin)
    ox, oy = ORIGIN
    return [[[ox - h, oy - h], [ox + h, oy - h], [ox + h, oy + h], [ox - h, oy + h], [ox - h, oy - h]]]


def _src(rodzaj, h=600.0):
    return {"bdot10k": {"OT_PTTR_A": [{"id": "t", "geometry": {"type": "Polygon", "coordinates": _sq(h)},
                                       "props": {"rodzaj": rodzaj}}], "OT_PTNZ_A": []}, "osm": {"areas": []}}


def test_shader_use_thresholds_match_the_python_mirror():
    body = HLSL[HLSL.index("int KFUse("):HLSL.index("void KFLook(")]
    found = [(float(v), n) for v, n in re.findall(r"if \(r < ([0-9.]+)\) return (KF_[A-Z_]+);", body)]
    ar = [c for _, c in VG.FIELD_USES_ARABLE][:-1]
    gr = [c for _, c in VG.FIELD_USES_GRASS][:-1]
    assert [v for v, _ in found] == ar + gr
    names = [n for _, n in found]
    defs = dict(re.findall(r"#define (KF_[A-Z_]+) (\d+)\n", HLSL))
    idx = [int(defs[n]) for n in names]
    assert idx == list(range(len(ar))) + list(range(len(VG.FIELD_USES_ARABLE), len(VG.FIELD_USES_ARABLE) + len(gr)))
    assert int(defs["KF_FALLOW"]) == VG.FIELD_USES.index("fallow")
    assert int(defs["KF_UNCUT"]) == VG.FIELD_USES.index("meadow_uncut")
    assert f"#define KF_OWN_SHARE {VG.FIELD_OWN_SHARE_SHADER}" in HLSL
    assert f"#define KF_BAULK_MIN_M {VG.FIELD_BAULK_W[0]}" in HLSL and f"#define KF_BAULK_SPAN_M {VG.FIELD_BAULK_W[1]}" in HLSL
    for salt in ("911u", "913u", "917u", "919u", "923u", "929u", "931u", "937u", "939u", "943u", "947u"):
        assert salt in HLSL, salt
    for salt in ("971u", "973u", "975u", "977u"):                       # ADR 0334 districts
        assert salt in HLSL, salt
    assert f"#define KF_DISTRICT_M {VG.FIELD_DISTRICT_M:.1f}" in HLSL and f"#define KF_STRETCH {VG.FIELD_STRETCH:.1f}" in HLSL
    # the layout is relative to the block seed in both (precision 700 km from the CRS origin)
    assert "float2 rel = local - seed;" in HLSL and "float2 r0 = local - sD;" in HLSL


def test_field_layout_is_a_function_of_the_position():
    x = np.linspace(760000.0, 761000.0, 301)[None, :] + np.zeros((201, 1))
    y = np.linspace(612000.0, 612600.0, 201)[:, None] + np.zeros((1, 301))
    L0 = VG.field_layout(x, y)
    L1 = VG.field_layout(x[50:120, 100:200], y[50:120, 100:200])
    for k in ("fid", "bid", "across", "block_edge"):
        assert np.array_equal(L0[k][50:120, 100:200], L1[k]), k
    assert ((L0["across"] >= 0) & (L0["across"] < L0["w"] + 1e-9)).all()
    assert (L0["w"] >= VG.FIELD_STRIP_M[0]).all() and (L0["w"] <= VG.FIELD_STRIP_M[1]).all()


def test_use_shares_follow_the_table():
    rng = np.random.default_rng(1)
    P = rng.uniform(0, 40000, (60000, 2)) + np.array([700000.0, 560000.0])
    L = VG.field_layout(P[:, 0], P[:, 1])
    for arable, table, off in ((True, VG.FIELD_USES_ARABLE, 0), (False, VG.FIELD_USES_GRASS, len(VG.FIELD_USES_ARABLE))):
        u = VG.field_use(L, arable)
        prev = 0.0
        for i, (name, c) in enumerate(table):
            share = float(np.mean(u == off + i))
            assert abs(share - (c - prev)) < 0.05, (name, share, c - prev)     # area shares, strips of unequal size
            prev = c


def test_field_plants_stand_on_baulks_and_fallow_and_do_not_depend_on_the_tile():
    hf = _Hf()
    src = _src("uprawa na gruntach ornych")
    pl = VG.field_plants(src, ORIGIN, hf)
    key = lambda q: [(round(float(p[0]), 3), round(float(p[1]), 3), s, h, t) for p, s, h, t in q]
    assert pl and key(pl) == key(VG.field_plants(src, ORIGIN, hf))           # deterministic
    baulk = np.array([p for p, _, _, t in pl if t == "baulk"])
    fallow = np.array([p for p, _, _, t in pl if t == "fallow"])
    area_km2 = ((1200 - 2 * VG.SELF_SEED_EDGE_M) / 1000.0) ** 2
    assert 20 < len(baulk) / area_km2 < 600, len(baulk) / area_km2            # sparse scrub runs, not a hedge grid
    L = VG.field_layout(baulk[:, 0] + ORIGIN[0], baulk[:, 1] + ORIGIN[1])
    e = np.minimum(L["across"], L["w"] - L["across"])
    assert (e <= 0.35 + 1e-6).all()                                          # on the strip edge (lateral jitter 0.3 m)
    if len(fallow):
        Lf = VG.field_layout(fallow[:, 0] + ORIGIN[0], fallow[:, 1] + ORIGIN[1])
        assert (VG.field_use(Lf, True) == VG.FIELD_USES.index("fallow")).all()
    # a second tile overlapping the first one plants the same baulk plants in the common part
    hf2 = _Hf(x0=-200.0, y1=1000.0)
    pl2 = VG.field_plants(_src("uprawa na gruntach ornych", 1200.0), ORIGIN, hf2)
    inner = lambda p: -190 < p[0] < 590 and -190 < p[1] < 590
    a = sorted((round(float(p[0]), 3), round(float(p[1]), 3), s) for p, s, _, t in pl if t == "baulk" and inner(p))
    b = sorted((round(float(p[0]), 3), round(float(p[1]), 3), s) for p, s, _, t in pl2 if t == "baulk" and inner(p))
    assert a and a == b
    sp = {s for _, s, _, _ in pl}
    assert sp <= {n for n, _ in VG.BAULK_SPECIES} | {n for n, _ in VG.FALLOW_SPECIES}


def test_grassland_has_no_fallow_samosiew_and_no_fields_no_plants():
    hf = _Hf(n=600, x0=-300.0, y1=300.0)
    pl = VG.field_plants(_src("roślinność trawiasta", 300.0), ORIGIN, hf)
    assert all(t == "baulk" for _, _, _, t in pl)
    assert VG.field_plants({"bdot10k": {"OT_PTTR_A": []}, "osm": {"areas": []}}, ORIGIN, hf) == []


def test_blocks_of_a_district_have_distinct_ids():
    """_h32(i, j) == _h32(-i, -j) (odd multipliers): the signed block indices of the district frame are offset before
    hashing (KF_BLOCK_HASH_OFS), else mirror blocks shared one id - one crop, one baulk plant set, two places."""
    assert f"#define KF_BLOCK_HASH_OFS {VG.FIELD_BLOCK_HASH_OFS}" in HLSL
    x = np.arange(755000.0, 768000.0, 25.0)
    X, Y = np.meshgrid(x, np.arange(605000.0, 618000.0, 25.0))
    L = VG.field_layout(X.ravel(), Y.ravel())
    seeds = {}
    for b, sx, sy in zip(L["bid"], np.round(L["sx"], 3), np.round(L["sy"], 3)):
        seeds.setdefault(int(b), set()).add((sx, sy))
    assert all(len(v) == 1 for v in seeds.values())
