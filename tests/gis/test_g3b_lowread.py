"""ADR 0127 - legibility of the G3-B landmarks on Low: lattice sign portal at distance (LOD1), boards standing on the
beam, HV tower silhouette + conductors on its arms, noise-screen posts and sheet. Pure generator checks (no build)."""
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))

from roads import build_world as BW  # noqa: E402
from roads import meshing as RM  # noqa: E402
from streetscape import furniture as F  # noqa: E402
from streetscape import landmarks as LM  # noqa: E402
from streetscape import life_props as LP  # noqa: E402
from streetscape import materials as MT  # noqa: E402
from streetscape import props as PR  # noqa: E402


def _tris(mesh):
    return sum(len(t) for p in mesh.prims.values() for t in p[1])


def _verts(mesh):
    return np.concatenate([v for p in mesh.prims.values() for v in p[0]])


def _lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def test_gantry_lod1_is_a_lattice_not_a_box():
    l0, l1, col = LP.sign_gantry(16.0, 7.6)
    assert col is None
    t0, t1 = _tris(l0), _tris(l1)
    # two boxes were 24 triangles; a lattice of 3-sided members is a few hundred, and stays under LOD0
    assert 300 <= t1 <= 900 and t1 < t0 <= 3000, (t0, t1)
    # no LOD1 member is thicker than 2 x the chord radius: nothing spans the 0.8 m beam depth as a solid face
    v = _verts(l1)
    assert abs(v[:, 0]).max() <= 8.0 + 0.3 + LP.GANTRY_CHORD_R[1] + 1e-6
    assert LP.GANTRY_CHORD_R[1] >= LP.GANTRY_CHORD_R[0] and LP.GANTRY_LACE_R[1] >= LP.GANTRY_LACE_R[0]
    assert LP.GANTRY_CHORD_R[1] <= 0.10          # still a tube, not a beam


def test_cantilever_lod1_is_a_lattice():
    l0, l1, _ = LP.sign_cantilever(9.0, 7.6)
    assert 150 <= _tris(l1) < _tris(l0)


def test_gantry_and_overhead_boards_stay_visible_on_low():
    # Low lodBias 0.5: portal lattice LOD0 to 50 m, LOD1 to 400 m; overhead boards to 400 m (was 25 / 125 m)
    assert BW.instance_ends("sign_gantry_16_76", 2)[0] == [100.0, 800.0]
    assert BW.instance_ends("sign_cantilever_R9_76", 2)[0] == [100.0, 800.0]
    assert BW.instance_ends("board_OB_12345678", 2)[0] == [50.0, 800.0]
    assert BW.instance_ends("sign_post", 2)[0] == [50.0, 250.0]           # ordinary signs unchanged
    cs = (ROOT / "game/Assets/_Project/World/Import/InstanceImporter.cs").read_text(encoding="utf-8")
    assert re.search(r'StartsWith\("sign_gantry_"\).*new\[\] \{ 100f, 800f \}', cs)
    assert re.search(r'StartsWith\("board_OB_"\).*new\[\] \{ 50f, 800f \}', cs)
    assert cs.index('"sign_gantry_"') < cs.index('proto.StartsWith("sign_")')   # specific prefix first


def test_boards_stand_on_the_portal_beam():
    assert 0.1 <= LM.BOARD_ABOVE_BEAM_M <= 0.5
    src = (ROOT / "tools/worldgen/streetscape/landmarks.py").read_text(encoding="utf-8")
    assert "z + H + top_off - hm / 2" in src


def test_overhead_board_back_is_plain():
    m, _, _ = PR.board("OB_test", 5.0, 2.2)
    assert "board_back" in m.prims and "plate_back" not in m.prims
    m, _, _ = PR.board("E-2_x", 2.0, 1.0)
    assert "plate_back" in m.prims
    assert "texture" not in MT.M["board_back"]


def test_pylon_silhouette_and_lods():
    l0, l1, col = PR.pylon()
    v0, v1 = _verts(l0), _verts(l1)
    for v in (v0, v1):
        assert 31.9 <= v[:, 2].max() <= 32.2
        assert PR.PYLON_ARM_L <= abs(v[:, 0]).max() <= PR.PYLON_ARM_L + 0.2        # arms along local x
        assert abs(v[:, 1]).max() <= PR.pylon_half_width(0.0) + 0.2                # slender across
    assert PR.pylon_half_width(0.0) <= 2.6 and PR.pylon_half_width(20.0) <= 0.8
    assert len(PR.PYLON_ARM_Z) == 3
    assert l1 is not l0 and _tris(l1) < _tris(l0) <= 2500 and _tris(l1) <= 900, (_tris(l0), _tris(l1))
    assert col is not None
    c = MT.M["pylon_steel"]
    assert _lum(c["color"]) <= 0.15 and c["metal"] <= 0.3         # dark and dull against the sky


def test_hv_conductors_hang_from_the_tower_arms():
    src = (ROOT / "tools/worldgen/streetscape/furniture.py").read_text(encoding="utf-8")
    assert "PR.PYLON_ARM_L" in src and "PR.PYLON_INSULATOR_M" in src and "hang.append((0.0, 32.0))" in src
    assert min(PR.PYLON_ARM_Z) - PR.PYLON_INSULATOR_M > 15.0      # lowest conductor well above the road gauge


def test_gantry_steel_is_not_a_sky_mirror():
    c = MT.M["gantry_steel"]
    assert c["metal"] <= 0.4 and 0.15 <= _lum(c["color"]) <= 0.32


def test_noise_screen_posts_and_sheet():
    assert F.NOISE_POST_W >= 0.20
    assert RM.SCREEN_POST_W >= 0.20 and RM.SCREEN_POST_M <= 2.5
    for k in ("noise_glass", "noise_glass_lined"):
        m = MT.M[k]
        assert m["shader"] == "car_glass" and m["alpha"] <= 0.2 and m["blend"]
        assert 0.5 <= m["screen"]["horizon_sky"] <= 1.0 and 0.0 < m["screen"]["haze"] <= 0.2
    lines, strength, duty = MT.M["noise_glass_lined"]["screen"]["stripe"]
    assert 15 <= lines <= 30 and 0 < strength <= 0.6 and 0 < duty < 0.5
    sh = (ROOT / "game/Assets/_Project/Environment/Shaders/WorldCarGlass.shader").read_text(encoding="utf-8")
    assert "shader_feature_local_fragment _SCREEN_SHEET" in sh       # car panes compile without the screen code


def _overrides():
    import yaml
    return yaml.safe_load((ROOT / "Data/Regions/bialystok-industrial-c/overrides.yaml").read_text(encoding="utf-8"))


def _find(node, oid):
    if isinstance(node, dict):
        if node.get("id") == oid:
            return node
        node = list(node.values())
    if isinstance(node, list):
        for v in node:
            r = _find(v, oid)
            if r:
                return r
    return None


def test_portal_span_from_the_orthophoto():
    o = _find(_overrides(), "andersa-putry-approach-gantry")
    a, b = (np.asarray(v, float) for v in o["columns_en"])
    assert 13.0 <= np.hypot(*(b - a)) <= 14.5                    # beam 14.0 m on the hi-res orthophoto (rule: 16 m)
    assert np.hypot(*((a + b) / 2 - [-261.0, -208.0])) <= 3.0    # ADR 0125 position kept
    qa_f = ROOT / "Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json"
    import json
    qa = json.loads(qa_f.read_text(encoding="utf-8"))
    g = {x["id"]: x for x in qa["furniture"]["landmarks"]["gantries"]}[o["id"]]
    if g["span_m"] == 16:
        import pytest
        pytest.skip("generated world predates ADR 0127 (rebuild)")
    assert g["span_m"] in (13, 14) and 6.0 <= g["height_m"] <= 7.5


def test_tysiaclecia_barrier_is_a_tall_glazed_screen():
    o = _find(_overrides(), "andersa-ne-noise-barrier-glazed")
    tall = [z for z in o["zones"] if z.get("height_m")]
    assert len(tall) == 2 and all(z["style"] == "glazed" and 5.0 <= z["height_m"] <= 5.5 for z in tall)
    zones, _ = F._noise_style_overrides([o], np.array([777995.0, 596223.0]))
    assert sum(1 for z in zones if z[2].get("height_m") == 5.2) == 2
    # the set-back barrier beside camera 1801374 (local E,N ~ -530, 75) falls inside a tall glazed zone
    assert any(np.hypot(*(np.array([-530.0, 75.0]) - z[0])) <= z[1] and z[2].get("height_m") for z in zones)
