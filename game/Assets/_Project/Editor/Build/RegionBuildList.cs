using System;
using System.Collections.Generic;
using System.IO;
using Game.Gameplay;
using Game.World;
using UnityEngine;

namespace Game.Editor.Build
{
    /// <summary>
    /// Optional region scenes for one APK (ADR 0229), composed in memory for <c>BuildPlayerOptions.scenes</c>: the
    /// EditorBuildSettings list in git (Boot, DrivingLab, WorldC) is never changed.
    /// Command line (all optional; nothing given = the build list exactly as before):
    /// <c>-regions "c,dojlidy,dk65-01..dk65-11,knyszyn"</c> (ids, aliases, set names, ranges - see
    /// <see cref="RegionCatalog.Resolve"/>), <c>-regionsFile Data/build_regions.json</c> (same tokens in a JSON list),
    /// <c>-regionsAllowMissing</c> (skip regions whose scene was not imported instead of failing the build).
    /// With <c>-worldHigh</c> the High scene of every listed region is added too, when it exists.
    /// Names come from the start-menu catalog (Resources/Regions/region_catalog.json), so the build and the menu agree.
    /// </summary>
    public static class RegionBuildList
    {
        public const string FileSchema = "truck-sim-pl/build-regions/1";
        public const string CatalogAssetPath = "Assets/_Project/Gameplay/Resources/Regions/region_catalog.json";

        [Serializable]
        sealed class FileDoc
        {
            public string schema = "";
            public string[] regions = Array.Empty<string>();
        }

        /// <summary>Tokens of a build-regions JSON file (<c>{"schema": "truck-sim-pl/build-regions/1", "regions": [...]}</c>)
        /// joined with commas; null + an error on a wrong file.</summary>
        public static string ParseFile(string json, List<string> errors)
        {
            FileDoc doc;
            try { doc = string.IsNullOrWhiteSpace(json) ? null : JsonUtility.FromJson<FileDoc>(json); }
            catch (Exception e) { errors?.Add("build regions file: " + e.Message); return null; }
            if (doc == null) { errors?.Add("build regions file: empty"); return null; }
            if (doc.schema != FileSchema) { errors?.Add("build regions file: schema '" + doc.schema + "', expected " + FileSchema); return null; }
            return string.Join(",", doc.regions ?? Array.Empty<string>());
        }

        public const string RegionsFlag = "-regions";

        /// <summary>
        /// Value of <c>-regions</c> in <paramref name="args"/>: every argument after the flag up to the next one starting with
        /// '-', joined with commas (ADR 0267). A launcher that splits a value at spaces (PowerShell <c>Start-Process</c> with
        /// <c>-Regions 'c knyszyn'</c>) then still passes every region. null when the flag is absent, "" when it has no value.
        /// </summary>
        public static string RegionsArgFrom(IReadOnlyList<string> args)
        {
            if (args == null) return null;
            for (int i = 0; i < args.Count; i++)
            {
                if (!string.Equals(args[i], RegionsFlag, StringComparison.OrdinalIgnoreCase)) continue;
                var values = new List<string>();
                for (int j = i + 1; j < args.Count && !(args[j] ?? "").StartsWith("-", StringComparison.Ordinal); j++)
                    if (!string.IsNullOrWhiteSpace(args[j])) values.Add(args[j]);
                return string.Join(",", values);
            }
            return null;
        }

        /// <summary>
        /// Regions of the command line resolved with <paramref name="catalog"/>: null when neither <c>-regions</c> nor
        /// <c>-regionsFile</c> was given (default build). Given but unknown names, a missing / wrong file or a list that
        /// resolves to no region at all (<c>-Regions ','</c>, a file with <c>"regions": []</c>) are errors (ADR 0267: an
        /// APK named '-regions' without regions would mislead the size measurement).
        /// </summary>
        public static List<string> ResolveRegions(string regionsArg, string regionsFileArg, string repoRoot, RegionCatalog catalog,
            List<string> errors)
        {
            if (regionsArg == null && string.IsNullOrWhiteSpace(regionsFileArg)) return null;
            errors ??= new List<string>();
            int before = errors.Count;
            string spec = SpecFromArgs(regionsArg, regionsFileArg, repoRoot, errors);
            if (errors.Count > before) return new List<string>();
            var regions = catalog != null ? catalog.Resolve(spec, errors) : new List<string>();
            if (catalog == null) errors.Add("region catalog missing");
            else if (errors.Count == before && regions.Count == 0)
                errors.Add("-regions/-regionsFile given but resolves to no region ('" + spec + "')");
            return regions;
        }

        /// <summary>The region specification of the command line: <c>-regions</c> and / or the tokens of <c>-regionsFile</c>
        /// (relative paths from the repo root). "" when neither is given.</summary>
        public static string SpecFromArgs(string regionsArg, string regionsFileArg, string repoRoot, List<string> errors)
        {
            var parts = new List<string>();
            if (!string.IsNullOrWhiteSpace(regionsArg)) parts.Add(regionsArg);
            if (!string.IsNullOrWhiteSpace(regionsFileArg))
            {
                string path = Path.IsPathRooted(regionsFileArg) ? regionsFileArg : Path.Combine(repoRoot ?? "", regionsFileArg);
                if (!File.Exists(path)) errors?.Add("-regionsFile not found: " + path);
                else
                {
                    string fromFile = ParseFile(File.ReadAllText(path), errors);
                    if (!string.IsNullOrEmpty(fromFile)) parts.Add(fromFile);
                }
            }
            return string.Join(",", parts);
        }

        /// <summary>
        /// Build scene list: <paramref name="baseScenes"/> (in order) + the Low scene of each region (+ its High scene when
        /// <paramref name="withHigh"/>), no duplicates. Low scenes that do not exist go to <paramref name="missing"/> and are
        /// left out; High scenes that do not exist go to <paramref name="missingHigh"/> (High is optional, ADR 0012).
        /// </summary>
        public static List<string> ComposeScenes(IReadOnlyList<string> baseScenes, IReadOnlyList<string> regions, bool withHigh,
            Func<string, bool> sceneExists, List<string> missing, List<string> missingHigh = null)
        {
            var scenes = new List<string>();
            if (baseScenes != null) foreach (var s in baseScenes) if (!scenes.Contains(s)) scenes.Add(s);
            if (regions == null) return scenes;
            foreach (var id in regions)
            {
                string low = RegionScenes.ScenePathFor(id, RegionScenes.LowTier);
                if (!sceneExists(low)) { missing?.Add(low); continue; }
                if (!scenes.Contains(low)) scenes.Add(low);
                // ADR 0235: the streamed tile scene goes with its region when it was imported (older imports: none).
                string lowTile = RegionScenes.TileScenePathFor(id, RegionScenes.LowTier);
                if (sceneExists(lowTile) && !scenes.Contains(lowTile)) scenes.Add(lowTile);
                if (!withHigh) continue;
                string high = RegionScenes.ScenePathFor(id, RegionScenes.HighTier);
                if (!sceneExists(high)) { missingHigh?.Add(high); continue; }
                if (!scenes.Contains(high)) scenes.Add(high);
                string highTile = RegionScenes.TileScenePathFor(id, RegionScenes.HighTier);
                if (sceneExists(highTile) && !scenes.Contains(highTile)) scenes.Add(highTile);
            }
            return scenes;
        }

        /// <summary>
        /// BuildCommands entry: reads <c>-regions</c> / <c>-regionsFile</c>, resolves them with the catalog and appends the
        /// region scenes to <paramref name="scenes"/>. Returns false (with <paramref name="error"/>) on an unknown name, a
        /// missing file, a list that resolves to no region (ADR 0267) or a region scene that was not imported (unless
        /// <c>-regionsAllowMissing</c>). No argument = true, list unchanged.
        /// </summary>
        public static bool AppendFromCommandLine(List<string> scenes, bool withHigh, out string error)
        {
            error = null;
            var errors = new List<string>();
            string regionsArg = RegionsArgFrom(Environment.GetCommandLineArgs());
            string regionsFileArg = EditorTools.Arg("-regionsFile", null);
            if (regionsArg == null && string.IsNullOrWhiteSpace(regionsFileArg)) return true;   // default build: list unchanged

            string catalogFile = Path.Combine(EditorTools.ProjectRoot, CatalogAssetPath);
            RegionCatalog catalog;
            try { catalog = RegionCatalog.Parse(File.ReadAllText(catalogFile)); }
            catch (Exception e) { error = "region catalog " + CatalogAssetPath + ": " + e.Message; return false; }

            var regions = ResolveRegions(regionsArg, regionsFileArg, EditorTools.RepoRoot, catalog, errors);
            if (errors.Count > 0) { error = string.Join("; ", errors); return false; }

            var missing = new List<string>();
            var missingHigh = new List<string>();
            var composed = ComposeScenes(scenes, regions, withHigh,
                p => File.Exists(Path.Combine(EditorTools.ProjectRoot, p)), missing, missingHigh);
            foreach (var h in missingHigh) Debug.LogWarning("[BUILD] -worldHigh: " + h + " missing (scripts/import-region.ps1 -Tiers Low,High)");
            if (missing.Count > 0)
            {
                string msg = "region scenes not imported (scripts/import-region.ps1 -Region <id>): " + string.Join(", ", missing);
                if (!EditorTools.HasArg("-regionsAllowMissing")) { error = msg; return false; }
                Debug.LogWarning("[BUILD] -regionsAllowMissing: " + msg);
            }
            scenes.Clear();
            scenes.AddRange(composed);
            Debug.Log($"[BUILD] regions ({regions.Count - missing.Count}/{regions.Count} in the APK): {string.Join(", ", regions)}");
            return true;
        }
    }
}
