"""Deterministic per-sign wear, post finish, U-channel municipal posts, and +-1.5 deg tilt."""
from __future__ import annotations

import math

import numpy as np
import pytest

from roads import standards as S
from streetscape import furniture as F
from streetscape import materials as MAT
from streetscape import props as P


def test_sign_post_lod0_is_12_sided_with_single_material():
    m0, m1, _ = P.sign_post()
    p0 = m0.out()
    p1 = m1.out()
    assert len(p0) == 1 and len(p1) == 1
    assert p0[0]["mat"] == "sign_post_galv"
    assert MAT.M["sign_post_galv"]["shader"] == "Kamion/Furniture Post"
    # 12-sided shaft (24) + cap (12) + 12-sided collar (24) + collar cap (12) = 72 tris
    assert len(p0[0]["T"]) == 72


def test_sign_wear_params_deterministic_and_bounded():
    t1, pw1, fw1 = F.sign_wear_params((100.0, 200.0), "rule:test:1", road_cls="G", sidewalk=False)
    t2, pw2, fw2 = F.sign_wear_params((100.0, 200.0), "rule:test:1", road_cls="G", sidewalk=False)
    assert t1 == t2 and pw1 == pw2 and fw1 == fw2
    assert math.hypot(t1[0], t1[1]) <= F.SIGN_MAX_TILT_DEG + 1e-6
    assert all(0.0 <= x <= 1.0 for x in pw1 + fw1)
    # Municipal road (L/D) -> U-channel flag == 1.0; national/regional road -> 0.0
    _, pw_l, _ = F.sign_wear_params((100.0, 200.0), "rule:test:1", road_cls="L", sidewalk=False)
    _, pw_d, _ = F.sign_wear_params((100.0, 200.0), "rule:test:1", road_cls="D", sidewalk=False)
    _, pw_z, _ = F.sign_wear_params((100.0, 200.0), "rule:test:1", road_cls="Z", sidewalk=False)
    assert pw1[1] == 0.0 and pw_z[1] == 0.0
    assert pw_l[1] == 1.0 and pw_d[1] == 1.0


def test_sign_wear_population_has_painted_and_galv_and_stickers():
    paints, ages, stickers, tilts = [], [], [], []
    for i in range(100):
        t, pw, fw = F.sign_wear_params((10.0 * i, 5.0 * i), f"rule:pop:{i}", road_cls="G")
        tilts.append(math.hypot(t[0], t[1]))
        paints.append(pw[0])
        ages.append(fw[0])
        stickers.append(fw[2] > 0.52)
    assert 0.15 <= np.mean(paints) <= 0.45
    assert 0.15 <= np.mean(stickers) <= 0.50
    assert max(tilts) <= F.SIGN_MAX_TILT_DEG + 1e-6
    assert any(a > 0.7 for a in ages) and any(a < 0.35 for a in ages)


def test_sign_assembly_emits_tilt_pivot_and_wear_without_breaking_ground_coords():
    flat = lambda e, n: np.full_like(e, 140.0, dtype=float)
    pl = F.Placer(flat, flat)
    F.sign_assembly(pl, (50.0, 80.0), (0.0, 1.0), ["A-7", "T-1_150"], "unit:multi", road_cls="L")
    post, p_top, p_bot = pl.items
    assert post["p"] == "sign_post"
    assert p_top["e"] == post["e"] and p_top["n"] == post["n"]
    assert p_bot["e"] == post["e"] and p_bot["n"] == post["n"]
    assert post["wear"][1] == 1.0  # municipal road -> U-channel
    assert post["tilt"] == p_top["tilt"] == p_bot["tilt"]
    assert p_top["pivot_dy"] == pytest.approx(p_top["z"] - post["z"], abs=1e-3)
    assert p_bot["pivot_dy"] == pytest.approx(p_bot["z"] - post["z"], abs=1e-3)
