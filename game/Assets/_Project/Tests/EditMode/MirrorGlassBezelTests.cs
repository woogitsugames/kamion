using System.Linq;
using Game.Editor.Setup;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    public class MirrorGlassBezelTests
    {
        [Test]
        public void BezelCoversSharpGlassCorners_LeavesCentreOpen_UsesExistingSlotAndPreservesBody()
        {
            var frame = Matrix4x4.TRS(new Vector3(.4f, .2f, -.3f), Quaternion.Euler(8, 17, 4), Vector3.one);
            var points = new[] { new Vector3(2, 0, 0), new Vector3(3, 0, 0), new Vector3(3, 1, 0), new Vector3(2, 1, 0),
                new Vector3(.2f, -.2f, -.03f), new Vector3(.4f, -.2f, -.03f), new Vector3(.3f, -.1f, -.03f) };
            var source = new Mesh { vertices = points.Select(frame.inverse.MultiplyPoint3x4).ToArray(), subMeshCount = 2 };
            source.SetTriangles(new[] { 0, 1, 2, 0, 2, 3 }, 0); source.SetTriangles(new[] { 4, 5, 6 }, 1);
            source.uv = points.Select(p => new Vector2(p.x, p.y)).ToArray();
            source.uv2 = source.uv.Select(p => p * .5f).ToArray(); source.uv3 = source.uv.Select(p => p * .25f).ToArray();
            source.colors32 = points.Select(_ => new Color32(20, 30, 40, 50)).ToArray();
            source.RecalculateNormals(); source.RecalculateTangents();
            var original = source.vertices;
            Mesh result = null;
            try
            {
                var opening = new MirrorGlassBezel.Opening { centre = Vector3.zero, right = Vector3.right, up = Vector3.up,
                    normal = Vector3.forward, width = .2f, height = .44f };
                result = MirrorGlassBezel.Apply(source, frame, new[] { opening }, 1, new Vector3(.3f, -.15f, -.03f), out int triangles);
                Assert.AreEqual(120, triangles);
                Assert.AreEqual(source.subMeshCount, result.subMeshCount, "no extra renderer/material draw");
                CollectionAssert.AreEqual(source.GetTriangles(0), result.GetTriangles(0));
                CollectionAssert.AreEqual(original, source.vertices, "source remains untouched");
                CollectionAssert.AreEqual(original, result.vertices.Take(original.Length));
                CollectionAssert.AreEqual(source.uv, result.uv.Take(original.Length));
                CollectionAssert.AreEqual(source.uv2, result.uv2.Take(original.Length));
                CollectionAssert.AreEqual(source.uv3, result.uv3.Take(original.Length));
                CollectionAssert.AreEqual(source.colors32, result.colors32.Take(original.Length));
                var vertices = result.vertices.Select(frame.MultiplyPoint3x4).ToArray();
                var indices = result.GetTriangles(1);
                float Cross(Vector2 a, Vector2 b) => a.x * b.y - a.y * b.x;
                bool Covered(Vector2 point)
                {
                    for (int t = 3; t < indices.Length; t += 3)
                    {
                        Vector3 a = vertices[indices[t]], b = vertices[indices[t + 1]], c = vertices[indices[t + 2]];
                        if (Mathf.Abs(a.z - MirrorGlassBezel.Front) > 1e-5f || Mathf.Abs(b.z - MirrorGlassBezel.Front) > 1e-5f || Mathf.Abs(c.z - MirrorGlassBezel.Front) > 1e-5f) continue;
                        Vector2 v = new Vector2(b.x - a.x, b.y - a.y), w = new Vector2(c.x - a.x, c.y - a.y), p = point - new Vector2(a.x, a.y);
                        float denominator = Cross(v, w);
                        if (Mathf.Abs(denominator) < 1e-10f) continue;
                        float x = Cross(p, w) / denominator, y = Cross(v, p) / denominator;
                        if (x >= -1e-5f && y >= -1e-5f && x + y <= 1.00001f) return true;
                    }
                    return false;
                }
                Assert.IsFalse(Covered(Vector2.zero), "reflective centre stays open");
                foreach (float x in new[] { -.1f, .1f }) foreach (float y in new[] { -.22f, .22f })
                    Assert.IsTrue(Covered(new Vector2(x, y)), "sharp glass tip is covered by opaque rounded trim");
            }
            finally { Object.DestroyImmediate(source); if (result != null) Object.DestroyImmediate(result); }
        }
    }
}
