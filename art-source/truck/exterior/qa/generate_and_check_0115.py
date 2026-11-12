"""One heavy Blender process: canonical generation, cache, then native FBX validator."""
import argparse
import os
from pathlib import Path
import runpy
import sys

import bpy

ROOT = Path(__file__).resolve().parents[4]
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument('--domain',choices=('exterior','trailer'),required=True)
parser.add_argument('--artifact-root',default='artifacts/truck-r3')
parser.add_argument('--regular-front-wheels',action='store_true')
options = parser.parse_args(args)
domain = options.domain
artifact_root = ROOT/options.artifact_root
if options.regular_front_wheels and domain != 'exterior':
    parser.error('Regular front wheels belong to the exterior generator')
if options.regular_front_wheels:
    # Preconditions of this generation cycle, inside the caller's one heavy slot.
    # They write no canonical assets and a failure stops before any full bake.
    os.environ['TRUCK_0115_ARTIFACT_ROOT'] = str(artifact_root)
    seams = ROOT/'art-source/truck/exterior/qa/check_round_atlas_seams_0115.py'
    sys.argv = [str(seams)]
    runpy.run_path(str(seams),run_name='__main__')
    smoke = ROOT/'art-source/truck/exterior/qa/check_disc_blender_0115.py'
    sys.argv = [str(smoke),'--','--output',str(artifact_root/'disc-native-smoke.json')]
    runpy.run_path(str(smoke),run_name='__main__')
folder = ROOT/'tools/blender/truck'/domain
exporter = folder/('a6_export.py' if domain=='exterior' else 'trailer_export.py')
out = ROOT/'art-source/truck'/domain/'export'
manifest = out/('truck_exterior_manifest.json' if domain=='exterior' else 'trailer_manifest.json')
cache = artifact_root/'cache'/f'{domain}.blend'
cache.parent.mkdir(parents=True,exist_ok=True)
sys.argv = [str(exporter),'--','--out',str(out),'--no-renders','--blend',str(cache)]
if options.regular_front_wheels:
    sys.argv.append('--regular-front-wheels')
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
