"""Extension (c) (M37): building sanity.

  building_roof_only        building=roof footprints (no walls) - by design for wiaty/canopies, reported as
                            info so the leader can eyeball that each one is intentional;
  building_height_default   height_source == "default": the height is a generator guess, not OSM/LoD/BDOT;
  building_height_vs_storeys height_m / storeys outside the plausible storey band (WORKING_VALUE) - wrong
                            height for the tagged number of floors (BDOT storeys / OSM levels);
  building_in_carriageway   lives in overlaps.py (check 1).
"""

from __future__ import annotations

from .common import STOREY_H_MAX_M, STOREY_H_MIN_M, Finding, World


def check(w: World) -> list[Finding]:
    findings: list[Finding] = []
    for b in w.buildings:
        c = b["poly"].centroid
        if b.get("is_roof_only"):
            findings.append(Finding("building_roof_only", c.x, c.y, b["id"],
                                    "building=roof footprint (no walls) - verify it is an intentional canopy",
                                    severity="info", extra={"name": b.get("name")}))
        if b.get("height_source") == "default":
            findings.append(Finding("building_height_default", c.x, c.y, b["id"],
                                    f"height {b.get('height_m')} m from the default rule, not from OSM/LoD/BDOT",
                                    severity="info", extra={"height_m": b.get("height_m")}))
        h, st = b.get("height_m"), b.get("storeys")
        if h and st and float(st) >= 2:   # halls/warehouses with storeys=1: LoD height is not storey-based
            per = float(h) / float(st)
            if not (STOREY_H_MIN_M <= per <= STOREY_H_MAX_M):
                findings.append(Finding("building_height_vs_storeys", c.x, c.y, b["id"],
                                        f"height {float(h):.1f} m / {st} storeys = {per:.2f} m per storey, "
                                        f"outside [{STOREY_H_MIN_M}, {STOREY_H_MAX_M}] m",
                                        severity="warn",
                                        extra={"height_m": float(h), "storeys": st, "m_per_storey": round(per, 2)}))
    return findings
