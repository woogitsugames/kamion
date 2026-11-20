"""s8-north-s24 (owner D93 p.4 + D95 p.4, D63 "rough first"): the corridor north out of Bialystok towards Wasilkow and
Korycin - rough definition of its tiles on the 2048 m lattice of ADR 0203, in driving order from bialystok-industrial-c.

Why DK8 and not the S8: in the pinned OSM snapshot (podlaskie-261108.osm.pbf) the S8 ends at the junction Bialystok
Zachod (dk8-s8-jeroniki / dk65-01); the expressway north of dk65-02 (S19 Bialystok Ksiezyno - Bialystok Polnoc) is
`highway=construction` (lattice (-4,2), (-3,2), (-1,3), (0,3)), so the only drivable road towards Wasilkow / Korycin
is the DK8 (ref 8;19, Al. Tysiaclecia Panstwa Polskiego - Bialostocka) leaving tile C on its north seam. The tiles follow
that road: column i = 0 from j = 1 (seam with C) to j = 3 (junction Wasilkow, DK8 / DK19 split) and j = 4 (DK8 alone
towards Korycin, leaving on the west seam).

    uv run --project tools/worldgen python tools/worldgen/qa/dk8_north_plan.py                  # plan json (no network)
    uv run --project tools/worldgen python tools/worldgen/qa/dk8_north_plan.py --png            # + control render
    uv run --project tools/worldgen python tools/worldgen/qa/dk8_north_plan.py --print-regions  # regions.py entries
    uv run --project tools/worldgen python tools/worldgen/qa/dk8_north_plan.py --init-regions   # authored files (missing only)

Input: the pinned Geofabrik pbf (Data/SourceManifests/osm-geofabrik-podlaskie.json; ODbL) through osm_extract (same
snapshot as build_region.py) and the PRG powiat polygons (Data/Admin/powiaty_prg.geojson, powiaty.py). Deterministic:
no network, no clock.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import powiaty  # noqa: E402
import regions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
PLAN = REPO / "docs" / "reports" / "map" / "dk8_north_plan.json"
PNG = REPO / "docs" / "reports" / "map" / "dk8_north_plan.png"
REG = REPO / "Data" / "Regions"
C = regions.REGIONS["bialystok-industrial-c"]
X0, Y0, T = C.bbox[0], C.bbox[1], regions.TILE_SIZE_M
REF_RE = r"(?:^|;)8(?:;|$)"          # DK8 (also 8;19)
NMT_PIN = "2025"                     # = bialystok-industrial-c (gugik-nmt-2025-bialystok-industrial-c), chained north

# driving order: id, lattice i, j, entry edge, exit edge, title
TILES: list[tuple[str, int, int, str, str, str]] = [
    ("dk8-wasilkow-01", 0, 1, "S", "N",
     "DK8/DK19 Al. Tysiąclecia Państwa Polskiego na północ od kafla C, wylot z Białegostoku (Wysoki Stoczek, Dziesięciny)"),
    ("dk8-wasilkow-02", 0, 2, "S", "N",
     "DK8/DK19 Białostocka — Wasilków południe, węzeł Jurowiecka / Wasilkowska"),
    ("dk8-wasilkow-03", 0, 3, "S", "N",
     "Węzeł Wasilków — rozdział DK8 (Korycin, Augustów) i DK19 (Sokółka)"),
    ("dk8-korycin-01", 0, 4, "S", "W",
     "DK8 za Wasilkowem w stronę Korycina — wyjazd na zachodni szew"),
]


def tile_bbox(i: int, j: int) -> tuple[float, float, float, float]:
    return (X0 + i * T, Y0 + j * T, X0 + (i + 1) * T, Y0 + (j + 1) * T)


def edge_line(bb, edge: str) -> LineString:
    x0, y0, x1, y1 = bb
    return {"S": LineString([(x0, y0), (x1, y0)]), "N": LineString([(x0, y1), (x1, y1)]),
            "W": LineString([(x0, y0), (x0, y1)]), "E": LineString([(x1, y0), (x1, y1)])}[edge]


def crossings(roads, bb, edge: str) -> list[dict]:
    """DK8 trunk carriageways crossing one tile edge, with their direction relative to the tile (in / out)."""
    line = edge_line(bb, edge)
    sub = roads[roads["ref"].fillna("").str.contains(REF_RE, regex=True) & (roads["highway"] == "trunk")]
    out = []
    for _, r in sub.iterrows():
        g = r.geometry
        if not g.intersects(line):
            continue
        cs = list(g.coords)
        for a, b in zip(cs, cs[1:]):
            seg = LineString([a, b])
            p = seg.intersection(line)
            if p.is_empty or p.geom_type != "Point":
                continue
            inside_b = box(*bb).buffer(1e-6).contains(Point(b))
            out.append({"x": round(p.x, 1), "y": round(p.y, 1), "osm_way": int(r.osm_id), "ref": r["ref"],
                        "oneway": r["oneway"], "lanes": r["lanes"], "into_tile": bool(inside_b)})
    return sorted(out, key=lambda c: (c["x"], c["y"], c["osm_way"]))


def build_plan() -> dict:
    import osm_extract
    roads = osm_extract.load_layers()["roads"]
    tiles = []
    for tid, i, j, ein, eout, title in TILES:
        bb = tile_bbox(i, j)
        shares = powiaty.powiat_shares(bb)
        pw = sorted(shares, key=lambda k: (-shares[k], k))       # largest area share first = teryt_powiat
        cin = [c for c in crossings(roads, bb, ein) if c["into_tile"] and c["oneway"] == "yes"]
        cout = [c for c in crossings(roads, bb, eout) if not c["into_tile"] or c["oneway"] != "yes"]
        tiles.append({
            "id": tid, "ij": [i, j], "title": title, "bbox": list(bb),
            "origin": [bb[0] + T / 2, bb[1] + T / 2], "powiaty": pw,
            "powiat_shares": {k: round(v, 4) for k, v in sorted(shares.items())},
            "entry": {"edge": ein, "crossing": cin[0] if len(cin) == 1 else None, "candidates": cin},
            "exit": {"edge": eout, "crossing": cout[0] if len(cout) == 1 else None, "candidates": cout},
        })
    for a, b in zip(tiles, tiles[1:]):      # chained: exit of A == entry of B
        ea, eb = a["exit"]["crossing"], b["entry"]["crossing"]
        a["exit"]["joins_next"] = bool(ea and eb and ea["osm_way"] == eb["osm_way"]
                                       and abs(ea["x"] - eb["x"]) < 0.2 and abs(ea["y"] - eb["y"]) < 0.2)
    return {"schema": "truck-sim-pl/dk8-north-plan/1", "agent": "s8-north-s24",
            "source": "Data/SourceManifests/osm-geofabrik-podlaskie.json (pinned pbf) + Data/Admin/powiaty_prg.geojson",
            "lattice": {"x0": X0, "y0": Y0, "tile_m": T}, "nmt_pin": NMT_PIN, "tiles": tiles}


def print_regions(plan: dict) -> str:
    out = []
    for t in plan["tiles"]:
        pw = t["powiaty"]
        main, extra = pw[0], pw[1:]
        ex = f'\n        teryt_powiat_extra=({", ".join(repr(p) for p in extra)},),' if extra else ""
        i, j = t["ij"]
        out.append(f'''    "{t['id']}": Region(
        id="{t['id']}",
        title="{t['title']}",
        candidate="P_dk8_wasilkow",
        bbox=({t['bbox'][0]}, {t['bbox'][1]}, {t['bbox'][2]}, {t['bbox'][3]}),
        origin=({t['origin'][0]}, {t['origin'][1]}),
        teryt_powiat="{main}",{ex}
        status="WORKING_ASSUMPTION (s8-north-s24, owner D93/D95/D63; tile = lattice ({i},{j}) of the ADR 0203 plan)",
    ),''')
    return "\n".join(out).replace("'", '"')


def init_regions(plan: dict) -> list[str]:
    written = []
    for t in plan["tiles"]:
        d = REG / t["id"]
        d.mkdir(parents=True, exist_ok=True)
        a, b = t["entry"]["crossing"], t["exit"]["crossing"]
        files = {
            "overrides.yaml": (
                f"# Authored overrides of region {t['id']} (s8-north-s24, rough definition, D63: drivable first).\n"
                "# Every entry survives a re-import. Nothing checked on the orthophoto yet; generator rules apply.\n"
                "overrides: []\n"),
            "sources.authored.json": json.dumps({
                "provenance": "authored_override (s8-north-s24, mechanism of ADR 0209/0212): source pins of region "
                              f"{t['id']}, read by ingest.py and build_region.py",
                "pins": {"nmt_year": NMT_PIN},
                "reason": "The DK8 seam chain starts at bialystok-industrial-c, built from NMT 2025 "
                          "(gugik-nmt-2025-bialystok-industrial-c); the same series on every tile of the chain keeps "
                          "the terrain of the shared edges identical (ADR 0209).",
                "verify": "ingest.py exits with 'no NMT 1 m series fully covers the tile' when the 2025 series does "
                          "not cover the tile - then pin the year of the neighbour on the entry seam",
            }, ensure_ascii=False, indent=1) + "\n",
            "route_endpoints.json": json.dumps({
                "provenance": "authored_override (s8-north-s24): control route for cameras/QA = the DK8 through road",
                "description": f"DK8 carriageway in driving direction from the {t['entry']['edge']} tile edge (OSM way "
                               f"{a['osm_way']}) to the {t['exit']['edge']} tile edge (OSM way {b['osm_way']}); "
                               "points = edge crossings of the pinned pbf (tools/worldgen/qa/dk8_north_plan.py); "
                               "build_world snaps them to the nearest graph node.",
                "start_epsg2180": [a["x"], a["y"]], "end_epsg2180": [b["x"], b["y"]],
                "confidence": "high (crossings computed from the pinned pbf used by build_region.py)",
            }, ensure_ascii=False, indent=1) + "\n" if a and b else None,
        }
        for name, text in files.items():
            if text is not None and not (d / name).exists():
                (d / name).write_text(text, encoding="utf-8", newline="\n")
                written.append(f"{t['id']}/{name}")
    return written


def render_png(plan: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import osm_extract
    roads = osm_extract.load_layers()["roads"]
    xs = [t["bbox"][0] for t in plan["tiles"]] + [t["bbox"][2] for t in plan["tiles"]]
    ys = [t["bbox"][1] for t in plan["tiles"]] + [t["bbox"][3] for t in plan["tiles"]]
    win = box(min(xs) - T, min(ys) - T, max(xs) + T, max(ys) + 0.2 * T)
    sub = roads[roads.intersects(win)]
    fig, ax = plt.subplots(figsize=(8, 12), dpi=110)
    styles = {"trunk": ("#b5462e", 2.2), "trunk_link": ("#b5462e", 1.0), "construction": ("#999999", 1.0),
              "motorway": ("#3a5a9a", 2.4), "primary": ("#c98a2b", 1.4), "secondary": ("#c9b22b", 1.0),
              "tertiary": ("#777777", 0.8)}
    for _, r in sub.iterrows():
        c, w = styles.get(r.highway, ("#cccccc", 0.3))
        x, y = r.geometry.xy
        ax.plot(x, y, color=c, lw=w, zorder=2 if r.highway in styles else 1)
    for rid, reg in regions.REGIONS.items():
        bb = reg.bbox
        if box(*bb).intersects(win) and abs(bb[2] - bb[0] - T) < 1 and rid not in {t["id"] for t in plan["tiles"]}:
            ax.add_patch(plt.Rectangle(bb[:2], T, T, fill=False, ec="#4a7a4a", lw=1.0, ls="--"))
            ax.text(bb[0] + 40, bb[1] + 40, rid, fontsize=7, color="#4a7a4a", clip_on=True)
    for t in plan["tiles"]:
        bb = t["bbox"]
        ax.add_patch(plt.Rectangle(bb[:2], T, T, fill=False, ec="#1b1b1b", lw=1.6))
        ax.text(bb[0] + 40, bb[3] - 120, f"{t['id']} {tuple(t['ij'])}", fontsize=8, weight="bold")
        for k, m in (("entry", "o"), ("exit", "s")):
            c = t[k]["crossing"]
            if c:
                ax.plot(c["x"], c["y"], m, color="#1b1b1b", ms=6, zorder=5)
    ax.set_xlim(win.bounds[0], win.bounds[2])
    ax.set_ylim(win.bounds[1], win.bounds[3])
    ax.set_aspect("equal")
    ax.set_title("DK8 Białystok → Wasilków → Korycin: kafle s8-north-s24 (OSM pbf 2026-11-08, EPSG:2180)", fontsize=9)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(PNG)


def render_routes(plan: dict, out: Path) -> dict:
    """Control render of the BUILT tiles (own data only): graph edges of roads.graph.json + the control routes of
    route_start.json (rightmost lane centre) + C; returns route lengths and the gap between consecutive route ends."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ids = ["bialystok-industrial-c"] + [t["id"] for t in plan["tiles"]]
    fig, ax = plt.subplots(figsize=(7, 13), dpi=120)
    col = {"motorway": "#3a5a9a", "trunk": "#b5462e", "trunk_link": "#d07a5e", "primary": "#c98a2b",
           "secondary": "#c9b22b", "tertiary": "#777777"}
    info, ends = {}, []
    for rid in ids:
        d = REG / rid
        if not (d / "roads.graph.json").exists():
            continue
        g = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
        for e in g["edges"]:
            hw = e["attrs"]["highway"]["v"]
            x, y = zip(*e["geometry"])
            ax.plot(x, y, color=col.get(hw, "#c8c8c8"), lw=1.6 if hw in col else 0.4, zorder=2 if hw in col else 1)
        bb = g["bbox"] if isinstance(g["bbox"], list) else [g["bbox"][k] for k in ("xmin", "ymin", "xmax", "ymax")]
        ax.add_patch(plt.Rectangle(bb[:2], bb[2] - bb[0], bb[3] - bb[1], fill=False, ec="#1b1b1b", lw=1.0))
        ax.text(bb[0] + 30, bb[3] - 110, rid, fontsize=7, weight="bold")
        rp = d / "route_start.json"
        if rp.exists():
            r = json.loads(rp.read_text(encoding="utf-8"))
            ox, oy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            pts = [(e_ + ox, n_ + oy) for e_, n_ in r["points_en"]]
            ax.plot(*zip(*pts), color="#1f6fd1", lw=2.4, zorder=4)
            info[rid] = {"length_m": r["length_m"], "start": [round(v, 2) for v in pts[0]],
                         "end": [round(v, 2) for v in pts[-1]]}
            ends.append((rid, pts[0], pts[-1]))
    for (a, _, ea), (b, sb, _) in zip(ends, ends[1:]):
        info[b]["gap_from_prev_end_m"] = round(((ea[0] - sb[0]) ** 2 + (ea[1] - sb[1]) ** 2) ** 0.5, 2)
    ax.set_aspect("equal")
    ax.set_title("s8-north-s24: zbudowane kafle, graf dróg i trasy kontrolne (dane własne, EPSG:2180)", fontsize=8)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    return info


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--print-regions", action="store_true")
    ap.add_argument("--init-regions", action="store_true")
    ap.add_argument("--routes-png", type=Path, help="control render of the built tiles + routes to this file")
    a = ap.parse_args()
    plan = build_plan()
    if a.routes_png:
        print(json.dumps(render_routes(plan, a.routes_png), indent=1))
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for t in plan["tiles"]:
        print(t["id"], t["ij"], t["powiaty"], "entry", t["entry"]["crossing"], "exit", t["exit"]["crossing"],
              "joins_next", t["exit"].get("joins_next"))
    if a.print_regions:
        print(print_regions(plan))
    if a.init_regions:
        print("written", init_regions(plan))
    if a.png:
        render_png(plan)
        print("png", PNG.relative_to(REPO))


if __name__ == "__main__":
    main()
