using System;
using System.Collections.Generic;
using UnityEngine;

namespace Game.World.Packs
{
    /// <summary>
    /// Manifest of one region pack set (ADR 0234): written by <c>Game.Editor.Build.RegionPackCommands.BuildRegionPacks</c>
    /// next to the bundles (<c>artifacts/regionpacks/&lt;ver&gt;/regionpacks.json</c>) and kept on the device as
    /// <c>persistentDataPath/regionpacks/regionpacks.json</c>. One set = one bundle build run: the region bundles reference
    /// the shared <c>common</c> bundle of the SAME run, so packs of different sets are never mixed.
    /// Plain fields for <see cref="JsonUtility"/>; parsing and validation run once in the menu, never while driving.
    /// </summary>
    [Serializable]
    public sealed class RegionPackManifest
    {
        public const string SchemaId = "truck-sim-pl/region-packs/1";
        public const string FileName = "regionpacks.json";

        public string schema = "";
        /// <summary>Set version: "&lt;bundleVersion&gt;-&lt;git sha&gt;" of the commit the bundles were built from.</summary>
        public string packSetVersion = "";
        /// <summary>Exact Unity editor version that built the bundles (the player must match, ADR 0234 §3).</summary>
        public string unityVersion = "";
        /// <summary>Build target names of a set (ADR 0273): the player compares them with <see cref="TargetFor"/>.</summary>
        public const string TargetAndroid = "Android", TargetWin64 = "Win64";

        /// <summary>Set target name of a running platform: Android, Win64 (Windows player and editor), else the enum name.</summary>
        public static string TargetFor(UnityEngine.RuntimePlatform p) =>
            p == UnityEngine.RuntimePlatform.Android ? TargetAndroid
            : p == UnityEngine.RuntimePlatform.WindowsPlayer || p == UnityEngine.RuntimePlatform.WindowsEditor ? TargetWin64
            : p.ToString();

        public string buildTarget = "";
        /// <summary>Lowest Android versionCode (git commit count, BuildInfoWriter) whose scripts can read these bundles.</summary>
        public int minAppVersionCode;
        /// <summary>Highest compatible versionCode; 0 = no upper bound.</summary>
        public int maxAppVersionCode;
        public string gitSha = "";
        public string createdUtc = "";
        public RegionPackEntry[] packs = Array.Empty<RegionPackEntry>();

        public RegionPackEntry Find(string id)
        {
            if (packs == null || string.IsNullOrEmpty(id)) return null;
            foreach (var p in packs)
                if (p != null && p.id == id) return p;
            return null;
        }

        /// <summary>The scene pack of a region and content tier ("Low" / "High"); null when the set has none.</summary>
        public RegionPackEntry FindRegion(string region, string tier)
        {
            if (packs == null || string.IsNullOrEmpty(region)) return null;
            string t = string.IsNullOrEmpty(tier) ? RegionPackEntry.LowTier : tier;
            foreach (var p in packs)
                if (p != null && p.IsScenePack && p.region == region && p.tier == t) return p;
            return null;
        }

        /// <summary>Parses and validates a manifest. Returns false with a one-line reason on any problem.</summary>
        public static bool TryParse(string json, out RegionPackManifest manifest, out string error)
        {
            manifest = null;
            if (string.IsNullOrWhiteSpace(json)) { error = "empty manifest"; return false; }
            RegionPackManifest m;
            try { m = JsonUtility.FromJson<RegionPackManifest>(json); }
            catch (Exception e) { error = "manifest is not JSON: " + e.Message; return false; }
            if (m == null) { error = "manifest is not JSON"; return false; }
            if (!Validate(m, out error)) return false;
            manifest = m;
            return true;
        }

        public static bool Validate(RegionPackManifest m, out string error)
        {
            if (m.schema != SchemaId) { error = "unknown schema '" + m.schema + "' (expected " + SchemaId + ")"; return false; }
            if (string.IsNullOrEmpty(m.packSetVersion)) { error = "packSetVersion missing"; return false; }
            if (string.IsNullOrEmpty(m.unityVersion)) { error = "unityVersion missing"; return false; }
            if (m.minAppVersionCode < 0 || (m.maxAppVersionCode != 0 && m.maxAppVersionCode < m.minAppVersionCode))
            { error = "bad app version range " + m.minAppVersionCode + ".." + m.maxAppVersionCode; return false; }
            if (m.packs == null || m.packs.Length == 0) { error = "no packs"; return false; }

            var ids = new HashSet<string>();
            var files = new HashSet<string>();
            foreach (var p in m.packs)
            {
                if (p == null) { error = "null pack entry"; return false; }
                if (!RegionPackPaths.IsSafeId(p.id)) { error = "bad pack id '" + p.id + "'"; return false; }
                if (!ids.Add(p.id)) { error = "duplicate pack id '" + p.id + "'"; return false; }
                if (!RegionPackPaths.IsSafeBundleFileName(p.file)) { error = "pack '" + p.id + "': bad file name '" + p.file + "'"; return false; }
                if (!files.Add(p.file)) { error = "pack '" + p.id + "': file '" + p.file + "' listed twice"; return false; }
                if (p.sizeBytes <= 0) { error = "pack '" + p.id + "': sizeBytes must be > 0"; return false; }
                if (!RegionPackHash.IsSha256Hex(p.sha256)) { error = "pack '" + p.id + "': sha256 must be 64 lowercase hex chars"; return false; }
                if (p.IsScenePack && string.IsNullOrEmpty(p.region)) { error = "pack '" + p.id + "': scene pack without region"; return false; }
                if (p.IsScenePack && p.tier != RegionPackEntry.LowTier && p.tier != RegionPackEntry.HighTier)
                { error = "pack '" + p.id + "': tier must be Low or High"; return false; }
            }
            foreach (var p in m.packs)
            {
                if (p.dependencies == null) continue;
                foreach (var d in p.dependencies)
                {
                    if (d == p.id) { error = "pack '" + p.id + "' depends on itself"; return false; }
                    var dep = m.Find(d);
                    if (dep == null) { error = "pack '" + p.id + "': unknown dependency '" + d + "'"; return false; }
                    // Unity cannot make a scene bundle a dependency of another bundle; a set where it happens is broken.
                    if (dep.IsScenePack) { error = "pack '" + p.id + "' depends on scene pack '" + d + "'"; return false; }
                    // Lists are transitively closed (AssetBundleManifest.GetAllDependencies): a dependency's own
                    // dependencies must be listed too. With "no self-dependency" this also rules out cycles.
                    if (dep.dependencies != null)
                        foreach (var dd in dep.dependencies)
                            if (Array.IndexOf(p.dependencies, dd) < 0)
                            { error = "pack '" + p.id + "': dependency list not closed ('" + d + "' needs '" + dd + "')"; return false; }
                }
            }
            error = null;
            return true;
        }

        /// <summary>Dependencies of a pack in load order: fewest own dependencies first (common before region data).</summary>
        public List<RegionPackEntry> LoadOrder(RegionPackEntry entry)
        {
            var list = new List<RegionPackEntry>();
            if (entry?.dependencies == null) return list;
            foreach (var d in entry.dependencies)
            {
                var dep = Find(d);
                if (dep != null) list.Add(dep);
            }
            list.Sort((a, b) => (a.dependencies?.Length ?? 0).CompareTo(b.dependencies?.Length ?? 0));
            return list;
        }

        /// <summary>Total bytes of a pack plus its dependencies (download / storage size shown in the menu).</summary>
        public long SizeWithDependencies(RegionPackEntry entry)
        {
            if (entry == null) return 0;
            long n = entry.sizeBytes;
            if (entry.dependencies != null)
                foreach (var d in entry.dependencies)
                {
                    var dep = Find(d);
                    if (dep != null) n += dep.sizeBytes;
                }
            return n;
        }
    }

    /// <summary>One bundle of a pack set: the shared <c>common</c> bundle, a region data bundle (<c>&lt;region&gt;-data</c>:
    /// assets used by both content tiers of one region, e.g. collision and instances) or one region scene bundle.</summary>
    [Serializable]
    public sealed class RegionPackEntry
    {
        public const string LowTier = "Low", HighTier = "High";
        public const string CommonId = "common";

        /// <summary>"common", "&lt;region&gt;-data", "&lt;region&gt;" (Low content) or "&lt;region&gt;-high".</summary>
        public string id = "";
        /// <summary>Region id (Data/Regions/&lt;id&gt;); empty for the common bundle.</summary>
        public string region = "";
        /// <summary>"Low" (Low + Medium quality) or "High" (High + Ultra), ADR 0012; empty for the shared bundle.</summary>
        public string tier = "";
        /// <summary>Bundle file name, e.g. "dk65-06.bundle" (no directories).</summary>
        public string file = "";
        public long sizeBytes;
        /// <summary>SHA-256 of the bundle file, lowercase hex.</summary>
        public string sha256 = "";
        /// <summary>Unity CRC-32 of the uncompressed content (BuildPipeline.GetCRCForAssetBundle); informative only.</summary>
        public uint crc;
        /// <summary>Scene names inside the bundle (e.g. "World_dk65-06"); empty for the shared bundle.</summary>
        public string[] scenes = Array.Empty<string>();
        /// <summary>Pack ids that must be loaded first (normally ["common"], plus "&lt;region&gt;-data" when both tiers exist).</summary>
        public string[] dependencies = Array.Empty<string>();

        /// <summary>A scene bundle (what the menu starts); common and data bundles are only dependencies.</summary>
        public bool IsScenePack => scenes != null && scenes.Length > 0;
    }
}
