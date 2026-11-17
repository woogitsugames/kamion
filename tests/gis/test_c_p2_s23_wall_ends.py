"""c-p2-s23 (REVIEW-2026-11-17-s23-c-p1 P2) on synthetic data, no Data/raw:
- the rural shoulder profile on the station borrowed from a walled ramp stays inside the wall line, its skirt on
  that span is not meshed (the wall stands there);
- the grass batter turns around the wall end as a quarter cone no steeper than the verge QA limit, outside the wall;
- ground inside the outline of a walled ramp never stands above the ground outside (no terrain through the wall);
- a noise barrier ends on a post (plinth and panels do not run past the last post)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from roads import meshing as M  # noqa: E402
from roads import standards as S  # noqa: E402
from roads.network import RURAL, side_extent  # noqa: E402
from streetscape import furniture as FU  # noqa: E402
from terrain_mesh import conform as CF  # noqa: E402


def _rural_strip(uclip):
    n = 5
    G = np.column_stack([np.arange(n) * 2.0, np.zeros(n)])
    OUT = np.tile([0.0, 1.0], (n, 1))
    params = [(RURAL, 0.3, 0.0, S.FLANGE_DEPTH, 0)] * n
    buf = M.MeshBuf()
    M._emit_strip(buf, G, OUT, np.full(n, 100.0), params, np.zeros(n), np.full(n, 3.5), False, None, False, "w1:L:1",
                  uclip=uclip)
    return buf, side_extent(*params[0])


def test_borrowed_walled_station_profile_stays_inside_wall_line():
    clip = 0.65
    uc = np.full(5, np.inf)
    uc[0] = clip
    buf, full = _rural_strip(uc)
    assert full > clip + 0.5
    for p in buf.parts:
        at0 = np.isclose(p.V[:, 0], 0.0)
        assert p.V[at0, 1].max() <= clip + 1e-6, p.mat          # nothing beyond the wall line at the deck station
    # the free stations keep their width; station 1 onwards is battered beyond the rim
    assert max(p.V[:, 1].max() for p in buf.parts) > full
    # skirt (last, vertical profile row): no face on the span next to the clipped station
    free, _ = _rural_strip(None)
    sk, sk0 = buf.parts[-1], free.parts[-1]
    assert sk.mat == sk0.mat == "verge_grass"
    assert len(sk0.T) - len(sk.T) == 2
    assert not np.isclose(sk.V[np.unique(sk.T), 0], 0.0).any()
    # no grass face steeper than the QA limit anywhere on the clipped strip
    for p in buf.parts:
        if p.mat != "verge_grass" or not len(p.T):
            continue
        a, b, c = (p.V[p.T[:, k]] for k in range(3))
        nrm = np.cross(b - a, c - a)
        nz = np.abs(nrm[:, 2]) / np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)
        assert nz.min() > CF.WALL_STEEP_NZ


def test_unclipped_strip_unchanged_by_uclip_none_or_inf():
    a, _ = _rural_strip(None)
    b, _ = _rural_strip(np.full(5, np.inf))
    assert len(a.parts) == len(b.parts)
    for p, q in zip(a.parts, b.parts):
        assert np.allclose(p.V, q.V) and np.array_equal(p.T, q.T)


def test_wall_end_cone_is_a_gentle_batter_outside_the_wall():
    rim = np.array([10.0, 0.0, 100.7])
    out = np.array([0.0, 1.0])
    V, T = M.wall_end_cone(rim, 100.0, np.array([8.0, 0.0, 101.0]), out)
    run = 0.7 * S.EMBANKMENT_SLOPE
    assert np.allclose(V[0], [10.0, M.WALL_CONE_GAP_M, 100.7])            # apex on the rim, just off the wall face
    assert np.allclose(V[1], [10.0, run, 100.0])                          # joins the batter toe of the shoulder
    assert np.allclose(V[3], [10.0 - run, M.WALL_CONE_GAP_M, 100.0])      # runs out along the wall foot
    assert V[:, 1].min() >= M.WALL_CONE_GAP_M - 1e-9                      # never behind the wall face
    assert V[:, 0].max() <= 10.0 + 1e-9                                   # never past the wall end
    a, b, c = (V[T[:, k]] for k in range(3))
    nrm = np.cross(b - a, c - a)
    nz = np.abs(nrm[:, 2]) / np.linalg.norm(nrm, axis=1)
    assert nz.min() > CF.GRASS_STEEP_NZ
    assert len(T) == 4                                                    # two facets, both windings
    # a short last wall segment limits the run along the wall
    V2, _ = M.wall_end_cone(rim, 100.0, np.array([9.5, 0.0, 101.0]), out)
    assert V2[:, 0].min() >= 9.5
    assert M.wall_end_cone(rim, 100.68, np.array([8.0, 0.0, 101.0]), out) is None


def test_ground_inside_wall_outline_not_above_ground_outside():
    z = np.full((21, 21), 100.0)
    z[:, 12:] = 99.5                      # lower ground east of the ramp
    fill = np.zeros(z.shape, bool)
    fill[:, 8:12] = True                  # the outline of the walled ramp
    z[fill] = 101.3                       # nodes kept just under the ramp surface
    keep = np.zeros(z.shape, bool)
    keep[0:3, :] = True                   # a ground road crossing at the toe keeps its nodes
    z[keep] = 100.2
    out, n = CF.level_under_walled(z, fill, keep)
    assert n == int((fill & ~keep).sum())
    assert np.array_equal(out[keep], z[keep]) and np.array_equal(out[~fill], z[~fill])
    assert np.allclose(out[5:, 8:10], 100.0) and np.allclose(out[5:, 10:12], 99.5)     # nearest outside node
    assert (out <= z).all()
    same, n0 = CF.level_under_walled(z, np.zeros(z.shape, bool), keep)
    assert n0 == 0 and same is z


def test_walled_fill_mask_covers_the_ramp_between_its_walls_only():
    from roads.build_world import WALLED_FILL_MARGIN_M, walled_fill_mask
    s = np.arange(0.0, 31.0, 1.0)
    P = np.column_stack([s - 15.0, np.zeros_like(s)])
    walled = s <= 15.0

    def frame(ss):
        return np.tile([1.0, 0.0], (len(ss), 1)), np.tile([0.0, 1.0], (len(ss), 1))

    n = len(s)
    side = {sd: {"kind": np.full(n, 1), "h": np.full(n, 0.2), "w": np.full(n, 1.5), "depth": np.full(n, 1.4),
                 "mat": np.full(n, 2)} for sd in ("L", "R")}
    c = SimpleNamespace(meta={"walled": walled}, line=SimpleNamespace(s=s, p=P, frame=frame), hw=np.full(n, 3.5),
                        side=side, idx=lambda x: int(round(float(x))),
                        interp=lambda arr, x: float(np.interp(x, s, np.asarray(arr, float))))
    hf = SimpleNamespace(z=np.zeros((41, 41)), x0=-20.0, y1=20.0)
    m = walled_fill_mask(SimpleNamespace(chains=[c]), hf)
    edge = 3.5 + side_extent(1, 0.2, 1.5, 1.4, 2) + WALLED_FILL_MARGIN_M

    def node(e, nn):
        return m[int(round(hf.y1 - nn)), int(round(e - hf.x0))]
    assert node(-10, 0) and node(-10, 5) and node(-10, -5)
    assert not node(-10, int(np.ceil(edge)) + 1) and not node(-10, -int(np.ceil(edge)) - 1)
    assert not node(10, 0)                       # beyond the walled run (span / ground road)


class _Lin(FU.Lin):
    def __init__(self):
        super().__init__(M.MeshBuf(), lambda e, n: np.zeros_like(np.asarray(e, float)))


def _post_centres(lin, mat="noise_post", h_min=3.0):
    out = []
    for p in lin.buf.parts:
        if p.mat != mat or p.layer != "furniture" or len(p.V) % 8:
            continue
        B = p.V.reshape(-1, 8, 3)
        tall = (B[:, :, 2].max(1) - B[:, :, 2].min(1)) > h_min
        out += [b[:, :2].mean(0) for b in B[tall]]
    return np.array(out)


def test_noise_wall_ends_on_a_post():
    P = np.column_stack([np.linspace(0.0, 10.0, 6), np.zeros(6)])     # 10 m: posts at 0, 4, 8 -> 2 m of panel past the last
    st = dict(FU.NOISE_STYLES["glazed"], name="glazed")
    lin = _Lin()
    FU.noise_wall(lin, P, np.zeros(6), st, 4.0, "t")
    c = _post_centres(lin)
    assert np.allclose(sorted(c[:, 0]), [0.0, 4.0, 8.0, 10.0])
    plinth = np.concatenate([p.V for p in lin.buf.parts if p.mat == "concrete_plinth"])
    assert plinth[:, 0].max() <= c[:, 0].max() + FU.NOISE_POST_W / 2          # plinth ends inside the end post
    # a style joint inside one barrier: the next run starts with its own post, no doubled post
    lin2 = _Lin()
    FU.noise_wall(lin2, P, np.zeros(6), st, 4.0, "t", end_post=False)
    assert np.allclose(sorted(_post_centres(lin2)[:, 0]), [0.0, 4.0, 8.0])
    # a run that already ends on a post gets no second one
    P8 = np.column_stack([np.linspace(0.0, 8.0, 5), np.zeros(5)])
    lin3 = _Lin()
    FU.noise_wall(lin3, P8, np.zeros(5), st, 4.0, "t")
    assert np.allclose(sorted(_post_centres(lin3)[:, 0]), [0.0, 4.0, 8.0])
