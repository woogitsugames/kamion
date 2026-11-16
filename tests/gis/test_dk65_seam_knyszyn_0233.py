"""ADR 0233: the DK65 carriageway is the same road on both sides of the seams dk65-10 | dk65-11 | knyszyn-s and matches
research K1 there (painted edge lines 6.0-6.4 m apart, corridor median 6.2 m); the knyszyn-s section (7.5 m) starts at the
repaving joint at route km 25.32 inside knyszyn-s (override `width` profile + `lanes_follow_width`).

Network-level tests (roads.graph.json + overrides, always run) and built-geometry tests (chunk GLBs of build_world,
skipped where Data/raw/derived is not on the machine)."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "Data" / "Regions"
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
sys.path.insert(0, str(ROOT / "tools" / "worldgen" / "qa"))

SEAMS = [("dk65-10", "dk65-11", (762892.896, 609535.0)), ("dk65-11", "knyszyn-s", (762635.0, 609811.108))]
TOL = 0.1                      # task tolerance: width, lines, axis height (m)
K1_RANGE = (6.0, 6.4)          # research/dk65-knyszyn-refs/README.md, table (a)
K1_MEDIAN = 6.2
KS_EDGE = "w27718745:897574813-1134817563"
JOINT_M = (484.0, 496.0)       # repaving joint, metres into KS_EDGE from the seam (orthophoto 0.1 m, ADR 0233)
_NET = {}


def _net(t):
    if t not in _NET:
        from roads import pipeline
        _NET[t] = pipeline.build_network(t)[0]
    return _NET[t]


def _section_at(t, xy, inside_m=0.0):
    """Cross-section of the chain nearest to xy (EPSG:2180), `inside_m` metres along the chain into the tile."""
    from roads.markings import edge_lines, lane_layout
    net = _net(t)
    p = np.asarray(xy, float) - np.asarray(net.origin, float)
    best = None
    for c in net.chains:
        d = np.hypot(*(c.line.p - p).T)
        i = int(d.argmin())
        if best is None or d[i] < best[0]:
            best = (float(d[i]), c, float(c.line.s[i]))
    dist, c, s0 = best
    assert dist < 0.05, (t, dist)
    s = s0 + inside_m * (1 if s0 < c.length / 2 else -1)
    sec = c.section(s, net.sec_list)
    hw = float(c.hw_at(s))
    dirn = int(c.dirn[c.idx(s)]) or 1
    lat_c, _, cen = lane_layout(sec, hw, dirn)
    el = sorted(float(lat) for lat, _ in edge_lines(sec, hw, dirn))
    return {"edge": sec.edge_id, "width": 2 * hw, "edge_lines": el, "spacing": el[-1] - el[0] if len(el) == 2 else None,
            "centre": float(lat_c), "lanes": sorted(abs(float(x)) for x in cen["fwd"] + cen["bwd"]),
            "lane_w": float(sec.lane_w_at(hw)), "edge_strip": sec.edge_strip, "no_lamps": bool(sec.provenance.get("no_lamps"))}


@pytest.mark.parametrize("a,b,pt", SEAMS)
def test_seam_network_section_identical_and_k1(a, b, pt):
    assert not _net(a).overrides_stale and not _net(b).overrides_stale
    for inside in (0.0, 5.0, 50.0):
        va, vb = _section_at(a, pt, inside), _section_at(b, pt, inside)
        for k in ("width", "spacing", "centre", "lane_w", "edge_strip"):
            assert va[k] == pytest.approx(vb[k], abs=1e-6), (a, b, inside, k, va[k], vb[k])
        assert va["edge_lines"] == pytest.approx(vb["edge_lines"], abs=1e-6)
        assert va["lanes"] == pytest.approx(vb["lanes"], abs=1e-6)
        assert va["no_lamps"] and vb["no_lamps"]
        for v in (va, vb):
            assert K1_RANGE[0] <= v["spacing"] <= K1_RANGE[1], (a, b, inside, v["spacing"])
            assert abs(v["spacing"] - K1_MEDIAN) <= TOL
            assert abs(v["centre"]) < 1e-6          # centre line on the OSM axis


def test_k1_entry_verbatim_06_to_11():
    ent = []
    for t in ("dk65-06", "dk65-07", "dk65-08", "dk65-09", "dk65-10", "dk65-11"):
        ov = yaml.safe_load((REG / t / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
        ent.append(next(o for o in ov if o["id"] == "dk65-xsec-k1"))
        assert not any(o["id"] in ("dk65-carriageway-width", "dk65-old-xsec") for o in ov), t
    assert all(x == ent[0] for x in ent)
    assert ent[0]["set"] == {"lanes": 2, "lane_width": 3.1, "edge_strip": 0.2, "edge_lines": "both"}


def test_knyszyn_s_keeps_k1_to_the_joint_then_widens():
    ov = yaml.safe_load((REG / "knyszyn-s" / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    ids = [o["id"] for o in ov]
    assert ids.index("dk65-k1-section-to-km25.32") > ids.index("dk65-carriageway-width")      # refines the shared entry
    ent = ov[ids.index("dk65-k1-section-to-km25.32")]
    assert ent["target"] == {"edge": KS_EDGE} and ent["set"]["lanes_follow_width"] is True
    prof = ent["set"]["width"]
    assert prof[0] == [0.0, 6.6] and prof[-1] == [1.0, 7.5] and max(w for _, w in prof) == 7.5
    # the shared knyszyn entry is untouched (same set in knyszyn / knyszyn-w, ADR 0212)
    assert ov[ids.index("dk65-carriageway-width")]["set"] == {"lanes": 2, "lane_width": 3.4, "edge_strip": 0.35, "edge_lines": "both"}
    net = _net("knyszyn-s")
    sec = net.sections[KS_EDGE]
    assert sec.lane_follow and sec.lanes == 2 and sec.width == pytest.approx(7.5)
    L = next(c for c in net.chains if any(sp[2] == KS_EDGE for sp in c.raw_spans)).length
    assert prof[1][0] * L == pytest.approx(JOINT_M[0], abs=1.0) and prof[2][0] * L == pytest.approx(JOINT_M[1], abs=1.0)
    pt = SEAMS[1][2]
    prev = 0.0
    for m in range(0, int(L) - 5, 5):
        v = _section_at("knyszyn-s", pt, float(m))
        assert v["edge"] == KS_EDGE
        assert abs(v["centre"]) < 1e-6 and v["lanes"] == pytest.approx([v["lane_w"] / 2] * 2, abs=1e-6)
        assert v["spacing"] >= prev - 1e-9            # only widens
        prev = v["spacing"]
        if m <= JOINT_M[0] - 20:
            assert v["spacing"] == pytest.approx(K1_MEDIAN, abs=0.01), m
        if m >= JOINT_M[1] + 20:
            assert v["spacing"] == pytest.approx(7.1, abs=0.01), m          # the ADR 0212 section of knyszyn*


def test_lane_follow_is_opt_in():
    """Without `lanes_follow_width` nothing changes: lane_w_at() is lane_w, also on width-profile sections (ADR 0095)."""
    for t in ("dk65-10", "knyszyn-s"):
        net = _net(t)
        for s in net.sec_list:
            if s.edge_id == KS_EDGE:
                continue
            if str(s.provenance.get("lanes_follow_width", "")).startswith("derived:seam_taper"):
                continue      # ADR 0275: sections inside a seam width transition (knyszyn-s: w98071886 towards dw671)
            assert not s.lane_follow
            assert s.lane_w_at(s.width / 2 - 0.4) == s.lane_w
    from roads.network import EdgeSection
    import dataclasses
    base = _net("knyszyn-s").sections[KS_EDGE]
    plain = dataclasses.replace(base, lane_follow=False)
    assert plain.lane_w_at(3.3) == plain.lane_w
    assert float(base.lane_w_at(3.3)) == pytest.approx(3.1) and float(base.lane_w_at(3.75)) == pytest.approx(3.55)
    assert np.allclose(base.lane_w_at(np.array([3.3, 3.75])), [3.1, 3.55])
    assert isinstance(base, EdgeSection)


# ---------------------------------------------------------------- built geometry (chunk GLBs)
def _built(a, b):
    import seam_section
    for t in (a, b):
        m = REG / t / "generated" / "world_manifest.json"
        if not m.exists():
            pytest.skip(f"{t}: no world_manifest.json")
        if not (ROOT / json.loads(m.read_text(encoding="utf-8"))["chunks"][0]["file"]).exists():
            pytest.skip(f"{t}: chunk GLBs not on this machine (build_world not run)")
    return seam_section.measure(ROOT, [(a, b)])["seams"][0]


def _taper_asphalt_delta(a, b, inside_m):
    """Planned asphalt width of tile a minus tile b at `inside_m` from the seam (ADR 0275 seam transition; 0 without one).

    Read from roads_qa.json summary.seam_tapers of tile a (written by build_world): nominal widths + paved shoulder
    parts of both tiles, transition length L; both tiles lay half of one curve v(x) = A + (B - A) * smoothstep(0.5 + x / L).
    """
    q = json.loads((REG / a / "generated" / "roads_qa.json").read_text(encoding="utf-8"))
    tapers = [t for t in (q.get("summary") or {}).get("seam_tapers") or [] if t.get("neighbour") == b and "shoulder_cm" in t]
    if not tapers:
        return 0.0
    t = max(tapers, key=lambda x: x["step_m"])            # the route road is the only primary on these seams
    paved = sum(t["shoulder_cm"][s]["own"][0] - t["shoulder_cm"][s]["other"][0] for s in ("L", "R")) / 100.0
    full = (t["width_own"] - t["width_other"]) + paved    # nominal asphalt a - b, far from the seam
    u = min(1.0, 0.5 + inside_m / t["length_m"])
    return full * (2.0 * (3 * u * u - 2 * u ** 3) - 1.0)


@pytest.mark.parametrize("a,b,pt", SEAMS)
def test_seam_built_geometry(a, b, pt):
    row = _built(a, b)
    assert row["seam_epsg2180"] == pytest.approx(list(pt), abs=0.02)
    assert row["axis_kink_deg"] < 0.1
    sa, sb = row["sides"][a], row["sides"][b]
    for t, side in ((a, sa), (b, sb)):         # chunk GLBs are not in git: a stale local build is not a regression
        if abs((side["sections"][0]["edge_line_spacing"] or 0.0) - _section_at(t, pt, 2.0)["spacing"]) > 0.05:
            pytest.skip(f"{t}: chunk GLBs older than the overrides (rebuild: roads/build_world.py --region {t})")
    for k, xa in enumerate(sa["sections"]):
        xb = sb["sections"][k]
        for x in (xa, xb):
            assert K1_RANGE[0] <= x["edge_line_spacing"] <= K1_RANGE[1], (a, b, x["inside_m"], x["edge_line_spacing"])
            assert abs(x["edge_line_spacing"] - K1_MEDIAN) <= TOL
            assert len(x["asphalt"]) == 1 and abs(sum(x["edge_lines"])) <= 0.05          # one carriageway, lines symmetric
            assert [ln for ln in x["lines"] if abs(ln[0]) <= 2.0] == [] or abs([ln for ln in x["lines"] if abs(ln[0]) <= 2.0][0][0]) <= 0.1
        # ADR 0275: where the generator joins two nominal cross-sections with a seam transition, the asphalt widths
        # at the same distance on both sides differ by the planned S-curve (0 on the seam itself), not by 0
        want = _taper_asphalt_delta(a, b, xa["inside_m"])
        assert abs((xa["asphalt_width"] - xb["asphalt_width"]) - want) <= TOL, (a, b, xa["inside_m"], want)
        assert abs(xa["edge_line_spacing"] - xb["edge_line_spacing"]) <= TOL
    d = row["delta"]
    assert abs(d["z_seam"]) <= TOL, d            # axis height across the seam
    assert abs(d["route_lat"]) <= TOL, d         # route (right lane centre) does not step sideways
    assert abs(sa["grade_pct_travel"] - sb["grade_pct_travel"]) <= 0.5
