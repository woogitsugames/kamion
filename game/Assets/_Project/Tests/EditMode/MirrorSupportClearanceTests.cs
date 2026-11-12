using System;
using Game.Editor.Setup;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests.EditMode
{
    public class MirrorSupportClearanceTests
    {
        static MirrorSupportClearance.Support Support => new MirrorSupportClearance.Support {
            name = "support", start = Vector3.zero, end = Vector3.right,
            right = Vector3.forward, up = Vector3.up, halfWidth = .02f, halfHeight = .035f, shift = new Vector3(0, 0, .08f),
        };

        [Test]
        public void RearAttachmentMoves_AnchorAndOtherPanelStay_TopologyAndUvsStay()
        {
            var frame = Matrix4x4.TRS(new Vector3(2, 3, 4), Quaternion.Euler(8, 17, 4), Vector3.one);
            var world = new[] { new Vector3(0, -.02f, 0), new Vector3(1, -.02f, 0),
                new Vector3(1, .02f, 0), new Vector3(0, .02f, 0),
                new Vector3(2, 0, 0), new Vector3(3, 0, 0), new Vector3(2, 1, 0) };
            var local = Array.ConvertAll(world, frame.inverse.MultiplyPoint3x4);
            var source = new Mesh { vertices = local, triangles = new[] { 0, 1, 2, 0, 2, 3, 4, 5, 6 },
                uv = new[] { Vector2.zero, Vector2.right, Vector2.one, Vector2.up, Vector2.zero, Vector2.right, Vector2.up } };
            source.RecalculateNormals(); source.RecalculateTangents();
            Mesh result = null;
            try
            {
                result = MirrorSupportClearance.Apply(source, frame, new[] { Support }, out int moved);
                Assert.AreEqual(4, moved);
                CollectionAssert.AreEqual(source.triangles, result.triangles);
                CollectionAssert.AreEqual(source.uv, result.uv);
                CollectionAssert.AreEqual(local, source.vertices, "source remains reusable by other LOD/build paths");
                var output = result.vertices;
                for (int i = 4; i < local.Length; i++) Assert.AreEqual(local[i], output[i], "unrelated body panel");
                Vector3 anchor = (frame.MultiplyPoint3x4(output[0]) + frame.MultiplyPoint3x4(output[3])) * .5f;
                Vector3 rear = (frame.MultiplyPoint3x4(output[1]) + frame.MultiplyPoint3x4(output[2])) * .5f;
                Assert.Less(anchor.magnitude, 1e-5f, "cab anchor stays attached");
                Assert.Less((rear - Support.end - Support.shift).magnitude, 1e-5f, "rear attachment follows clearance data");
            }
            finally { Object.DestroyImmediate(source); if (result != null) Object.DestroyImmediate(result); }
        }

        [Test]
        public void MissingSupportFailsInsteadOfDeformingUnrelatedCab()
        {
            var source = new Mesh { vertices = new[] { Vector3.one * 5, Vector3.one * 6, Vector3.one * 7 }, triangles = new[] { 0, 1, 2 } };
            try { Assert.Throws<InvalidOperationException>(() => MirrorSupportClearance.Apply(source, Matrix4x4.identity, new[] { Support }, out _)); }
            finally { Object.DestroyImmediate(source); }
        }
    }
}
