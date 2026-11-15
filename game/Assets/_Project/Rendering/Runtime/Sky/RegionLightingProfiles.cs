using System;
using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0216: per-region lighting data (Data/Regions/lighting_profiles.json, owner D65 p.7-8). A profile lists the regions
    /// it applies to; later profiles override earlier ones field by field. Regions not listed keep the global behaviour
    /// (tile C, Dojlidy). Read by the world import (WorldSceneBuilder) and written to the scene's EnvironmentLighting.
    /// </summary>
    [Serializable]
    public sealed class RegionLightingProfiles
    {
        [Serializable]
        public sealed class Profile
        {
            public string id = "";
            public string[] regions = new string[0];
            public string season = "";
            public float duskClockHour = -1f;
            public float ledCctK;                    // nominal CCT of the luminaires (documentation)
            public float[] ledColour = new float[0];   // linear Rec.709, max channel 1 (WORKING_VALUE)
        }

        public Profile[] profiles = new Profile[0];

        public static RegionLightingProfiles Parse(string json) =>
            string.IsNullOrEmpty(json) ? new RegionLightingProfiles() : JsonUtility.FromJson<RegionLightingProfiles>(json) ?? new RegionLightingProfiles();

        /// <summary>Writes the fields of every profile listing <paramref name="regionId"/>; returns the ids applied.</summary>
        public string ApplyTo(EnvironmentLighting env, string regionId)
        {
            string applied = "";
            if (env == null || profiles == null) return applied;
            foreach (var p in profiles)
            {
                if (p == null || p.regions == null || Array.IndexOf(p.regions, regionId) < 0) continue;
                if (!string.IsNullOrEmpty(p.season)) env.season = p.season;
                if (p.duskClockHour >= 0f) env.duskClockHour = p.duskClockHour;
                if (p.ledColour != null && p.ledColour.Length >= 3) env.ledColour = new Color(p.ledColour[0], p.ledColour[1], p.ledColour[2], 1f);
                applied += (applied.Length > 0 ? "," : "") + p.id;
            }
            return applied;
        }
    }
}
