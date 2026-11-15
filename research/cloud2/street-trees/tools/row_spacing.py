"""Rozstaw drzew w szpalerach przyulicznych z OSM natural=tree (Białystok).
Metoda: każde drzewo -> najbliższa oś jezdni (highway primary..residential, bez service) w ≤ 15 m; rzut na oś
(pikietaż s wzdłuż drogi o tej samej nazwie+way, strona L/P, odsunięcie d). Grupowanie: (way_id, strona);
drzewa sortowane po s; odstęp = różnica pikietażu sąsiadów; szpaler = ciąg ≥ 4 drzew o odstępach ≤ 30 m
i |Δd| ≤ 3 m. Uruchom: uv run --with shapely --with pyproj python -I tools/row_spacing.py files/osm data/row_spacing.json
"""
import json, sys, statistics as st, collections
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
from pyproj import Transformer
src, outp = sys.argv[1], sys.argv[2]
tr = Transformer.from_crs(4326, 2180, always_xy=True)
trees = json.load(open(src + '/osm_trees.json'))['elements']
roads = json.load(open(src + '/osm_roads.json'))['elements']
CL = {'primary','secondary','tertiary','unclassified','residential','living_street','trunk','primary_link','secondary_link','tertiary_link'}
R = [r for r in roads if r['tags']['highway'] in CL]
lines = [LineString([tr.transform(x, y) for x, y in r['geom']]) for r in R]
tree = STRtree(lines)
def q(vals, p):
    v = sorted(vals); i = (len(v) - 1) * p; lo = int(i); hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)
groups = collections.defaultdict(list)
near = 0
for t in trees:
    p = Point(tr.transform(t['lon'], t['lat']))
    idx = tree.query(p.buffer(15))
    best = None
    for i in idx:
        d = lines[i].distance(p)
        if d <= 15 and (best is None or d < best[0]): best = (d, i)
    if not best: continue
    near += 1
    d, i = best; ln = lines[i]; s = ln.project(p)
    a = ln.interpolate(max(s - 0.5, 0)); b = ln.interpolate(min(s + 0.5, ln.length))
    cross = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x)
    side = 'L' if cross > 0 else 'P'
    groups[(R[i]['id'], side)].append((s, d, t))
def road_half_width(tg):
    """połowa szerokości jezdni: tag width, inaczej lanes*3.25 (WORKING_VALUE), inaczej klasa."""
    try:
        if 'width' in tg: return float(tg['width'].replace(',', '.').split()[0]) / 2, 'width'
    except ValueError: pass
    try:
        if 'lanes' in tg: return int(tg['lanes']) * 3.25 / 2, 'lanes*3.25'
    except ValueError: pass
    return {'residential': 2.75, 'living_street': 2.5}.get(tg['highway'], 3.5), 'klasa'
rows_out = []; gaps_all = []; off_all = []; kerb_all = []
for (wid, side), L in groups.items():
    L.sort(key=lambda x: x[0])
    run = [L[0]]
    def flush(run):
        if len(run) >= 4:
            g = [run[k + 1][0] - run[k][0] for k in range(len(run) - 1)]
            rd = next(r for r in R if r['id'] == wid)
            hw, how = road_half_width(rd['tags'])
            offs = [x[1] for x in run]
            rows_out.append({'way': wid, 'name': rd['tags'].get('name'), 'highway': rd['tags']['highway'], 'side': side,
                             'oneway': rd['tags'].get('oneway'), 'lanes': rd['tags'].get('lanes'), 'width_tag': rd['tags'].get('width'),
                             'n': len(run), 'len_m': round(run[-1][0] - run[0][0], 1), 'gap_median': round(st.median(g), 2),
                             'gap_min': round(min(g), 2), 'gap_max': round(max(g), 2), 'axis_offset_median': round(st.median(offs), 2),
                             'half_width': hw, 'half_width_src': how, 'kerb_offset_median': round(st.median(offs) - hw, 2),
                             'lat': run[0][2]['lat'], 'lon': run[0][2]['lon'],
                             'leaf_type': collections.Counter(x[2]['tags'].get('leaf_type', '?') for x in run).most_common(),
                             'tree_ids': [x[2]['id'] for x in run]})
            gaps_all.extend(g); off_all.extend(offs); kerb_all.extend(o - hw for o in offs)
    for x in L[1:]:
        if x[0] - run[-1][0] <= 30 and abs(x[1] - run[-1][1]) <= 3: run.append(x)
        else: flush(run); run = [x]
    flush(run)
rows_out.sort(key=lambda r: -r['n'])
def summ(v): return {'n': len(v), 'p10': round(q(v, .1), 2), 'p25': round(q(v, .25), 2), 'median': round(q(v, .5), 2), 'p75': round(q(v, .75), 2), 'p90': round(q(v, .9), 2)} if v else {}
res = {'n_trees_total': len(trees), 'n_trees_within_15m_of_road_axis': near, 'n_rows': len(rows_out),
       'n_trees_in_rows': sum(r['n'] for r in rows_out), 'gap_m': summ(gaps_all), 'axis_offset_m': summ(off_all),
       'kerb_offset_m_est': summ(kerb_all),
       'gap_m_per_row_median': summ([r['gap_median'] for r in rows_out]),
       'rows': rows_out}
json.dump(res, open(outp, 'w'), ensure_ascii=False, indent=1)
print({k: v for k, v in res.items() if k != 'rows'})
for r in rows_out[:40]: print(r['name'], r['highway'], r['side'], r['n'], r['len_m'], r['gap_median'], r['gap_min'], r['gap_max'], r['axis_offset_median'], r['half_width'], r['half_width_src'], r['kerb_offset_median'], r['lat'], r['lon'])
