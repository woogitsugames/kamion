"""Compare extracted GIS inputs, separating measured heights from generated silhouettes."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
before = json.loads((HERE / 'before-gis-cache.json').read_text())
after = json.loads((ROOT / 'Data/raw/derived/bialystok-industrial-c/world/far_field_gis_cache.json').read_text())
assert after['schema'] == 'far-field-gis-cache/11'
old = {b['id']: b for b in before['buildings']}
new = {b['id']: b for b in after['buildings']}
assert old.keys() == new.keys(), 'This round must not add or remove GIS footprints'
changed = []
for bid, b in new.items():
    a = old[bid]
    assert all(a[key] == b[key] for key in ('rect', 'typ', 'area', 'storeys', 'func'))
    if a['h'] != b['h']:
        changed.append(dict(id=bid, typ=b['typ'], rect=b['rect'], before_m=a['h'],
                            after_m=b['h'], delta_m=round(b['h'] - a['h'], 2),
                            height_source=b['height_source']))
for group in ('forests', 'chimneys', 'pylons', 'power_lines'):
    assert before[group] == after[group], f'Unexpected change to {group}'
sources = dict(Counter(b['height_source'] for b in new.values()))
assert sources == after['building_height_sources']
qa = json.loads((ROOT / 'Data/Regions/bialystok-industrial-c/generated/far_field_qa.json').read_text())
assert qa['building_height_sources'] == sources
for tier in qa['tiers'].values():
    assert hashlib.sha256((ROOT / tier['file']).read_bytes()).hexdigest() == tier['sha256']
old_qa = json.loads((HERE / 'before-far-field-qa.json').read_text())
result = dict(before_buildings=len(old), after_buildings=len(new), footprints_unchanged=True,
              other_gis_feature_groups_unchanged=True, changed_heights=len(changed),
              changed_by_typology=dict(Counter(b['typ'] for b in changed)),
              source_counts=sources, lod1_audit=after['lod1_height_audit'],
              tiers={tier: dict(before_triangles=old_qa['tiers'][tier]['total_triangles'],
                                after_triangles=qa['tiers'][tier]['total_triangles'])
                     for tier in ('Low', 'High')},
              note='Source heights before foreshortening; no claim of full-scale height in rendered backdrop.')
(HERE / 'height-audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
(HERE / 'changed-heights.json').write_text(json.dumps(changed, indent=2), encoding='utf-8')
print(json.dumps(result))
