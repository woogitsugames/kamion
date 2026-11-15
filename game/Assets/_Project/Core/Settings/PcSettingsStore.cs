using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Game.Core.Settings
{
    /// <summary>Read-only view of the PlayerPrefs keys written before ADR 0270 (migration source; tests use a dictionary).</summary>
    public interface ILegacySettingsSource
    {
        bool HasKey(string key);
        string GetString(string key);
        int GetInt(string key);
        float GetFloat(string key);
    }

    /// <summary>PlayerPrefs as the legacy source.</summary>
    public sealed class PlayerPrefsLegacySource : ILegacySettingsSource
    {
        public bool HasKey(string key) => PlayerPrefs.HasKey(key);
        public string GetString(string key) => PlayerPrefs.GetString(key, "");
        public int GetInt(string key) => PlayerPrefs.GetInt(key, 0);
        public float GetFloat(string key) => PlayerPrefs.GetFloat(key, 0f);
    }

    /// <summary>Where the loaded settings came from and what had to be repaired (logged once at startup).</summary>
    public sealed class PcSettingsLoadReport
    {
        public enum Origin { File, Backup, Legacy, Defaults }
        public Origin Source;
        public int FileSchemaVersion;
        public bool Migrated;
        /// <summary>The file was written by a newer game version: known fields were read, unknown ones are lost on the next save.</summary>
        public bool FromNewerVersion;
        /// <summary>The main file could not be parsed (kept next to it as <c>.bad</c>).</summary>
        public bool Corrupt;
        public readonly List<string> FixedFields = new List<string>();

        public override string ToString() =>
            "source=" + Source + " fileSchema=" + FileSchemaVersion + " migrated=" + Migrated + " newer=" + FromNewerVersion +
            " corrupt=" + Corrupt + " fixed=[" + string.Join(",", FixedFields) + "]";
    }

    /// <summary>
    /// JSON codec and schema migration of <see cref="PcSettingsData"/> (ADR 0270). Pure: no file system, no Unity objects
    /// besides JsonUtility.
    ///
    /// Migrations:
    /// - legacy (no file): PlayerPrefs keys written before ADR 0270 - <c>diag.qualityTier</c> (start menu / -tier),
    ///   <c>diag.targetFps</c> (start menu fps buttons), <c>ui.hudScale</c> (ADR 0265, #131) - become schema 1 fields;
    /// - schema 0 / missing <c>schemaVersion</c>: same layout as 1 (fields missing in the file keep their defaults);
    /// - schema newer than <see cref="PcSettingsData.CurrentSchemaVersion"/>: known fields are read, the report says so.
    /// Every path ends in <see cref="PcSettingsData.Sanitize"/>.
    /// </summary>
    public static class PcSettingsJson
    {
        public const string LegacyTierKey = "diag.qualityTier";
        public const string LegacyFpsKey = "diag.targetFps";
        /// <summary>Same key as <c>UiPreferences.PrefHudScale</c> of ADR 0265 (#131).</summary>
        public const string HudScaleKey = "ui.hudScale";

        [Serializable]
        sealed class VersionProbe { public int schemaVersion; }

        public static string ToJson(PcSettingsData d) => JsonUtility.ToJson(d, true);

        /// <summary>Parses a settings file. Null when the text is not usable JSON of an object (caller falls back).</summary>
        public static PcSettingsData TryParse(string json, PcSettingsLoadReport report)
        {
            if (string.IsNullOrWhiteSpace(json)) return null;
            string t = json.Trim();
            if (t.Length < 2 || t[0] != '{' || t[t.Length - 1] != '}') return null;
            PcSettingsData d;
            int version;
            try
            {
                var probe = JsonUtility.FromJson<VersionProbe>(t);
                version = probe != null ? probe.schemaVersion : 0;
                d = JsonUtility.FromJson<PcSettingsData>(t);
            }
            catch (Exception) { return null; }
            if (d == null) return null;
            Migrate(d, version, report);
            return d;
        }

        /// <summary>Upgrades a parsed object from <paramref name="fileVersion"/> to the current schema, then sanitizes.</summary>
        public static PcSettingsData Migrate(PcSettingsData d, int fileVersion, PcSettingsLoadReport report)
        {
            if (report != null)
            {
                report.FileSchemaVersion = fileVersion;
                report.Migrated = fileVersion < PcSettingsData.CurrentSchemaVersion;
                report.FromNewerVersion = fileVersion > PcSettingsData.CurrentSchemaVersion;
            }
            // 0 -> 1: no field renames (the pre-release file had the same layout); missing fields already hold defaults.
            // Future: "if (fileVersion < 2) { ... }" blocks go here, oldest first.
            return d.Sanitize(report?.FixedFields);
        }

        /// <summary>Schema 1 from the PlayerPrefs keys of the start menu / ADR 0265; null when none of them exists.</summary>
        public static PcSettingsData FromLegacy(ILegacySettingsSource src, PcSettingsLoadReport report)
        {
            if (src == null) return null;
            bool any = false;
            var d = PcSettingsData.Defaults();
            if (src.HasKey(LegacyTierKey))
            {
                string id = TierChoices.FromQualityLevel(src.GetString(LegacyTierKey));
                if (id != null) { d.graphicsTier = id; any = true; }
            }
            if (src.HasKey(LegacyFpsKey))
            {
                int fps = src.GetInt(LegacyFpsKey);
                if (fps > 0) { d.fpsCap = PcSettingsData.IsAllowedFpsCap(fps) ? fps : d.fpsCap; any = true; }
            }
            if (src.HasKey(HudScaleKey)) { d.hudScale = src.GetFloat(HudScaleKey); any = true; }
            if (!any) return null;
            if (report != null) { report.Migrated = true; report.FileSchemaVersion = 0; }
            return d.Sanitize(report?.FixedFields);
        }
    }

    /// <summary>
    /// The settings file <c>&lt;persistentDataPath&gt;/settings_pc.json</c> (ADR 0270). Atomic save: write <c>.tmp</c>, flush to
    /// disk, then replace the file (previous version kept as <c>.bak</c>); a crash mid-write leaves either the old or the new
    /// file, never a half one. Load order: file -> <c>.bak</c> -> legacy PlayerPrefs -> defaults. An unreadable file is
    /// renamed to <c>.bad</c> (kept for diagnosis) instead of being silently overwritten.
    /// </summary>
    public sealed class PcSettingsStore
    {
        public const string FileName = "settings_pc.json";

        readonly ILegacySettingsSource m_Legacy;

        public string Directory { get; }
        public string FilePath { get; }
        public string BackupPath => FilePath + ".bak";
        public string TempPath => FilePath + ".tmp";
        public string CorruptPath => FilePath + ".bad";

        public PcSettingsStore(string directory, ILegacySettingsSource legacy = null)
        {
            Directory = directory;
            FilePath = Path.Combine(directory, FileName);
            m_Legacy = legacy;
        }

        public bool Exists => File.Exists(FilePath);

        public PcSettingsData Load(out PcSettingsLoadReport report)
        {
            report = new PcSettingsLoadReport();
            if (File.Exists(FilePath))
            {
                var d = PcSettingsJson.TryParse(ReadOrNull(FilePath), report);
                if (d != null) { report.Source = PcSettingsLoadReport.Origin.File; return d; }
                report.Corrupt = true;
                report.FixedFields.Clear();
                TryMove(FilePath, CorruptPath);
            }
            if (File.Exists(BackupPath))
            {
                var d = PcSettingsJson.TryParse(ReadOrNull(BackupPath), report);
                if (d != null) { report.Source = PcSettingsLoadReport.Origin.Backup; return d; }
                report.FixedFields.Clear();
            }
            var legacy = PcSettingsJson.FromLegacy(m_Legacy, report);
            if (legacy != null) { report.Source = PcSettingsLoadReport.Origin.Legacy; return legacy; }
            report.Source = PcSettingsLoadReport.Origin.Defaults;
            return PcSettingsData.Defaults();
        }

        /// <summary>Sanitizes a copy and writes it atomically. Throws on I/O errors (caller logs; the old file stays intact).</summary>
        public void Save(PcSettingsData data)
        {
            var copy = data.Clone().Sanitize();
            string json = PcSettingsJson.ToJson(copy);
            System.IO.Directory.CreateDirectory(Directory);
            using (var fs = new FileStream(TempPath, FileMode.Create, FileAccess.Write, FileShare.None))
            using (var w = new StreamWriter(fs, new System.Text.UTF8Encoding(false)))
            {
                w.Write(json);
                w.Flush();
                fs.Flush(true);
            }
            if (File.Exists(FilePath))
            {
                try { File.Replace(TempPath, FilePath, BackupPath, true); return; }
                catch (PlatformNotSupportedException) { }
                catch (IOException) { }
                // Fallback (file systems without Replace): keep the old file as .bak, then move the new one in.
                if (File.Exists(BackupPath)) File.Delete(BackupPath);
                File.Move(FilePath, BackupPath);
            }
            File.Move(TempPath, FilePath);
        }

        static string ReadOrNull(string path)
        {
            try { return File.ReadAllText(path); }
            catch (IOException) { return null; }
            catch (UnauthorizedAccessException) { return null; }
        }

        static void TryMove(string from, string to)
        {
            try
            {
                if (File.Exists(to)) File.Delete(to);
                File.Move(from, to);
            }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }
    }
}
