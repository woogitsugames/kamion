using UnityEngine;

namespace Game.UI.CabDisplays
{
    /// <summary>
    /// Colours of the cab screens (sRGB), taken from the A6 display textures (tools/blender/truck/interior/make_textures.py)
    /// so the live screens keep the reviewed look: near-black background, warm white, one green, red needle, ISO 2575
    /// telltale colours (red = stop / danger, amber = fault / caution, green = function on, blue = main beam).
    /// Night mode (dipped beam on, same light sensor) dims the graphics; Kamion/Cab Display adds the exposure-based
    /// panel brightness on top, so these are relative values only.
    /// </summary>
    public static class DisplayPalette
    {
        public static readonly Color32 ClusterBg = new Color32(6, 7, 8, 255);
        public static readonly Color32 White = new Color32(225, 222, 214, 255);
        public static readonly Color32 Grey = new Color32(130, 130, 128, 255);
        public static readonly Color32 Dim = new Color32(58, 59, 60, 255);
        public static readonly Color32 Panel = new Color32(20, 21, 23, 255);
        public static readonly Color32 Hub = new Color32(28, 28, 30, 255);
        public static readonly Color32 Needle = new Color32(205, 52, 38, 255);
        public static readonly Color32 Band = new Color32(74, 150, 92, 255);
        public static readonly Color32 RedZone = new Color32(120, 36, 30, 255);
        public static readonly Color32 AdBlue = new Color32(110, 160, 210, 255);

        public static readonly Color32 TellRed = new Color32(205, 52, 38, 255);
        public static readonly Color32 TellAmber = new Color32(226, 150, 28, 255);
        public static readonly Color32 TellGreen = new Color32(74, 168, 92, 255);
        public static readonly Color32 TellBlue = new Color32(60, 120, 230, 255);

        /// <summary>Night dimming of the cluster graphics (relative to day). WORKING_VALUE (review r4 L3: "-60 %" for the navigation).</summary>
        public const float ClusterNight = 0.62f;

        // Navigation, day (A6 infotainment texture) and night (dark map, as truck navigations switch with the dipped beam).
        public struct Nav
        {
            public Color32 Bg, Building, Casing, Road, MajorCasing, Major, Route, RouteCasing, RoutePassed, Arrow, ArrowEdge,
                Box, BoxText, BoxSub, Bar, BarText, BarSub, Limit, LimitFace, LimitText;
        }

        public static readonly Nav NavDay = new Nav
        {
            Bg = new Color32(226, 226, 220, 255), Building = new Color32(208, 204, 196, 255),
            Casing = new Color32(196, 196, 190, 255), Road = new Color32(255, 255, 255, 255),
            MajorCasing = new Color32(214, 176, 102, 255), Major = new Color32(240, 200, 120, 255),
            Route = new Color32(46, 110, 190, 255), RouteCasing = new Color32(28, 72, 140, 255), RoutePassed = new Color32(150, 160, 175, 255),
            Arrow = new Color32(30, 30, 30, 255), ArrowEdge = new Color32(255, 255, 255, 255),
            Box = new Color32(36, 70, 120, 255), BoxText = new Color32(255, 255, 255, 255), BoxSub = new Color32(210, 220, 235, 255),
            Bar = new Color32(40, 42, 46, 255), BarText = new Color32(255, 255, 255, 255), BarSub = new Color32(190, 192, 196, 255),
            Limit = new Color32(200, 40, 34, 255), LimitFace = new Color32(255, 255, 255, 255), LimitText = new Color32(20, 20, 20, 255),
        };

        public static readonly Nav NavNight = new Nav
        {
            Bg = new Color32(26, 28, 32, 255), Building = new Color32(42, 44, 50, 255),
            Casing = new Color32(18, 19, 22, 255), Road = new Color32(74, 77, 84, 255),
            MajorCasing = new Color32(60, 52, 34, 255), Major = new Color32(118, 100, 62, 255),
            Route = new Color32(58, 120, 205, 255), RouteCasing = new Color32(24, 50, 92, 255), RoutePassed = new Color32(70, 74, 82, 255),
            Arrow = new Color32(230, 230, 228, 255), ArrowEdge = new Color32(20, 20, 22, 255),
            Box = new Color32(26, 46, 80, 255), BoxText = new Color32(205, 208, 212, 255), BoxSub = new Color32(140, 150, 165, 255),
            Bar = new Color32(14, 15, 17, 255), BarText = new Color32(200, 200, 198, 255), BarSub = new Color32(120, 122, 126, 255),
            Limit = new Color32(150, 34, 28, 255), LimitFace = new Color32(150, 150, 148, 255), LimitText = new Color32(14, 14, 14, 255),
        };

        public static Color32 Scale(Color32 c, float k) =>
            new Color32((byte)(c.r * k + 0.5f), (byte)(c.g * k + 0.5f), (byte)(c.b * k + 0.5f), c.a);
    }
}
