"""Restore E's two ignored, SHA-pinned CC0 inputs without regenerating textures.

uv run --project tools/worldgen python artifacts/firestation-r10/restore_cc0_inputs.py [--check-only]
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
here=Path(__file__).resolve().parent;repo=here.parents[1].resolve()
bundle=here/'source-cache';manifest=json.loads((bundle/'manifest.json').read_text())
current=repo/'art-source/world/landmarks/fire_station_jrg2/conifer_source.json'
if current.exists():
    pins={x['file']:x['sha256'] for x in json.loads(current.read_text())['files']}
    assert pins=={x['file']:x['sha256'] for x in manifest['files']},'Production source pin differs from package'
for source in manifest['files']:
    packed=bundle/manifest['id']/source['file']
    assert hashlib.sha256(packed.read_bytes()).hexdigest()==source['sha256'],'Corrupt packaged CC0 input'
    target=(repo/manifest['raw_dir']/source['file']).resolve()
    assert target.is_relative_to(repo),'Restore target escapes intended repository (junction/path rejected)'
    matches=target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==source['sha256']
    if args.check_only:
        assert matches,'Missing or stale CC0 input: '+str(target)
    elif not matches:
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(packed,target)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==source['sha256']
    print('CC0_INPUT_OK',target.relative_to(repo),source['sha256'])
