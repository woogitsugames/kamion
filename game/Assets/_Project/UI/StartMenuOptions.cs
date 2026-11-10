using System.Globalization;
using Game.Rendering;
using UnityEngine;

namespace Game.UI
{
    /// <summary>
    /// What the start menu lets the owner pick besides the scene: time of day (applies to the routes, which carry
    /// <c>EnvironmentLighting</c>), graphics tier and frame-rate cap. Tier and cap apply and persist at once (they are
    /// the same prefs the launch arguments and the diagnostics overlay use); the time of day persists under
    /// <see cref="PrefLighting"/>. Every change writes a <c>[CONTROLS] menu ...</c> line to logcat.
    /// </summary>
    public sealed class StartMenuOptions
    {
        public const string PrefLighting = "menu.lighting";
        /// <summary>Preset ids understood by <c>EnvironmentLighting.SetPreset</c> (LP_Overcast, LP_LowSun, LP_Dusk).</summary>
        public static readonly string[] LightingIds = { "overcast", "lowsun", "dusk" };
        public static readonly string[] LightingLabels = { "Pochmurno", "Niskie słońce", "Zmierzch" };

        public int Lighting { get; private set; }
        public string LightingId => LightingIds[Lighting];
        public string Tier => QualityTiers.Current;
        public int Fps => Application.targetFrameRate > 0 ? Application.targetFrameRate : 30;

        public static StartMenuOptions Load()
        {
            var o = new StartMenuOptions();
            int saved = PlayerPrefs.GetInt(PrefLighting, 0);
            o.Lighting = saved >= 0 && saved < LightingIds.Length ? saved : 0;
            return o;
        }

        public void SetLighting(int index)
        {
            Lighting = Mathf.Clamp(index, 0, LightingIds.Length - 1);
            PlayerPrefs.SetInt(PrefLighting, Lighting);
            PlayerPrefs.Save();
            Debug.Log("[CONTROLS] menu light=" + LightingId);
        }

        public bool SetTier(string tier)
        {
            if (!QualityTiers.Apply(tier, persist: true)) return false;
            Debug.Log("[CONTROLS] menu tier=" + QualityTiers.Current);
            return true;
        }

        public void SetFps(int fps)
        {
            QualityTiers.SetTargetFrameRate(fps, persist: true);
            Debug.Log("[CONTROLS] menu fps=" + fps.ToString(CultureInfo.InvariantCulture));
        }

        /// <summary>One line with the whole start choice, logged when a scene is started.</summary>
        public string StartLine(string label) =>
            "[CONTROLS] menu-start scene=" + label + " light=" + LightingId + " tier=" + Tier + " fps=" + Fps.ToString(CultureInfo.InvariantCulture);
    }
}
