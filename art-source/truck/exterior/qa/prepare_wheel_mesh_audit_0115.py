"""Prepare a read-only Editor dump of representative imported wheel LOD meshes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
target = ROOT / 'game/Assets/_Generated/TruckQa0115/Editor/TruckWheelMeshAudit0115.cs'
text = r'''using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using Game.Editor.Build;

namespace Game.Editor.VisualQA
{
    public static class TruckWheelMeshAudit0115
    {
        [Serializable] public sealed class Indices { public string topology; public int[] values; }
        [Serializable] public sealed class Row
        {
            public string asset, node, mesh;
            public bool runtimeReadable;
            public Vector3 min, max;
            public Matrix4x4 modelMatrix;
            public Vector3[] vertices, normals;
            public Vector4[] tangents;
            public Vector2[] uv;
            public List<Indices> submeshes = new List<Indices>();
        }
        [Serializable] public sealed class Packet
        {
            public string note = "Read-only imported CPU data, not GPU output or an automatic topology PASS. Runtime readability remains false.";
            public List<Row> rows = new List<Row>();
        }
        public static void RunBatch()
        {
            string output = EditorTools.Arg("-wheelAuditOutput", "artifacts/truck-r3/wheel-mesh-before.json");
            var packet = new Packet();
            var seen = new HashSet<string>();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[]{"Assets/_Generated/Truck/Source/Exterior", "Assets/_Generated/Trailer/Source"}))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                var root = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (root == null) continue;
                foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
                {
                    if (!filter.name.StartsWith("WHEEL_FL_LOD",StringComparison.Ordinal) && !filter.name.StartsWith("WHEEL_1L_LOD",StringComparison.Ordinal)) continue;
                    var mesh = filter.sharedMesh;
                    if (mesh == null || !seen.Add(path+"|"+filter.name)) continue;
                    // Editor access is permitted without enabling runtime Read/Write:
                    // https://docs.unity3d.com/6000.0/Documentation/ScriptReference/ModelImporter-isReadable.html
                    var row = new Row { asset=path,node=filter.name,mesh=mesh.name,runtimeReadable=mesh.isReadable,
                        min=mesh.bounds.min,max=mesh.bounds.max,modelMatrix=filter.transform.localToWorldMatrix,
                        vertices=mesh.vertices,normals=mesh.normals,tangents=mesh.tangents,uv=mesh.uv };
                    for(int sub=0;sub<mesh.subMeshCount;sub++)
                        row.submeshes.Add(new Indices {topology=mesh.GetTopology(sub).ToString(),values=mesh.GetIndices(sub)});
                    packet.rows.Add(row);
                    Debug.Log("TRUCK_WHEEL_MESH: "+path+" "+row.node+" vertices="+row.vertices.Length+" submeshes="+row.submeshes.Count);
                }
            }
            if(packet.rows.Count!=6)throw new InvalidOperationException("Expected 3 tractor and 3 trailer wheel LODs; got "+packet.rows.Count);
            string full=Path.GetFullPath(Path.Combine(EditorTools.RepoRoot,output));
            Directory.CreateDirectory(Path.GetDirectoryName(full));
            File.WriteAllText(full,JsonUtility.ToJson(packet,true));
            Debug.Log("TRUCK_WHEEL_MESH_RESULT: OK rows="+packet.rows.Count+" file="+full);
        }
    }
}
'''
# RepoRoot is not part of the established EditorTools contract; derive from Application.dataPath.
text = text.replace('EditorTools.RepoRoot', 'Path.GetDirectoryName(Path.GetDirectoryName(Application.dataPath))')
target.parent.mkdir(parents=True, exist_ok=True)
if not target.exists() or target.read_text(encoding='utf8') != text:
    target.write_text(text, encoding='utf8')
print(f'Prepared {target.relative_to(ROOT)}; no import settings or assets changed.')
