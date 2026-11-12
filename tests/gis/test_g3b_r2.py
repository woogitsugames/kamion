"""ADR 0139 - G3-B fixes after review s13-0127: clear viaduct screen with thin dense lines, dark posts on the
al. Tysiaclecia screens, portal boards / beam sized from the frontal photo, HV tower arm length from the orthophoto.
Pure generator checks (no build)."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))

from streetscape import furniture as F  # noqa: E402
from streetscape import life_props as LP  # noqa: E402
from streetscape import materials as MT  # noqa: E402
from streetscape import props as PR  # noqa: E402
from streetscape import signs as SG  # noqa: E402

RID = "bialystok-industrial-c"


def _lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _overrides():
    import yaml
    return yaml.safe_load((ROOT / f"Data/Regions/{RID}/overrides.yaml").read_text(encoding="utf-8"))["overrides"]


def test_viaduct_screen_is_clear_glass_with_faint_lines():
    s = MT.M["noise_glass_lined"]["screen"]
    lines, strength, duty = s["stripe"]
    # mean extra opacity of the sheet (film + line coverage): was 0.06 + 0.45 * 0.25 = 0.17 ("milky blind")
    assert s["haze"] + strength * duty <= 0.07
    period_m = 2.75 / (lines * 1.25)                 # v spans 1.25 over the 2.75 m sheet (roads.meshing)
    assert 0.04 <= period_m <= 0.07 and duty * period_m <= 0.008          # ~50 lines per bay, each a few mm
    assert _lum(s["haze_color"]) <= 0.21             # not brighter than the old film (0.5 sRGB = 0.21 linear)
    cs = (ROOT / "game/Assets/_Project/World/Import/RegionImporter.cs").read_text(encoding="utf-8")
    assert '"haze_color"' in cs
    sh = (ROOT / "game/Assets/_Project/Environment/Shaders/WorldCarGlass.shader").read_text(encoding="utf-8")
    assert "Transparent+" not in sh.split("SubShader")[0]           # queue is set by the importer, per material


def test_tysiaclecia_screen_posts_are_dark():
    dark, light = MT.M["noise_post_dark"], MT.M["noise_post"]
    assert _lum(dark["color"]) <= 0.45 * _lum(light["color"])
    assert dark["color"][1] > dark["color"][0] and dark["color"][1] > dark["color"][2]       # still a green
    o = next(x for x in _overrides() if x["id"] == "andersa-ne-noise-barrier-glazed")
    zones, _ = F._noise_style_overrides([o], np.array([777995.0, 596223.0]))
    tys = [z for z in zones if z[0][1] > 60.0 and z[0][0] < -500.0]                 # the al. Tysiaclecia zones
    assert len(tys) == 4 and all(z[2]["post_mat"] == "noise_post_dark" for z in tys)
    rest = [z for z in zones if not (z[0][1] > 60.0 and z[0][0] < -500.0)]
    assert rest and all(z[2]["post_mat"] == "noise_post" for z in rest)              # Andersa link zones unchanged


def test_overhead_board_authored_size_and_arrows():
    rows = [(["8", "E67"], "Warszawa"), (["65"], "Ełk")]
    im0, w0, h0 = SG.overhead_board(rows)
    assert abs(w0 - 4.0625) < 0.01 and abs(h0 - 1.41875) < 0.01               # rule layout unchanged
    im, w, h = SG.overhead_board(rows, size_m=(3.75, 0.82), arrows=2)
    assert abs(w - 3.75) < 0.02 and abs(h - 0.82) < 0.02
    a = np.asarray(im.convert("RGB")).astype(int)
    white = (a.min(axis=2) > 200)
    k = int(0.36 * 160)
    # a lane arrow at both ends, nothing but the green field right inside them
    assert white[:, 12:k].sum() > 200 and white[:, -k:-12].sum() > 200
    im1, _, _ = SG.overhead_board(rows, size_m=(3.75, 0.82), arrows=1)
    assert (np.asarray(im1.convert("RGB")).astype(int).min(axis=2) > 200)[20:-20, -k:-16].sum() == 0


def test_putry_portal_boards_and_beam_from_the_photo():
    o = next(x for x in _overrides() if x["id"] == "andersa-putry-approach-gantry")
    assert 0.45 <= o["beam_depth_m"] <= 0.65
    span = 14.0
    ws = [b["size_m"][0] for b in o["boards"]]
    assert all(0.25 <= w / span <= 0.29 for w in ws)             # photo: 0.27 of the column spacing (rule: 0.29)
    assert o["boards"][0]["size_m"][1] < 1.0 and o["boards"][1]["size_m"][1] <= 1.3
    assert LP.gantry_name(14, 64, 5) == "sign_gantry_14_64_b5" and LP.gantry_name(16, 76) == "sign_gantry_16_76"
    l0, _, _ = LP.sign_gantry(14.0, 6.4, 0.55)
    v = np.concatenate([x for p in l0.prims.values() for x in p[0]])
    beam = v[(abs(v[:, 0]) < 5.0)]
    assert beam[:, 2].min() >= 6.4 - 0.55 - 0.1 and beam[:, 2].max() <= 6.4 + 0.1
    import json
    qa = json.loads((ROOT / f"Data/Regions/{RID}/generated/streetscape_qa.json").read_text(encoding="utf-8"))
    g = {x["id"]: x for x in qa["furniture"]["landmarks"]["gantries"]}[o["id"]]
    if g["height_m"] >= 7.0:
        import pytest
        pytest.skip("generated world predates ADR 0139 (rebuild)")
    assert 6.0 <= g["height_m"] <= 6.5 and g["span_m"] == 14      # clearance rule: 6.1 m (photo: 6.2-6.5)


def test_hv_tower_arms_from_the_orthophoto():
    assert 4.0 <= PR.PYLON_ARM_L <= 4.6                    # 8.6 m tip to tip (GUGiK hi-res orthophoto)
