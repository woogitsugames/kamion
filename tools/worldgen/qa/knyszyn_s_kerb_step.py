"""ADR 0227 D41 (e), review REVIEW-2026-11-16-pr169 P2-4: the drop behind the hard edge of DK65 south of the Knyszyn
compact roundabout, read off the generated chunk GLBs (repeatable on any build, no Data/raw needed beyond derived).

Stations every 1 m from 2 to 24 m from the (moved) split node of `knyszyn-roundabout-dk65-split-s` towards the ring
centre; at each station a perpendicular cross-section on both sides, 0..16 m from the axis, 0.05 m step:
  hard   = triangles of node `road` / `paved` whose material is not grass (carriageway, kerb, sidewalk, paving),
  ground = the highest of `terrain_lod0`, `plot_ground` and grass materials of `road`.
The hard edge is the outermost lateral reached from the axis without a gap > 0.3 m in `hard`; the step is
z(hard edge) - z(ground at edge + 1.5 m). Output JSON: per side max / median step and the stations.
    uv run --project tools/worldgen python tools/worldgen/qa/knyszyn_s_kerb_step.py [out.json]"""
import json, sys
from pathlib import Path
import numpy as np, yaml
sys.path.insert(0, str(Path(__file__).resolve().parent))
import seam_section as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
REG = "knyszyn"
SPLIT_NODE = "n4898926854"       # OSM split node of the S arm (override knyszyn-roundabout-dk65-split-s)
TOWARD = "n1134813637"           # far end of way 286990127 (the split moves out along it)
LAT = np.arange(0.0, 16.0001, 0.05)
BEHIND_M = 1.5
GRASS = ("grass", "verge")


def main(out=None):
    region = yaml.safe_load((ROOT / "Data/Regions" / REG / "region.yaml").read_text(encoding="utf-8"))
    o = np.array([region["origin"]["x"], region["origin"]["y"]])
    g = json.loads((ROOT / "Data/Regions" / REG / "roads.graph.json").read_text(encoding="utf-8"))
    N = {n["id"]: np.array([n["x"], n["y"]]) - o for n in g["nodes"]}
    ov = yaml.safe_load((ROOT / "Data/Regions" / REG / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    sp = next(e for e in ov if e.get("id") == "knyszyn-roundabout-dk65-split-s")
    move = float(sp["set"]["length_m"])            # the split node moves this far out along the arm
    d_out = N[TOWARD] - N[SPLIT_NODE]; d_out /= np.linalg.norm(d_out)
    split = N[SPLIT_NODE] + d_out * move
    d_in = -d_out                                    # towards the ring
    nrm = np.array([-d_in[1], d_in[0]])              # left of the direction towards the ring (= west side)
    centre = split + d_in * 13.0
    road = S.tris(ROOT, REG, "road", centre, rad=40.0)
    paved = S.tris(ROOT, REG, "paved", centre, rad=40.0)
    ground_parts = [v for k, v in road.items() if any(x in k for x in GRASS)]
    for node in ("terrain_lod0", "plot_ground"):
        ground_parts += list(S.tris(ROOT, REG, node, centre, rad=40.0).values())
    hard_parts = [v for k, v in list(road.items()) + list(paved.items()) if not any(x in k for x in GRASS)]
    hard = np.concatenate(hard_parts) if hard_parts else np.zeros((0, 3, 3))
    ground = np.concatenate(ground_parts) if ground_parts else np.zeros((0, 3, 3))
    res = {"split_local_en": split.round(2).tolist(), "behind_m": BEHIND_M, "sides": {}}
    for side, sg in (("west", 1.0), ("east", -1.0)):
        rows = []
        for s in np.arange(2.0, 24.01, 1.0):
            p0 = split + d_in * s
            pts = p0 + np.outer(LAT, nrm * sg)
            zh = S.locate(hard, pts)
            ok = ~np.isnan(zh)
            if not ok[0]:
                continue
            gap = 0; edge = 0
            for i in range(len(LAT)):
                if ok[i]:
                    edge, gap = i, 0
                else:
                    gap += 1
                    if gap * 0.05 > 0.3:
                        break
            q = p0 + nrm * sg * (LAT[edge] + BEHIND_M)
            zg = S.locate(ground, q[None])[0]
            if np.isnan(zg):
                continue
            rows.append({"s_m": round(float(s), 1), "edge_lat_m": round(float(LAT[edge]), 2),
                         "z_edge": round(float(zh[edge]), 3), "z_ground_behind": round(float(zg), 3),
                         "step_m": round(float(zh[edge] - zg), 3)})
        st = [r["step_m"] for r in rows]
        res["sides"][side] = {"stations": rows, "max_step_m": max(st) if st else None,
                              "median_step_m": float(np.median(st)) if st else None}
    txt = json.dumps(res, indent=1)
    if out:
        Path(out).write_text(txt, encoding="utf-8")
    print(json.dumps({k: {kk: v[kk] for kk in ("max_step_m", "median_step_m")} for k, v in res["sides"].items()}))
    return res


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
