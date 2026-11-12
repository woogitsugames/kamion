using System;
using System.Linq;
using Game.Editor.Setup;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    public class CabLeatherMappingTests
    {
        static Mesh Wheel(Matrix4x4 frame)
        {
            var points = new[] { new Vector3(.23f, 0, 0), new Vector3(.22f, .03f, .01f), new Vector3(.21f, .02f, -.01f),
                new Vector3(.03f, 0, 0), new Vector3(.02f, .03f, .01f), new Vector3(.01f, .02f, -.01f),
                new Vector3(-.23f, 0, 0), new Vector3(-.22f, .03f, .01f), new Vector3(-.21f, .02f, -.01f) };
            var mesh = new Mesh { vertices = points.Select(frame.inverse.MultiplyPoint3x4).ToArray(), subMeshCount = 2 };
            mesh.SetTriangles(new[] { 0, 1, 2, 3, 4, 5 }, 0);
            mesh.SetTriangles(new[] { 6, 7, 8 }, 1);
            mesh.uv = points.Select(p => new Vector2(p.x * 20, p.y * 20)).ToArray();
            mesh.uv2 = points.Select(p => new Vector2(p.x + .5f, p.y + .5f)).ToArray();
            mesh.uv3 = points.Select(_ => new Vector2(.7f, .8f)).ToArray();
            mesh.colors32 = points.Select(_ => new Color32(20, 30, 40, 50)).ToArray();
            mesh.RecalculateNormals(); mesh.RecalculateTangents();
            return mesh;
        }

        [Test]
        public void PhysicalRimScale_LeavesHubOtherMaterialsAndAoUntouched()
        {
            var frame = Matrix4x4.TRS(new Vector3(.2f, -.4f, .7f), Quaternion.Euler(21, 8, 17), Vector3.one);
            var source = Wheel(frame); Mesh result = null;
            var before = source.uv;
            try
            {
                result = CabLeatherMapping.Apply(source, frame, new[] { 0 }, .19f, .27f, .05f / .12f, out int count);
                Assert.AreEqual(3, count);
                for (int i = 0; i < before.Length; ++i)
                    Assert.That(Vector2.Distance(result.uv[i], before[i] * (i < 3 ? .05f / .12f : 1)), Is.LessThan(1e-6f));
                CollectionAssert.AreEqual(before, source.uv);
                CollectionAssert.AreEqual(source.vertices, result.vertices);
                CollectionAssert.AreEqual(source.uv2, result.uv2);
                CollectionAssert.AreEqual(source.uv3, result.uv3);
                CollectionAssert.AreEqual(source.colors32, result.colors32);
                CollectionAssert.AreEqual(source.normals, result.normals);
                CollectionAssert.AreEqual(source.tangents, result.tangents);
                Assert.AreEqual(source.bounds, result.bounds);
                Assert.AreEqual(source.subMeshCount, result.subMeshCount);
                for (int sub = 0; sub < source.subMeshCount; sub++) CollectionAssert.AreEqual(source.GetTriangles(sub), result.GetTriangles(sub));
            }
            finally { UnityEngine.Object.DestroyImmediate(source); if (result != null) UnityEngine.Object.DestroyImmediate(result); }
        }

        [TestCase(true)]
        [TestCase(false)]
        public void AmbiguousRimRegionFailsInsteadOfScalingOtherParts(bool sharedMaterialVertex)
        {
            var source = Wheel(Matrix4x4.identity);
            try
            {
                if (sharedMaterialVertex) source.SetTriangles(new[] { 0, 7, 8 }, 1);
                else source.SetTriangles(new[] { 0, 1, 3 }, 0);
                Assert.Throws<InvalidOperationException>(() => CabLeatherMapping.Apply(source, Matrix4x4.identity, new[] { 0 }, .19f, .27f, .05f / .12f, out _));
            }
            finally { UnityEngine.Object.DestroyImmediate(source); }
        }
    }
}
