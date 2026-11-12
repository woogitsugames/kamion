"""Prepare an editor-only truck diagnostic in ignored _Generated; production sources stay intact.

The existing truck diagnostic restores materials and globals in finally. This adapter adds
an explicit output directory and temporary pigment/dirt controls. It never edits a scene.
"""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[4]
source = ROOT / 'game/Assets/_Project/Editor/VisualQA/TruckPaintRound.cs'
text = source.read_text(encoding='utf-8-sig')

def replace_once(old, new):
    global text
    if text.count(old) != 1:
        raise RuntimeError(f'Upstream truck diagnostic changed: {old[:90]}')
    text = text.replace(old, new, 1)

replace_once('public static class TruckPaintRound', 'public static class TruckRound0115')
replace_once('static bool noPane, noCoat;', '''static bool noPane, noCoat;
        static float? pigment, dirt;
        static readonly List<(Material material, string json)> pigmentMaterials = new List<(Material,string)>();
        static readonly List<(Material material, string json)> dirtMaterials = new List<(Material,string)>();''')
replace_once('if (!noPane) return;', '''if (pigment.HasValue && pigmentMaterials.Count == 0)
            {
                foreach (var guid in AssetDatabase.FindAssets("MI_Ext_Paint t:Material", new[]{"Assets/_Generated/Truck"}))
                {
                    var material = AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
                    if (material == null || !material.HasProperty("_IsPaint") || material.GetFloat("_IsPaint") < 0.5f) continue;
                    pigmentMaterials.Add((material, EditorJsonUtility.ToJson(material)));
                    material.SetColor("_PaintColor", new Color(pigment.Value, pigment.Value, pigment.Value, 1));
                    Debug.Log("TRUCK_0115_PIGMENT: " + material.name + " authored=" + pigment.Value + " stored=" + material.GetColor("_PaintColor"));
                }
                if (pigmentMaterials.Count != 3) throw new InvalidOperationException("Expected three canonical pigment controls");
            }
            if (dirt.HasValue && dirtMaterials.Count == 0)
            {
                foreach (var guid in AssetDatabase.FindAssets("t:Material", new[]{"Assets/_Generated/Truck", "Assets/_Generated/Trailer"}))
                {
                    var material = AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
                    if (material == null || material.shader == null || material.shader.name != "Kamion/Truck Exterior" || !material.HasProperty("_Dirt")) continue;
                    dirtMaterials.Add((material, EditorJsonUtility.ToJson(material)));
                    material.SetFloat("_Dirt", dirt.Value);
                }
                if (dirtMaterials.Count == 0) throw new InvalidOperationException("No exterior dirt controls");
                Debug.Log("TRUCK_0115_DIRT: amount=" + dirt.Value + " materials=" + dirtMaterials.Count);
            }
            if (!noPane) return;''')
replace_once('panes.Clear(); paints.Clear(); int total=0;', '''panes.Clear(); paints.Clear(); pigmentMaterials.Clear(); dirtMaterials.Clear(); int total=0;
            string pigmentArg = EditorTools.Arg("-truckPigment", null);
            pigment = string.IsNullOrEmpty(pigmentArg) ? (float?)null : float.Parse(pigmentArg, System.Globalization.CultureInfo.InvariantCulture);
            if (pigment.HasValue && (pigment.Value < 0 || pigment.Value > 1)) throw new ArgumentOutOfRangeException("truckPigment");
            string dirtArg = EditorTools.Arg("-truckDirt", null);
            dirt = string.IsNullOrEmpty(dirtArg) ? (float?)null : float.Parse(dirtArg, System.Globalization.CultureInfo.InvariantCulture);
            if (dirt.HasValue && (float.IsNaN(dirt.Value) || float.IsInfinity(dirt.Value) || dirt.Value < 0 || dirt.Value > 1)) throw new ArgumentOutOfRangeException("truckDirt");
            string outputRoot = EditorTools.Arg("-truckOutputRoot", "artifacts/truck-r1");''')
replace_once('"artifacts/truck-paint-r1",round,tier+"-"+light', 'outputRoot,round,tier+"-"+light')
replace_once('foreach(var paint in paints) if(paint.material!=null)', '''foreach (var saved in pigmentMaterials) if (saved.material != null)
                {
                    EditorJsonUtility.FromJsonOverwrite(saved.json, saved.material);
                    if (EditorJsonUtility.ToJson(saved.material) != saved.json) throw new InvalidOperationException("Pigment control restoration failed");
                }
                foreach(var paint in paints) if(paint.material!=null)''')
replace_once('foreach (var saved in pigmentMaterials) if (saved.material != null)', '''foreach (var saved in dirtMaterials) if (saved.material != null)
                {
                    EditorJsonUtility.FromJsonOverwrite(saved.json, saved.material);
                    if (EditorJsonUtility.ToJson(saved.material) != saved.json) throw new InvalidOperationException("Dirt control restoration failed");
                }
                foreach (var saved in pigmentMaterials) if (saved.material != null)''')
replace_once('total+=count; Debug.Log("TRUCK_ROUND_CONDITION:', '''if (dirt.HasValue)
                        {
                            var used = new HashSet<Material>();
                            foreach (var renderer in Resources.FindObjectsOfTypeAll<Renderer>())
                            {
                                if (!renderer.gameObject.scene.IsValid()) continue;
                                foreach (var material in renderer.sharedMaterials)
                                {
                                    if (material == null || material.shader == null || material.shader.name != "Kamion/Truck Exterior") continue;
                                    if (Mathf.Abs(material.GetFloat("_Dirt") - dirt.Value) > 0.000001f) throw new InvalidOperationException("Rendered exterior dirt override lost: " + material.name);
                                    used.Add(material);
                                }
                            }
                            if (used.Count == 0) throw new InvalidOperationException("No live exterior dirt materials");
                            Debug.Log("TRUCK_0115_DIRT_AFTER_RENDER: amount=" + dirt.Value + " liveMaterials=" + used.Count);
                        }
                        total+=count; Debug.Log("TRUCK_ROUND_CONDITION:''')

target = ROOT / 'game/Assets/_Generated/TruckQa0115/Editor/TruckRound0115.cs'
target.parent.mkdir(parents=True, exist_ok=True)
if not target.exists() or target.read_text(encoding='utf-8') != text:
    target.write_text(text, encoding='utf-8')
print(f'Prepared {target.relative_to(ROOT)}; upstream SHA256={hashlib.sha256(source.read_bytes()).hexdigest()}')
