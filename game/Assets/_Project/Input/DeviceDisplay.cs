using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Physical display facts for touch input and the [SCREEN] log (ADR 0135). On Android <c>Screen.dpi</c> can be the
    /// density bucket (e.g. 480 / 560) rather than the panel's real pixel density; <c>DisplayMetrics.xdpi</c> is the
    /// panel value. Both are read once per window size (a fold switches panels, which have different densities) and
    /// sanitised (<see cref="SteeringMath.SanitizeDpi"/>). JNI only on a size change; no allocation per frame.
    /// </summary>
    public static class DeviceDisplay
    {
        static int s_W = -1, s_H = -1;
        static float s_Dpi, s_ReportedDpi, s_XDpi;
        static int s_Rotation = -1;

        /// <summary>DPI to convert finger travel to millimetres for the current window.</summary>
        public static float Dpi { get { Refresh(); return s_Dpi; } }
        /// <summary>Unity <c>Screen.dpi</c> at the last refresh (may be a density bucket).</summary>
        public static float ReportedDpi { get { Refresh(); return s_ReportedDpi; } }
        /// <summary>Android <c>DisplayMetrics.xdpi</c> (0 = not available).</summary>
        public static float PanelXDpi { get { Refresh(); return s_XDpi; } }
        /// <summary>Android display rotation 0..3 (Surface.ROTATION_0..270) relative to the panel's natural orientation; -1 = unknown.</summary>
        public static int Rotation { get { Refresh(); return s_Rotation; } }

        /// <summary>Forces a re-read on the next access (orientation lock changes the rotation without a size change).</summary>
        public static void Invalidate() { s_W = -1; s_H = -1; }

        /// <summary>
        /// Picks the panel xdpi when it is plausible against the reported (bucket) DPI (within 0.6-1.6x), otherwise the
        /// reported DPI; then <see cref="SteeringMath.SanitizeDpi"/>. Pure, unit-tested.
        /// </summary>
        public static float Choose(float reportedDpi, float panelXDpi)
        {
            bool panelOk = panelXDpi > 100f && panelXDpi < 1000f && (reportedDpi <= 1f || (panelXDpi > 0.6f * reportedDpi && panelXDpi < 1.6f * reportedDpi));
            return SteeringMath.SanitizeDpi(panelOk ? panelXDpi : reportedDpi);
        }

        /// <summary>"portrait" / "landscape" natural orientation of the panel from the current window and the display
        /// rotation (rotation 0/2 = window is in the natural orientation); "unknown" without a rotation.</summary>
        public static string NaturalOrientation(int width, int height, int rotation)
        {
            if (rotation < 0 || width <= 0 || height <= 0) return "unknown";
            bool windowLandscape = width >= height;
            bool upright = rotation == 0 || rotation == 2;
            return (windowLandscape == upright) ? "landscape" : "portrait";
        }

        static void Refresh()
        {
            int w = Screen.width, h = Screen.height;
            if (w == s_W && h == s_H) return;
            s_W = w; s_H = h;
            s_ReportedDpi = Screen.dpi;
            s_XDpi = 0f; s_Rotation = -1;
#if UNITY_ANDROID && !UNITY_EDITOR
            try
            {
                using (var player = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
                using (var activity = player.GetStatic<AndroidJavaObject>("currentActivity"))
                using (var res = activity.Call<AndroidJavaObject>("getResources"))
                using (var dm = res.Call<AndroidJavaObject>("getDisplayMetrics"))
                using (var wm = activity.Call<AndroidJavaObject>("getWindowManager"))
                using (var display = wm.Call<AndroidJavaObject>("getDefaultDisplay"))
                {
                    s_XDpi = dm.Get<float>("xdpi");
                    s_Rotation = display.Call<int>("getRotation");
                }
            }
            catch (System.Exception) { s_XDpi = 0f; s_Rotation = -1; }
#endif
            s_Dpi = Choose(s_ReportedDpi, s_XDpi);
        }
    }
}
