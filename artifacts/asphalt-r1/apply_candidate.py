"""Apply r1 after baseline captures finish. Changes only owned/shared material paths."""
from pathlib import Path

def change(path, old, new):
    p = Path(path)
    s = p.read_text(encoding='utf-8-sig')
    assert s.count(old) == 1, (path, old[:80], s.count(old))
    p.write_text(s.replace(old, new), encoding='utf-8')

shader = 'game/Assets/_Project/Environment/Shaders/WorldPBR.shader'
change(shader, '        _WheelPolish (',
       '        _AsphaltWear ("Asphalt: tone, wheel darkening, Low cracks, reserved (ADR0118)", Vector) = (1, 0, 0, 0)\n        _WheelPolish (')
change(shader, '            float4 _PaintColor, _PaintWear;',
       '            float4 _PaintColor, _PaintWear;\n            float4 _AsphaltWear;')
change(shader, '            #if defined(_CRACKS) && defined(_KAMION_WORLD_DETAIL)\n                {',
       '            #if defined(_CRACKS)\n            #if !defined(_KAMION_WORLD_DETAIL)\n                if (_AsphaltWear.z > 0.5) // opt-in: existing mask, one fetch, no crack normal on Low\n            #endif\n                {')
change(shader, '                    half3 cn = UnpackNormalScale(SAMPLE_TEXTURE2D(_CrackNormal, sampler_CrackMap, uc), amount);\n                    tn = normalize(half3(tn.xy + cn.xy, tn.z * cn.z));',
       '                #if defined(_KAMION_WORLD_DETAIL)\n                    half3 cn = UnpackNormalScale(SAMPLE_TEXTURE2D(_CrackNormal, sampler_CrackMap, uc), amount);\n                    tn = normalize(half3(tn.xy + cn.xy, tn.z * cn.z));\n                #endif')
change(shader, '                    float2 w = i.uv.zw;\n                    if (w.x > -0.5)',
       '                    float2 w = i.uv.zw;\n                    albedo *= _AsphaltWear.x; // tone also applies to old-road patches without lane data\n                    if (w.x > -0.5)')
change(shader, '                        albedo *= 1.0 - 0.10 * wp * _WheelPolish;',
       '                        // ADR0118: traffic polish darkens binder; existing macro breaks continuous bands.\n                        half traffic = _AsphaltWear.y * (0.65 + 0.35 * macro.a);\n                        albedo *= 1.0 - wp * (0.10 * _WheelPolish + traffic);')

imp = 'game/Assets/_Project/World/Import/WorldPbrMaterials.cs'
change(imp, '            bool asphalt = setName == "asphalt_worn"',
       '''            // ADR0118: explicit opt-in data. Reset on every import so removing a block is idempotent.
            mat.SetVector("_AsphaltWear", new Vector4(1f, 0f, 0f, 0f));
            if (def.Get("asphalt_wear") is Dictionary<string, object> aw)
            {
                float A(string key, float fallback) => aw.Get(key) != null ? (float)Num(aw.Get(key)) : fallback;
                mat.SetVector("_AsphaltWear", new Vector4(A("tone", 1f), A("wheel_darkening", 0f),
                    A("low_cracks", 0f), 0f));
            }
            bool asphalt = setName == "asphalt_worn"''')
change(imp, '                    float wheelWear = P("wheel_wear", 0.85f) * 0.5f;',
       '                    float wheelWear = P("wheel_wear", 0.85f); // ADR0118: strength belongs to material data')

materials = Path('tools/worldgen/streetscape/materials.py')
with materials.open('a', encoding='utf-8') as f:
    f.write('''

# ADR0118 r1: asphalt-only overrides of the road material table (MATERIALS.update(M)).
# WORKING_VALUE: judged against local photo wheel/centre ratio 0.67, not measured physical albedo.
# No road generator/geometry change; fresh SMA deliberately has no old-road damage opt-in.
M["road_asphalt"] = {"color": [0.081, 0.08, 0.079], "rough": 0.9, "surface": "asphalt",
                     "texture_set": "asphalt_worn",
                     "asphalt_wear": {"tone": 0.90, "wheel_darkening": 0.45, "low_cracks": 1.0}}
# Restore authored wheel wear (0099 halved it in C#). Keep all coefficients visible here.
# Glyphs share the transverse encoding: their readability is an explicit visual control, not a claimed fix.
from roads.standards import MARKING_LIFT as _ASPHALT_PAINT_LIFT
M["marking_white"] = {"color": [0.55, 0.55, 0.54], "rough": 0.65, "surface": "paint",
                      "texture_set": "asphalt_worn", "decal": True, "depth_offset_m": _ASPHALT_PAINT_LIFT,
                      "paint": {"wheel_wear": 0.85, "age_wear": 0.25, "dirt": 0.38, "line_w_m": 0.12}}
''')
print('Applied asphalt r1 candidate. Regenerate world, import, render matched cameras before acceptance.')
