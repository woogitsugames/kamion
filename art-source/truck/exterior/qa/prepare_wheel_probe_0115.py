"""Read-only wheel probes on actual geometry. All changed materials restore in finally."""
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
runpy.run_path(str(HERE / 'prepare_wheel_mesh_audit_0115.py'))
runpy.run_path(str(HERE / 'prepare_detail_0115.py'))
source = ROOT / 'game/Assets/_Generated/TruckQa0115/Editor/TruckDetail0115.cs'
text = source.read_text(encoding='utf8')

def replace_once(old, new):
    global text
    if text.count(old) != 1:
        raise RuntimeError(f'Wheel probe upstream changed: {old[:90]}')
    text = text.replace(old, new, 1)

replace_once('public static class TruckDetail0115', 'public static class TruckWheelProbe0115')
replace_once('if(mode=="radiance-off") source=source.Replace', '''if(mode=="flat-twosided")source=source.Replace("Cull Back ZWrite On","Cull Off ZWrite On");
            if(mode=="radiance-off") source=source.Replace''')
replace_once('public static void RunBatch()\n        {', '''public static void RunBatch()
        {
            if (EditorTools.Arg("-truckMeshProbe", "") == "flat") TruckWheelMeshAudit0115.RunBatch();''')
replace_once('string fields=mode=="mask"?"float3(coat,dirt,m.r)":',
             'string fields=mode=="albedo"?"c.rgb":(mode=="flat"||mode=="flat-twosided")?"float3(0.5,0.5,0.5)":mode=="geonormal"?"normalize(i.normalWS)*0.5+0.5":mode=="mappednormal"?"nWS*0.5+0.5":mode=="atlas-mask"?"m.rgb":mode=="uv"?"float3(frac(i.uv01.xy),0)":mode=="mask"?"float3(coat,dirt,m.r)":')
replace_once('if(mode=="crown")source=source.Replace("sampler_CMap","sampler_MMap");',
             'if(mode=="crown"||mode=="atlas-mask")source=source.Replace("sampler_CMap","sampler_MMap");\n            if(mode=="mappednormal")source=source.Replace("sampler_CMap","sampler_NMap");')
replace_once('AssetDatabase.FindAssets("MI_Ext_Paint t:Material",new[]{"Assets/_Generated/Truck"})',
             'AssetDatabase.FindAssets("t:Material",new[]{"Assets/_Generated/Truck","Assets/_Generated/Trailer"})')
replace_once('if(material==null||!material.HasProperty("_IsPaint")||material.GetFloat("_IsPaint")<0.5f) continue;',
             'if(material==null||material.shader==null||material.shader.name!="Kamion/Truck Exterior") continue;')
replace_once('if(paints.Count!=3)', 'if(paints.Count==0)')
target = source.with_name('TruckWheelProbe0115.cs')
if not target.exists() or target.read_text(encoding='utf8') != text:
    target.write_text(text, encoding='utf8')
print(f'Prepared {target.relative_to(ROOT)}. Diagnostic display channels, not radiometry.')
