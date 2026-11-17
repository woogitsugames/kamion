"""Seam QA of the route-link joins (stream-gaps-s23): the built carriageway on both sides of every corridor seam that a
route link crosses, read off the generated chunk GLBs with the ADR 0233 tool (qa/seam_section.py: tris / locate / runs).

    uv run --project tools/worldgen python tools/worldgen/streaming/link_seams.py <out.json>

Per seam (corridor join whose exit or entry is a link): seam point = the graph boundary node of the joined road (the same
node id on both sides, `Bw<way>:...`), travel direction from that edge's geometry; on each side cross-sections 2 / 4 / 6 m
inside the tile (asphalt runs, edge lines), the asphalt axis height extrapolated to the seam, and the lateral offset of
the autopilot polyline (link / route point nearest the seam) from the OSM axis (left of travel = +).
Needs Data/Regions/<id>/generated/world_manifest.json + chunk GLBs (Data/raw/derived); a tile without them is reported
`built: false` (not a failure of the data: build_world not run on this machine).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
sys.path.insert(0, str(HERE))
import seam_section as SS  # noqa: E402
import route_links as RL  # noqa: E402

LINKS = RL.OUT


def _built(t: str) -> bool:
    m = REPO / "Data" / "Regions" / t / "generated" / "world_manifest.json"
    if not m.exists():
        return False
    ch = json.loads(m.read_text(encoding="utf-8"))["chunks"]
    return bool(ch) and (REPO / ch[0]["file"]).exists()


def _boundary_edge(t: str, sp):
    """Edge of tile t whose end node is the boundary node at sp: (unit direction pointing INTO the tile, node id)."""
    g = json.loads((REPO / "Data" / "Regions" / t / "roads.graph.json").read_text(encoding="utf-8"))
    best = None
    for e in g["edges"]:
        p = np.asarray(e["geometry"], float)[:, :2]
        for end, nxt in ((p[0], p[1]), (p[-1], p[-2])):
            d = float(np.linalg.norm(end - sp))
            if best is None or d < best[0]:
                v = nxt - end
                best = (d, v / np.linalg.norm(v), e["id"])
    return best


def _poly_near(link_or_route, origin, sp):
    pts = np.column_stack([link_or_route[0], link_or_route[1]]) + np.asarray(origin, float)
    i = int(np.argmin(np.linalg.norm(pts - sp, axis=1)))
    return pts[i]


def measure(links_json: Path = LINKS) -> dict:
    d = json.loads(links_json.read_text(encoding="utf-8"))
    tg = json.loads(RL.TG.OUT.read_text(encoding="utf-8"))
    anchors = {t["id"]: (t["anchorX"], t["anchorY"]) for t in tg["tiles"]}
    links = {L["id"]: L for L in d["links"]}
    out = {"seams": []}
    for c in d["corridors"]:
        for j in c["joins"]:
            if not (j["exit"].startswith("link:") or j["entry"].startswith("link:")):
                continue
            a, b = j["from"], j["to"]
            row = {"corridor": c["id"], "a": a, "b": b, "exit": j["exit"], "entry": j["entry"], "join_gap_m": j["gapM"],
                   "built": _built(a) and _built(b)}
            # seam point: nearest graph boundary node of tile a to the join point (both tiles share it)
            jp = np.array([j["x"], j["y"]])
            da_, va, ea = _boundary_edge(a, jp)
            db_, vb, eb = _boundary_edge(b, jp)
            g = json.loads((REPO / "Data" / "Regions" / a / "roads.graph.json").read_text(encoding="utf-8"))
            sp = min((np.array([n["x"], n["y"]]) for n in g["nodes"] if n.get("boundary")),
                     key=lambda p: float(np.linalg.norm(p - jp)))
            _, va, ea = _boundary_edge(a, sp)
            _, vb, eb = _boundary_edge(b, sp)
            row["seam_epsg2180"] = [round(float(sp[0]), 2), round(float(sp[1]), 2)]
            row["edges"] = [ea, eb]
            travel = -va                      # travel a -> b: out of a (va points into a) ...
            row["axis_kink_deg"] = round(float(np.degrees(np.arccos(np.clip(travel @ vb, -1, 1)))), 3)
            sides = {}
            for t, dirv, sign, key in ((a, travel, -1.0, j["exit"]), (b, vb, 1.0, j["entry"])):
                o = {"x": anchors[t][0], "y": anchors[t][1]}
                if key.startswith("link:"):
                    L = links[key[5:]]
                    poly = (L["e"], L["n"])
                else:
                    r = json.loads((REPO / "Data" / "Regions" / t / "route_start.json").read_text(encoding="utf-8"))
                    poly = ([p[0] for p in r["points_en"]], [p[1] for p in r["points_en"]])
                rp = _poly_near(poly, anchors[t], sp) - sp
                n = np.array([-dirv[1], dirv[0]]) if sign > 0 else np.array([-travel[1], travel[0]])
                s = {"route_lat": round(float(rp @ n), 3), "route_along": round(float(rp @ (travel if sign < 0 else dirv)), 3)}
                if row["built"]:
                    full = SS.measure_side(REPO, t, o, {"points_en": [[0.0, 0.0]]}, sign > 0, sp,
                                           travel if sign < 0 else dirv, sign)
                    full.pop("route_lat", None); full.pop("route_along", None)
                    s.update(full)
                sides[t] = s
            row["sides"] = sides
            if row["built"]:
                xa, xb = sides[a]["sections"][0], sides[b]["sections"][0]
                dif = lambda p, q: None if p is None or q is None else round(q - p, 3)
                row["delta"] = {"asphalt_width": dif(xa["asphalt_width"], xb["asphalt_width"]),
                                "edge_line_spacing": dif(xa["edge_line_spacing"], xb["edge_line_spacing"]),
                                "z_seam": dif(sides[a]["z_seam"], sides[b]["z_seam"])}
            row["delta_route_lat"] = round(sides[b]["route_lat"] - sides[a]["route_lat"], 3)
            out["seams"].append(row)
    return out


if __name__ == "__main__":
    res = measure()
    for r in res["seams"]:
        print(f"{r['a']}|{r['b']} seam {r['seam_epsg2180']} {r['exit']} -> {r['entry']} gap {r['join_gap_m']} kink {r['axis_kink_deg']} built {r['built']}")
        for t, s in r["sides"].items():
            x = s.get("sections", [{}])[0]
            print(f"   {t:18s} route_lat {s['route_lat']} along {s['route_along']} asphalt {x.get('asphalt')} lines {x.get('lines')} z_seam {s.get('z_seam')}")
        print("   delta", r.get("delta"), "route_lat", r["delta_route_lat"])
    if len(sys.argv) > 1:
        Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)
        Path(sys.argv[1]).write_text(json.dumps(res, indent=1), encoding="utf-8")
