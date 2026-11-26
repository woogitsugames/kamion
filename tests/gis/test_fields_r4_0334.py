"""fields4-s24 (ADR 0334 r4, critic s24 wave 11 pt 10 / pola): the margin of the maize stand (no flat walls of cards),
seams without a baulk crossed by the stand, the atlas edge cell, ruts and the far plan in the shader, the wide layout
warp octave (Python mirror) and the broken far forest edge (streetscape.far_field)."""
import re
from pathlib import Path

import numpy as np

from roads.meshing import MeshBuf
from streetscape import far_field as FF
from streetscape import field_crops as FC
from streetscape import vegetation as VG
from streetscape import verge_atlas as VA

import test_fields_r3_0334 as R3

ROOT = Path(__file__).resolve().parents[2]
HLSL = (ROOT / "game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl").read_text(encoding="utf-8")
MAIZE = VG.FIELD_USES.index("maize")


def test_far_warp_octave_matches_the_shader_and_bows_far_borders():
    (cx, ax, sa, sb), = VG.FIELD_WARP_FAR
    assert f"#define KF_WARP_X_M {cx:.1f}" in HLSL and f"#define KF_WARP_AX {ax:.1f}" in HLSL
    assert f"KFNoise(local, origin, KF_WARP_X_M, {sa}u)" in HLSL and f"KFNoise(local, origin, KF_WARP_X_M, {sb}u)" in HLSL
    rng = np.random.default_rng(7)
    P = rng.uniform(0, 8000, (20000, 2)) + np.array([758000.0, 609000.0])
    dx, dy = VG.field_warp(P[:, 0], P[:, 1])
    assert 4.0 < np.std(dx) < 10.0 and 4.0 < np.std(dy) < 10.0      # metres: a border 300-1000 m out bows visibly
    dx2, _ = VG.field_warp(P[:, 0] + 10.0, P[:, 1])
    assert np.abs(dx2 - dx).max() < 1.6                              # still no kink over 10 m
    x, y = VG.field_unwarp(P[:, 0] + dx, P[:, 1] + dy, rounds=14)
    assert np.abs(x - P[:, 0]).max() < 0.01 and np.abs(y - P[:, 1]).max() < 0.01


def _stand():
    o = R3._maize_origin()
    buf, hf, col, dist = R3._crop_world()
    rep = {}
    FC.build(buf, col, hf, np.zeros(hf.z.shape), o, dist, None, rep)
    parts = {p.src.split(":")[1]: p for p in buf.parts if p.src.startswith("field_crops:")}
    return o, hf, col, dist, parts, rep["field_crops"]


def test_maize_stand_runs_over_seams_without_a_baulk_and_stops_at_baulks():
    o, hf, col, dist, parts, rep = _stand()
    V = np.concatenate([parts[k].V.reshape(-1, 4, 3) for k in ("maize", "maize_edge")])
    mid = V[:, :2, :2].mean(1)
    L = VG.field_layout(mid[:, 0] + o[0], mid[:, 1] + o[1])
    lo, hi = FC._baulk_sides(L)
    a, w = L["across"], L["w"]
    rows = parts["maize"].V.reshape(-1, 4, 3)[:, :2, :2].mean(1)
    Lr = VG.field_layout(rows[:, 0] + o[0], rows[:, 1] + o[1])
    lo_r, hi_r = FC._baulk_sides(Lr)
    plain_r = ((Lr["across"] < 1.0) & ~lo_r) | (((Lr["w"] - Lr["across"]) < 1.0) & ~hi_r)
    assert plain_r.sum() > 20                                        # r3 left a 3.2 m corridor on every seam
    c_lo, c_hi = FC.baulk_clear(L, mid, o)
    e_b = np.minimum(np.where(lo, a - c_lo, np.inf), np.where(hi, w - a - c_hi, np.inf))
    nr = len(parts["maize"].V) // 4
    assert (e_b[:nr] > -0.3).all() and (e_b[:nr] < 0.6).mean() < 0.2   # off the baulk, but up to it (no corridor)
    assert (c_lo < FC.MAIZE_SEAM_CLEAR_M).mean() > 0.4


def test_maize_margin_is_ragged_not_a_wall_of_cards():
    o, hf, col, dist, parts, rep = _stand()
    assert rep["maize"]["edge_cards"] > 500 and rep["maize"]["strays"] > 100
    E = parts["maize_edge"].V.reshape(-1, 4, 3)
    h = E[:, 2:, 2].mean(1) - E[:, :2, 2].mean(1)
    assert h.std() > 0.18 and np.percentile(h, 10) < 1.75 and h.max() <= FC.MAIZE_H[1] * 1.06 + FC.MAIZE_SINK_M + 0.01
    w = np.hypot(*(E[:, 1, :2] - E[:, 0, :2]).T)
    assert (w < 0.8).sum() > 100 and (np.abs(w - VA.MAIZE_CELL_M) < 0.05).sum() > 300   # strays + single-cell cards
    assert not (np.abs(w - FC.MAIZE_CARD_L) < 0.05).any()            # no 3.2 m card at the margin
    # the edge cards are turned off the row line (no straight wall), the strays any way
    mid = E[:, :2, :2].mean(1)
    L = VG.field_layout(mid[:, 0] + o[0], mid[:, 1] + o[1])
    d = (E[:, 1, :2] - E[:, 0, :2]) / np.maximum(w, 1e-6)[:, None]
    along = np.column_stack([-np.sin(L["th"]), np.cos(L["th"])])
    off = np.arccos(np.clip(np.abs((d * along).sum(1)), 0.0, 1.0))
    assert (off > 0.12).mean() > 0.35
    # the edge cell (single plants) is used, and only the wall cells by the stand inside
    u = parts["maize_edge"].UV.reshape(-1, 4, 2)[:, :2, 0]
    edge_u = VA.MAIZE_EDGE_CELL / VA.N_MAIZE
    assert (u.min(1) >= edge_u - 1e-6).mean() > 0.3
    ur = parts["maize"].UV.reshape(-1, 4, 2)[:, :2, 0]
    assert ur.max() <= VA.N_MAIZE_WALL / VA.N_MAIZE + 1e-6
    # no cross card faces out of a cut: every cross card is deeper in than the edge zone
    C = parts["maize_cross"].V.reshape(-1, 4, 3)[:, :2, :2]
    g = FC._Ground(col, hf, np.zeros(hf.z.shape), dist, None)
    for k in (0, 1):
        Q = C[:, k]
        Lq = VG.field_layout(Q[:, 0] + o[0], Q[:, 1] + o[1])
        assert (FC._edge_dist(g, Q, Lq, o) > FC.MAIZE_EDGE_M - 1e-6).all()


def test_maize_cards_stay_in_the_triangle_budget():
    """r4 costs triangles at the margin (single cards, strays); bounded per hectare of maize within the card range."""
    o, hf, col, dist, parts, rep = _stand()
    n = hf.z.shape[0]
    x, y = np.meshgrid(np.arange(n) + hf.x0 + 0.5, hf.y1 - np.arange(n) - 0.5)
    mz = (VG.field_use(VG.field_layout(x + o[0], y + o[1]), True) == MAIZE) & (col[..., 2] >= FC.ARABLE_B)
    tris = sum(len(parts[k].T) for k in ("maize", "maize_cross", "maize_edge"))
    per_ha = tris / (mz.sum() / 1e4)
    assert per_ha < 4200, per_ha                                     # r4 ~3 870 / ha on this fixture (margins +36 %)


def test_atlas_edge_cell_holds_single_plants_beside_a_dense_wall():
    a = np.asarray(VA.texture())[..., 3] > 127
    mz = a[: VA.TEX_H // 2]
    cw = VA.TEX_W // VA.N_MAIZE
    body = mz[int(0.25 * mz.shape[0]):int(0.9 * mz.shape[0])]
    for k in range(VA.N_MAIZE_WALL):
        assert body[:, k * cw:(k + 1) * cw].mean() > 0.85
    ec = body[:, VA.MAIZE_EDGE_CELL * cw:(VA.MAIZE_EDGE_CELL + 1) * cw]
    assert 0.12 < ec.mean() < 0.5                                    # plants apart, the sky between them
    third = cw // VA.MAIZE_EDGE_PLANTS
    for q in range(VA.MAIZE_EDGE_PLANTS):                            # one plant per third (a stray maps one)
        assert ec[:, q * third:(q + 1) * third].mean() > 0.08


def test_shader_ruts_and_far_plan_contract():
    assert re.search(r"half farK = \(half\)saturate\(\(fp - [0-9.]+\) / [0-9.]+\);", HLSL)
    cereal = HLSL[HLSL.index("// tramlines: two wheel tracks"):HLSL.index("else if (u <= KF_RAPE_STUBBLE)")]
    assert "slopeEN +=" in cereal and "tthin" in cereal               # a rut with a profile and a thinned crop beside it
    assert "saturate(7.3 / (2.0 * fpr) - 0.5)" in HLSL                # pass streaks filtered across the rows
    assert "farK > 0.0h && !hrow" in HLSL                             # far: passes along the rows
    assert "float fpk = clamp(abs(dot(enDx, gW)) + abs(dot(enDy, gW))" in HLSL   # block border filtered across
    assert "bc *= 1.0h - 0.40h * farK;" in HLSL                       # baulks darker far away


def test_far_forest_edge_is_broken():
    assert FF.FAR_END_FLOOR < 0.52 and FF.FAR_END_TAPER_M > 16.0
    assert FF.FAR_COMPARTMENT_H[0] < 0.8 < 1.0 < FF.FAR_COMPARTMENT_H[1] and FF.FAR_EMERGENT_H[0] > 1.0
    e = np.linspace(1100.0, 3100.0, 400)
    n = np.full_like(e, 300.0)
    h = FF._crown_height_wave(e, n, 19.5, mix="mixed")
    step = np.abs(np.diff(h))
    assert h.std() / h.mean() > 0.12 and np.percentile(step, 99) > 3.0 * np.median(step)   # steps, not only a wave
