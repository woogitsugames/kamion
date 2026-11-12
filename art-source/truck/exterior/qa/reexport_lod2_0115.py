"""Regenerate only LOD2 from a verified canonical Blender cache; no texture rebake.

Uses the production export_lod and native FBX validator. Preserves every texture and
LOD0/1 byte. The master pieces in the cache retain the original baked Atlas contract.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import bpy

ROOT=Path(__file__).resolve().parents[4]
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser=argparse.ArgumentParser()
parser.add_argument('--domain',choices=('exterior','trailer'),required=True)
domain=parser.parse_args(argv).domain
folder=ROOT/'tools/blender/truck'/domain
out=ROOT/'art-source/truck'/domain/'export'
manifest=out/('truck_exterior_manifest.json' if domain=='exterior' else 'trailer_manifest.json')
cache=ROOT/'artifacts/truck-r3/cache'/f'{domain}.blend'
cache_records=json.loads((ROOT/'artifacts/truck-r3/cache-v2-sha.json').read_text(encoding='utf-8-sig'))
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
if digest(cache) != cache_records[domain]:
    raise RuntimeError('Cache differs from the validated full generation')

# The reducer regression is small and runs inside this same heavy process.
runpy.run_path(str(ROOT/'art-source/truck/exterior/qa/check_round_atlas_seams_0115.py'),run_name='__main__')
sys.path.insert(0,str(ROOT/'tools/blender/truck/exterior'))
import a6_export as A
if domain=='trailer':
    sys.path.insert(0,str(folder))
    import trailer_export as exporter
else:
    exporter=A

preserved={str(path.relative_to(out)):digest(path) for path in out.rglob('*') if path.is_file()
           and (path.suffix=='.png' or path.name.endswith(('LOD0.fbx','LOD1.fbx')))}
bpy.ops.wm.open_mainfile(filepath=str(cache))
game=bpy.data.collections.get('GAME')
if game is None:
    raise RuntimeError('Canonical cache lacks the master GAME collection')
master=[obj for obj in game.objects if obj.type=='MESH' and 'part' in obj]
if not master:
    raise RuntimeError('No master pieces in cache')
for obj in master:
    obj.hide_viewport=False
    obj.hide_render=False
    obj.hide_set(False)
lod_collection=bpy.data.collections.get('LODS')
if lod_collection is None:
    raise RuntimeError('Canonical cache lacks LODS collection')
for obj in list(lod_collection.objects):
    bpy.data.objects.remove(obj,do_unlink=True)
packet=json.loads(manifest.read_text(encoding='utf8'))
args=SimpleNamespace(out=str(out))
if domain=='exterior':
    mirrors={obj['part']:obj for obj in master if obj.name.startswith('MIRROR_')}
    exporter.export_lod(2,master,mirrors,args,packet,lod_collection)
else:
    exporter.export_lod(2,master,args,packet,lod_collection)
for name,sha in preserved.items():
    if digest(out/name)!=sha:
        raise RuntimeError('LOD2-only export changed an unrelated file: '+name)
manifest.write_text(json.dumps(packet,indent=1,ensure_ascii=False),encoding='utf8')
sys.argv=[str(folder/'check_export.py'),'--','--manifest',str(manifest)]
try:
    runpy.run_path(str(folder/'check_export.py'),run_name='__main__')
except SystemExit as result:
    if result.code not in (None,0):
        raise
proof=ROOT/'artifacts/truck-r3'/f'lod2-{domain}-preserved.json'
proof.write_text(json.dumps({'domain':domain,'cache_sha256':cache_records[domain],
    'preserved_sha256':preserved,'note':'All textures and LOD0/1 byte-identical to the validated full bake; LOD2 exported using current production code and native validator.'},indent=2),encoding='utf8')
print('TRUCK_LOD2_REEXPORT: OK '+domain)
