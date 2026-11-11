"""Texture-only refresh of the cached after library, keeping the baseline available to the active import.

Uses the GLB writer's exact packing contract. A no-op repack must be byte-identical, and all geometry accessors
must stay byte-identical after refreshing embedded PNGs. A full build_world also regenerates these same atlases.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0,'tools/worldgen')
from streetscape import furniture_textures as FT, signs as SG

snap=Path('Data/raw/derived/bialystok-industrial-c/furniture-r1-after')
p=snap/'props/street_props.glb'; raw=p.read_bytes()
n=struct.unpack_from('<I',raw,12)[0]; doc=json.loads(raw[20:20+n]); binary=raw[28+n:]


def pack(replacements):
    d=json.loads(json.dumps(doc)); buf=bytearray()
    for i,v in enumerate(d['bufferViews']):
        while len(buf)%4: buf+=b'\0'
        old=doc['bufferViews'][i]; start=old.get('byteOffset',0)
        data=replacements.get(i,binary[start:start+old['byteLength']])
        v['byteOffset']=len(buf); v['byteLength']=len(data); buf+=data
    while len(buf)%4: buf+=b'\0'
    d['buffers'][0]['byteLength']=len(buf)
    js=json.dumps(d,sort_keys=True,separators=(',',':')).encode()
    while len(js)%4: js+=b' '
    return (struct.pack('<III',0x46546C67,2,28+len(js)+len(buf))+
            struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(buf),0x004E4942)+buf)


assert pack({})==raw, 'No-op packing differs from generator; do not patch the cached library'
png={k:SG.png_bytes(im) for k,im in FT.textures().items()}
replacements={}
for mat in doc['materials']:
    name=mat['name']
    if not name.startswith('furniture_'): continue
    key='furniture_concrete' if name=='furniture_footing' else name
    t=mat['pbrMetallicRoughness']['baseColorTexture']['index']
    vi=doc['images'][doc['textures'][t]['source']]['bufferView']
    replacements[vi]=png[key]
geometry_views={a['bufferView'] for a in doc['accessors']}
assert not geometry_views.intersection(replacements), 'An image shares geometry storage'
new=pack(replacements); p.write_bytes(new)
for name,data in png.items(): (snap/'textures'/f'{name}.png').write_bytes(data)
result={'noop_repack_byte_identical':True,'geometry_accessor_views_unchanged':len(geometry_views),
        'image_views_refreshed':len(replacements),'before_sha256':hashlib.sha256(raw).hexdigest(),
        'after_sha256':hashlib.sha256(new).hexdigest()}
Path('artifacts/furniture-r1/atlas-refresh.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
