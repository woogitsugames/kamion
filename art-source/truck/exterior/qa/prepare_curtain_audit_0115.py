"""Read-only curtain transform/material audit after a real QA render."""
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
runpy.run_path(str(HERE / 'prepare_round_0115.py'))
source = ROOT / 'game/Assets/_Generated/TruckQa0115/Editor/TruckRound0115.cs'
text = source.read_text(encoding='utf8').replace('public static class TruckRound0115', 'public static class TruckCurtainAudit0115', 1)
needle = 'static void OnScene(Scene scene, OpenSceneMode mode)'
audit = '''[Serializable] sealed class CurtainRow
        {
            public string renderer, mesh, material;
            public bool enabled, active, staticBatch, propertyBlock;
            public uint grimeSlot;
            public Vector3 meshMin, meshMax, lossyScale, objectOriginWS, axisY, axisZ;
            public Vector4 curtain, posts, axles;
        }
        [Serializable] sealed class CurtainPacket { public string note; public List<CurtainRow> rows = new List<CurtainRow>(); }
        static void WriteCurtainAudit(string path)
        {
            var packet = new CurtainPacket { note = "Read-only CPU mesh bounds, renderer matrices and material values after actual rendering. Disabled LODs are listed separately. Not a GPU readback." };
            foreach (var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter == null || filter.sharedMesh == null) continue;
                foreach (var material in renderer.sharedMaterials)
                {
                    if (material == null || material.shader == null || material.shader.name != "Kamion/Truck Exterior" || material.GetVector("_CurtainGrime").x < 0.5f) continue;
                    var matrix = renderer.localToWorldMatrix;
                    packet.rows.Add(new CurtainRow { renderer=renderer.name, mesh=filter.sharedMesh.name, material=material.name,
                        enabled=renderer.enabled, active=renderer.gameObject.activeInHierarchy, staticBatch=renderer.isPartOfStaticBatch,
                        propertyBlock=renderer.HasPropertyBlock(), grimeSlot=renderer.GetShaderUserValue(),
                        meshMin=filter.sharedMesh.bounds.min, meshMax=filter.sharedMesh.bounds.max, lossyScale=renderer.transform.lossyScale,
                        objectOriginWS=matrix.MultiplyPoint3x4(Vector3.zero), axisY=matrix.MultiplyVector(Vector3.up), axisZ=matrix.MultiplyVector(Vector3.forward),
                        curtain=material.GetVector("_CurtainGrime"), posts=material.GetVector("_CurtainPosts"), axles=material.GetVector("_CurtainAxles") });
                }
            }
            if (packet.rows.Count == 0) throw new InvalidOperationException("No curtain audit rows");
            File.WriteAllText(path, JsonUtility.ToJson(packet, true));
            Debug.Log("TRUCK_CURTAIN_AUDIT: rows=" + packet.rows.Count + " file=" + path);
        }
        '''
if text.count(needle) != 1:
    raise RuntimeError('Audit hook changed')
text = text.replace(needle, audit + needle, 1)
needle = 'total+=count; Debug.Log("TRUCK_ROUND_CONDITION:'
if text.count(needle) != 1:
    raise RuntimeError('Post-render hook changed')
text = text.replace(needle, 'WriteCurtainAudit(Path.Combine(target,"curtain-transform-audit.json"));\n                        ' + needle, 1)
target = source.with_name('TruckCurtainAudit0115.cs')
if not target.exists() or target.read_text(encoding='utf8') != text:
    target.write_text(text, encoding='utf8')
print(f'Prepared {target.relative_to(ROOT)}; no production material/scene changes.')
