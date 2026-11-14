"""ADR 0196 - paint of an aerodrome runway laid as an authored `paved_area` (Krywlany 09R/27L).

The road marking generator only paints carriageways of the road graph; a runway is a paved area. Override
`kind: runway_markings` (region-local E/N, every number read off the orthophoto and quoted in the entry):

    axis_en: [[E, N], [E, N]]            # runway centre line, from the low-station end to the high-station end
    edge_lines: {offset_m, width_m, s_m: [s0, s1]}            # side stripes, centre +-offset from the axis
    centre_dashes: [{s_m: [s0, s1]} ...]  width_m             # centre line pieces
    bars: [{s_m, width_m, half_span_m}]                       # threshold bars across the runway
    chevrons: [{s_m: [tip, tail], rows_lat_m: [...], width_m}]         # pre-threshold arrow heads (tip at s_m[0])
    arrows: {tips_s_m: [...], length_m, head_m: [length, width], shaft_w_m, towards: low | high}

s = metres along the axis from its first point. Everything is drawn as bands along the axis, sampled every STEP_M
both ways and draped on the paved surface (`zsurf`) + standards.MARKING_LIFT in the road paint material
`marking_white` on the `markings` layer (decal depth offset in the engine: no z-fighting, no new material). No
lettering: the runway designator is not drawn. Regions without such an override get nothing.
"""

from __future__ import annotations

import math
import zlib

import numpy as np

from roads import standards as S

STEP_M = 2.0
MAT = "marking_white"


def _band(buf, P0, t, n, s0, s1, lat_a, lat_b, zsurf, src):
    """Band between stations s0 < s1; lat_a(s) / lat_b(s) = its two lateral limits (m left of the axis). Grid of
    <= STEP_M cells. Returns the triangle count."""
    ns = max(1, int(math.ceil((s1 - s0) / STEP_M)))
    ss = np.linspace(s0, s1, ns + 1)
    wmax = max(abs(lat_b(s) - lat_a(s)) for s in ss)
    nl = max(1, int(math.ceil(wmax / STEP_M)))
    f = np.linspace(0.0, 1.0, nl + 1)
    V2 = []
    for s in ss:
        a, b = lat_a(s), lat_b(s)
        for q in f:
            V2.append(P0 + t * s + n * (a + (b - a) * q))
    V2 = np.asarray(V2)
    T = []
    m = nl + 1
    for i in range(ns):
        for j in range(nl):
            v00, v01, v10, v11 = i * m + j, i * m + j + 1, (i + 1) * m + j, (i + 1) * m + j + 1
            T += [(v00, v10, v11), (v00, v11, v01)]              # s forward, lat to the left: CCW from above
    T = np.asarray(T)
    A = V2[T]
    area = 0.5 * ((A[:, 1, 0] - A[:, 0, 0]) * (A[:, 2, 1] - A[:, 0, 1]) - (A[:, 2, 0] - A[:, 0, 0]) * (A[:, 1, 1] - A[:, 0, 1]))
    T = T[np.abs(area) > 1e-5]                                    # the tip of an arrow head degenerates
    flip = area[np.abs(area) > 1e-5] < 0                          # lat_a > lat_b bands
    T[flip] = T[flip][:, ::-1]
    if not len(T):
        return 0
    Z = zsurf(V2[:, 0], V2[:, 1]) + S.MARKING_LIFT
    age = (zlib.crc32(src.encode()) % 1000) / 1000.0 * 0.98
    buf.add("markings", MAT, np.column_stack([V2, Z]), V2.copy(), T, src=src,
            UV1=np.column_stack([np.full(len(V2), 0.5), np.full(len(V2), 0.35 + age)]))
    return int(len(T))


def build(buf, overrides, zsurf, report):
    rep = []
    for o in overrides:
        if o.get("kind") != "runway_markings":
            continue
        A = np.asarray(o["axis_en"], float)
        L = float(np.hypot(*(A[1] - A[0])))
        t = (A[1] - A[0]) / L
        n = np.array([-t[1], t[0]])
        P0 = A[0]
        tris = 0
        src = f"runway:{o['id']}"
        const = lambda v: (lambda s: v)
        e = o.get("edge_lines")
        if e:
            s0, s1 = e.get("s_m", [0.0, L])
            for sgn in (-1, 1):
                c, w = sgn * float(e["offset_m"]), float(e["width_m"])
                tris += _band(buf, P0, t, n, s0, s1, const(c - w / 2), const(c + w / 2), zsurf, f"{src}:edge{sgn}")
        cw = float(o.get("centre_w_m", 0.45))
        for k, d in enumerate(o.get("centre_dashes") or []):
            tris += _band(buf, P0, t, n, d["s_m"][0], d["s_m"][1], const(-cw / 2), const(cw / 2), zsurf, f"{src}:dash{k}")
        for k, b in enumerate(o.get("bars") or []):
            w, hs = float(b["width_m"]), float(b["half_span_m"])
            tris += _band(buf, P0, t, n, b["s_m"] - w / 2, b["s_m"] + w / 2, const(-hs), const(hs), zsurf, f"{src}:bar{k}")
        for k, c in enumerate(o.get("chevrons") or []):
            tip, tail = (float(x) for x in c["s_m"])
            hw = float(c["width_m"]) / 2
            arm = float(c.get("arm_m", 0.9))                     # paint thickness of an arm, measured along the axis
            lo, hi = min(tip, tail), max(tip, tail)
            ln = hi - lo
            for j, lat in enumerate(c["rows_lat_m"]):
                # V of two arms meeting at the tip: outer edge from the tip to +-hw at the tail, inner edge the same
                # line shifted `arm` along the axis (clamped at the axis)
                def outer(s, sgn, lat=lat):
                    return lat + sgn * hw * abs(s - tip) / ln

                def inner(s, sgn, lat=lat):
                    return lat + sgn * hw * max(abs(s - tip) - arm, 0.0) / ln
                for sgn in (-1, 1):
                    tris += _band(buf, P0, t, n, lo, hi, lambda s, sgn=sgn: inner(s, sgn), lambda s, sgn=sgn: outer(s, sgn),
                                  zsurf, f"{src}:chev{k}:{j}:{sgn}")
        a = o.get("arrows")
        if a:
            ln, (hl, hwid), sw = float(a["length_m"]), (float(x) for x in a["head_m"]), float(a["shaft_w_m"])
            dirn = -1.0 if a.get("towards", "low") == "low" else 1.0     # the tip looks to the low-station end
            for k, tip in enumerate(a["tips_s_m"]):
                tip = float(tip)
                base = tip - dirn * hl                             # head: tip -> base
                tail = tip - dirn * ln
                lo, hi = min(tip, base), max(tip, base)
                tris += _band(buf, P0, t, n, lo, hi, lambda s, tip=tip: -hwid / 2 * abs(s - tip) / hl,
                              lambda s, tip=tip: hwid / 2 * abs(s - tip) / hl, zsurf, f"{src}:arrowhead{k}")
                lo, hi = min(base, tail), max(base, tail)
                tris += _band(buf, P0, t, n, lo, hi, const(-sw / 2), const(sw / 2), zsurf, f"{src}:arrowshaft{k}")
        if tris == 0:
            raise ValueError(f"runway_markings {o['id']}: nothing built")
        rep.append({"id": o["id"], "length_m": round(L, 1), "triangles": tris})
    if rep:
        report["runway_markings"] = rep
