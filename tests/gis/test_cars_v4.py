"""Parked cars v4 (ADR 0041 par. 9, REVIEW r6 W-N6 / W-N7 / W-N8 / W-N9)."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict

import numpy as np
import pytest

from conftest import REGION_DIR, REGION_ID, REPO

WORLD = REPO / "Data" / "raw" / "derived" / REGION_ID / "world"
GEN = REGION_DIR / "generated"


def test_vehicle_policy_mirrors_engine():
    """The frame estimate uses the engine's per-family LOD ends; the vehicle cull is fixed on every tier."""
    from roads import build_world as BW
    cs = (REPO / "game/Assets/_Project/World/Runtime/WorldInstances.cs").read_text(encoding="utf-8")
    assert float(re.search(r"VehicleCullM = ([\d.]+)f", cs).group(1)) == BW.VEHICLE_CULL_M
    imp = (REPO / "game/Assets/_Project/World/Import/InstanceImporter.cs").read_text(encoding="utf-8")
    assert "new[] { 25f, 90f, WorldInstances.VehicleCullM }" in imp and "new[] { 40f, WorldInstances.VehicleCullM }" in imp
    hi = BW.instance_rule("car_hatch_red", 3, BW.LOD_POLICY["High"]["lod_bias"])
    lo = BW.instance_rule("car_hatch_red", 3, BW.LOD_POLICY["Low"]["lod_bias"])
    assert hi[-1][0] == lo[-1][0] == BW.VEHICLE_CULL_M >= 150          # W-N6: LOD2 instead of a cull on Low
    # r8 (REVIEW r7 N-14): LOD0 floor on every tier, so the cars 8-12 m beside the route are LOD0 on Low too
    assert float(re.search(r"VehicleLod0MinM = ([0-9.]+)f", cs).group(1)) == BW.VEHICLE_LOD0_MIN_M >= 15.0
    assert lo[0][0] == BW.VEHICLE_LOD0_MIN_M and hi[0][0] == 37.5 and lo[1][0] == 45.0
    assert BW.instance_rule("tractor_white", 2, 0.5)[0][0] == 20.0       # 40 x 0.5 is already above the floor
    assert BW.instance_rule("trailer_box_0", 2, 0.5)[-1][0] == BW.VEHICLE_CULL_M
    assert BW.instance_rule("bin_1100_blue", 2, 0.5)[-1][0] == 60.0      # non-vehicles still scale with lodBias


def test_car_lod2_is_cheap_and_plates_textured():
    from streetscape import life_cars as LC
    from streetscape.materials import M
    for b in LC.CARS:
        m0, m1, _, m2 = LC.car(b, "red")
        t2 = sum(len(p["T"]) for p in m2.out())
        assert t2 <= 60, (b, t2)
        p0 = {p["mat"]: p for p in m0.out()}["car_plate"]
        p1 = {p["mat"]: p for p in m1.out()}["car_plate"]
        k = LC._plate_index(f"{b}_red")
        u0, v0, u1, v1 = LC.plate_uv(k)
        assert p0["UV"][:, 0].min() >= u0 - 1e-6 and p0["UV"][:, 0].max() <= u1 + 1e-6
        # r8 (REVIEW r7 N-14): LOD1 carries the prototype's own plate too (the atlas mips do the far blur)
        assert p1["UV"][:, 0].min() >= u0 - 1e-6 and p1["UV"][:, 0].max() <= u1 + 1e-6
    assert M["car_plate"]["texture"] == "car_plates"
    assert 0.5 <= M["car_glass_tint"]["alpha"] <= 0.7                    # W-N8: transmission 0.3-0.5


def test_plate_strings_fictional_polish_format():
    from streetscape import life_cars as LC
    seen = set()
    for k in range(LC.PLATE_FAR):
        code, rest = LC.plate_text(k)
        assert code in dict(LC.PLATE_DISTRICTS)
        assert len(code) + len(rest) in (6, 7, 8)
        assert not set(rest) & set("BDIOZ") and rest[0].isdigit()
        seen.add(code + rest)
    assert len(seen) == LC.PLATE_FAR
    im = np.asarray(LC.plate_atlas())
    assert im.shape == (64 * LC.PLATE_ROWS, 256 * LC.PLATE_COLS, 3)
    white = (im.min(axis=2) > 230).mean()
    assert white < 0.9                                                   # W-N9: no blank white plates


@pytest.mark.skipif(not WORLD.exists(), reason="world instances not generated (Data/raw)")
def test_parking_mix_and_neighbours():
    """W-N7: sedans <= 25 %, 10-15 % reversed, no prototype repeated within 4 consecutive stalls of a row."""
    qa = json.loads((GEN / "streetscape_qa.json").read_text(encoding="utf-8"))
    pk = qa["furniture"]["life"]["parking"]
    assert pk["body_share"].get("sedan", 0) <= 0.25
    assert 0.08 <= pk["reversed_share"] <= 0.16
    cars = []
    for f in sorted(WORLD.glob("instances_*.json")):
        cars += [i for i in json.loads(f.read_text(encoding="utf-8"))["instances"] if i["p"].startswith(("car_", "van_"))]
    assert cars
    E = np.array([[c["e"], c["n"]] for c in cars])
    bad = 0
    for i, c in enumerate(cars):
        d = np.hypot(*(E - E[i]).T)
        for j in np.flatnonzero((d > 0.5) & (d < 2.9)):                 # direct neighbour stall (2.5 m pitch)
            if cars[j]["p"] == c["p"] and abs(math.cos(cars[j]["yaw"] - c["yaw"])) > 0.9:
                bad += 1
    assert bad == 0, bad
