using UnityEngine;

namespace Game.UI
{
    /// <summary>
    /// UI typeface: Inter Regular (SIL OFL 1.1, Resources/Fonts/Inter-Regular.otf with Inter-OFL.txt; docs/LICENSES.md
    /// font-inter), the same family as the cab displays. Falls back to Unity's built-in font if the file is missing.
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
    }
}
