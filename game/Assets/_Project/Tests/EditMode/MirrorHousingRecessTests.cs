using Game.Editor.Setup;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    public class MirrorHousingRecessTests
    {
        [Test]
        public void Recess_KeepsBudgetChannelsAndUnrelatedBody_InVehicleFrame()
        {
            // A backing plate plus a separate body panel, with a non-identity mesh frame.
            var frame = Matrix4x4.TRS(new Vector3(0.4f, 0.2f, -0.3f), Quaternion.Euler(8, 17, 4), Vector3.one);
            var original = new[] {
                new Vector3(-.07f, -.2f, -.004f), new Vector3(.07f, -.2f, -.004f),
                new Vector3(.07f, .2f, -.004f), new Vector3(-.07f, .2f, -.004f),
                new Vector3(1, 0, 0), new Vector3(2, 0, 0), new Vector3(1, 1, 0)
            };
            var local = new Vector3[original.Length];
            var normals = new Vector3[local.Length];
            var tangents = new Vector4[local.Length];
            var uv = new Vector2[local.Length];
            var colours = new Color32[local.Length];
            for (int i = 0; i < local.Length; i++)
            {
                local[i] = frame.inverse.MultiplyPoint3x4(original[i]);
                normals[i] = frame.inverse.MultiplyVector(Vector3.forward);
                Vector3 t = frame.inverse.MultiplyVector(Vector3.right);
                tangents[i] = new Vector4(t.x, t.y, t.z, 1);
                uv[i] = new Vector2(i * .1f, i * .07f);
                colours[i] = new Color32((byte)(10 + i), 20, 30, 200);
            }
            var src = new Mesh { vertices = local, normals = normals, tangents = tangents, uv = uv, uv2 = uv, colors32 = colours, subMeshCount = 2 };
            src.SetTriangles(new[] { 0, 1, 2, 0, 2, 3 }, 0);
            src.SetTriangles(new[] { 4, 5, 6 }, 1);
            var opening = new MirrorHousingRecess.Opening {
                centre = Vector3.zero, right = Vector3.right, up = Vector3.up, normal = Vector3.forward,
                halfWidth = .097f, bottom = -.3f, top = .3f
            };
            Mesh result = null;
            try
            {
                result = MirrorHousingRecess.Apply(src, frame, new[] { opening }, out int moved);
                Assert.NotNull(result);
                Assert.AreEqual(4, moved);
                Assert.AreEqual(src.vertexCount, result.vertexCount);
                Assert.AreEqual(src.subMeshCount, result.subMeshCount);
                for (int s = 0; s < src.subMeshCount; s++) CollectionAssert.AreEqual(src.GetTriangles(s), result.GetTriangles(s));
                CollectionAssert.AreEqual(uv, result.uv);
                CollectionAssert.AreEqual(uv, result.uv2);
                CollectionAssert.AreEqual(colours, result.colors32);
                CollectionAssert.AreEqual(local, src.vertices, "source asset is immutable");
                var points = result.vertices;
                for (int i = 0; i < 4; i++)
                    Assert.That(frame.MultiplyPoint3x4(points[i]).z, Is.EqualTo(-MirrorHousingRecess.Depth).Within(1e-6f));
                for (int i = 4; i < points.Length; i++) Assert.AreEqual(local[i], points[i], "unrelated cab body unchanged");
                Assert.IsNull(MirrorHousingRecess.Apply(result, frame, new[] { opening }, out _), "rebuild does not keep pushing the backing");
            }
            finally { Object.DestroyImmediate(result); Object.DestroyImmediate(src); }
        }

        [Test]
        public void Recess_KeepsOuterBezelAndRearCap()
        {
            var src = new Mesh { vertices = new[] { new Vector3(.12f, 0, 0), new Vector3(0, 0, -.08f), new Vector3(0, .5f, 0) }, triangles = new[] { 0, 1, 2 } };
            try
            {
                var opening = new MirrorHousingRecess.Opening { right = Vector3.right, up = Vector3.up,
                    normal = Vector3.forward, halfWidth = .097f, bottom = -.3f, top = .3f };
                Assert.IsNull(MirrorHousingRecess.Apply(src, Matrix4x4.identity, new[] { opening }, out int moved));
                Assert.AreEqual(0, moved);
            }
            finally { Object.DestroyImmediate(src); }
        }
    }
}
