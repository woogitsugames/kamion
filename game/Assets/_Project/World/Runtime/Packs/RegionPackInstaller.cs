using System;
using System.Collections.Generic;
using System.IO;

namespace Game.World.Packs
{
    /// <summary>Outcome of <see cref="RegionPackInstaller.InstallIncoming"/>.</summary>
    public sealed class RegionPackInstallResult
    {
        /// <summary>False when there was nothing to install (no incoming manifest).</summary>
        public bool Attempted;
        /// <summary>Set-level rejection (bad manifest, incompatible): nothing changed in the installed set.</summary>
        public string Error;
        public string PackSetVersion = "";
        public readonly List<string> Installed = new List<string>();
        public readonly List<string> Kept = new List<string>();
        public readonly List<string> Rejected = new List<string>();
        public readonly List<string> Removed = new List<string>();

        public bool Ok => Attempted && Error == null;

        public override string ToString() => !Attempted ? "nothing incoming"
            : Error != null ? "rejected: " + Error
            : $"set {PackSetVersion}: installed [{string.Join(",", Installed)}] kept [{string.Join(",", Kept)}] " +
              $"rejected [{string.Join(",", Rejected)}] removed [{string.Join(",", Removed)}]";
    }

    /// <summary>
    /// Moves verified bundles from <c>regionpacks/incoming/</c> (adb push or a finished download) into the installed set
    /// (ADR 0234 §5). Plain System.IO, no Unity calls: runs on a worker thread from the menu and in EditMode tests.
    /// Rules: the incoming manifest must parse and fit this APK, otherwise it is renamed to <c>*.rejected</c> and nothing
    /// changes. Every incoming bundle is checked (size + SHA-256) before it replaces an installed file; a bad one is deleted.
    /// Installed bundles that the new set does not list, or whose bytes differ from the new manifest, are deleted (they
    /// belong to an older set and reference its common bundle). The manifest is written last, via a temp file.
    /// </summary>
    public static class RegionPackInstaller
    {
        public const string RejectedSuffix = ".rejected";

        public static RegionPackInstallResult InstallIncoming(RegionPackPaths paths, in RegionPackAppIdentity app, IRegionPackFiles files)
        {
            var r = new RegionPackInstallResult();
            if (!File.Exists(paths.IncomingManifest)) return r;
            r.Attempted = true;

            if (!RegionPackManifest.TryParse(File.ReadAllText(paths.IncomingManifest), out var incoming, out string err))
                return Reject(paths, r, "incoming manifest invalid: " + err);
            r.PackSetVersion = incoming.packSetVersion;
            string compat = RegionPackResolver.CompatibilityProblem(incoming, app);
            if (compat != null) return Reject(paths, r, "incoming set " + incoming.packSetVersion + " incompatible: " + compat);

            RegionPackManifest current = null;
            if (File.Exists(paths.InstalledManifest))
                RegionPackManifest.TryParse(File.ReadAllText(paths.InstalledManifest), out current, out _);

            Directory.CreateDirectory(paths.Root);
            foreach (var e in incoming.packs)
            {
                string src = paths.IncomingFile(e.file), dst = paths.Installed(e.file);
                if (files.Size(src) >= 0)
                {
                    if (files.Size(src) == e.sizeBytes && files.Sha256(src) == e.sha256)
                    {
                        if (File.Exists(dst)) File.Delete(dst);
                        File.Move(src, dst);
                        r.Installed.Add(e.id);
                    }
                    else
                    {
                        File.Delete(src);
                        r.Rejected.Add(e.id);
                    }
                    continue;
                }
                long have = files.Size(dst);
                if (have < 0) continue;   // not installed, not supplied: stays "NotInstalled" in the new set
                var old = current?.Find(e.id);
                // Same bytes as an already verified file of the current set: no need to hash again.
                bool sameAsVerified = old != null && old.sha256 == e.sha256 && old.sizeBytes == e.sizeBytes && have == e.sizeBytes;
                if (sameAsVerified || (have == e.sizeBytes && files.Sha256(dst) == e.sha256)) r.Kept.Add(e.id);
                else
                {
                    File.Delete(dst);
                    r.Removed.Add(e.id);
                }
            }

            // Bundles of an older set that the new set no longer lists.
            foreach (var path in Directory.GetFiles(paths.Root, "*" + RegionPackPaths.BundleExtension))
            {
                string name = Path.GetFileName(path);
                if (FindByFile(incoming, name) != null) continue;
                File.Delete(path);
                r.Removed.Add(name);
            }

            string tmp = paths.InstalledManifest + ".tmp";
            File.WriteAllText(tmp, File.ReadAllText(paths.IncomingManifest));
            if (File.Exists(paths.InstalledManifest)) File.Delete(paths.InstalledManifest);
            File.Move(tmp, paths.InstalledManifest);
            File.Delete(paths.IncomingManifest);
            return r;
        }

        static RegionPackInstallResult Reject(RegionPackPaths paths, RegionPackInstallResult r, string error)
        {
            r.Error = error;
            string rejected = paths.IncomingManifest + RejectedSuffix;
            try
            {
                if (File.Exists(rejected)) File.Delete(rejected);
                File.Move(paths.IncomingManifest, rejected);   // do not retry the same bad set on every start
            }
            catch (IOException) { }
            return r;
        }

        static RegionPackEntry FindByFile(RegionPackManifest m, string file)
        {
            foreach (var p in m.packs)
                if (string.Equals(p.file, file, StringComparison.Ordinal)) return p;
            return null;
        }
    }
}
