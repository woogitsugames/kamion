"""Artifact-only Fab texture payload audit; does not launch Unity or change imports.

Run: uv run --project tools/worldgen python artifacts/megascans-r1/measure-fab-textures.py
ASTC is fixed16-byte blocks. This reports complete mip payload, not GPU residency,
streaming state, driver alignment, APK size or a measured phone number.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from PIL import Image
import yaml

ROOT = Path(__file__).resolve().parents[2]
REGION = 'bialystok-industrial-c'
ASTC_6X6_ENUM = 50


def mip_chain(width, height, enabled=True):
    levels=[]
    while True:
        blocks_x,blocks_y=math.ceil(width/6),math.ceil(height/6)
        levels.append({'level':len(levels),'width':width,'height':height,
                       'blocks_x':blocks_x,'blocks_y':blocks_y,'bytes':blocks_x*blocks_y*16})
        if not enabled or (width==1 and height==1):break
        width,height=max(1,width//2),max(1,height//2)
    return levels


def clamped_size(size,maximum):
    width,height=size
    ratio=min(1., maximum/max(width,height))
    return max(1,int(round(width*ratio))),max(1,int(round(height*ratio)))


def material_refs(path):
    text=path.read_text(encoding='utf-8-sig')
    if '\nMaterial:\n' not in text:return []
    material=yaml.safe_load(text.split('\nMaterial:\n',1)[1].split('\n--- ',1)[0])
    keywords=set(material.get('m_ValidKeywords') or [])
    result=[]
    for entry in material.get('m_SavedProperties',{}).get('m_TexEnvs',[]):
        for slot,settings in entry.items():
            texture=settings.get('m_Texture',{})
            guid=str(texture.get('guid','')).lower().zfill(32)
            if not texture.get('fileID') or not re.fullmatch('[0-9a-f]{32}',guid):continue
            active=True
            if slot=='_BumpMap':active='_NORMALMAP' in keywords
            elif slot=='_OcclusionMap':active='_OCCLUSIONMAP' in keywords
            elif slot=='_MetallicGlossMap':active='_METALLICSPECGLOSSMAP' in keywords
            elif slot=='_SpecGlossMap':active='_SPECULAR_SETUP' in keywords
            elif slot=='_EmissionMap':active='_EMISSION' in keywords
            elif slot.startswith('_Detail') and slot.endswith('Map'):
                active=bool(keywords & {'_DETAIL_MULX2','_DETAIL_SCALED'})
            result.append({'guid':guid,'slot':slot,'active':active,
                           'material':path.relative_to(ROOT).as_posix()})
    return result


def canonical_high(id,channel,generated):
    for name in ('surfaces_manifest.json','drainage_atlas_manifest.json','grass_surface_manifest.json'):
        path=generated/name
        if path.exists():
            item=json.loads(path.read_text(encoding='utf-8')).get('materials',{}).get(id)
            if item:return item.get('textures',{}).get('High',{}).get(channel)
    data=json.loads((generated/'manifest.json').read_text(encoding='utf-8')).get('items',{})
    billboard=id.endswith('_billboard')
    source=id.removesuffix('_billboard') if billboard else id
    item=data.get(source.removeprefix('fab_').replace('_','-'),{})
    return item.get('billboard_textures' if billboard else 'textures',{}).get('High',{}).get(channel)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--region',default=REGION)
    parser.add_argument('--output',default='artifacts/megascans-r1/round4/fab-textures-budget.json')
    args=parser.parse_args()
    world=ROOT/'game/Assets/_Generated/World'/args.region
    fab=world/'Textures/Fab'
    generated=ROOT/'art-source/world/megascans/_generated'
    refs=[]
    material_files=sorted((world/'Materials').rglob('M*.mat'))
    for path in material_files:refs.extend(material_refs(path))
    active={}
    inactive=[]
    for ref in refs:
        if ref['active']:active.setdefault(ref['guid'],[]).append(ref)
        else:inactive.append(ref)
    textures=[];ignored=[];errors=[]
    for meta in sorted(fab.rglob('*.png.meta')):
        text=meta.read_text(encoding='utf-8-sig')
        guid_match=re.search(r'^guid:\s*([0-9a-f]{32})\s*$',text,re.M)
        if not guid_match:errors.append('Missing GUID: '+str(meta));continue
        guid=guid_match.group(1)
        texture=Path(str(meta)[:-5])
        if guid not in active:
            ignored.append({'path':texture.relative_to(ROOT).as_posix(),
                            'reason':'No active generated-material texture slot references this GUID',
                            'inactive_references':[r for r in inactive if r['guid']==guid]})
            continue
        info=yaml.safe_load(text)['TextureImporter']
        platform=next((p for p in info.get('platformSettings',[]) if p.get('buildTarget')=='Android'),{})
        maximum=int(platform.get('maxTextureSize',info.get('maxTextureSize',2048)))
        verified=platform.get('overridden')==1 and maximum==512 and platform.get('textureFormat')==ASTC_6X6_ENUM
        if not verified:errors.append('Expected explicit Android ASTC6x6/max512: '+str(texture))
        with Image.open(texture) as image:original_size=image.size
        size=clamped_size(original_size,maximum)
        mips=bool(info.get('mipmaps',{}).get('enableMipMap',0))
        chain=mip_chain(*size,mips)
        material_id=texture.parent.name;channel=texture.stem
        canonical=canonical_high(material_id,channel,generated)
        projected=None
        if canonical and (ROOT/canonical).is_file():
            with Image.open(ROOT/canonical) as image:high_source_size=image.size
            high_size=clamped_size(high_source_size,1024)
            high_chain=mip_chain(*high_size,mips)
            projected={'status':'UNVERIFIED runtime projection; canonical High maps at Android max1024, not current imported texture',
                       'canonical_map':canonical,'source_size':list(high_source_size),'projected_size':list(high_size),
                       'complete_mip_chain_astc6x6_bytes':sum(m['bytes'] for m in high_chain)}
        else:errors.append('Missing canonical High map for '+str(texture))
        textures.append({'guid':guid,'path':texture.relative_to(ROOT).as_posix(),'channel':channel,
                         'source_png_size':list(original_size),'android_clamped_size':list(size),
                         'android':platform,'verified_android_astc6x6_max512':verified,
                         'mipmaps_enabled':mips,'streaming_mipmaps':bool(info.get('streamingMipmaps')),
                         'current_complete_mip_chain':chain,'current_astc6x6_payload_bytes':sum(m['bytes'] for m in chain),
                         'material_references':active[guid],'projection_high1024':projected,
                         'meta_sha256':hashlib.sha256(meta.read_bytes()).hexdigest()})
    # GUID is the resource identity. Distinct GUIDs with identical PNG bytes remain
    # distinct resources; do not assume Unity will deduplicate them in the build.
    assert len(textures)==len({t['guid'] for t in textures}), 'Duplicate GUID metadata under Fab'
    current=sum(t['current_astc6x6_payload_bytes'] for t in textures)
    projected=sum(t['projection_high1024']['complete_mip_chain_astc6x6_bytes'] for t in textures if t['projection_high1024'])
    previous=ROOT/'artifacts/megascans-r1/round4/import-report.json'
    legacy=json.loads(previous.read_text())['pbr_textures_gpu_bytes_astc'] if previous.exists() else 32611231
    report={'schema':'kamion/fab-texture-budget/1','region':args.region,
            'method':'Actual generated M*.mat active texture GUID references -> Fab PNG.meta Android settings -> PIL dimensions clamped to maxTextureSize -> sum16*ceil(w/6)*ceil(h/6) for every mip down to1x1; GUID deduplication.',
            'scope':'Texture resources referenced by generated material assets. Does not prove which materials are included/resident in a particular scene/build/camera.',
            'current_status':'Static exact ASTC payload under parsed import settings; NOT measured runtime residency/device memory',
            'material_files_scanned':len(material_files),'unique_active_referenced_fab_texture_guids':len(textures),
            'verified_all_current_android_max512_astc6x6':bool(textures) and all(t['verified_android_astc6x6_max512'] for t in textures),
            'current_fab_complete_mip_astc6x6_payload_bytes':current,'current_fab_payload_mib':current/(1024**2),
            'legacy_report_pbr_textures_gpu_bytes_astc':legacy,
            'legacy_report_excludes_fab':True,
            'legacy_plus_fab_conservative_payload_bytes':legacy+current,
            'combined_caveat':'Legacy WorldPbrMaterials.EstimatedGpuBytes sums original s_Tex spec and excludes Fab. Adding Fab is conservative: original PBR base textures replaced by Fab may still be counted by that legacy estimator. No claim of exact combined residency.',
            'projected_high1024':{'status':'UNVERIFIED runtime projection only; current imports are512 for BOTH scene tiers',
                                  'fab_complete_mip_astc6x6_payload_bytes':projected,'mib':projected/(1024**2),
                                  'resolved_canonical_maps':sum(t['projection_high1024'] is not None for t in textures)},
            'sources':{'unity_enum_50_astc6x6':'https://github.com/Unity-Technologies/UnityCsReference/blob/master/Editor/Mono/AssetPipeline/TextureImporterEnums.cs',
                       'astc128bit_blocks':'https://registry.khronos.org/DataFormat/specs/1.4/dataformat.1.4.pdf'},
            'textures':textures,'ignored_unreferenced_or_inactive_textures':ignored,'errors':errors}
    output=ROOT/args.output;output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('unique_active_referenced_fab_texture_guids','verified_all_current_android_max512_astc6x6','current_fab_complete_mip_astc6x6_payload_bytes','current_fab_payload_mib','legacy_report_pbr_textures_gpu_bytes_astc','legacy_plus_fab_conservative_payload_bytes','projected_high1024','errors')},indent=2))
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
