using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using Game.Editor.Build;
using Game.Gameplay;
using Game.Vehicle.Runtime;
using Game.World;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0262: the start of every region stands behind the region-edge closure its start route enters through, clear of
    /// every static collider, with a closure-free route ahead. Owner report 2026-11-15 (A16, APK d67-full): every start
    /// outside a barrier row ("road end behind, blocks ahead"), dk65-05 inside the row.
    /// </summary>
    public class StartClearanceTests
    {
        static readonly System.Type EdgeBuilder = System.Type.GetType("Game.World.Import.WorldEdgeBuilder, Game.World.Import.Editor", true);

        static List<WorldBoundary.Closure> RegionClosures(string region)
        {
            var raw = EdgeBuilder.GetMethod("PlanRegionClosures", BindingFlags.Public | BindingFlags.Static).Invoke(null, new object[] { region });
            return (List<WorldBoundary.Closure>)EdgeBuilder.GetMethod("ResolveClosures", BindingFlags.Public | BindingFlags.Static).Invoke(null, new[] { raw });
        }

        public static IEnumerable<string> RegionIds() => RegionCatalog.Load().regions.Select(r => r.id);

        static string DataDir(string region) => Path.Combine(EditorTools.RepoRoot, "Data", "Regions", region);

        static void ReadRoute(string region, out Vector3[] pts, out float[] dist)
        {
            string path = Path.Combine(DataDir(region), "route_start.json");
            string text = File.ReadAllText(path);
            int at = text.IndexOf("\"points_en\"", System.StringComparison.Ordinal);
            Assert.GreaterOrEqual(at, 0, path + ": points_en");
            int end = text.IndexOf("]]", at, System.StringComparison.Ordinal);
            var list = new List<Vector3>();
            foreach (Match m in Regex.Matches(text.Substring(at, end - at + 2), @"\[\s*(-?[0-9.eE+-]+)\s*,\s*(-?[0-9.eE+-]+)\s*\]"))
                list.Add(new Vector3(float.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture), 0f, float.Parse(m.Groups[2].Value, CultureInfo.InvariantCulture)));
            Assert.Greater(list.Count, 1, path);
            pts = list.ToArray();
            dist = new float[pts.Length];
            for (int i = 1; i < pts.Length; i++) dist[i] = dist[i - 1] + Vector3.Distance(pts[i - 1], pts[i]);
        }

        static string F(float v) => float.IsInfinity(v) ? "none" : v.ToString("F1", CultureInfo.InvariantCulture);

        // ------------------------------------------------------------------ dimensions

        /// <summary>The footprint constants follow the vehicle definitions (tractor dims, fifth wheel, trailer body).</summary>
        [Test]
        public void Footprint_FollowsTheVehicleDefinitions()
        {
            var td = new TractorDimensions();
            Assert.AreEqual(td.FrontFaceZ, StartClearance.FrontM, 0.02f, "tractor origin (rear axle) -> front face");
            string defs = Path.Combine(EditorTools.RepoRoot, "game", "Assets", "_Project", "Vehicle", "Physics", "Definitions", "Data");
            float Num(string file, string pattern)
            {
                var m = Regex.Match(File.ReadAllText(Path.Combine(defs, file)), pattern, RegexOptions.Singleline);
                Assert.IsTrue(m.Success, file + ": " + pattern);
                return float.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
            }
            float fifthWheelZ = Num("tractor_4x2_generic.vehicle.json", "\"fifthWheel\"\\s*:\\s*\\{\\s*\"position\"\\s*:\\s*\\{[^}]*\"z\"\\s*:\\s*(-?[0-9.]+)");
            float bayFrontZ = Num("curtainsider_tridem_13_6.trailer.json", "\"cargoBay\"\\s*:\\s*\\{[^}]*\"frontZ\"\\s*:\\s*(-?[0-9.]+)");
            var tr = new TrailerDimensions();
            float rear = tr.length - (bayFrontZ + tr.frontWall) - fifthWheelZ;
            Assert.AreEqual(rear, StartClearance.RearM, 0.02f, "tractor origin -> rear end of the coupled trailer");
            Assert.AreEqual(tr.width * 0.5f, StartClearance.HalfWidthM, 0.001f);
            Assert.GreaterOrEqual(StartClearance.MarginM, 0.5f, "task: at least 0.5 m around the combination");
            Assert.Greater(StartClearance.BehindClosureM, StartClearance.RearM + StartClearance.BoardsM + StartClearance.MarginM);
        }

        // ------------------------------------------------------------------ geometry (synthetic)

        static WorldBoundary.Closure Row(float e, float n, float headingDeg, float width = 7f) =>
            new WorldBoundary.Closure { localPos = new Vector3(e, 0f, n), headingDeg = headingDeg, widthM = width, road = "t" };

        static void Line(float fromN, float toN, float e, out Vector3[] pts, out float[] dist)
        {
            int n = Mathf.RoundToInt(Mathf.Abs(toN - fromN) / 2f) + 1;
            pts = new Vector3[n]; dist = new float[n];
            for (int i = 0; i < n; i++)
            {
                pts[i] = new Vector3(e, 0f, Mathf.Lerp(fromN, toN, i / (float)(n - 1)));
                if (i > 0) dist[i] = dist[i - 1] + Vector3.Distance(pts[i - 1], pts[i]);
            }
        }

        [Test]
        public void Crossings_EntryAtTheStart_ExitAtTheEnd_AndRowsBesideTheRouteAreIgnored()
        {
            // Route northwards from the south edge (n = 0) to the north edge (n = 1000), right lane 1.75 m east of the axis.
            Line(0f, 1000f, 1.75f, out var pts, out var dist);
            var closures = new List<WorldBoundary.Closure>
            {
                Row(0f, 60f, 180f),            // road leaves southwards: the route enters through this row
                Row(0f, 940f, 0f),             // road leaves northwards: the route leaves through this row
                Row(40f, 500f, 90f),           // side road to the east, row 40 m beside the route
                Row(12f, 300f, 0f, 4f),        // neighbouring carriageway: row ends 12 - 4.5 = 7.5 m from the axis
            };
            var found = new List<StartClearance.Crossing>();
            StartClearance.Crossings(pts, dist, closures, found);
            Assert.AreEqual(2, found.Count);
            Assert.AreEqual(60f, found[0].s, 0.01f); Assert.IsTrue(found[0].entry); Assert.AreEqual(0, found[0].closure);
            Assert.AreEqual(940f, found[1].s, 0.01f); Assert.IsFalse(found[1].entry);

            Assert.AreEqual(60f + StartClearance.BehindClosureM, StartClearance.SafeStartS(pts, dist, closures, 12f), 0.01f, "12 m is outside the row");
            Assert.AreEqual(62f + StartClearance.BehindClosureM - 2f, StartClearance.SafeStartS(pts, dist, closures, 62f), 0.01f, "inside the row but the trailer is in it");
            Assert.AreEqual(200f, StartClearance.SafeStartS(pts, dist, closures, 200f), 0.01f, "a start well inside stays");
            Assert.AreEqual(12f, StartClearance.SafeStartS(pts, dist, new List<WorldBoundary.Closure>(), 12f), "no closures: unchanged (region C)");

            StartClearance.FreeAround(found, 85f, out float behind, out float ahead);
            Assert.AreEqual(85f - StartClearance.RearM - 60f - StartClearance.BoardsM, behind, 0.01f);
            Assert.AreEqual(940f - StartClearance.BoardsM - 85f - StartClearance.FrontM, ahead, 0.01f);
            StartClearance.FreeAround(found, 12f, out behind, out ahead);
            Assert.IsTrue(float.IsPositiveInfinity(behind));
            Assert.AreEqual(60f - 12f - StartClearance.FrontM, ahead, 0.01f, "the old start: the row 43 m ahead of the bumper");
        }

        [Test]
        public void Crossings_RouteNodeExactlyOnTheRow_CountsOnce()
        {
            Line(0f, 200f, 0f, out var pts, out var dist);   // points every 2 m: one lies exactly on n = 60
            var found = new List<StartClearance.Crossing>();
            StartClearance.Crossings(pts, dist, new List<WorldBoundary.Closure> { Row(0f, 60f, 180f) }, found);
            Assert.AreEqual(1, found.Count);
            Assert.AreEqual(60f, found[0].s, 0.01f);
        }

        // ------------------------------------------------------------------ committed data: every region of the catalog

        /// <summary>
        /// (a) closures: the catalog start of a region is behind every closure its route enters through, the rear end of the
        /// trailer at least <see cref="StartClearance.MarginM"/> clear of the boards; (b) no closure row on the route within
        /// <see cref="StartClearance.AheadFreeM"/> ahead of the bumper. Real closures: WorldEdgeBuilder.PlanRegionClosures +
        /// ResolveClosures on the committed graph (the one implementation, ADR 0169).
        /// </summary>
        [TestCaseSource(nameof(RegionIds))]
        public void CatalogStart_IsBehindTheEntryClosure_AndTheRouteAheadIsOpen(string region)
        {
            var r = RegionCatalog.Load().Find(region);
            ReadRoute(region, out var pts, out var dist);
            float length = dist[dist.Length - 1];
            float s = RegionStart.ClampStartS(r.startS, r.routeLengthM);
            var crossings = new List<StartClearance.Crossing>();
            StartClearance.Crossings(pts, dist, RegionClosures(region), crossings);
            string where = region + ": startS " + F(s) + " m, closures on the route at " +
                           string.Join(", ", crossings.Select(c => F(c.s) + (c.entry ? " (entry)" : " (exit)"))) + " m";

            Assert.AreEqual(s, StartClearance.SafeStartS(crossings, s, length), 0.01f,
                where + " - the start is outside / too close to the closure the route enters through (python scripts/export-region-catalog.py)");
            StartClearance.FreeAround(crossings, s, out float behind, out float ahead);
            Assert.GreaterOrEqual(behind, StartClearance.MarginM, where + " - trailer rear end to the row behind");
            float need = Mathf.Min(StartClearance.AheadFreeM, length - s - StartClearance.FrontM);
            Assert.GreaterOrEqual(ahead, need, where + " - a closure row on the route " + F(ahead) + " m ahead of the bumper");
            Assert.GreaterOrEqual(length - s, RegionStart.MinAheadM, where + " - route left ahead");
        }

        /// <summary>
        /// Colliders of the imported scene (barriers, bollards, signs, buildings, fences - whatever the importer built):
        /// the combination box at the catalog start touches nothing (<see cref="StartClearance.MarginM"/> around) and the
        /// tractor swept along the route for <see cref="StartClearance.AheadFreeM"/> (or to the route end) meets nothing
        /// standing on the carriageway. Scenes are generated (not in git): a region that is not imported is skipped.
        /// </summary>
        [TestCaseSource(nameof(RegionIds)), Category("WorldScenes")]
        public void ImportedScene_StartBoxIsFree_AndNothingStandsOnTheRouteAhead(string region)
        {
            string scenePath = RegionScenes.ScenePathFor(region);
            if (!File.Exists(Path.Combine(EditorTools.RepoRoot, "game", scenePath))) Assert.Ignore(region + ": scene not imported (" + scenePath + ")");
            var r = RegionCatalog.Load().Find(region);
            EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            try
            {
                var route = Object.FindAnyObjectByType<WorldRoute>();
                var boundary = Object.FindAnyObjectByType<WorldBoundary>();
                Assert.IsNotNull(route, region + ": WorldRoute");
                Assert.IsNotNull(boundary, region + ": WorldBoundary");
                var ignore = new List<Transform>();
                foreach (var v in Object.FindObjectsByType<VehicleBody>(FindObjectsSortMode.None)) ignore.Add(v.transform);
                foreach (var t in Object.FindObjectsByType<TrailerBody>(FindObjectsSortMode.None)) ignore.Add(t.transform);
                Physics.SyncTransforms();

                float s = RegionStart.ClampStartS(r.startS, route.Length);
                float resolved = SpawnSafety.ResolveStartS(route, boundary, s, ignore, out string reason);
                Assert.IsNull(reason, region + ": start at route_s " + F(s) + " m is not free (" + reason + "), first free place " + F(resolved) + " m");

                float end = Mathf.Min(s + StartClearance.AheadFreeM, route.Length - StartClearance.FrontM);
                for (float d = s + SpawnSafety.StepM; d <= end; d += SpawnSafety.StepM)
                {
                    // the tractor alone, no margin: a bend puts the straight 16.5 m box of the whole combination over kerbs and islands
                    var hit = SpawnSafety.FirstOverlap(route, d, ignore, 0.8f, 0f);
                    Assert.IsNull(hit, region + ": collider '" + (hit != null ? hit.name : "") + "' on the route at " + F(d) + " m (" + F(d - s) + " m after the start)");
                }
            }
            finally
            {
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            }
        }
    }
}
