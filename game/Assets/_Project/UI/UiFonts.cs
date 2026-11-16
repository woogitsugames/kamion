using UnityEngine;

namespace Game.UI
{
    /// <summary>
    /// UI typeface: Inter Regular (SIL OFL 1.1, Resources/Fonts/Inter-Regular.otf with Inter-OFL.txt; docs/LICENSES.md
    /// font-inter), the same family as the cab displays. Falls back to Unity's built-in font if the file is missing.
    /// ADR 0283: <see cref="Strong"/> = Inter SemiBold (OFL 1.1, Inter 4.1 release, docs/LICENSES.md font-inter-semibold) for
    /// titles, section heads, numbers of the HUD strip and warning tiles; falls back to <see cref="Default"/>.
    /// </summary>
    public static class UiFonts
    {
        static Font s_Default;

        public static Font Default
        {
            get
            {
                if (s_Default != null) return s_Default;
                s_Default = Resources.Load<Font>("Fonts/Inter-Regular");
                if (s_Default == null) s_Default = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                return s_Default;
            }
        }

        static Font s_Strong;

        public static Font Strong
        {
            get
            {
                if (s_Strong != null) return s_Strong;
                s_Strong = Resources.Load<Font>("Fonts/Inter-SemiBold");
                if (s_Strong == null) s_Strong = Default;
                return s_Strong;
            }
        }
    }
}
