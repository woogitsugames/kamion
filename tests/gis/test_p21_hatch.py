"""P-21 hatching is analytic: every stripe is one quad, stripes of a field are parallel (ADR 0100, REVIEW s10-0095 P0-1).

The ADR 0093/0095 hatching triangulated border + stripes as one polygon and draped only the triangle corners, so the
paint sank under the crowned asphalt and rendered as fragments, "Z" shapes and empty frames.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import p21_hatch as H  # noqa: E402
from roads import standards as S  # noqa: E402

REGION = ROOT / "Data" / "Regions" / "bialystok-industrial-c"


def _zones():
    ov = yaml.safe_load(open(REGION / "overrides.yaml", encoding="utf-8"))
    ov = ov.get("overrides", ov)
    return [o for o in ov if o.get("kind") == "painted_zone"]


def _dir(q):
    """Direction (deg, mod 180) of the long sides of quad q, and their misalignment (deg)."""
    a, b = q[1] - q[0], q[2] - q[3]
    da = math.degrees(math.atan2(a[1], a[0])) % 180.0
    db = math.degrees(math.atan2(b[1], b[0])) % 180.0
    d = abs(da - db)
    return da, min(d, 180.0 - d)


def _convex(q):
    cr = []
    for i in range(4):
        u, v = q[(i + 1) % 4] - q[i], q[(i + 2) % 4] - q[(i + 1) % 4]
        cr.append(u[0] * v[1] - u[1] * v[0])
    return all(c > -1e-9 for c in cr) or all(c < 1e-9 for c in cr)


def _check(o):
    g = H.hatch(o)
    pg = g["polygon"]
    assert g["stripes"], f"{o['id']}: no stripe"
    for q in g["stripes"] + g["border"]:
        assert np.asarray(q).shape == (4, 2), f"{o['id']}: not a quad"
        assert _convex(np.asarray(q)), f"{o['id']}: concave quad {np.round(q, 2).tolist()}"
        assert Polygon(q).area > 0.02, f"{o['id']}: degenerate quad"
    for q in g["stripes"]:
        assert Polygon(q).difference(pg).area < 1e-3, f"{o['id']}: stripe outside the zone"
        da, skew = _dir(np.asarray(q))
        assert skew < 0.5, f"{o['id']}: stripe sides not parallel ({skew:.2f} deg)"
    # stripes of one field are parallel: every stripe direction is one of the field directions
    want = [d % 180.0 for d, n in g["fields"] if n]
    for q in g["stripes"]:
        da, _ = _dir(np.asarray(q))
        assert min(min(abs(da - w), 180.0 - abs(da - w)) for w in want) < 0.5, f"{o['id']}: stripe {da:.1f} deg off its field"
    # no two stripes overlap (fragments painted twice read as blobs)
    P = [Polygon(q) for q in g["stripes"]]
    for i in range(len(P)):
        for k in range(i + 1, len(P)):
            assert P[i].intersection(P[k]).area < 1e-3, f"{o['id']}: stripes {i} and {k} overlap"
    return g


@pytest.mark.parametrize("o", _zones(), ids=lambda o: o["id"])
def test_every_stripe_is_a_parallel_quad(o):
    _check(o)


def test_chevrons_are_mirrored_about_the_axis():
    o = {"id": "synthetic", "polygon_en": [[0, -1.5], [20, -1.5], [20, 1.5], [0, 1.5]],
         "chevron_axis": [[0, 0], [20, 0]], "stripe_rel_deg": 35, "chevron_apex": "nose"}
    g = _check(o)
    (d0, n0), (d1, n1) = g["fields"]
    assert n0 > 5 and n1 > 5 and abs(n0 - n1) <= 1
    assert abs((d0 + d1)) < 1e-6 and abs(abs(d0) - 35.0) < 1e-6
    # apex towards the nose (+x): the left (north) field runs down-right
    assert d0 < 0
    g2 = H.hatch(dict(o, chevron_apex="tip"))
    assert g2["fields"][0][0] > 0


def test_border_edges_subset():
    o = {"id": "s", "polygon_en": [[0, 0], [10, 0], [10, 2], [0, 2]], "axis": [[0, 1], [10, 1]], "border_edges": [2]}
    g = H.hatch(o)
    assert len(g["border"]) == 1
    q = np.asarray(g["border"][0])
    assert np.allclose(sorted(q[:2, 1].tolist()), [2.0, 2.0]) or np.isclose(q[:, 1].max(), 2.0)


def test_built_zones_do_not_sink_and_keep_their_stripes():
    q = json.load(open(REGION / "generated" / "roads_qa.json", encoding="utf-8"))
    zs = q["summary"]["painted_zones"]
    if not zs or "max_lift_m" not in zs[0]:
        pytest.skip("roads_qa.json from before ADR 0100 (rebuild the region)")
    for z in zs:
        assert z["built"], z["id"]
        # cells are lifted onto the highest surface sample (no paint under the asphalt), never by more than a step
        assert z["max_lift_m"] <= H.MAX_LIFT_M, (z["id"], z["max_lift_m"])
        assert z["stripes"] > 0, z["id"]
