using System;
using System.IO;

namespace Game.World.Packs
{
    /// <summary>State of a region's content as the start menu sees it (ADR 0234 §4).</summary>
    public enum RegionPackState
    {
        /// <summary>The region scene is in the APK (build list); no pack needed.</summary>
        InBase,
        /// <summary>No installed bundle (or no installed set): can be pushed with adb or downloaded.</summary>
        NotInstalled,
        /// <summary>Installed and (as far as checked) intact; dependencies present.</summary>
        Installed,
        /// <summary>The installed set does not fit this APK (Unity version, app version range, target).</summary>
        Incompatible,
        /// <summary>File size or SHA-256 differs from the manifest: delete and fetch again.</summary>
        Corrupt,
        /// <summary>The region bundle is fine but a dependency (common) is missing or broken.</summary>
        MissingDependency,
        /// <summary>A download of this pack is running.</summary>
        Downloading,
        /// <summary>The bundles are loaded (scene can be opened with SceneManager.LoadScene).</summary>
        Loaded,
    }

    /// <summary>Identity of the running player, compared with a manifest (from BuildInfo + Application in the game).</summary>
    public readonly struct RegionPackAppIdentity
    {
        public readonly int VersionCode;
        public readonly string UnityVersion;
        public readonly string BuildTarget;

        public RegionPackAppIdentity(int versionCode, string unityVersion, string buildTarget)
        {
            VersionCode = versionCode; UnityVersion = unityVersion ?? ""; BuildTarget = buildTarget ?? "";
        }
    }

    /// <summary>Result of resolving one region pack: state, a short English reason for logs, bytes to download/store.</summary>
    public readonly struct RegionPackInfo
    {
        public readonly RegionPackState State;
        public readonly string Reason;
        /// <summary>Pack + missing dependencies (bytes still to fetch) or pack + dependencies when installed.</summary>
        public readonly long SizeBytes;
        /// <summary>Download progress 0..1 while <see cref="RegionPackState.Downloading"/>.</summary>
        public readonly float Progress;

        public RegionPackInfo(RegionPackState state, string reason, long sizeBytes, float progress = 0f)
        {
            State = state; Reason = reason ?? ""; SizeBytes = sizeBytes; Progress = progress;
        }

        public bool CanStart => State == RegionPackState.InBase || State == RegionPackState.Installed || State == RegionPackState.Loaded;
        public override string ToString() => State + (Reason.Length > 0 ? " (" + Reason + ")" : "") + " " + SizeBytes + " B";
    }

    /// <summary>File system access used by the resolver; a fake in EditMode tests.</summary>
    public interface IRegionPackFiles
    {
        /// <summary>Size of the file or -1 when it does not exist.</summary>
        long Size(string path);
        string Sha256(string path);
    }

    public sealed class RegionPackDiskFiles : IRegionPackFiles
    {
        public static readonly RegionPackDiskFiles Instance = new RegionPackDiskFiles();
        public long Size(string path) => path != null && File.Exists(path) ? new FileInfo(path).Length : -1;
        public string Sha256(string path) => RegionPackHash.Sha256File(path);
    }

    /// <summary>
    /// Pure state resolution (ADR 0234 §4). Order: no set → NotInstalled; set incompatible → Incompatible; pack not in the
    /// set or file missing → NotInstalled; size differs → Corrupt; (deep) SHA-256 differs → Corrupt; any dependency not
    /// intact → MissingDependency; else Installed. A shallow check (sizes only) is what the menu shows; the deep check
    /// (hashing every file, ~1 s per 100 MB, ESTIMATED) runs once before loading.
    /// </summary>
    public static class RegionPackResolver
    {
        /// <summary>Checks Unity version, build target and the app version range. Null = compatible, else the reason.</summary>
        public static string CompatibilityProblem(RegionPackManifest m, in RegionPackAppIdentity app)
        {
            if (m == null) return "no manifest";
            // Bundles carry serialized data of this exact editor; a different player version may not read them (ADR 0234 §3).
            if (!string.Equals(m.unityVersion, app.UnityVersion, StringComparison.Ordinal))
                return "built with Unity " + m.unityVersion + ", app runs " + app.UnityVersion;
            if (!string.IsNullOrEmpty(m.buildTarget) && !string.IsNullOrEmpty(app.BuildTarget) &&
                !string.Equals(m.buildTarget, app.BuildTarget, StringComparison.OrdinalIgnoreCase))
                return "built for " + m.buildTarget + ", app is " + app.BuildTarget;
            if (app.VersionCode < m.minAppVersionCode)
                return "needs app versionCode >= " + m.minAppVersionCode + " (app " + app.VersionCode + ")";
            if (m.maxAppVersionCode != 0 && app.VersionCode > m.maxAppVersionCode)
                return "needs app versionCode <= " + m.maxAppVersionCode + " (app " + app.VersionCode + ")";
            return null;
        }

        /// <summary>Resolves the pack of <paramref name="region"/>/<paramref name="tier"/> in the installed set.</summary>
        public static RegionPackInfo Resolve(RegionPackManifest installed, string region, string tier, in RegionPackAppIdentity app,
                                             RegionPackPaths paths, IRegionPackFiles files, bool deep)
        {
            if (installed == null) return new RegionPackInfo(RegionPackState.NotInstalled, "no pack set installed", 0);
            string compat = CompatibilityProblem(installed, app);
            var entry = installed.FindRegion(region, tier);
            if (compat != null) return new RegionPackInfo(RegionPackState.Incompatible, compat, installed.SizeWithDependencies(entry));
            if (entry == null) return new RegionPackInfo(RegionPackState.NotInstalled, "region not in pack set " + installed.packSetVersion, 0);

            var own = CheckFile(entry, paths, files, deep);
            if (own == RegionPackState.NotInstalled)
                return new RegionPackInfo(RegionPackState.NotInstalled, entry.file + " missing", MissingBytes(installed, entry, paths, files));
            if (own == RegionPackState.Corrupt)
                return new RegionPackInfo(RegionPackState.Corrupt, entry.file + (deep ? " size or sha256 mismatch" : " size mismatch"),
                                          installed.SizeWithDependencies(entry));
            if (entry.dependencies != null)
                foreach (var d in entry.dependencies)
                {
                    var dep = installed.Find(d);
                    var ds = dep == null ? RegionPackState.NotInstalled : CheckFile(dep, paths, files, deep);
                    if (ds != RegionPackState.Installed)
                        return new RegionPackInfo(RegionPackState.MissingDependency,
                                                  "dependency '" + d + "' " + (ds == RegionPackState.Corrupt ? "corrupt" : "missing"),
                                                  MissingBytes(installed, entry, paths, files));
                }
            return new RegionPackInfo(RegionPackState.Installed, "", installed.SizeWithDependencies(entry));
        }

        /// <summary>Installed / NotInstalled / Corrupt for one bundle file.</summary>
        public static RegionPackState CheckFile(RegionPackEntry e, RegionPackPaths paths, IRegionPackFiles files, bool deep)
        {
            string path = paths.Installed(e.file);
            if (path == null) return RegionPackState.Corrupt;
            long size = files.Size(path);
            if (size < 0) return RegionPackState.NotInstalled;
            if (size != e.sizeBytes) return RegionPackState.Corrupt;
            if (deep && !string.Equals(files.Sha256(path), e.sha256, StringComparison.Ordinal)) return RegionPackState.Corrupt;
            return RegionPackState.Installed;
        }

        /// <summary>Bytes still to fetch for a pack: itself and dependencies whose file is not intact (shallow check).</summary>
        public static long MissingBytes(RegionPackManifest m, RegionPackEntry entry, RegionPackPaths paths, IRegionPackFiles files)
        {
            if (entry == null) return 0;
            long n = CheckFile(entry, paths, files, false) == RegionPackState.Installed ? 0 : entry.sizeBytes;
            if (entry.dependencies != null)
                foreach (var d in entry.dependencies)
                {
                    var dep = m.Find(d);
                    if (dep != null && CheckFile(dep, paths, files, false) != RegionPackState.Installed) n += dep.sizeBytes;
                }
            return n;
        }

        /// <summary>Content tier to start a region with: High for High/Ultra quality when its pack is usable, else Low (ADR 0012).</summary>
        public static string PreferredTier(string qualityTier, bool highUsable) =>
            (qualityTier == "High" || qualityTier == "Ultra") && highUsable ? RegionPackEntry.HighTier : RegionPackEntry.LowTier;
    }
}
