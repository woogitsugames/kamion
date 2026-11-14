"""ADR 0194: road stains follow the traffic (class, junction approaches, wheel paths), oil stays matt and dark."""
from types import SimpleNamespace

import numpy as np

from roads import decals as DC
from streetscape.materials import M


def _sec(oneway, lanes=2, lane_w=3.5, edge=0.25, cls="Z"):
    return SimpleNamespace(oneway=oneway, lanes=lanes, lane_w=lane_w, edge_strip=edge, cls=cls)


def test_class_rates_follow_pavement_age():
    r = DC.PATCH_RATE_CLASS
    assert r["GP"] < r["G"] < r["Z"] < r["L"] <= r["D"]
    assert DC.JUNCTION_BOOST > 1.0 > DC.MIDBLOCK_RATE


def test_wheel_path_patches_sit_in_wheel_paths():
    """Every hashed wheel-path offset is within 0.15 m (jitter) of 0.26 / 0.74 of a lane, the _ROADWEAR paths."""
    for oneway in (True, False):
        sec = _sec(oneway)
        hw = sec.edge_strip + sec.lanes * sec.lane_w / (1 if oneway else 2) if oneway else 3.75
        outer = 0
        for k in range(400):
            lat = DC.wheel_path_lat(None, sec, hw, ("t", oneway, k))
            lane_pos = (lat + hw - sec.edge_strip) / sec.lane_w
            lc = lane_pos - np.floor(lane_pos)
            assert abs(abs(lc - 0.5) - DC.WHEEL_PATH_FRAC) <= 0.15 / sec.lane_w + 1e-9, (oneway, lat, lc)
            outer += (lc < 0.5) if (oneway or lat < 0) else (lc > 0.5)
        assert 0.55 < outer / 400 < 0.75          # OUTER_PATH_SHARE 0.65


def test_oil_look_is_matt_dark_and_opt_in():
    look = M["decal_oil"]["oil_look"]
    asphalt_smooth = 0.094                     # materials_spec asphalt_worn smoothness_mean (Low)
    assert look["smooth_aged"] <= asphalt_smooth * 1.2 and look["smooth_fresh"] < 0.3
    assert 0.4 <= look["coverage_gamma"] < 1.0
    # manhole / drain covers share _DECAL_ALPHA; they must not get the oil look
    assert all("oil_look" not in v for k, v in M.items() if k != "decal_oil")


def test_plate_uv1_spread_encoding_round_trips():
    """ADR 0194: plate UV1.y = 20 + 100 * spread + min(edge, 1); decode like KamionPlateWear."""
    from roads import meshing as MS
    for spread in (0.0, 0.3, 1.0):
        for edge in (0.0, 0.2, 0.64, 3.0):
            enc = MS.PLATE_EDGE_FLAG + MS.PLATE_SPREAD_SCALE * spread + min(edge, 1.0)
            assert enc > 15.0
            v = enc - MS.PLATE_EDGE_FLAG
            dec_spread = min(max((v - 1.0) / MS.PLATE_SPREAD_SCALE, 0.0), 1.0)
            if spread == 0.0:
                assert dec_spread == 0.0 and abs(min(max(v, 0.0), 1.0) - min(edge, 1.0)) < 1e-9
            else:
                assert abs(dec_spread - spread) <= 1.0 / MS.PLATE_SPREAD_SCALE + 1e-9


def test_plate_uv1_large_plate_never_drops_into_gutter_band():
    """Large >15m junction plates must encode ALL vertices >=20.0 (never fallback 5.0) and extend arm >5m."""
    from types import SimpleNamespace
    import numpy as np
    from roads import meshing as MS
    from roads.geom import Polyline

    sec = SimpleNamespace(lane_edges=None, oneway=False, roundabout=False, edge_strip=0.0, lane_w=3.5)

    def make_chain(pts, hw=4.0):
        line = Polyline(pts)
        return SimpleNamespace(
            line=line,
            length=float(line.length),
            dirn=np.zeros(len(line.p), int),
            idx=lambda s: int(np.argmin(np.abs(line.s - float(s)))),
            hw_at=lambda s: float(hw),
            section=lambda s, sec_list: sec_list[0],
        )

    c_west = make_chain(np.column_stack([np.linspace(-30.0, 0.0, 61), np.zeros(61)]), hw=4.0)
    c_east = make_chain(np.column_stack([np.linspace(0.0, 35.0, 71), np.zeros(71)]), hw=4.0)
    c_south = make_chain(np.column_stack([np.full(41, 4.0), np.linspace(-20.0, 0.0, 41)]), hw=3.0)

    def make_arm(chain, end, dir_vec):
        return SimpleNamespace(
            chain=chain,
            end=end,
            s=lambda d, ch=chain, e=end: float(d) if e == "a" else float(ch.length - d),
            direction=lambda d, v=np.array(dir_vec, float): v,
        )

    j = SimpleNamespace(
        arms=[
            make_arm(c_west, "b", [-1.0, 0.0]),
            make_arm(c_east, "a", [1.0, 0.0]),
            make_arm(c_south, "b", [0.0, -1.0]),
        ],
        trims={0: 5.0, 1: 18.0, 2: 5.0},  # arm 1 trims 18m from junction centre (> 5m old bound)
    )
    net = SimpleNamespace(sec_list=[sec])
    poly = np.array([
        [-5.0, 4.0], [18.0, 4.0], [18.0, -4.0], [10.0, -10.0], [-2.0, -10.0], [-5.0, -4.0],
    ])
    V = np.array([
        [-4.0, 0.0, 0.0],    # near west seam (interior)
        [0.0, 2.0, 0.0],     # plate centre carriageway
        [10.0, 1.5, 0.0],    # 10m along east plate (>5m old arm projection bound)
        [16.0, 0.0, 0.0],    # 16m along east plate (still within trim=18m, <= d+25)
        [4.0, -9.0, 0.0],    # turnoff lobe outside all arm widths (must NOT be 5.0!)
        [10.0, 4.0, 0.0],    # genuine kerb edge (UV1.y should stay ~20.0..20.5)
        [10.0, -9.5, 0.0],   # southern lobe vertex
    ])
    uv1 = MS._patch_uv1(net, j, V, poly)

    assert (uv1[:, 1] >= MS.PLATE_EDGE_FLAG).all(), f"unflagged plate vertex: {uv1[:, 1]}"
    # No vertex drops to -1.0 beside positive lane coords (would sawtooth wheel ruts across flare triangles)
    assert (uv1[:, 0] > -0.5).all(), f"lane dropped to -1.0 on plate: {uv1[:, 0]}"
    # Outer turnoff flare vertices snap smoothly to an integer lane boundary (frac=0 -> wp=drip=0) with spread=1
    assert np.allclose(uv1[[4, 6], 0], np.rint(uv1[[4, 6], 0]), atol=1e-6), f"flare not integer lane: {uv1[[4, 6], 0]}"
    assert (uv1[[4, 6], 1] >= MS.PLATE_EDGE_FLAG + MS.PLATE_SPREAD_SCALE + 1.0 - 1e-6).all()
    # Interior carriageway & outer flare vertices (indices 0..4, 6) must NOT land in [20.0, 20.65]
    assert (uv1[[0, 1, 2, 3, 4, 6], 1] >= MS.PLATE_EDGE_FLAG + 1.0).all(), f"gutter band leak: {uv1}"
    # 10m & 16m along east plate keep valid through-road lane coordinates
    assert (uv1[[1, 2, 3], 0] >= 0.0).all(), f"lost lane coord past 5m: {uv1[:, 0]}"
    # Genuine kerb vertex stays in gutter edge range [20.0, 20.65)
    assert MS.PLATE_EDGE_FLAG <= uv1[5, 1] < MS.PLATE_EDGE_FLAG + 0.65


def test_road_asphalt_shoulder_strip_uses_no_roadwear_uv1():
    """RURAL paved-shoulder / flush road_asphalt strips must use UV1=(-1, 5), never longitudinal metres along."""
    import numpy as np
    from roads import meshing as MS

    buf = MS.MeshBuf()
    n = 11
    G = np.column_stack([np.linspace(0.0, 20.0, n), np.zeros(n)])
    OUT = np.tile([0.0, -1.0], (n, 1))
    zg = np.zeros(n)
    params = [(MS.RURAL, 0.3, 0.0, 0.5, 0) for _ in range(n)]
    MS._emit_strip(buf, G, OUT, zg, params, np.zeros(n), 3.5, flip=False, br=None, coarse=False, src="test")

    road_parts = [p for p in buf.parts if p.mat in ("road_asphalt", "road_asphalt_new") and len(p.T)]
    assert road_parts, "expected road_asphalt paved-shoulder strip in RURAL profile"
    for p in road_parts:
        assert np.allclose(p.UV1[:, 0], -1.0), f"shoulder UV1.x leaked station m: {p.UV1[:, 0]}"
        assert np.allclose(p.UV1[:, 1], 5.0), f"shoulder UV1.y expected 5.0: {p.UV1[:, 1]}"
    other_parts = [p for p in buf.parts if p.mat in ("shoulder_gravel", "verge_grass") and p.UV1 is not None]
    assert any(p.UV1[:, 0].max() > 10.0 for p in other_parts), "non-road strips should keep along_m UV1.x"


def test_assemble_preserves_plate_uv1_across_arm_seam():
    """Arm-to-plate seam in assemble() must not overwrite plate UV1>=20 with arm UV1<15."""
    from types import SimpleNamespace
    import numpy as np
    from roads.build_world import assemble

    # Arm ribbon [x=0..10] followed by plate [x=10..20], sloping at seam x=10 to verify smooth normal sharing
    Va = np.array([
        [0.0, -3.5, 0.0], [0.0, 0.0, 0.0], [0.0, 3.5, 0.0],
        [10.0, -3.5, 1.0], [10.0, 0.0, 1.0], [10.0, 3.5, 1.0],
    ])
    Ta = np.array([[0, 3, 4], [0, 4, 1], [1, 4, 5], [1, 5, 2]])
    UV1a = np.array([
        [1.0, 0.0], [0.0, 3.5], [1.0, 0.0],
        [1.0, 0.0], [0.0, 3.5], [1.0, 0.0],
    ])

    Vp = np.array([
        [10.0, -3.5, 1.0], [10.0, 0.0, 1.0], [10.0, 3.5, 1.0],
        [20.0, -3.5, 1.0], [20.0, 0.0, 1.0], [20.0, 3.5, 1.0],
    ])
    Tp = np.array([[0, 3, 4], [0, 4, 1], [1, 4, 5], [1, 5, 2]])
    UV1p = np.array([
        [1.0, 20.0], [0.0, 21.0], [1.0, 20.0],
        [1.0, 20.0], [0.0, 50.0], [1.0, 20.0],
    ])

    arm = SimpleNamespace(layer="road", mat="road_asphalt", V=Va, T=Ta, UV=Va[:, :2], UV1=UV1a, COL=None)
    plate = SimpleNamespace(layer="road", mat="road_asphalt", V=Vp, T=Tp, UV=Vp[:, :2], UV1=UV1p, COL=None)
    out = assemble([arm, plate], {"road"}, half=128.0)
    prims = [p for p in out[(0, 0)]["road"] if p["mat"] == "road_asphalt"]
    assert len(prims) == 1
    m = prims[0]
    tri_uv1y = m["UV1"][m["T"], 1]
    crosses = ((tri_uv1y.min(1) < 15.0) & (tri_uv1y.max(1) >= 15.0)).any()
    assert not crosses, f"triangle crosses arm/plate UV1 threshold: {tri_uv1y}"

    seam = np.isclose(m["V"][:, 0], 10.0) & np.isclose(m["V"][:, 1], 0.0)
    assert seam.sum() == 2, "seam vertex should split cleanly across UV1 jump"
    assert m["UV1"][seam, 1].min() < 15.0 and m["UV1"][seam, 1].max() >= 21.0
    # Split seam copies must still share the exact same position-welded smooth normal
    norms = m["N"][seam]
    assert np.allclose(norms[0], norms[1], atol=1e-6)
    assert norms[0, 0] < -1e-3  # tilted by x=0..10 climb, not flat plate normal [0,0,1]
