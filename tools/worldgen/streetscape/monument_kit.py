"""Small mesh kit for authored monuments (ADR 0320): lathed bodies with a per-ring section, limbs, spheres.

Everything lands in a buildings_mesh.Acc. Rings share vertices, so a body shades as one surface; a ring listed twice at
one height makes a hard edge (cornices, plinth steps). No textures, lettering or emblems.
"""
from __future__ import annotations

import math

import numpy as np


def frame(forward):
    """(forward, right, up) unit vectors in 3D from a horizontal forward direction."""
    f = np.array([forward[0], forward[1], 0.0], float)
    f /= np.linalg.norm(f)
    return f, np.array([f[1], -f[0], 0.0]), np.array([0.0, 0.0, 1.0])


def section(sides, rx, ry, power=2.0, phase=0.0):
    """Closed superellipse section, `sides` points: power 2 = ellipse, 6-10 = rounded rectangle. x = right, y = fwd."""
    out = []
    for i in range(sides):
        a = phase + 2.0 * math.pi * i / sides
        c, s = math.cos(a), math.sin(a)
        out.append((rx * math.copysign(abs(c) ** (2.0 / power), c), ry * math.copysign(abs(s) ** (2.0 / power), s)))
    return out


def lathe(acc, layer, mat, origin, forward, rings, sides=12, power=2.0, phase=0.0, cap=True, bottom=False):
    """Body through `rings` = [(z, rx, ry[, off_right, off_fwd[, power]])] above `origin` (x, y, z)."""
    f, r, up = frame(forward)
    o = np.asarray(origin, float)
    V = []
    for ring in rings:
        z, rx, ry = ring[:3]
        ox, oy = (ring[3], ring[4]) if len(ring) >= 5 else (0.0, 0.0)
        pw = ring[5] if len(ring) >= 6 else power
        for x, y in section(sides, rx, ry, pw, phase):
            V.append(o + r * (x + ox) + f * (y + oy) + up * z)
    T = []
    for j in range(len(rings) - 1):
        for i in range(sides):
            a, b = j * sides + i, j * sides + (i + 1) % sides
            T += [(a, b, b + sides), (a, b + sides, a + sides)]
    if cap:
        b0 = (len(rings) - 1) * sides
        T += [(b0, b0 + i, b0 + i + 1) for i in range(1, sides - 1)]
    if bottom:
        T += [(0, i + 1, i) for i in range(1, sides - 1)]
    acc.add(layer, mat, np.array(V), T)
    return len(T)


def limb(acc, layer, mat, pts, radii, sides=6):
    """Tube through 3D points with a radius per point, closed at both ends."""
    P = [np.asarray(p, float) for p in pts]
    V = []
    for k, p in enumerate(P):
        d = P[min(k + 1, len(P) - 1)] - P[max(k - 1, 0)]
        d /= np.linalg.norm(d)
        ref = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        a = np.cross(d, ref)
        a /= np.linalg.norm(a)
        b = np.cross(d, a)
        for i in range(sides):
            ang = 2.0 * math.pi * i / sides
            V.append(p + (a * math.cos(ang) + b * math.sin(ang)) * radii[k])
    T = []
    for j in range(len(P) - 1):
        for i in range(sides):
            a_, b_ = j * sides + i, j * sides + (i + 1) % sides
            T += [(a_, b_, b_ + sides), (a_, b_ + sides, a_ + sides)]
    b0 = (len(P) - 1) * sides
    T += [(b0, b0 + i, b0 + i + 1) for i in range(1, sides - 1)]
    T += [(0, i + 1, i) for i in range(1, sides - 1)]
    acc.add(layer, mat, np.array(V), T)
    return len(T)


def sphere(acc, layer, mat, centre, radius, sides=8, stacks=5, squash=1.0):
    """Low-poly sphere as a lathe (squash scales the height)."""
    rings = []
    for j in range(stacks + 1):
        a = math.pi * j / stacks
        rr = max(radius * math.sin(a), radius * 0.02)
        rings.append((-radius * squash * math.cos(a), rr, rr))
    c = np.asarray(centre, float)
    return lathe(acc, layer, mat, c, (0.0, 1.0), rings, sides=sides, cap=True, bottom=True)
