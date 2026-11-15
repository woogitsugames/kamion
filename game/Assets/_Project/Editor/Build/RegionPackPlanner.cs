using System;
using System.Collections.Generic;
using Game.World;

namespace Game.Editor.Build
{
    /// <summary>
    /// One scene bundle to build: pack id, region, content tier, the full region scene and - when imported - the streamed
    /// tile scene of the same region and tier (ADR 0235 <c>World_&lt;id&gt;[_High]_Tile</c>). ADR 0273: a pack carries every
    /// scene the runtime may open for that region and tier (menu start = full scene, additive streaming = tile scene); both
    /// scenes go into ONE bundle so their shared region assets are stored once.
    /// </summary>
    public readonly struct RegionPackScene
    {
        public readonly string Id, Region, Tier, ScenePath, TileScenePath;
        public RegionPackScene(string id, string region, string tier, string scenePath, string tileScenePath = null)
        {
            Id = id; Region = region; Tier = tier; ScenePath = scenePath;
            TileScenePath = string.IsNullOrEmpty(tileScenePath) ? null : tileScenePath;
        }

        /// <summary>Scene paths of the bundle: the full scene first, then the tile scene (if any).</summary>
        public string[] ScenePaths => TileScenePath == null ? new[] { ScenePath } : new[] { ScenePath, TileScenePath };

        /// <summary>Scene names for the manifest (<c>scenes[]</c>), same order as <see cref="ScenePaths"/>.</summary>
        public string[] SceneNames => TileScenePath == null
            ? new[] { RegionPackPlanner.SceneName(Region, Tier) }
            : new[] { RegionPackPlanner.SceneName(Region, Tier), RegionPackPlanner.TileSceneName(Region, Tier) };
    }

    /// <summary>
    /// Splits the dependencies of region scenes into the shared <c>common</c> bundle and the scene bundles (ADR 0234 §2).
    /// Unity copies an implicitly referenced asset into EVERY bundle that uses it (manual "Avoiding asset duplication"),
    /// so an asset goes to <c>common</c> when (a) scenes of two or more regions use it, or (b) it lives outside the region's
    /// own generated folder <c>Assets/_Generated/World/&lt;region&gt;/</c> (truck, trailer, world PBR textures, prop
    /// libraries, shaders, URP assets). Region-folder assets used by both tiers of one region (collision, instances) go to
    /// "&lt;region&gt;-data"; the rest stays implicit in the one scene bundle that uses it. Rule (b) keeps the common bundle
    /// stable whatever subset of regions is built. Pure string logic for EditMode tests.
    /// </summary>
    public static class RegionPackPlanner
    {
        public const string GeneratedWorldRoot = "Assets/_Generated/World/";

        public sealed class Plan
        {
            /// <summary>Assets explicitly assigned to the common bundle (sorted, ordinal).</summary>
            public readonly List<string> Common = new List<string>();
            /// <summary>Per region: assets of the region folder used by both of its tier scenes (Low + High) and by no
            /// other region - explicit in the bundle "&lt;region&gt;-data" (collision, instances), sorted.</summary>
            public readonly Dictionary<string, List<string>> RegionData = new Dictionary<string, List<string>>();
            /// <summary>Per pack id: assets that stay implicit in its scene bundle (informative, sorted).</summary>
            public readonly Dictionary<string, List<string>> Unique = new Dictionary<string, List<string>>();
            /// <summary>Assets skipped because they cannot or must not be in a bundle (scripts, editor-only, scenes).</summary>
            public readonly List<string> Skipped = new List<string>();
            /// <summary>
            /// Subset of <see cref="Common"/> under a <c>Resources/</c> folder (review s22 #112 P2-4). Such an asset is
            /// always in the player too, and a bundle cannot reference the player's copy (manual "Avoiding asset
            /// duplication": content is not shared between builds), so a scene from a pack gets a SECOND instance -
            /// not the object Resources.Load returns. Excluding it would not help: an unassigned dependency is copied
            /// implicitly into every scene bundle. It stays in common (one copy) and is listed for review: a region
            /// scene must not reference Resources/ assets (fix at the importer, not here).
            /// </summary>
            public readonly List<string> ResourcesCopies = new List<string>();
        }

        /// <summary>True for dependencies that never go into a bundle: scripts and assemblies (code lives in the player),
        /// scene files (a scene bundle holds only its scene), editor-only folders, packages' editor resources.</summary>
        public static bool IsExcluded(string assetPath)
        {
            if (string.IsNullOrEmpty(assetPath)) return true;
            string p = assetPath.Replace('\\', '/');
            string ext = System.IO.Path.GetExtension(p).ToLowerInvariant();
            switch (ext)
            {
                case ".cs": case ".dll": case ".asmdef": case ".asmref": case ".unity": case ".rsp": return true;
            }
            if (p.Contains("/Editor/") || p.StartsWith("Editor/", StringComparison.Ordinal)) return true;
            if (p.Contains("/Editor Default Resources/")) return true;
            return false;
        }

        /// <summary>True for an asset in a Resources/ folder (always in the player as well).</summary>
        public static bool IsUnderResources(string assetPath)
        {
            if (string.IsNullOrEmpty(assetPath)) return false;
            string p = assetPath.Replace('\\', '/');
            return p.Contains("/Resources/") || p.StartsWith("Resources/", StringComparison.Ordinal);
        }

        public static string RegionFolder(string region) => GeneratedWorldRoot + region + "/";

        /// <param name="scenes">Pack scenes of this build run.</param>
        /// <param name="dependencies">Recursive dependencies per scene path (AssetDatabase.GetDependencies(path, true)).</param>
        public static Plan Build(IReadOnlyList<RegionPackScene> scenes, Func<string, IEnumerable<string>> dependencies)
        {
            var plan = new Plan();
            var users = new Dictionary<string, List<int>>(StringComparer.Ordinal);
            var skipped = new HashSet<string>(StringComparer.Ordinal);
            for (int i = 0; i < scenes.Count; i++)
            {
                // Full scene and tile scene of one pack are one user: assets only they share stay implicit in the bundle.
                foreach (var scenePath in scenes[i].ScenePaths)
                {
                    foreach (var raw in dependencies(scenePath) ?? Array.Empty<string>())
                    {
                        string a = raw.Replace('\\', '/');
                        if (a == scenePath) continue;
                        if (IsExcluded(a)) { skipped.Add(a); continue; }
                        if (!users.TryGetValue(a, out var list)) users[a] = list = new List<int>();
                        if (!list.Contains(i)) list.Add(i);
                    }
                }
            }
            foreach (var kv in users)
            {
                var owner = scenes[kv.Value[0]];
                bool outsideRegion = !kv.Key.StartsWith(RegionFolder(owner.Region), StringComparison.Ordinal);
                bool otherRegion = false;
                foreach (int u in kv.Value) otherRegion |= scenes[u].Region != owner.Region;
                if (outsideRegion || otherRegion) plan.Common.Add(kv.Key);
                else if (kv.Value.Count >= 2)
                {
                    if (!plan.RegionData.TryGetValue(owner.Region, out var d)) plan.RegionData[owner.Region] = d = new List<string>();
                    d.Add(kv.Key);
                }
                else
                {
                    if (!plan.Unique.TryGetValue(owner.Id, out var u)) plan.Unique[owner.Id] = u = new List<string>();
                    u.Add(kv.Key);
                }
            }
            plan.Common.Sort(StringComparer.Ordinal);
            foreach (var a in plan.Common) if (IsUnderResources(a)) plan.ResourcesCopies.Add(a);
            foreach (var u in plan.Unique.Values) u.Sort(StringComparer.Ordinal);
            foreach (var d in plan.RegionData.Values) d.Sort(StringComparer.Ordinal);
            plan.Skipped.AddRange(skipped);
            plan.Skipped.Sort(StringComparer.Ordinal);
            return plan;
        }

        /// <summary>
        /// Region tokens of -regions: comma/semicolon/space separated ids, or "all" = every available region except
        /// region C (it stays in the base APK, ADR 0234 §1). Unknown ids are returned in <paramref name="unknown"/>.
        /// </summary>
        public static List<string> ResolveRegions(string arg, IReadOnlyList<string> available, string baseRegion, out List<string> unknown)
        {
            unknown = new List<string>();
            var result = new List<string>();
            if (string.IsNullOrWhiteSpace(arg)) arg = "all";
            foreach (var t in arg.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries))
            {
                string tok = t.Trim();
                if (tok == "all")
                {
                    foreach (var r in available)
                        if (r != baseRegion && !result.Contains(r)) result.Add(r);
                    continue;
                }
                string id = Contains(available, tok) ? tok : Contains(available, "bialystok-" + tok) ? "bialystok-" + tok : null;
                if (id == null) { unknown.Add(tok); continue; }
                if (!result.Contains(id)) result.Add(id);
            }
            return result;
        }

        static bool Contains(IReadOnlyList<string> list, string s)
        {
            foreach (var x in list) if (x == s) return true;
            return false;
        }

        /// <summary>Pack id of a region and tier: "&lt;region&gt;" for Low, "&lt;region&gt;-high" for High.</summary>
        public static string PackId(string region, string tier) => tier == "High" ? region + "-high" : region;

        public static string DataPackId(string region) => region + "-data";

        /// <summary>Scene name rule of ADR 0011/0229: delegates to <see cref="RegionScenes"/> (one rule for importer, build,
        /// menu and packs; review s22 #112 P2-3).</summary>
        public static string SceneName(string region, string tier) =>
            RegionScenes.SceneNameFor(region, tier == "High" ? RegionScenes.HighTier : RegionScenes.LowTier);

        public static string ScenePath(string region, string tier) =>
            RegionScenes.ScenePathFor(region, tier == "High" ? RegionScenes.HighTier : RegionScenes.LowTier);

        /// <summary>Streamed tile scene (ADR 0235/0273), e.g. World_dk65-06_Tile, World_knyszyn_High_Tile.</summary>
        public static string TileSceneName(string region, string tier) =>
            RegionScenes.TileSceneNameFor(region, tier == "High" ? RegionScenes.HighTier : RegionScenes.LowTier);

        public static string TileScenePath(string region, string tier) =>
            RegionScenes.TileScenePathFor(region, tier == "High" ? RegionScenes.HighTier : RegionScenes.LowTier);
    }
}
