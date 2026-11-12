using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Game.World;
using NUnit.Framework;
using UnityEngine;
using Object = UnityEngine.Object;

namespace Game.Tests.EditMode
{
    /// <summary>ADR 0141: grouped road closures (double U-20 board, B-1 on carriageways) and the far skyline bounds.</summary>
    public class WorldEdgeClosureSkylineTests
    {
        static readonly System.Type Builder = System.Type.GetType("Game.World.Import.WorldEdgeBuilder, Game.World.Import.Editor", true);

        static T Call<T>(string method, params object[] args) =>
            (T)Builder.GetMethod(method, BindingFlags.Public | BindingFlags.Static).Invoke(null, args);

        static WorldBoundary.Closure Closure(float e, float n, float width, float heading = 0f) =>
            new WorldBoundary.Closure { localPos = new Vector3(e, 130f, n), headingDeg = heading, widthM = width, road = "t" };

        [Test]
        public void NeighbouringClosures_ShareAGroup_DistantOnesDoNot()
        {
            var closures = new List<WorldBoundary.Closure>
            {
                Closure(0f, -1000f, 7f), Closure(100f, -1000f, 4f), Closure(220f, -1000f, 4f),   // chain: 100 m and 120 m links
                Closure(600f, -1000f, 7f),
            };
            var groups = Call<List<List<int>>>("ClusterClosures", closures, 150f);
            Assert.AreEqual(2, groups.Count);
            CollectionAssert.AreEqual(new[] { 0, 1, 2 }, groups[0]);
            CollectionAssert.AreEqual(new[] { 3 }, groups[1]);
        }

        [Test]
        public void GroupMesh_HasTwoSubmeshes_AndSpansTheCarriagewayInRegionSpace()
        {
            var mesh = new Mesh();
            try
            {
                var closures = new List<WorldBoundary.Closure> { Closure(100f, -900f, 10f, 90f) };   // road heading east
                Builder.GetMethod("BuildClosureGroupMesh").Invoke(null, new object[] { mesh, closures });
                Assert.AreEqual(2, mesh.subMeshCount, "concrete + paint");
                Assert.AreEqual(mesh.vertexCount, mesh.colors32.Length, "paint albedo in COLOR_0");
                // Heading 90 deg: the barrier line (closure x) runs north-south, 10 m + 5 m shoulders.
                Assert.That(mesh.bounds.size.z, Is.EqualTo(15f).Within(0.2f));
                Assert.That(mesh.bounds.center.x, Is.EqualTo(100f).Within(1f));
                Assert.That(mesh.bounds.min.y, Is.EqualTo(130f).Within(0.01f));
                // B-1 on a 10 m carriageway: top of the disc 1.85 + 0.45 m above the road.
                Assert.That(mesh.bounds.max.y, Is.EqualTo(132.30f).Within(0.02f));
                var reds = mesh.colors32.Count(c => c.r > 80 && c.g < 20);
                var whites = mesh.colors32.Count(c => c.r > 150 && c.g > 150 && c.a == 0);
                Assert.Greater(reds, 100); Assert.Greater(whites, 100);
            }
            finally { Object.DestroyImmediate(mesh); }
        }

        [Test]
        public void ServiceRoadClosure_HasBoardsButNoSign_AndFewerTrianglesThanTheOldLayout()
        {
            var mesh = new Mesh();
            try
            {
                var closures = new List<WorldBoundary.Closure> { Closure(0f, 0f, 4f) };
                Builder.GetMethod("BuildClosureGroupMesh").Invoke(null, new object[] { mesh, closures });
                Assert.That(mesh.bounds.max.y, Is.EqualTo(131.25f).Within(0.02f), "post tops 1.25 m, no sign");
                // Old single-board layout for a 9 m span: 5 barriers x 10 + 18 fields x 10 + 5 posts x 10 = 280 triangles.
                long tris = (long)(mesh.GetIndexCount(0) + mesh.GetIndexCount(1)) / 3;
                Assert.Less(tris, 280);
            }
            finally { Object.DestroyImmediate(mesh); }
        }

        [Test]
        public void SkylineBounds_ContainTheWholeTile()
        {
            var ring = new Bounds(new Vector3(1400f, 160f, 0f), new Vector3(300f, 120f, 2600f));
            var b = Call<Bounds>("SkylineBounds", ring, new Vector2(-1024f, -1024f), new Vector2(1024f, 1024f));
            Assert.IsTrue(b.Contains(new Vector3(-1000f, 150f, 900f)), "a camera anywhere on the tile is inside: never culled by the far plane");
            Assert.IsTrue(b.Contains(new Vector3(1500f, 200f, 1200f)), "the ring itself stays inside");
        }
    }
}
