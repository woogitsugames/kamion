namespace Game.Core.Navigation
{
    /// <summary>
    /// ETA of the remaining route from the OSM speed limits and the Polish truck speed profile
    /// (art. 20 ustawy Prawo o ruchu drogowym, Dz.U. 1997 nr 98 poz. 602: vehicle combination > 3.5 t -
    /// 80 km/h on motorways / expressways, 70 km/h outside built-up areas, 50 km/h in built-up areas;
    /// quoted, UNVERIFIED - no network check in this session). Road class approximates the area:
    /// class 0/1 (service/residential/tertiary) = built-up 50, class 2 (secondary) = 70, class 3 (primary/trunk) = 80.
    /// A tagged OSM limit below the profile caps the speed. Pure, no allocation.
    /// </summary>
    public static class NavEta
    {
        public const float ExpresswayKmh = 80f, OutsideBuiltUpKmh = 70f, BuiltUpKmh = 50f;

        /// <summary>ETA speed of the truck on a segment [km/h] from its road class and the OSM limit (0 = untagged).</summary>
        public static float TruckSpeedKmh(byte edgeClass, byte osmLimitKmh)
        {
            float profile = edgeClass <= 1 ? BuiltUpKmh : edgeClass == 2 ? OutsideBuiltUpKmh : ExpresswayKmh;
            return osmLimitKmh > 0 ? UnityEngine.Mathf.Min(osmLimitKmh, profile) : profile;
        }

        /// <summary>ETA [s] of the route from <paramref name="routeS"/> to the destination (0 when no route). No allocation.</summary>
        public static float RemainingSeconds(RoutePath p, float routeS)
        {
            if (p == null || p.Count < 2) return 0f;
            float eta = 0f;
            for (int i = 1; i < p.Count; i++)
            {
                float s1 = p.S[i];
                if (s1 <= routeS) continue;
                float from = UnityEngine.Mathf.Max(p.S[i - 1], routeS);
                float kmh = TruckSpeedKmh(p.Class[i - 1], p.Limit[i - 1]);
                eta += (s1 - from) / (kmh / 3.6f);
            }
            return eta;
        }
    }
}
