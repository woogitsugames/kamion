"""World C v3.4 (ADR 0023): multi-view lit impostors and HLOD edge walls, forest understorey, signs from OSM
`traffic_sign`, roundabout signing (C-9, exit boards, E-1 diagrams) and the sign audit of the start route."""

from __future__ import annotations

import json
import sys

import numpy as np
import pytest
from PIL import Image

from conftest import REGION_DIR, REPO, require_lfs

sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from streetscape import signs as SG            # noqa: E402
from streetscape import signs_route as SR      # noqa: E402

GEN = REGION_DIR / "generated"
VEG = REPO / "art-source" / "world" / "vegetation"
LUM = np.array([0.2126, 0.7152, 0.0722])


@pytest.fixture(scope="module")
def sqa():
    return json.loads((GEN / "streetscape_qa.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def meta():
    return json.loads((VEG / "trees_meta.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("value,codes", [
    ("PL:B-33[40]", ["B-33_40"]),
    ("PL:A-7;PL:B-33[50]", ["A-7", "B-33_50"]),
    ("PL:A-7,B-33[70]", ["A-7", "B-33_70"]),
    ("PL:B-1", ["B-1"]),
    ("DE:206", []),
    ("", []),
])
def test_parse_traffic_sign(value, codes):
    assert SR.parse_traffic_sign(value) == codes


def test_sign_faces_and_weathering():
    """Every face we draw is a square RGBA texture with transparent corners; ageing keeps the alpha, darkens the
    lower edge more than the top and is deterministic."""
    for code in sorted(SG.KNOWN) + ["B-33_70"]:
        shape, im = SG.face(code)
        a = np.asarray(im)
        assert a.shape == (512, 512, 4), code
        assert a[0, 0, 3] == 0 and a[256, 256, 3] == 255, code
        w1 = np.asarray(SG.weather(im, code)).astype(float)
        w2 = np.asarray(SG.weather(im, code)).astype(float)
        assert np.array_equal(w1, w2)
        assert np.array_equal(w1[..., 3], a[..., 3].astype(float))
        cov = a[..., 3] > 128
        ratio = (w1[..., :3] @ LUM + 1) / (a[..., :3].astype(float) @ LUM + 1)
        top, bot = ratio[:170][cov[:170]].mean(), ratio[340:][cov[340:]].mean()
        assert 0.80 < bot < top <= 1.0, (code, top, bot)


def test_roundabout_diagram_board():
    items = [(0.0, ["Augustów"], ["8"]), (-85.0, ["Lublin"], ["19"]), (90.0, ["Centrum"], [])]
    im, w, h = SG.roundabout_diagram(items)
    assert 1.5 < w < 3.5 and 1.2 < h < 3.0
    a = np.asarray(im)
    assert tuple(a[40, 40, :3]) == SG.GREEN                      # national road signed -> green field


def test_impostors_multi_view_and_lit(meta):
    """v3.4 impostors: IMP_NF views side by side + a normal / sky-visibility map; colour under the alpha is dilated
    (no dark or light fringe), so far coverage-preserving mips show leaf colour only."""
    for name, t in meta["trees"].items():
        n = t["impostor_views"]
        assert n >= 4, name
        require_lfs(VEG / f"impostor_{name}.png", VEG / f"impostor_{name}_n.png")
        alb = np.asarray(Image.open(VEG / f"impostor_{name}.png").convert("RGBA")).astype(float) / 255
        nrm = np.asarray(Image.open(VEG / f"impostor_{name}_n.png").convert("RGBA")).astype(float) / 255
        assert alb.shape[1] == round(alb.shape[0] * t["impostor_aspect"]) * n, name
        assert nrm.shape[0] * 2 == alb.shape[0] and nrm.shape[1] * 2 == alb.shape[1], name   # half-res map
        cov = alb[..., 3] > 0.5
        lum = alb[..., :3] @ LUM
        empty = alb[..., 3] < 0.02
        assert abs(lum[empty].mean() - lum[cov].mean()) < 0.08, (name, lum[empty].mean(), lum[cov].mean())
        vis = nrm[..., 2][cov[::2, ::2][: nrm.shape[0], : nrm.shape[1]]]
        assert 0.05 < np.median(vis) < 0.95, name
        # every view has coverage (the tree is in the frame)
        w = alb.shape[1] // n
        for k in range(n):
            assert cov[:, k * w:(k + 1) * w].mean() > 0.02, (name, k)


def test_hlod_edge_textures(meta):
    for mix, f in meta["forest_hlod"].items():
        e = f["edge"]
        assert (VEG / e["normal_png"]).exists(), mix
        require_lfs(VEG / e["png"])
        alb = np.asarray(Image.open(VEG / e["png"]).convert("RGBA")).astype(float) / 255
        cov = alb[..., 3] > 0.5
        # no floating specks above the stand silhouette: the top 12 % of the texture is (nearly) empty except the
        # crowns that continue below it
        h = alb.shape[0]
        top = cov[: int(h * 0.12)]
        assert top.mean() < 0.12, (mix, top.mean())


def test_manifest_edge_material_has_normal_ref():
    man = json.loads((GEN / "world_manifest.json").read_text(encoding="utf-8"))
    for mix in ("conifer", "mixed", "broadleaf"):
        m = man["materials"][f"forest_edge_{mix}"]
        assert m.get("normal_ref", "").endswith(f"forest_edge_{mix}_n.png"), mix
        assert (REPO / m["normal_ref"]).exists()


def test_forest_understorey(sqa):
    v = sqa["vegetation"]
    assert v["understorey"] > 5000, v.get("understorey")
    assert v["forest_hlod"]["cells"] >= 500


def test_route_signs_listed(sqa):
    """Sign audit of the start route: every roundabout on the route is announced by A-7 + C-12 that face the
    route driver, Putry and Bieżeństwa (ring >= 18 m) also by an E-1 diagram; the list is in streetscape_qa.json."""
    f = sqa["furniture"]
    rs = f["route_signs"]
    assert len(rs) >= 15
    assert all({"s_m", "code", "offset_m", "faces_route_driver", "src"} <= set(r) for r in rs)
    checks = f["route_checks"]
    assert len(checks) >= 2
    for c in checks:
        assert c["A-7"] and c["C-12"], c
    assert sum(1 for c in checks if c["E-1"]) >= 1, checks
    codes = {r["code"] for r in rs}
    assert any(c.startswith("B-33_") for c in codes), codes
    rb = f["roundabout_signs"]
    assert rb["c9_islands"] >= 4 and rb["exit_boards"] >= 4 and rb["diagrams"] >= 2, rb


def test_osm_signs_reported(sqa):
    o = sqa["furniture"]["osm_signs"]
    assert set(o) >= {"placed", "unknown", "skipped_far", "give_way_stop"}


@pytest.mark.parametrize("code", ["A-7", "B-33_70", "C-12", "C-9", "D-1", "D-6", "B-20"])
def test_plate_faces_the_driver(code):
    """The face of every plate shape points +y (toward the driver), the back -y (the r4 grey disc seen from behind)."""
    from streetscape import props as PP
    m, _, _ = PP.plate(code)
    for prim in m.out():
        V, T = prim["V"], prim["T"]
        n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        flat = np.abs(n[:, 1]) > 0.9 * np.linalg.norm(n, axis=1)
        if prim["mat"].startswith("sign_"):
            assert (n[:, 1] > 0).all(), code
        elif prim["mat"] == "plate_back":
            assert (n[flat][:, 1] < 0).all(), code


def test_board_faces_the_driver():
    from streetscape import props as PP
    m, _, _ = PP.board("E-2_x", 2.0, 1.0)
    for prim in m.out():
        V, T = prim["V"], prim["T"]
        n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        if prim["mat"].startswith("sign_"):
            assert (n[:, 1] > 0).all()
        elif prim["mat"] == "plate_back":
            assert (n[:, 1] < 0).all()
