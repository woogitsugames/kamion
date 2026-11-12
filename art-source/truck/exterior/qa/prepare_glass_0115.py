"""Ignored editor diagnostic covering both glass paths; no production shader edits."""
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
runpy.run_path(str(HERE / 'prepare_round_0115.py'))
base = ROOT / 'game/Assets/_Generated/TruckQa0115/Editor/TruckRound0115.cs'
text = base.read_text(encoding='utf-8-sig').replace('class TruckRound0115', 'class TruckGlassRound0115')

def once(old, new):
    global text
    if text.count(old) != 1:
        raise RuntimeError('Diagnostic upstream changed: ' + old[:90])
    text = text.replace(old, new, 1)

once('static Shader GlassDiagnostic(string mode)\n        {', '''static Shader GlassDiagnostic(string mode)
        {
            if(mode!="near-transmission" && mode!="near-radiance-off")
                throw new InvalidOperationException("This diagnostic supports transmission/radiance ablations only");''')
anchor = 'source=source.Replace(output,"return half4("+fields+","+(mode=="near-radiance-off"?"alpha":"1")+");");'
once(anchor, anchor + '''
            const string fastOutput="return pane;";
            if(source.Split(new[]{fastOutput},StringSplitOptions.None).Length!=2)
                throw new InvalidOperationException("Expected exactly one FragFast output");
            source=source.Replace(fastOutput,"return half4("+fields+","+(mode=="near-radiance-off"?"pane.a":"1")+");");''')

once('static bool noPane, noCoat;', '''[Serializable] sealed class GlassMaterialRow
        {
            public string renderer,material,asset,shader;
            public bool active,enabled,forcedOff,fastKeyword;
            public float opacity,grime,wiper,smoothness,exteriorTransmission,farClutter;
        }
        [Serializable] sealed class GlassMaterialPacket
        {
            public string note="Actual scene bindings after render; LOD rows are NOT simultaneous layers. Values are material parameters, not measured optical transmittance.";
            public List<GlassMaterialRow> rows=new List<GlassMaterialRow>();
        }
        static void WriteGlassMaterials(string output)
        {
            var packet=new GlassMaterialPacket();
            foreach(var r in Resources.FindObjectsOfTypeAll<Renderer>())
            {
                if(!r.gameObject.scene.IsValid()) continue;
                foreach(var m in r.sharedMaterials)
                {
                    if(m==null || m.shader==null || !(m.shader.name=="Kamion/Truck Glass" || m.shader.name.StartsWith("Hidden/Kamion/TruckGlassDiagnostic_",StringComparison.Ordinal))) continue;
                    packet.rows.Add(new GlassMaterialRow {renderer=r.name,material=m.name,asset=AssetDatabase.GetAssetPath(m),shader=m.shader.name,
                        active=r.gameObject.activeInHierarchy,enabled=r.enabled,forcedOff=r.forceRenderingOff,fastKeyword=Shader.IsKeywordEnabled("_KAMION_GLASS_FAST"),
                        opacity=m.GetFloat("_Opacity"),grime=m.GetFloat("_Grime"),wiper=m.GetFloat("_Wiper"),smoothness=m.GetFloat("_Smoothness"),
                        exteriorTransmission=m.GetFloat("_ExteriorTransmission"),farClutter=m.GetFloat("_SeeThroughClutter")});
                }
            }
            if(packet.rows.Count==0) throw new InvalidOperationException("No glass scene bindings after render");
            File.WriteAllText(output,JsonUtility.ToJson(packet,true));
        }
        static bool noPane, noCoat;''')
once('if(EditorTools.Arg("-truckGlassAudit","0")=="1") TruckGlassAudit.Write(Path.Combine(target,"glass-mesh-audit.json"));',
     '''if(EditorTools.Arg("-truckGlassAudit","0")=="1")
                        {
                            TruckGlassAudit.Write(Path.Combine(target,"glass-mesh-audit.json"));
                            WriteGlassMaterials(Path.Combine(target,"glass-material-bindings.json"));
                        }''')
target = base.with_name('TruckGlassRound0115.cs')
if not target.exists() or target.read_text(encoding='utf-8') != text:
    target.write_text(text, encoding='utf-8')
print('Prepared both-path glass diagnostic and actual material bindings audit')
