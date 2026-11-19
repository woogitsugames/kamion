"""ADR 0301: before / after summary of lane_width_audit.py runs (robust metrics, not the raw asphalt run).

  uv run --project tools/worldgen python tools/worldgen/qa/lane_audit_compare.py <before_dir> <after_dir> [region ...]

Per station the orthophoto lanes are the chain of paint lines around the route point (ortho_lane_fit.station_layout,
same rules as the fit); metrics: (1) line error = distance from each such orthophoto lane boundary to the nearest
generated longitudinal line, (2) lane width error of the route lane (generated - orthophoto), (3) lane count
(generated lane lines inside the generated carriageway + 1 vs orthophoto chain). Stations without an orthophoto chain
are not counted. Medians / p90 per region."""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortho_lane_fit as F  # noqa: E402


def metrics(rows):
    le, lw, lc, n = [], [], [], 0
    for r in rows:
        o, g = r["ortho"], r["gen"]
        lay = F.station_layout(o["asphalt"], o["lines"], at=0.0)
        if not lay or not g["asphalt"] or not g["lines"]:
            continue
        n += 1
        gl = sorted(g["lines"]) + list(g["asphalt"])
        le += [min(abs(x - y) for y in gl) for x in lay["b"]]
        b = lay["b"]
        lane = next(((a, c) for a, c in zip(b, b[1:]) if a <= 0 <= c), None)
        gb = sorted(set([g["asphalt"][0]] + [x for x in g["lines"] if g["asphalt"][0] + 0.6 < x < g["asphalt"][1] - 0.6]
                        + [g["asphalt"][1]]))
        gl2 = next(((a, c) for a, c in zip(gb, gb[1:]) if a <= 0 <= c), None)
        if lane and gl2:
            lw.append((gl2[1] - gl2[0]) - (lane[1] - lane[0]))
        inner = [x for x in g["lines"] if g["asphalt"][0] + 0.6 < x < g["asphalt"][1] - 0.6]
        lc.append(len(inner) + 1 == len(b) - 1)
    q = lambda v, p: sorted(v)[min(len(v) - 1, int(p * len(v)))] if v else None
    return {"stations": n, "line_err_med": round(statistics.median(le), 2) if le else None,
            "line_err_p90": round(q(le, 0.9), 2) if le else None,
            "lane_w_err_med": round(statistics.median(lw), 2) if lw else None,
            "lane_w_abs_med": round(statistics.median([abs(x) for x in lw]), 2) if lw else None,
            "lane_count_ok": f"{sum(lc)}/{len(lc)}"}


def main(argv):
    a, b = Path(argv[0]), Path(argv[1])
    regs = argv[2:] or sorted(p.stem for p in a.glob("*.json"))
    for r in regs:
        out = {}
        for tag, d in (("before", a), ("after", b)):
            f = d / f"{r}.json"
            if f.exists():
                out[tag] = metrics(json.loads(f.read_text(encoding="utf-8")))
        print(r, json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1:])
