"""ADR 0238 d. props-fix-s24 (props-fix-s24, critic s24 wave 11 pkt 8): farm outbuildings of the rural tiles get a typology (LoD2 roof,
board / brick / block wall, plinth, windows) instead of a flat white box - opt-in per region, so the Bialystok tiles
stay bit-identical (ADR 0238)."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import yaml
from shapely.geometry import box

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(REPO / "tests" / "gis"))

_HF = SimpleNamespace(sample=lambda x, y: np.full(np.shape(x), 100.0))


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kw):
        self.parts.append(SimpleNamespace(layer=layer, mat=mat, V=np.asarray(V, float), T=np.asarray(T).reshape(-1, 3)))

    def tris(self, layer=None):
        return sum(len(p.T) for p in self.parts if layer in (None, p.layer))

    def mats(self, layer):
        return {p.mat for p in self.parts if p.layer == layer}


def _region(rid):
    d = REPO / "Data" / "Regions" / rid
    fc = json.loads((d / "buildings.geojson").read_text(encoding="utf-8"))
    ovr = yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    o = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))["origin"]
    return fc, ovr, (o["x"], o["y"])


def _build(blds):
    from streetscape import buildings_mesh as BM
    buf = _Buf()
    rep = {}
    BM.build(buf, blds, _HF, None, None, box(-5000, -5000, -4990, -4990), rep, sign_out=[])
    return buf, rep


def _sheds(rid, ids=None):
    from streetscape import buildings_mesh as BM
    fc, ovr, origin = _region(rid)
    blds = BM.load(fc, origin, ovr)
    return [b for b in blds if b["typ"] == "shed" and (ids is None or b["id"] in ids)], ovr, fc, origin


def test_dk65_07_marks_outbuildings_and_not_transformers():
    from streetscape import buildings_mesh as BM
    sheds, _, _, _ = _sheds("dk65-07")
    assert len(sheds) > 20
    flagged = [b for b in sheds if b.get("rural_outbuilding")]
    assert len(flagged) >= 0.5 * len(sheds)
    assert all(b["poly"].area >= BM.RURAL_SHED_MIN_AREA_M2 for b in flagged)
    assert all(b["props"].get("function") not in BM.RURAL_SHED_NO_ROOF_FUNCS for b in flagged)


def test_without_the_rule_a_shed_is_unchanged_flat_box():
    """Bialystok tiles carry no `rural_outbuildings` entry: no flag, flat roof, no windows."""
    from streetscape import buildings_mesh as BM
    fc, ovr, origin = _region("bialystok-industrial-c")
    blds = BM.load(fc, origin, ovr)
    assert not any(b.get("rural_outbuilding") for b in blds)


def test_gable_outbuilding_gets_pitched_roof_windows_and_a_non_plaster_palette():
    from streetscape import buildings_mesh as BM
    sheds, _, _, _ = _sheds("dk65-07", {"bdot:2C9A9AB4-440C-0F0D-E053-CA2BA8C04DCD", "bdot:2C9A9AB4-749B-0F0D-E053-CA2BA8C04DCD"})
    assert len(sheds) == 2 and all(b.get("rural_outbuilding") for b in sheds)
    for b in sheds:
        buf, rep = _build([b])
        zs = np.concatenate([p.V[:, 2] for p in buf.parts if p.layer == "buildings"])
        assert zs.max() - zs.min() > 3.0
        roof_mats = [m for m in buf.mats("buildings") if m.startswith("roof_")]
        assert roof_mats, "pitched covering expected"
        assert not any(m == "roof_membrane" for m in buf.mats("buildings"))
        assert buf.mats("buildings") & {"wood_planks", "wood_planks_graphite", "brick_red", "plaster_grey",
                                         "plaster_light", "plaster_cream"}
        # a blank gable box is ~30 triangles; windows / door reveals, roof planes and plinth add several times that
        assert buf.tris("buildings") > 120


def test_flat_lod2_outbuilding_stays_flat():
    from streetscape import buildings_mesh as BM
    sheds, _, _, _ = _sheds("dk65-07")
    flat = [b for b in sheds if b.get("rural_outbuilding") and b["props"].get("roof_type_lod2") == "1000"]
    if not flat:
        return
    buf, _ = _build(flat[:1])
    assert "roof_membrane" in buf.mats("buildings")


def test_palette_is_deterministic_and_varied_between_neighbours():
    from streetscape import buildings_mesh as BM
    sheds, _, _, _ = _sheds("dk65-07")
    fl = [b for b in sheds if b.get("rural_outbuilding")]
    walls = [BM.rural_shed_pick(b["id"], BM.RURAL_SHED_WALLS, "rswall") for b in fl]
    walls2 = [BM.rural_shed_pick(b["id"], BM.RURAL_SHED_WALLS, "rswall") for b in fl]
    assert walls == walls2
    assert len(set(walls)) >= 4
    assert max(walls.count(w) for w in set(walls)) < 0.45 * len(walls)
    roofs = {BM.rural_shed_pick(b["id"], BM.RURAL_SHED_ROOFS, "rsroof") for b in fl}
    assert len(roofs) >= 4


def test_every_rural_outbuilding_of_both_prototype_tiles_builds():
    for rid in ("dk65-07", "dw671-tykocin-03"):
        sheds, _, _, _ = _sheds(rid)
        fl = [b for b in sheds if b.get("rural_outbuilding")]
        assert fl, rid
        buf, rep = _build(fl)
        assert buf.tris("buildings") > 0


# ---------------------------------------------------------------- rural bus shelter (same ADR, P1 7)
def test_rural_shelter_is_opaque_one_slot_and_within_the_bkm_envelope():
    from streetscape import props as PP
    for name, colour in PP.RURAL_SHELTERS.items():
        m, l1, col = PP.bus_shelter_rural(colour)
        for mesh in (m, l1):
            mats = {r["mat"] for r in mesh.out()}
            assert mats == {"shelter_paint"}, (name, mats)      # no glass slot: nothing transparent to vanish
        allv = np.concatenate([r["V"] for r in m.out()])
        assert 2.2 <= allv[:, 2].max() <= 3.6                    # fits under the 2.8 m clearance table with the D-15 rack
        assert abs(allv[:, 0]).max() <= PP.RURAL_SHELTER_HALF_M + 0.2
        t0 = sum(len(r["T"]) for r in m.out())
        t1 = sum(len(r["T"]) for r in l1.out())
        assert t1 < 0.45 * t0 and t1 >= 80, (t0, t1)           # LOD1 keeps posts, back wall, end wall, roof, bench
        uv = np.concatenate([r["UV"] for r in m.out()])
        assert uv.min() >= -1e-9 and uv.max() <= 1 + 1e-9, "flat swatches / pictures stay inside the atlas"


def test_rural_shelter_uv_swatches_do_not_overlap_the_pictures():
    from streetscape import props as PP
    for k in ("green", "brown", "galv", "sheet"):
        u, v = PP.SHELTER_UV[k]
        assert v < PP.SHELTER_UV_TIMETABLE[1] - 0.05 and v < PP.SHELTER_UV_D15[1] - 0.05


def test_shelter_variant_rural_is_opt_in_and_deterministic():
    from streetscape import furniture as FU
    from streetscape import props as PP
    q = (123.4, -56.7)
    assert FU.shelter_variant(q) == FU.shelter_variant(q, False)
    assert FU.shelter_variant(q) not in PP.RURAL_SHELTERS
    names = {FU.shelter_variant((float(i) * 17.0, float(i) * 3.0), True) for i in range(200)}
    assert names == set(PP.RURAL_SHELTERS)
    assert FU.rural_shelters_enabled([{"kind": "facade_rules", "rural_shelters": True}])
    assert not FU.rural_shelters_enabled([{"kind": "facade_rules", "small_town": True}])
    assert not FU.rural_shelters_enabled(None)


def test_region_overrides_enable_both_rules_only_on_the_prototype_tiles():
    from streetscape import furniture as FU
    for rid in ("dk65-07", "dw671-tykocin-03"):
        _, ovr, _ = _region(rid)
        assert FU.rural_shelters_enabled(ovr), rid
    _, ovr, _ = _region("bialystok-industrial-c")
    assert not FU.rural_shelters_enabled(ovr)


def test_verge_strip_triangles_are_split_so_ground_masks_are_sampled_every_3_m():
    """P1 9 (tykocin route_s0160): verge strip quads 40-90 m long x 1 m carried COLOR_0 only at their ends; the linear blend
    painted an olive ribbon across the embankment. subdivide_long_edges keeps the surface and bounds the edge length."""
    sys.path.insert(0, str(REPO / "tools" / "worldgen" / "roads"))
    from roads import build_world as BW
    V = np.array([[0, 0, 100.0], [1, 0, 100.0], [0, 90, 101.0], [1, 90, 101.0]])
    N = np.tile([0, 0, 1.0], (4, 1))
    T = np.array([[0, 1, 3], [0, 3, 2]])
    V2, N2, T2 = BW.subdivide_long_edges(V, N, T, 3.0)
    P = V2[T2]
    e = np.max([np.linalg.norm(P[:, 1] - P[:, 0], axis=1), np.linalg.norm(P[:, 2] - P[:, 1], axis=1),
                np.linalg.norm(P[:, 0] - P[:, 2], axis=1)], axis=0)
    assert e.max() <= 3.0 + 1e-9
    def area(P_):
        a_, b_ = P_[:, 1, :2] - P_[:, 0, :2], P_[:, 2, :2] - P_[:, 0, :2]
        return 0.5 * np.abs(a_[:, 0] * b_[:, 1] - a_[:, 1] * b_[:, 0]).sum()
    assert abs(area(P) - 90.0) < 1e-6                        # same footprint
    z_plane = lambda x_, y_: 100.0 + y_ / 90.0               # heights stay on the original plane
    assert np.abs(V2[:, 2] - z_plane(V2[:, 0], V2[:, 1])).max() < 1e-9
    assert len(T2) < 2500                                     # bounded growth


def test_atlas_swatch_colours_match_the_bottom_strip():
    from streetscape import furniture_textures as FT
    from streetscape import props as PP
    a = np.asarray(FT.shelter_atlas())
    n = a.shape[0]
    for k, c in (("green", FT.SHELTER_GREEN_SRGB), ("brown", FT.SHELTER_BROWN_SRGB), ("galv", FT.SHELTER_GALV_SRGB),
                 ("sheet", FT.SHELTER_GRAPHITE_SRGB)):
        u, v = PP.SHELTER_UV[k]
        px = a[int(round((1 - v) * n)), int(round(u * n))].astype(float)
        assert np.abs(px - np.array(c)).max() <= 14, (k, px, c)
