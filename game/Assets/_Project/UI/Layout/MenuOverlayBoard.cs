using Game.Controls;
using UnityEngine;

namespace Game.UI.Layout
{
    /// <summary>
    /// ADR 0276: what the start menu and the diagnostics overlay tell each other so that neither covers the other. The
    /// menu publishes its block (unshifted bounding box, centre origin, y up, canvas units); the overlay publishes whether
    /// it exists, whether its text panel is wanted and the panel size it reserves. Both call <see cref="Solve"/> every
    /// frame with their own content size (same screen, same <see cref="HudScaleModel"/> scale) and apply their part of
    /// the result. Plain static fields: no allocation.
    /// </summary>
    public static class MenuOverlayBoard
    {
        public static bool MenuActive;
        public static Rect MenuBlock;
        public static bool OverlayActive;
        public static bool PanelShown = true;
        public static Vector2 PanelSize = MenuOverlayLayout.DefaultPanelSize;
        /// <summary>Diagnostics button size and spacing (DiagnosticsOverlay: 300 x 84, spacing 14).</summary>
        public static readonly Vector2 ButtonSize = new Vector2(300f, 84f);
        public const float ButtonSpacing = 14f;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetStatics()
        {
            MenuActive = false; MenuBlock = default; OverlayActive = false; PanelShown = true;
            PanelSize = MenuOverlayLayout.DefaultPanelSize;
        }

        public static void Solve(Vector2 contentUnits, out MenuOverlayResult result)
        {
            var input = new MenuOverlayInput
            {
                ContentUnits = contentUnits,
                HasMenu = MenuActive,
                MenuBlock = MenuBlock,
                HasOverlay = OverlayActive,
                PanelShown = PanelShown,
                PanelSize = PanelSize,
                ButtonSize = ButtonSize,
                ButtonSpacing = ButtonSpacing,
            };
            MenuOverlayLayout.Solve(input, out result);
        }
    }
}
