namespace Game.Rendering
{
    /// <summary>
    /// night-pc-s23: dusk / night lighting of the PC tiers (Windows primary, D73), kept apart from <see cref="PcTierTable"/>
    /// (ADR 0269; shadows / AA / vegetation are another agent's fields) and applied at the end of
    /// <see cref="PcGraphicsTiers.Overlay"/>. Phones never reach this (PC overlay only on the desktop player and in
    /// visual QA with -Pc). Pure data, no UnityEngine calls.
    /// - lampPools: analytic street-lamp pools (ADR 0062 / 0191; cost a uniform loop on lit pixels at dusk / night only).
    ///   Supersedes PcTierTable.lampPools (6 / 8 / 8 / 8) - leader: fold back into the table after both branches merge.
    ///   16 = shader array size (StreetLamps.MaxPools). With more than 8 the focus moves ahead (StreetLamps.PoolFocusAhead).
    /// - lampPoolSpecular: GGX highlight of the pools and of the headlamps (the streak on asphalt); mobile Low / Medium off.
    /// - projectedHeadlamps: the player truck's dipped beam lights the world (UN R112 class B-shaped analytic beam), on
    ///   every PC tier - two beam evaluations per lit world pixel while the low beam is on.
    /// All WORKING_VALUE (no measurement on the D74 hardware classes).
    /// </summary>
    public static class PcNightLighting
    {
        public struct Settings
        {
            public int lampPools;
            public bool lampPoolSpecular;
            public bool projectedHeadlamps;
        }

        static readonly Settings[] k_Table =
        {
            new Settings { lampPools = 8,  lampPoolSpecular = false, projectedHeadlamps = true },   // Low (GTX 660 class)
            new Settings { lampPools = 12, lampPoolSpecular = true,  projectedHeadlamps = true },   // Medium
            new Settings { lampPools = 16, lampPoolSpecular = true,  projectedHeadlamps = true },   // High
            new Settings { lampPools = 16, lampPoolSpecular = true,  projectedHeadlamps = true },   // Ultra
        };

        public static Settings Get(PcTier tier) => k_Table[(int)tier];

        /// <summary>Night fields of a PC tier onto a (PC-overlaid) quality tier.</summary>
        public static QualityProfile.Tier Overlay(PcTier tier, QualityProfile.Tier t)
        {
            var s = Get(tier);
            t.lampPools = s.lampPools;
            t.lampPoolSpecular = s.lampPoolSpecular;
            t.projectedHeadlamps = s.projectedHeadlamps;
            return t;
        }
    }
}
