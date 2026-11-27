using System;
using Game.Rendering;

namespace Game.World
{
    /// <summary>ADR 0136: runtime overrides for selected instanced props on PC Low and Medium.</summary>
    public static class WorldPropTierPolicy
    {
        public readonly struct Rule
        {
            public readonly float CullM;
            readonly float m_LodScale;
            public readonly bool SuppressShadows;

            internal Rule(float cullM, float lodScale, bool suppressShadows)
            {
                CullM = cullM;
                m_LodScale = lodScale;
                SuppressShadows = suppressShadows;
            }

            public float CullLimit(float distanceScale) => CullM > 0f ? CullM * distanceScale : float.PositiveInfinity;
            public float LodScale => m_LodScale > 0f ? m_LodScale : 1f;
        }

        // WORKING_VALUE. Vehicle contact patches are shared by spec, so all their owners use the same cap.
        static readonly Rule k_LightVehicleLow = new Rule(150f, 0.8f, true);
        static readonly Rule k_LightVehicleMedium = new Rule(225f, 0.9f, false);
        static readonly Rule k_HeavyVehicleLow = new Rule(150f, 1f, false);
        static readonly Rule k_HeavyVehicleMedium = new Rule(225f, 1f, false);

        static readonly (string Prefix, Rule Low, Rule Medium)[] k_Rules =
        {
            ("car_", k_LightVehicleLow, k_LightVehicleMedium),
            ("van_", k_LightVehicleLow, k_LightVehicleMedium),
            ("tractor_", k_HeavyVehicleLow, k_HeavyVehicleMedium),
            ("trailer_", k_HeavyVehicleLow, k_HeavyVehicleMedium),
            ("contact_", k_HeavyVehicleLow, k_HeavyVehicleMedium),
            ("fab_", new Rule(50f, 1f, true), new Rule(70f, 1f, false)),
        };

        public static bool TryGetTier(bool pcEnabled, string tierName, out PcTier tier) =>
            PcTierTable.TryParse(tierName, out tier) && pcEnabled && (tier == PcTier.Low || tier == PcTier.Medium);

        public static Rule For(PcTier tier, string prototype)
        {
            if ((tier != PcTier.Low && tier != PcTier.Medium) || string.IsNullOrEmpty(prototype)) return default;
            foreach (var row in k_Rules)
                if (prototype.StartsWith(row.Prefix, StringComparison.Ordinal))
                    return tier == PcTier.Low ? row.Low : row.Medium;
            return default;
        }
    }
}
