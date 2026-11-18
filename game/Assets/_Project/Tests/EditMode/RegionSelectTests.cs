using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using Game.Core.Navigation;
using Game.Editor.Build;
using Game.Gameplay;
using Game.World;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>ADR 0229: regions in the build (-regions / -regionsFile), region -> scene -> route mapping, start point.</summary>
    public class RegionSelectTests
    {
        const string TestCatalog = @"{
  ""schema"": ""truck-sim-pl/region-catalog/1"",
  ""regions"": [
    {""id"": ""bialystok-industrial-c"", ""label"": ""C"", ""group"": ""B"", ""routeLengthM"": 2397.47, ""startS"": 12},
    {""id"": ""bialystok-dojlidy"", ""label"": ""Dojlidy"", ""group"": ""B"", ""routeLengthM"": 2133.17, ""startS"": 12},
    {""id"": ""dk65-01"", ""label"": ""01"", ""group"": ""DK65"", ""routeLengthM"": 631.76, ""startS"": 12},
    {""id"": ""dk65-02"", ""label"": ""02"", ""group"": ""DK65"", ""routeLengthM"": 2400.64, ""startS"": 12},
    {""id"": ""dk65-03"", ""label"": ""03"", ""group"": ""DK65"", ""routeLengthM"": 484.44, ""startS"": 12},
    {""id"": ""knyszyn"", ""label"": ""Knyszyn"", ""group"": ""K"", ""routeLengthM"": 1159.85, ""startS"": 12}
  ],
  ""aliases"": [ {""alias"": ""c"", ""region"": ""bialystok-industrial-c""} ],
  ""sets"": [ {""name"": ""corr"", ""regions"": [""c"", ""dk65-01"", ""knyszyn""]} ]
}";

        static RegionCatalog Test() => RegionCatalog.Parse(TestCatalog);

        static List<string> Resolve(RegionCatalog c, string spec, List<string> errors = null) => c.Resolve(spec, errors ?? new List<string>());

        // ------------------------------------------------------------------ -regions parsing

        [Test]
        public void Resolve_IdsAliasesPrefixAndEllipsisRange()
        {
            var errors = new List<string>();
            var r = Resolve(Test(), "c,dojlidy,dk65-01,...,knyszyn", errors);
            CollectionAssert.IsEmpty(errors);
            CollectionAssert.AreEqual(new[] { "bialystok-industrial-c", "bialystok-dojlidy", "dk65-01", "dk65-02", "dk65-03", "knyszyn" }, r);
        }

        [Test]
        public void Resolve_RangesSetsAllDuplicatesAndSeparators()
        {
            var c = Test();
            CollectionAssert.AreEqual(new[] { "dk65-01", "dk65-02", "dk65-03" }, Resolve(c, "dk65-01..dk65-03"));
            CollectionAssert.AreEqual(new[] { "dk65-03", "dk65-02", "dk65-01" }, Resolve(c, "dk65-03..dk65-01"), "reverse range keeps the written order");
            CollectionAssert.AreEqual(new[] { "dk65-01", "dk65-02", "dk65-03" }, Resolve(c, "dk65-01...dk65-03"), "three dots inside one token");
            CollectionAssert.AreEqual(new[] { "bialystok-industrial-c", "dk65-01", "knyszyn" }, Resolve(c, "corr"));
            Assert.AreEqual(6, Resolve(c, "all").Count);
            CollectionAssert.AreEqual(new[] { "bialystok-industrial-c" }, Resolve(c, "c, C ;bialystok-industrial-c"), "no duplicates, case-insensitive");
            CollectionAssert.AreEqual(new[] { "bialystok-industrial-c", "knyszyn" }, Resolve(c, "c knyszyn"), "PowerShell array joined with spaces");
            CollectionAssert.IsEmpty(Resolve(c, ""));
            CollectionAssert.IsEmpty(Resolve(c, null));
        }

        [Test]
        public void Resolve_UnknownNamesAndDanglingEllipsisAreErrors()
        {
            var c = Test();
            var errors = new List<string>();
            CollectionAssert.AreEqual(new[] { "knyszyn" }, Resolve(c, "warszawa,knyszyn", errors));
            Assert.AreEqual(1, errors.Count);
            StringAssert.Contains("warszawa", errors[0]);
            errors.Clear(); Resolve(c, "...,knyszyn", errors);
            Assert.AreEqual(1, errors.Count, "ellipsis without a region before it");
            errors.Clear(); Resolve(c, "knyszyn,...", errors);
            Assert.AreEqual(1, errors.Count, "ellipsis without a region after it");
            errors.Clear(); Resolve(c, "c..warszawa", errors);
            Assert.AreEqual(1, errors.Count, "range with an unknown end");
        }

        [Test]
        public void Catalog_RejectsWrongSchemaAndDuplicateIds()
        {
            Assert.Throws<System.FormatException>(() => RegionCatalog.Parse(TestCatalog.Replace("region-catalog/1", "region-catalog/9")));
            Assert.Throws<System.FormatException>(() => RegionCatalog.Parse(TestCatalog.Replace("\"dk65-02\", \"label\"", "\"dk65-01\", \"label\"")));
            Assert.Throws<System.FormatException>(() => RegionCatalog.Parse(""));
        }

        // ------------------------------------------------------------------ build regions JSON + command line

        [Test]
        public void BuildRegionsFile_ParsesTokens_RejectsWrongSchema()
        {
            var errors = new List<string>();
            Assert.AreEqual("c,dk65-01..dk65-03", RegionBuildList.ParseFile(@"{""schema"": ""truck-sim-pl/build-regions/1"", ""regions"": [""c"", ""dk65-01..dk65-03""]}", errors));
            CollectionAssert.IsEmpty(errors);
            Assert.IsNull(RegionBuildList.ParseFile(@"{""schema"": ""other"", ""regions"": [""c""]}", errors));
            Assert.AreEqual(1, errors.Count);
            errors.Clear();
            Assert.IsNull(RegionBuildList.ParseFile("", errors));
            Assert.AreEqual(1, errors.Count);
        }

        [Test]
        public void SpecFromArgs_NoArguments_IsEmpty_FileAndArgumentCombine()
        {
            var errors = new List<string>();
            Assert.AreEqual("", RegionBuildList.SpecFromArgs(null, null, EditorTools.RepoRoot, errors), "default build: no region list");
            Assert.AreEqual("knyszyn", RegionBuildList.SpecFromArgs("knyszyn", null, EditorTools.RepoRoot, errors));
            string tmp = Path.Combine(Path.GetTempPath(), "kamion-build-regions-test.json");
            File.WriteAllText(tmp, @"{""schema"": ""truck-sim-pl/build-regions/1"", ""regions"": [""c""]}");
            try { Assert.AreEqual("knyszyn,c", RegionBuildList.SpecFromArgs("knyszyn", tmp, EditorTools.RepoRoot, errors)); }
            finally { File.Delete(tmp); }
            CollectionAssert.IsEmpty(errors);
            RegionBuildList.SpecFromArgs(null, "Data/no-such-file.json", EditorTools.RepoRoot, errors);
            Assert.AreEqual(1, errors.Count, "missing -regionsFile is an error");
        }

        [Test]
        public void ShippedBuildRegionsFile_IsTheD67Corridor()
        {
            var errors = new List<string>();
            string spec = RegionBuildList.SpecFromArgs(null, "Data/build_regions.json", EditorTools.RepoRoot, errors);
            var catalog = RegionCatalog.Load();
            Assert.IsNotNull(catalog, "Resources/Regions/region_catalog.json");
            var regions = catalog.Resolve(spec, errors);
            CollectionAssert.IsEmpty(errors);
            Assert.AreEqual(17, regions.Count, "C, Maczka, Kleeberga, Knyszyńska, DK65 01-11, Knyszyn-S, Knyszyn");
            Assert.AreEqual(RegionScenes.RegionC, regions[0]);
            Assert.AreEqual("knyszyn", regions[regions.Count - 1]);
        }

        // ------------------------------------------------------------------ ADR 0267 (follow-up of the #104 review)

        [Test]
        public void ShippedCatalog_D67Full_IsD67PlusTheD71Regions()
        {
            var catalog = RegionCatalog.Load();
            Assert.IsNotNull(catalog, "Resources/Regions/region_catalog.json");
            var errors = new List<string>();
            var d67 = catalog.Resolve("d67", errors);
            var full = catalog.Resolve("d67-full", errors);
            CollectionAssert.IsEmpty(errors);
            Assert.AreEqual(17, d67.Count, "d67 stays the lighter main-route variant (ADR 0229)");
            Assert.AreEqual(39, full.Count, "d67 (17) + Dojlidy, Knyszyn-W, Monki, Tykocin + the 18 ring tiles of ADR 0231 (owner decision 2026-11-16)");
            CollectionAssert.AreEqual(d67, full.GetRange(0, d67.Count), "d67-full starts with d67");
            CollectionAssert.AreEqual(new[] { "bialystok-dojlidy", "knyszyn-w", "dk65-monki-01", "dw671-tykocin-01" }, full.GetRange(17, 4));
            CollectionAssert.AreEqual(new[]
            {
                "dk65-monki-02", "dk65-monki-03", "dk65-monki-04", "dk65-monki-05", "dk65-monki-06", "dk65-monki-07", "monki-e", "monki",
                "dw671-tykocin-02", "dw671-tykocin-03", "dw671-tykocin-04", "dw671-tykocin-05", "dw671-tykocin-06",
                "dw671-tykocin-07", "dw671-tykocin-08", "dw671-tykocin-09", "tykocin", "dw671-jasionowka-01",
            }, full.GetRange(21, 18));
            CollectionAssert.AllItemsAreUnique(full);
        }

        [Test]
        public void ResolveRegions_NotGiven_IsNull_GivenButEmpty_IsAnError()
        {
            var c = Test();
            var errors = new List<string>();
            Assert.IsNull(RegionBuildList.ResolveRegions(null, null, EditorTools.RepoRoot, c, errors), "default build");
            CollectionAssert.IsEmpty(errors);

            CollectionAssert.AreEqual(new[] { "bialystok-industrial-c" }, RegionBuildList.ResolveRegions("c", null, EditorTools.RepoRoot, c, errors));
            CollectionAssert.IsEmpty(errors);

            foreach (var spec in new[] { ",", "", " ; , " })
            {
                errors.Clear();
                CollectionAssert.IsEmpty(RegionBuildList.ResolveRegions(spec, null, EditorTools.RepoRoot, c, errors));
                Assert.AreEqual(1, errors.Count, "-regions '" + spec + "' resolves to no region");
                StringAssert.Contains("no region", errors[0]);
            }

            // Unique name: two Unity slots may run EditMode at once (review #129 P2-3, ADR 0276).
            string tmp = Path.Combine(Path.GetTempPath(), "kamion-build-regions-empty-" + Path.GetRandomFileName() + ".json");
            File.WriteAllText(tmp, @"{""schema"": ""truck-sim-pl/build-regions/1"", ""regions"": []}");
            try
            {
                errors.Clear();
                CollectionAssert.IsEmpty(RegionBuildList.ResolveRegions(null, tmp, EditorTools.RepoRoot, c, errors));
                Assert.AreEqual(1, errors.Count, "file with regions: [] is an error");
            }
            finally { File.Delete(tmp); }

            errors.Clear();
            RegionBuildList.ResolveRegions("warszawa", null, EditorTools.RepoRoot, c, errors);
            Assert.AreEqual(1, errors.Count, "an unknown name is reported once, not also as 'no region'");
        }

        [Test]
        public void RegionsArg_ValueSplitAtSpaces_IsJoined_SpacesAndSemicolonsSeparate()
        {
            Assert.IsNull(RegionBuildList.RegionsArgFrom(new[] { "Unity", "-batchmode", "-buildOutput", "a.apk" }));
            Assert.AreEqual("c", RegionBuildList.RegionsArgFrom(new[] { "Unity", "-regions", "c", "-regionsFile", "x.json" }));
            Assert.AreEqual("c,dojlidy,knyszyn", RegionBuildList.RegionsArgFrom(new[] { "Unity", "-REGIONS", "c", "dojlidy", "knyszyn", "-regionsAllowMissing" }),
                "Start-Process split 'c dojlidy knyszyn' into three arguments");
            Assert.AreEqual("", RegionBuildList.RegionsArgFrom(new[] { "Unity", "-regions", "-buildOutput", "a.apk" }));
            Assert.AreEqual("", RegionBuildList.RegionsArgFrom(new[] { "Unity", "-regions" }));

            var c = Test();
            var want = new[] { "bialystok-industrial-c", "bialystok-dojlidy", "knyszyn" };
            CollectionAssert.AreEqual(want, Resolve(c, "c dojlidy  knyszyn"));
            CollectionAssert.AreEqual(want, Resolve(c, "c;dojlidy;knyszyn"));
            CollectionAssert.AreEqual(want, Resolve(c, " c ;, dojlidy\tknyszyn\u00A0"));
            CollectionAssert.AreEqual(want, Resolve(c, RegionBuildList.RegionsArgFrom(new[] { "-regions", "c", "dojlidy;knyszyn" })));
        }

        [Test]
        public void Catalog_BrokenJson_GivesNullWithoutAnException()
        {
            foreach (var json in new[] { "{ \"schema\": ", "not json at all", "[1,2,", TestCatalog.Replace("region-catalog/1", "region-catalog/9"), "" })
            {
                LogAssert.Expect(LogType.Error, new Regex(@"^\[REGIONS\] region catalog unreadable"));
                RegionCatalog parsed = null;
                Assert.DoesNotThrow(() => parsed = RegionCatalog.ParseOrNull(json), json);
                Assert.IsNull(parsed, json);
            }
            Assert.IsNotNull(RegionCatalog.ParseOrNull(TestCatalog));
        }

        // ------------------------------------------------------------------ scene list composition

        static readonly string[] k_Base =
        {
            "Assets/_Project/Core/Scenes/Boot.unity", "Assets/_Project/World/Scenes/DrivingLab.unity",
            "Assets/_Generated/World/bialystok-industrial-c/WorldC.unity",
        };

        [Test]
        public void ComposeScenes_AppendsRegions_SkipsDuplicatesAndMissing()
        {
            var have = new HashSet<string>(k_Base)
            {
                "Assets/_Generated/World/knyszyn/World_knyszyn.unity",
                "Assets/_Generated/World/knyszyn/World_knyszyn_High.unity",
            };
            var missing = new List<string>();
            var missingHigh = new List<string>();
            var scenes = RegionBuildList.ComposeScenes(k_Base, new[] { "bialystok-industrial-c", "knyszyn", "dk65-01" }, false, have.Contains, missing, missingHigh);
            CollectionAssert.AreEqual(new List<string>(k_Base) { "Assets/_Generated/World/knyszyn/World_knyszyn.unity" }, scenes, "Boot first, C once, knyszyn added");
            CollectionAssert.AreEqual(new[] { "Assets/_Generated/World/dk65-01/World_dk65-01.unity" }, missing);
            CollectionAssert.IsEmpty(missingHigh, "no High asked");

            missing.Clear();
            scenes = RegionBuildList.ComposeScenes(k_Base, new[] { "bialystok-industrial-c", "knyszyn" }, true, have.Contains, missing, missingHigh);
            CollectionAssert.Contains(scenes, "Assets/_Generated/World/knyszyn/World_knyszyn_High.unity");
            CollectionAssert.AreEqual(new[] { "Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity" }, missingHigh, "High is optional: reported, not added");
            CollectionAssert.IsEmpty(missing);
        }

        [Test]
        public void ComposeScenes_NoRegions_KeepsBuildSettingsListExactly()
        {
            var scenes = RegionBuildList.ComposeScenes(k_Base, new string[0], true, _ => true, new List<string>());
            CollectionAssert.AreEqual(k_Base, scenes);
            scenes = RegionBuildList.ComposeScenes(k_Base, null, false, _ => true, new List<string>());
            CollectionAssert.AreEqual(k_Base, scenes);
        }

        // ------------------------------------------------------------------ region -> scene -> route

        [Test]
        public void RegionScenes_NamesMatchImporterAndBuildSettings()
        {
            Assert.AreEqual("WorldC", RegionScenes.SceneNameFor(RegionScenes.RegionC));
            Assert.AreEqual("WorldC_High", RegionScenes.SceneNameFor(RegionScenes.RegionC, RegionScenes.HighTier));
            Assert.AreEqual("World_knyszyn", RegionScenes.SceneNameFor("knyszyn"));
            Assert.AreEqual("World_dk65-01_High", RegionScenes.SceneNameFor("dk65-01", "High"));
            Assert.AreEqual(Game.Editor.Setup.BuildScenes.WorldCScenePath, RegionScenes.ScenePathFor(RegionScenes.RegionC), "build list of git = the same path");
            Assert.AreEqual(GameBootstrap.WorldCSceneName, RegionScenes.SceneNameFor(RegionScenes.RegionC));
            Assert.AreEqual(GameBootstrap.WorldCHighSceneName, RegionScenes.SceneNameFor(RegionScenes.RegionC, RegionScenes.HighTier));
            Assert.IsTrue(RegionScenes.UsesHighContent("High") && RegionScenes.UsesHighContent("Ultra"));
            Assert.IsFalse(RegionScenes.UsesHighContent("Medium") || RegionScenes.UsesHighContent("Low"));
        }

        [Test]
        public void ShippedCatalog_CoversEveryRegionWithAStartRoute_AndStartIsInsideTheRoute()
        {
            var catalog = RegionCatalog.Load();
            Assert.IsNotNull(catalog);
            string regionsDir = Path.Combine(EditorTools.RepoRoot, "Data", "Regions");
            foreach (var dir in Directory.GetDirectories(regionsDir))
            {
                string id = Path.GetFileName(dir);
                if (!File.Exists(Path.Combine(dir, "route_start.json"))) continue;
                var r = catalog.Find(id);
                Assert.IsNotNull(r, id + ": no catalog entry (scripts/export-region-catalog.py --check)");
                float length = ReadLength(Path.Combine(dir, "route_start.json"));
                Assert.AreEqual(length, r.routeLengthM, 0.05f, id + ": routeLengthM stale (scripts/export-region-catalog.py)");
                float s = RegionStart.ClampStartS(r.startS, r.routeLengthM);
                Assert.GreaterOrEqual(s, 0f, id);
                Assert.LessOrEqual(s, r.routeLengthM - RegionStart.MinAheadM, id + ": start leaves too little route");
                StringAssert.DoesNotContain("Kwadrat", r.label, id + ": labels name streets and places, not companies");
            }
            foreach (var set in catalog.sets)
                foreach (var t in set.regions) Assert.IsNotNull(catalog.ResolveId(t), set.name + ": " + t);
        }

        /// <summary>Real data: the start point of every region that ships a routing graph (Resources/CabDisplay/Nav/&lt;id&gt;_route.bytes)
        /// lies on a road of that graph (right-lane centre within <see cref="RegionStart.SnapMaxM"/> of the axis).</summary>
        [Test]
        public void StartPoint_FromRouteStart_SnapsToTheRegionGraph()
        {
            var catalog = RegionCatalog.Load();
            int checkedRegions = 0;
            foreach (var r in catalog.regions)
            {
                var g = RouteGraph.Load(r.id);
                if (g == null) continue;   // region without a routing graph: start still works, the log says road_edge=-1
                string json = Path.Combine(EditorTools.RepoRoot, "Data", "Regions", r.id, "route_start.json");
                ReadRoute(json, out var pts, out var dist);
                float s = RegionStart.ClampStartS(r.startS, r.routeLengthM);
                Vector2 en = RegionStart.LocalPointAt(pts, dist, s);
                var road = RegionStart.FindRoad(g, en);
                Assert.GreaterOrEqual(road.Edge, 0, r.id + ": start point " + en + " not on a graph road");
                Assert.LessOrEqual(road.Distance, RegionStart.SnapMaxM, r.id);
                StringAssert.StartsWith("[START] region=" + r.id + " route_s=" + s.ToString("F1", CultureInfo.InvariantCulture), RegionStart.Describe(r.id, s, en, road));
                checkedRegions++;
            }
            Assert.GreaterOrEqual(checkedRegions, 1, "at least region C ships a routing graph");
        }

        // ------------------------------------------------------------------ start point (synthetic)

        [Test]
        public void ClampStartS_DefaultAndRouteLimits()
        {
            Assert.AreEqual(RegionStart.DefaultStartS, RegionStart.ClampStartS(-1f, 1000f));
            Assert.AreEqual(250f, RegionStart.ClampStartS(250f, 1000f));
            Assert.AreEqual(900f, RegionStart.ClampStartS(5000f, 1000f), "keep MinAheadM of route ahead");
            Assert.AreEqual(0f, RegionStart.ClampStartS(12f, 80f), "route shorter than MinAheadM: its start");
            Assert.AreEqual(0f, RegionStart.ClampStartS(0f, 1000f), "an explicit 0 is the route start, not the default");
            Assert.AreEqual(40f, RegionStart.ClampStartS(40f, 0f), "unknown length: no upper clamp");
        }

        [Test]
        public void LocalPointAt_InterpolatesInRegionFrame()
        {
            var pts = new[] { new Vector3(0, 5, 0), new Vector3(0, 6, 10), new Vector3(10, 7, 10) };
            var dist = new[] { 0f, 10f, 20f };
            Assert.AreEqual(new Vector2(0, 0), RegionStart.LocalPointAt(pts, dist, -3f));
            Assert.AreEqual(new Vector2(0, 4), RegionStart.LocalPointAt(pts, dist, 4f));
            Assert.AreEqual(new Vector2(5, 10), RegionStart.LocalPointAt(pts, dist, 15f));
            Assert.AreEqual(new Vector2(10, 10), RegionStart.LocalPointAt(pts, dist, 99f));
            Assert.AreEqual(Vector2.zero, RegionStart.LocalPointAt(new Vector3[0], new float[0], 3f));
        }

        [Test]
        public void FindRoad_NearestNamedEdge_NoneWhenFarOrNoGraph()
        {
            // Two straight roads: "Dolna" (0,0)-(200,0), "Boczna" (200,0)-(200,200).
            var g = new RouteGraph
            {
                Names = new[] { "", "Dolna", "Boczna" },
                NodePos = new[] { new Vector2(0, 0), new Vector2(200, 0), new Vector2(200, 200) },
                NodeFlags = new byte[3],
                EdgeFrom = new[] { 0, 1 }, EdgeTo = new[] { 1, 2 }, EdgeLength = new[] { 200f, 200f },
                EdgeClass = new byte[] { 1, 1 }, EdgeFlags = new byte[2], EdgeName = new ushort[] { 1, 2 },
                EdgeMaxSpeed = new byte[2], EdgeMaxSpeedOsm = new bool[2], EdgeStart = new[] { 0, 2, 4 },
                Points = new[] { new Vector2(0, 0), new Vector2(200, 0), new Vector2(200, 0), new Vector2(200, 200) },
            };
            g.BuildAdjacency();
            var road = RegionStart.FindRoad(g, new Vector2(196f, 120f));   // 4 m left of "Boczna"
            Assert.AreEqual(1, road.Edge);
            Assert.AreEqual("Boczna", road.Name);
            Assert.AreEqual(4f, road.Distance, 1e-3f);
            Assert.AreEqual(120f, road.Along, 1e-3f);
            road = RegionStart.FindRoad(g, new Vector2(60f, -3f));
            Assert.AreEqual("Dolna", road.Name);
            Assert.AreEqual(-1, RegionStart.FindRoad(g, new Vector2(60f, -80f)).Edge, "farther than SnapMaxM");
            Assert.AreEqual(-1, RegionStart.FindRoad(null, Vector2.zero).Edge, "no graph for the region");
            StringAssert.Contains("road_edge=-1 road='' road_dist=-", RegionStart.Describe("x", 12f, Vector2.zero, RegionStart.FindRoad(null, Vector2.zero)));
        }

        [Test]
        public void StartRequest_RegionIsConsumedOnce_AndPlainStartsClearIt()
        {
            StartRequest.SetRegion("region knyszyn", "knyszyn", 12f, "overcast");
            Assert.IsTrue(StartRequest.Consume(out float s, out float end));
            Assert.AreEqual(12f, s); Assert.AreEqual(-1f, end, "free driving: no route end");
            Assert.AreEqual("knyszyn", StartRequest.ConsumeRegion());
            Assert.AreEqual("", StartRequest.ConsumeRegion());
            StartRequest.SetRegion("region knyszyn", "knyszyn", 12f);
            StartRequest.Set("G3-A", StartRequest.G3AStartS, StartRequest.G3AEndS);
            Assert.AreEqual("", StartRequest.ConsumeRegion(), "a G3 start is not a region start");
            StartRequest.Consume(out _, out _); StartRequest.ConsumeLighting();
        }

        // ------------------------------------------------------------------ helpers (route_start.json: plain regex, no JSON library in tests)

        static float ReadLength(string path)
        {
            var m = Regex.Match(File.ReadAllText(path), "\"length_m\"\\s*:\\s*(-?[0-9.]+)");
            Assert.IsTrue(m.Success, path + ": length_m");
            return float.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
        }

        static void ReadRoute(string path, out Vector3[] pts, out float[] dist)
        {
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
    }
}
