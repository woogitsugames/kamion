"""Generate research-only plan views and derived historic roof summaries.
Run from the isolated worktree with Python containing matplotlib, pyproj, shapely.
Inputs are the per-polygon source vertices and OSM footprints in ../data.
This does not edit or run the game.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from matplotlib.colors import Normalize
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import unary_union

p = Path(__file__).resolve().parents[1]
d = json.loads((p / 'data/lod2-target-candidates.json').read_text(encoding='utf-8'))
osm = json.loads((p / 'data/osm-target-buildings.json').read_text(encoding='utf-8'))['buildings']
tr = Transformer.from_crs(4326, 2180, always_xy=True)
groups = [(300667350, 'Rynek 1 — kandydat'), (294345656, 'Kościelna 4'),
          (294345008, 'UM Rynek 39 — 2 części'), (294345650, 'Kościół — kandydat')]
fig, axes = plt.subplots(2, 2, figsize=(8, 8), dpi=100)
summary = []
for ax, (oid, label) in zip(axes.flat, groups):
    ms = [m for m in d['candidates'] if m['osm_way'] == oid]
    o = next(a for a in osm if a['osm_way'] == oid)
    opoly = Polygon([tr.transform(x, y) for x, y in o['points_lonlat']])
    cx, cy = opoly.centroid.coords[0]
    gp = unary_union([Polygon(r) for m in ms for r in m['ground_footprint_xy']])
    iou = gp.intersection(opoly).area / gp.union(opoly).area
    hmax = max(m['height_to_roof_max_m'] for m in ms)
    norm = Normalize(0, hmax)
    cmap = plt.get_cmap('viridis')
    for m in ms:
        for ring in m['roof_polygons_xyz']:
            h = sum(v[2] for v in ring) / len(ring) - m['ground_z_median']
            ax.add_patch(Patch([(x-cx, y-cy) for x, y, z in ring],
                              facecolor=cmap(norm(h)), edgecolor='#2c3440', linewidth=.5))
    xs, ys = opoly.exterior.xy
    ax.plot([v-cx for v in xs], [v-cy for v in ys], 'r--', lw=1)
    b = gp.union(opoly).bounds
    ax.set_xlim(b[0]-cx-4, b[2]-cx+4)
    ax.set_ylim(b[1]-cy-4, b[3]-cy+4)
    ax.set_aspect('equal')
    ax.grid(alpha=.2)
    ax.set_title(label + '\nIoU ' + f'{iou:.2f}; dach max ~{hmax:.1f} m', fontsize=9, pad=7)
    ax.set_xlabel('wschód siatkowy [m]', fontsize=7)
    ax.set_ylabel('północ siatkowa [m]', fontsize=7)
    ax.tick_params(labelsize=7)
    summary.append({
        'osm_way': oid, 'label': label, 'union_ground_match_iou': iou,
        'height_to_roof_max_rounded_m': round(hmax, 1),
        'individual_parts_height_to_roof_max_rounded_m': [round(m['height_to_roof_max_m'], 1) for m in ms],
        'roof_min_range_rounded_m': [round(min(m['height_to_roof_min_m'] for m in ms), 1),
                                     round(max(m['height_to_roof_min_m'] for m in ms), 1)],
        'status': 'ESTIMATED from historic source geometry; match is spatial, not authoritative identification',
        'not_eaves': 'Minimum roof vertex may belong to porch/low projection; not general eaves height.'})
fig.suptitle('Knyszyn: rzuty połaci LoD2 i zgodność obrysów\n'
             'Kolor = względna wysokość modelu, nie kolor pokrycia\n'
             'Czerwony obrys przerywany = OSM', fontsize=10, y=.98)
fig.subplots_adjust(left=.08, right=.97, bottom=.12, top=.83, hspace=.65, wspace=.4)
fig.text(.5, .035, 'Źródło: GUGiK LoD2, CC BY 4.0 (aktZrodla 2016); © OpenStreetMap contributors, ODbL 1.0\n'
         'Historyczny model i obrysy: wynik nie jest inwentaryzacją 2026', ha='center', fontsize=7)
fig.savefig(p / 'files/03-roof-plan-analysis.png')
plt.close(fig)
(p / 'data/lod2-target-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
