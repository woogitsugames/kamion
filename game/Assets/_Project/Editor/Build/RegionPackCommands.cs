using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.World.Packs;
using UnityEditor;
using UnityEngine;

namespace Game.Editor.Build
{
    /// <summary>
    /// Region packs as AssetBundles (ADR 0234), no extra packages. Batchmode:
    ///   Unity.exe -batchmode -quit -buildTarget Android|Win64 -projectPath game
    ///     -executeMethod Game.Editor.Build.RegionPackCommands.BuildRegionPacks
    ///     [-regions "all" | "dojlidy,dk65-01,..."] [-packTiers Low|High|Both] [-packOutput dir]
    ///     [-packSetVersion v] [-minAppVersionCode n] [-maxAppVersionCode n] [-packTarget Android|Win64]
    /// Output: &lt;packOutput&gt;/&lt;packSetVersion&gt;/{common.bundle, &lt;region&gt;.bundle, &lt;region&gt;-high.bundle,
    /// &lt;region&gt;-data.bundle, regionpacks.json, regionpacks.plan.txt}. Prints "REGIONPACKS_RESULT: Succeeded|Failed ...";
    /// exit 0 on success. Scenes come from scripts/import-region.ps1 (Assets/_Generated/World/&lt;id&gt;/, gitignored).
    /// Region C (WorldC) stays in the base APK and is not packed unless named explicitly.
    /// EditorBuildSettings, scenes and asset import settings are never modified (bundle names are passed in memory).
    /// </summary>
    public static class RegionPackCommands
    {
        public const string RegionC = "bialystok-industrial-c";

        public static void BuildRegionPacks()
        {
            int exit = 1;
            try
            {
                exit = Build(
                    EditorTools.Arg("-regions", "all"),
                    EditorTools.Arg("-packTiers", "Low"),
                    EditorTools.Arg("-packOutput", Path.Combine(EditorTools.RepoRoot, "artifacts", "regionpacks")),
                    EditorTools.Arg("-packSetVersion", null),
                    ParseInt(EditorTools.Arg("-minAppVersionCode", null), -1),
                    ParseInt(EditorTools.Arg("-maxAppVersionCode", null), 0),
                    EditorTools.Arg("-packTarget", RegionPackManifest.TargetAndroid));
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.Log("REGIONPACKS_RESULT: Failed (exception)");
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Build/Region packs (all, Low)")]
        static void MenuBuild() => Build("all", "Low", Path.Combine(EditorTools.RepoRoot, "artifacts", "regionpacks"), null, -1, 0, RegionPackManifest.TargetAndroid);

        static int ParseInt(string s, int fallback) => int.TryParse(s, out int v) ? v : fallback;

        static string ExistingOrNull(string projectRelativePath) =>
            File.Exists(Path.Combine(EditorTools.ProjectRoot, projectRelativePath)) ? projectRelativePath : null;

        /// <summary>Regions with an imported Low scene (Assets/_Generated/World/&lt;id&gt;/World_&lt;id&gt;.unity).</summary>
        public static List<string> AvailableRegions()
        {
            var list = new List<string>();
            string root = Path.Combine(EditorTools.ProjectRoot, RegionPackPlanner.GeneratedWorldRoot);
            if (!Directory.Exists(root)) return list;
            foreach (var dir in Directory.GetDirectories(root).OrderBy(d => d, StringComparer.Ordinal))
            {
                string id = Path.GetFileName(dir);
                if (File.Exists(Path.Combine(EditorTools.ProjectRoot, RegionPackPlanner.ScenePath(id, "Low")))) list.Add(id);
            }
            return list;
        }

        public static int Build(string regionsArg, string tiersArg, string outputRoot, string setVersion, int minAppVersionCode, int maxAppVersionCode,
                                string packTarget = RegionPackManifest.TargetAndroid)
        {
            // ADR 0273: packs are per build target - Windows (D73, main platform: DLC / updates) or Android (lite version).
            BuildTarget target; BuildTargetGroup group;
            if (packTarget == RegionPackManifest.TargetWin64) { target = BuildTarget.StandaloneWindows64; group = BuildTargetGroup.Standalone; }
            else if (packTarget == RegionPackManifest.TargetAndroid) { target = BuildTarget.Android; group = BuildTargetGroup.Android; }
            else { Debug.LogError("REGIONPACKS_RESULT: Failed (-packTarget must be Android or Win64, got '" + packTarget + "')"); return 4; }
            if (EditorUserBuildSettings.activeBuildTarget != target && !EditorUserBuildSettings.SwitchActiveBuildTarget(group, target))
            {
                Debug.LogError("REGIONPACKS_RESULT: Failed (cannot switch to " + packTarget + "; start Unity with -buildTarget " + packTarget + ")");
                return 2;
            }

            var available = AvailableRegions();
            var regions = RegionPackPlanner.ResolveRegions(regionsArg, available, RegionC, out var unknown);
            if (unknown.Count > 0)
            {
                Debug.LogError("REGIONPACKS_RESULT: Failed (-regions: not imported: " + string.Join(", ", unknown) +
                               "; available: " + string.Join(", ", available) + ")");
                return 4;
            }
            if (regions.Count == 0) { Debug.LogError("REGIONPACKS_RESULT: Failed (no imported region to pack)"); return 4; }

            bool low = tiersArg != "High", high = tiersArg == "High" || tiersArg == "Both";
            var scenes = new List<RegionPackScene>();
            int withTile = 0;
            foreach (var r in regions)
            {
                // ADR 0273: the tile scene (ADR 0235) of the same tier goes into the same bundle, so additive streaming
                // can open a region from a pack exactly like a region in the player build.
                if (low)
                {
                    string lt = ExistingOrNull(RegionPackPlanner.TileScenePath(r, "Low"));
                    if (lt != null) withTile++;
                    else Debug.LogWarning("[PACKS] " + r + ": no tile scene " + RegionPackPlanner.TileScenePath(r, "Low") + " (import before ADR 0235?) - pack opens from the menu only, its seams stay closed");
                    scenes.Add(new RegionPackScene(RegionPackPlanner.PackId(r, "Low"), r, "Low", RegionPackPlanner.ScenePath(r, "Low"), lt));
                }
                if (!high) continue;
                string hp = RegionPackPlanner.ScenePath(r, "High");
                if (File.Exists(Path.Combine(EditorTools.ProjectRoot, hp)))
                {
                    string ht = ExistingOrNull(RegionPackPlanner.TileScenePath(r, "High"));
                    if (ht != null) withTile++;
                    scenes.Add(new RegionPackScene(RegionPackPlanner.PackId(r, "High"), r, "High", hp, ht));
                }
                else Debug.LogWarning("[PACKS] " + r + ": no High scene " + hp + " (import-region.ps1 without High?) - High pack skipped");
            }

            // Set identity: same scheme as the APK name (build-android.ps1: kamion-<bundleVersion>-<sha>[-dirty]).
            string sha = EditorTools.Git("rev-parse --short=10 HEAD") ?? "unknown";
            bool dirty = !string.IsNullOrEmpty(EditorTools.Git("status --porcelain --untracked-files=no"));
            if (string.IsNullOrEmpty(setVersion)) setVersion = PlayerSettings.bundleVersion + "-" + sha + (dirty ? "-dirty" : "");
            if (minAppVersionCode < 0)
            {
                // The APK built from this commit gets versionCode = commit count (BuildInfoWriter); older APKs may have
                // different serialized script layouts, so they are refused by default.
                int.TryParse(EditorTools.Git("rev-list --count HEAD"), out int count);
                minAppVersionCode = Math.Max(1, count);
            }
            if (!RegionPackPaths.IsSafeId(setVersion.ToLowerInvariant()))
            { Debug.LogError("REGIONPACKS_RESULT: Failed (bad -packSetVersion '" + setVersion + "')"); return 4; }

            string outDir = Path.Combine(outputRoot, setVersion);
            if (Directory.Exists(outDir)) Directory.Delete(outDir, true);   // a set is built in one run, never patched
            Directory.CreateDirectory(outDir);

            var plan = RegionPackPlanner.Build(scenes, p => AssetDatabase.GetDependencies(p, true));
            var builds = new List<AssetBundleBuild>();
            if (plan.Common.Count > 0)
                builds.Add(new AssetBundleBuild { assetBundleName = RegionPackEntry.CommonId + RegionPackPaths.BundleExtension, assetNames = plan.Common.ToArray() });
            foreach (var kv in plan.RegionData)
                builds.Add(new AssetBundleBuild { assetBundleName = RegionPackPlanner.DataPackId(kv.Key) + RegionPackPaths.BundleExtension, assetNames = kv.Value.ToArray() });
            foreach (var s in scenes)
                builds.Add(new AssetBundleBuild { assetBundleName = s.Id + RegionPackPaths.BundleExtension, assetNames = s.ScenePaths });
            WritePlan(Path.Combine(outDir, "regionpacks.plan.txt"), plan, scenes);
            Debug.Log($"[PACKS] set {setVersion}: {scenes.Count} scene packs ({withTile} with a tile scene), common {plan.Common.Count} assets, " +
                      $"data packs {plan.RegionData.Count}, skipped {plan.Skipped.Count} (scripts/scenes/editor)");
            if (plan.ResourcesCopies.Count > 0)
                Debug.LogWarning($"[PACKS] {plan.ResourcesCopies.Count} asset(s) under Resources/ referenced by region scenes: second copy in common " +
                                 "(another instance than Resources.Load) - see regionpacks.plan.txt [resources-copies]");

            // LZ4 (ChunkBasedCompression): LoadFromFile reads chunks on demand; LZMA would be decompressed whole into RAM
            // (ScriptReference AssetBundle.LoadFromFile). StrictMode: any build error fails the run.
            ShaderVariantStripper.Enabled = !EditorTools.HasArg("-noShaderStrip");
            var sw = System.Diagnostics.Stopwatch.StartNew();
            var abManifest = BuildPipeline.BuildAssetBundles(outDir, builds.ToArray(),
                BuildAssetBundleOptions.ChunkBasedCompression | BuildAssetBundleOptions.StrictMode, target);
            if (abManifest == null) { Debug.LogError("REGIONPACKS_RESULT: Failed (BuildPipeline.BuildAssetBundles returned null)"); return 1; }

            var manifest = new RegionPackManifest
            {
                schema = RegionPackManifest.SchemaId,
                packSetVersion = setVersion,
                unityVersion = Application.unityVersion,
                buildTarget = packTarget,
                minAppVersionCode = minAppVersionCode,
                maxAppVersionCode = maxAppVersionCode,
                gitSha = sha + (dirty ? "-dirty" : ""),
                createdUtc = DateTime.UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'"),
            };
            var entries = new List<RegionPackEntry>();
            long total = 0;
            foreach (var b in builds)
            {
                string file = b.assetBundleName;
                string path = Path.Combine(outDir, file);
                if (!File.Exists(path)) { Debug.LogError("REGIONPACKS_RESULT: Failed (missing output " + file + ")"); return 1; }
                BuildPipeline.GetCRCForAssetBundle(path, out uint crc);
                var scene = scenes.FirstOrDefault(s => s.Id + RegionPackPaths.BundleExtension == file);
                string id = Path.GetFileNameWithoutExtension(file);
                var deps = abManifest.GetAllDependencies(file).Select(Path.GetFileNameWithoutExtension)
                                     .OrderBy(d => d, StringComparer.Ordinal).ToArray();   // load order: RegionPackManifest.LoadOrder
                var e = new RegionPackEntry
                {
                    id = id,
                    region = scene.Region ?? (plan.RegionData.Keys.FirstOrDefault(r => RegionPackPlanner.DataPackId(r) == id) ?? ""),
                    tier = scene.Tier ?? "",
                    file = file,
                    sizeBytes = new FileInfo(path).Length,
                    sha256 = RegionPackHash.Sha256File(path),
                    crc = crc,
                    scenes = scene.ScenePath != null ? scene.SceneNames : Array.Empty<string>(),
                    dependencies = deps,
                };
                total += e.sizeBytes;
                entries.Add(e);
                Debug.Log($"REGIONPACK: {e.id} {e.sizeBytes / 1048576.0:F1} MB sha256={e.sha256} deps=[{string.Join(",", deps)}]");
            }
            manifest.packs = entries.ToArray();
            if (!RegionPackManifest.Validate(manifest, out string err))
            {
                Debug.LogError("REGIONPACKS_RESULT: Failed (manifest invalid: " + err + ")");
                return 1;
            }
            File.WriteAllText(Path.Combine(outDir, RegionPackManifest.FileName), JsonUtility.ToJson(manifest, true));
            Debug.Log($"REGIONPACKS_RESULT: Succeeded packs={entries.Count} total={total / 1048576.0:F1} MB time={sw.Elapsed.TotalSeconds:F0}s " +
                      $"set={setVersion} minAppVersionCode={minAppVersionCode} out={outDir}");
            return 0;
        }

        static void WritePlan(string path, RegionPackPlanner.Plan plan, List<RegionPackScene> scenes)
        {
            var sb = new System.Text.StringBuilder();
            sb.Append("# region pack plan (ADR 0234): explicit assets per bundle; scene bundles also hold their implicit assets\n");
            sb.Append("[common] ").Append(plan.Common.Count).Append('\n');
            foreach (var a in plan.Common) sb.Append("  ").Append(a).Append('\n');
            foreach (var kv in plan.RegionData)
            {
                sb.Append('[').Append(RegionPackPlanner.DataPackId(kv.Key)).Append("] ").Append(kv.Value.Count).Append('\n');
                foreach (var a in kv.Value) sb.Append("  ").Append(a).Append('\n');
            }
            foreach (var s in scenes)
            {
                plan.Unique.TryGetValue(s.Id, out var u);
                sb.Append('[').Append(s.Id).Append("] ").Append(string.Join(" + ", s.ScenePaths)).Append(" implicit=").Append(u?.Count ?? 0).Append('\n');
            }
            sb.Append("[resources-copies] ").Append(plan.ResourcesCopies.Count).Append('\n');
            foreach (var a in plan.ResourcesCopies) sb.Append("  ").Append(a).Append('\n');
            sb.Append("[skipped] ").Append(plan.Skipped.Count).Append('\n');
            File.WriteAllText(path, sb.ToString());
        }
    }
}
