using System;

namespace Game.Rendering
{
    /// <summary>
    /// The player's graphics-tier choice of the PC settings (ADR 0270) applied to the quality levels (ADR 0269), with the
    /// rule for "auto" (review #136 P1-1, D74):
    /// - "auto" is never saved. At startup it leaves the tier GameBootstrap picked alone (launch argument, a saved
    ///   explicit choice, or the hardware default of <see cref="PcGraphicsTiers.DefaultFor(PcHardwareInfo)"/>).
    /// - choosing "auto" in the menu forgets the saved tier and applies the hardware default without saving it, so the
    ///   detection also runs on every later start;
    /// - an explicit tier is applied and saved as before (the key the start menu and <c>-tier</c> use).
    /// A choice is the Unity quality level name ("Low" .. "Ultra"); null or empty = auto. Startup and menu only.
    /// </summary>
    public static class PcTierChoice
    {
        /// <summary>Quality level name "auto" stands for on this hardware (pure; at most High, ADR 0269).</summary>
        public static string AutoTierName(PcHardwareInfo hw) => PcTierTable.NameOf(PcGraphicsTiers.DefaultFor(hw));

        /// <summary>Quality level name "auto" stands for on this machine.</summary>
        public static string AutoTierName() => AutoTierName(PcGraphicsTiers.DetectHardware());

        /// <summary>
        /// Startup, after GameBootstrap made its own choice. Auto: nothing is applied and nothing is saved. An explicit
        /// tier from the settings file is applied and saved. Returns true when the choice was explicit and is in effect.
        /// </summary>
        public static bool ApplyAtStartup(string qualityLevel)
        {
            if (string.IsNullOrEmpty(qualityLevel)) return false;
            return ApplyExplicit(qualityLevel);
        }

        /// <summary>
        /// Menu ("Zastosuj"). Auto: the saved tier is removed first (also when the level does not change), then the
        /// default for <paramref name="hw"/> is applied without saving. Returns false when the quality level is unknown.
        /// </summary>
        public static bool ApplyFromMenu(string qualityLevel, PcHardwareInfo hw)
        {
            if (!string.IsNullOrEmpty(qualityLevel)) return ApplyExplicit(qualityLevel);
            QualityTiers.ClearSavedTier();
            string auto = AutoTierName(hw);
            if (string.Equals(QualityTiers.Current, auto, StringComparison.OrdinalIgnoreCase)) return true;
            return QualityTiers.Apply(auto, persist: false);
        }

        static bool ApplyExplicit(string qualityLevel)
        {
            // Already active and saved (GameBootstrap applied the same saved tier): no second apply, no second [PC_TIER] line.
            if (string.Equals(QualityTiers.Current, qualityLevel, StringComparison.OrdinalIgnoreCase) &&
                string.Equals(QualityTiers.SavedTier, qualityLevel, StringComparison.OrdinalIgnoreCase)) return true;
            return QualityTiers.Apply(qualityLevel, persist: true);
        }
    }
}
