"""Artifact-only integer packing prototype. Never changes source assets or Unity bindings."""
from pathlib import Path
import hashlib,json,re,struct,subprocess
import numpy as np
from PIL import Image, __version__ as pillow_version
from bus_world_proof import ROOT,OUT

MASK=ROOT/'game/Assets/_Generated/World/bialystok-industrial-c/Textures/PBR/asphalt_worn/T_asphalt_worn_MaskMap.png'
CRACK=ROOT/'game/Assets/_Generated/World/bialystok-industrial-c/Textures/PBR/asphalt_cracks_layer/T_asphalt_cracks_layer_Mask.png'
MATERIAL=ROOT/'game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_road_asphalt.mat'
PRIVATE=OUT/'packed-mask16-private'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(array):return hashlib.sha256(array.tobytes()).hexdigest()
def astc_bytes(size):
    total=0;levels=[]
    while True:
        value=((size+7)//8)**2*16;levels.append(dict(size=size,bytes=value));total+=value
        if size==1:break
        size=max(1,size//2)
    return total,levels
def box2(array):
    a=array.astype(np.uint16)
    return ((a[::2,::2]+a[1::2,::2]+a[::2,1::2]+a[1::2,1::2]+2)//4).astype(np.uint8)
def chunks(path):
    data=path.read_bytes();offset=8;result=[]
    assert data[:8]==b'\x89PNG\r\n\x1a\n'
    while offset<len(data):
        length=struct.unpack_from('>I',data,offset)[0];result.append(data[offset+4:offset+8].decode('ascii'));offset+=12+length
    return result
def main():
    assert MASK.is_file() and CRACK.is_file()
    mask=np.asarray(Image.open(MASK));crack=np.asarray(Image.open(CRACK))
    assert mask.dtype==crack.dtype==np.uint8 and mask.shape==crack.shape==(1024,1024,4)
    assert np.all(mask[:,:,0]==0)
    material=MATERIAL.read_text();meta=Path(str(MASK)+'.meta').read_text()
    assert re.search(r'_MetallicScale: 0(?:\s|$)',material)
    assert '_Tile: {r: 4, g: 4, b: 16, a: 1}'in material
    guid=re.search(r'^guid: (\w+)',meta,re.M).group(1)
    assert re.search(r'_MaskMap:\s*\n\s*m_Texture: \{fileID: 2800000, guid: '+guid,material)
    assert re.search(r'sRGBTexture: 0',meta)
    native=json.loads((OUT/'native-gate-r2.json').read_text())
    actual=next(m for m in native['materials']if m['path'].endswith('/M_road_asphalt.mat'))
    assert actual['shader']=='Kamion/World PBR'and '_CRACKS'in actual['keywords'].split(',')
    # Integer-only copies: G/B/A are literal4x4 repetitions, R replicates existing16m coverage.
    packed=np.tile(mask,(4,4,1))
    packed[:,:,0]=np.repeat(np.repeat(crack[:,:,0],4,axis=0),4,axis=1)
    tile_hashes=[]
    for y in range(4):
        for x in range(4):
            tile=packed[y*1024:(y+1)*1024,x*1024:(x+1)*1024,1:]
            assert np.array_equal(tile,mask[:,:,1:]);tile_hashes.append(digest(tile))
    assert len(set(tile_hashes))==1
    assert np.array_equal(packed[:,:,0].reshape(1024,4,1024,4)[:,0,:,0],crack[:,:,0])
    # World-coordinate checks include negative positions and period boundaries. No PRNG is used.
    for world in [-33.75,-16.,-15.999,-4.001,-4.,-.001,0.,.001,3.999,4.,15.999,16.,31.75]:
        src=int(np.floor((world%4)/4*1024));dst=int(np.floor((world%16)/16*4096))
        assert src==dst%1024
        assert int(np.floor((world%16)/16*1024))==dst//4
    # Ideal box mip parity is a CPU proof only; actual Unity resize/ASTC can couple channels.
    old=box2(mask[:,:,1:]);new=box2(packed[:,:,1:]);mips=[]
    while True:
        expected=np.tile(old,(4,4,1))
        assert np.array_equal(new,expected)
        mips.append(dict(old_tile_pixels=old.shape[0],packed_pixels=new.shape[0],GBA_byte_exact=True))
        if old.shape[0]==1:break
        old=box2(old);new=box2(new)
    private=PRIVATE.resolve();assert private.is_relative_to(OUT.resolve())
    # Retain the importer-recognized suffix: alpha enabled, low-frequency Android half-size.
    PRIVATE.mkdir(exist_ok=True);output=PRIVATE/'T_road_asphalt_packed16_MaskMap.png'
    Image.fromarray(packed,'RGBA').save(output,compress_level=6)
    decoded=np.asarray(Image.open(output));assert np.array_equal(decoded,packed)
    png_chunks=chunks(output);assert not set(png_chunks)&{'gAMA','sRGB','iCCP'}
    memory,levels=astc_bytes(2048);assert memory==1398144
    # Verify every shipping cached/raw asset against actual END BEFORE; this recipe changes none.
    fixture=json.loads((OUT/'wear-probe-before-final-fixture.json').read_text())
    for row in fixture['files']+fixture['raw']:assert sha(ROOT/row['file'])==row['sha256'],row['file']
    shader=ROOT/'game/Assets/_Project/Environment/Shaders/WorldPBR.shader'
    assert sha(shader)=='1dc7db4ea4ec839f4dc8fbd301ba5aedd38a12c3fff892e66818841d125edce4'
    proof=dict(status='ARTIFACT_ONLY_NOT_BOUND_OR_RENDERED',source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        recipe_sha256=sha(Path(__file__)),pillow_version=pillow_version,inputs=[dict(file=str(p.relative_to(ROOT)).replace('\\','/'),sha256=sha(p))for p in [MASK,CRACK,MATERIAL,Path(str(MASK)+'.meta')]],
        native_material=actual,actual_tile=[4,4,16,1],metallic_scale=0,original_mask_R_all_zero=True,
        output=dict(file=str(output.relative_to(OUT)).replace('\\','/'),sha256=sha(output),size=[4096,4096],mode='RGBA',png_chunks=sorted(set(png_chunks)),importer_MaskMap_suffix=True,
            integer_copy_no_gamma=True,planned_import_sRGB=False,GBA_tile_sha256=tile_hashes[0],GBA_exact_tiles=16,
            red_source_channel='existing16m open crack R only; nearest4x replication; no sealant/no random generation',red_mean_source=float(crack[:,:,0].mean()),red_mean_packed=float(packed[:,:,0].mean())),
        metric_phase=dict(base_and_normal_tile_m=4,mask_tile_m=16,planned_mask_uv_scale=.25,source_GBA_texel_m=4/1024,packed_GBA_texel_m=16/4096,
            original_Android_GBA_texel_m=4/512,planned_Android_GBA_texel_m=16/2048,negative_and_boundary_coordinates_verified=True),
        ideal_CPU_box_mip_parity=mips,planned_Android=dict(size=2048,format='ASTC8x8 linear with alpha and mipmaps',bytes_with_mips=memory,MiB=memory/1048576,levels=levels,
            added_bytes_if_original_stays_resident=memory),
        scope=dict(proposed_binding_only='M_road_asphalt',road_new_unchanged=True,base_normal_tile_unchanged=True,High_ignores_packed_R=True,Low_open_R_from_existing_mask_fetch=True,
            proposed_additional_texture_fetches=0,actual_shipping_cached_files_unchanged=len(fixture['files']),actual_raw_files_unchanged=len(fixture['raw']),shader_and_bindings_untouched=True),
        required_gates=['ROOT/E approval before activation','Actual Unity resize and ASTC G/B/A drift readback; CPU parity is not runtime proof','High source/mask parity and no second crack layer',
            'Fresh-road negative unchanged','Visible Low contrast with metric scale; no arbitrary width/gain','Matched material mean within1displayRGBlevel','Budget ledger including original resident texture and importer cap override'],
        provenance='CrackMap is existing authored procedural WORKING_VALUE data, not surveyed damage. G/B/A derive from existing CC0 asphalt processing. Local PNG is private and not committed; this recipe/proof carries source hashes.')
    (OUT/'packed-mask16-prototype-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('CPU prototype4096RGBA:16exact GBA tiles, original16mR, exact ideal box mip parity, planned2048ASTC8=',memory,'bytes; no shipping change.')
if __name__=='__main__':main()
