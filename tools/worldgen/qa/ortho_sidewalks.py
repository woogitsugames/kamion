"""Sidewalks attached to the kerb of a through road, read off the tile's GUGiK orthophoto -> report + generated
overrides (ADR 0349). OSM carries no `sidewalk=*` on DW671 through the villages (pbf 2026-11-08: the graph of
dw671-tykocin-03 has highway / surface / lanes / ref only) and maps no footway there, so the generator laid a kerb with
grass behind it on both sides: the street read as a bare wide avenue (critic of build #8, frame t2590).

  measure: uv run --project tools/worldgen python tools/worldgen/qa/ortho_sidewalks.py measure --region <id>
           [--ref 671] [--highway secondary,tertiary,primary] [--step 10] [--out docs/reports/village-street-0349]
           [--strips artifacts/village-street-s24/strips]     -> <out>/<region>.json (numbers only, no pixel)
  fit:     ... ortho_sidewalks.py fit --region <id> [same options] [--dry-run]
           -> Data/Regions/<id>/overrides.ortho_sidewalks.json (roads.pipeline.GENERATED_OVERRIDES: loaded before
              overrides.yaml, an authored `side_left` / `side_right` / `sidewalk_w_*` of the same edge wins)

Method. Source: Data/raw/derived/<region>/ortho_0p25m.tif (GUGiK open data, 0.25 m; docs/05 §3: reference only).
Two-way edges of the chosen highway classes, no roundabout / bridge / tunnel. Stations every --step m, END_SKIP_M
from the edge ends. Per station a profile across the graph axis (+-HALF_M, 0.125 m cells, bilinear), median over
+-ALONG_M along the axis. "Paved" cell: brightness not more than DARK below the +-1.5 m core, saturation not more
than SAT above the core's, R - B not more than WARM above the core's (dry grass, sand), not green. The paved run through the axis (GAP_CELLS of noise tolerated) gives the left /
right extent; the centre line (brightest cell within +-1.5 m, >= core + LINE_MIN) is the lateral origin where it shows,
else the graph axis. extra = extent - half of the nominal carriageway width (roads.network.edge_section: BDOT10k
SZEROKOSCNAWIERZCHNI clamped to PTB2022 § 17, before the D94 gameplay widening). A station is valid when the run
covers >= 0.8 of the carriageway and its lane core is not darker than the sunlit asphalt of its OSM way (p85 of the cores) by SHADOW. Side with a sidewalk: extra >= MIN_EXTRA_M
at >= SHARE of the valid stations (>= MIN_STATIONS) of an edge lying in the BDOT10k built-up area
(streetscape.pavements.built_up_area); width = median extra - kerb, rounded to 0.25 m, clamped to WIDTH_RANGE.
A short edge with fewer valid stations takes the pooled result of its OSM way in the tile when its own stations do
not contradict it, else the sidewalk the measured edges at both its ends share (fill_from_neighbours).
A connected run of edges gets one width per side (even_runs: weighted median of the per-edge widths). Pass the
tiles of one road together (--region a --region b ...): a run cut by a tile seam gets one width on both sides of it. Reading accuracy at 0.25 m: about +-0.4 m per extent (ESTIMATED; one tile checked by eye on the
straightened strips). Asphalt and old concrete paving have the same brightness, so the carriageway edge itself is NOT
measured here: the split paved-run -> carriageway + sidewalk rests on the BDOT10k width. A paved bus bay or a wide
asphalt shoulder would read as a sidewalk - check the strips (--strips) before committing a fit. All thresholds
WORKING_VALUE.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
REPO = HERE.parents[3]
REGIONS = REPO / "Data" / "Regions"

HALF_M = 13.0
CELL_M = 0.125
ALONG_M = 4.0
END_SKIP_M = 10.0
DARK = 32.0
SAT = 8.0
SHADOW = 25.0           # lane core this much darker than the sunlit asphalt of the way (p85 of its cores): shadow, invalid
WARM = 10.0             # R - B above the core's: dry grass / sand verge (beige), not paving
LINE_MIN = 8.0
GAP_CELLS = 3
MIN_EXTRA_M = 1.3
SHARE = 0.6
MIN_STATIONS = 4
KERB_M = 0.15
WIDTH_RANGE = (1.5, 3.0)
BUILT_UP_SHARE = 0.5
SCHEMA = "truck-sim-pl/ortho-sidewalks/1"
OUT_NAME = "overrides.ortho_sidewalks.json"
DEFAULT_HIGHWAYS = ("primary", "secondary", "tertiary")


class Ortho:
    def __init__(self, region_id: str):
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        self.region = yaml.safe_load((REGIONS / region_id / "region.yaml").read_text(encoding="utf-8"))
        meta = json.loads((REGIONS / region_id / "ortho.json").read_text(encoding="utf-8"))
        self.meta = meta
        self.im = np.asarray(Image.open(REPO / meta["file"]).convert("RGB"))
        self.h, self.w, _ = self.im.shape
        self.x0, self.y0, self.x1, self.y1 = meta["bounds"]
        self.res = (self.x1 - self.x0) / self.w

    def sample(self, x, y):
        """Bilinear RGB (float32) at EPSG:2180 x / y arrays."""
        fx = (np.asarray(x) - self.x0) / self.res - 0.5
        fy = (self.y1 - np.asarray(y)) / self.res - 0.5
        ix = np.clip(np.floor(fx).astype(int), 0, self.w - 2)
        iy = np.clip(np.floor(fy).astype(int), 0, self.h - 2)
        tx = np.clip(fx - ix, 0, 1)[..., None]
        ty = np.clip(fy - iy, 0, 1)[..., None]
        im = self.im
        return (im[iy, ix] * (1 - tx) * (1 - ty) + im[iy, ix + 1] * tx * (1 - ty)
                + im[iy + 1, ix] * (1 - tx) * ty + im[iy + 1, ix + 1] * tx * ty).astype(np.float32)


def straighten(ortho: Ortho, geom, step=0.5):
    """(image [lat cells, stations, 3], lat [m, left +], station [m], x, y) of an edge polyline (EPSG:2180)."""
    p = np.asarray(geom, float)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(p, axis=0).T))])
    st = np.arange(0.0, s[-1], step)
    x, y = np.interp(st, s, p[:, 0]), np.interp(st, s, p[:, 1])
    tx, ty = np.gradient(x), np.gradient(y)
    k = 21                                           # tangent smoothed over ~10 m
    ker = np.ones(k) / k
    tx = np.convolve(np.pad(tx, k // 2, mode="edge"), ker, "valid")
    ty = np.convolve(np.pad(ty, k // 2, mode="edge"), ker, "valid")
    n = np.maximum(np.hypot(tx, ty), 1e-9)
    tx, ty = tx / n, ty / n
    lat = np.arange(HALF_M, -HALF_M - 1e-6, -CELL_M)
    img = ortho.sample(x[None, :] - ty[None, :] * lat[:, None], y[None, :] + tx[None, :] * lat[:, None])
    return img, lat, st, x, y


def station_profile(img, lat, col, half_cols):
    blk = img[:, max(0, col - half_cols):col + half_cols + 1]
    gray = np.median(blk.mean(axis=2), axis=1)
    sat = np.median(blk.max(axis=2) - blk.min(axis=2), axis=1)
    green = ((blk[..., 1] > blk[..., 0] + 6) & (blk[..., 1] > blk[..., 2] + 6)).mean(axis=1)
    warm = np.median(blk[..., 0] - blk[..., 2], axis=1)
    return gray, sat, green, warm


def paved_extent(gray, sat, green, warm, lat):
    """(left extent, right extent, centre offset, line seen) in metres from the lateral origin (centre line if seen)."""
    core_m = np.abs(lat) < 1.5
    core, core_sat = float(np.median(gray[core_m])), float(np.median(sat[core_m]))
    core_warm = float(np.median(warm[core_m]))
    ok = (gray >= core - DARK) & (sat <= core_sat + SAT) & (green < 0.5) & (warm <= core_warm + WARM)
    i0 = int(np.argmin(np.abs(lat)))

    def run(d):
        i, bad, last = i0, 0, i0
        while 0 <= i < len(lat):
            if ok[i]:
                bad, last = 0, i
            else:
                bad += 1
                if bad > GAP_CELLS:
                    break
            i += d
        return float(lat[last])

    left, right = run(-1), run(+1)                   # lat decreases with the index: -1 = towards the left
    cand = np.where(core_m)[0]
    k = int(cand[np.argmax(gray[cand])])
    seen = bool(gray[k] >= core + LINE_MIN)
    off = float(lat[k]) if seen else 0.0
    return left - off, -(right - off), off, seen, core


def select_edges(graph, highways, ref):
    out = []
    for e in sorted(graph["edges"], key=lambda e: e["id"]):
        a = e["attrs"]
        v = lambda k: (a.get(k) or {}).get("v")      # noqa: E731
        if v("highway") not in highways:
            continue
        if ref and str(v("ref") or "") not in ref:
            continue
        if v("oneway") not in (None, "no") or v("junction") in ("roundabout", "circular") or v("bridge") or v("tunnel"):
            continue
        out.append(e)
    return out


def measure_region(region_id: str, highways=DEFAULT_HIGHWAYS, ref=None, step=10.0, strips: Path | None = None) -> dict:
    import shapely
    from roads import network as Nw
    from streetscape import pavements as PV
    ortho = Ortho(region_id)
    rdir = REGIONS / region_id
    graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    origin = (ortho.region["origin"]["x"], ortho.region["origin"]["y"])
    ss = rdir / "generated" / "streetscape_sources.json"
    area = PV.built_up_area(json.loads(ss.read_text(encoding="utf-8")) if ss.exists() else None, origin)
    half_cols = int(round(ALONG_M / 0.5))
    edges = []
    for e in select_edges(graph, highways, ref):
        sec = Nw.edge_section(e)
        hw = sec.width / 2
        img, lat, st, x, y = straighten(ortho, e["geometry"])
        length = float(e["length_m"])
        rows = []
        s = END_SKIP_M
        while s <= length - END_SKIP_M:
            col = int(round(s / 0.5))
            if col >= img.shape[1]:
                break
            left, right, off, seen, core = paved_extent(*station_profile(img, lat, col, half_cols), lat)
            rows.append({"s": round(s, 1), "left_m": round(left, 2), "right_m": round(right, 2), "axis_off_m": round(off, 2),
                         "centre_line": seen, "core": round(core, 1), "valid": bool(left + right >= 0.8 * sec.width),
                         "built_up": bool(area.contains(shapely.Point(x[col] - origin[0], y[col] - origin[1])))})
            s += step
        if strips is not None:
            from PIL import Image
            strips.mkdir(parents=True, exist_ok=True)
            Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(
                strips / f"{region_id}_{e['id'].replace(':', '_')}.jpg", quality=90)
        edges.append({"edge": e["id"], "osm_way": e["osm_way"], "from": e["from"], "to": e["to"], "length_m": round(length, 1),
                      "highway": sec.highway, "carriageway_m": sec.width, "width_src": sec.width_src,
                      "stations": rows})
    # a station whose lane core lies in a tree shadow has no brightness reference: everything lit beside it passes
    # (reference = the 85th percentile of the cores of the OSM way in the tile: sunlit asphalt of that road)
    cores = {}
    for ed in edges:
        cores.setdefault(ed["osm_way"], []).extend(r["core"] for r in ed["stations"])
    sun = {w: float(np.percentile(v, 85)) for w, v in cores.items() if v}
    for ed in edges:
        for r in ed["stations"]:
            r["valid"] = bool(r["valid"] and r["core"] >= sun[ed["osm_way"]] - SHADOW)
        ed.update(edge_summary(ed["stations"], ed["carriageway_m"] / 2))
    pool_ways(edges)
    fill_from_neighbours(edges)
    even_runs(runs_of(edges))
    return {"schema": SCHEMA, "region": region_id,
            "ortho": {k: ortho.meta[k] for k in ("file", "sha256", "res_m", "source_manifest")},
            "thresholds": {"MIN_EXTRA_M": MIN_EXTRA_M, "SHARE": SHARE, "MIN_STATIONS": MIN_STATIONS, "KERB_M": KERB_M,
                           "WIDTH_RANGE": list(WIDTH_RANGE), "DARK": DARK, "SAT": SAT, "WARM": WARM, "SHADOW": SHADOW, "status": "WORKING_VALUE"},
            "edges": edges}


def side_stats(rows, hw, key):
    ex = [r[key] - hw for r in rows if r["valid"]]
    yes = [v for v in ex if v >= MIN_EXTRA_M]
    return {"valid": len(ex), "share": round(len(yes) / len(ex), 2) if ex else None,
            "extra_median_m": round(statistics.median(ex), 2) if ex else None,
            "sidewalk_m": round(statistics.median(yes) - KERB_M, 2) if yes else None}


def edge_summary(rows, hw):
    bu = [r["built_up"] for r in rows]
    tot = [r["left_m"] + r["right_m"] for r in rows if r["valid"]]
    return {"built_up_share": round(sum(bu) / len(bu), 2) if bu else None,
            "paved_total_median_m": round(statistics.median(tot), 2) if tot else None,
            "left": side_stats(rows, hw, "left_m"), "right": side_stats(rows, hw, "right_m")}


def _round_w(w):
    return float(min(max(round(w / 0.25) * 0.25, WIDTH_RANGE[0]), WIDTH_RANGE[1]))


def pool_ways(edges):
    """Decision per edge side: `sidewalk_w` (m) or None, with `decided_by` edge | way | none."""
    by_way = {}
    for ed in edges:
        by_way.setdefault(ed["osm_way"], []).append(ed)
    for _way, eds in sorted(by_way.items()):
        for side in ("left", "right"):
            key = f"{side}_m"
            rows = [(r, ed["carriageway_m"] / 2) for ed in eds if (ed["built_up_share"] or 0) >= BUILT_UP_SHARE
                    for r in ed["stations"] if r["valid"]]
            yes = [r[key] - hw for r, hw in rows if r[key] - hw >= MIN_EXTRA_M]
            pooled = (statistics.median(yes) - KERB_M) if len(rows) >= MIN_STATIONS and len(yes) / len(rows) >= SHARE else None
            for ed in eds:
                st = ed[side]
                dec, by = None, "none"
                if (ed["built_up_share"] or 0) >= BUILT_UP_SHARE or (ed["built_up_share"] is None and pooled is not None):
                    if st["valid"] >= MIN_STATIONS:
                        if st["share"] >= SHARE and st["sidewalk_m"] is not None:
                            dec, by = _round_w(st["sidewalk_m"]), "edge"
                    elif pooled is not None and (st["valid"] == 0 or st["share"] >= 0.5):
                        dec, by = _round_w(pooled), "way"
                st["sidewalk_w"] = dec
                st["decided_by"] = by


def fill_from_neighbours(edges):
    """A short edge between two measured ones (too few stations of its own, another OSM way id: no pool) takes the
    sidewalk of a side when the measured edges at BOTH its ends have one on that side (their left / right swapped where
    the edge directions oppose) and its own stations do not contradict; width = their mean. One pass, measured
    decisions only (an inherited one is not passed on)."""
    measured = {ed["edge"]: {s: ed[s]["sidewalk_w"] if ed[s]["decided_by"] in ("edge", "way") else None
                             for s in ("left", "right")} for ed in edges}
    other = {"left": "right", "right": "left"}
    for ed in edges:
        for side in ("left", "right"):
            st = ed[side]
            if st["sidewalk_w"] is not None or st["valid"] >= MIN_STATIONS or (st["valid"] and st["share"] < 0.5):
                continue
            got = []
            for node in (ed["from"], ed["to"]):
                ws = []
                for nb in edges:
                    if nb is ed or node not in (nb["from"], nb["to"]):
                        continue
                    same_dir = (nb["to"] == node) == (ed["from"] == node)      # nb runs into the node ed leaves, or the reverse
                    w = measured[nb["edge"]][side if same_dir else other[side]]
                    if w is not None:
                        ws.append(w)
                got.append(ws)
            if all(got):
                st["sidewalk_w"] = _round_w(statistics.mean(w for ws in got for w in ws))
                st["decided_by"] = "neighbours"


def runs_of(edges):
    """Connected runs of edge sides that carry a sidewalk: [[(edge dict, side), ...], ...] (left / right swapped where
    the directions of two edges at a node oppose)."""
    other = {"left": "right", "right": "left"}
    by_node = {}
    for i, ed in enumerate(edges):
        for node in (ed["from"], ed["to"]):
            by_node.setdefault(node, []).append(i)
    seen, runs = set(), []
    for i0, ed0 in enumerate(edges):
        for side0 in ("left", "right"):
            if (i0, side0) in seen or ed0[side0]["sidewalk_w"] is None:
                continue
            run, todo = [], [(i0, side0)]
            seen.add((i0, side0))
            while todo:
                i, side = todo.pop()
                run.append((edges[i], side))
                ed = edges[i]
                for node in (ed["from"], ed["to"]):
                    for j in by_node[node]:
                        nb = edges[j]
                        if j == i:
                            continue
                        same_dir = (nb["to"] == node) == (ed["from"] == node)
                        s2 = side if same_dir else other[side]
                        if (j, s2) not in seen and nb[s2]["sidewalk_w"] is not None:
                            seen.add((j, s2))
                            todo.append((j, s2))
            runs.append(run)
    return runs


def even_runs(runs):
    """One width per side along a connected run of edges with a sidewalk on that side: the per-edge medians differ by
    less than the reading accuracy (2.5 / 2.75 / 3.0 m on consecutive edges of one street), and a step of the sidewalk
    edge at every graph node is not on the orthophoto. Width of the run = median of the per-edge widths weighted by
    their valid stations; the per-edge value stays in `sidewalk_edge_w`."""
    for run in runs:
        for ed, s in run:
            ed[s].setdefault("sidewalk_edge_w", ed[s]["sidewalk_w"])
        vals = sorted((ed[s]["sidewalk_edge_w"], max(ed[s]["valid"], 1)) for ed, s in run)
        half, acc, w = sum(n for _, n in vals) / 2, 0.0, vals[-1][0]
        for v, n in vals:
            acc += n
            if acc >= half:
                w = v
                break
        for ed, s in run:
            ed[s]["sidewalk_w"] = w


def even_across_seams(reports):
    """Tiles measured together: runs that reach a tile edge (boundary node `B...`) on the same OSM way and side are one
    street cut by the seam -> one width on both sides of it (OSM way direction is the same in both graphs)."""
    runs = [r for rep in reports for r in runs_of(rep["edges"])]
    key_of = {}
    parent = list(range(len(runs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for k, run in enumerate(runs):
        for ed, s in run:
            if str(ed["from"]).startswith("B") or str(ed["to"]).startswith("B"):
                j = key_of.setdefault((ed["osm_way"], s), k)
                parent[find(k)] = find(j)
    groups = {}
    for k, run in enumerate(runs):
        groups.setdefault(find(k), []).extend(run)
    even_runs(list(groups.values()))


def overrides_of(report: dict) -> list:
    out = []
    for ed in report["edges"]:
        st = {}
        for side in ("left", "right"):
            w = ed[side]["sidewalk_w"]
            if w is not None:
                st[f"side_{side}"] = "sidewalk"
                st[f"sidewalk_w_{side}"] = w
                st[f"shoulder_{side}"] = "kerb"      # a sidewalk sits behind a kerb (ADR 0272 `force: kerb`)
        if not st:
            continue
        out.append({
            "id": f"ortho-sidewalk-{ed['edge']}",
            "target": {"edge": ed["edge"]},
            "source": (f"GUGiK orthophoto 0.25 m of the tile ({report['ortho']['source_manifest']}), "
                       f"tools/worldgen/qa/ortho_sidewalks.py: paved run {ed['paved_total_median_m']} m, carriageway "
                       f"{ed['carriageway_m']} m ({ed['width_src']}); left {ed['left']['decided_by']} "
                       f"{ed['left']['valid']} st. share {ed['left']['share']}, right {ed['right']['decided_by']} "
                       f"{ed['right']['valid']} st. share {ed['right']['share']}"),
            "reason": "sidewalk attached to the kerb seen on the orthophoto; OSM has no sidewalk=* / footway here (ADR 0349)",
            "confidence": "medium",
            "verify": "owner photo of the street or the 0.05 m orthophoto WMS",
            "set": st,
        })
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("measure", "fit"))
    ap.add_argument("--region", action="append", required=True)
    ap.add_argument("--ref", default=None, help="comma list of OSM ref values (default: any)")
    ap.add_argument("--highway", default=",".join(DEFAULT_HIGHWAYS))
    ap.add_argument("--step", type=float, default=10.0)
    ap.add_argument("--out", default="docs/reports/village-street-0349")
    ap.add_argument("--strips", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    reports = [measure_region(rid, tuple(a.highway.split(",")), set(a.ref.split(",")) if a.ref else None, a.step,
                              Path(a.strips) if a.strips else None) for rid in a.region]
    even_across_seams(reports)
    for rid, rep in zip(a.region, reports):
        out = REPO / a.out
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{rid}.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        for ed in rep["edges"]:
            print(f"{rid} {ed['edge']:44s} L {ed['length_m']:6.1f} bu {ed['built_up_share']} paved {ed['paved_total_median_m']} "
                  f"cw {ed['carriageway_m']} | left {ed['left']['valid']}/{ed['left']['share']} -> {ed['left']['sidewalk_w']} "
                  f"({ed['left']['decided_by']}) | right {ed['right']['valid']}/{ed['right']['share']} -> "
                  f"{ed['right']['sidewalk_w']} ({ed['right']['decided_by']})")
        if a.cmd == "fit":
            ovs = overrides_of(rep)
            f = REGIONS / rid / OUT_NAME
            if a.dry_run:
                print(f"{rid}: {len(ovs)} entries (dry run)")
            elif ovs:
                f.write_text(json.dumps({"schema": SCHEMA, "generated_by": "tools/worldgen/qa/ortho_sidewalks.py fit",
                                         "overrides": ovs}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"{rid}: wrote {len(ovs)} entries -> {f.relative_to(REPO)}")
            elif f.exists():
                f.unlink()
                print(f"{rid}: no entries, removed {f.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
