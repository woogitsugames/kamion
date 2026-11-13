"""ADR 0186 - greenery of the frame P11-063 (Mickiewicza / Kuronia, region bialystok-dojlidy): the `thicket` shrub
mass, traced tree stems (`points_en`), the node override `signalized` and the camera of the frame.

Everything is opt-in: region C has no such data, so its output cannot change (asserted on the data)."""
import json
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


class _Buf:
    def __init__(self):
        self.tris, self.V = {}, []

    def add(self, layer, mat, V, UV, T, src="", **kw):
        self.tris[mat] = self.tris.get(mat, 0) + len(T)
        self.V.append(np.asarray(V, float))


def test_region_c_uses_none_of_it():
    ov = _ov(C)
    assert not [o["id"] for o in ov if o.get("kind") == "tree_groups" and o.get("points_en")]
    assert not [o["id"] for o in ov if "signalized" in (o.get("set") or {})]
    assert not [o["id"] for o in ov if o.get("kind") == "plantings"
                and any(b.get("plant") == "thicket" for b in o.get("beds", []))]


def test_thicket_is_a_closed_mass_on_the_ground():
    from shapely.geometry import Polygon
    from streetscape import plantings as PT
    S = PT.SPECIES["thicket"]
    assert S["gap_p"] == 0.0                     # no missing plants: nothing shows through
    assert max(S["plant"]) <= 1.9                # bushes closer than 2 m (review s19 0179: gaps between the balls)
    buf = _Buf()
    st = {}
    PT.hedge_mass(buf, Polygon([(0, 0), (15, 0), (15, 4.4), (0, 4.4)]), lambda x, y: np.zeros(len(np.atleast_1d(x))),
                  ("t", 0, 0), h=2.8, plant="thicket", stats=st)
    assert set(buf.tris) == {"hedge_hornbeam", "hedge_shell_hornbeam", "hedge_sprig_hornbeam"}      # no new material
    V = np.vstack(buf.V)
    assert V[:, 2].min() < 0.0                   # the core goes into the ground, no floating foot
    assert 2.6 < V[:, 2].max() < 3.8
    assert st["tris"] < 3500                     # 15 m of thicket; the 2 x 8 shrub instances it replaces: ~6 000


def test_tree_points_keep_their_place_and_height():
    from streetscape import vegetation as VG
    ov = [{"id": "c", "kind": "tree_groups", "points_en": [[1.0, 2.0, 10.5], [3.0, 4.0]], "height_m": [9.0, 11.0],
           "species": {"maple": 1.0}}]
    (P, hs, sp, hr, key), = VG._tree_point_overrides(ov)
    assert P.tolist() == [[1.0, 2.0], [3.0, 4.0]] and hs == [10.5, None] and hr == (9.0, 11.0)
    assert key == "override:c:points"
    assert VG._tree_group_overrides(ov, np.zeros(2)) == []        # a points-only override draws no line clumps
    with pytest.raises(ValueError):
        VG._tree_point_overrides([{"id": "x", "kind": "tree_groups", "points_en": [[0, 0]], "height_m": [5, 2]}])


def test_dojlidy_data_and_report():
    ov = {o["id"]: o for o in _ov(DOJ)}
    band = ov["mickiewicza-kuronia-shrub-band"]
    assert band["kind"] == "plantings" and len(band["beds"]) >= 5
    assert all(b["plant"] == "thicket" and 2.0 <= b["height_m"] <= 3.3 for b in band["beds"])
    trees = ov["mickiewicza-kuronia-corner-trees"]
    assert 3 <= len(trees["points_en"]) <= 4 and all(9.0 <= p[2] <= 11.0 for p in trees["points_en"])
    assert ov["mickiewicza-u-turn-not-signalised"]["set"] == {"signalized": False}
    for o in ov.values():
        assert o.get("reason") and o.get("confidence"), o["id"]
    rep = json.loads((DOJ / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
    tg = rep["vegetation"]["tree_groups"]
    assert tg["points"] == len(trees["points_en"]) and not tg["points_refused"]
    assert rep["plantings"]["hedges"] == len(band["beds"]) and not rep["plantings"]["stale"]
    man = json.loads((DOJ / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    assert not man.get("overrides_stale")


def test_camera_063_looks_at_the_frame():
    cams = json.loads((DOJ / "control_cameras_photo.authored.json").read_text(encoding="utf-8"))["cameras"]
    cam = next(c for c in cams if c["id"] == "photo_P11-063")
    e, n = cam["pos_en"]
    f = 1255.0                                   # px at 1600 px width, hFOV 65 deg

    def x_of(pe, pn):
        d = (math.degrees(math.atan2(pe - e, pn - n)) - cam["heading_deg"] + 180) % 360 - 180
        return 800 + f * math.tan(math.radians(d))
    # objects of the photo (x in the 1600 px frame) against the orthophoto / BDOT10k positions, +-1 deg = 22 px
    for (pe, pn), x in (((47.8, 337.4), 1160), ((-15.3, 371.0), 1102), ((-35.5, 368.0), 1492), ((-13.0, 372.5), 1037)):
        assert abs(x_of(pe, pn) - x) < 22, (pe, pn, x_of(pe, pn))
    assert x_of(-35.5, 368.0) > 1400              # the signal mast stands at the right edge of the frame
