using System;
using System.IO;
using System.Text.RegularExpressions;
using UnityEngine;

namespace Game.Core
{
    /// <summary>
    /// Build metadata baked by the editor build pipeline into Resources/build_info.json
    /// (generated, git-ignored). Falls back to "editor" values when the file is absent.
    /// ADR 0276: the git sha is baked before the build (it is part of the player data); the content hash of the player
    /// data (<c>Kamion_Data</c>) can only be computed after the build, so scripts/postbuild-windows.py writes it to
    /// <see cref="BuildIdFileName"/> NEXT TO the exe (outside the hashed folder, so the hash never contains itself) and
    /// the player reads it once at start (<see cref="ContentHash"/>; "" when the file is absent: editor, Android, older builds).
    /// </summary>
    [Serializable]
    public sealed class BuildInfo
    {
        public const string ResourceName = "build_info";

        public string version = "0.0.0";
        public string gitSha = "editor";
        public bool gitDirty;
        public int versionCode;
        public string buildTimeUtc = "";
        public string unityVersion = "";
        public bool development;

        /// <summary>File next to the player exe with the content hash (ADR 0276, scripts/postbuild-windows.py).</summary>
        public const string BuildIdFileName = "build-id.json";
        /// <summary>Length of the short content hash (hex digits) shown in the menu and the log.</summary>
        public const int ContentHashLength = 12;

        /// <summary>First 12 hex digits of the SHA-256 of the player data manifest; "" when unknown. Not serialised
        /// into build_info.json (it cannot be known before the build).</summary>
        [NonSerialized] public string contentHash = "";

        public string ContentHash => contentHash ?? "";

        static BuildInfo s_Current;

        public static BuildInfo Current => s_Current ??= Load();

        public string ShortLabel => $"{version} ({gitSha}{(gitDirty ? "-dirty" : "")})";

        /// <summary><see cref="ShortLabel"/> plus the content hash of the player data when known (ADR 0276): two builds
        /// of the same commit differ here, while Kamion.exe (the Unity launcher stub) is the same file in every build.</summary>
        public string IdentityLabel => string.IsNullOrEmpty(contentHash) ? ShortLabel : ShortLabel + " · dane " + contentHash;

        static readonly Regex k_ContentHash = new Regex(
            "\"contentHash\"\\s*:\\s*\"([0-9a-fA-F]+)\"", RegexOptions.CultureInvariant);

        /// <summary>Content hash from the text of <see cref="BuildIdFileName"/>: exactly <see cref="ContentHashLength"/> hex
        /// digits, lower case; "" for anything else (missing key, wrong length, not JSON). Pure; no Unity API.</summary>
        public static string ParseContentHash(string json)
        {
            if (string.IsNullOrEmpty(json)) return "";
            var m = k_ContentHash.Match(json);
            if (!m.Success || m.Groups[1].Value.Length != ContentHashLength) return "";
            return m.Groups[1].Value.ToLowerInvariant();
        }

        /// <summary>Path of <see cref="BuildIdFileName"/> for a player whose data folder is <paramref name="dataPath"/>
        /// (Application.dataPath = &lt;exe dir&gt;/Kamion_Data on Windows); null when there is no parent folder.</summary>
        public static string BuildIdPathFor(string dataPath)
        {
            if (string.IsNullOrEmpty(dataPath)) return null;
            string dir = Path.GetDirectoryName(dataPath.TrimEnd('/', '\\'));
            return string.IsNullOrEmpty(dir) ? null : Path.Combine(dir, BuildIdFileName);
        }

        /// <summary>Reads the content hash next to the player; "" when the file is absent or unreadable (never throws).</summary>
        public static string ReadContentHash(string dataPath)
        {
            try
            {
                string path = BuildIdPathFor(dataPath);
                return path != null && File.Exists(path) ? ParseContentHash(File.ReadAllText(path)) : "";
            }
            catch (Exception) { return ""; }   // IO / security errors: identification is optional
        }

        public static BuildInfo Parse(string json)
        {
            if (string.IsNullOrWhiteSpace(json)) return Fallback();
            try
            {
                var info = JsonUtility.FromJson<BuildInfo>(json);
                return info ?? Fallback();
            }
            catch (ArgumentException)
            {
                return Fallback();
            }
        }

        static BuildInfo Load()
        {
            var asset = Resources.Load<TextAsset>(ResourceName);
            var info = asset != null ? Parse(asset.text) : Fallback();
            if (string.IsNullOrEmpty(info.unityVersion)) info.unityVersion = Application.unityVersion;
            // ADR 0276: once per process (Current is cached) - no file access in the driving loop. Desktop players only:
            // on Android dataPath is the APK and there is no file next to it.
            if (!Application.isEditor && Application.platform != RuntimePlatform.Android)
                info.contentHash = ReadContentHash(Application.dataPath);
            return info;
        }

        static BuildInfo Fallback() => new BuildInfo
        {
            version = Application.version,
            gitSha = "editor",
            unityVersion = Application.unityVersion,
        };
    }
}
