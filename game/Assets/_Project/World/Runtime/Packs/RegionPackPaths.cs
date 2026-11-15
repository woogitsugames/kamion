using System.IO;

namespace Game.World.Packs
{
    /// <summary>
    /// On-device layout of region packs (ADR 0234), rooted at <c>Application.persistentDataPath</c>:
    /// <code>
    /// regionpacks/regionpacks.json        installed set manifest
    /// regionpacks/&lt;file&gt;.bundle          verified bundles of that set
    /// regionpacks/incoming/               drop zone: adb push (manifest + bundles) and downloads (*.part while running)
    /// </code>
    /// On Android persistentDataPath is normally /storage/emulated/0/Android/data/&lt;package&gt;/files, so the drop zone is
    /// <c>/sdcard/Android/data/com.woogitsugames.kamion/files/regionpacks/incoming/</c> for <c>adb push</c> (UNVERIFIED on the A16:
    /// the lead checks access to Android/data with Android 14 shell permissions).
    /// Pure path logic, no Unity calls, so EditMode tests can use any temp directory as the root.
    /// </summary>
    public sealed class RegionPackPaths
    {
        public const string DirName = "regionpacks";
        public const string IncomingDirName = "incoming";
        public const string PartSuffix = ".part";
        public const string BundleExtension = ".bundle";
        const int MaxNameLength = 96;

        public readonly string Root;
        public readonly string Incoming;

        /// <param name="persistentDataPath">Application.persistentDataPath (or a temp dir in tests).</param>
        public RegionPackPaths(string persistentDataPath)
        {
            Root = Path.Combine(persistentDataPath ?? "", DirName);
            Incoming = Path.Combine(Root, IncomingDirName);
        }

        public string InstalledManifest => Path.Combine(Root, RegionPackManifest.FileName);
        public string IncomingManifest => Path.Combine(Incoming, RegionPackManifest.FileName);

        /// <summary>Installed bundle path; null for an unsafe name (never touches the file system outside <see cref="Root"/>).</summary>
        public string Installed(string file) => IsSafeBundleFileName(file) ? Path.Combine(Root, file) : null;

        public string IncomingFile(string file) => IsSafeBundleFileName(file) ? Path.Combine(Incoming, file) : null;

        public string IncomingPart(string file) => IsSafeBundleFileName(file) ? Path.Combine(Incoming, file + PartSuffix) : null;

        /// <summary>Pack ids: lowercase a–z, 0–9, '-', '_', '.', starting with a letter or digit, no "..".</summary>
        public static bool IsSafeId(string id) => IsSafeName(id);

        /// <summary>
        /// Bundle file names come from a manifest that may arrive over the network, so they are checked before any file
        /// operation: a safe id + ".bundle", no separators, no "..", at most 96 characters.
        /// </summary>
        public static bool IsSafeBundleFileName(string file)
        {
            if (string.IsNullOrEmpty(file) || !file.EndsWith(BundleExtension, System.StringComparison.Ordinal)) return false;
            return IsSafeName(file.Substring(0, file.Length - BundleExtension.Length)) && file.Length <= MaxNameLength;
        }

        static bool IsSafeName(string s)
        {
            if (string.IsNullOrEmpty(s) || s.Length > MaxNameLength) return false;
            if (s.Contains("..")) return false;
            for (int i = 0; i < s.Length; i++)
            {
                char c = s[i];
                bool alnum = (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9');
                if (i == 0 && !alnum) return false;
                if (!alnum && c != '-' && c != '_' && c != '.') return false;
            }
            return true;
        }

        /// <summary>Joins a base URL and a file name ("https://host/packs" + "a.bundle"); null when the base is empty.</summary>
        public static string Url(string baseUrl, string file)
        {
            if (string.IsNullOrWhiteSpace(baseUrl)) return null;
            string b = baseUrl.Trim();
            return b.EndsWith("/") ? b + file : b + "/" + file;
        }
    }
}
