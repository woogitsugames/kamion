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
        public void SlipLaneClosure_MergesIntoItsCarriageway_OneSignPerCarriageway()
        {
            // Maczka at the west edge (WorldC scene, 2026-11-12): each carriageway (10 m) and its trunk_link (7 / 6.5 m)
            // were closed 0.5 - 0.9 m apart, so two B-1 discs overlapped on each carriageway (review s15-0141 P1).
            var closures = new List<WorldBoundary.Closure>
            {
                Closure(-991.63f, 47.04f, 10f, -95.40f), Closure(-1002.02f, 58.19f, 10f, -95.21f),
                Closure(-1002.02f, 58.74f, 7f, -89.56f), Closure(-991.63f, 46.10f, 6.5f, -101.88f),
                Closure(215.12f, -1015.32f, 7f, 118.54f), Closure(209.94f, -1015.32f, 7f, -151.34f),   // crossing roads: kept
            };
            var visible = Call<List<WorldBoundary.Closure>>("MergeOverlappingClosures", closures);
            Assert.AreEqual(4, visible.Count, "two carriageways + two crossing service roads");
            Assert.AreEqual(6, closures.Count, "input (colliders, WorldBoundary) untouched");
            // No two parallel visible closures (so no two B-1 discs) closer than 2 m.
            for (int i = 0; i < visible.Count; i++)
                for (int j = i + 1; j < visible.Count; j++)
                    if (Mathf.Abs(Mathf.DeltaAngle(visible[i].headingDeg, visible[j].headingDeg)) < 25f)
                        Assert.Greater(Vector3.Distance(visible[i].localPos, visible[j].localPos), 2f);
            // The merged span covers both originals: 10 m carriageway widened by the lateral offset (< 1 m here).
            Assert.That(visible[0].widthM, Is.InRange(10f, 11.5f));
            Assert.That(visible[0].headingDeg, Is.EqualTo(-95.40f).Within(0.01f), "frame of the wider road");
            var mesh = new Mesh();
            try
            {
                Builder.GetMethod("BuildClosureGroupMesh").Invoke(null, new object[] { mesh, visible.Take(2).ToList() });
                // Count B-1 discs by their white fan: the centre vertex at 1.85 m followed by the first rim vertex
                // 0.36 m (inner radius) straight above it.
                var pos = mesh.vertices; var col = mesh.colors32;
                int discs = 0;
                for (int i = 0; i + 1 < pos.Length; i++)
                    if (col[i].g > 180 && Mathf.Abs(pos[i].y - 131.85f) < 1e-3f && Mathf.Abs(pos[i + 1].y - pos[i].y - 0.36f) < 1e-3f
                        && Vector3.Distance(new Vector3(pos[i].x, 0f, pos[i].z), new Vector3(pos[i + 1].x, 0f, pos[i + 1].z)) < 1e-3f) discs++;
                Assert.AreEqual(2, discs, "one B-1 disc per carriageway");
            }
            finally { Object.DestroyImmediate(mesh); }
        }

        [Test]
        public void CarriagewaysAcrossAMedian_AndClosuresFurtherAlongTheRoad_AreNotMerged()
        {
            // Tysiaclecia north edge: two 7.5 m carriageways 16 m apart (spans 12.5 m) - a median between them.
            var closures = new List<WorldBoundary.Closure>
            {
                Closure(-856.52f, 965.25f, 7.5f, -11.73f), Closure(-846.74f, 977.89f, 7.5f, -11.99f),
                Closure(0f, 0f, 7f, 0f), Closure(3f, 40f, 7f, 0f),   // same line, 40 m further along the road
            };
            Assert.AreEqual(4, Call<List<WorldBoundary.Closure>>("MergeOverlappingClosures", closures).Count);
        }

        [Test]
        public void SignWhite_IsBrightSheeting_NotConcreteGrey()
        {
            var mesh = new Mesh();
            try
            {
                Builder.GetMethod("BuildClosureGroupMesh").Invoke(null, new object[] { mesh, new List<WorldBoundary.Closure> { Closure(0f, 0f, 10f) } });
                // Paint whites (the concrete submesh carries plain 255 = "no tint").
                var whites = mesh.colors32.Where(c => c.r > 150 && c.g > 150 && c.b > 150 && c.r < 255).ToList();
                Assert.Greater(whites.Count, 100);
                Assert.GreaterOrEqual(whites.Min(c => c.g), 200, "linear albedo >= 0.78 (sRGB >= 0.90)");
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
