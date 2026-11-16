"""Swept path (tor śladu) of the tractor + 13.6 m semitrailer through a single-lane roundabout (ADR 0218).

Low-speed kinematic model (no tyre slip, valid at roundabout speeds < ~20 km/h): the centre of the tractor front axle
follows a drawn path exactly; the tractor rear axle follows it as a tractrix at the wheelbase L1; the kingpin sits
`fifth_wheel_lead` ahead of the tractor rear axle; the (effective) trailer axle follows the kingpin as a tractrix at
L2. Every tyre edge and body corner is tracked; the result is the radius envelope about the roundabout centre.

Steady state on a circle (closed form, used as a cross-check by the tests):
    R1 = tractor rear-axle radius, front-axle radius Rf = sqrt(R1^2 + L1^2)
    kingpin radius        Rk = sqrt(R1^2 + c^2)          (c = kingpin lead ahead of the rear axle)
    trailer-axle radius   R2 = sqrt(Rk^2 - L2^2)         (exists only for Rk > L2)
    off-tracking          Rf - R2

Vehicle data: art-source/truck/dims.json + game/.../Definitions/Data/*.json (values and statuses quoted in ADR 0218).
Run as a script for the ADR 0218 tables:  uv run --project tools/worldgen python tools/worldgen/roads/swept_path.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Combination:
    """Tractor 4x2 + tridem curtainsider (art-source/truck/dims.json, tractor_4x2_generic.vehicle.json,
    curtainsider_tridem_13_6.trailer.json). Lengths in m, from the tractor rear axle / the kingpin."""
    L1: float = 3.70                 # tractor wheelbase (dims.json wheelbase_m, WORKING_VALUE; vehicle.json axle z 3.7)
    front_overhang: float = 1.45     # front axle -> front face (WORKING_VALUE)
    rear_overhang: float = 0.80      # rear axle -> frame end (WORKING_VALUE)
    cab_half_w: float = 1.245        # cab width 2.49 / 2 (WORKING_VALUE)
    front_track: float = 2.04        # wheel centres (WORKING_VALUE)
    front_tyre_w: float = 0.315      # 315/80 R22.5 (DERIVED from the designation)
    rear_outer_half: float = 1.24    # outer tyre edges of the drive duals 2.48 / 2 (WORKING_VALUE)
    rear_inner_half: float = 0.58    # inner tyre edge of the duals: 1.82/2 - 0.34/2 - 0.315/2 (DERIVED)
    c: float = 0.68                  # fifth_wheel_lead_m: kingpin ahead of the tractor rear axle (WORKING_VALUE)
    max_steer_deg: float = 40.0      # vehicle.json steering.maxRoadWheelAngleDeg (WORKING_VALUE)
    kp_front: float = 1.60           # kingpin -> trailer front (DERIVED, dims.json)
    kp_rear: float = 12.00           # kingpin -> trailer rear (SOURCED, 96/53/EC Annex I 1.6)
    trailer_half_w: float = 1.275    # 2.55 / 2 (SOURCED limit, 96/53/EC Annex I 1.2)
    trailer_axles: tuple = (6.32, 7.63, 8.94)   # kingpin -> axles (trailer.json, D79/ADR 0280: 7,63 m SOURCED), none steered
    trailer_track: float = 2.04      # wheel centres (WORKING_VALUE)
    trailer_tyre_w: float = 0.385    # 385/65 R22.5 (DERIVED)
    L2: float | None = None          # effective trailer wheelbase; None = middle axle of the tridem (ESTIMATED)

    @property
    def l2(self) -> float:
        return self.L2 if self.L2 is not None else self.trailer_axles[1]

    @property
    def length(self) -> float:
        return self.front_overhang + self.L1 - self.c + self.kp_rear


def steady_state(R1: float, v: Combination = Combination()) -> dict:
    """Closed-form radii (centre lines) for a tractor rear-axle radius R1 on an endless circle."""
    Rf = math.hypot(R1, v.L1)
    Rk = math.hypot(R1, v.c)
    R2 = math.sqrt(Rk * Rk - v.l2 * v.l2) if Rk > v.l2 else 0.0
    return {"R1": R1, "Rf": Rf, "Rk": Rk, "R2": R2, "offtrack": Rf - R2,
            "front_outer_tyre": math.hypot(R1 + v.front_track / 2 + v.front_tyre_w / 2, v.L1),
            "front_outer_corner": math.hypot(R1 + v.cab_half_w, v.L1 + v.front_overhang),
            "trailer_inner_tyre": R2 - v.trailer_track / 2 - v.trailer_tyre_w / 2,
            "steer_deg": math.degrees(math.atan2(v.L1, R1))}


# ------------------------------------------------------------------------------------------------ path geometry
@dataclass
class RoundaboutPath:
    """Front-axle path through a 4-arm roundabout centred at (0, 0), traffic counter-clockwise (right-hand traffic).
    Entry arm from the south; `turn_deg` = 90 right, 180 straight on, 270 left, 360 U-turn."""
    Rp: float                 # radius of the front-axle path on the ring
    turn_deg: float = 180.0
    lane_off: float = 1.75    # entry / exit lane centre right of the arm axis (WORKING_VALUE: 3.5 m lane)
    Re: float = 12.0          # front-axle path radius of the entry curve (WORKING_VALUE)
    Rx: float = 14.0          # ... of the exit curve (WORKING_VALUE)
    lead_in: float = 60.0     # straight approach (the combination starts straight)
    lead_out: float = 30.0
    step: float = 0.02
    pts: np.ndarray = field(init=False)
    phase: np.ndarray = field(init=False)     # 0 approach, 1 entry curve, 2 ring, 3 exit curve, 4 leave

    def __post_init__(self):
        a, Rp, Re, Rx, h = self.lane_off, self.Rp, self.Re, self.Rx, self.step
        ye = -math.sqrt((Rp + Re) ** 2 - (a + Re) ** 2)
        ce = np.array([a + Re, ye])
        seg, ph = [], []

        def line(p0, p1, k):
            n = max(2, int(math.ceil(np.linalg.norm(p1 - p0) / h)))
            t = np.linspace(0, 1, n, endpoint=False)
            seg.append(p0 + (p1 - p0) * t[:, None])
            ph.append(np.full(n, k))

        def arc(c, r, a0, a1, k):
            n = max(2, int(math.ceil(abs(a1 - a0) * r / h)))
            t = np.linspace(a0, a1, n, endpoint=False)
            seg.append(c + r * np.column_stack([np.cos(t), np.sin(t)]))
            ph.append(np.full(n, k))

        line(np.array([a, ye - self.lead_in]), np.array([a, ye]), 0)
        ae1 = math.atan2(-ce[1], -ce[0])               # tangent point on the ring, seen from the entry centre
        arc(ce, Re, math.pi, ae1, 1)                   # right turn = clockwise
        phi_e = math.atan2(ce[1], ce[0])
        # exit built for an arm pointing north, then rotated to the exit arm direction
        yx = math.sqrt((Rp + Rx) ** 2 - (a + Rx) ** 2)
        cx_loc = np.array([a + Rx, yx])
        psi = math.radians(-90.0 + self.turn_deg)
        rot = psi - math.pi / 2
        R = np.array([[math.cos(rot), -math.sin(rot)], [math.sin(rot), math.cos(rot)]])
        cx = R @ cx_loc
        phi_x = math.atan2(cx[1], cx[0])
        while phi_x <= phi_e + 1e-6:
            phi_x += 2 * math.pi
        if self.turn_deg >= 359.0 and phi_x - phi_e < math.pi:
            phi_x += 2 * math.pi
        arc(np.zeros(2), Rp, phi_e, phi_x, 2)
        ax0 = math.atan2(-cx_loc[1], -cx_loc[0]) + rot
        arc(cx, Rx, ax0, ax0 - (ax0 - (-math.pi + rot)) % (2 * math.pi), 3)
        p_out = R @ np.array([a, yx])
        d_out = np.array([math.cos(psi), math.sin(psi)])
        line(p_out, p_out + d_out * self.lead_out, 4)
        seg.append((p_out + d_out * self.lead_out)[None, :])
        ph.append(np.array([4]))
        self.pts = np.vstack(seg)
        self.phase = np.concatenate(ph)
        self.ring_arc_deg = math.degrees(phi_x - phi_e)


# ------------------------------------------------------------------------------------------------ simulation
def _unit(v):
    return v / np.linalg.norm(v)


def simulate(path: RoundaboutPath, v: Combination = Combination()) -> dict:
    """Tractrix integration along the front-axle path. Returns radius envelopes about the roundabout centre."""
    P = path.pts
    t0 = _unit(P[1] - P[0])
    pr = P[0] - t0 * v.L1                       # straight start: everything aligned with the approach
    pk = pr + t0 * v.c
    pt = pk - t0 * v.l2
    th = v.trailer_track / 2 + v.trailer_tyre_w / 2          # outer edge of a trailer tyre
    ti = v.trailer_track / 2 - v.trailer_tyre_w / 2
    fo = v.front_track / 2 + v.front_tyre_w / 2
    fi = v.front_track / 2 - v.front_tyre_w / 2
    out = {"tyre_min_r": np.inf, "tyre_min_r_trailer": np.inf, "tyre_min_r_tractor": np.inf,
           "tyre_max_r_ring": 0.0, "body_max_r_ring": 0.0, "body_min_r": np.inf,
           "steer_max_deg": 0.0, "artic_max_deg": 0.0}
    for i in range(1, len(P)):
        pf = P[i]
        u1 = _unit(pf - pr)
        pr = pf - u1 * v.L1
        pk = pr + u1 * v.c
        u2 = _unit(pk - pt)
        pt = pk - u2 * v.l2
        tan = _unit(P[i] - P[i - 1])
        n1 = np.array([-u1[1], u1[0]])
        n2 = np.array([-u2[1], u2[0]])
        steer = math.degrees(math.atan2(u1[0] * tan[1] - u1[1] * tan[0], float(u1 @ tan)))
        art = math.degrees(math.atan2(u1[0] * u2[1] - u1[1] * u2[0], float(u1 @ u2)))
        out["steer_max_deg"] = max(out["steer_max_deg"], abs(steer))
        out["artic_max_deg"] = max(out["artic_max_deg"], abs(art))
        # tyres: (centre point, lateral normal, inner/outer half offsets)
        tyres = [(pf, n1, fi, fo), (pr, n1, v.rear_inner_half, v.rear_outer_half)]
        tyres_t = [(pk - u2 * d, n2, ti, th) for d in v.trailer_axles]
        rmin_trac = min(np.linalg.norm(c + s * n * o) for c, n, a_, b_ in tyres for s in (1, -1) for o in (a_, b_))
        rmin_trl = min(np.linalg.norm(c + s * n * o) for c, n, a_, b_ in tyres_t for s in (1, -1) for o in (a_, b_))
        out["tyre_min_r_tractor"] = min(out["tyre_min_r_tractor"], rmin_trac)
        out["tyre_min_r_trailer"] = min(out["tyre_min_r_trailer"], rmin_trl)
        cab_f, cab_r = pr + u1 * (v.L1 + v.front_overhang), pr - u1 * v.rear_overhang
        tr_f, tr_r = pk + u2 * v.kp_front, pk - u2 * v.kp_rear
        body = [cab_f + n1 * v.cab_half_w, cab_f - n1 * v.cab_half_w, cab_r + n1 * v.cab_half_w, cab_r - n1 * v.cab_half_w,
                tr_f + n2 * v.trailer_half_w, tr_f - n2 * v.trailer_half_w, tr_r + n2 * v.trailer_half_w,
                tr_r - n2 * v.trailer_half_w]
        out["body_min_r"] = min(out["body_min_r"], min(np.linalg.norm(b) for b in body))
        if path.phase[i] == 2:          # front axle on the ring: outer envelope against the outer kerb
            # at < 20 km/h the trailer tracks inside the tractor: the outer envelope is the tractor front (outer
            # front tyre, front cab corners); trailer points still on the approach arm are not on the ring
            out["tyre_max_r_ring"] = max(out["tyre_max_r_ring"], max(np.linalg.norm(pf + s * n1 * fo) for s in (1, -1)))
            out["body_max_r_ring"] = max(out["body_max_r_ring"], max(np.linalg.norm(b) for b in body[:2]))
    out["tyre_min_r"] = min(out["tyre_min_r_tractor"], out["tyre_min_r_trailer"])
    out["ring_arc_deg"] = path.ring_arc_deg
    return out


def required(R_ext: float, turn_deg: float, kerb_margin: float = 0.50, v: Combination = Combination(), **kw) -> dict:
    """Driver keeps the outer front tyre `kerb_margin` inside the outer kerb (radius R_ext). Returns the envelope and
    the traversable inner radius the combination needs (tyres) for one manoeuvre."""
    Rp = R_ext - kerb_margin - v.front_track / 2 - v.front_tyre_w / 2
    r = simulate(RoundaboutPath(Rp=Rp, turn_deg=turn_deg, **kw), v)
    r.update({"R_ext": R_ext, "Rp": Rp, "turn_deg": turn_deg,
              "swept_width_tyres": R_ext - r["tyre_min_r"],
              "outer_body_over_kerb": r["body_max_r_ring"] - R_ext})
    return r


# Knyszyn DK65 x DW671 (OSM way 1426801304): arm bearings from the ring centre (roads.graph.json of region knyszyn,
# E = 0, N = 90): Obozowa S -61, Tykocka E 37, Obozowa N 113, Tykocka W -139. Entry from Obozowa S (from Bialystok):
# Tykocka E = 98 deg of turn (route to Rynek), Obozowa N = 174, Tykocka W = 282; return Rynek -> Bialystok = entry
# Tykocka E, exit Obozowa S = 262 deg.
TURNS = {"w prawo 98° (trasa do Rynku)": 98.0, "na wprost 174°": 174.0, "w lewo 262° (powrót Rynek→Białystok)": 262.0,
         "w lewo 282°": 282.0, "zawracanie 360°": 360.0}
ISLAND_CLEARANCE = 0.25      # WORKING_VALUE: tyre edge to the island kerb face
APRON_LIP_MAX = 0.05         # WORKING_VALUE: highest mountable apron lip modelled


def apron_needed(R_ext: float, ring_w: float, turn_deg: float, **kw) -> dict:
    """Width of a traversable apron inside a ring of asphalt width ring_w so that every tyre stays clear of the
    island kerb (ISLAND_CLEARANCE)."""
    r = required(R_ext, turn_deg, **kw)
    island_r_max = r["tyre_min_r"] - ISLAND_CLEARANCE
    return {**r, "ring_w": ring_w, "island_r_max": island_r_max,
            "apron_w_needed": max(0.0, (R_ext - ring_w) - island_r_max)}


def main():
    v = Combination()
    print(f"combination length {v.length:.2f} m (dims.json artic_length_m 16.47), L1 {v.L1}, c {v.c}, L2 {v.l2}")
    print("\nsteady state (closed form), front outer tyre on R:")
    for R1 in (6.0, 8.0, 8.34, 10.0):
        ss = steady_state(R1, v)
        print("  " + "  ".join(f"{k} {val:.2f}" for k, val in ss.items()))
    print("\n| R_ext | ring asphalt | manoeuvre | ring arc ° | max steer ° | max artic ° | min tyre r (trailer / tractor) |"
          " outer front tyre r | cab corner r | island r max | apron needed |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for R_ext, ring_w in ((10.8, 4.0), (11.3, 5.0), (11.8, 6.0), (13.0, 6.0)):
        for name, t in TURNS.items():
            r = apron_needed(R_ext, ring_w, t)
            print(f"| {R_ext:.2f} | {ring_w:.1f} | {name} | {r['ring_arc_deg']:.0f} | {r['steer_max_deg']:.1f} | "
                  f"{r['artic_max_deg']:.1f} | {r['tyre_min_r']:.2f} ({r['tyre_min_r_trailer']:.2f} / "
                  f"{r['tyre_min_r_tractor']:.2f}) | {r['tyre_max_r_ring']:.2f} | {r['body_max_r_ring']:.2f} | "
                  f"{r['island_r_max']:.2f} | {r['apron_w_needed']:.2f} |")
    print("\nsensitivity, R_ext 11.30, left 262 deg (min tyre radius):")
    base = required(11.3, 262.0)["tyre_min_r"]
    print(f"  base {base:.2f}")
    print(f"  L2 8.00 (tridem equivalent wheelbase longer than the middle axle): {required(11.3, 262.0, v=Combination(L2=8.0))['tyre_min_r']:.2f}")
    print(f"  kerb margin 0.30: {required(11.3, 262.0, kerb_margin=0.3)['tyre_min_r']:.2f}; 0.80: {required(11.3, 262.0, kerb_margin=0.8)['tyre_min_r']:.2f}")
    print(f"  entry/exit radius 10/12: {required(11.3, 262.0, Re=10.0, Rx=12.0)['tyre_min_r']:.2f}; 15/18: {required(11.3, 262.0, Re=15.0, Rx=18.0)['tyre_min_r']:.2f}")


if __name__ == "__main__":
    main()
