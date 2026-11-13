"""ADR 0189 - masonry gate kit (override `kind: masonry_gate`): brick wall with pillars and plaques, brick porch
under a concrete canopy, signs on masonry and on a lamp post - one prototype, one material, one atlas.

Opt-in: the reference region C has no such override, so its output cannot change (asserted on the data)."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

DOJ = REPO / "Data" / "Regions" / "bialystok-dojlidy"
C = REPO / "Data" / "Regions" / "bialystok-industrial-c"


def _ov(d):
    return (yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", [])


@pytest.fixture(scope="module")
def kit():
    from streetscape import masonry_gate as MG
    kits = MG.plan(_ov(DOJ))
    assert [k["id"] for k in kits] == ["zurawia-hospital-gate"]
    return kits[0], MG.build_kit(kits[0])


def test_region_c_has_no_masonry_gate():
    from streetscape import masonry_gate as MG
    assert MG.plan(_ov(C)) == [] and MG.fence_cut([]) == []


def test_one_material_and_budget(kit):
    k, (lod0, lod1, col, im, tris) = kit
    prims = lod0.out()
    assert [p["mat"] for p in prims] == [f"sign_{k['key']}"]            # one draw on every tier
    assert sum(len(p["T"]) for p in prims) == tris <= 800
    assert im.size == (1024, 1024)
    uv = prims[0]["UV"]
    assert uv.min() >= 0.0 and uv.max() <= 1.0                           # no reliance on texture wrap
    assert {p["mat"] for p in col.out()} <= {"collision_building", "collision_steel"}


def test_faces_look_outward(kit):
    """Every triangle of a vertical brick / board face must look away from the solid it belongs to: checked on the
    whole mesh as `no degenerate triangles` and on the sign faces as `normal toward the street` (frame +a)."""
    k, (lod0, *_rest) = kit
    p = lod0.out()[0]
    V, T = p["V"], p["T"]
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    assert (np.linalg.norm(n, axis=1) > 1e-9).all()
    fr = k["frame"]
    stop = next(s for s in k["spec"]["faces"] if s["face"] == "B-20")
    c = fr.en(stop["at_la"]) - fr.o
    d = np.hypot(V[:, 0] - c[0], V[:, 1] - c[1])
    near = np.isin(T, np.where((d < 0.45) & (abs(V[:, 2] - stop["z_m"]) < 0.45))[0]).all(axis=1)
    front = n[near] @ np.array([fr.out[0], fr.out[1], 0.0])
    assert near.sum() >= 12 and (front > 0).sum() >= 6 and (front < 0).sum() >= 6     # face + its grey back


def test_signs_of_the_photo(kit):
    k, _ = kit
    spec = k["spec"]
    faces = [s["face"] for s in spec["faces"]] + [s["face"] for p in spec["posts"] for s in p["faces"]]
    assert sorted(faces) == ["B-20", "B-33_20", "C-2"]                  # read off frame P11-129, not the manifest
    post = spec["posts"][0]["faces"]
    assert post[0]["face"] == "C-2" and post[0]["z_m"] > post[1]["z_m"]  # C-2 above the speed limit


def test_c2_is_the_bent_arrow():
    """C-2 = turn right AFTER the sign: the arrow enters from below and leaves to the right (the stem is in the left
    half, the head in the upper right); a straight horizontal arrow would be C-1."""
    from streetscape import masonry_gate as MG
    a = np.asarray(MG.c2_face().convert("RGB")).astype(int)
    white = (a.min(axis=2) > 200)
    n = a.shape[0]
    assert white[int(n * 0.70), int(n * 0.36)]                           # stem, lower left
    assert white[int(n * 0.34), int(n * 0.70)]                           # head, upper right
    assert not white[int(n * 0.70), int(n * 0.70)]                       # nothing lower right
    assert not white[int(n * 0.34), int(n * 0.20)]                       # no tail to the left of the stem


def test_no_real_names_on_plaques():
    from streetscape import masonry_gate as MG
    words = " ".join(" ".join(t) for t in MG.PLAQUE_TEXTS).lower()
    for banned in ("uniwersyt", "klinik", "białyst", "żurawia", "usk", "umb"):
        assert banned not in words


def test_fence_cut_covers_the_wall(kit):
    from shapely.geometry import Point
    from streetscape import masonry_gate as MG
    k, _ = kit
    cut = MG.fence_cut([k])
    for ln in k["wall_lines"]:
        for p in ln:
            assert any(c.contains(Point(*p)) for c in cut)
    # the wall ends at the end of the OSM barrier way (local 328.5 805.4), within 1.5 m
    assert math.hypot(*(k["wall_lines"][0][0] - np.array([328.5, 805.4]))) < 1.5


def test_brick_is_grey_sand_lime_not_red():
    from streetscape import masonry_gate as MG
    b = MG.brick_band()
    m = b.reshape(-1, 3).mean(0)
    assert abs(m[0] - m[2]) < 0.08 and 0.40 < m.mean() < 0.72            # near neutral, mid albedo (sRGB)
