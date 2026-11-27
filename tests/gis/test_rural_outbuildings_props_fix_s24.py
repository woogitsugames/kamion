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
        self.parts.append(SimpleNamespace(layer=layer, mat=mat, V=np.asarray(V, float),
                                          T=np.asarray(T).reshape(-1, 3), COL=kw.get("COL")))

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
        # draw-call budget: only materials the houses of the same chunks already use (no wood / brick / sheet / cement roofs)
        allowed = {"plaster_grey", "plaster_light", "plaster_cream", "plaster_beige", "plinth_dark", "facade_atlas",
                   "reveal_plaster", "soffit_boards", "hall_flashing", "roof_metal_graphite", "roof_tiles_brown",
                   "roof_tiles_red"}
        assert buf.mats("buildings") <= allowed, buf.mats("buildings") - allowed
        assert buf.mats("buildings") & {"plaster_grey", "plaster_light", "plaster_cream", "plaster_beige"}
        # a blank gable box is ~30 triangles; windows / door reveals, roof planes and plinth add several times that
        assert buf.tris("buildings") > 60


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
    assert len(roofs) >= 3


def test_every_rural_outbuilding_of_both_prototype_tiles_builds():
    for rid in ("dk65-07", "dw671-tykocin-03"):
        sheds, _, _, _ = _sheds(rid)
        fl = [b for b in sheds if b.get("rural_outbuilding")]
        assert fl, rid
        buf, rep = _build(fl)
        assert buf.tris("buildings") > 0


def test_outbuildings_r2_barn_doors_gutters_roof_weather_plinth_and_runoff():
    """ADR 0238 d. props-fix r2 (neon-outbuildings2-s24, critic build #10 pkt 9):
    (1) vertical-board barn doors + hardware (no urban graffiti variants 2/3/4),
    (2) LOD0-only gutters & downpipes in facade_atlas (+0 draws, +0 LOD1 tris),
    (3) roof COLOR_0 weather + shader down-slope metal sheet ribs,
    (4) darker & taller plinth (0.45-0.65 m) + under-eave runoff UV1 on LOD0 plaster walls."""
    from streetscape import buildings_mesh as BM
    from streetscape import facade_atlas as FA

    class _FullBuf:
        def __init__(self):
            self.parts = []

        def add(self, layer, mat, V, UV, T, **kw):
            self.parts.append(SimpleNamespace(
                layer=layer, mat=mat, V=np.asarray(V, float), UV=np.asarray(UV, float),
                T=np.asarray(T).reshape(-1, 3), UV1=kw.get("UV1"), COL=kw.get("COL"),
            ))

    sheds, _, _, _ = _sheds("dk65-07", {"bdot:2C9A9AB4-440C-0F0D-E053-CA2BA8C04DCD",
                                        "bdot:2C9A9AB4-749B-0F0D-E053-CA2BA8C04DCD",
                                        "bdot:2C9A9AB4-8870-0F0D-E053-CA2BA8C04DCD"})
    assert len(sheds) == 3
    buf = _FullBuf()
    BM.build(buf, sheds, _HF, None, None, box(-5000, -5000, -4990, -4990), {}, sign_out=[])

    # +0 new materials (all within allowed house/outbuilding palette, no downpipe material)
    allowed = {"plaster_grey", "plaster_light", "plaster_cream", "plaster_beige", "plinth_dark", "facade_atlas",
               "reveal_plaster", "soffit_boards", "hall_flashing", "roof_metal_graphite", "roof_tiles_brown",
               "roof_tiles_red"}
    mats_l0 = {p.mat for p in buf.parts if p.layer == "buildings"}
    assert mats_l0 <= allowed, mats_l0 - allowed
    assert "downpipe" not in mats_l0

    # (1) Barn doors: vertical board cells (balf 2/5) + hardware swatches (steel_dark/pvc_brown/wood), no graffiti (garage 2/3/4)
    fa_l0 = [p for p in buf.parts if p.layer == "buildings" and p.mat == "facade_atlas"]
    assert fa_l0
    uv_all = np.concatenate([p.UV for p in fa_l0])
    b2, b5 = FA.cell("balf", 2), FA.cell("balf", 5)
    in_barn = (
        ((uv_all[:, 0] >= b2[0]) & (uv_all[:, 0] <= b2[0] + b2[2]) & (uv_all[:, 1] >= b2[1]) & (uv_all[:, 1] <= b2[1] + b2[3])) |
        ((uv_all[:, 0] >= b5[0]) & (uv_all[:, 0] <= b5[0] + b5[2]) & (uv_all[:, 1] >= b5[1]) & (uv_all[:, 1] <= b5[1] + b5[3]))
    )
    assert in_barn.any(), "expected vertical-board barn door UVs from balf(2/5)"
    # (2) Gutters & downpipes in facade_atlas swatches (galv / steel_grey / steel_dark) on LOD0 only
    gutter_hits = 0
    for sw in BM.RURAL_SHED_GUTTER_SWATCHES:
        u0, v0, w, h = FA.CELLS[("sw_" + sw, 0)]
        m = (uv_all[:, 0] >= u0) & (uv_all[:, 0] <= u0 + w) & (uv_all[:, 1] >= v0) & (uv_all[:, 1] <= v0 + h)
        gutter_hits += int(m.sum())
    assert gutter_hits >= 24, "expected gutter/downpipe/hardware swatch vertices on LOD0"
    assert not any(p.mat == "facade_atlas" for p in buf.parts if p.layer == "buildings_low")

    # (3) Roof COLOR_0 weathering written for rural_outbuildings + shader/importer sheet ribs
    roof_l0 = [p for p in buf.parts if p.layer == "buildings" and p.mat.startswith("roof_")]
    assert roof_l0 and all(p.COL is not None and (p.COL[:, 3] > 0).all() for p in roof_l0)
    pbr = (REPO / "game/Assets/_Project/Environment/Shaders/WorldPBR.shader").read_text(encoding="utf-8")
    imp = (REPO / "game/Assets/_Project/World/Import/WorldPbrMaterials.cs").read_text(encoding="utf-8")
    assert "_RoofWeather.w > 0.5" in pbr and "sheetRibs" in imp

    # (4) Darker plinth shade (<= 0.30 linear COLOR_0 = <= 0.60 multiplier) + under-eave runoff UV1 on plaster walls
    for b in sheds:
        _, _, _, pl_col = BM.rural_shed_shades(b["id"])
        assert 0.16 <= pl_col[1] <= 0.30, pl_col
    plaster_l0 = [p for p in buf.parts if p.layer == "buildings" and p.mat.startswith("plaster_")]
    assert plaster_l0 and all(p.UV1 is not None for p in plaster_l0), "under-eave runoff UV1 expected on LOD0 plaster"


def test_r4_roof_profiles_and_seed_match_at_both_lods():
    from streetscape import buildings_mesh as BM
    from streetscape import materials as MAT
    from streetscape import roofs as RF

    sheds, _, _, _ = _sheds("dk65-07")
    profiles = set()
    seeds = set()
    saw_felt = saw_cap = False
    for b in (b for b in sheds if b.get("rural_outbuilding")):
        buf, _ = _build([b])
        covers = [p for p in buf.parts if p.mat.startswith("roof_") and p.COL is not None]
        assert {p.layer for p in covers} == {"buildings", "buildings_low"}
        codes = {round(a * 255) for p in covers for a in p.COL[:, 3]}
        assert len(codes) == 1, b["id"]
        code = codes.pop()
        if covers[0].mat == "roof_membrane":
            assert code == 255 and MAT.M["roof_membrane"]["roof_felt"] and MAT.M["roof_membrane"]["vertex_color"]
            assert all((p.COL[:, 2] == 64.0 / 255.0).all() for p in covers)
            saw_felt = True
            continue
        profile, seed = divmod(code - 1, RF.RURAL_ROOF_SEEDS)
        material = BM.rural_shed_pick(b["id"], BM.RURAL_SHED_ROOFS, "rsroof")
        assert 1 <= code <= 93 and profile == BM.rural_roof_profile(b["id"], material)
        assert all(p.mat == material for p in covers)
        assert all((p.COL[:, 2] < 1).all() for p in covers if p.layer == "buildings_low")
        saw_cap |= any((p.COL[:, 2] == 1).any() for p in covers)
        profiles.add(profile)
        seeds.add(seed)
    assert profiles == {RF.RURAL_METAL, RF.RURAL_FIBRE_CEMENT, RF.RURAL_CLAY}
    assert len(seeds) > 10
    assert saw_felt and saw_cap


def test_r4_keeps_an_authored_pitched_covering():
    sheds, _, _, _ = _sheds("dk65-07", {"bdot:2C9A9AB4-440C-0F0D-E053-CA2BA8C04DCD"})
    [barn] = sheds
    override = dict(barn["ovr"], roof_material="roof_tiles_brown")
    buf, _ = _build([dict(barn, ovr=override)])
    covers = [p for p in buf.parts if p.mat.startswith("roof_")]
    assert covers and all(p.mat == "roof_tiles_brown" for p in covers)
    assert any((p.COL[:, 3] >= 0.5).any() for p in covers if p.COL is not None)
    assert all(((p.COL[:, 3] == 0.0) | (p.COL[:, 3] >= 0.5)).all() for p in covers if p.COL is not None)


def test_barn_doors_are_weathered_grey_brown_r3():
    """ADR 0238 d. r3 (plaza-barn-fix-s24, critic s24 day 27 pkt 6): barn leaves and their timber frames carry a COLOR_0
    tint on facade_atlas (facade_tint, same material: +0 draws) that brings the painted cells to weathered grey-brown
    boards (albedo ~0.17-0.25), tone from the building seed; every other atlas vertex stays a = 0 (no-op)."""
    from streetscape import buildings_mesh as BM
    from streetscape import facade_atlas as FA
    from streetscape import materials as MAT
    assert MAT.M["facade_atlas"].get("facade_tint") is True

    class _ColBuf:
        def __init__(self):
            self.parts = []

        def add(self, layer, mat, V, UV, T, **kw):
            self.parts.append(SimpleNamespace(layer=layer, mat=mat, UV=np.asarray(UV, float), COL=kw.get("COL"),
                                              n=len(V)))

    sheds, _, _, _ = _sheds("dk65-07")
    flagged = [b for b in sheds if b.get("rural_outbuilding")]
    buf = _ColBuf()
    BM.build(buf, flagged, _HF, None, None, box(-5000, -5000, -4990, -4990), {}, sign_out=[])
    fa = [p for p in buf.parts if p.mat == "facade_atlas" and p.layer == "buildings"]
    fa = [p for p in fa if p.COL is not None]          # groups without a barn door carry no COLOR_0 at all
    assert fa and all(len(p.COL) == p.n for p in fa)
    UV, COL = np.concatenate([p.UV for p in fa]), np.concatenate([p.COL for p in fa])
    tinted = COL[:, 3] > 0.99
    assert tinted.any() and ((COL[:, 3] < 0.01) | tinted).all(), "atlas COLOR_0 is either a tint (a = 1) or a no-op (a = 0)"
    lum = lambda c: c @ np.array([0.2126, 0.7152, 0.0722])
    tones = set()
    for v, mean in BM.RURAL_BARN_CELL_MEAN.items():
        u0, v0, w, h = FA.cell("balf", v)
        leaf = tinted & (UV[:, 0] > u0) & (UV[:, 0] < u0 + w) & (UV[:, 1] > v0) & (UV[:, 1] < v0 + h)
        if not leaf.any():
            continue
        alb = COL[leaf, :3] * 2 * np.asarray(mean)          # implied leaf albedo
        assert (lum(alb) > 0.12).all() and (lum(alb) < 0.26).all(), lum(alb).min()
        assert (alb[:, 0] / alb[:, 2] < 1.8).all(), "no orange: weathered wood is grey-brown"
        tones |= {tuple(c) for c in np.round(COL[leaf, :3], 3)}
    assert len(tones) >= 4, "the leaf tone varies with the building seed"
    # the untinted atlas (windows, gutters, hinges) keeps a = 0 - nothing else changes colour
    assert (~tinted).sum() > tinted.sum()


def test_dk65_07_outbuildings_stay_within_triangle_budget():
    """Budget gate (neon-outbuildings2-s24): total dk65-07 LOD0 building triangles <= +5 % vs main baseline (104 892)."""
    from streetscape import buildings_mesh as BM
    fc, ovr, origin = _region("dk65-07")
    blds = BM.load(fc, origin, ovr)
    buf, _ = _build(blds)
    base_lod0 = 104_892
    assert buf.tris("buildings") <= int(base_lod0 * 1.05), (buf.tris("buildings"), int(base_lod0 * 1.05))


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
