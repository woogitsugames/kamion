"""ADR 0203 (D64): truck route Białystok (tile C, Andersa) -> Knyszyn (Rynek) from the pinned OSM extract.

    uv run --project tools/worldgen python tools/worldgen/qa/dk65_route_plan.py

Writes docs/reports/map/dk65_route_plan.json (+ .png overview): two route variants, the list of ways,
junctions, restrictions, construction/proposed roads near the route, administrative crossings and the
2048 m lattice tiles (anchored at tile C, regions.py) each variant passes through.

Variant A "old road"  : no highway=motorway(_link); ways with ref 65 preferred (cost x1, others x3).
Variant B "signed DK65": motorway allowed (in the 2026-11-08 extract ref 65 is on the open S19 section).
The pipeline's osm_extract.BBOX_WGS84 stops at lat 53.20 / lon 22.98, so this script parses the pbf itself
with its own bbox (corridor + Knyszyn); it does not touch the osm_extract cache.
"""

from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path

import networkx as nx
import osmium
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fetch_osm  # noqa: E402
import regions  # noqa: E402

REPO = fetch_osm.REPO_ROOT
OUT = REPO / "docs" / "reports" / "map" / "dk65_route_plan.json"
BBOX = (22.80, 53.08, 23.30, 53.38)  # lon/lat: tile C .. Knyszyn with margin
DRIVE = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential",
         "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link"}
START_NEAR = (778700.0, 596300.0)   # Andersa, east part of tile C, snapped to a ref=65 node
END_NEAR = (761037.0, 612399.0)     # OSM place=town Knyszyn node
ADMIN = ("Białystok", "Knyszyn", "gmina Knyszyn", "gmina Dobrzyniewo Duże", "powiat białostocki", "powiat moniecki")
LIMIT_TAGS = ("hgv", "maxweight", "maxweight:hgv", "maxheight", "maxaxleload", "maxlength", "access",
              "hgv:conditional", "maxweight:conditional")
C = regions.get("bialystok-industrial-c")
X0, Y0, T = C.bbox[0], C.bbox[1], regions.TILE_SIZE_M


def has65(tags: dict) -> bool:
    return "65" in tags.get("ref", "").split(";")


def load():
    tr = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    pbf = fetch_osm.cached_pbf()
    ways, nodes, rels = [], {}, {}
    for o in osmium.FileProcessor(str(pbf), osmium.osm.RELATION):
        t = o.tags
        if t.get("boundary") == "administrative" and t.get("name") in ADMIN:
            rels[(t["name"], t.get("admin_level", ""))] = dict(
                ways=[m.ref for m in o.members if m.type == "w"], teryt=t.get("teryt:terc", ""), id=o.id)
    bways = {w for r in rels.values() for w in r["ways"]}
    bgeo = {}
    for o in osmium.FileProcessor(str(pbf)).with_locations():
        if o.is_node():
            t = o.tags
            if (t.get("highway") in ("traffic_signals", "crossing") or t.get("railway") == "level_crossing") \
                    and BBOX[0] <= o.lon <= BBOX[2] and BBOX[1] <= o.lat <= BBOX[3]:
                nodes[o.id] = t.get("railway") or t.get("highway")
        elif o.is_way():
            if o.id in bways:
                try:
                    bgeo[o.id] = LineString([tr.transform(n.lon, n.lat) for n in o.nodes])
                except Exception:
                    pass
            if "highway" not in o.tags:
                continue
            try:
                pts = [(n.ref, n.lon, n.lat) for n in o.nodes]
            except Exception:
                continue
            if not any(BBOX[0] <= p[1] <= BBOX[2] and BBOX[1] <= p[2] <= BBOX[3] for p in pts):
                continue
            ways.append(dict(id=o.id, tags=dict(o.tags), nodes=[p[0] for p in pts], ts=str(o.timestamp)[:10],
                             xy=[tr.transform(p[1], p[2]) for p in pts]))
    admin = {}
    for k, r in rels.items():
        ps = list(polygonize(unary_union([bgeo[w] for w in r["ways"] if w in bgeo])))
        if ps:
            admin[k] = (unary_union(ps), r)
    return pbf, ways, nodes, admin


def graph(ways, allow_motorway: bool):
    g, xy = nx.DiGraph(), {}
    for w in ways:
        t = w["tags"]
        h = t.get("highway")
        if h not in DRIVE or (not allow_motorway and h in ("motorway", "motorway_link")):
            continue
        if t.get("access") in ("no", "private") or t.get("hgv") == "no":
            continue
        one = t.get("oneway") == "yes" or t.get("junction") in ("roundabout", "circular") or h == "motorway"
        rev = t.get("oneway") == "-1"
        k = 1.0 if has65(t) else 3.0
        for a, pa, b, pb in zip(w["nodes"], w["xy"], w["nodes"][1:], w["xy"][1:]):
            xy[a], xy[b] = pa, pb
            L = math.dist(pa, pb)
            if not rev:
                g.add_edge(a, b, L=L, c=L * k, w=w["id"])
            if rev or not one:
                g.add_edge(b, a, L=L, c=L * k, w=w["id"])
    return g, xy


def variant(ways, sig_nodes, admin, allow_motorway: bool) -> dict:
    wby = {w["id"]: w for w in ways}
    g, xy = graph(ways, allow_motorway)
    n65 = {u for u, v, d in g.edges(data=True) if has65(wby[d["w"]]["tags"])}
    start = min(n65, key=lambda n: math.dist(xy[n], START_NEAR))
    end = min(g, key=lambda n: math.dist(xy[n], END_NEAR))
    p = nx.shortest_path(g, start, end, weight="c")
    line = LineString([xy[n] for n in p])
    # node -> other drivable/service ways meeting the route there
    touch = collections.defaultdict(set)
    for w in ways:
        if w["tags"].get("highway") in DRIVE | {"service"}:
            for n in w["nodes"]:
                touch[n].add(w["id"])
    on_route = set()
    rows, km, junctions = [], 0.0, []
    for a, b in zip(p, p[1:]):
        e = g[a][b]
        on_route.add(e["w"])
    cum = {p[0]: 0.0}
    for a, b in zip(p, p[1:]):
        e = g[a][b]
        km += e["L"]
        cum[b] = km
        t = wby[e["w"]]["tags"]
        if rows and rows[-1]["way_id"] == e["w"]:
            rows[-1]["length_m"] += e["L"]
            rows[-1]["km_end"] = round(km / 1000, 3)
        else:
            rows.append(dict(way_id=e["w"], km_start=round((km - e["L"]) / 1000, 3), km_end=round(km / 1000, 3),
                             length_m=e["L"], highway=t.get("highway"), ref=t.get("ref", ""), name=t.get("name", ""),
                             lanes=t.get("lanes", ""), oneway=t.get("oneway", ""), junction=t.get("junction", ""),
                             maxspeed=t.get("maxspeed", ""), bridge=t.get("bridge", ""), layer=t.get("layer", ""),
                             limits={k: t[k] for k in LIMIT_TAGS if k in t}, osm_edit=wby[e["w"]]["ts"],
                             x=round(xy[a][0], 1), y=round(xy[a][1], 1)))
    for r in rows:
        r["length_m"] = round(r["length_m"], 1)
    for n in p[1:-1]:
        other = [wby[i] for i in touch[n] if i not in on_route]
        roads = sorted({(o["tags"]["highway"], o["tags"].get("ref", ""), o["tags"].get("name", "")) for o in other
                        if o["tags"]["highway"] != "service"})
        if roads or n in sig_nodes:
            junctions.append(dict(node=n, km=round(cum[n] / 1000, 3), x=round(xy[n][0], 1), y=round(xy[n][1], 1),
                                  control=sig_nodes.get(n, ""), roads=[list(r) for r in roads]))
    # roundabouts and bridges as merged stretches
    def stretches(pred):
        out = []
        for r in rows:
            if pred(r):
                if out and abs(out[-1]["km_end"] - r["km_start"]) < 1e-6:
                    out[-1]["km_end"] = r["km_end"]
                    out[-1]["ways"].append(r["way_id"])
                else:
                    out.append(dict(km_start=r["km_start"], km_end=r["km_end"], name=r["name"], x=r["x"], y=r["y"],
                                    ways=[r["way_id"]]))
        return out
    # class summary
    by = collections.Counter()
    for r in rows:
        by[f"{r['highway']}|{r['ref']}"] += r["length_m"]
    # admin crossings
    cross = {}
    for (name, lvl), (poly, rel) in admin.items():
        inter = line.intersection(poly.boundary)
        pts = [inter] if inter.geom_type == "Point" else [q for q in getattr(inter, "geoms", []) if q.geom_type == "Point"]
        cross[f"{name}|admin_level={lvl}"] = dict(teryt=rel["teryt"], relation=rel["id"], km=sorted(
            round(line.project(q) / 1000, 2) for q in pts), inside_km=round(line.intersection(poly).length / 1000, 2))
    # construction / proposed within 600 m
    cons = collections.defaultdict(lambda: dict(length_m=0.0, km_min=1e9, km_max=-1.0, last_edit="", ways=0))
    for w in ways:
        t = w["tags"]
        if t["highway"] in ("construction", "proposed"):
            gl = LineString(w["xy"])
            if gl.distance(line) < 600:
                k = f"{t['highway']}|{t.get('construction', t.get('proposed', ''))}|ref={t.get('ref', '')}"
                c = cons[k]
                c["length_m"] += gl.length
                c["ways"] += 1
                c["last_edit"] = max(c["last_edit"], w["ts"])
                for q in w["xy"]:
                    if Point(q).distance(line) < 600:
                        s = line.project(Point(q)) / 1000
                        c["km_min"], c["km_max"] = min(c["km_min"], s), max(c["km_max"], s)
    for c in cons.values():
        c.update(length_m=round(c["length_m"]), km_min=round(c["km_min"], 1), km_max=round(c["km_max"], 1))
    # lattice tiles
    tiles = collections.OrderedDict()
    for i in range(int(line.length) + 1):          # 1 m steps: seam positions are good to ~1 m
        q = line.interpolate(i)
        ij = (math.floor((q.x - X0) / T), math.floor((q.y - Y0) / T))
        t = tiles.setdefault(ij, [i / 1000, 0.0, [round(q.x, 1), round(q.y, 1)], None])
        t[1], t[3] = i / 1000, [round(q.x, 1), round(q.y, 1)]
    return dict(
        allow_motorway=allow_motorway, length_km=round(km / 1000, 3),
        start=dict(node=start, xy=[round(v, 1) for v in xy[start]]), end=dict(node=end, xy=[round(v, 1) for v in xy[end]]),
        length_by_class_m={k: round(v) for k, v in sorted(by.items(), key=lambda kv: -kv[1])},
        ways=rows, junctions=junctions, roundabouts=stretches(lambda r: r["junction"] in ("roundabout", "circular")),
        bridges=stretches(lambda r: bool(r["bridge"])), limits=[dict(way_id=r["way_id"], km=r["km_start"], **r["limits"])
                                                                 for r in rows if r["limits"]],
        admin_crossings=cross, construction_within_600m=dict(cons),
        tiles=[dict(ij=list(ij), bbox=[X0 + ij[0] * T, Y0 + ij[1] * T, X0 + (ij[0] + 1) * T, Y0 + (ij[1] + 1) * T],
                    km_in=round(a, 3), km_out=round(b, 3), route_m=round((b - a) * 1000), xy_in=qi, xy_out=qo)
               for ij, (a, b, qi, qo) in tiles.items()],
        polyline=[[round(v, 1) for v in xy[n]] for n in p],
    )


def render(plan: dict, ways, admin, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 11), dpi=110)
    for w in ways:
        h = w["tags"]["highway"]
        if h in ("motorway", "trunk", "primary", "secondary", "construction"):
            xs, ys = zip(*w["xy"])
            ax.plot(xs, ys, lw=0.6, color={"motorway": "#b03060", "construction": "#e08000"}.get(h, "#909090"),
                    ls="--" if h == "construction" else "-")
    for (name, lvl), (poly, _) in admin.items():
        if name in ("Białystok", "Knyszyn"):
            for g in getattr(poly, "geoms", [poly]):
                ax.plot(*g.exterior.xy, color="#3060a0", lw=0.8)
    for key, col in (("B_signed_dk65_via_s19", "#b03060"), ("A_old_road", "#107030")):
        v = plan["variants"][key]
        xs, ys = zip(*v["polyline"])
        ax.plot(xs, ys, lw=2.2, color=col, label=f"{key} {v['length_km']:.1f} km")
    for t in plan["variants"]["A_old_road"]["tiles"]:
        x0, y0, x1, y1 = t["bbox"]
        ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color="#202020", lw=0.7)
        ax.text(x0 + 60, y0 + 60, f"{t['ij'][0]},{t['ij'][1]}", fontsize=7)
    ax.set_aspect("equal")
    xs, ys = zip(*plan["variants"]["A_old_road"]["polyline"])
    ax.set_xlim(min(xs) - 2500, max(xs) + 2500)
    ax.set_ylim(min(ys) - 2500, max(ys) + 2500)
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title("ADR 0203: Białystok (kafel C) → Knyszyn; kafle 2048 m (i,j od kafla C); © OpenStreetMap contributors",
                 fontsize=9)
    fig.savefig(out, bbox_inches="tight")


def main() -> None:
    pbf, ways, sig, admin = load()
    plan = dict(
        generator="tools/worldgen/qa/dk65_route_plan.py", adr="0203", osm_extract=pbf.name,
        osm_sha256=fetch_osm.sha256_of(pbf), crs="EPSG:2180", lattice=dict(x0=X0, y0=Y0, size_m=T, anchor="bialystok-industrial-c"),
        variants=dict(A_old_road=variant(ways, sig, admin, False), B_signed_dk65_via_s19=variant(ways, sig, admin, True)),
        ref65_other=[dict(way_id=w["id"], highway=w["tags"]["highway"], proposed=w["tags"].get("proposed", ""),
                          construction=w["tags"].get("construction", ""), osm_edit=w["ts"],
                          a=[round(v) for v in w["xy"][0]], b=[round(v) for v in w["xy"][-1]],
                          length_m=round(LineString(w["xy"]).length))
                     for w in ways if has65(w["tags"]) and w["tags"]["highway"] in ("proposed", "construction")],
    )
    OUT.write_text(json.dumps(plan, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    render(plan, ways, admin, OUT.with_suffix(".png"))
    for k, v in plan["variants"].items():
        print(k, v["length_km"], "km;", len(v["ways"]), "ways;", len(v["junctions"]), "junction nodes;",
              len(v["roundabouts"]), "roundabouts;", len(v["bridges"]), "bridges; tiles", [t["ij"] for t in v["tiles"]])
        print("  classes", v["length_by_class_m"])
        print("  limits", v["limits"])
        print("  admin", {a: (c["teryt"], c["km"], c["inside_km"]) for a, c in v["admin_crossings"].items()})
    print("ref65 proposed/construction", plan["ref65_other"])


if __name__ == "__main__":
    main()
