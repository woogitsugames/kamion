"""ADR 0288 (s24): measure the S8 median as the generator builds it - gap between the inner edge lines (axis to axis)
and between the asphalt edges of the two carriageways, per tile, from the built road network (roads.network via
seam_taper.plain_network: graph + overrides, authored center_offset, smoothing - the same chain lines the meshes use).

    uv run --project tools/worldgen python tools/worldgen/qa/s8_median_gap.py [--tiles s8-01,...] [--json out.json]

Per dense sample of an S8 chain (every ~SAMPLE_M), nearest point of an opposite-direction S8 chain within 25 m:
  line gap    = d - (hw1 - INNER) - (hw2 - INNER)          INNER = 0.20 m (lane_edges[0], s8_xsec_overrides)
  asphalt gap = d - (hw1 + MED) - (hw2 + MED)               MED = standards.PAVED_SHOULDER_MEDIAN (paved median strip)
d = distance between the carriageway centre lines, hw = half width of the section. Samples where the opposite chain is
not roughly parallel (|cos| < 0.95) are skipped. Reference: QA 2026-11-16 row 78 (orthophoto, 8 stations): line gap
3.8-4.85 m (median ~4.5), asphalt gap 3.45-4.0 m (median 3.6).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[3]
REG = ROOT / "Data" / "Regions"
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))

from roads import seam_taper as ST  # noqa: E402
from roads import standards as S  # noqa: E402

TILES = ["s8-01", "s8-02", "s8-03", "s8-04", "s8-05", "dk65-01"]
INNER = 0.20
SAMPLE_M = 10.0
SEARCH_M = 25.0


def s8_edges(graph: dict) -> set:
    out = set()
    for e in graph["edges"]:
        a = e["attrs"]
        if a["highway"]["v"] == "motorway" and "S8" in str((a.get("ref") or {}).get("v") or ""):
            out.add(e["id"])
    return out


def measure(tid: str, ref: str | None = None) -> dict:
    d = REG / tid
    region = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
    graph = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
    text = (d / "overrides.yaml").read_text(encoding="utf-8")
    if ref:                                   # overrides of another revision (before/after), same graph
        import subprocess
        text = subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:Data/Regions/{tid}/overrides.yaml"],
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout
    ov = (yaml.safe_load(text) or {}).get("overrides") or []
    net = ST.plain_network(graph, (float(region["origin"]["x"]), float(region["origin"]["y"])), ov)
    ids = s8_edges(graph)
    med = float(getattr(S, "PAVED_SHOULDER_MEDIAN", 0.5))
    chains = []
    for c in net.chains:
        if not c.edges or not all(eid in ids for eid, _ in c.edges) or c.line is None:
            continue
        p = np.asarray(c.line.p)
        hw = np.asarray(c.hw) if c.hw is not None else np.full(len(p), 0.0)
        dirn = np.asarray(c.dirn) if c.dirn is not None else np.ones(len(p))
        t = np.gradient(p, axis=0)
        t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
        t *= np.where(dirn < 0, -1.0, 1.0)[:, None]          # travel direction
        chains.append((c.id, p, hw, t))
    line_gaps, asph_gaps = [], []
    for i, (cid, p, hw, t) in enumerate(chains):
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        picks = np.searchsorted(s, np.arange(SAMPLE_M / 2, s[-1], SAMPLE_M))
        for k in picks[picks < len(p)]:
            best = None
            for j, (cid2, p2, hw2, t2) in enumerate(chains):
                if j == i:
                    continue
                dd = np.linalg.norm(p2 - p[k], axis=1)
                m = int(np.argmin(dd))
                if dd[m] > SEARCH_M or float(np.dot(t[k], t2[m])) > -0.95:
                    continue
                if best is None or dd[m] < best[0]:
                    best = (float(dd[m]), float(hw2[m]))
            if best:
                dist, h2 = best
                line_gaps.append(dist - (hw[k] - INNER) - (h2 - INNER))
                asph_gaps.append(dist - (hw[k] + med) - (h2 + med))

    def q(v):
        if not v:
            return None
        a = np.asarray(v)
        return {"n": int(len(a)), "p10": round(float(np.percentile(a, 10)), 2), "p50": round(float(np.median(a)), 2),
                "p90": round(float(np.percentile(a, 90)), 2), "share_4_0_4_8": round(float(np.mean((a >= 4.0) & (a <= 4.8))), 3)}
    return {"tile": tid, "overrides": ref or "checkout", "s8_chains": len(chains), "line_gap_m": q(line_gaps), "asphalt_gap_m": q(asph_gaps)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiles", default=",".join(TILES))
    ap.add_argument("--json")
    ap.add_argument("--ref", help="git revision of overrides.yaml (default: checkout)")
    a = ap.parse_args()
    rows = [measure(t, a.ref) for t in a.tiles.split(",") if t]
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
