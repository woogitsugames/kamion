"""Temporary surface/retention channels on real exterior geometry; no production edits."""
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
runpy.run_path(str(HERE / 'prepare_detail_0115.py'))
source = ROOT / 'game/Assets/_Generated/TruckQa0115/Editor/TruckDetail0115.cs'
text = source.read_text(encoding='utf8')

def replace_once(old, new):
    global text
    if text.count(old) != 1:
        raise RuntimeError(f'Retention source changed: {old[:90]}')
    text = text.replace(old, new, 1)

replace_once('public static class TruckDetail0115', 'public static class TruckRetention0115')
replace_once('string source=File.ReadAllText(original);', '''string source=File.ReadAllText(original);
            source=source.Replace("half grime = m.g;", "half debugProc = 0; half grime = m.g;")
                .Replace("grime = max(grime * 0.8, proc);", "debugProc = proc; grime = max(grime * 0.8, proc);");''')
replace_once('string fields=mode=="mask"?"float3(coat,dirt,m.r)":', 'string fields=mode=="retention"?"float3(saturate(m.g*0.8),saturate(debugProc),saturate(grime))":mode=="surface"?"float3(m.b,m.r,saturate(normalize(i.normalWS).y))":mode=="mask"?"float3(coat,dirt,m.r)":')
replace_once('if(mode=="crown")source=source.Replace', 'if(mode=="crown"||mode=="surface")source=source.Replace')
replace_once('AssetDatabase.FindAssets("MI_Ext_Paint t:Material",new[]{"Assets/_Generated/Truck"})', 'AssetDatabase.FindAssets("t:Material",new[]{"Assets/_Generated/Truck","Assets/_Generated/Trailer"})')
replace_once('if(material==null||!material.HasProperty("_IsPaint")||material.GetFloat("_IsPaint")<0.5f) continue;', 'if(material==null||material.shader==null||material.shader.name!="Kamion/Truck Exterior") continue;')
replace_once('if(paints.Count!=3)', 'if(paints.Count==0)')
target = source.with_name('TruckRetention0115.cs')
if not target.exists() or target.read_text(encoding='utf8') != text:
    target.write_text(text, encoding='utf8')
print(f'Prepared {target.relative_to(ROOT)}; retention R=baked, G=procedural, B=final; surface R=metal, G=AO, B=up.')
