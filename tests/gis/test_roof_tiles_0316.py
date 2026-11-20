"""ADR 0316 (roof-tiles-s24): ceramic roof tile sets by covering, covering variants of the rule roofs, ridge cap UV,
and the plot kit fence rows (natural / painted pickets, galvanised chain-link)."""
import sys
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import box

from streetscape import buildings_mesh as BM
from streetscape import materials as MT
from streetscape import plot_kit as PK
from streetscape import plots as PL
from streetscape import roofs as RF

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "art-source/world/materials/_src"))


def test_every_covering_has_its_own_set():
    import sets_facade as F
    want = {"roof_tiles_red": "roof_tiles", "roof_tiles_old": "roof_tiles_old", "roof_tiles_brown": "roof_zakladkowa",
            "roof_cement_grey": "roof_zakladkowa", "roof_karp_red": "roof_karpiowka", "roof_metal_graphite": "roof_metal_tile"}
    for mat, st in want.items():
        m = MT.M[mat]
        assert m["texture_set"] == st and m["set_tile"] is True and m["tint_linear"] is True, mat
        assert st in F.FACADE_SETS
    # the tile sets are larger than the 1.4 m lattice of ADR 0091 (7 x 4 tiles repeated over every slope)
    for st in ("roof_tiles", "roof_karpiowka", "roof_zakladkowa"):
        assert F.FACADE_SETS[st]["tile_m"] == [4.2, 4.2]
    assert F.FACADE_SETS["roof_metal_tile"]["tile_m"] == [1.4, 1.4]          # a pressed sheet is a lattice
    # LOD1 draws the plain tile with the S-tile material: same colour, so no tone step at the LOD switch
    assert BM.ROOF_LOD1 == {"roof_karp_red": "roof_tiles_red"}
    assert MT.M["roof_karp_red"]["color"] == MT.M["roof_tiles_red"]["color"]
    for mat in ("roof_tiles_red", "roof_tiles_brown", "roof_karp_red", "roof_cement_grey"):
        assert MT.M[mat]["macro"][1] > 0.1


@pytest.mark.parametrize("name,cols,rows", [("roof_tiles", 21, 12), ("roof_tiles_old", 14, 8), ("roof_karpiowka", 23, 28),
                                            ("roof_zakladkowa", 18, 12)])
def test_tile_sets_are_neutral_tileable_and_not_a_lattice(name, cols, rows):
    import sets_roof as R
    s = getattr(R, name)(256)
    L = s.c.Lx
    assert s.albedo.shape == (256, 256, 3) and s.albedo.mean() == pytest.approx(0.5, abs=0.01)
    assert 0.010 < s.height.max() - s.height.min() < 0.06                    # tile relief 1-6 cm
    lum = s.albedo.mean(-1)
    # tileable: the wrap-around seam is no stronger than an ordinary texel step
    step = np.abs(np.diff(lum, axis=1)).mean()
    assert np.abs(lum[:, 0] - lum[:, -1]).mean() < 3 * step and np.abs(lum[0] - lum[-1]).mean() < 6 * np.abs(np.diff(lum, axis=0)).mean()
    # not a lattice: the mean tone of the tile cells varies in clusters (neighbouring cells correlate) ...
    cw, ch = 256 // cols, 256 // rows
    cells = np.array([[lum[int(r * 256 / rows):int(r * 256 / rows) + ch, int(c * 256 / cols):int(c * 256 / cols) + cw].mean()
                       for c in range(cols)] for r in range(rows)])
    assert cells.std() > 0.012
    # ... and the two halves of the set are not copies of each other (the 1.4 m set repeated every 7 x 4 tiles)
    assert np.abs(cells[:, :cols // 2] - cells[:, cols - cols // 2:]).mean() > 0.008
    assert L in (2.8, 4.2)


def test_roof_variant_is_deterministic_and_keeps_other_roofs():
    keys = [f"bdot:{i:05d}" for i in range(4000)]
    got = [BM.roof_variant(k, "roof_tiles_red", False) for k in keys]
    assert got == [BM.roof_variant(k, "roof_tiles_red", False) for k in keys]
    share = got.count("roof_karp_red") / len(got)
    assert set(got) == {"roof_tiles_red", "roof_karp_red"} and abs(share - BM.KARP_SHARE) < 0.03
    old = [BM.roof_variant(k, "roof_tiles_red", True) for k in keys]
    assert set(old) == {"roof_tiles_red", "roof_tiles_old"} and abs(old.count("roof_tiles_old") / len(old) - BM.OLD_TILE_SHARE) < 0.03
    for m in ("roof_tiles_brown", "roof_metal_graphite", "roof_sheet_grey", "roof_karp_red", "roof_cement_grey"):
        assert BM.roof_variant(keys[0], m, False) == m and BM.roof_variant(keys[0], m, True) == m
    assert {"roof_karp_red", "roof_cement_grey"} <= BM.ROOF_OVERRIDES
    assert BM.house_roof_material({"id": "h", "ovr": {"roof_material": "roof_karp_red"}}, "roof_tiles_red") == "roof_karp_red"


def _kf(salt):
    return 0.5


@pytest.mark.parametrize("mat", ["roof_tiles_red", "roof_karp_red", "roof_tiles_brown", "roof_metal_graphite"])
def test_ridge_cap_uv_stays_inside_one_profile_strip(mat):
    fp = box(0, 0, 12, 8)
    r = RF.plan(fp, {"roof_type_lod2": "1030", "height_lod2_2017_m": 7.0, "lod2_eave_rel_m": 3.2}, 5.3, 100.0, _kf)
    acc = BM.Acc()
    RF.build(acc, r, fp, mat, low_mat=BM.ROOF_LOD1.get(mat))
    low = BM.ROOF_LOD1.get(mat, mat)
    assert ("buildings_low", low) in acc.d and (low == mat or ("buildings_low", mat) not in acc.d)
    zmax = max(float(it[0][:, 2].max()) for it in acc.d[("buildings", mat)])
    cap = [it for it in acc.d[("buildings", mat)] if len(it[0]) == 8 and float(it[0][:, 2].max()) == pytest.approx(zmax)]
    assert len(cap) == 1
    uv = np.asarray(cap[0][2])
    if mat in RF.RIDGE_UV:
        uc, uh, vs = RF.RIDGE_UV[mat]
        assert uv[:, 0].min() == pytest.approx(uc - uh) and uv[:, 0].max() == pytest.approx(uc + uh)
        assert uv[:, 1].max() == pytest.approx(13.0 * vs, abs=0.3 * vs)
    else:
        assert uv[:, 0].min() == pytest.approx(-0.11) and uv[:, 0].max() == pytest.approx(0.11)
    # S-tile: the strip is exactly the roll of one tile (0.70 of the 0.20 m cover width)
    assert RF.RIDGE_UV["roof_tiles_red"][0] + RF.RIDGE_UV["roof_tiles_red"][1] == pytest.approx(0.70 * 0.20)


# rows of the atlas as they were before ADR 0316 (y0 px, height px): regions built earlier hold these UVs
_OLD_ROWS = {"picket": (5, 150), "boards_rust": (5, 150), "boards_brown": (165, 150), "chainlink": (165, 150),
             "concrete": (325, 150), "bars": (325, 150), "lamella": (485, 150), "boards_grey": (485, 150), "wall": (645, 56),
             "brick": (711, 160), "swatch": (881, 28), "thuja": (919, 180), "hedge": (1109, 170), "sprites": (1289, 256),
             "tall": (1555, 420)}


def test_plot_kit_new_rows_do_not_move_the_old_ones():
    for name, yh in _OLD_ROWS.items():
        assert PK.ROW_Y[name] == yh, name
    y0, h = PK.ROW_Y["picket_wood"]
    assert PK.ROW_Y["picket_paint"] == (y0, h) and y0 >= 1555 + 420 + PK.PAD and y0 + h + PK.PAD // 2 <= PK.N
    assert {"picket_wood", "picket_paint"} <= PK.HALF_ROWS and PK.ROW_H_M["picket_wood"] == PK.ROW_H_M["picket_paint"] == 1.30
    im = np.asarray(PK.atlas()).astype(float)

    def texels(name):
        y0, h = PK.ROW_Y[name]
        x0, w = PK.ROW_X[name]
        row = im[y0:y0 + h, x0:x0 + w]
        return row[row[..., 3] > 200][:, :3]
    cov = PK.coverage()
    assert 0.5 < cov["picket_wood"] < 0.8 and 0.5 < cov["picket_paint"] < 0.8
    wood, paint, mesh, rust = texels("picket_wood"), texels("picket_paint"), texels("chainlink"), texels("picket")
    # natural / stained wood: brown (R > G > B), no olive texel (G never above R)
    assert wood[:, 0].mean() > wood[:, 1].mean() + 20 > wood[:, 2].mean() + 40 and (wood[:, 1] > wood[:, 0] + 2).mean() < 0.01
    # painted pickets and the chain-link wire are neutral: their colour is the run tint
    for px in (paint, mesh):
        assert np.abs(px[:, 0] - px[:, 1]).mean() < 8 and np.abs(px[:, 1] - px[:, 2]).mean() < 10
    assert mesh.max() < 140                                      # review 0107 P1-r7-b: the mesh must not glow
    # the rust-red pickets: a peeled picket is weathered wood, not a neutral grey that a plot tint turns olive
    assert (rust[:, 0] > rust[:, 1] + 6).mean() > 0.97


def test_fence_styles_and_run_tints():
    for age in PL.FRONT_BY_AGE:
        assert sum(w for _, w in PL.FRONT_BY_AGE[age]) == pytest.approx(1.0)
        assert sum(w for _, w in PL.SIDE_BY_AGE[age]) == pytest.approx(1.0)
        assert {s for s, _ in PL.FRONT_BY_AGE[age]} <= set(PL.STYLES)
    old = dict(PL.FRONT_BY_AGE["old"])
    assert old["picket_wood"] + old["picket_paint"] >= old["picket"] and old["chainlink_galv"] > 0
    assert PL.STYLES["chainlink_galv"][0] == "chainlink" and PL.STYLES["picket_paint"][0] == "picket_paint"
    assert sum(w for _, w in PL.PICKET_PAINTS) == pytest.approx(1.0)
    assert all(0.0 <= c <= 2.0 for m, _ in PL.PICKET_PAINTS for c in m)
    kit = PL.Kit((0.8, 0.8, 0.8))
    assert PL.style_col(kit, "picket_wood", "k") is None and PL.style_col(kit, "chainlink_galv", "k") is None
    green = PL.style_col(kit, "chainlink", "k")
    assert green[3] == 0.0 and green[1] > green[0] * 2 and green[1] > green[2]          # the PVC coat of ADR 0114
    assert green[:3] == pytest.approx([0.4 * c for c in PK.CHAINLINK_GREEN])
    paints = {tuple(PL.style_col(kit, "picket_paint", f"plot{i}")) for i in range(200)}
    assert len(paints) == len(PL.PICKET_PAINTS)                                          # one paint per plot, all in use
    assert PL.style_col(kit, "picket_paint", ("plot3", "swing", 1.0)) == PL.style_col(kit, "picket_paint", "plot3")

    def run(style):
        k = PL.Kit((0.8, 0.8, 0.8))
        PL.fence_run(k, style, np.array([0.0, 0.0]), np.array([10.0, 0.0]), np.array([0.0, 1.0]), 1.3, lambda p: 0.0, "plot3")
        assert k.tint == PL.Kit((0.8, 0.8, 0.8)).tint                                    # the kit tint is restored
        return k
    k = run("picket_paint")
    C = np.concatenate(k.C)
    assert np.allclose(C, PL.style_col(PL.Kit((0.8, 0.8, 0.8)), "picket_paint", "plot3"))    # posts painted with the pickets
    k = run("chainlink")
    C = np.concatenate(k.C)
    assert (np.isclose(C[:, 0], 0.4) | np.isclose(C[:, 0], green[0])).all() and np.isclose(C[:, 0], green[0]).sum() == 8
    k = run("picket_wood")
    v0, v1 = PK.row("picket_wood")
    UV = np.concatenate(k.UV)
    assert np.isclose(UV[:, 1], v0).sum() >= 4 and np.isclose(UV[:, 1], v1).sum() >= 4 and np.allclose(np.concatenate(k.C)[:, :3], 0.4)
