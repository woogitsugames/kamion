"""Parked cars r10 (ADR 0078): modelled lamps and openings, plate holders, tyres, wheel styles, LOD2 silhouette, paint."""

from __future__ import annotations

import numpy as np


def _protos():
    from streetscape import life_cars as LC
    for b in LC.CARS:
        yield f"car_{b}_grey", LC.CARS[b], LC.car(b, "grey")
    yield "van_white", LC.VAN, LC.van("white")


def _by(mesh):
    return {p["mat"]: p for p in mesh.out()}


def test_lamps_grille_and_intake_have_depth():
    """The lamp reflector / tray and the grille back lie behind the body skin (r9: overlays 6-10 mm proud of it)."""
    from streetscape import life_cars as LC
    for name, d, P in _protos():
        m0 = _by(P[0])
        sh = LC._Shell(d, 0)
        y_face = float(sh.P[sh.seg["H1"]][0])                       # bonnet lip (top of the lamp band)
        head = m0["car_light_head"]["V"]
        front = head[head[:, 1] > 0]
        assert y_face - front[:, 1].min() >= 0.03, name             # reflector >= 30 mm behind the lip
        lamp = m0["car_lamp"]["V"]
        assert np.ptp(lamp[lamp[:, 1] > 0][:, 1]) >= 0.04, name     # bucket walls run back
        tail = m0["car_light_tail"]["V"]
        rear = tail[tail[:, 1] < 0]
        assert rear[:, 1].max() - rear[:, 1].min() >= 0.02, name
        g = np.asarray(m0["car_glass_tint"]["UV"], float)
        assert (np.abs(g[:, 0]) > 6.0).sum() >= 4 * 6, name         # clear covers: 2 head + 2 tail units


def test_plate_stands_off_on_a_holder_and_tyres_are_textured():
    from streetscape import life_cars as LC
    from streetscape.materials import M
    for name, d, P in _protos():
        m0 = _by(P[0])
        tyre = m0.get("car_tyre_dusty") or m0["car_tyre"]
        uv = np.asarray(tyre["UV"], float)
        assert uv[:, 0].max() >= LC.TYRE_REP - 1e-6 and 0.0 <= uv[:, 1].min() and uv[:, 1].max() <= 1.0, name
        assert (uv[:, 1] > 0.5).any() and (uv[:, 1] < 0.3).any(), name      # tread and sidewall zones
        assert len(m0["car_plate"]["T"]) == 4, name
    assert M["car_tyre"]["texture"] == "car_tyre" == M["car_tyre_dusty"]["texture"]
    im = np.asarray(LC.tyre_texture())[:, :, 0].astype(float)
    h = im.shape[0]
    tread, side = im[: h // 2], im[h // 2:]
    assert tread.min() < 90 and tread.max() > 200                   # grooves and blocks
    assert abs(im[:, :32].mean() - im[:, -32:].mean()) < 4          # tiles around the tyre (32 px slot period)
    assert side[-2:].std() < 1.0                                    # plain row for primitives without UVs


def test_wheel_styles_and_paint_types():
    from streetscape import life_cars as LC
    from streetscape.materials import M
    styles = {LC._style(f"{b}_{c}")["wheel"] for b in LC.CARS for c in LC.CAR_COLOURS}
    assert len(styles) >= 4, styles
    kinds = set()
    for c in LC.CAR_COLOURS + LC.VAN_COLOURS:
        p = M[f"car_paint_{c}"]["paint"]
        assert len(p) == 4 and 0.0 <= p[0] <= 1.0 and 0.0 <= p[1] <= 0.5 and 0.3 <= p[3] <= 0.7, c
        assert (p[0] == 0.0) == (p[1] == 0.0), c                     # flake only in a metallic base coat
        kinds.add("pearl" if p[2] > 0 else "metallic" if p[0] > 0 else "solid")
    assert kinds == {"solid", "metallic", "pearl"}
    assert M["car_glass_tint"]["lens_alpha"] <= 0.2


def test_lod2_keeps_the_silhouette():
    """LOD2 follows the LOD0 side outline: bonnet lower than the belt, nose narrower than the body, lamps present."""
    for name, d, P in _protos():
        m2 = _by(P[3])
        paint = next(v for k, v in m2.items() if k.startswith("car_paint_"))["V"]
        nose = paint[paint[:, 1] > d["L"] / 2 - 0.05]
        assert np.abs(nose[:, 0]).max() <= d["W"] / 2 - 0.05, name            # plan taper at the corners
        assert abs(paint[:, 1].max() - d["L"] / 2) < 0.03 and abs(paint[:, 2].max() - d["H"]) < 0.03, name
        hood = paint[(paint[:, 1] > d["L"] / 2 - d["hood"] * 0.5) & (paint[:, 2] > d["sill"] + 0.3)]
        assert hood[:, 2].max() <= d["belt"] + 0.02, name
        assert "car_light_tail" in m2 and "car_light_head" in m2 and ("rim" in m2 or "rim_steel" in m2), name


def test_door_seams_start_behind_the_front_arch():
    """r9 put the front door's leading seam 0.10 m AHEAD of the front arch (a stray line on the wing, the door-bottom
    line crossed the wheel opening); r10: no low trim on the side just ahead of the arch."""
    from streetscape import life_cars as LC
    for name, d, P in _protos():
        sh = LC._Shell(d, 0)
        v = _by(P[0])["car_trim"]["V"]
        side = v[(np.abs(v[:, 0]) > 0.3 * d["W"]) & (v[:, 2] < sh.sill + 0.12)]
        ahead = side[(side[:, 1] > sh.yfa + sh.ra + 0.05) & (side[:, 1] < sh.yfa + sh.ra + 0.15)]
        assert len(ahead) == 0, (name, ahead[:3])


def test_tail_film_uses_shell_uv_without_a_floating_skin():
    """ADR0089 film follows the actual curved painted shell, so its former off-surface alpha chords cannot recur."""
    for name, d, P in _protos():
        assert not any(k.startswith("car_dirt_") for k in _by(P[0]))
        paint = [p for k, p in _by(P[0]).items() if k.startswith("car_paint_")]
        for primitive in paint:
            assert np.allclose(primitive["UV"], primitive["V"][:, [1, 2]])
        v = np.concatenate([p["V"] for p in paint])
        tail = v[v[:, 1] < -d["L"] / 2 + 0.25]
        assert len(np.unique(np.round(np.abs(tail[:, 0]), 3))) >= 6, name
