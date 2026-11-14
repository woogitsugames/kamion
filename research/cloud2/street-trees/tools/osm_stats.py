"""Statystyka tagów drzew OSM (Białystok, trasa C, Dojlidy). python3 -I tools/osm_stats.py data/ > data/osm_stats.json"""
import json, sys, collections
d = sys.argv[1]
trees = json.load(open(d + '/osm_trees.json'))['elements']
rows = json.load(open(d + '/osm_rows.json'))['elements']
hedges = json.load(open(d + '/osm_hedges.json'))['elements']
BBOX = {'bialystok': None,
        'trasa_c': (53.1499, 53.1672, 23.1437, 23.1761),     # kafel bialystok-industrial-c (research/g7)
        'dojlidy': (53.096, 53.114, 23.176, 23.206)}        # kafel Dojlidy (research/mistral/p11)
def inb(lat, lon, b): return b is None or (b[0] <= lat <= b[1] and b[2] <= lon <= b[3])
KEYS = ['species', 'species:pl', 'genus', 'taxon', 'leaf_type', 'leaf_cycle', 'height', 'circumference',
        'diameter_crown', 'denotation', 'start_date', 'name']
out = {}
for name, b in BBOX.items():
    T = [t for t in trees if inb(t['lat'], t['lon'], b)]
    n = len(T)
    comp = {k: sum(1 for t in T if k in t['tags']) for k in KEYS}
    sp = collections.Counter()
    gen = collections.Counter()
    for t in T:
        tg = t['tags']
        s = tg.get('species') or tg.get('taxon') or tg.get('species:pl')
        if s: sp[s.strip()] += 1
        g = tg.get('genus') or (s.split()[0] if s and s[0].isupper() else None)
        if g: gen[g.strip()] += 1
    lt = collections.Counter(t['tags'].get('leaf_type', '(brak)') for t in T)
    den = collections.Counter(t['tags'].get('denotation', '(brak)') for t in T)
    hs = sorted(float(t['tags']['height'].replace(',', '.').split()[0]) for t in T if 'height' in t['tags'] and t['tags']['height'].replace(',', '.').split()[0].replace('.', '').isdigit())
    cs = sorted(float(t['tags']['circumference'].replace(',', '.').split()[0]) for t in T if 'circumference' in t['tags'] and t['tags']['circumference'].replace(',', '.').split()[0].replace('.', '').isdigit())
    R = [r for r in rows if any(inb(la, lo, b) for lo, la in r['geom'])]
    Hd = [r for r in hedges if any(inb(la, lo, b) for lo, la in r['geom'])]
    out[name] = {'n_tree': n, 'tag_count': comp, 'tag_pct': {k: round(100 * v / n, 1) if n else None for k, v in comp.items()},
                 'species': sp.most_common(40), 'genus': gen.most_common(30), 'leaf_type': lt.most_common(),
                 'denotation': den.most_common(), 'height_m': hs, 'circumference_m': cs,
                 'n_tree_row': len(R), 'tree_row_tags': [r['tags'] for r in R][:40], 'n_hedge': len(Hd),
                 'hedge_tag_keys': collections.Counter(k for r in Hd for k in r['tags']).most_common(12)}
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
