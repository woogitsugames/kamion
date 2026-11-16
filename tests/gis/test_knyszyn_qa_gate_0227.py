"""ADR 0227 (rynek-s23): the Knyszyn-only generators must leave no trace in another region's QA.

stage.py calls the six `knyszyn_*_0227` builders for every region; before rynek-s23 each wrote a
`{"status": "skipped"}` entry into the report before its region gate, so every other tile's
streetscape_qa.json would gain six keys on its next rebuild.  vegetation.place likewise added an
empty `park_replacements` key.  Contract: other region -> no geometry and no report key.
"""
from types import SimpleNamespace

import numpy as np

from streetscape import knyszyn_church_0227 as KC
from streetscape import knyszyn_fountain_0227 as KF
from streetscape import knyszyn_market_0227 as KM
from streetscape import knyszyn_market_buildings_0227 as KMB
from streetscape import knyszyn_park_props_0227 as KP
from streetscape import knyszyn_townhall_0227 as KT
from streetscape import vegetation as VG
from test_house_greenery_0163 import _forest_src

ORIGIN = [761611, 612607]


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, *args, **kwargs):
        self.parts.append(args)


def _flat(e, n):
    return np.zeros_like(np.asarray(e, float))


def test_other_region_leaves_no_report_entry_or_geometry():
    report = {}
    buf = Buffer()
    for mod in (KC, KT, KMB):
        r = mod.build(buf, "bialystok-industrial-c", [], _flat, report)
        assert r["status"] == "skipped"
    for mod in (KP, KM, KF):
        r = mod.build(buf, "bialystok-industrial-c", ORIGIN, [], _flat, report)
        assert r["status"] == "skipped"
    assert report == {}
    assert not buf.parts


def test_knyszyn_still_reports_skip_reason():
    report = {}
    KF.build(Buffer(), KF.REGION, ORIGIN, [], _flat, report)
    assert report[KF.ASSET_ID]["status"] == "skipped" and "plate" in report[KF.ASSET_ID]["reason"]


def test_vegetation_without_park_replacement_adds_no_key():
    src = _forest_src("F1:0", [[0, 0], [100, 0], [100, 100], [0, 100]])
    hf = SimpleNamespace(x0=-10.0, y1=110.0)
    z = np.zeros((121, 121))
    report = {}
    VG.place(src, (0.0, 0.0), hf, z, np.zeros_like(z, dtype=bool), report, [])
    assert "park_replacements" not in report
