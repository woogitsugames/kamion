"""ADR 0220: route chainage (km) of the DK65 truck route -> region-local coordinates and side.

Pikietaż (kilometrage) used by research K1 (`research/dk65-knyszyn-refs/README.md`) and by ADR 0203/0205/0207:
"km trasy" = distance along `variants.A_old_road.polyline` of `docs/reports/map/dk65_route_plan.json` (EPSG:2180,
the OSM nodes of variant A, rounded to 0.1 m), measured from the start of variant A (OSM node 3341716402, Andersa in
tile C, (778302.0, 595649.3)) and growing towards Knyszyn. The tile table of the plan (`tiles[*].km_in/km_out`) and
the K1 sample points (`research/dk65-knyszyn-refs/data/km_points.json`) use the same chainage.
DK65 milestones (OSM highway=milestone ref=65) count the other way: DK65 km ~= 170.05 - km trasy (K1, ESTIMATED).

Side: K1 "L" / "P" = left / right of the axis in the direction of growing km (Białystok -> Knyszyn).
Region-local frame: E = x - origin.x, N = y - origin.y (EPSG:2180); Unity X = E, Z = N (ADR 0003).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
PLAN = REPO / "docs" / "reports" / "map" / "dk65_route_plan.json"
SIDES = {"L": 1.0, "P": -1.0}        # sign of the LEFT normal (direction of growing km)


@dataclass(frozen=True)
class Station:
    km: float
    x: float          # EPSG:2180
    y: float
    tx: float         # unit tangent, direction of growing km
    ty: float

    @property
    def left(self):
        return (-self.ty, self.tx)


class RouteKm:
    """Chainage along a polyline (EPSG:2180)."""

    def __init__(self, polyline):
        p = np.asarray(polyline, float)
        if p.ndim != 2 or len(p) < 2:
            raise ValueError("polyline needs >= 2 points")
        seg = np.hypot(*np.diff(p, axis=0).T)
        keep = np.concatenate([[True], seg > 1e-6])
        self.p = p[keep]
        self.s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(self.p, axis=0).T))])

    @classmethod
    def from_plan(cls, path: Path = PLAN, variant: str = "A_old_road") -> "RouteKm":
        plan = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(plan["variants"][variant]["polyline"])

    @property
    def length_km(self) -> float:
        return float(self.s[-1]) / 1000.0

    def at(self, km: float) -> Station:
        """Point and tangent at `km` (clamped to the route)."""
        s = min(max(float(km) * 1000.0, 0.0), float(self.s[-1]))
        i = int(np.clip(np.searchsorted(self.s, s, side="right") - 1, 0, len(self.s) - 2))
        a, b = self.p[i], self.p[i + 1]
        L = float(self.s[i + 1] - self.s[i])
        f = (s - float(self.s[i])) / L
        t = (b - a) / L
        q = a + f * (b - a)
        return Station(km=s / 1000.0, x=float(q[0]), y=float(q[1]), tx=float(t[0]), ty=float(t[1]))

    def point(self, km: float, side: str | None = None, offset_m: float = 0.0):
        """EPSG:2180 point `offset_m` from the axis on `side` ("L" / "P"; None = on the axis)."""
        st = self.at(km)
        sg = SIDES[side] if side else 0.0
        lx, ly = st.left
        return st.x + sg * offset_m * lx, st.y + sg * offset_m * ly

    def locate(self, x: float, y: float):
        """(km, lateral) of the nearest point of the route; lateral > 0 = left ("L"), < 0 = right ("P")."""
        q = np.array([x, y], float)
        a, b = self.p[:-1], self.p[1:]
        d = b - a
        L2 = np.einsum("ij,ij->i", d, d)
        f = np.clip(np.einsum("ij,ij->i", q - a, d) / L2, 0.0, 1.0)
        c = a + f[:, None] * d
        dist = np.hypot(*(q - c).T)
        i = int(np.argmin(dist))
        s = float(self.s[i] + f[i] * math.sqrt(L2[i]))
        cross = d[i, 0] * (q[1] - a[i, 1]) - d[i, 1] * (q[0] - a[i, 0])
        return s / 1000.0, math.copysign(float(dist[i]), cross) if dist[i] > 0 else 0.0


def region_origin(region_id: str):
    import yaml
    r = yaml.safe_load((REPO / "Data" / "Regions" / region_id / "region.yaml").read_text(encoding="utf-8"))
    return float(r["origin"]["x"]), float(r["origin"]["y"]), r["bbox"]


def km_to_region(region_id: str, km: float, side: str | None = None, offset_m: float = 0.0,
                 route: RouteKm | None = None) -> dict:
    """km (+ side, lateral offset) -> region-local E/N (= Unity x/z), the side sign and whether it is inside the tile.

    Returns {"x", "z", "e", "n", "side", "sign", "inside", "tangent_en", "epsg2180"}."""
    route = route or RouteKm.from_plan()
    ox, oy, bb = region_origin(region_id)
    x, y = route.point(km, side, offset_m)
    st = route.at(km)
    inside = bb["xmin"] <= x <= bb["xmax"] and bb["ymin"] <= y <= bb["ymax"]
    e, n = x - ox, y - oy
    return {"x": round(e, 3), "z": round(n, 3), "e": round(e, 3), "n": round(n, 3), "side": side,
            "sign": SIDES[side] if side else 0.0, "inside": bool(inside),
            "tangent_en": (round(st.tx, 6), round(st.ty, 6)), "epsg2180": (round(x, 2), round(y, 2))}


def tile_of_km(km: float, path: Path = PLAN, variant: str = "A_old_road") -> str | None:
    """Region id of the tile that holds `km` (from the plan's tile table and the known region bboxes)."""
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    route = RouteKm(plan["variants"][variant]["polyline"])
    x, y = route.point(km)
    for d in sorted((REPO / "Data" / "Regions").iterdir()):
        f = d / "region.yaml"
        if not f.exists():
            continue
        _, _, bb = region_origin(d.name)
        if bb["xmin"] <= x < bb["xmax"] and bb["ymin"] <= y < bb["ymax"]:
            return d.name
    return None
