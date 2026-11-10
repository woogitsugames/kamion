"""Write hash-only Fab fingerprints so public CI can reject renamed licensed files.
No licensed payload or image is written to tracked output. Run after preparing local assets.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
ROOT = Path(__file__).resolve().parents[3]

def build(root=ROOT):
    source = json.loads((root/'Data/SourceManifests/fab-megascans-2026-11-10.json').read_text())
    hashes = set()
    for item in source['items']:
        archive = root/item['file']
        if not archive.exists():
            raise FileNotFoundError(archive)
        with ZipFile(archive) as z:
            for info in z.infolist():
                if info.is_dir(): continue
                h = hashlib.sha256()
                with z.open(info) as stream:
                    for block in iter(lambda: stream.read(1<<20), b''): h.update(block)
                hashes.add(h.hexdigest())
    generated = root/'art-source/world/megascans/_generated'
    derivatives=set()
    for path in generated.rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.png','.fbx','.glb','.gltf','.asset','.jpg','.jpeg','.exr','.tga'}:
            h=hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
            derivatives.add(h.hexdigest())
    output=root/'Data/SourceManifests/fab-content-hashes.json'
    output.write_text(json.dumps({'schema':1,'items':[], 'purpose':'Hash-only denylist; no licensed payload. Exact byte matches only, not arbitrary transformed derivatives.', 'member_sha256':sorted(hashes),'derivative_sha256':sorted(derivatives)},indent=2)+'\n')
    print(f'Fab inventory: {len(hashes)} source members, {len(derivatives)} local products')
if __name__=='__main__':build()
