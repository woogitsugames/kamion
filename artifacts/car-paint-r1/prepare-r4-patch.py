"""Prepare an INACTIVE, git-apply-checkable candidate. Never writes production."""
from pathlib import Path
import difflib
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'artifacts/car-paint-r1'
changes = {}

def edit(path, old, new):
    before = changes.get(path, (ROOT/path).read_text(encoding='utf-8'))
    assert before.count(old) == 1, (path, old[:80], before.count(old))
    changes[path] = before.replace(old, new)

life = 'tools/worldgen/streetscape/life_cars.py'
model = (ART/'r4-model.py').read_text()
payload = model[model.index('def payload('):model.index('\ndef opacity(')]
adapter = payload + '''
def paint_deposition(primitives, prototype):
    """R4 data-only adapter after normal splitting; leave every existing array intact."""
    name = prototype.removeprefix('car_')
    body = name.split('_')[0]
    dimensions = VAN if body == 'van' else CARS.get(body)
    if dimensions is None:
        return primitives
    result = []
    for primitive in primitives:
        if primitive['mat'].startswith('car_paint_'):
            primitive = dict(primitive, UV1=payload(primitive['V'], dimensions))
        result.append(primitive)
    return result

'''
edit(life, 'def _paint_uv(m):', adapter+'def _paint_uv(m):')
export = 'tools/worldgen/streetscape/export.py'
for value in ('prims = crease_normals(lod0.out())', 'p1 = crease_normals(lod1.out())', 'p2 = crease_normals(more[0].out())'):
    lhs, rhs = value.split(' = ')
    edit(export, value, lhs+' = LC.paint_deposition('+rhs+', name)')

facade = 'art-source/world/materials/_src/sets_facade.py'
edit(facade, 'def car_grime(n=1024):', 'def car_grime(n=1024, lower_film=True):')
edit(facade,
    '    return _finish("car_grime", c, lum, h, rough, np.zeros_like(X), np.zeros_like(X), extra=tint, ao_k=0.2)',
    '''    result = _finish("car_grime", c, lum, h, rough, np.zeros_like(X), np.zeros_like(X), extra=tint, ao_k=0.2)
    if not lower_film:
        # Preserve the LEGACY calibration gain. Recalibrating the clean map would
        # alter upper dust/peel pixels unrelated to the removed lower film.
        legacy_raw = tint(lum[..., None] * np.ones(3, np.float32)).astype(np.float32)
        gain = MOD_MEAN / float((legacy_raw @ LUM).mean())
        clean_lum = (1 + 0.01 * peel) * (1 - 0.07 * runs * belt) * (1 + 0.05 * dust)
        clean_raw = clean_lum[..., None] * np.ones(3, np.float32)
        kd = dust[..., None] * 0.5
        clean_raw = clean_raw * (1 - kd) + clean_raw * np.array([1.0, 0.97, 0.90], np.float32) * kd
        result.albedo = np.where(film[..., None] > 0, np.clip(clean_raw.astype(np.float32) * gain, 0, 1), result.albedo)
        result.rough = np.clip(0.32 + 0.15 * dust, 0.05, 1).astype(np.float32)
    return result''')
needle = '    "car_grime": dict(fn=car_grime, tile_m=[5.0, 2.5], slots=["car_paint_*"],'
edit(facade, needle, '''    "car_grime_clean": dict(fn=lambda: car_grime(lower_film=False), tile_m=[5.0, 2.5],
        slots=["car_paint_silver", "car_paint_grey", "car_paint_black", "car_paint_white", "car_paint_white2", "car_paint_blue", "car_paint_red"],
        note="R4 clean lower shell; original upper dust/runs/peel and calibration retained. Road deposition is instance-driven."),
'''+needle)
materials = 'tools/worldgen/streetscape/materials.py'
text = (ROOT/materials).read_text(encoding='utf-8')
for colour in ('silver','grey','black','white','white2','blue','red'):
    start = text.index('    "car_paint_'+colour+'":')
    stop = text.index('\n',start)
    line = text[start:stop]
    assert '"texture_set": "car_grime"' in line
    edit(materials,line,line.replace('"texture_set": "car_grime"','"texture_set": "car_grime_clean"'))

shader = 'game/Assets/_Project/Environment/Shaders/WorldPBR.shader'
edit(shader,'return float2((h >> 30) * (1.0 / 3.0), (h & 1023u) * (1.0 / 1024.0));',
    '''uint level = h < 429496730u ? 0u : (h < 1932735283u ? 1u : (h < 3435973837u ? 2u : 3u));
                return float2(level * (1.0 / 3.0), (h & 1023u) * (1.0 / 1024.0));''')
text = (ROOT/shader).read_text()
start=text.index('                    // Recover the old car_grime')
stop=text.index('\n                    mask.a = lerp',start)
edit(shader,text[start:stop],'''                    // WORKING_VALUE: source UV1 is height above the actual class sill
                    // and an affine rear=0/front=1 axle coordinate. No film inversion.
                    half amount = 0.08h + 0.92h * i.carFilm.x;
                    half falloff = 0.16h + 0.06h * i.carFilm.x;
                    half vertical = exp2(-max(i.uv.z, 0.0) / falloff * 1.442695h);
                    half keepUpper = smoothstep(0.45h, 0.85h, abs(n.y)) * smoothstep(0.6, 0.8, um.y);
                    half frontTrail = saturate(1.0h - abs(i.uv.w - 0.87h) / 0.28h);
                    half rearTrail = saturate(1.0h - abs(i.uv.w + 0.13h) / 0.28h);
                    half rearFace = saturate((-i.uv.w - 0.20h) * 8.0h);
                    half deposition = max(max(frontTrail, rearTrail), rearFace);
                    carFilmOpacity = 0.5h * amount * vertical * (0.72h + 0.28h * deposition) * (1.0h - keepUpper);''')
edit(shader,'half3(0.140h, 0.136h, 0.128h)','half3(0.240h, 0.230h, 0.205h)')
importer='game/Assets/_Project/World/Import/WorldPbrMaterials.cs'
edit(importer,'            if (def.Get("uv1") as string == "along_m") uv1 = true;',
    '''            if (def.Get("uv1") as string == "along_m") uv1 = true;
            if (id.StartsWith("car_paint_") && def.Get("paint") is List<object>) uv1 = true; // R4 source deposition payload''')

edit('tests/gis/test_streetscape.py',
     'M[name]["texture_set"] == "car_grime" and len(M[name]["paint"]) == 4',
     'M[name]["texture_set"] == "car_grime_clean" and len(M[name]["paint"]) == 4')

patch=[]
for path,after in changes.items():
    before=(ROOT/path).read_text(encoding='utf-8')
    patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+path,tofile='b/'+path))
    target=ART/'r4-inactive-source'/path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(after,encoding='utf-8')
(ART/'R4-INACTIVE.patch').write_text(''.join(patch),encoding='utf-8')
print('Prepared inactive patch for',len(changes),'files. Production untouched.')
