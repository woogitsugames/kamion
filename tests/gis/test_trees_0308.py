"""ADR 0308: lobed broadleaf crowns, branchlet atlases, poplar, garden trees as library instances on High.

Blender-free: make_trees.py is read through ast (it imports bpy); the baked library is checked through trees_meta.json.
"""
import ast
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools/worldgen"))
from streetscape import leaf_sprays as LS      # noqa: E402
from streetscape import plantings as PT        # noqa: E402
from streetscape import vegetation as VG       # noqa: E402

SCRIPT = REPO / "tools/blender/world/make_trees.py"
VEG = REPO / "art-source/world/vegetation"


def isolated():
    tree = ast.parse(SCRIPT.read_text(encoding="utf8"))
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in ("spray_uv", "crown_radius"))
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("CROWN", "ADDED_0308"))]
    assert len(keep) == 4
    ns = {"math": math, "random": random}
    exec(compile(ast.fix_missing_locations(ast.Module(body=keep, type_ignores=[])), str(SCRIPT), "exec"), ns)
    return ns


def test_spray_cell_is_a_branchlet_not_a_disc():
    a = LS.spray("linden", 5, 256)
    b = LS.spray("linden", 5, 256)
    assert a.shape == (256, 256, 4) and a.dtype == np.uint8 and np.array_equal(a, b), "deterministic"
    al = a[..., 3] > 127
    assert 0.18 < al.mean() < 0.70
    # leaves are never cut by the cell edge (cells share an atlas: no bleed, no straight edges)
    assert not al[:3].any() and not al[-2:].any() and not al[:, :3].any() and not al[:, -3:].any()
    # the twig base is at the bottom centre: the lowest covered rows sit near the middle column
    rows = np.where(al.any(axis=1))[0]
    low = np.where(al[rows.max() - 3:rows.max() + 1].any(axis=0))[0]
    assert abs(low.mean() / 256 - 0.5) < 0.12
    # not a round pompon: the old card filled the disc around its centre; a branchlet leaves bays of sky in it
    ys, xs = np.nonzero(al)
    rad = np.hypot(ys - ys.mean(), xs - xs.mean())
    assert al.sum() / (math.pi * np.percentile(rad, 98) ** 2) < 0.66
    # no black fringe under transparent texels (mips of the alpha-tested card)
    assert a[..., :3][~al].reshape(-1, 3).mean(axis=0).min() > 20


@pytest.mark.parametrize("species", LS.SPECIES)
def test_committed_atlas_matches_the_generator_layout(species):
    from PIL import Image
    im = np.asarray(Image.open(VEG / f"leaves_{species}.png").convert("RGBA"))
    assert im.shape == (LS.CELL * LS.GRID, LS.CELL * LS.GRID, 4)
    cov = [LS.coverage(im[r * LS.CELL:(r + 1) * LS.CELL, c * LS.CELL:(c + 1) * LS.CELL]) for r in range(2) for c in range(2)]
    assert min(cov) > 0.12 and max(cov) < 0.70, cov
    assert len({round(c, 3) for c in cov}) == 4, "four different branchlets"


def test_atlas_uvs_agree_between_generator_and_tree_builder():
    ns = isolated()
    for cell in range(4):
        for mirror in (False, True):
            assert ns["spray_uv"](cell, mirror) == LS.cell_uv(cell, mirror)
    (u0, v0), (u1, _), (_, v1), _ = LS.cell_uv(0)
    assert (u0, u1) == (0.0, 0.5) and (v0, v1) == (0.5, 1.0), "cell 0 = top-left of the image, v = 0 side is the twig base"


def test_crown_envelopes_are_closed_and_species_specific():
    ns = isolated()
    C, radius = ns["CROWN"], ns["crown_radius"]
    assert set(C) == {"linden", "maple", "birch", "alder", "poplar"} and ns["ADDED_0308"] == ("poplar",)
    ph = [0.3, 1.1, 2.0, 4.0]
    for sp, P in C.items():
        prof = [np.mean([radius(P, u, a, ph) for a in np.linspace(0, 6.28, 24)]) for u in np.linspace(0, 1, 21)]
        assert prof[-1] < 0.02 and prof[0] > 0.3 * max(prof), sp      # closed top, broad base (no ball on a stick)
        assert abs(max(prof) - P["rmax"]) < 0.06, sp
        ring = [radius(P, P["peak"], a, ph) for a in np.linspace(0, 6.28, 48)]
        assert max(ring) / min(ring) > 1.25, "lobed outline, not a body of revolution"
    assert C["maple"]["rmax"] > C["linden"]["rmax"] > C["alder"]["rmax"] > C["poplar"]["rmax"]
    assert C["birch"]["hang"] > 0.3 and all(P["hang"] == 0 for s, P in C.items() if s != "birch")
    assert PT.LIB_CROWN_R_PER_H == {s: C[s]["rmax"] for s in ("linden", "maple", "birch")}


def test_library_meta_budget():
    tr = json.loads((VEG / "trees_meta.json").read_text(encoding="utf-8"))["trees"]
    for sp, nv in (("linden", 3), ("maple", 3), ("birch", 3), ("alder", 3), ("poplar", 2)):
        for v in range(nv):
            t = tr[f"tree_{sp}_{v}"]
            assert t["tris_lod0"] <= 3800, (sp, v, t)           # pre-0308 library: 2450-4130
            assert t["tris_lod1"] <= 0.5 * t["tris_lod0"] and t["tris_lod2"] == 2, (sp, v, t)
            assert (VEG / f"impostor_tree_{sp}_{v}.png").exists()
    assert "tree_poplar_2" not in tr
    assert max(tr[f"tree_pine_{v}"]["tris_lod0"] for v in range(3)) <= 2800


def test_poplar_is_placeable():
    assert VG.HEIGHT["poplar"][0] >= 16 and VG.NVAR["poplar"] == 2
    assert "poplar" not in VG.SPECIES, "not in the BDOT forest mixes: rows / overrides only"


def test_garden_tree_becomes_a_library_instance_on_high():
    t = {"p": (10.0, -4.0), "r": 3.3, "plot": "p1"}
    a = PT.library_instance(t, "linden", 12.0, 151.2, "k1")
    assert a["p"] == "tree_linden" and a["tier"] == "high" and a["src"] == "plot:p1:g7-lib" and a["v"] in (0, 1, 2)
    assert a["h"] == pytest.approx(3.3 / 0.33, abs=0.06) and (a["e"], a["n"], a["z"]) == (10.0, -4.0, 151.2)
    assert PT.library_instance(t, "linden", 12.0, 151.2, "k1") == a, "deterministic"
    assert PT.library_instance(t, "ash", 12.0, 0.0, "k")["p"] == "tree_linden"
    assert PT.library_instance(t, "chestnut", 12.0, 0.0, "k")["p"] == "tree_maple"
    assert PT.library_instance(t, "fruit", 5.0, 0.0, "k") is None
    assert PT.library_instance({**t, "r": 1.2}, "birch", 6.0, 0.0, "k") is None, "small crowns stay kit trees"
    # height follows the orthophoto crown but stays within 0.8-1.3 of the kit height and under the species ceiling
    assert PT.library_instance({**t, "r": 9.0}, "birch", 14.0, 0.0, "k")["h"] == pytest.approx(18.2)
    assert PT.library_instance({**t, "r": 9.0}, "maple", 21.0, 0.0, "k")["h"] == 22.0
    assert PT.library_instance({**t, "r": 1.7}, "maple", 12.0, 0.0, "k")["h"] == pytest.approx(9.6)
