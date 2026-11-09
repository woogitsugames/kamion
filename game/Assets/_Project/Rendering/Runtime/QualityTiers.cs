using System;
using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// Quality tiers = Unity quality levels named Low/Medium/High/Ultra, each bound to its own
    /// URP asset (Assets/_Project/Rendering/Settings/URP_*.asset). Frame-rate target is separate.
    /// </summary>
    public static class QualityTiers
    {
        public static readonly string[] Names = { "Low", "Medium", "High", "Ultra" };
        public static readonly int[] SupportedFrameRates = { 30, 60 };

        const string PrefTier = "diag.qualityTier";
        const string PrefFps = "diag.targetFps";

        public static string Current
        {
            get
            {
                int q = QualitySettings.GetQualityLevel();
                var names = QualitySettings.names;
                return q >= 0 && q < names.Length ? names[q] : q.ToString();
            }
        }

        /// <summary>Applies a tier by name (case-insensitive). Returns false if unknown.</summary>
        public static bool Apply(string tier, bool persist = false)
        {
            if (string.IsNullOrEmpty(tier)) return false;
            var names = QualitySettings.names;
            for (int i = 0; i < names.Length; i++)
            {
                if (!string.Equals(names[i], tier, StringComparison.OrdinalIgnoreCase)) continue;
                QualitySettings.SetQualityLevel(i, true);
                if (persist) { PlayerPrefs.SetString(PrefTier, names[i]); PlayerPrefs.Save(); }
                return true;
            }
            return false;
        }

        public static string Next()
        {
            var names = QualitySettings.names;
            if (names.Length == 0) return Current;
            int next = (QualitySettings.GetQualityLevel() + 1) % names.Length;
            Apply(names[next], persist: true);
            return names[next];
        }

        public static void SetTargetFrameRate(int fps, bool persist = false)
        {
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = fps;
            if (persist) { PlayerPrefs.SetInt(PrefFps, fps); PlayerPrefs.Save(); }
        }

        public static int ToggleFrameRate()
        {
            int fps = Application.targetFrameRate == 60 ? 30 : 60;
            SetTargetFrameRate(fps, persist: true);
            return fps;
        }

        public static string SavedTier => PlayerPrefs.GetString(PrefTier, null);
        public static int SavedFrameRate => PlayerPrefs.GetInt(PrefFps, 0);
    }
}
