using System;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Editor.Build;
using Game.Rendering;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>Measures the actual imported AO UV metric. Projected triangles are not an occlusion/visibility test.</summary>
    public static class CabAoUvAudit
    {
        static Vector2 Singular(Vector3 a, Vector3 b, Vector2 u, Vector2 v)
        {
            float length = a.magnitude, along = Vector3.Dot(b, a / length);
            float across = (b - a / length * along).magnitude;
            if (length < 1e-8f || across < 1e-8f) return Vector2.zero;
            Vector2 c0 = u / length, c1 = (v - c0 * along) / across;
            double trace = c0.sqrMagnitude + c1.sqrMagnitude;
            double determinant = (double)c0.x * c1.y - (double)c0.y * c1.x;
            double discriminant = Math.Sqrt(Math.Max(0, trace * trace - 4 * determinant * determinant));
            double maximum = Math.Sqrt(Math.Max(0, (trace + discriminant) * .5));
            // Product of singular values avoids cancellation for thin triangles.
            double minimum = maximum > 0 ? Math.Abs(determinant) / maximum : 0;
            return new Vector2((float)minimum, (float)maximum);
        }

        public static void Run()
        {
            int exit = 1, rows = 0; Exception failure = null; bool measured = false;
            string output = EditorTools.Arg("-cabOutput", Path.Combine(EditorTools.RepoRoot, "artifacts/cab-r2/ao-uv-audit"));
            void Measure(ScriptableRenderContext context, Camera camera)
            {
                var control = camera.GetComponent<ControlCamera>();
                if (measured || control == null || control.id != "cab-grain") return;
                measured = true;
                try
                {
                    var text = new StringBuilder("renderer\ttriangle\tviewportX\tviewportY\tdetailMinUvPerM\tdetailMaxUvPerM\taoMinTexelsPerM\taoMaxTexelsPerM\n");
                    var rig = UnityEngine.Object.FindFirstObjectByType<TruckVisualRig>();
                    foreach (var renderer in rig.interiorLods[0].renderers)
                    {
                        if (!renderer.name.StartsWith("CAB_Interior", StringComparison.Ordinal)) continue;
                        var mesh = renderer.GetComponent<MeshFilter>().sharedMesh;
                        var vertices = mesh.vertices; var normals = mesh.normals;
                        var uv = mesh.uv; var ao = mesh.uv2; var data = mesh.uv3;
                        var matrix = renderer.localToWorldMatrix; var normalMatrix = matrix.inverse.transpose;
                        for (int slot = 0; slot < mesh.subMeshCount; slot++)
                        {
                            var material = renderer.sharedMaterials[slot];
                            if (!material.name.StartsWith("MI_Cab_Plastic", StringComparison.Ordinal)) continue;
                            var texture = material.GetTexture("_AO");
                            var indices = mesh.GetTriangles(slot);
                            for (int j = 0; j < indices.Length; j += 3)
                            {
                                int a = indices[j], b = indices[j + 1], c = indices[j + 2];
                                if (data[a].y + data[b].y + data[c].y <= 0) continue;
                                var normal = normalMatrix.MultiplyVector(normals[a] + normals[b] + normals[c]).normalized;
                                if (Vector3.Dot(normal, rig.transform.up) < .35f) continue;
                                var p = matrix.MultiplyPoint3x4(vertices[a]); var q = matrix.MultiplyPoint3x4(vertices[b]); var r = matrix.MultiplyPoint3x4(vertices[c]);
                                var viewport = camera.WorldToViewportPoint((p + q + r) / 3);
                                if (viewport.z <= 0 || viewport.x < 0 || viewport.x > 1 || viewport.y < 0 || viewport.y > 1) continue;
                                var detailMetric = Singular(q - p, r - p, uv[b] - uv[a], uv[c] - uv[a]);
                                var aoMetric = Singular(q - p, r - p, ao[b] - ao[a], ao[c] - ao[a]) * texture.width;
                                text.AppendLine(string.Format(CultureInfo.InvariantCulture, "{0}\t{1}\t{2:R}\t{3:R}\t{4:R}\t{5:R}\t{6:R}\t{7:R}",
                                    renderer.name, j / 3, viewport.x, viewport.y, detailMetric.x, detailMetric.y, aoMetric.x, aoMetric.y));
                                rows++;
                            }
                        }
                    }
                    Directory.CreateDirectory(output); File.WriteAllText(Path.Combine(output, "metrics.tsv"), text.ToString());
                }
                catch (Exception exception) { failure = exception; }
            }
            RenderPipelineManager.beginCameraRendering += Measure;
            try
            {
                int rendered = VisualQaRunner.Render("WorldC_High", 1920, 1080, "High", output, "clear", "cab-grain");
                if (failure != null) throw failure;
                if (rendered != 1 || rows == 0) throw new InvalidOperationException("Missing AO UV metric evidence");
                Debug.Log("CAB_AO_UV_AUDIT rows=" + rows); exit = 0;
            }
            catch (Exception exception) { Debug.LogException(exception); }
            finally { RenderPipelineManager.beginCameraRendering -= Measure; }
            Debug.Log("CAB_AO_UV_AUDIT_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
