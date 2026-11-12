"""One heavy Blender process: canonical generation, cache, then native FBX validator."""
import argparse
from pathlib import Path
import runpy
import sys

import bpy

ROOT = Path(__file__).resolve().parents[4]
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument('--domain',choices=('exterior','trailer'),required=True)
domain = parser.parse_args(args).domain
folder = ROOT/'tools/blender/truck'/domain
exporter = folder/('a6_export.py' if domain=='exterior' else 'trailer_export.py')
out = ROOT/'art-source/truck'/domain/'export'
manifest = out/('truck_exterior_manifest.json' if domain=='exterior' else 'trailer_manifest.json')
cache = ROOT/'artifacts/truck-r3/cache'/f'{domain}.blend'
cache.parent.mkdir(parents=True,exist_ok=True)
sys.argv = [str(exporter),'--','--out',str(out),'--no-renders','--blend',str(cache)]
try:
    runpy.run_path(str(exporter),run_name='__main__')
except BaseException:
    if not cache.exists():
        try:
            bpy.ops.wm.save_as_mainfile(filepath=str(cache.with_name(domain+'-failed.blend')))
        except Exception as error:
            print('TRUCK_CACHE_FAILED:',str(error))
    raise
sys.argv = [str(folder/'check_export.py'),'--','--manifest',str(manifest)]
try:
    runpy.run_path(str(folder/'check_export.py'),run_name='__main__')
except SystemExit as result:
    if result.code not in (None,0):
        raise
print('TRUCK_GENERATOR_AND_CHECK: OK '+domain)
