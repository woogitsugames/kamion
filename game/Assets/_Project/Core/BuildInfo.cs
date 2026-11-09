using System;
using UnityEngine;

namespace Game.Core
{
    /// <summary>
    /// Build metadata baked by the editor build pipeline into Resources/build_info.json
    /// (generated, git-ignored). Falls back to "editor" values when the file is absent.
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

        static BuildInfo s_Current;

        public static BuildInfo Current => s_Current ??= Load();

        public string ShortLabel => $"{version} ({gitSha}{(gitDirty ? "-dirty" : "")})";

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
