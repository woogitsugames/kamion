"""Check actual native material uniforms against fresh manifest data, including repeat-import idempotence."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
stage=sys.argv[1]if len(sys.argv)>1 else'gate-first'
native=json.loads((OUT/f'native-{stage}.json').read_text())
manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
rows=[]
for material in native['materials']:
    if '_DECAL_PAINT'not in material['keywords'].split(','):continue
    id=Path(material['path']).stem.removeprefix('M_');cfg=manifest['materials'][id]['paint']
    raw=next(x.split('=',1)[1]for x in material['fields']if x.startswith('_PaintWear='))
    actual=[float(x)for x in re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?',raw)]
    expected=[cfg.get('wheel_wear',.85)*.5,cfg.get('age_wear',.25),cfg.get('dirt',.3),cfg.get('line_w_m',.12)]
    assert len(actual)==4 and all(abs(a-b)<1e-6 for a,b in zip(actual,expected)),(id,actual,expected)
    rows.append(dict(material=id,nominal_source_wheel=cfg.get('wheel_wear',.85),actual_uniform=actual,expected_from_fresh_metadata=expected))
assert rows
if stage!='gate-first':
    first=json.loads((OUT/'paint-uniform-gate-first.json').read_text())['materials']
    assert rows==first,(rows,first)
packet=dict(stage=stage,materials=rows,repeated_import_matches_first=stage!='gate-first',note='Actual native material readback, fresh metadata*.5; age/dirt/width exact. No scaling of existing material values. Repeat check uses a later planned canonical import, not an extra round.')
(OUT/f'paint-uniform-{stage}.json').write_text(json.dumps(packet,indent=2)+'\n');print(json.dumps(packet))
