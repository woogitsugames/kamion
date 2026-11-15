"""OSM API 0.6 /map along route (every 500 m, half-size H m): collect lamps, bus stops, rail, level crossings, guard rails,
trees/tree rows; distance + side (L/R in direction Białystok->Knyszyn) to route. usage: osm_corridor.py out.json H step_m"""
import json, math, sys, time, requests, xml.etree.ElementTree as ET
from pyproj import Transformer
UA = {"User-Agent": "research-client/1.0 (generic)"}
R = '/workspace/kamion/.claude/worktrees/agent-ab851075007c7ffbb/'
pl = json.load(open(R + 'docs/reports/map/dk65_route_plan.json'))['variants']['A_old_road']['polyline']
bw = Transformer.from_crs('EPSG:2180', 'EPSG:4326', always_xy=True); fw = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
cum = [0]
for i in range(1, len(pl)): cum.append(cum[-1] + math.dist(pl[i - 1], pl[i]))
def at(s):
    i = next(i for i in range(1, len(cum)) if cum[i] >= s); f = (s - cum[i - 1]) / (cum[i] - cum[i - 1])
    return pl[i - 1][0] + f * (pl[i][0] - pl[i - 1][0]), pl[i - 1][1] + f * (pl[i][1] - pl[i - 1][1])
def proj(X, Y):
    best = (1e9, 0, 0)
    for k in range(1, len(pl)):
        ax, ay = pl[k - 1]; bx, by = pl[k]; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        t = max(0, min(1, ((X - ax) * dx + (Y - ay) * dy) / L2)) if L2 else 0
        d = math.dist((X, Y), (ax + t * dx, ay + t * dy))
        if d < best[0]:
            cross = dx * (Y - ay) - dy * (X - ax)
            best = (d, (cum[k - 1] + t * math.sqrt(L2)) / 1000, 'L' if cross > 0 else 'R')
    return best
H = float(sys.argv[2]); step = int(sys.argv[3])
nodes_out, ways_out, seen = {}, {}, set()
for s in range(8600, 28400, step):
    x, y = at(s); a = bw.transform(x - H, y - H); b = bw.transform(x + H, y + H)
    for att in range(5):
        try:
            r = requests.get("https://api.openstreetmap.org/api/0.6/map", params={"bbox": f"{a[0]:.6f},{a[1]:.6f},{b[0]:.6f},{b[1]:.6f}"}, headers=UA, timeout=120)
            if r.status_code == 200: break
        except Exception as e: print("err", e)
        time.sleep(10 * (att + 1))
    root = ET.fromstring(r.content)
    N = {n.get("id"): (float(n.get("lon")), float(n.get("lat")), {t.get("k"): t.get("v") for t in n.iter("tag")}, n.get("timestamp")) for n in root.iter("node")}
    for i, (lo, la, t, ts) in N.items():
        if i in seen: continue
        key = None
        if t.get("highway") in ("street_lamp", "bus_stop") or t.get("public_transport") or t.get("railway") in ("level_crossing", "crossing", "station", "halt") or t.get("natural") == "tree" or t.get("highway") in ("traffic_signals", "crossing", "milestone") or t.get("traffic_sign"):
            seen.add(i); X, Y = fw.transform(lo, la); d, km, side = proj(X, Y)
            nodes_out[i] = {"lat": la, "lon": lo, "x": round(X, 1), "y": round(Y, 1), "tags": t, "ts": ts, "dist": round(d, 1), "km": round(km, 3), "side": side}
    for w in root.iter("way"):
        wid = w.get("id"); t = {q.get("k"): q.get("v") for q in w.iter("tag")}
        if wid in ways_out: continue
        if t.get("railway") or t.get("barrier") in ("guard_rail", "fence", "wall") and False or t.get("barrier") == "guard_rail" or t.get("natural") == "tree_row" or t.get("highway") == "street_lamp":
            pts = [fw.transform(*N[nd.get("ref")][:2]) for nd in w.iter("nd") if nd.get("ref") in N]
            pr = [proj(*p) for p in pts[:: max(1, len(pts) // 8)]] if pts else []
            ways_out[wid] = {"tags": t, "ts": w.get("timestamp"), "n": len(pts), "dist_min": round(min(p[0] for p in pr), 1) if pr else None, "dist_max": round(max(p[0] for p in pr), 1) if pr else None,
                             "km_min": round(min(p[1] for p in pr), 2) if pr else None, "km_max": round(max(p[1] for p in pr), 2) if pr else None, "sides": sorted({p[2] for p in pr}),
                             "len_m": round(sum(math.dist(pts[i - 1], pts[i]) for i in range(1, len(pts))), 1)}
    print(s, len(nodes_out), len(ways_out), flush=True); time.sleep(1.2)
json.dump({"queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "half_m": H, "step_m": step, "nodes": nodes_out, "ways": ways_out}, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
