"""ADR 0198: do the piers of the under-deck dressing (`viaduct_underdeck.json`) stand clear of the ground roads?

Runs without Data/raw and without Unity: the road stage of the generator (`roads.pipeline.build`: network, junction
plates, ribbons - the same code as build_world) is run on a FLAT ground model, because the plan position of the
roads does not depend on the terrain heights (checked: the open ranges of both Putry decks come out within 6 mm of
the committed spec of the full build). The pier rows are then produced by `streetscape.hero_bridge.build_spec` itself
(same call as `hero_bridge.plan`), and every column is tested twice:

  keepout      the generator's own rule (`hero_bridge.keepout`: a node of the rasterised ground footprint of the road
               layer within 2 nodes) -> `hero_bridge.BLOCKED_COLS`. NOT included here: the paved areas of the
               streetscape stage (yards, plots; they need the full build). The raw yard polygons near the viaduct
               are tested instead (`yard_m` >= YARD_CLEAR_M).
  carriageway  plan distance from the column footprint (col_len x col_wid rectangle) to the driven surface: road-layer
               footprint parts with a `road_*` material or `apron_sett` (the definition of
               `streetscape.furniture.pier_guardrails`, ADR 0117 / 0123). Required: >= CLEAR_M.

    uv run --project tools/worldgen python tools/worldgen/qa/check_piers_vs_roads.py --region bialystok-industrial-c \
        [--out artifacts/piers-0198/piers_vs_roads.json] [--stations NE=24.39,48.78 SW=19.5]

Exit code 1 when an active column fails one of the two tests. `--stations` prints the axis points (local E, N) of
stations given in metres from the north-west end of the open range of a deck - the form `pier_lines_en` takes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roads import pipeline                    # noqa: E402
from streetscape import hero_bridge as H      # noqa: E402
from terrain_mesh import conform as CF        # noqa: E402

REPO = Path(__file__).resolve().parents[3]
# WORKING_VALUE: free strip between a column face and the edge of the driven surface. The same 0.5 m that
# roads.standards uses for lamp columns ("skrajnia >= 0.5 m", LAMP_OFFSET); not a measured value of this object.
CLEAR_M = 0.5
# Paved areas are part of the keep-out mask of the full build (about 2.5 m, hero_bridge.keepout); their raw polygons
# are held to 3.0 m here because the final paved outline (streetscape.paved.collect) is not reproduced.
YARD_CLEAR_M = 3.0


def flat_world(region_id: str):
    """The road stage on a flat ground model (z = region origin). Takes about 100 s for bialystok-industrial-c."""
    region = pipeline.load_region(region_id)
    origin = (region["origin"]["x"], region["origin"]["y"])
    meta = json.loads((pipeline.REGIONS / region_id / "terrain.json").read_text(encoding="utf-8"))
    nx, ny = meta["samples"]
    hf = pipeline.P.Heightfield(np.full((ny, nx), float(region["origin"].get("z", 0.0))), meta["bbox"], origin)
    return pipeline.build(region_id, hf=hf)


def carriageway(parts, bounds):
    """Union of the driven ground surface inside bounds (xmin, ymin, xmax, ymax): shapely geometry."""
    import shapely
    from shapely.geometry import Polygon
    x0, y0, x1, y1 = bounds
    tris = []
    for p in parts:
        if p.layer != "road" or not p.footprint or not len(p.T) or p.src.endswith(":vg"):
            continue
        if not (p.mat.startswith("road_") or p.mat == "apron_sett"):
            continue
        v = p.V[:, :2]
        if v[:, 0].max() < x0 or v[:, 0].min() > x1 or v[:, 1].max() < y0 or v[:, 1].min() > y1:
            continue
        for t in v[p.T]:
            a, b = t[1] - t[0], t[2] - t[0]
            if abs(a[0] * b[1] - a[1] * b[0]) > 1e-9:
                tris.append(Polygon(t))
    return shapely.union_all(tris)


def yards(region_id: str, origin, bounds):
    """Raw paved-area polygons of the streetscape stage (BDOT10k squares, OSM parkings, `paved_area` overrides)
    that touch bounds, or None."""
    import shapely
    from shapely.geometry import Polygon, box
    from streetscape import paved as PV
    from streetscape import sources as SRC
    src = SRC.load(region_id)
    o = np.asarray(origin, float)
    ys = [PV._poly_local(f["geometry"]["coordinates"], tuple(origin)) for f in src["bdot10k"]["OT_PTPL_A"]
          if f["props"].get("materialnawierzchni") != "grunt naturalny"]
    ys += [PV._poly_local(a["geometry"]["coordinates"], tuple(origin)) for a in src["osm"]["areas"]
           if a["tags"].get("amenity") == "parking"]
    ys += [Polygon(np.asarray(v["polygon_epsg2180"], float) - o) for v in pipeline.load_overrides(region_id)
           if v.get("kind") == "paved_area"]
    near = [shapely.make_valid(p) for p in ys if p.intersects(box(*bounds))]
    return shapely.union_all(near) if near else None


def _footprint(q, t, prm):
    from shapely.geometry import Polygon
    t = np.asarray(t, float)
    n = np.array([-t[1], t[0]])
    hl, hw = prm["col_len_m"] / 2, prm["col_wid_m"] / 2
    q = np.asarray(q, float)[:2]
    return Polygon([q + t * a * hl + n * b * hw for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))])


def _rows(w, cfg, c, rows, blocked, car, yard):
    """Pier rows of deck chain c for the given authored rows (None = span rule): the generator's build_spec."""
    local = SimpleNamespace(net=SimpleNamespace(chains=[c]), region=w.region)
    H.BLOCKED_COLS.clear()
    spec = H.build_spec(local, cfg if rows is None else {**cfg, "set": {**cfg["set"], "pier_lines_en": rows}},
                        lambda e, n: 0.0, blocked)
    flagged = {tuple(q) for q in H.BLOCKED_COLS}
    dk, prm = spec["decks"][0], spec["params"]
    out = []
    for pr in dk["piers"]:
        st = H._station(c, pr["s"])
        cols = []
        for q in pr["cols"]:
            fp = _footprint(q, st["t"], prm)
            cols.append({"en": [q[0], q[1]], "carriageway_m": round(float(car.distance(fp)), 2),
                         "yard_m": None if yard is None else round(float(yard.distance(fp)), 2),
                         "keepout": bool(blocked(q[:2])) or (round(q[0], 1), round(q[1], 1)) in flagged})
        out.append({"s": pr["s"], "from_nw_end_m": round(pr["s"] - dk["s_open"][0], 2), "cols": cols})
    ends = [dk["s_open"][0]] + [r["s"] for r in out] + [dk["s_open"][1]]
    return {"chain": c.id, "s_open": dk["s_open"], "rows": out, "rows_dropped": spec["pier_lines_skipped"],
            "spans_m": [round(b - a, 2) for a, b in zip(ends, ends[1:])]}


def _bad(col):
    return (col["keepout"] or col["carriageway_m"] < CLEAR_M
            or (col["yard_m"] is not None and col["yard_m"] < YARD_CLEAR_M))


def check(region_id: str, w=None):
    """(report, world). `w` = a world from flat_world() to reuse."""
    w = w or flat_world(region_id)
    cfg = json.loads((pipeline.REGIONS / region_id / "viaduct_underdeck.json").read_text(encoding="utf-8"))
    chains = H._chains(w.net, {str(x) for x in cfg["target"]["osm_way"]})
    road = [p for p in w.buf.parts if p.layer == "road"]
    _, rmask = CF.rasterise(road, w.hf)
    blocked = H.keepout(w.hf, rmask)
    pts = np.concatenate([np.asarray(c.line.point(s), float)[None] for c in chains for s in H._run(c)])
    bounds = (pts[:, 0].min() - 40, pts[:, 1].min() - 40, pts[:, 0].max() + 40, pts[:, 1].max() + 40)
    car = carriageway(road, bounds)
    yard = yards(region_id, w.origin, bounds)
    held = cfg.get("pier_lines_en_held") or {}
    rep = {"schema": "truck-sim-pl/piers-vs-roads/1", "region": region_id, "id": cfg["id"], "clear_m": CLEAR_M,
           "ground_model": "flat (plan geometry only; no Data/raw)", "yards_near": yard is not None, "decks": []}
    for c in chains:
        rows = H.underdeck_rows(cfg, c)
        d = _rows(w, cfg, c, rows, blocked, car, yard)
        d["authored"] = rows is not None
        d["ways"] = sorted(H.chain_ways(c))
        d["failed"] = [[r["from_nw_end_m"], col["en"]] for r in d["rows"] for col in r["cols"] if _bad(col)]
        hk = sorted(k for k in held if str(k) in H.chain_ways(c))
        if hk:
            h = _rows(w, cfg, c, [list(map(float, q)) for q in held[hk[0]]], blocked, car, yard)
            d["held"] = [{"from_nw_end_m": r["from_nw_end_m"], "cols": r["cols"],
                          "still_blocked": any(_bad(col) for col in r["cols"])} for r in h["rows"]]
        rep["decks"].append(d)
    H.BLOCKED_COLS.clear()
    rep["ok"] = all(not d["failed"] and not d["rows_dropped"] for d in rep["decks"])
    return rep, w


def stations(w, cfg, spec: dict) -> dict:
    """{"<way id>": [[E, N], ...]} for {"<way id>": [metres from the north-west end of the open range, ...]}."""
    out = {}
    for c in H._chains(w.net, {str(x) for x in cfg["target"]["osm_way"]}):
        for k, ss in spec.items():
            if str(k) in H.chain_ways(c):
                s0 = H._open_range(c, *H._run(c))[0]
                out[str(k)] = [[round(float(v), 2) for v in c.line.point(s0 + s)] for s in ss]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--stations", nargs="*", default=[], metavar="WAY=s1,s2",
                    help="print the axis points of these stations (m from the NW end of the open range)")
    a = ap.parse_args(argv)
    rep, w = check(a.region)
    if a.stations:
        cfg = json.loads((pipeline.REGIONS / a.region / "viaduct_underdeck.json").read_text(encoding="utf-8"))
        want = {x.split("=")[0]: [float(v) for v in x.split("=")[1].split(",")] for x in a.stations}
        print(json.dumps(stations(w, cfg, want)))
    for d in rep["decks"]:
        print(f"{d['chain']}: {len(d['rows'])} rows ({'authored' if d['authored'] else 'span rule'}), "
              f"spans {d['spans_m']} m, max {max(d['spans_m'])} m")
        for r in d["rows"]:
            print(f"  +{r['from_nw_end_m']:7.2f} m  " + "  ".join(
                f"[{c['en'][0]:.1f}, {c['en'][1]:.1f}] carriageway {c['carriageway_m']:.2f} m"
                f"{' KEEPOUT' if c['keepout'] else ''}" for c in r["cols"]))
        for r in d.get("held", []):
            print(f"  held +{r['from_nw_end_m']:7.2f} m  " + "  ".join(
                f"carriageway {c['carriageway_m']:.2f} m{' KEEPOUT' if c['keepout'] else ''}" for c in r["cols"])
                + ("  -> still blocked" if r["still_blocked"] else "  -> FREE NOW: move the row to pier_lines_en"))
        if d["failed"] or d["rows_dropped"]:
            print(f"  FAILED columns: {d['failed']}; rows skipped or dropped: {d['rows_dropped']}")
    print("BLOCKED_COLS empty, all columns clear of the carriageway" if rep["ok"] else "NOT OK: a column on the keep-out or carriageway, or a row skipped")
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
