"""D51 landmarks of a region: authored list (OSM ids + research references) -> derived presence check + 2D map.

Usage (repo root):
    uv run --project tools/worldgen python tools/worldgen/qa/region_landmarks.py --region bialystok-dojlidy

Input  : Data/Regions/<id>/landmarks_d51.authored.json  (authored: OSM way/node ids, names, reference files)
         Data/Regions/<id>/{region.yaml, roads.graph.json, buildings.geojson}, the Geofabrik extract of the region
         sources (Data/raw/osm, sha256 checked against Data/SourceManifests/osm-geofabrik-podlaskie.json)
Output : Data/Regions/<id>/generated/landmarks_d51.json  (derived: OSM geometry EPSG:2180, in-tile flag, our buildings
         whose centroid lies in the landmark polygon, height range, gate node on the road graph or not)
         docs/reports/map/<id>_landmarks.png  (own data only: roads graph, BDOT10k/OSM buildings, landmark outlines)

Nothing is guessed: a landmark whose OSM object is missing in the extract is reported "missing", a gate that is not a
graph node is reported "gate_not_in_graph" (the access road ends before the gate or the gate is not on a road way).
Deterministic: sorted inputs, fixed figure size / dpi, no timestamps in the JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import osmium  # noqa: E402
import shapely  # noqa: E402
import yaml  # noqa: E402
from pyproj import Transformer  # noqa: E402
from shapely.geometry import LineString, Point, Polygon, shape  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
SCHEMA = "kamion/region-landmarks/1"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class _Grab(osmium.SimpleHandler):
    def __init__(self, ways: set[int], nodes: set[int]):
        super().__init__()
        self.ways_want, self.nodes_want = ways, nodes
        self.ways, self.nodes = {}, {}

    def way(self, w):
        if w.id in self.ways_want:
            try:
                coords = [(n.lon, n.lat) for n in w.nodes]
            except osmium.InvalidLocationError:
                coords = []
            self.ways[w.id] = {"coords": coords, "tags": dict(w.tags), "version": w.version}

    def node(self, n):
        if n.id in self.nodes_want:
            self.nodes[n.id] = {"lonlat": (n.location.lon, n.location.lat), "tags": dict(n.tags), "version": n.version}


def build(region_id: str) -> dict:
    rdir = REPO / "Data" / "Regions" / region_id
    reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    bb = reg["bbox"]
    tile = Polygon([(bb["xmin"], bb["ymin"]), (bb["xmax"], bb["ymin"]), (bb["xmax"], bb["ymax"]), (bb["xmin"], bb["ymax"])])
    spec = json.loads((rdir / "landmarks_d51.authored.json").read_text(encoding="utf-8"))
    man = json.loads((REPO / "Data/SourceManifests/osm-geofabrik-podlaskie.json").read_text(encoding="utf-8"))
    pbf = REPO / man["local_path"]
    sha = _sha256(pbf)
    if sha != man["sha256"]:
        sys.exit(f"OSM extract sha256 mismatch: {sha} != manifest {man['sha256']}")
    ways = {lm["osm_way"] for lm in spec["landmarks"] if lm.get("osm_way")}
    nodes = {lm["gate_node"] for lm in spec["landmarks"] if lm.get("gate_node")}
    g = _Grab(ways, nodes)
    g.apply_file(str(pbf), locations=True)
    tr = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)

    graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    graph_nodes = {n["id"] for n in graph["nodes"]}
    bld = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))["features"]
    bgeo = [(f["properties"], shape(f["geometry"])) for f in bld]

    out = []
    for lm in sorted(spec["landmarks"], key=lambda d: d["id"]):
        rec = {k: lm[k] for k in ("id", "name", "kind", "references", "source_research") if k in lm}
        rec["provenance"] = "authored (landmark choice, research P6) + derived (geometry/matches from OSM + our data)"
        w = g.ways.get(lm.get("osm_way"))
        if w is None or len(w["coords"]) < 2:
            rec.update(status="missing", note="OSM way not in the extract (or without node locations)")
            out.append(rec)
            continue
        xy = [tr.transform(lon, lat) for lon, lat in w["coords"]]
        geom = Polygon(xy) if xy[0] == xy[-1] and len(xy) >= 4 else LineString(xy)
        if not geom.is_valid:
            geom = shapely.make_valid(geom)
        inter = geom.intersection(tile)
        rec["osm"] = {"way": lm["osm_way"], "version": w["version"],
                      "tags": {k: v for k, v in sorted(w["tags"].items()) if k in
                               ("name", "landuse", "building", "aeroway", "industrial", "operator", "addr:street",
                                "addr:housenumber", "man_made")}}
        rec["centroid_epsg2180"] = [round(geom.centroid.x, 2), round(geom.centroid.y, 2)]
        rec["area_m2"] = round(geom.area, 1)
        rec["in_tile_fraction"] = round(inter.area / geom.area, 3) if geom.area > 0 else (1.0 if inter.length else 0.0)
        # a building belongs to the landmark when its centroid lies inside or >= 50 % of its footprint overlaps
        hits = sorted((p for p, b in bgeo if geom.area > 0 and geom.intersects(b)
                       and (geom.contains(b.centroid) or geom.intersection(b).area >= 0.5 * b.area)),
                      key=lambda p: p["id"])
        rec["our_buildings"] = {"count": len(hits), "ids": [p["id"] for p in hits][:40],
                                "area_m2": round(sum(p["area_m2"] or 0 for p in hits), 1),
                                "height_m_range": ([min(p["height_m"] for p in hits), max(p["height_m"] for p in hits)]
                                                   if hits else None),
                                "height_sources": sorted({p["height_source"] for p in hits})}
        if lm.get("gate_node"):
            n = g.nodes.get(lm["gate_node"])
            gid = f"n{lm['gate_node']}"
            gate = {"node": lm["gate_node"], "in_graph": gid in graph_nodes}
            if n:
                gx, gy = tr.transform(*n["lonlat"])
                gate.update(version=n["version"], barrier=n["tags"].get("barrier"), access=n["tags"].get("access"),
                            epsg2180=[round(gx, 2), round(gy, 2)], in_tile=tile.contains(Point(gx, gy)))
            else:
                gate["missing_in_extract"] = True
            rec["gate"] = gate
        flags = []
        if rec["in_tile_fraction"] < 0.5:
            flags.append("mostly_outside_tile")
        if geom.area > 0 and not hits and "building" in w["tags"]:     # an OSM building with no footprint of ours
            flags.append("no_building_in_polygon")
        if rec.get("gate") and not rec["gate"]["in_graph"]:
            flags.append("gate_not_in_graph")
        rec["status"] = "ok" if not flags else "check"
        rec["flags"] = flags
        rec["_geom"] = geom
        out.append(rec)

    res = {"schema": SCHEMA, "region": region_id,
           "sources": {"osm_extract": man["local_path"], "osm_sha256": sha, "license": "ODbL 1.0, © OpenStreetMap contributors",
                       "buildings": f"Data/Regions/{region_id}/buildings.geojson"},
           "landmarks": out}
    return res, graph, bgeo, tile


def render(res, graph, bgeo, tile, png: Path):
    fig, ax = plt.subplots(figsize=(9, 9), dpi=110)
    x0, y0, x1, y1 = tile.bounds
    for _, b in bgeo:
        for poly in getattr(b, "geoms", [b]):
            ax.fill(*poly.exterior.xy, color="#b9b4aa", lw=0)
    for e in sorted(graph["edges"], key=lambda e: e["id"]):
        xs, ys = zip(*e["geometry"])
        hw = e["attrs"]["highway"]["v"]
        lw = 2.2 if hw in ("primary", "secondary", "trunk") else 1.2 if hw in ("tertiary", "residential", "unclassified") else 0.5
        ax.plot(xs, ys, color="#333333", lw=lw, solid_capstyle="round")
    for lm in res["landmarks"]:
        geom = lm.get("_geom")
        if geom is None:
            continue
        col = "#c0392b" if lm["status"] != "ok" else "#1f6fb2"
        for part in getattr(geom, "geoms", [geom]):
            if part.geom_type == "Polygon":
                ax.plot(*part.exterior.xy, color=col, lw=1.6)
            elif part.geom_type == "LineString":
                ax.plot(*part.xy, color=col, lw=1.6)
        cx, cy = lm["centroid_epsg2180"]
        cx, cy = min(max(cx, x0 + 60), x1 - 60), min(max(cy, y0 + 40), y1 - 40)
        ax.annotate(lm["id"], (cx, cy), fontsize=8, ha="center", color=col, weight="bold",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
        if lm.get("gate", {}).get("epsg2180"):
            gx, gy = lm["gate"]["epsg2180"]
            ax.plot(gx, gy, marker="s", ms=5, color="#2e8b57" if lm["gate"]["in_graph"] else "#c0392b")
    ax.plot(*tile.exterior.xy, color="black", lw=1, ls="--")
    ax.set_xlim(x0 - 50, x1 + 50)
    ax.set_ylim(y0 - 50, y1 + 50)
    ax.set_aspect("equal")
    ax.set_title(f"{res['region']}: D51 landmarks (blue ok / red check; square = gate, green on graph)\n"
                 "own data: OSM roads graph + BDOT10k/OSM footprints; EPSG:2180", fontsize=9)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, metadata={"Software": None})
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    a = ap.parse_args()
    res, graph, bgeo, tile = build(a.region)
    render(res, graph, bgeo, tile, REPO / "docs/reports/map" / f"{a.region}_landmarks.png")
    for lm in res["landmarks"]:
        lm.pop("_geom", None)
    p = REPO / "Data/Regions" / a.region / "generated" / "landmarks_d51.json"
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    for lm in res["landmarks"]:
        print(f"{lm['id']:<12} {lm['status']:<7} {','.join(lm.get('flags', []))} bld={lm.get('our_buildings', {}).get('count')}"
              f" tile={lm.get('in_tile_fraction')} {lm['name']}")


if __name__ == "__main__":
    main()
