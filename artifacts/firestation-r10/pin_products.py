"""Pin canonical products around import/capture/tests; never restores or mutates production files."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--verify',action='store_true');a=p.parse_args();R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
raw=R/'Data/raw/derived/bialystok-industrial-c/world';base=json.loads((O/'baseline-raw-sha256.json').read_text());paths=[raw/n for n in base]
assert len(paths)==192
paths+=list((R/'Data/Regions/bialystok-industrial-c/generated').rglob('*.json'))
vehicle=json.loads((O/'baseline-vehicle-sha256.json').read_text());paths += [R/n for n in vehicle]
paths+=list((R/'art-source/world/materials/fire_station').rglob('*.png'))
paths+=[R/'art-source/world/textures/fire_station_alpha.png',R/'art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb']
files={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
for n,sha in vehicle.items():assert files[n]==sha,'Canonical vehicle changed: '+n
if a.name=='final':
 expected=json.loads((O/'glass2-ready-product-pins.json').read_text())['files']
 for path in paths[:192]:
  key=path.relative_to(R).as_posix();assert files[key]==expected[key],'Canonical raw changed since accepted build: '+key
pin=O/(a.name+'-product-pins.json')
if a.verify:
 old=json.loads(pin.read_text())['files'];changes={k:{'before':old.get(k),'after':files.get(k)} for k in old.keys()|files.keys() if old.get(k)!=files.get(k)}
 (O/(a.name+'-product-verification.json')).write_text(json.dumps({'matched':not changes,'changes':changes,'canonical_raw_count':192,'vehicle_baseline_match':True},indent=2));assert not changes,str(changes);print('PASS: all'+str(len(files))+'pinned products unchanged,192raw+canonicalvehicle')
else:
 assert not pin.exists(),'Preserve existing pins; choose a new evidence name'
 pin.write_text(json.dumps({'canonical_raw_count':192,'vehicle_baseline_match':True,'files':files},indent=2));print('PINNED',len(files))
