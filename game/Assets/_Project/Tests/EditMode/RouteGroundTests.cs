using Game.Gameplay;
using Game.World;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0350 (build #9, -scene dk65-07: "no free place for the combination ... (collider 'col_asphalt')"): the route
    /// heights followed the terrain mesh 0.4-0.8 m UNDER the carriageway, because the first route points lay outside the
    /// tile (no hit, y = 0) and the "closest to the previous height" rule then took the lowest layer. The start box (0.5 m
    /// above the route) overlapped the road surface at every place. Measured on the build #9 scene (colprobe on
    /// World_dk65-07_High.unity): s = 90 m, asphalt 14.946 m, terrain 14.191 m = stored route height.
    /// </summary>
    public class RouteGroundTests
    {
        // dk65-07 start point (XZ 973.29, 381.56): the two ground layers under the route.
        const float Asphalt = 14.946f, Terrain = 14.191f;

        [Test]
        public void Pick_WithoutReference_TakesTheTopSurface()
        {
            Assert.That(RouteGround.Pick(new[] { Terrain, Asphalt }, 2, float.NaN), Is.EqualTo(Asphalt));
        }

        [Test]
        public void Pick_ReferenceOnTheTerrain_StillTakesTheRoadOverIt()
        {
            // The old rule (closest to the previous height) returned the terrain here and kept it for the whole route.
            Assert.That(RouteGround.Pick(new[] { Asphalt, Terrain }, 2, Terrain), Is.EqualTo(Asphalt));
        }

        [Test]
        public void Pick_KeepsViaductLevelsApart()
        {
            // Road under a bridge (deck 6 m above) and the deck over a road (6 m below): the level of the previous point.
            Assert.That(RouteGround.Pick(new[] { 16.0f, 10.1f, 9.6f }, 3, 10.0f), Is.EqualTo(10.1f));
            Assert.That(RouteGround.Pick(new[] { 16.05f, 10.0f }, 2, 16.0f), Is.EqualTo(16.05f));
            // No surface in the window: the closest one.
            Assert.That(RouteGround.Pick(new[] { 30.0f, 3.0f }, 2, 10.0f), Is.EqualTo(3.0f));
        }

        [Test]
        public void Pick_NoHit_IsUnknownNotZero()
        {
            Assert.That(float.IsNaN(RouteGround.Pick(new float[4], 0, float.NaN)));
            Assert.That(float.IsNaN(RouteGround.Pick(new float[4], 0, 12f)));
        }

        [Test]
        public void ImportSequence_RouteStartingOutsideTheTile_FollowsTheRoad()
        {
            // As WorldSceneBuilder: 2 points outside the tile (no hit), then asphalt over terrain on every point.
            var pts = new Vector3[8];
            float prev = float.NaN;
            for (int i = 0; i < pts.Length; i++)
            {
                float y = i < 2 ? RouteGround.Pick(new float[2], 0, prev) : RouteGround.Pick(new[] { Terrain - 0.01f * i, Asphalt - 0.01f * i }, 2, prev);
                pts[i] = new Vector3(0f, y, 2f * i);
                if (!float.IsNaN(y)) prev = y;
            }
            Assert.That(RouteGround.FillMissing(pts), Is.EqualTo(2));
            for (int i = 0; i < pts.Length; i++)
                Assert.That(pts[i].y, Is.EqualTo(Asphalt - 0.01f * Mathf.Max(i, 2)).Within(1e-4f), "point " + i);
        }

        [Test]
        public void FillMissing_InterpolatesAndExtends()
        {
            var pts = new[] { new Vector3(0, float.NaN, 0), new Vector3(0, 10f, 1), new Vector3(0, float.NaN, 2), new Vector3(0, float.NaN, 3), new Vector3(0, 13f, 4), new Vector3(0, float.NaN, 5) };
            Assert.That(RouteGround.FillMissing(pts), Is.EqualTo(4));
            Assert.That(pts[0].y, Is.EqualTo(10f));
            Assert.That(pts[2].y, Is.EqualTo(11f).Within(1e-5f));
            Assert.That(pts[3].y, Is.EqualTo(12f).Within(1e-5f));
            Assert.That(pts[5].y, Is.EqualTo(13f));
            var none = new[] { new Vector3(0, float.NaN, 0), new Vector3(0, float.NaN, 1) };
            Assert.That(RouteGround.FillMissing(none), Is.EqualTo(2));
            Assert.That(none[0].y, Is.EqualTo(0f));
        }

        // ---------------- physics: the start check on an old scene (route stored on the terrain) ----------------

        [SetUp]
        public void EmptyScene() => EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // The WorldRoute left in the scene would be picked up by later tests that search the scene (WorldStreamerHook0273Tests:
        // the route continuation appended this 101-point route).
        [TearDown]
        public void LeaveEmptyScene() => EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        static void Quad(string name, float y, float halfWidth, float length)
        {
            var mesh = new Mesh
            {
                vertices = new[] { new Vector3(-halfWidth, y, -10f), new Vector3(halfWidth, y, -10f), new Vector3(-halfWidth, y, length), new Vector3(halfWidth, y, length) },
                triangles = new[] { 0, 2, 1, 1, 2, 3 },
            };
            mesh.RecalculateBounds();
            var go = new GameObject(name);
            go.AddComponent<MeshCollider>().sharedMesh = mesh;
        }

        static WorldRoute RouteOnTheTerrain(float length)
        {
            var route = new GameObject("Route_start").AddComponent<WorldRoute>();
            int n = Mathf.RoundToInt(length / 2f) + 1;
            route.points = new Vector3[n];
            route.distances = new float[n];
            for (int i = 0; i < n; i++) { route.points[i] = new Vector3(0f, Terrain, 2f * i); route.distances[i] = 2f * i; }
            return route;
        }

        [Test]
        public void StartCheck_RouteStoredOnTheTerrainUnderTheRoad_IsFree()
        {
            Quad("col_terrain", Terrain, 40f, 220f);
            Quad("col_asphalt", Asphalt, 3.5f, 220f);
            var route = RouteOnTheTerrain(200f);
            Physics.SyncTransforms();

            Assert.That(SpawnSafety.RoadY(route.PointAt(90f), null), Is.EqualTo(Asphalt).Within(1e-3f));
            var b = SpawnSafety.Check(route, 90f, null, out Collider hit);
            Assert.That(b, Is.EqualTo(StartBlock.Free), "blocked by " + (hit != null ? hit.name : "-") + " (build #9 dk65-07: col_asphalt)");
        }

        /// <summary>
        /// Real data (skipped when the scene is not imported): the importer's route height rule (WorldSceneBuilder.RouteHeight
        /// + FillMissing, called by reflection) on the dk65-07 ground collision gives the carriageway, not the terrain the old
        /// import stored (14.19 m at the start vs asphalt 14.95 m).
        /// </summary>
        [Test]
        public void Dk65_07_ImporterRouteHeights_LieOnTheCarriageway()
        {
            const string scene = "Assets/_Generated/World/dk65-07/World_dk65-07.unity";
            if (!System.IO.File.Exists(System.IO.Path.Combine(Game.Editor.Build.EditorTools.RepoRoot, "game", scene))) Assert.Ignore("dk65-07 not imported");
            EditorSceneManager.OpenScene(scene, OpenSceneMode.Single);
            foreach (var cooker in Object.FindObjectsByType<WorldCollisionCooker>(FindObjectsSortMode.None))
                foreach (var c in cooker.colliders) if (c != null && c.sharedMesh != null) c.enabled = true;
            Physics.SyncTransforms();
            var route = Object.FindAnyObjectByType<WorldRoute>();
            var height = System.Type.GetType("Game.World.Import.WorldSceneBuilder, Game.World.Import.Editor", true)
                .GetMethod("RouteHeight", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);
            var pts = new Vector3[route.points.Length];
            float prev = float.NaN, oldBelow = 0f;
            for (int i = 0; i < pts.Length; i++)
            {
                Vector3 w = route.transform.TransformPoint(route.points[i]);
                float y = (float)height.Invoke(null, new object[] { w.x, w.z, prev });
                pts[i] = new Vector3(w.x, y, w.z);
                if (!float.IsNaN(y)) prev = y;
            }
            RouteGround.FillMissing(pts);
            int checkedPts = 0;
            for (int i = 0; i < pts.Length; i++)
            {
                if (route.distances[i] < 20f || route.distances[i] > 200f) continue;   // the catalog start (90 m) and the search ahead
                Assert.IsTrue(AsphaltY(pts[i].x, pts[i].z, out float asphalt), "no col_asphalt under route point " + i);
                Assert.That(pts[i].y, Is.EqualTo(asphalt).Within(0.02f), "route point " + i + " at s " + route.distances[i]);
                oldBelow = Mathf.Max(oldBelow, asphalt - route.transform.TransformPoint(route.points[i]).y);
                checkedPts++;
            }
            Assert.That(checkedPts, Is.GreaterThan(50));
            TestContext.WriteLine($"dk65-07: {checkedPts} route points on col_asphalt; the stored (old import) route lay up to {oldBelow:F2} m under it");
        }

        static bool AsphaltY(float x, float z, out float y)
        {
            y = float.NegativeInfinity;
            foreach (var h in Physics.RaycastAll(new Vector3(x, 400f, z), Vector3.down, 800f))
                if (h.collider.name == "col_asphalt" && h.point.y > y) y = h.point.y;
            return !float.IsNegativeInfinity(y);
        }

        [Test]
        public void StartCheck_ObstacleOnTheRoad_IsStillFound()
        {
            Quad("col_terrain", Terrain, 40f, 220f);
            Quad("col_asphalt", Asphalt, 3.5f, 220f);
            var route = RouteOnTheTerrain(200f);
            // A 1 m high box (bale / barrier) on the carriageway at the start: an obstacle, never ground.
            var block = GameObject.CreatePrimitive(PrimitiveType.Cube);
            block.name = "bale";
            block.transform.position = new Vector3(0f, Asphalt + 0.5f, 90f);
            Physics.SyncTransforms();

            var b = SpawnSafety.Check(route, 90f, null, out Collider hit);
            Assert.That(b, Is.EqualTo(StartBlock.Collider));
            Assert.That(hit.name, Is.EqualTo("bale"));
        }
    }
}
