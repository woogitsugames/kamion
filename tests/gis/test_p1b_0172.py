"""ADR 0172 (gate 3 P1 after s17): the 8.8 m signal mast with two arm heads at Rondo Putry, the sign cluster and the
lamp column on the splitter island of the EC access road. Unit tests need no raw data."""

from __future__ import annotations

import numpy as np
import pytest
from shapely.geometry import box

from roads import pipeline
from roads import standards as S
from streetscape import gate3_landmarks as G3
from streetscape import props as PP

REGION = "bialystok-industrial-c"


class _Pl:
    def __init__(self):
        self.items = []
        self.zsurf = lambda e, n: np.full(len(e), 140.0)
        self.zground = None

    def add(self, proto, p, yaw, z=None, src=""):
        z = 140.0 if z is None else z
        self.items.append((proto, [round(float(v), 2) for v in p], round(float(yaw), 4), z, src))
        return z


def _build(ov, **kw):
    pl, rep = _Pl(), {}
    G3.build(pl, None, {"nodes": []}, ov, (0, 0), {}, rep, **kw)
    return pl, rep["gate3_landmarks"]


def test_long_mast_prototype_reaches_its_arm_length():
    assert S.SIGNAL_MAST_ARMS == {"signal_mast": 6.0, "signal_mast_9m": 8.8}
    for name, arm in S.SIGNAL_MAST_ARMS.items():
        m, l1, col = PP.signal_pole(S.SIGNAL_MAST_H, arm)
        for mesh in (m, l1):
            V = np.concatenate([p["V"] for p in mesh.out()])
            assert V[:, 1].max() == pytest.approx(arm, abs=0.06)
            assert V[:, 2].max() == pytest.approx(S.SIGNAL_MAST_H - 0.4 + 0.11, abs=0.05)


def test_mast_with_two_arm_heads_and_pole_head():
    ov = [{"id": "m", "kind": "gate3_signal", "at_en": [10.0, 0.0], "travel_bearing_deg": 0, "arm_bearing_deg": 270,
           "arm_m": 8.8, "arm_heads_m": [5.5, 8.3]},
          {"id": "nopole", "kind": "gate3_signal", "at_en": [50.0, 0.0], "travel_bearing_deg": 0, "arm_bearing_deg": 270,
           "pole_head": False}]
    pl, g = _build(ov)
    assert [i[0] for i in pl.items] == ["signal_mast_9m", "signal_head_red", "signal_head_red", "signal_head_red",
                                        "signal_mast", "signal_head_red"]
    assert [i[1] for i in pl.items[1:4]] == [[4.5, 0.0], [1.7, 0.0], [10.0, -0.15]]
    assert pl.items[1][3] == pl.items[2][3] == pytest.approx(140.0 + S.SIGNAL_MAST_H - 1.25)
    assert pl.items[5][1] == [45.0, 0.0]                                 # default head 5.0 m out, no pole head
    assert g["signals"][0]["arm_heads_m"] == [5.5, 8.3] and g["stale"] == []


@pytest.mark.parametrize("extra", [{"arm_m": 7.0}, {"arm_m": 8.8, "arm_heads_m": [9.5]}, {"arm_heads_m": [0.5]},
                                   {"arm_heads_m": []}])
def test_bad_arm_is_stale_not_dropped_silently(extra):
    pl, g = _build([{"id": "m", "kind": "gate3_signal", "at_en": [0, 0], "travel_bearing_deg": 0,
                     "arm_bearing_deg": 270, **extra}])
    assert pl.items == [] and g["stale"][0].startswith("m: arm_m")


def test_new_faces_f10_ls_and_c12():
    lod0, lod1, col, im, (wm, hm), key, top = G3.assembly_mesh([{"face": "A-7"}, {"face": "C-12"}], "galv", 2.1)
    w, h = G3.FACE_DIM["A-7"][1:]
    assert top == pytest.approx(2.1 + 0.60 + 0.05 + h + 0.05)
    V = np.concatenate([p["V"] for p in lod0.out()])
    assert V[:, 0].max() == pytest.approx(w / 2, abs=1e-6)               # the triangle is the widest part
    f = G3.draw_face("F-10-ls", 378, 504)
    blue = np.asarray(f)[..., 0] < 80
    white = np.asarray(f).min(-1) > 200
    assert 0.55 < blue.mean() < 0.95 and 0.08 < white.mean() < 0.35
    # the arrow head of the left lane points left: white in the left 20 % at mid height, none on the right edge strip
    assert white[240:265, 40:90].any() and not white[240:265, 300:310].any()
    lod0, *_ = G3.assembly_mesh([{"face": "F-10-ls"}], "galv", 2.2)
    V = np.concatenate([p["V"] for p in lod0.out()])
    assert V[:, 2].max() == pytest.approx(2.2 + 1.20 + 0.05, abs=0.01)
    disc = G3._outline("disc", 0.6, 0.6)
    assert len(disc) == 16 and all(abs(np.hypot(x, z) - 0.3) < 1e-9 for x, z in disc)
    # clockwise in (x, z), as every other outline (the face looks along +y)
    area2 = sum(x0 * z1 - x1 * z0 for (x0, z0), (x1, z1) in zip(disc, disc[1:] + disc[:1]))
    tri = G3._outline("tri_up", 1, 1)
    assert area2 * sum(x0 * z1 - x1 * z0 for (x0, z0), (x1, z1) in zip(tri, tri[1:] + tri[:1])) > 0


def test_gate3_lamp_is_placed_or_reported():
    ov = [{"id": "ok", "kind": "gate3_lamp", "at_en": [50.0, 5.0], "proto": "lamp_10m", "arm_bearing_deg": 90},
          {"id": "road", "kind": "gate3_lamp", "at_en": [20.0, 20.0], "proto": "lamp_10m", "arm_bearing_deg": 90},
          {"id": "notlamp", "kind": "gate3_lamp", "at_en": [50.0, 9.0], "proto": "bench", "arm_bearing_deg": 90},
          {"id": "nokey", "kind": "gate3_lamp", "at_en": [50.0, 9.0]}]
    pl, g = _build(ov, carriage=box(0, 0, 40, 40))
    assert [i[0] for i in pl.items] == ["lamp_10m"] and pl.items[0][2] == pytest.approx(G3.PP_yaw(np.array([1.0, 0.0])), abs=1e-3)
    assert [x["id"] for x in g["lamps"]] == ["ok"] and sorted(s.split(":")[0] for s in g["stale"]) == ["nokey", "notlamp", "road"]


def test_overrides_of_0172_are_data():
    ov = {o["id"]: o for o in pipeline.load_overrides(REGION)}
    m = ov["putry-ring-s-approach-signal-mast"]
    assert m["arm_m"] == 8.8 and m["arm_heads_m"] == [5.5, 8.3] and m["pole_head"] is True
    assert m["arm_heads_m"][1] - m["arm_heads_m"][0] == pytest.approx(2.8)      # head shadows 2.8 m apart (orthophoto)
    isl = [ov[i] for i in ("ec-island-f10", "ec-island-a7-c12", "ec-island-d6", "ec-island-street-name")]
    assert all(o["kind"] == "gate3_sign" for o in isl) and ov["ec-island-lamp"]["kind"] == "gate3_lamp"
    assert [p["face"] for p in ov["ec-island-a7-c12"]["parts"]] == ["A-7", "C-12"]
    # the cluster stands within 3 m of the lamp column, as on the orthophoto
    lamp = np.array(ov["ec-island-lamp"]["at_en"])
    assert all(np.hypot(*(np.array(o["at_en"]) - lamp)) < 3.8 for o in isl)
