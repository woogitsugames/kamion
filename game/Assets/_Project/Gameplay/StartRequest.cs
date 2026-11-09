using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Start choice made in the Boot menu, consumed once by <see cref="DrivingLabBootstrap"/> in the next scene.
    /// Carries the same values as the launch arguments route_s / route_end (route distance in metres), so a menu start
    /// and an adb start behave identically; an explicit launch argument still wins.
    /// </summary>
    public static class StartRequest
    {
        /// <summary>Gate 3 samples (docs/plan/STAGE-3.md section 2): G3-A s 12-450 m, G3-B s 1232-1718 m.</summary>
        public const float G3AStartS = 12f, G3AEndS = 450f, G3BStartS = 1232f, G3BEndS = 1718f;

        public static bool Pending { get; private set; }
        public static float RouteS { get; private set; } = -1f;
        public static float RouteEndS { get; private set; } = -1f;
        public static string Label { get; private set; } = "";

        public static void Set(string label, float routeS, float routeEndS)
        {
            Pending = true; Label = label; RouteS = routeS; RouteEndS = routeEndS;
            Debug.Log($"[START] menu choice '{label}' route_s={routeS} route_end={routeEndS}");
        }

        /// <summary>Returns the pending request once and clears it.</summary>
        public static bool Consume(out float routeS, out float routeEndS)
        {
            routeS = RouteS; routeEndS = RouteEndS;
            bool had = Pending;
            Pending = false; RouteS = -1f; RouteEndS = -1f;
            return had;
        }
    }
}
